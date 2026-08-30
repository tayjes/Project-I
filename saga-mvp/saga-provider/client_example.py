"""
Example client for the SAGA Provider MVP.

Demonstrates the crypto and API calls an agent container will need to
make: generate keys, register a user + agent, and have one agent look
up another (which issues an OTK per the contact policy).

Run against a local Provider:
    python client_example.py

Requires: pip install pynacl httpx
"""
import json

import httpx
from nacl.public import PrivateKey
from nacl.signing import SigningKey

PROVIDER_URL = "https://localhost:8443"
# For local dev with a self-signed cert; in production verify properly.
VERIFY_TLS = False


def canonical_agent_info(aid, device, ip, port, pac_hex):
    payload = {"aid": aid, "device": device, "ip": ip, "port": port, "pac": pac_hex}
    return json.dumps(payload, sort_keys=True).encode()


def register_user(client: httpx.Client, uid: str, password: str) -> SigningKey:
    signing_key = SigningKey.generate()
    resp = client.post(
        f"{PROVIDER_URL}/users/register",
        json={
            "uid": uid,
            "password": password,
            "verify_key_hex": signing_key.verify_key.encode().hex(),
        },
    )
    resp.raise_for_status()
    print(f"[{uid}] registered:", resp.json())
    return signing_key


def register_agent(
    client: httpx.Client,
    signing_key: SigningKey,
    uid: str,
    password: str,
    name: str,
    device: str,
    ip: str,
    port: int,
    contact_policy: list[dict],
    num_otks: int = 5,
):
    aid = f"{uid}:{name}"

    # Long-term access-control keypair (X25519) used later for the
    # agent-to-agent Diffie-Hellman handshake.
    pac = PrivateKey.generate()
    pac_hex = bytes(pac.public_key).hex()

    # One-time keys (X25519), each signed individually.
    otk_privs = [PrivateKey.generate() for _ in range(num_otks)]
    otks = [bytes(k.public_key).hex() for k in otk_privs]
    otk_signatures = [
        signing_key.sign(f"{aid}:{otk_hex}".encode()).signature.hex() for otk_hex in otks
    ]

    info_bytes = canonical_agent_info(aid, device, ip, port, pac_hex)
    signature_hex = signing_key.sign(info_bytes).signature.hex()

    resp = client.post(
        f"{PROVIDER_URL}/agents/register",
        json={
            "aid": aid,
            "uid": uid,
            "password": password,
            "device": device,
            "ip": ip,
            "port": port,
            "pac_hex": pac_hex,
            "otks": otks,
            "signature_hex": signature_hex,
            "otk_signatures": otk_signatures,
            "contact_policy": contact_policy,
        },
    )
    resp.raise_for_status()
    print(f"[{aid}] registered:", resp.json())
    # Return the private keys too -- the agent container will need them
    # to actually run the DH handshake and decrypt tokens later.
    return aid, pac, otk_privs


def lookup(client: httpx.Client, target_aid: str, initiator_aid: str):
    resp = client.get(
        f"{PROVIDER_URL}/agents/{target_aid}/lookup",
        params={"initiator_aid": initiator_aid},
    )
    resp.raise_for_status()
    print(f"[{initiator_aid} -> {target_aid}] lookup:", resp.json())
    return resp.json()


if __name__ == "__main__":
    with httpx.Client(verify=VERIFY_TLS) as client:
        alice_key = register_user(client, "alice", "alicepass123")
        bob_key = register_user(client, "bob", "bobpass123")

        alice_aid, alice_pac, alice_otks = register_agent(
            client,
            alice_key,
            "alice",
            "alicepass123",
            "calendar_agent",
            device="alice-agent-container",
            ip="alice-agent",
            port=9001,
            contact_policy=[{"agents": "bob:calendar_agent", "budget": 15}],
        )

        bob_aid, bob_pac, bob_otks = register_agent(
            client,
            bob_key,
            "bob",
            "bobpass123",
            "calendar_agent",
            device="bob-agent-container",
            ip="bob-agent",
            port=9002,
            contact_policy=[{"agents": "alice:calendar_agent", "budget": 15}],
        )

        # Alice wants to contact Bob -> Provider checks Bob's contact
        # policy and issues an OTK for Bob if Alice is permitted.
        lookup(client, target_aid=bob_aid, initiator_aid=alice_aid)
