"""
Loads this agent's identity from the key file `seed_data.py` produced on
the Provider side (mounted read-only into this container).

Also tracks which of our own one-time keys (OTKs) have been consumed to
issue a token, in memory. This resets on container restart -- a known MVP
limitation: an OTK could theoretically be reused for a short window after
a restart. Worth persisting to disk/Mongo before this goes anywhere real.
"""
import json

from nacl.public import PrivateKey
from nacl.signing import SigningKey

from . import config


class AgentIdentity:
    def __init__(self, data: dict):
        self.aid = data["aid"]
        self.device = data.get("device")
        self.ip = data.get("ip")
        self.port = data.get("port")
        self.provider_signature_hex = data.get("provider_signature_hex")

        self.signing_key = SigningKey(bytes.fromhex(data["signing_key_seed_hex"]))
        self.pac_private = PrivateKey(bytes.fromhex(data["pac_private_hex"]))
        self.pac_public_hex = bytes(self.pac_private.public_key).hex()

        self._otk_privates: dict[str, PrivateKey] = {}
        for h in data.get("otk_private_hexes", []):
            priv = PrivateKey(bytes.fromhex(h))
            self._otk_privates[bytes(priv.public_key).hex()] = priv
        self._used_otks: set[str] = set()

    def take_otk_private(self, otk_hex: str) -> PrivateKey | None:
        """Consume one of our own OTKs by its public hex. Returns None if
        unknown or already used -- caller should reject the request."""
        if otk_hex in self._used_otks:
            return None
        priv = self._otk_privates.get(otk_hex)
        if priv is None:
            return None
        self._used_otks.add(otk_hex)
        return priv


def load_identity() -> AgentIdentity:
    if not config.KEY_FILE.exists():
        raise FileNotFoundError(
            f"No key file at {config.KEY_FILE} -- run seed_data.py against the Provider "
            f"first, then mount its seed-keys/ directory into this container."
        )
    data = json.loads(config.KEY_FILE.read_text())
    identity = AgentIdentity(data)
    if not identity.provider_signature_hex:
        raise ValueError(
            f"Key file for {identity.aid} has no provider_signature_hex. Wipe the Provider's "
            f"data (docker compose down -v) and re-run seed_data.py -- it now saves this field."
        )
    return identity
