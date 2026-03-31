"""Desenho do menu, tabuleiro e overlay (geometria e pintura juntos)."""

from __future__ import annotations

from dataclasses import dataclass

import pygame

from tic_tac_toe_client.models.game_model import GameModel
from tic_tac_toe_client.settings import Colors, Window


@dataclass(frozen=True)
class FontSet:
    """Fontes carregadas uma vez no ciclo de vida da aplicação."""

    title: pygame.font.Font
    body: pygame.font.Font
    small: pygame.font.Font


class BoardLayout:
    """
    Geometria do tabuleiro 3x3 centralizado.

    Usada para desenhar e para converter clique em (linha, coluna).
    """

    def __init__(self, win_w: int, win_h: int) -> None:
        self._win_w = win_w
        self._win_h = win_h

    def origin_and_side(self) -> tuple[int, int, int]:
        w, h = self._win_w, self._win_h
        side = min(w - 120, h - 200, 420)
        ox = (w - side) // 2
        oy = 100
        return ox, oy, side

    def cell_at_screen(self, pos: tuple[int, int]) -> tuple[int, int] | None:
        mx, my = pos
        ox, oy, side = self.origin_and_side()
        if mx < ox or my < oy or mx >= ox + side or my >= oy + side:
            return None
        cell = side // 3
        col = (mx - ox) // cell
        row = (my - oy) // cell
        if 0 <= row < 3 and 0 <= col < 3:
            return row, col
        return None


