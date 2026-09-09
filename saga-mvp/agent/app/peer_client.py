"""
Functions for acting as the *initiating* agent: get a session with a peer
(via the Provider, then a direct handshake with the peer), and send task
messages over that session (SAGA paper, Section IV-E, steps 2-8).
"""
import httpx

from . import crypto, provider_client, session_store
from .keys import AgentIdentity


def _peer_client(ip: str, port: int) -> httpx.Client:
    # MVP: agents trust each other's self-signed certs implicitly by
    # disabling verification, the same simplification used for the
    # Provider's TLS setup. Swap verify=True + a real cert bundle (or
    # pinned certs) before this touches anything beyond a local demo.
    return httpx.Client(base_url=f"https://{ip}:{port}", verify=False, timeout=10.0)


def ensure_session(identity: AgentIdentity, target_aid: str) -> dict:
    """Returns a held session for target_aid, establishing a fresh one via
    the Provider + a direct handshake with the peer if we don't already
    have a valid one."""
    existing = session_store.get_held(target_aid)
    if existing and not session_store.is_expired(existing) and existing["request_count"] < existing["qmax"]:
        return existing

    # Steps 2-3: ask the Provider for the peer's info + a fresh OTK
    peer_info = provider_client.lookup_peer(identity.aid, target_aid)

    # Verify the Provider actually vouches for this peer bundle before
    # trusting any of it (paper step 3).
    provider_vk = provider_client.get_provider_verify_key()
    if not crypto.verify_provider_signature(
        provider_vk,
        peer_info["aid"],
        peer_info["device"],
        peer_info["ip"],
        peer_info["port"],
        peer_info["pac_hex"],
        peer_info["provider_signature_hex"],
    ):
        raise RuntimeError(f"Provider signature on {target_aid}'s identity did not verify -- refusing to contact it")

    # Steps 4-5: contact the peer directly and request a token, presenting
    # our own Provider-signed identity bundle plus the OTK we were given.
    with _peer_client(peer_info["ip"], peer_info["port"]) as client:
        resp = client.post(
            "/saga/token-request",
            json={
                "aid": identity.aid,
                "device": identity.device,
                "ip": identity.ip,
                "port": identity.port,
                "pac_hex": identity.pac_public_hex,
                "provider_signature_hex": identity.provider_signature_hex,
                "otk_hex": peer_info["otk_hex"],
            },
        )
        resp.raise_for_status()
        data = resp.json()

    # Steps 6-7: derive the shared key (same DH result the peer computed)
    # and decrypt the token they created for us. The pairing must mirror
    # the receiver's exactly: they used (their OTK private, our PAC
    # public); we use (our PAC private, their OTK public) -- NOT their
    # PAC public key, which would derive a different, wrong shared secret.
    box = crypto.make_box(identity.pac_private, peer_info["otk_hex"])
    token = crypto.decrypt_token(box, data["token_hex"])

    session_store.store_held(target_aid, data["token_hex"], token, box, peer_info["ip"], peer_info["port"])
    return session_store.get_held(target_aid)


def send_message(identity: AgentIdentity, target_aid: str, payload: dict) -> dict:
    """Step 8: send an actual task message, establishing a session first
    if we don't already have a usable one."""
    session = ensure_session(identity, target_aid)
    with _peer_client(session["ip"], session["port"]) as client:
        resp = client.post(
            "/saga/message",
            json={"token_hex": session["token_hex"], "from_aid": identity.aid, "payload": payload},
        )
        resp.raise_for_status()
    session_store.bump_held_request_count(target_aid)
    return resp.json()
