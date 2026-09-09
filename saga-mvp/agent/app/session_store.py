"""
In-memory session state. MVP only -- resets on container restart, single
process (fine since one agent = one container = one process here).

Two roles a session can be in:
- "issued": we're the receiver, we created this token for someone else
- "held": we're the initiator, we're holding a token someone else gave us
"""
import time

_issued_sessions: dict[str, dict] = {}  # token_hex -> {...token fields, request_count, box}
_held_sessions: dict[str, dict] = {}  # peer_aid -> {...token fields, token_hex, box, ip, port, request_count}


def store_issued(token_hex: str, token: dict, box):
    _issued_sessions[token_hex] = {**token, "request_count": 0, "box": box}


def get_issued(token_hex: str) -> dict | None:
    return _issued_sessions.get(token_hex)


def bump_issued_request_count(token_hex: str):
    _issued_sessions[token_hex]["request_count"] += 1


def is_expired(session: dict) -> bool:
    return time.time() > session["expires_at"]


def store_held(peer_aid: str, token_hex: str, token: dict, box, ip: str, port: int):
    _held_sessions[peer_aid] = {
        **token,
        "token_hex": token_hex,
        "box": box,
        "ip": ip,
        "port": port,
        "request_count": 0,
    }


def get_held(peer_aid: str) -> dict | None:
    return _held_sessions.get(peer_aid)


def bump_held_request_count(peer_aid: str):
    _held_sessions[peer_aid]["request_count"] += 1


def clear_held(peer_aid: str):
    _held_sessions.pop(peer_aid, None)
