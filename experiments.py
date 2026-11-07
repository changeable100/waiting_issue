"""合成场景是工程测试夹具，系数不代表校园测量值。"""
import csv
import json
from pathlib import Path
from locker_model import compare_capacities, simulate

ROOT = Path(__file__).resolve().parent


def run():
    registry = json.loads((ROOT / 'examples' / 'registry.json').read_text(encoding='utf-8'))
    rows = []
    full = []
    for scenario, relative in registry.items():
        config = json.loads((ROOT / 'examples' / relative).read_text(encoding='utf-8'))
        results = compare_capacities(config, [8, 16, 24], seed=42, replications=20)
        full.append({'scenario_id': scenario, 'results': results})
        for item in results:
            p = item['prediction']
            rows.append({'scenario_id': scenario, 'source_kind': 'synthetic',
                         'capacity_per_locker': item['capacity_per_locker'],
                         'deposit_wait_mean_min': p['metrics']['deposit_wait_min']['mean'],
                         'student_queue_wait_mean_min': p['metrics']['student_queue_wait_min']['mean'],
                         'total_queue_wait_p90_min': p['metrics']['total_queue_wait_min']['p90'],
                         'utilization': p['lockers'][0]['utilization'],
                         'full_time_fraction': p['lockers'][0]['full_time_fraction']})
    out = ROOT / 'results'
    out.mkdir(exist_ok=True)
    (out / 'experiments.json').write_text(json.dumps(full, ensure_ascii=False, indent=2), encoding='utf-8')
    with (out / 'experiments.csv').open('w', newline='', encoding='utf-8-sig') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    baseline = json.loads((ROOT / 'examples' / 'synthetic_config.json').read_text(encoding='utf-8'))
    (out / 'single_run.json').write_text(json.dumps(simulate(baseline, seed=42), ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'{len(rows)} scenario/capacity combinations, 20 replications each -> {out}')


if __name__ == '__main__':
    run()
