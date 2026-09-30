import os
from pathlib import Path

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

app = FastAPI(title="SAGA Meeting UI")
BASE = Path(__file__).resolve().parent
ALICE_URL = os.getenv("ALICE_AGENT_URL", "https://alice-agent:9001")
BOB_URL = os.getenv("BOB_AGENT_URL", "https://bob-agent:9002")
SEED_ADMIN_URL = os.getenv("SEED_ADMIN_URL", "http://seed-admin:8081")
SEED_ADMIN_TOKEN = os.getenv("SEED_ADMIN_TOKEN", "")
VERIFY_TLS = os.getenv("AGENT_VERIFY_TLS", "false").lower() == "true"

class MeetingRequest(BaseModel):
    initiator: str
    title: str
    start: str
    end: str

class RefreshRequest(BaseModel):
    uid: str
    num_otks: int = 10

def _agent(name: str) -> str:
    if name == "alice": return ALICE_URL
    if name == "bob": return BOB_URL
    raise HTTPException(400, "user must be alice or bob")

async def _get_events(name: str, start: str, end: str):
    async with httpx.AsyncClient(verify=VERIFY_TLS, timeout=15.0) as c:
        r = await c.get(f"{_agent(name)}/calendar/events", params={"time_min": start, "time_max": end})
        r.raise_for_status()
        return r.json()

@app.get("/api/health")
async def health():
    result = {}
    async with httpx.AsyncClient(verify=VERIFY_TLS, timeout=5.0) as c:
        for name, url in (("alice", ALICE_URL), ("bob", BOB_URL)):
            try:
                r = await c.get(f"{url}/health")
                result[name] = r.json()
            except Exception as e:
                result[name] = {"status": "offline", "detail": str(e)}
    return result

@app.get("/api/availability")
async def availability(start: str, end: str):
    return {"alice": await _get_events("alice", start, end), "bob": await _get_events("bob", start, end)}

@app.post("/api/meeting")
async def create_meeting(req: MeetingRequest):
    if req.initiator not in ("alice", "bob"):
        raise HTTPException(400, "initiator must be alice or bob")
    target = "bob" if req.initiator == "alice" else "alice"
    payload = {"action": "schedule_meeting", "summary": req.title, "start": req.start, "end": req.end}
    async with httpx.AsyncClient(verify=VERIFY_TLS, timeout=20.0) as c:
        target_result = await c.post(f"{_agent(req.initiator)}/saga/send", json={"target_aid": f"{target}:calendar_agent", "payload": payload})
        target_result.raise_for_status()
        own_result = await c.post(f"{_agent(req.initiator)}/calendar/create", json=payload)
        own_result.raise_for_status()
    return {"status": "scheduled", "initiator": req.initiator, "target": target, "target_result": target_result.json(), "own_result": own_result.json()}

@app.post("/api/otk-refresh")
async def refresh_otks(req: RefreshRequest):
    if req.uid not in ("alice", "bob"):
        raise HTTPException(400, "uid must be alice or bob")
    async with httpx.AsyncClient(timeout=20.0) as c:
        r = await c.post(f"{SEED_ADMIN_URL}/refresh-otks", headers={"X-Seed-Admin-Token": SEED_ADMIN_TOKEN}, json=req.model_dump())
        if r.status_code >= 400:
            raise HTTPException(r.status_code, r.text)
        return r.json()

@app.get("/")
def index():
    return FileResponse(BASE / "static" / "index.html")
