"""Local UI bridge. The existing camera loop remains the sole hardware owner."""
import argparse
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import queue
import re
import socket
import threading
import time
from urllib.parse import urlsplit, parse_qs

import cv2
import main as detector


class VisionHTTPServer(ThreadingHTTPServer):
    """Prevent Windows from allowing two camera services to share one port."""
    allow_reuse_address = False

    def server_bind(self):
        if hasattr(socket, 'SO_EXCLUSIVEADDRUSE'):
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        super().server_bind()


class InspectionService:
    def __init__(self, args):
        self.args = args
        self.lock = threading.RLock()
        self.stop_event = threading.Event()
        self.resets = queue.Queue()
        self.thread = None
        self.state = 'stopped'
        self.error = None
        self.alarm_latched = False
        self.frames = 0
        self.count = 0
        self.clear_frames = 0
        self.last_frame = None
        self.last_tick = None
        self.fps = 0
        self.images = {}
        self.plc = None
        self.dimensions = None

    def start(self):
        with self.lock:
            if self.thread and self.thread.is_alive():
                raise RuntimeError('Inspection is already active or stopping')
            self.stop_event.clear()
            self.images = {}
            self.last_tick = None
            self.clear_frames = 0
            self.state, self.error = 'connecting', None
            self.thread = threading.Thread(target=self._run, daemon=True)
            self.thread.start()

    def _run(self):
        try:
            detector.run_camera(self.args, self)
            with self.lock:
                self.state = 'stopped'
        except Exception as error:
            with self.lock:
                self.state, self.error = 'fault', str(error)
        finally:
            with self.lock:
                self.images = {}
                self.plc = None
            while True:
                try:
                    self.complete_reset(self.resets.get_nowait(), 'Inspection stopped')
                except queue.Empty:
                    break

    def stop(self):
        with self.lock:
            if self.thread and self.thread.is_alive():
                self.state = 'stopping'
                self.stop_event.set()

    def publish(self, raw, annotated, count, alarm, clear_frames, plc):
        # Encoding is bounded to a preview resolution; the detector retains full-size evidence.
        images = {}
        for kind, image in (('raw', raw), ('annotated', annotated)):
            scale = min(1, 1280 / image.shape[1])
            preview = cv2.resize(image, (round(image.shape[1] * scale), round(image.shape[0] * scale)))
            ok, encoded = cv2.imencode('.jpg', preview, [cv2.IMWRITE_JPEG_QUALITY, 80])
            if not ok:
                raise OSError('Preview encoding failed')
            images[kind] = encoded.tobytes()
        now = time.monotonic()
        with self.lock:
            self.fps = 1 / (now - self.last_tick) if self.last_tick else 0
            self.last_tick = now
            self.last_frame = datetime.now(timezone.utc).isoformat()
            self.frames += 1
            self.count, self.alarm_latched, self.clear_frames = count, alarm, clear_frames
            self.images, self.plc = images, plc
            self.dimensions = [raw.shape[1], raw.shape[0]]
            if not self.stop_event.is_set():
                self.state = 'running'
            try:
                return self.resets.get_nowait()
            except queue.Empty:
                return None

    def complete_reset(self, request, error):
        with self.lock:
            if error is None:
                self.alarm_latched = False
            request['error'] = error
            request['done'].set()

    def reset(self):
        with self.lock:
            if not self.status()['reset_eligible']:
                raise RuntimeError('Reset unavailable: inspection must be live with consecutive clear frames and PLC ready')
            request = {'done': threading.Event(), 'error': None}
            self.resets.put(request)
        # A timeout does not imply cancellation; report pending rather than a false refusal.
        if not request['done'].wait(10):
            return 'Reset queued; waiting for inspection'
        if request['error']:
            raise RuntimeError(request['error'])
        return 'Software alarm reset; PLC reset request queued' if self.args.plc_config else 'Software alarm reset'

    def status(self):
        with self.lock:
            stale = self.last_tick is None or time.monotonic() - self.last_tick >= 5
            connected = False
            plc_ready = not self.args.plc_config
            if self.plc is not None:
                with self.plc.lock:
                    connected = self.plc.connected
                    plc_ready = connected and self.plc.config.reset_coil is not None
            return dict(state=self.state, error=self.error, stale=stale,
                        alarm_latched=self.alarm_latched, frames=self.frames,
                        object_count=self.count, clear_frames=self.clear_frames,
                        confirm_frames=self.args.confirm_frames,
                        reset_eligible=self.state == 'running' and not stale and plc_ready
                        and self.clear_frames >= self.args.confirm_frames,
                        fps=round(self.fps, 1), last_frame=self.last_frame,
                        dimensions=self.dimensions, camera_index=self.args.camera_index,
                        plc_enabled=bool(self.args.plc_config), plc_connected=connected)

    def image(self, kind):
        with self.lock:
            if self.state != 'running' or self.status()['stale']:
                raise RuntimeError('No live camera frame')
            return self.images[kind]


