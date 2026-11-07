import copy
import unittest
from locker_model import simulate, predict, compare_capacities
from locker_model.evaluation import evaluate
from locker_model.adapters import JsonParameterProvider
from pathlib import Path


def fixture(arrivals=(0, 0), capacity=1, walk=10, service=1, servers=1):
    return {'schema_version': '1.0', 'source_kind': 'synthetic', 'provenance': '手算测试',
            'horizon_min': 30, 'lockers': [{'id': 'A', 'capacity': capacity, 'pickup_servers': servers}],
            'arrival_profiles': [[{'id': str(i), 'arrival_min': t, 'locker_id': 'A', 'upstream_min': 5}
                                  for i, t in enumerate(arrivals)]],
            'notice_delay_samples_min': [0], 'walk_samples_min': [walk],
            'pickup_service_samples_min': [service]}


class ModelTests(unittest.TestCase):
    def test_full_cabinet_hand_calculation(self):
        r = simulate(fixture())
        self.assertEqual([o['deposit_wait_min'] for o in r['orders']], [0, 11])
        self.assertEqual([o['pickup_complete_min'] for o in r['orders']], [11, 22])
        self.assertAlmostEqual(r['lockers'][0]['utilization'], 22 / 30)

    def test_separate_pickup_queue(self):
        r = simulate(fixture(capacity=2, walk=0, service=3))
        self.assertEqual([o['deposit_wait_min'] for o in r['orders']], [0, 0])
        self.assertEqual([o['student_queue_wait_min'] for o in r['orders']], [0, 3])

    def test_parallel_terminals(self):
        r = simulate(fixture(capacity=2, servers=2, walk=0, service=3))
        self.assertEqual(r['metrics']['student_queue_wait_min']['max'], 0)

    def test_empty_day(self):
        r = simulate(fixture(arrivals=()))
        self.assertEqual(r['orders'], [])
        self.assertIsNone(r['metrics']['deposit_wait_min']['mean'])
        self.assertEqual(r['lockers'][0]['utilization'], 0)

    def test_drain_and_window_integral(self):
        r = simulate(fixture(arrivals=(29,), walk=10))
        self.assertEqual(r['drain_complete_min'], 40)
        self.assertAlmostEqual(r['lockers'][0]['utilization'], 1 / 30)

    def test_t1_t3_identity(self):
        for o in simulate(fixture())['orders']:
            self.assertAlmostEqual(o['pickup_complete_min'] - o['order_time_min'], o['order_to_pickup_min'])

    def test_unknown_upstream_remains_null(self):
        c = fixture()
        del c['arrival_profiles'][0][0]['upstream_min']
        self.assertIsNone(simulate(c)['orders'][0]['order_to_pickup_min'])

    def test_invalid_inputs(self):
        for field, value in [('walk_samples_min', []), ('walk_samples_min', [-1]),
                             ('walk_samples_min', [float('nan')]), ('horizon_min', 0),
                             ('pickup_service_samples_min', [0])]:
            with self.subTest(field=field, value=value):
                c = fixture()
                c[field] = value
                with self.assertRaises(ValueError):
                    simulate(c)
        c = fixture()
        c['lockers'][0]['capacity'] = True
        with self.assertRaises(ValueError):
            simulate(c)

    def test_duplicate_order_and_unknown_bank(self):
        c = fixture()
        c['arrival_profiles'][0][1]['id'] = '0'
        with self.assertRaises(ValueError):
            simulate(c)
        c = fixture()
        c['arrival_profiles'][0][0]['locker_id'] = 'unknown'
        with self.assertRaises(ValueError):
            simulate(c)

    def test_invariants_and_reproducibility(self):
        c = JsonParameterProvider(Path(__file__).resolve().parents[1] / 'examples' / 'registry.json').get_config('weekday_clear_lunch_normal')
        before = copy.deepcopy(c)
        a = simulate(c, 42)
        self.assertEqual(a, simulate(c, 42))
        self.assertEqual(c, before)
        self.assertEqual(len(a['orders']), len(c['arrival_profiles'][0]))
        for point in a['trace']:
            self.assertTrue(0 <= point['occupied'] <= c['lockers'][0]['capacity'])
            self.assertGreaterEqual(point['delivery_queue'], 0)
            self.assertGreaterEqual(point['pickup_queue'], 0)
        self.assertEqual(a['trace'][-1]['occupied'], 0)
        for o in a['orders']:
            self.assertLessEqual(o['arrival_min'], o['stored_min'])
            self.assertLessEqual(o['stored_min'], o['student_arrival_min'])
            self.assertLessEqual(o['student_arrival_min'], o['pickup_start_min'])
            self.assertLessEqual(o['pickup_start_min'], o['pickup_complete_min'])

    def test_multi_bank_isolation(self):
        c = fixture()
        c['lockers'].append({'id': 'B', 'capacity': 1, 'pickup_servers': 1})
        c['arrival_profiles'][0][1]['locker_id'] = 'B'
        self.assertEqual(simulate(c)['metrics']['deposit_wait_min']['max'], 0)

    def test_capacity_comparison(self):
        r = compare_capacities(fixture(), [1, 2], replications=2)
        self.assertGreater(r[0]['prediction']['metrics']['deposit_wait_min']['mean'],
                           r[1]['prediction']['metrics']['deposit_wait_min']['mean'])

    def test_replication_validation(self):
        for count in (0, True, 1001):
            with self.assertRaises(ValueError):
                predict(fixture(), replications=count)

    def test_prediction_empty_day(self):
        p = predict(fixture(arrivals=()), replications=2)
        self.assertIsNone(p['metrics']['deposit_wait_min']['p90'])

    def test_evaluation(self):
        r = evaluate([{'actual_min': 5, 'predicted_min': 3, 'lower_min': 2, 'upper_min': 5},
                      {'actual_min': 10, 'predicted_min': 9, 'lower_min': 1, 'upper_min': 8}])
        self.assertEqual(r, {'n': 2, 'mae_min': 1.5, 'interval_coverage': .5})
        with self.assertRaises(ValueError):
            evaluate([])

    def test_scenario_no_silent_fallback(self):
        provider = JsonParameterProvider(Path(__file__).resolve().parents[1] / 'examples' / 'registry.json')
        with self.assertRaises(ValueError):
            provider.get_config('unknown')


if __name__ == '__main__':
    unittest.main()
