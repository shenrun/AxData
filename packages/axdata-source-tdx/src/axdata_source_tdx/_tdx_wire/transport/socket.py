"""Synchronous 7709 socket transport."""

from __future__ import annotations

from collections.abc import Sequence
from importlib import import_module
from typing import TYPE_CHECKING, Any

from axdata_source_tdx._tdx_wire._connection_defaults import DEFAULT_HEARTBEAT_INTERVAL
from axdata_source_tdx._tdx_wire._host_utils import unique_hosts

if TYPE_CHECKING:
    from axdata_source_tdx._tdx_wire.protocol.frame import ResponseFrame

_FRAME_EXPORTS = {"ResponseFrame", "decode_response", "read_response_frame"}
_EXCEPTION_EXPORTS = {"ConnectionClosedError", "ProtocolError", "ResponseTimeoutError", "TransportError"}
_SESSION_COMMAND_EXPORTS = {"TYPE_HANDSHAKE", "TYPE_HEARTBEAT"}
_STDLIB_EXPORTS = {"Empty", "Queue", "socket", "threading"}
__all__ = [
    "Any",
    "ConnectionClosedError",
    "DEFAULT_HEARTBEAT_INTERVAL",
    "Empty",
    "ProtocolError",
    "Queue",
    "ResponseTimeoutError",
    "Sequence",
    "SocketTransport",
    "TYPE_CHECKING",
    "TYPE_HANDSHAKE",
    "TYPE_HEARTBEAT",
    "TransportError",
    "import_module",
    "socket",
    "threading",
    "unique_hosts",
]