def evidence_path(event, kind):
    if not re.fullmatch(r'alarm_\d{8}_\d{6}_\d{6}', event):
        raise ValueError('Invalid event ID')
    if kind not in ('raw', 'detection', 'mask'):
        raise ValueError('Invalid evidence kind')
    folder = detector.TEST_DIR if kind == 'raw' else detector.RESULT_DIR
    return folder / f'{event}_{kind}.png'


def events():
    records = []
    for path in sorted(detector.RESULT_DIR.glob('alarm_*_detection.png'), reverse=True)[:100]:
        event = path.name.removesuffix('_detection.png')
        try:
            evidence_path(event, 'detection')
            stamp = datetime.strptime(event, 'alarm_%Y%m%d_%H%M%S_%f').isoformat()
        except ValueError:
            continue
        records.append(dict(id=event, time=stamp, evidence={
            kind: f'/api/evidence/{event}/{kind}' for kind in ('raw', 'detection', 'mask')
            if evidence_path(event, kind).is_file()}))
    return records


def make_handler(service):
    class Handler(BaseHTTPRequestHandler):
        def respond(self, status, body, content_type='application/json'):
            if content_type == 'application/json':
                body = json.dumps(body).encode()
            self.send_response(status)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Length', str(len(body)))
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            url = urlsplit(self.path)
            try:
                if url.path == '/api/status':
                    return self.respond(200, service.status())
                if url.path == '/api/events':
                    return self.respond(200, events())
                if url.path == '/api/preview':
                    kind = parse_qs(url.query).get('kind', ['annotated'])[0]
                    if kind not in ('raw', 'annotated'):
                        raise ValueError('Invalid preview kind')
                    return self.respond(200, service.image(kind), 'image/jpeg')
                if url.path.startswith('/api/evidence/'):
                    parts = url.path.split('/')
                    if len(parts) != 5:
                        raise ValueError('Invalid evidence URL')
                    return self.respond(200, evidence_path(parts[3], parts[4]).read_bytes(), 'image/png')
                if url.path.startswith('/api/'):
                    return self.respond(404, {'error': 'Unknown endpoint'})
                root = (detector.BASE_DIR / 'UI' / 'dist').resolve()
                target = (root / url.path.lstrip('/')).resolve()
                if not target.is_relative_to(root):
                    raise ValueError('Invalid path')
                if not target.is_file():
                    target = root / 'index.html'
                import mimetypes
                return self.respond(200, target.read_bytes(), mimetypes.guess_type(target.name)[0] or 'application/octet-stream')
            except FileNotFoundError:
                self.respond(404, {'error': 'File unavailable. Build UI with pnpm build first.'})
            except (ValueError, RuntimeError) as error:
                self.respond(409, {'error': str(error)})

        def do_POST(self):
            # Only the local same-origin UI may issue hardware commands.
            origin = self.headers.get('Origin')
            host = self.headers.get('Host', '')
            if host not in (f'127.0.0.1:{self.server.server_port}', f'localhost:{self.server.server_port}'):
                return self.respond(403, {'error': 'Local host required'})
            if origin and origin not in (f'http://{host}', 'http://localhost:8443', 'http://127.0.0.1:8443'):
                return self.respond(403, {'error': 'Origin refused'})
            if self.headers.get('X-Vision-Control') != '1':
                return self.respond(403, {'error': 'Control header required'})
            try:
                command = self.path
                if command == '/api/start':
                    service.start()
                    message = 'Inspection starting'
                elif command == '/api/stop':
                    service.stop()
                    message = 'Inspection stopping'
                elif command == '/api/reset':
                    message = service.reset()
                else:
                    return self.respond(404, {'error': 'Unknown command'})
                self.respond(200, {'message': message, 'status': service.status()})
            except RuntimeError as error:
                self.respond(409, {'error': str(error)})

        def log_message(self, *_):
            pass
    return Handler


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8765)
    parser.add_argument('--camera-index', type=int, default=0)
    parser.add_argument('--sdk-dir')
    parser.add_argument('--frame-rate', type=int, default=10)
    parser.add_argument('--light-frequency', type=int, choices=(50, 60), default=50)
    parser.add_argument('--flip-vertical', action='store_true')
    parser.add_argument('--confirm-frames', type=int, default=3)
    parser.add_argument('--plc-config')
    args = parser.parse_args()
    if args.confirm_frames < 1 or args.frame_rate < 1:
        parser.error('Frame rate and confirmation frames must be positive')
    args.exposure_us, args.show = 10000, False
    service = InspectionService(args)
    try:
        server = VisionHTTPServer(('127.0.0.1', args.port), make_handler(service))
    except OSError as error:
        parser.exit(1, f'Cannot open port {args.port}: {error}. Close the existing vision server before starting another.\n')
    print(f'Vision UI: http://127.0.0.1:{args.port} (click Start inspection to open camera)', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        service.stop()
        if service.thread:
            service.thread.join(timeout=15)
        server.server_close()


if __name__ == '__main__':
    main()
