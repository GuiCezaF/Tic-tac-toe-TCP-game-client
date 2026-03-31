"""Loop Pygame: orquestra rede, estado e renderização."""

from __future__ import annotations

import socket
from enum import Enum, auto
from typing import Any

import pygame

from tic_tac_toe_client.models.game_model import GameModel
from tic_tac_toe_client.network.client import DEFAULT_PORT, ServerConnection
from tic_tac_toe_client.settings import Colors, Window
from tic_tac_toe_client.ui.renderer import FontSet, UIRenderer
from tic_tac_toe_client.utils.queue_utils import drain_queue


class AppMode(Enum):
    """Telas principais do cliente."""

    MENU = auto()
    PLAY = auto()


class GameApplication:
    """
    Ciclo de vida do cliente: eventos, mensagens TCP e desenho.

    Mantém conexão, modelo de jogo e campos do formulário de menu.
    """

    def __init__(self) -> None:
        self._mode = AppMode.MENU
        self._name_field = "Jogador"
        self._host_field = "127.0.0.1"
        self._field_focus = 0
        self._menu_error: str | None = None
        self._conn: ServerConnection | None = None
        self._model = GameModel()
        self._overlay_message: str | None = None
        self._screen: pygame.Surface | None = None
        self._clock: pygame.time.Clock | None = None
        self._renderer: UIRenderer | None = None

    def run(self) -> None:
        """Inicializa Pygame e executa o loop até fechar a janela."""
        pygame.init()
        pygame.display.set_caption("Tic-Tac-Toe — cliente")
        self._screen = pygame.display.set_mode(
            (Window.WIDTH, Window.HEIGHT),
        )
        self._clock = pygame.time.Clock()
        fonts = FontSet(
            title=pygame.font.Font(None, 48),
            body=pygame.font.Font(None, 32),
            small=pygame.font.Font(None, 26),
        )
        self._renderer = UIRenderer(fonts)

        running = True
        while running:
            running = self._tick()

        if self._conn is not None:
            self._conn.close()
        pygame.quit()

    def _tick(self) -> bool:
        """Um frame: eventos, rede, desenho. Retorna False para sair."""
        assert self._screen is not None
        assert self._clock is not None
        assert self._renderer is not None

        now = pygame.time.get_ticks()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            self._handle_event(event)

        if self._mode is AppMode.PLAY and self._conn is not None:
            self._poll_server_messages(now)

        self._screen.fill(Colors.BG)
        if self._mode is AppMode.MENU:
            self._renderer.draw_menu(
                self._screen,
                self._name_field,
                self._host_field,
                self._field_focus,
                self._menu_error,
                DEFAULT_PORT,
            )
        elif self._mode is AppMode.PLAY:
            if self._conn is not None:
                self._renderer.draw_play(self._screen, self._model)
                if self._model.last_error:
                    self._renderer.draw_error_bar(
                        self._screen,
                        self._model.last_error,
                    )
            if self._overlay_message is not None:
                self._renderer.draw_overlay(
                    self._screen,
                    self._overlay_message,
                )

        pygame.display.flip()
        self._clock.tick(60)
        return True

    def _handle_event(self, event: pygame.event.Event) -> None:
        assert self._renderer is not None

        if self._mode is AppMode.MENU:
            self._handle_menu_event(event)
        elif self._mode is AppMode.PLAY:
            self._handle_play_event(event)

    def _handle_menu_event(self, event: pygame.event.Event) -> None:
        assert self._renderer is not None
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            if self._renderer.connect_button.collidepoint(mx, my):
                self._try_connect()
            elif self._renderer.name_field_rect.collidepoint(mx, my):
                self._field_focus = 0
            elif self._renderer.host_field_rect.collidepoint(mx, my):
                self._field_focus = 1
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_TAB:
                self._field_focus = 1 - self._field_focus
            elif event.key == pygame.K_RETURN:
                self._try_connect()
            elif event.key == pygame.K_BACKSPACE:
                if self._field_focus == 0:
                    self._name_field = self._name_field[:-1]
                else:
                    self._host_field = self._host_field[:-1]
        elif event.type == pygame.TEXTINPUT:
            if self._field_focus == 0:
                self._name_field += event.text
            else:
                self._host_field += event.text

    def _handle_play_event(self, event: pygame.event.Event) -> None:
        assert self._renderer is not None
        if self._overlay_message is not None:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                pos = event.pos
                if self._renderer.overlay_play_again.collidepoint(pos):
                    self._play_again_reconnect()
                elif self._renderer.overlay_menu.collidepoint(pos):
                    self._reset_to_menu()
            return

        if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
            return
        if self._conn is None:
            return
        if not (
            self._model.phase == "playing"
            and self._model.role
            and self._model.current_turn == self._model.role
        ):
            return
        cell = self._renderer.cell_at(event.pos)
        if cell is None:
            return
        row, col = cell
        if self._model.board[row][col] != 0:
            return
        self._conn.send_json({"type": "move", "row": row, "col": col})

    def _poll_server_messages(self, now_ms: int) -> None:
        assert self._conn is not None
        for msg in drain_queue(self._conn.incoming):
            self._apply_server_message(msg, now_ms)
        self._model.clear_error_if_expired(now_ms)
        self._maybe_set_finished_overlay()

    def _apply_server_message(
        self,
        msg: dict[str, Any],
        now_ms: int,
    ) -> None:
        mtype = msg.get("type")
        if mtype == "waiting":
            self._model.waiting_opponent = True
        elif mtype == "game_start":
            self._model.apply_game_start(msg)
        elif mtype == "state":
            self._model.apply_state(msg)
        elif mtype == "error":
            text = str(msg.get("message", "Erro"))
            self._model.flash_error(text, now_ms)
        elif mtype == "opponent_disconnected":
            default = "O outro jogador desconectou."
            self._overlay_message = str(msg.get("message", default))
        elif mtype == "_client" and msg.get("kind") == "disconnected":
            if self._overlay_message is None:
                self._overlay_message = "Conexão encerrada."

    def _maybe_set_finished_overlay(self) -> None:
        if self._overlay_message is not None:
            return
        if self._model.phase != "finished":
            return
        w = self._model.winner
        if w == "draw":
            self._overlay_message = "Empate."
        elif w in ("X", "O"):
            display_name = self._model.winner_name
            if display_name:
                self._overlay_message = f"Vitória de {display_name}!"
            else:
                won = self._model.role == w
                self._overlay_message = (
                    "Você venceu!" if won else f"Vencedor: {w}."
                )
        else:
            self._overlay_message = "Partida encerrada."

    def _reset_to_menu(self) -> None:
        if self._conn is not None:
            self._conn.close()
            drain_queue(self._conn.incoming)
            self._conn = None
        self._model = GameModel()
        self._overlay_message = None
        self._mode = AppMode.MENU
        self._menu_error = None

    def _try_connect(self) -> None:
        self._menu_error = None
        name = self._name_field.strip()
        host = self._host_field.strip()
        if not name:
            self._menu_error = "Informe o nome."
            return
        if not host:
            self._menu_error = "Informe o IP ou host do servidor."
            return
        connection = ServerConnection()
        try:
            connection.connect(host, DEFAULT_PORT, name)
        except (
            TimeoutError,
            socket.gaierror,
            ConnectionRefusedError,
            OSError,
        ) as exc:
            self._menu_error = f"Falha ao conectar: {exc}"
            connection.close()
        else:
            self._conn = connection
            self._model = GameModel()
            self._overlay_message = None
            self._mode = AppMode.PLAY

    def _play_again_reconnect(self) -> None:
        name = self._name_field.strip()
        host = self._host_field.strip()
        if not name or not host:
            self._overlay_message = (
                "Nome ou servidor inválido. Volte ao menu."
            )
            return
        if self._conn is not None:
            self._conn.close()
            drain_queue(self._conn.incoming)
            self._conn = None
        self._model = GameModel()
        self._overlay_message = None
        connection = ServerConnection()
        try:
            connection.connect(host, DEFAULT_PORT, name)
        except (
            TimeoutError,
            socket.gaierror,
            ConnectionRefusedError,
            OSError,
        ) as exc:
            self._overlay_message = f"Falha ao reconectar: {exc}"
            connection.close()
        else:
            self._conn = connection


def run() -> None:
    """Ponto de entrada legível para scripts e testes."""
    GameApplication().run()
