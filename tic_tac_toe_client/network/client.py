"""Sessão TCP: uma linha JSON UTF-8 por mensagem (NDJSON)."""

from __future__ import annotations

import json
import queue
import socket
import threading
from typing import Any

# Porta padrão do servidor (TICTACTOE_PORT).
DEFAULT_PORT = 5001


def encode_line(payload: dict[str, Any]) -> bytes:
    """Serializa um objeto como uma linha NDJSON (newline final)."""
    raw = json.dumps(payload, separators=(",", ":"), ensure_ascii=False)
    return (raw + "\n").encode("utf-8")


class ServerConnection:
    """
    Mantém um socket TCP ao servidor e uma fila de mensagens recebidas.

    O construtor deixa o objeto inativo até `connect`. Após conectar, uma thread
    em segundo plano lê linhas NDJSON e coloca dicionários em `incoming`;
    o envio usa lock para não intercalar writes. Chame `close` ao sair para
    liberar o socket e parar a leitura.
    """

    def __init__(self) -> None:
        self._sock: socket.socket | None = None
        self._send_lock = threading.Lock()
        self.incoming: queue.Queue[dict[str, Any]] = queue.Queue()
        self._stop = threading.Event()
        self._reader_thread: threading.Thread | None = None

    def connect(
        self,
        host: str,
        port: int,
        name: str,
        timeout: float = 10.0,
    ) -> None:
        """Abre TCP, inicia leitura em thread e envia `join` (bloqueante)."""
        self.close()
        self._stop.clear()
        sock = socket.create_connection((host, port), timeout=timeout)
        sock.settimeout(None)
        self._sock = sock
        self._reader_thread = threading.Thread(
            target=self._read_loop,
            daemon=True,
        )
        self._reader_thread.start()
        self.send_json({"type": "join", "name": name})

    def _read_loop(self) -> None:
        buffer = b""
        sock = self._sock
        if sock is None:
            return
        try:
            while not self._stop.is_set():
                chunk = sock.recv(65536)
                if not chunk:
                    break
                buffer += chunk
                while True:
                    idx = buffer.find(b"\n")
                    if idx < 0:
                        break
                    line = buffer[:idx]
                    buffer = buffer[idx + 1 :]
                    stripped = line.strip()
                    if not stripped:
                        continue
                    try:
                        obj = json.loads(stripped.decode("utf-8"))
                    except (json.JSONDecodeError, UnicodeDecodeError):
                        continue
                    if isinstance(obj, dict):
                        self.incoming.put(obj)
        except OSError:
            pass
        finally:
            self.incoming.put({"type": "_client", "kind": "disconnected"})

    def send_json(self, payload: dict[str, Any]) -> None:
        """Envia uma mensagem; ignorado se o socket já foi fechado."""
        with self._send_lock:
            if self._sock is None:
                return
            self._sock.sendall(encode_line(payload))

    def close(self) -> None:
        """Encerra leitura e fecha o socket."""
        self._stop.set()
        with self._send_lock:
            if self._sock is not None:
                try:
                    self._sock.shutdown(socket.SHUT_RDWR)
                except OSError:
                    pass
                try:
                    self._sock.close()
                except OSError:
                    pass
                self._sock = None
