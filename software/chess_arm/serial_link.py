"""Serial transport to the ESP32.

Speaks the newline-delimited JSON protocol described in docs/protocol.md:
each line sent or received is a single JSON object. Reading happens on a
background thread so the caller never blocks waiting on the board scan
while it also wants to send a move.
"""

from __future__ import annotations

import json
import logging
import queue
import threading
import time
from dataclasses import dataclass
from typing import Any

import serial

logger = logging.getLogger(__name__)


@dataclass
class SerialLinkConfig:
    port: str
    baudrate: int = 115200
    timeout: float = 1.0


class SerialLink:
    def __init__(self, config: SerialLinkConfig):
        self._config = config
        self._serial: serial.Serial | None = None
        self._events: queue.Queue[dict[str, Any]] = queue.Queue()
        self._reader_thread: threading.Thread | None = None
        self._stop = threading.Event()

    def connect(self) -> None:
        self._serial = serial.Serial(
            self._config.port, self._config.baudrate, timeout=self._config.timeout
        )
        self._stop.clear()
        self._reader_thread = threading.Thread(target=self._read_loop, daemon=True)
        self._reader_thread.start()
        logger.info("Connected to %s @ %d baud", self._config.port, self._config.baudrate)

    def close(self) -> None:
        self._stop.set()
        if self._reader_thread is not None:
            self._reader_thread.join(timeout=2.0)
        if self._serial is not None:
            self._serial.close()

    def __enter__(self) -> "SerialLink":
        self.connect()
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()

    def send_command(self, command: dict[str, Any]) -> None:
        if self._serial is None:
            raise RuntimeError("SerialLink is not connected")
        payload = json.dumps(command) + "\n"
        self._serial.write(payload.encode("utf-8"))
        logger.debug("-> %s", command)

    def get_event(self, timeout: float | None = None) -> dict[str, Any] | None:
        """Returns the next event from the ESP32, or None on timeout."""
        try:
            return self._events.get(timeout=timeout)
        except queue.Empty:
            return None

    def wait_for_event(self, event_type: str, timeout: float = 5.0) -> dict[str, Any] | None:
        """Drains events until one of `event_type` arrives, or timeout expires."""
        start = time.monotonic()
        remaining = timeout
        while remaining > 0:
            event = self.get_event(timeout=remaining)
            if event is None:
                return None
            if event.get("event") == event_type:
                return event
            remaining = timeout - (time.monotonic() - start)
        return None

    def _read_loop(self) -> None:
        assert self._serial is not None
        while not self._stop.is_set():
            try:
                raw = self._serial.readline()
            except serial.SerialException:
                logger.exception("Serial read failed, stopping reader thread")
                return
            if not raw:
                continue
            line = raw.decode("utf-8", errors="replace").strip()
            if not line:
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                logger.warning("Dropping malformed line from ESP32: %r", line)
                continue
            logger.debug("<- %s", event)
            self._events.put(event)
