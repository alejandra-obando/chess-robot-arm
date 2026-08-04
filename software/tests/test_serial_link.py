import json
import time

from chess_arm.serial_link import SerialLink, SerialLinkConfig


class FakeSerial:
    """Stands in for pyserial's Serial so the protocol can be tested without
    a real ESP32 attached."""

    def __init__(self, port, baudrate, timeout):  # noqa: D107 - mirrors pyserial's signature
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.written: list[bytes] = []
        self._lines = [
            (json.dumps({"event": "ready", "board_size": 8}) + "\n").encode(),
            b"not valid json\n",
            (json.dumps({"event": "board", "state": "0" * 64}) + "\n").encode(),
        ]

    def readline(self) -> bytes:
        if self._lines:
            return self._lines.pop(0)
        time.sleep(0.01)
        return b""

    def write(self, data: bytes) -> None:
        self.written.append(data)

    def close(self) -> None:
        pass


def test_reader_thread_parses_events_and_skips_malformed_lines(monkeypatch):
    fake = FakeSerial("COM_TEST", 115200, 1.0)
    monkeypatch.setattr("chess_arm.serial_link.serial.Serial", lambda *a, **k: fake)

    link = SerialLink(SerialLinkConfig(port="COM_TEST"))
    link.connect()
    try:
        ready = link.wait_for_event("ready", timeout=2.0)
        assert ready == {"event": "ready", "board_size": 8}

        board = link.wait_for_event("board", timeout=2.0)
        assert board["state"] == "0" * 64
    finally:
        link.close()


def test_send_command_writes_newline_delimited_json():
    link = SerialLink(SerialLinkConfig(port="COM_TEST"))
    fake = FakeSerial("COM_TEST", 115200, 1.0)
    link._serial = fake  # bypass connect(); no reader thread needed for this check

    link.send_command({"cmd": "ping"})

    assert len(fake.written) == 1
    sent = fake.written[0].decode()
    assert sent.endswith("\n")
    assert json.loads(sent) == {"cmd": "ping"}
