"""单位统一为分钟；有限柜位 FIFO 投递及独立取餐操作队列。"""
import math
import random
import statistics
import simpy


def number(value, name, positive=False):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f'{name} 必须为数值')
    if not math.isfinite(value) or value < 0 or (positive and value == 0):
        raise ValueError(f'{name} 必须为有限的非负数' + ('且大于零' if positive else ''))


def integer(value, name, minimum=1):
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise ValueError(f'{name} 必须为不小于 {minimum} 的整数')


def validate_config(config):
    if config.get('schema_version') != '1.0':
        raise ValueError('不支持的 schema_version')
    if config.get('source_kind') not in ('synthetic', 'observed', 'literature', 'mixed'):
        raise ValueError('source_kind 不合法')
    if not isinstance(config.get('provenance'), str) or not config['provenance'].strip():
        raise ValueError('provenance 不得为空')
    number(config['horizon_min'], 'horizon_min', True)
    banks = config['lockers']
    if not isinstance(banks, list) or not banks:
        raise ValueError('至少配置一个外卖柜')
    ids = [b['id'] for b in banks]
    if any(not isinstance(i, str) or not i for i in ids) or len(set(ids)) != len(ids):
        raise ValueError('柜体 id 必须为唯一非空字符串')
    for b in banks:
        integer(b['capacity'], 'capacity')
        integer(b['pickup_servers'], 'pickup_servers')
    for field in ('notice_delay_samples_min', 'walk_samples_min', 'pickup_service_samples_min'):
        samples = config[field]
        if not isinstance(samples, list) or not samples:
            raise ValueError(f'{field} 不能为空')
        for v in samples:
            number(v, field, field == 'pickup_service_samples_min')
    profiles = config['arrival_profiles']
    if not isinstance(profiles, list) or not profiles:
        raise ValueError('arrival_profiles 必须至少包含一天的轨迹，允许空日 []')
    for profile in profiles:
        seen = set()
        for order in profile:
            oid = order['id']
            if not isinstance(oid, str) or not oid or oid in seen:
                raise ValueError('订单 id 必须在每日轨迹内唯一')
            seen.add(oid)
            number(order['arrival_min'], 'arrival_min')
            if order['arrival_min'] >= config['horizon_min']:
                raise ValueError('arrival_min 必须小于 horizon_min')
            if order['locker_id'] not in ids:
                raise ValueError('未知 locker_id')
            lead = order.get('upstream_min')
            if lead is not None:
                number(lead, 'upstream_min')


def quantile(values, p):
    if not values:
        return None
    a = sorted(values)
    index = (len(a) - 1) * p
    lo = int(index)
    hi = min(lo + 1, len(a) - 1)
    return a[lo] + (a[hi] - a[lo]) * (index - lo)


def distribution(values):
    return {'count': len(values), 'mean': statistics.mean(values) if values else None,
            'p50': quantile(values, .5), 'p90': quantile(values, .9),
            'p95': quantile(values, .95), 'max': max(values) if values else None}


def simulate(config, seed=0):
    """从空柜开始；到达窗口结束后排空，避免丢掉等待最久的订单。"""
    validate_config(config)
    integer(seed, 'seed', 0)
    rng = random.Random(seed)
    profile = rng.choice(config['arrival_profiles'])
    # 先抽样再调度，保证容量对比时每个订单使用完全相同的输入。
    orders = []
    for item in profile:
        orders.append({**item,
                       'notice': rng.choice(config['notice_delay_samples_min']),
                       'walk': rng.choice(config['walk_samples_min']),
                       'service': rng.choice(config['pickup_service_samples_min'])})
    orders.sort(key=lambda o: (o['arrival_min'], o['id']))
    env = simpy.Environment()
    cabinets = {b['id']: simpy.Resource(env, capacity=b['capacity']) for b in config['lockers']}
    terminals = {b['id']: simpy.Resource(env, capacity=b['pickup_servers']) for b in config['lockers']}
    state = {b['id']: {'occupied': 0, 'delivery_queue': 0, 'pickup_queue': 0} for b in config['lockers']}
    trace = []
    records = []

    def snapshot(bid):
        trace.append({'time_min': env.now, 'locker_id': bid, **state[bid]})

    for bid in state:
        snapshot(bid)

    def process(o):
        yield env.timeout(o['arrival_min'])
        bid = o['locker_id']
        s = state[bid]
        with cabinets[bid].request() as slot:
            waiting_for_slot = not slot.triggered
            if waiting_for_slot:
                s['delivery_queue'] += 1
                snapshot(bid)
            yield slot
            stored = env.now
            if waiting_for_slot:
                s['delivery_queue'] -= 1
            s['occupied'] += 1
            snapshot(bid)
            yield env.timeout(o['notice'] + o['walk'])
            student_arrival = env.now
            with terminals[bid].request() as terminal:
                waiting_for_terminal = not terminal.triggered
                if waiting_for_terminal:
                    s['pickup_queue'] += 1
                    snapshot(bid)
                yield terminal
                pickup_start = env.now
                if waiting_for_terminal:
                    s['pickup_queue'] -= 1
                snapshot(bid)
                yield env.timeout(o['service'])
                done = env.now
            s['occupied'] -= 1
            snapshot(bid)
        lead = o.get('upstream_min')
        records.append({'id': o['id'], 'locker_id': bid, 'arrival_min': o['arrival_min'],
                        'stored_min': stored, 'student_arrival_min': student_arrival,
                        'pickup_start_min': pickup_start, 'pickup_complete_min': done,
                        'deposit_wait_min': stored - o['arrival_min'],
                        'student_queue_wait_min': pickup_start - student_arrival,
                        'total_queue_wait_min': stored - o['arrival_min'] + pickup_start - student_arrival,
                        'pickup_service_min': o['service'],
                        'arrival_to_pickup_min': done - o['arrival_min'],
                        'order_time_min': None if lead is None else o['arrival_min'] - lead,
                        'order_to_pickup_min': None if lead is None else done - o['arrival_min'] + lead})

    for order in orders:
        env.process(process(order))
    env.run()
    horizon = config['horizon_min']
    pressure = []
    for b in config['lockers']:
        points = [p for p in trace if p['locker_id'] == b['id']]
        area = full = 0.0
        for i, point in enumerate(points):
            end = points[i + 1]['time_min'] if i + 1 < len(points) else horizon
            dt = max(0, min(end, horizon) - min(point['time_min'], horizon))
            area += point['occupied'] * dt
            full += (point['occupied'] == b['capacity']) * dt
        pressure.append({'locker_id': b['id'], 'utilization': area / (horizon * b['capacity']),
                         'full_time_fraction': full / horizon,
                         'max_delivery_queue': max(p['delivery_queue'] for p in points),
                         'max_pickup_queue': max(p['pickup_queue'] for p in points)})
    return {'seed': seed, 'source_kind': config['source_kind'], 'provenance': config['provenance'],
            'horizon_min': horizon, 'drain_complete_min': env.now, 'orders': records,
            'metrics': {f: distribution([r[f] for r in records]) for f in
                        ('deposit_wait_min', 'student_queue_wait_min', 'total_queue_wait_min',
                         'arrival_to_pickup_min')},
            'lockers': pressure, 'trace': trace}
