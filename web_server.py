"""仅供本机演示的 HTTP 适配器；模型接口保持独立。"""
import argparse
from copy import deepcopy
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import sys
import threading
from urllib.parse import urlsplit
import webbrowser

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / '.deps'))
from locker_model import predict, simulate
from locker_model.adapters import JsonParameterProvider

PROVIDER = JsonParameterProvider(ROOT / 'examples' / 'registry.json')
GATE = threading.BoundedSemaphore(1)
LABELS = {'weekday': '工作日', 'weekend': '周末', 'clear': '晴天', 'rain': '雨天',
          'lunch': '午高峰', 'dinner': '晚高峰', 'normal': '普通周', 'exam': '考试周'}


def bounded_int(value, name, low, high):
    if isinstance(value, bool) or not isinstance(value, int) or not low <= value <= high:
        raise ValueError(f'{name} 需为 {low}—{high} 的整数')
    return value


def run_request(payload):
    if not isinstance(payload, dict):
        raise ValueError('请求内容必须为 JSON 对象')
    scenario = payload.get('scenario_id')
    if not isinstance(scenario, str) or scenario not in PROVIDER.registry:
        raise LookupError('所选场景尚无参数，请选择已有场景')
    capacity = bounded_int(payload.get('capacity'), '柜位容量', 1, 200)
    reps = bounded_int(payload.get('replications'), '重复次数', 1, 100)
    seed = bounded_int(payload.get('seed'), '随机种子', 0, 2147483647)
    config = deepcopy(PROVIDER.get_config(scenario))
    # 本地服务只接受注册表中的已知数据，避免客户端提交任意大规模模型。
    if len(config['lockers']) > 10 or sum(map(len, config['arrival_profiles'])) > 10000:
        raise ValueError('当前配置超过本地演示的计算规模限制')
    for bank in config['lockers']:
        bank['capacity'] = capacity
    return {'settings': {'scenario_id': scenario, 'scenario_label': ' · '.join(LABELS[k] for k in scenario.split('_')),
                         'capacity': capacity, 'replications': reps, 'seed': seed},
            'prediction': predict(config, seed=seed, replications=reps),
            'single_run': simulate(config, seed=seed)}


class Handler(BaseHTTPRequestHandler):
    def respond(self, status, value, content_type='application/json; charset=utf-8'):
        body = value if isinstance(value, bytes) else json.dumps(value, ensure_ascii=False, allow_nan=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'")
        self.end_headers()
        self.wfile.write(body)

    def valid_host(self):
        return self.headers.get('Host') in (f'127.0.0.1:{self.server.server_port}', f'localhost:{self.server.server_port}')

    def do_GET(self):
        if not self.valid_host():
            self.respond(403, {'error': '仅支持本机访问'})
            return
        path = urlsplit(self.path).path
        if path == '/api/scenarios':
            self.respond(200, {'scenarios': [{'id': key, 'label': ' · '.join(LABELS[k] for k in key.split('_')),
                                             'source_kind': PROVIDER.get_config(key)['source_kind']}
                                            for key in PROVIDER.registry]})
            return
        allowed = {'/': ('index.html', 'text/html; charset=utf-8'),
                   '/app.js': ('app.js', 'text/javascript; charset=utf-8'),
                   '/style.css': ('style.css', 'text/css; charset=utf-8')}
        if path not in allowed:
            self.respond(404, {'error': '未找到页面'})
            return
        name, mime = allowed[path]
        self.respond(200, (ROOT / 'web' / name).read_bytes(), mime)

    def do_POST(self):
        origin = self.headers.get('Origin')
        if not self.valid_host() or (origin and origin not in
                (f'http://127.0.0.1:{self.server.server_port}', f'http://localhost:{self.server.server_port}')):
            self.respond(403, {'error': '请求来源不被允许'})
            return
        if urlsplit(self.path).path != '/api/simulate':
            self.respond(404, {'error': '未找到接口'})
            return
        if self.headers.get('Content-Type', '').split(';')[0].strip() != 'application/json':
            self.respond(415, {'error': '请求必须使用 application/json'})
            return
        try:
            length = int(self.headers.get('Content-Length', '0'))
            if not 0 < length <= 4096:
                self.respond(413, {'error': '请求大小需为 1—4096 字节'})
                return
            payload = json.loads(self.rfile.read(length))
        except (ValueError, UnicodeError):
            self.respond(400, {'error': '请求 JSON 无效'})
            return
        if not GATE.acquire(blocking=False):
            self.respond(429, {'error': '已有仿真正在运行，请稍后重试'})
            return
        try:
            self.respond(200, run_request(payload))
        except LookupError:
            self.respond(422, {'error': '所选场景尚无参数'})
        except (ValueError, TypeError):
            self.respond(400, {'error': '参数无效，请检查容量、重复次数和随机种子的范围'})
        except Exception:
            self.log_error('Model execution failed')
            self.respond(500, {'error': '仿真暂时无法完成，请检查本地配置'})
        finally:
            GATE.release()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8765)
    parser.add_argument('--open', action='store_true')
    args = parser.parse_args()
    server = ThreadingHTTPServer(('127.0.0.1', args.port), Handler)
    print(f'Local: http://127.0.0.1:{server.server_port}', flush=True)
    if args.open:
        webbrowser.open(f'http://127.0.0.1:{server.server_port}')
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == '__main__':
    main()
