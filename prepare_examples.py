"""生成版本化的合成测试配置；不接触或改写原申请书。"""
import itertools
import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parent
out = ROOT / 'examples'
out.mkdir(exist_ok=True)
registry = {}
for index, (day, weather, period, week) in enumerate(itertools.product(
        ['weekday', 'weekend'], ['clear', 'rain'], ['lunch', 'dinner'], ['normal', 'exam'])):
    scenario = '_'.join([day, weather, period, week])
    # 下列系数仅用于构造不同负载的测试夹具，没有实测或文献依据。
    count = round(100 * (1 if day == 'weekday' else .8) * (1 if weather == 'clear' else 1.25)
                  * (1 if period == 'lunch' else 1.1) * (1 if week == 'normal' else 1.15))
    profiles = []
    rng = random.Random(20261107 + index)
    for profile_index in range(3):
        times = sorted(round(rng.triangular(0, 119.9, 50), 4) for _ in range(count))
        profiles.append([{'id': f'd{profile_index}-{i:04d}', 'arrival_min': t,
                          'locker_id': 'A', 'upstream_min': rng.choice([20, 25, 30, 35])}
                         for i, t in enumerate(times)])
    config = {'schema_version': '1.0', 'source_kind': 'synthetic',
              'provenance': f'工程测试合成数据 seed={20261107 + index}；情境系数不代表真实校园规律',
              'scenario_id': scenario, 'horizon_min': 120,
              'lockers': [{'id': 'A', 'capacity': 16, 'pickup_servers': 2}],
              'arrival_profiles': profiles, 'notice_delay_samples_min': [0, .2, .5],
              'walk_samples_min': [4, 6, 8, 10, 12, 15] if weather == 'clear' else [6, 8, 10, 12, 15, 18],
              'pickup_service_samples_min': [.3, .5, .7]}
    registry[scenario] = f'{scenario}.json'
    (out / registry[scenario]).write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding='utf-8')
    if index == 0:
        (out / 'synthetic_config.json').write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding='utf-8')
(out / 'registry.json').write_text(json.dumps(registry, indent=2), encoding='utf-8')
print(f'Generated {len(registry)} synthetic scenarios')
