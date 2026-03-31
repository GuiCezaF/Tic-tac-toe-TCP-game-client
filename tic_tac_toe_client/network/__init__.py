"""Cliente TCP e serialização NDJSON alinhada ao servidor."""

from tic_tac_toe_client.network.client import (
    DEFAULT_PORT,
    ServerConnection,
    encode_line,
)

__all__ = ["DEFAULT_PORT", "ServerConnection", "encode_line"]
