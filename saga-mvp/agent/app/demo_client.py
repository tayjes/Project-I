"""
Manual demo: have this agent (the initiator) contact a peer agent and
schedule a real Google Calendar event on the peer's calendar, exercising
the full SAGA handshake plus the Calendar tool.

Usage (from the host, once both agent containers are up):
    docker compose exec alice-agent python -m app.demo_client bob:calendar_agent

Or pass the peer's ip/port explicitly if they differ from convention:
    docker compose exec alice-agent python -m app.demo_client bob:calendar_agent bob-agent 9002
"""
import sys
from datetime import datetime, timedelta, timezone

from . import peer_client
from .keys import load_identity


def main():
    if len(sys.argv) < 2:
        print("usage: python -m app.demo_client <target_aid>")
        sys.exit(1)

    target_aid = sys.argv[1]
    identity = load_identity()

    start = datetime.now(timezone.utc) + timedelta(days=1)
    end = start + timedelta(minutes=30)

    payload = {
        "action": "schedule_meeting",
        "summary": f"Sync: {identity.aid} <> {target_aid}",
        "start": start.isoformat(),
        "end": end.isoformat(),
    }

    print(f"[{identity.aid}] sending scheduling request to {target_aid} (will establish a session if needed)")
    resp = peer_client.send_message(identity, target_aid, payload)
    print("response:", resp)

    if resp.get("response", {}).get("status") == "scheduled":
        print("\nEvent created:", resp["response"]["event_link"])
    else:
        print("\nScheduling did not succeed -- check the peer's logs (docker compose logs <peer>).")


if __name__ == "__main__":
    main()

