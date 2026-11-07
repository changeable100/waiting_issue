import http.client
import json
import threading
import unittest
from http.server import ThreadingHTTPServer
from web_server import Handler, run_request, PROVIDER, GATE

PAYLOAD = {'scenario_id': 'weekday_clear_lunch_normal', 'capacity': 16, 'replications': 2, 'seed': 42}


class WebTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def request(self, method, path, body=None, headers=None):
        conn = http.client.HTTPConnection('127.0.0.1', self.server.server_port, timeout=10)
        conn.request(method, path, body=body, headers=headers or {})
        response = conn.getresponse()
        result = response.status, response.getheader('Content-Type'), response.read()
        conn.close()
        return result

    def post(self, body=PAYLOAD, headers=None):
        return self.request('POST', '/api/simulate', json.dumps(body), headers or {'Content-Type': 'application/json'})

    def test_page_and_assets(self):
        for path, text in [('/', '校园外卖柜'), ('/app.js', '/api/simulate'), ('/style.css', '@media')]:
            with self.subTest(path=path):
                code, _, body = self.request('GET', path)
                self.assertEqual(code, 200)
                self.assertIn(text, body.decode())

    def test_scenario_catalog(self):
        code, _, body = self.request('GET', '/api/scenarios')
        self.assertEqual(code, 200)
        self.assertEqual(len(json.loads(body)['scenarios']), 16)

    def test_real_model_endpoint(self):
        code, _, body = self.post()
        self.assertEqual(code, 200)
        result = json.loads(body)
        self.assertEqual(result, run_request(PAYLOAD))
        self.assertEqual(result['prediction']['source_kind'], 'synthetic')
        self.assertEqual(result['prediction']['replications'], 2)
        self.assertEqual(len(result['single_run']['orders']), 100)

    def test_capacity_input_changes_model(self):
        low = run_request({**PAYLOAD, 'capacity': 8})
        high = run_request({**PAYLOAD, 'capacity': 24})
        self.assertGreater(low['prediction']['metrics']['deposit_wait_min']['mean'],
                           high['prediction']['metrics']['deposit_wait_min']['mean'])
        self.assertEqual(PROVIDER.get_config(PAYLOAD['scenario_id'])['lockers'][0]['capacity'], 16)

    def test_bad_inputs(self):
        for field, value in [('capacity', 0), ('capacity', True), ('capacity', 201),
                             ('replications', 101), ('seed', -1), ('seed', 1.5)]:
            with self.subTest(field=field, value=value):
                self.assertEqual(self.post({**PAYLOAD, field: value})[0], 400)
        self.assertEqual(self.post([])[0], 400)
        self.assertEqual(self.post({**PAYLOAD, 'scenario_id': 'missing'})[0], 422)

    def test_payload_content_type_and_origin(self):
        self.assertEqual(self.request('POST', '/api/simulate', '{', {'Content-Type': 'application/json'})[0], 400)
        self.assertEqual(self.post(headers={'Content-Type': 'text/plain'})[0], 415)
        self.assertEqual(self.post(headers={'Content-Type': 'application/json', 'Origin': 'https://example.com'})[0], 403)
        self.assertEqual(self.request('GET', '/', headers={'Host': 'example.com'})[0], 403)
        self.assertEqual(self.request('POST', '/api/simulate', 'x' * 4097, {'Content-Type': 'application/json'})[0], 413)

    def test_no_arbitrary_file_access(self):
        self.assertEqual(self.request('GET', '/README.md')[0], 404)
        self.assertEqual(self.request('GET', '/../web_server.py')[0], 404)

    def test_busy_response(self):
        GATE.acquire()
        try:
            self.assertEqual(self.post()[0], 429)
        finally:
            GATE.release()
