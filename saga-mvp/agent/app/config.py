import os
from pathlib import Path

AGENT_UID = os.environ["AGENT_UID"]
AGENT_NAME = os.environ["AGENT_NAME"]
AID = f"{AGENT_UID}:{AGENT_NAME}"

AGENT_PORT = int(os.getenv("AGENT_PORT", "9000"))
PROVIDER_URL = os.getenv("PROVIDER_URL", "https://provider:8443")
PROVIDER_VERIFY_TLS = os.getenv("PROVIDER_VERIFY_TLS", "false").lower() == "true"

KEYS_DIR = Path(os.getenv("KEYS_DIR", "/keys"))
KEY_FILE = KEYS_DIR / f"{AGENT_UID}__{AGENT_NAME}.json"

# SAGA paper's own example values (Section on the security add-on): 5 min / limited requests.
TOKEN_LIFETIME_SECONDS = int(os.getenv("TOKEN_LIFETIME_SECONDS", "300"))
TOKEN_MAX_REQUESTS = int(os.getenv("TOKEN_MAX_REQUESTS", "50"))
