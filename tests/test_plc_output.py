import json
from pathlib import Path
import socketserver
import struct
import threading
import time
import unittest
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import numpy as np
import main

from plc_output import ModbusCoilClient, PLCAlarmOutput, PLCConfig


class Simulator(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


class Handler(socketserver.BaseRequestHandler):
    def receive(self, size):
        data = b""
        while len(data) < size:
            try:
                part = self.request.recv(size - len(data))
            except OSError:
                return None
            if not part:
                return None
            data += part
        return data

    def handle(self):
        while True:
            header = self.receive(7)
            if header is None:
                return
            tx, protocol, length, unit = struct.unpack(">HHHB", header)
            body = self.receive(length - 1)
            if body is None:
                return
            function, address, value = struct.unpack(">BHH", body)
            self.server.writes.append((unit, function, address, value))
            mode = self.server.mode
            if mode == "disconnect":
                return
            response = b"\x85\x02" if mode == "exception" else body
            packet = struct.pack(">HHHB", tx + (mode == "wrong_transaction"), 0,
                                 len(response) + 1, unit) + response
            try:
                # Exercise fragmented TCP responses, not just one recv per message.
                self.request.sendall(packet[:3])
                self.request.sendall(packet[3:])
            except OSError:
                return


class PLCOutputTests(unittest.TestCase):
    def setUp(self):
        self.server = Simulator(("127.0.0.1", 0), Handler)
        self.server.mode = "echo"
        self.server.writes = []
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.config = PLCConfig(host="127.0.0.1", port=self.server.server_address[1],
                                unit_id=7, alarm_coil=3072, heartbeat_coil=3073,
                                healthy_coil=3074, timeout=0.2,
                                reset_coil=3075,
                                heartbeat_interval=0.03, inspection_timeout=0.12)

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()

    def wait_for(self, predicate):
        deadline = time.monotonic() + 3
        while time.monotonic() < deadline:
            if predicate():
                return
            time.sleep(0.01)
        self.fail("Timed out waiting for simulated PLC state")

    def test_write_coil_encoding_and_fragmented_response(self):
        client = ModbusCoilClient(self.config)
        try:
            client.write_coil(3072, True)
            client.write_coil(3072, False)
            self.assertEqual(self.server.writes, [(7, 5, 3072, 0xFF00), (7, 5, 3072, 0)])
        finally:
            client.close()

    def test_rejected_malformed_and_disconnected_responses(self):
        client = ModbusCoilClient(self.config)
        try:
            for mode in ("exception", "wrong_transaction", "disconnect"):
                self.server.mode = mode
                with self.assertRaises(ConnectionError):
                    client.write_coil(3072, True)
                self.assertIsNone(client.connection)
            self.server.mode = "echo"
            client.write_coil(3072, True)
        finally:
            client.close()

    def test_latch_reconnect_stale_health_and_shutdown(self):
        with patch("builtins.print"):
            with PLCAlarmOutput(self.config) as output:
                output.inspection_completed(True)
                self.wait_for(lambda: (7, 5, 3072, 0xFF00) in self.server.writes)
                self.wait_for(lambda: (7, 5, 3074, 0xFF00) in self.server.writes)
                output.inspection_completed(False)
                self.assertTrue(output.alarm)
                self.server.mode = "disconnect"
                self.wait_for(lambda: output.client.connection is None)
                marker = len(self.server.writes)
                self.server.mode = "echo"
                self.wait_for(lambda: (7, 5, 3072, 0xFF00) in self.server.writes[marker:])
                self.wait_for(lambda: (7, 5, 3074, 0) in self.server.writes[marker:])
                heartbeats = {value for _, _, addr, value in self.server.writes if addr == 3073}
                self.assertEqual(heartbeats, {0, 0xFF00})
            self.assertFalse(output.thread.is_alive())
            self.assertEqual(self.server.writes[-1], (7, 5, 3074, 0))

    def test_configuration_rejects_overlapping_addresses(self):
        with self.assertRaises(ValueError):
            PLCConfig(host="localhost", alarm_coil=0, heartbeat_coil=0, healthy_coil=2)

    def test_reset_clears_request_pulses_and_rearms(self):
        with patch("builtins.print"):
            with PLCAlarmOutput(self.config) as output:
                output.inspection_completed(True)
                self.wait_for(lambda: output.connected)
                marker = len(self.server.writes)
                output.request_reset()
                self.wait_for(lambda: (7, 5, 3075, 0xFF00) in self.server.writes[marker:])
                writes = self.server.writes[marker:]
                pulse_index = writes.index((7, 5, 3075, 0xFF00))
                self.assertIn((7, 5, 3072, 0), writes[:pulse_index])
                self.assertIn((7, 5, 3074, 0xFF00), writes[:pulse_index])
                self.assertFalse(output.alarm)
                output.inspection_completed(False)
                # A new confirmed alarm must cancel any reset pulse immediately.
                marker = len(self.server.writes)
                output.inspection_completed(True)
                self.wait_for(lambda: (7, 5, 3072, 0xFF00) in self.server.writes[marker:])
                self.wait_for(lambda: (7, 5, 3075, 0) in self.server.writes[marker:])
                self.assertTrue(output.alarm)

    def test_reset_refused_without_connection_or_fresh_inspection(self):
        output = PLCAlarmOutput(self.config)
        with self.assertRaises(RuntimeError):
            output.request_reset()
        output.connected = True
        output.last_inspection = time.monotonic() - 1
        with self.assertRaises(RuntimeError):
            output.request_reset()

    def test_reset_pulse_expires(self):
        with patch("builtins.print"):
            with PLCAlarmOutput(self.config) as output:
                output.inspection_completed(True)
                self.wait_for(lambda: output.connected)
                output.request_reset()
                self.wait_for(lambda: (7, 5, 3075, 0xFF00) in self.server.writes)
                marker = len(self.server.writes)
                self.wait_for(lambda: (7, 5, 3075, 0) in self.server.writes[marker:])
                self.assertFalse(output.alarm)

    def test_camera_confirmation_delivers_alarm_before_evidence_saving(self):
        frame = np.zeros((100, 100, 3), np.uint8)
        mask = np.zeros((100, 100), np.uint8)
        camera = MagicMock()
        camera.__enter__.return_value = camera
        counts = (1, 1, 0, 1, 1, 1, 1)
        camera.read.side_effect = [frame] * len(counts) + [KeyboardInterrupt()]
        with TemporaryDirectory() as directory:
            root = Path(directory)
            config = root / "plc.json"
            config.write_text(json.dumps(vars(self.config)), encoding="utf-8")
            args = SimpleNamespace(plc_config=str(config), camera_index=0, sdk_dir=None,
                                   exposure_us=10000, flip_vertical=False, frame_rate=10,
                                   light_frequency=50, confirm_frames=3, show=False)

            def save_after_delivery(path, image):
                self.wait_for(lambda: (7, 5, 3072, 0xFF00) in self.server.writes)
                return True

            with patch("camera_controller.MindVisionCamera", return_value=camera), \
                 patch.object(main, "TEST_DIR", root / "TestPic"), \
                 patch.object(main, "RESULT_DIR", root / "Results"), \
                 patch.object(main.cv2, "imread", return_value=frame), \
                 patch.object(main.cv2, "imwrite", side_effect=save_after_delivery) as write, \
                 patch.object(main.Detection, "detection", side_effect=[(frame, mask, n) for n in counts]), \
                 patch("builtins.print"):
                main.run_camera(args)
            self.assertEqual(write.call_count, 3)
            self.assertTrue(any(Path(call.args[0]).parent.name == "TestPic" for call in write.call_args_list))
            self.assertEqual(self.server.writes[-1], (7, 5, 3074, 0))

    def test_r_key_requires_clear_frames_and_allows_second_alarm(self):
        frame = np.zeros((100, 100, 3), np.uint8)
        mask = np.zeros((100, 100), np.uint8)
        camera = MagicMock()
        camera.__enter__.return_value = camera
        camera.read.return_value = frame
        plc = MagicMock()
        plc.__enter__.return_value = plc
        counts = (1, 1, 1, 0, 0, 0, 1, 1, 1)
        keys = (-1, -1, ord('r'), -1, -1, ord('R'), -1, -1, ord('q'))
        args = SimpleNamespace(plc_config="unused.json", camera_index=0, sdk_dir=None,
                               exposure_us=10000, flip_vertical=False, frame_rate=10,
                               light_frequency=50, confirm_frames=3, show=True)
        with TemporaryDirectory() as directory, \
             patch("plc_output.PLCConfig.load", return_value=self.config), \
             patch("plc_output.PLCAlarmOutput", return_value=plc), \
             patch("camera_controller.MindVisionCamera", return_value=camera), \
             patch.object(main, "TEST_DIR", Path(directory) / "TestPic"), \
             patch.object(main, "RESULT_DIR", Path(directory) / "Results"), \
             patch.object(main.cv2, "imread", return_value=frame), \
             patch.object(main.cv2, "imwrite", return_value=True) as write, \
             patch.object(main.Detection, "detection", side_effect=[(frame, mask, n) for n in counts]), \
             patch.multiple(main.cv2, namedWindow=MagicMock(), resizeWindow=MagicMock(),
                            imshow=MagicMock(), destroyAllWindows=MagicMock()), \
             patch.object(main.cv2, "waitKey", side_effect=keys), \
             patch("builtins.print"):
            main.run_camera(args)
        plc.request_reset.assert_called_once()
        self.assertEqual(write.call_count, 6)
        self.assertEqual(plc.inspection_completed.call_count, 9)


if __name__ == "__main__":
    unittest.main()
