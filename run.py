"""python run.py test | demo | predict --config ... --seed 42 --replications 20"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / '.deps'))
from locker_model import predict


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=['test', 'demo', 'predict'])
    parser.add_argument('--config', type=Path, default=ROOT / 'examples' / 'synthetic_config.json')
    parser.add_argument('--output', type=Path, default=ROOT / 'results' / 'prediction.json')
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--replications', type=int, default=20)
    args = parser.parse_args()
    if args.command == 'test':
        import unittest
        suite = unittest.defaultTestLoader.discover(str(ROOT / 'tests'))
        result = unittest.TextTestRunner(verbosity=2).run(suite)
        raise SystemExit(0 if result.wasSuccessful() else 1)
    if args.command == 'demo':
        from experiments import run
        run()
        return
    try:
        config = json.loads(args.config.read_text(encoding='utf-8'))
        result = predict(config, seed=args.seed, replications=args.replications)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
        print(args.output)
    except (ValueError, KeyError, TypeError, OSError) as exc:
        parser.error(str(exc))


if __name__ == '__main__':
    main()