class UIRenderer:
    """
    Centraliza retângulos de interface e rotinas de desenho.

    Depende de `FontSet` e das dimensões lógicas da janela.
    """

    MENU_MARGIN_X = 80
    FIELD_WIDTH_OFFSET = 160

    def __init__(self, fonts: FontSet) -> None:
        self._fonts = fonts
        self._w = Window.WIDTH
        self._h = Window.HEIGHT
        self._layout = BoardLayout(self._w, self._h)
        cx = self._w // 2
        field_w = self._w - self.FIELD_WIDTH_OFFSET
        mx = self.MENU_MARGIN_X
        self.connect_button = pygame.Rect(cx - 120, 428, 240, 44)
        self.name_field_rect = pygame.Rect(mx, 208, field_w, 40)
        self.host_field_rect = pygame.Rect(mx, 308, field_w, 40)
        self.overlay_play_again = pygame.Rect(
            cx - 195, self._h // 2 + 28, 180, 44
        )
        self.overlay_menu = pygame.Rect(cx + 15, self._h // 2 + 28, 180, 44)

    def cell_at(self, pos: tuple[int, int]) -> tuple[int, int] | None:
        """Índices (linha, coluna) do clique no tabuleiro, ou None."""
        return self._layout.cell_at_screen(pos)

    def draw_menu(
        self,
        surface: pygame.Surface,
        name_text: str,
        host_text: str,
        field_focus: int,
        menu_error: str | None,
        default_port: int,
    ) -> None:
        """Tela de conexão: nome, host e botão."""
        fonts = self._fonts
        title = fonts.title.render("Conectar", True, Colors.TEXT)
        surface.blit(title, (self._w // 2 - 90, 56))
        hints = (
            "Campos editáveis: clique no nome ou no IP e digite.",
            "Use Tab para alternar entre os campos.",
        )
        for i, hint in enumerate(hints):
            surf = fonts.small.render(hint, True, Colors.MUTED)
            cx = self._w // 2 - surf.get_width() // 2
            surface.blit(surf, (cx, 104 + i * 22))

        mx = self.MENU_MARGIN_X
        surface.blit(
            fonts.small.render("Nome", True, Colors.MUTED),
            (mx, 172),
        )
        surface.blit(
            fonts.small.render("IP ou host do servidor", True, Colors.MUTED),
            (mx, 273),
        )
        port_lbl = f"Porta: {default_port}"
        surface.blit(
            fonts.small.render(port_lbl, True, Colors.MUTED),
            (mx, 363),
        )

        for rect, text, focused in (
            (self.name_field_rect, name_text, field_focus == 0),
            (self.host_field_rect, host_text, field_focus == 1),
        ):
            pygame.draw.rect(surface, Colors.PANEL, rect, border_radius=6)
            if focused:
                pygame.draw.rect(
                    surface, Colors.ACCENT, rect, width=2, border_radius=6
                )
            label = fonts.body.render(text or " ", True, Colors.TEXT)
            surface.blit(label, (rect.x + 10, rect.y + 6))

        pygame.draw.rect(surface, Colors.ACCENT, self.connect_button, border_radius=8)
        lbl = fonts.body.render("Conectar", True, Colors.WHITE)
        surface.blit(lbl, lbl.get_rect(center=self.connect_button.center))

        if menu_error:
            err = fonts.small.render(menu_error, True, Colors.ERROR)
            surface.blit(err, (self.MENU_MARGIN_X, 480))

    def draw_play(
        self,
        surface: pygame.Surface,
        model: GameModel,
    ) -> None:
        """Tabuleiro, status e peças."""
        fonts = self._fonts
        ox, oy, side = self._layout.origin_and_side()
        cell = side // 3

        if model.role is None:
            if model.waiting_opponent:
                status = "Aguardando oponente…"
            else:
                status = "Conectado…"
        elif model.waiting_opponent:
            status = "Aguardando oponente…"
        elif model.phase == "finished":
            status = "Fim de jogo."
        elif model.current_turn == model.role:
            status = "Sua vez."
        else:
            status = "Vez do oponente."

        title = fonts.body.render(status, True, Colors.TEXT)
        tw = self._w // 2 - title.get_width() // 2
        surface.blit(title, (tw, 40))
        if model.role:
            role_txt = f"Você é {model.role}"
            role_s = fonts.small.render(role_txt, True, Colors.MUTED)
            surface.blit(role_s, (self._w // 2 - role_s.get_width() // 2, 72))

        board_rect = pygame.Rect(ox, oy, side, side)
        pygame.draw.rect(surface, Colors.PANEL, board_rect, border_radius=8)

        for i in range(1, 3):
            x = ox + i * cell
            pygame.draw.line(
                surface, Colors.GRID, (x, oy), (x, oy + side), 3
            )
            y = oy + i * cell
            pygame.draw.line(
                surface, Colors.GRID, (ox, y), (ox + side, y), 3
            )

        pad = cell // 10
        for row in range(3):
            for col in range(3):
                mark = model.board[row][col]
                rx = ox + col * cell + pad
                ry = oy + row * cell + pad
                rw = cell - 2 * pad
                if mark == 1:
                    pygame.draw.line(
                        surface,
                        Colors.MARK_X,
                        (rx, ry),
                        (rx + rw, ry + rw),
                        4,
                    )
                    pygame.draw.line(
                        surface,
                        Colors.MARK_X,
                        (rx + rw, ry),
                        (rx, ry + rw),
                        4,
                    )
                elif mark == 2:
                    center = (rx + rw // 2, ry + rw // 2)
                    radius = min(rw, rw) // 2 - 2
                    pygame.draw.circle(
                        surface, Colors.MARK_O, center, radius, 3
                    )

    def draw_error_bar(self, surface: pygame.Surface, message: str) -> None:
        """Barra inferior para erros efêmeros do servidor."""
        bar = self._fonts.small.render(message, True, Colors.WARNING)
        x = self._w // 2 - bar.get_width() // 2
        surface.blit(bar, (x, self._h - 48))

    def draw_overlay(self, surface: pygame.Surface, message: str) -> None:
        """Modal escuro com mensagem e dois botões."""
        fonts = self._fonts
        dim = pygame.Surface((self._w, self._h), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 160))
        surface.blit(dim, (0, 0))

        box = pygame.Rect(self._w // 2 - 240, self._h // 2 - 108, 480, 224)
        pygame.draw.rect(surface, Colors.PANEL, box, border_radius=12)
        pygame.draw.rect(
            surface, Colors.ACCENT, box, width=2, border_radius=12
        )

        msg_s = fonts.body.render(message, True, Colors.TEXT)
        center_y = self._h // 2 - 42
        surface.blit(
            msg_s,
            msg_s.get_rect(center=(self._w // 2, center_y)),
        )

        pygame.draw.rect(
            surface, Colors.ACCENT, self.overlay_play_again, border_radius=8
        )
        pygame.draw.rect(
            surface, Colors.ACCENT, self.overlay_menu, border_radius=8
        )
        pa = fonts.small.render("Jogar novamente", True, Colors.WHITE)
        vm = fonts.small.render("Voltar ao menu", True, Colors.WHITE)
        surface.blit(pa, pa.get_rect(center=self.overlay_play_again.center))
        surface.blit(vm, vm.get_rect(center=self.overlay_menu.center))