class SocketTransport:
    """Real TCP transport for the 7709 quote protocol.

    The public API is still request/response, but reads are handled by a
    background reader so unmatched push frames do not break ordinary requests.
    """

    def __init__(
        self,
        hosts: Sequence[str] | None = None,
        *,
        timeout: float = 8.0,
        heartbeat_interval: float | None = DEFAULT_HEARTBEAT_INTERVAL,
    ) -> None:
        self._hosts = _resolve_hosts(hosts)
        if not self._hosts:
            raise ValueError("at least one host is required")
        self._timeout = timeout
        self._heartbeat_interval = heartbeat_interval
        self._socket: socket.socket | None = None
        self._connected_host: str | None = None
        self._msg_id = 1
        threading_module = _threading_module()
        queue_cls, _ = _queue_exports()
        self._lock = threading_module.RLock()
        self._send_lock = threading_module.Lock()
        self._pending_lock = threading_module.Lock()
        self._pending: dict[tuple[int, int], Queue[ResponseFrame | BaseException]] = {}
        self._push_queue: Queue[ResponseFrame] = queue_cls()
        self._stop_reader = threading_module.Event()
        self._stop_heartbeat = threading_module.Event()
        self._reader_thread: threading.Thread | None = None
        self._heartbeat_thread: threading.Thread | None = None
        self._reader_error: BaseException | None = None
        self._handshaken = False
        self.last_handshake: Any = None
        self.last_heartbeat: Any = None

    @property
    def connected_host(self) -> str | None:
        return self._connected_host

    def connect(self) -> None:
        with self._lock:
            self._ensure_socket()

    def close(self) -> None:
        with self._lock:
            self._close_socket()
            self._handshaken = False

    def execute(self, command: int, payload: dict[str, Any] | None = None) -> Any:
        connection_closed_error, protocol_error, response_timeout_error, transport_error = _wire_exceptions()
        request_payload = dict(payload or {})
        with self._lock:
            try:
                return self._execute_locked(command, request_payload)
            except (OSError, connection_closed_error, response_timeout_error) as exc:
                self._close_socket()
                try:
                    return self._execute_locked(command, request_payload)
                except response_timeout_error:
                    raise
                except (OSError, connection_closed_error) as retry_exc:
                    raise transport_error(f"7709 request failed: 0x{command:04x}") from retry_exc
            except protocol_error:
                raise

    def request(self, command: str) -> str:
        if command == "ping":
            return "pong"
        raise ValueError(f"unsupported command: {command}")

    def _execute_locked(self, command: int, payload: dict[str, Any]) -> Any:
        self._ensure_socket()
        handshake_command, heartbeat_command = _session_command_codes()
        if command != handshake_command and not self._handshaken:
            self.last_handshake = self._request_locked(handshake_command, {})
            self._handshaken = True

        result = self._request_locked(command, payload)
        if command == handshake_command:
            self.last_handshake = result
            self._handshaken = True
        elif command == heartbeat_command:
            self.last_heartbeat = result
        return result

    def _request_locked(self, command: int, payload: dict[str, Any]) -> Any:
        from axdata_source_tdx._tdx_wire._command_codec import build_command_frame, parse_command_response

        _, _, response_timeout_error, _ = _wire_exceptions()
        queue_cls, empty_error = _queue_exports()
        frame = build_command_frame(command, payload, self._next_msg_id())
        response_queue: Queue[ResponseFrame | BaseException] = queue_cls(maxsize=1)
        key = (frame.msg_id, frame.msg_type)
        with self._pending_lock:
            self._pending[key] = response_queue

        assert self._socket is not None
        try:
            with self._send_lock:
                self._socket.sendall(frame.to_bytes())
            try:
                response_or_error = response_queue.get(timeout=self._timeout)
            except empty_error as exc:
                raise response_timeout_error(f"7709 response timed out: 0x{command:04x}") from exc
            if isinstance(response_or_error, BaseException):
                raise response_or_error
            return parse_command_response(command, response_or_error, payload)
        finally:
            with self._pending_lock:
                self._pending.pop(key, None)

    def _read_response_locked(self) -> ResponseFrame:
        from axdata_source_tdx._tdx_wire.protocol.frame import decode_response, read_response_frame

        assert self._socket is not None
        raw = read_response_frame(self._socket)
        return decode_response(raw)

    def _ensure_socket(self) -> None:
        if self._socket is not None:
            reader_alive = self._reader_thread is not None and self._reader_thread.is_alive()
            if self._reader_error is None and reader_alive:
                return
            self._close_socket()

        last_error: OSError | None = None
        socket_module = _socket_module()
        for host in self._hosts:
            address, port_text = host.rsplit(":", 1)
            try:
                sock = socket_module.create_connection((address, int(port_text)), timeout=self._timeout)
                sock.settimeout(self._timeout)
            except OSError as exc:
                last_error = exc
                continue
            self._socket = sock
            self._connected_host = host
            self._reader_error = None
            self._stop_reader.clear()
            self._stop_heartbeat.clear()
            self._start_reader_locked()
            self._start_heartbeat_locked()
            return
        connection_closed_error, _, _, _ = _wire_exceptions()
        raise connection_closed_error("unable to connect to any 7709 host") from last_error

    def _close_socket(self) -> None:
        connection_closed_error, _, _, _ = _wire_exceptions()
        self._stop_reader.set()
        self._stop_heartbeat.set()
        if self._socket is not None:
            try:
                self._socket.close()
            finally:
                self._socket = None
                self._connected_host = None
                self._handshaken = False
        threading_module = _threading_module()
        if self._reader_thread is not None and self._reader_thread is not threading_module.current_thread():
            self._reader_thread.join(timeout=0.2)
        self._reader_thread = None
        if self._heartbeat_thread is not None and self._heartbeat_thread is not threading_module.current_thread():
            self._heartbeat_thread.join(timeout=0.2)
        self._heartbeat_thread = None
        self._fail_pending(connection_closed_error("socket closed"))

    def _next_msg_id(self) -> int:
        value = self._msg_id
        self._msg_id = 1 if self._msg_id >= 0xFFFFFFFF else self._msg_id + 1
        return value

    def _start_reader_locked(self) -> None:
        if self._reader_thread is not None and self._reader_thread.is_alive():
            return
        thread = _threading_module().Thread(
            target=self._reader_loop,
            name="axdata_source_tdx._tdx_wire-7709-reader",
            daemon=True,
        )
        self._reader_thread = thread
        thread.start()

    def _start_heartbeat_locked(self) -> None:
        if self._heartbeat_interval is None or self._heartbeat_interval <= 0:
            return
        if self._heartbeat_thread is not None and self._heartbeat_thread.is_alive():
            return
        thread = _threading_module().Thread(
            target=self._heartbeat_loop,
            name="axdata_source_tdx._tdx_wire-7709-heartbeat",
            daemon=True,
        )
        self._heartbeat_thread = thread
        thread.start()

    def _heartbeat_loop(self) -> None:
        assert self._heartbeat_interval is not None
        _, heartbeat_command = _session_command_codes()
        while not self._stop_heartbeat.wait(self._heartbeat_interval):
            try:
                self.execute(heartbeat_command, {})
            except BaseException as exc:
                if not self._stop_heartbeat.is_set():
                    self._reader_error = exc
                    self._close_socket()
                return

    def _reader_loop(self) -> None:
        connection_closed_error, _, response_timeout_error, _ = _wire_exceptions()
        socket_module = _socket_module()
        while not self._stop_reader.is_set():
            try:
                response = self._read_response_locked()
            except (socket_module.timeout, TimeoutError, response_timeout_error):
                continue
            except (OSError, connection_closed_error) as exc:
                if not self._stop_reader.is_set():
                    self._reader_error = exc
                    error = connection_closed_error("7709 reader stopped")
                    error.__cause__ = exc
                    self._fail_pending(error)
                return
            except BaseException as exc:
                self._reader_error = exc
                self._fail_pending(exc)
                return
            self._route_response(response)

    def _route_response(self, response: ResponseFrame) -> None:
        _, protocol_error, _, _ = _wire_exceptions()
        key = (response.msg_id, response.msg_type)
        with self._pending_lock:
            pending = self._pending.get(key)
        if pending is not None:
            pending.put(response)
            return

        _, heartbeat_command = _session_command_codes()
        if response.msg_type == heartbeat_command:
            try:
                from axdata_source_tdx._tdx_wire._command_codec import parse_command_response

                self.last_heartbeat = parse_command_response(heartbeat_command, response, {})
            except protocol_error:
                self._push_queue.put(response)
            return

        self._push_queue.put(response)

    def _fail_pending(self, exc: BaseException) -> None:
        with self._pending_lock:
            queues = list(self._pending.values())
            self._pending.clear()
        for response_queue in queues:
            try:
                response_queue.put_nowait(exc)
            except Exception:
                pass


