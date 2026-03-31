"""Dimensões da janela e paleta (configuração estática da UI)."""

from __future__ import annotations


class Window:
    """Tamanho lógico da superfície principal."""

    WIDTH = 720
    HEIGHT = 640


class Colors:
    """Cores RGB usadas na interface."""

    BG = (24, 26, 32)
    PANEL = (40, 44, 56)
    TEXT = (230, 232, 238)
    MUTED = (140, 145, 160)
    ACCENT = (94, 156, 255)
    GRID = (200, 205, 220)
    MARK_X = (255, 120, 120)
    MARK_O = (120, 200, 255)
    ERROR = (255, 140, 140)
    WARNING = (255, 180, 120)
    WHITE = (255, 255, 255)
