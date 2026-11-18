import json
from pathlib import Path
from tempfile import TemporaryDirectory
import threading
import time
from types import SimpleNamespace
import unittest
from unittest.mock import patch, MagicMock
from urllib.request import urlopen, Request
from urllib.error import HTTPError
from http.server import ThreadingHTTPServer

import numpy as np
import main
from vision_server import InspectionService, VisionHTTPServer, evidence_path, make_handler


def arguments():
    return SimpleNamespace(plc_config=None, confirm_frames=3, camera_index=0,
                           sdk_dir=None, exposure_us=10000, flip_vertical=False,
                           frame_rate=10, light_frequency=50, show=False)


class VisionBridgeTests(unittest.TestCase):
    def test_duplicate_server_cannot_share_port(self):
        service = InspectionService(arguments())
        server = VisionHTTPServer(('127.0.0.1', 0), make_handler(service))
        try:
            with self.assertRaises(OSError):
                duplicate = VisionHTTPServer(server.server_address, make_handler(service))
                duplicate.server_close()
        finally:
            server.server_close()

    def test_stale_preview_and_reset_are_refused(self):
        service = InspectionService(arguments())
        image = np.zeros((100, 100, 3), np.uint8)
        service.publish(image, image, 0, True, 3, None)
        self.assertTrue(service.status()['reset_eligible'])
        self.assertTrue(service.image('raw').startswith(b'\xff\xd8'))
        service.last_tick = time.monotonic() - 6
        self.assertTrue(service.status()['stale'])
        with self.assertRaises(RuntimeError):
            service.image('raw')
        with self.assertRaises(RuntimeError):
            service.reset()

    def test_single_worker_and_fault_status(self):
        service = InspectionService(arguments())
        entered = threading.Event()
        release = threading.Event()

        def loop(*_):
            entered.set()
            release.wait(2)
            raise OSError('Camera unavailable')

        with patch('vision_server.detector.run_camera', side_effect=loop):
            service.start()
            self.assertTrue(entered.wait(1))
            with self.assertRaises(RuntimeError):
                service.start()
            release.set()
            service.thread.join(2)
        self.assertEqual(service.status()['state'], 'fault')
        self.assertEqual(service.status()['error'], 'Camera unavailable')
        self.assertFalse(service.status()['reset_eligible'])

    def test_loop_reset_and_latch_survive_stop(self):
        service = InspectionService(arguments())
        image = np.zeros((100, 100, 3), np.uint8)
        camera = MagicMock()
        camera.__enter__.return_value = camera
        camera.read.return_value = image
        # First three frames confirm; the next three permit a reset.
        counts = iter([1, 1, 1, 0, 0, 0, 0, 1, 1, 1])
        original_publish = service.publish
        request = {'done': threading.Event(), 'error': None}

        def publish(*args):
            result = original_publish(*args)
            if service.frames == 3:
                self.assertTrue(service.alarm_latched)
                # Queue a reset; next frame is not sufficiently clear and must refuse it.
                service.resets.put(request)
            if service.frames == 4:
                self.assertIs(result, request)
            if service.frames == 6:
                self.assertTrue(request['done'].is_set())
                self.assertIsNotNone(request['error'])
                service.resets.put({'done': threading.Event(), 'error': None})
            if service.frames == 8:
                self.assertFalse(service.alarm_latched)
            if service.frames == 10:
                service.stop_event.set()
            return result

        with TemporaryDirectory() as directory, \
             patch('camera_controller.MindVisionCamera', return_value=camera), \
             patch.object(main, 'TEST_DIR', Path(directory) / 'raw'), \
             patch.object(main, 'RESULT_DIR', Path(directory) / 'results'), \
             patch.object(main.cv2, 'imread', return_value=image), \
             patch.object(main.cv2, 'imwrite', return_value=True), \
             patch.object(main.Detection, 'detection', side_effect=lambda *_: (image, image[:, :, 0], next(counts))), \
             patch.object(service, 'publish', side_effect=publish), patch('builtins.print'):
            main.run_camera(service.args, service)
        # Reset on frame 7 clears the latch; three later object frames latch a second alarm.
        self.assertTrue(service.alarm_latched)

    def test_reset_success_and_plc_refusal(self):
        service = InspectionService(arguments())
        image = np.zeros((100, 100, 3), np.uint8)
        service.publish(image, image, 0, True, 3, None)
        results = []
        thread = threading.Thread(target=lambda: results.append(service.reset()))
        thread.start()
        request = service.resets.get(timeout=1)
        service.complete_reset(request, None)
        thread.join(1)
        self.assertFalse(service.alarm_latched)
        self.assertEqual(results, ['Software alarm reset'])
        service.args.plc_config = 'configured.json'
        self.assertFalse(service.status()['reset_eligible'])

    def test_http_commands_require_header_and_local_origin(self):
        service = InspectionService(arguments())
        server = ThreadingHTTPServer(('127.0.0.1', 0), make_handler(service))
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        base = f'http://127.0.0.1:{server.server_port}'
        try:
            with urlopen(base + '/api/status') as response:
                self.assertEqual(json.load(response)['state'], 'stopped')
            for headers in ({}, {'X-Vision-Control': '1', 'Origin': 'https://example.org'}):
                with self.assertRaises(HTTPError) as error:
                    urlopen(Request(base + '/api/start', data=b'', headers=headers))
                self.assertEqual(error.exception.code, 403)
                error.exception.close()
            with urlopen(Request(base + '/api/stop', data=b'', headers={'X-Vision-Control': '1'})) as response:
                self.assertEqual(response.status, 200)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(2)

    def test_evidence_rejects_traversal(self):
        for event, kind in (('../plc_config', 'raw'), ('alarm_20260101_010101_000000', '../raw')):
            with self.assertRaises(ValueError):
                evidence_path(event, kind)


if __name__ == '__main__':
    unittest.main()
