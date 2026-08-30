"""
Signing/verification helpers for the SAGA Provider.

The Provider has its own long-term Ed25519 signing keypair, used to
sign confirmations it issues to users after successful agent
registration (SAGA paper, Section IV-C, step 7).

Users and agents generate their own Ed25519 keypairs client-side and
only ever send the Provider their *public* verify key -- the Provider
never sees a private signing key.
"""
import os
from pathlib import Path

from nacl.exceptions import BadSignatureError
from nacl.signing import SigningKey, VerifyKey

KEY_FILE = Path(os.getenv("PROVIDER_KEY_FILE", "/keys/provider_signing_key.seed"))


def _load_or_create_provider_key() -> SigningKey:
    KEY_FILE.parent.mkdir(parents=True, exist_ok=True)
    if KEY_FILE.exists():
        seed = bytes.fromhex(KEY_FILE.read_text().strip())
        return SigningKey(seed)
    sk = SigningKey.generate()
    KEY_FILE.write_text(sk.encode().hex())
    return sk


_provider_signing_key: SigningKey = _load_or_create_provider_key()
PROVIDER_VERIFY_KEY_HEX = _provider_signing_key.verify_key.encode().hex()


def provider_sign(message: bytes) -> str:
    """Sign a message with the Provider's long-term key. Returns hex signature."""
    return _provider_signing_key.sign(message).signature.hex()


def verify_signature(verify_key_hex: str, message: bytes, signature_hex: str) -> bool:
    """Verify `message` was signed by the holder of `verify_key_hex`."""
    try:
        vk = VerifyKey(bytes.fromhex(verify_key_hex))
        vk.verify(message, bytes.fromhex(signature_hex))
        return True
    except (BadSignatureError, ValueError):
        return False
