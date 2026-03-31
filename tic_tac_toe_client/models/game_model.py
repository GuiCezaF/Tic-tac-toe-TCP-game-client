"""Estado da partida espelhando mensagens do servidor."""

from __future__ import annotations

from typing import Any


class GameModel:
    """
    Estado local da partida atualizado a partir das mensagens do servidor.

    `apply_game_start` e `apply_state` mantêm tabuleiro e metadados alinhados
    ao protocolo (`winner_name` quando o servidor envia); `flash_error` exibe
    feedback temporário na barra inferior.
    """

    def __init__(self) -> None:
        self.role: str | None = None
        self.waiting_opponent = False
        self.board: list[list[int]] = [
            [0, 0, 0],
            [0, 0, 0],
            [0, 0, 0],
        ]
        self.current_turn: str | None = "X"
        self.phase: str = "playing"
        self.winner: str | None = None
        # Nome do vencedor (`join`), só nas mensagens `state` com vencedor X/O.
        self.winner_name: str | None = None
        self.last_error: str | None = None
        self.error_until_ms: int = 0

    def apply_game_start(self, msg: dict[str, Any]) -> None:
        self.role = str(msg.get("role", ""))
        state = msg.get("state") or {}
        self._apply_state_dict(state)
        self.waiting_opponent = False

    def apply_state(self, msg: dict[str, Any]) -> None:
        self._apply_state_dict(msg)

    def _apply_state_dict(self, state: dict[str, Any]) -> None:
        board = state.get("board")
        if isinstance(board, list) and len(board) == 3:
            self.board = [
                [
                    int(c) if isinstance(c, (int, float)) else 0
                    for c in row
                ]
                for row in board
            ]
        turn = state.get("current_turn")
        if turn is None or turn in ("X", "O"):
            self.current_turn = turn
        phase = state.get("phase")
        if phase in ("playing", "finished"):
            self.phase = phase
        if "winner" in state:
            w = state.get("winner")
            self.winner = str(w) if w is not None else None
        if "winner_name" in state:
            raw = state.get("winner_name")
            self.winner_name = str(raw) if raw is not None else None
        else:
            self.winner_name = None

    def flash_error(
        self,
        message: str,
        now_ms: int,
        duration_ms: int = 3500,
    ) -> None:
        self.last_error = message
        self.error_until_ms = now_ms + duration_ms

    def clear_error_if_expired(self, now_ms: int) -> None:
        if self.last_error and now_ms >= self.error_until_ms:
            self.last_error = None
