from pydantic import BaseModel, Field


class ContactPolicyRule(BaseModel):
    agents: str  # glob pattern, e.g. "*:calendar_agent" or "alice:calendar_agent"
    budget: int  # number of OTKs granted to matching initiators; -1 = blocked


class UserRegisterRequest(BaseModel):
    uid: str
    password: str
    verify_key_hex: str  # user's Ed25519 public key (hex)


class AgentRegisterRequest(BaseModel):
    aid: str  # must be "{uid}:{name}", e.g. "alice:calendar_agent"
    uid: str
    password: str
    device: str
    ip: str
    port: int
    pac_hex: str  # agent's long-term access-control public key (X25519, hex)
    otks: list[str]  # one-time public keys (X25519, hex)
    signature_hex: str  # signs canonical agent info (see README)
    otk_signatures: list[str]  # one signature per OTK, signs f"{aid}:{otk_hex}"
    contact_policy: list[ContactPolicyRule] = Field(default_factory=list)


class PolicyUpdateRequest(BaseModel):
    uid: str
    password: str
    contact_policy: list[ContactPolicyRule]


class DeactivateRequest(BaseModel):
    uid: str
    password: str


class LookupResponse(BaseModel):
    aid: str
    device: str
    ip: str
    port: int
    pac_hex: str
    otk_hex: str
    user_verify_key_hex: str
    agent_signature_hex: str
    provider_signature_hex: str
