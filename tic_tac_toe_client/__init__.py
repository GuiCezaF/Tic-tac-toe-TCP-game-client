"""
Cliente Pygame para o servidor Tic-Tac-Toe (TCP / NDJSON).

Camadas: `application` (loop), `models` (estado), `network` (socket),
`ui` (renderização), `utils`, `settings`.
"""

from tic_tac_toe_client.application.game_app import GameApplication, run

__all__ = ["GameApplication", "run"]
