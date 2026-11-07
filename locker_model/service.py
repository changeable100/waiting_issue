"""留给后端与优化成员调用的 Python 接口；无 HTTP 或数据库依赖。"""
from copy import deepcopy
from .model import simulate, integer, distribution


def predict(config, *, seed=0, replications=20):
    integer(seed, 'seed', 0)
    integer(replications, 'replications')
    if replications > 1000:
        raise ValueError('replications 最大为 1000')
    runs = [simulate(config, seed + i) for i in range(replications)]
    fields = runs[0]['metrics'].keys()
    pooled = {f: distribution([o[f] for run in runs for o in run['orders']]) for f in fields}
    run_means = {f: distribution([run['metrics'][f]['mean'] for run in runs
                                  if run['metrics'][f]['mean'] is not None]) for f in fields}
    return {'schema_version': '1.0', 'source_kind': config['source_kind'],
            'provenance': config['provenance'], 'seed': seed, 'replications': replications,
            'metrics': pooled, 'run_mean_distribution': run_means,
            'lockers': [{'locker_id': b['id'],
                         'utilization': sum(run['lockers'][j]['utilization'] for run in runs) / replications,
                         'full_time_fraction': sum(run['lockers'][j]['full_time_fraction'] for run in runs) / replications}
                        for j, b in enumerate(config['lockers'])],
            'warnings': ['初始空柜，无实时状态接入；到达窗口结束后排空。',
                         '分位区间为样本分布，未经真实观测校准，不是置信区间。']}


def compare_capacities(config, capacities, *, seed=0, replications=20):
    """固定分柜和输入做敏感性对比；选址及最优方案由优化模块负责。"""
    results = []
    for capacity in capacities:
        integer(capacity, 'capacity')
        variant = deepcopy(config)
        for bank in variant['lockers']:
            bank['capacity'] = capacity
        results.append({'capacity_per_locker': capacity,
                        'prediction': predict(variant, seed=seed, replications=replications)})
    return results
