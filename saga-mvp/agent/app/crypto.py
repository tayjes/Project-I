"""
Crypto helpers for the agent-to-agent handshake (SAGA paper, Section IV-E,
steps 3-7).

canonical_agent_info() MUST exactly match the Provider's version
(saga-provider/app/main.py) -- it's what the Provider's signature actually
covers, so any drift here breaks signature verification.
"""
import json
import time
import uuid

from nacl.exceptions import BadSignatureError, CryptoError
from nacl.public import Box, PrivateKey, PublicKey
from nacl.signing import VerifyKey

from . import config


def canonical_agent_info(aid: str, device: str, ip: str, port: int, pac_hex: str) -> bytes:
    payload = {"aid": aid, "device": device, "ip": ip, "port": port, "pac": pac_hex}
    return json.dumps(payload, sort_keys=True).encode()


def verify_provider_signature(
    provider_verify_key_hex: str, aid: str, device: str, ip: str, port: int, pac_hex: str, signature_hex: str
) -> bool:
    info = canonical_agent_info(aid, device, ip, port, pac_hex)
    try:
        VerifyKey(bytes.fromhex(provider_verify_key_hex)).verify(info, bytes.fromhex(signature_hex))
        return True
    except (BadSignatureError, ValueError):
        return False


def make_box(my_private: PrivateKey, their_public_hex: str) -> Box:
    """
    NaCl's Box computes the X25519 shared secret from (my_private,
    their_public) and both sides derive the *same* shared key: A's
    Box(SOTK_A, PAC_B) and B's Box(SAC_B, OTK_A) agree, because X25519 is
    symmetric (a*B == b*A). This single call does what the paper describes
    as "DH exchange, then KDF, then symmetric encryption" -- Box handles
    all three steps together.
    """
    return Box(my_private, PublicKey(bytes.fromhex(their_public_hex)))


def build_token(initiator_aid: str) -> dict:
    now = time.time()
    return {
        "token_id": uuid.uuid4().hex,
        "initiator_aid": initiator_aid,
        "issued_at": now,
        "expires_at": now + config.TOKEN_LIFETIME_SECONDS,
        "qmax": config.TOKEN_MAX_REQUESTS,
    }


def encrypt_token(box: Box, token: dict) -> str:
    return box.encrypt(json.dumps(token).encode()).hex()


def decrypt_token(box: Box, token_hex: str) -> dict:
    plaintext = box.decrypt(bytes.fromhex(token_hex))
    return json.loads(plaintext)
