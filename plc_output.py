"""Small Modbus TCP coil client and independently serviced PLC alarm channel."""
import json
import socket
import struct
import threading
import time
from dataclasses import dataclass


@dataclass(frozen=True)
class PLCConfig:
    host: str
    alarm_coil: int
    heartbeat_coil: int
    healthy_coil: int
    port: int = 502
    unit_id: int = 1
    timeout: float = 1.0
    heartbeat_interval: float = 0.5
    inspection_timeout: float = 5.0
    reset_coil: int | None = None

    def __post_init__(self):
        if not self.host or not 1 <= self.port <= 65535 or not 0 <= self.unit_id <= 255:
            raise ValueError("Invalid PLC host, port or unit ID")
        addresses = (self.alarm_coil, self.heartbeat_coil, self.healthy_coil)
        if self.reset_coil is not None:
            addresses += (self.reset_coil,)
        if any(type(a) is not int or not 0 <= a <= 65535 for a in addresses):
            raise ValueError("Coil addresses must be zero-based integers between 0 and 65535")
        if len(set(addresses)) != len(addresses):
            raise ValueError("PLC signal coils must be distinct")
        if min(self.timeout, self.heartbeat_interval, self.inspection_timeout) <= 0:
            raise ValueError("PLC timeouts and intervals must be positive")

    @classmethod
    def load(cls, path):
        with open(path, encoding="utf-8-sig") as stream:
            return cls(**json.load(stream))


class ModbusCoilClient:
    """FC05 only. Validate transaction, unit, length, exceptions and echoed write."""
    def __init__(self, config):
        self.config, self.connection, self.transaction = config, None, 0

    def close(self):
        if self.connection is not None:
            self.connection.close()
            self.connection = None

    def _receive(self, size):
        data = bytearray()
        while len(data) < size:
            part = self.connection.recv(size - len(data))
            if not part:
                raise ConnectionError("PLC closed the connection")
            data.extend(part)
        return bytes(data)

    def write_coil(self, address, active):
        stage = "connecting TCP"
        try:
            if self.connection is None:
                self.connection = socket.create_connection(
                    (self.config.host, self.config.port), self.config.timeout)
                self.connection.settimeout(self.config.timeout)
            self.transaction = (self.transaction + 1) & 0xFFFF
            pdu = struct.pack(">BHH", 5, address, 0xFF00 if active else 0)
            header = struct.pack(">HHHB", self.transaction, 0, len(pdu) + 1, self.config.unit_id)
            stage = f"sending coil {address} write"
            self.connection.sendall(header + pdu)
            stage = f"waiting for Modbus response (unit {self.config.unit_id}, coil {address})"
            transaction, protocol, length, unit = struct.unpack(">HHHB", self._receive(7))
            if (transaction != self.transaction or protocol != 0
                    or unit != self.config.unit_id or not 2 <= length <= 254):
                raise ConnectionError("Invalid Modbus TCP response header")
            response = self._receive(length - 1)
            if response[0] == 0x85:
                if len(response) != 2:
                    raise ConnectionError("Malformed Modbus exception response")
                raise ConnectionError(f"PLC rejected coil write: Modbus exception {response[1]}")
            if response != pdu:
                raise ConnectionError("PLC did not acknowledge the requested coil state")
        except OSError as error:
            self.close()
            raise ConnectionError(
                f"{self.config.host}:{self.config.port} {stage}: {error}"
            ) from error
        except Exception:
            self.close()
            raise


class PLCAlarmOutput:
    """Latch confirmed detections; reconnect and resend state after LAN failures.

    PLC ladder owns the physical output, operator reset and watchdog action.
    HEALTHY requires a recent successful inspection, not just a living thread.
    """
    def __init__(self, config):
        self.config = config
        self.client = ModbusCoilClient(config)
        self.lock = threading.Lock()
        self.wake = threading.Event()
        self.stop = threading.Event()
        self.alarm = False
        self.last_inspection = None
        self.connected = False
        self.reset_pending = False
        self.reset_until = 0.0
        self.thread = threading.Thread(target=self._run, name="plc-output", daemon=True)

    def __enter__(self):
        self.thread.start()
        return self

    def inspection_completed(self, alarm_latched):
        with self.lock:
            changed = alarm_latched and not self.alarm
            self.alarm = self.alarm or alarm_latched
            self.last_inspection = time.monotonic()
        if changed:
            self.wake.set()

    def request_reset(self):
        """Queue an operator reset only on a live connection with recent inspection."""
        with self.lock:
            if self.config.reset_coil is None:
                raise RuntimeError("Configure reset_coil and the PLC reset rung first")
            if (not self.connected or self.last_inspection is None or
                    time.monotonic() - self.last_inspection >= self.config.inspection_timeout):
                raise RuntimeError("PLC disconnected or inspection stale; reset refused")
            self.alarm = False
            self.reset_pending = True
        self.wake.set()

    def _run(self):
        heartbeat = False
        failed = False
        try:
            while not self.stop.is_set():
                self.wake.clear()
                with self.lock:
                    alarm = self.alarm
                    healthy = (self.last_inspection is not None and
                               time.monotonic() - self.last_inspection < self.config.inspection_timeout)
                try:
                    # Serialize reset and alarm writes against new detections.
                    if self.config.reset_coil is not None:
                        with self.lock:
                            now = time.monotonic()
                            fresh = (self.last_inspection is not None and
                                     now - self.last_inspection < self.config.inspection_timeout)
                            if self.alarm or not fresh:
                                self.reset_pending = False
                                self.reset_until = 0.0
                            pulse = self.reset_pending or now < self.reset_until
                            # Always clear M0 and publish healthy before raising reset.
                            if pulse:
                                self.client.write_coil(self.config.alarm_coil, False)
                                self.client.write_coil(self.config.healthy_coil, True)
                            self.client.write_coil(self.config.reset_coil, pulse)
                            if self.reset_pending:
                                self.reset_until = time.monotonic() + 1.0
                                self.reset_pending = False
                                print("PLC reset request acknowledged; check PLC alarm/output status.", flush=True)
                            alarm = self.alarm
                    # Send the alarm before health and heartbeat, including on reconnect.
                    self.client.write_coil(self.config.alarm_coil, alarm)
                    self.client.write_coil(self.config.healthy_coil, healthy)
                    heartbeat = not heartbeat
                    self.client.write_coil(self.config.heartbeat_coil, heartbeat)
                    with self.lock:
                        self.connected = True
                    if failed:
                        print("PLC communication restored; current alarm state resent.", flush=True)
                    failed = False
                except (OSError, ConnectionError) as error:
                    with self.lock:
                        self.connected = False
                        self.reset_pending = False
                        self.reset_until = 0.0
                    if not failed:
                        print(f"PLC COMMUNICATION FAULT: {error}; reconnecting. Check PLC watchdog.", flush=True)
                    failed = True
                self.wake.wait(self.config.heartbeat_interval)
            try:
                if self.config.reset_coil is not None:
                    self.client.write_coil(self.config.reset_coil, False)
                self.client.write_coil(self.config.healthy_coil, False)
            except (OSError, ConnectionError):
                pass
        finally:
            self.client.close()

    def __exit__(self, *args):
        self.stop.set()
        self.wake.set()
        self.thread.join(timeout=self.config.timeout * 4 + 2)
        if self.thread.is_alive():
            print("PLC worker is still stopping; PLC watchdog must detect loss of service.", flush=True)