def _resolve_hosts(hosts: Sequence[str] | None) -> list[str]:
    if hosts:
        return unique_hosts(list(hosts))

    from axdata_source_tdx._tdx_wire._host_resource import DEFAULT_HOSTS

    return unique_hosts(list(DEFAULT_HOSTS))


def _session_command_codes() -> tuple[int, int]:
    from axdata_source_tdx._tdx_wire._command_codes import TYPE_HANDSHAKE, TYPE_HEARTBEAT

    globals()["TYPE_HANDSHAKE"] = TYPE_HANDSHAKE
    globals()["TYPE_HEARTBEAT"] = TYPE_HEARTBEAT
    return TYPE_HANDSHAKE, TYPE_HEARTBEAT


def _wire_exceptions() -> tuple[type[BaseException], type[BaseException], type[BaseException], type[BaseException]]:
    from axdata_source_tdx._tdx_wire.exceptions import (
        ConnectionClosedError,
        ProtocolError,
        ResponseTimeoutError,
        TransportError,
    )

    globals()["ConnectionClosedError"] = ConnectionClosedError
    globals()["ProtocolError"] = ProtocolError
    globals()["ResponseTimeoutError"] = ResponseTimeoutError
    globals()["TransportError"] = TransportError
    return ConnectionClosedError, ProtocolError, ResponseTimeoutError, TransportError


def _queue_exports():
    module = import_module("queue")
    globals()["Empty"] = module.Empty
    globals()["Queue"] = module.Queue
    return module.Queue, module.Empty


def _socket_module():
    module = import_module("socket")
    globals()["socket"] = module
    return module


def _threading_module():
    module = import_module("threading")
    globals()["threading"] = module
    return module


def __getattr__(name: str) -> Any:
    if name == "socket":
        return _socket_module()
    if name == "threading":
        return _threading_module()
    if name in {"Empty", "Queue"}:
        _queue_exports()
        return globals()[name]
    if name in _EXCEPTION_EXPORTS:
        _wire_exceptions()
        return globals()[name]
    if name in _SESSION_COMMAND_EXPORTS:
        _session_command_codes()
        return globals()[name]
    if name not in _FRAME_EXPORTS:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module = import_module("axdata_source_tdx._tdx_wire.protocol.frame")
    value = getattr(module, name)
    globals()[name] = value
    return value
