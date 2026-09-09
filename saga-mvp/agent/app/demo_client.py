"""
Manual demo: have this agent (the initiator) contact a peer agent and
exchange a couple of messages, exercising the full SAGA handshake.

Usage (from the host, once both agent containers are up):
    docker compose exec alice-agent python -m app.demo_client bob:calendar_agent

Or pass the peer's ip/port explicitly if they differ from convention:
    docker compose exec alice-agent python -m app.demo_client bob:calendar_agent bob-agent 9002
"""
import sys

from . import peer_client
from .keys import load_identity


def main():
    if len(sys.argv) < 2:
        print("usage: python -m app.demo_client <target_aid>")
        sys.exit(1)

    target_aid = sys.argv[1]
    identity = load_identity()

    print(f"[{identity.aid}] sending first message to {target_aid} (will establish a session if needed)")
    resp1 = peer_client.send_message(identity, target_aid, {"text": "Are you free tomorrow at 2pm?"})
    print("response 1:", resp1)

    print(f"\n[{identity.aid}] sending second message on the same session")
    resp2 = peer_client.send_message(identity, target_aid, {"text": "Great, see you then."})
    print("response 2:", resp2)


if __name__ == "__main__":
    main()
