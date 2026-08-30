"""
Contact policy matching (SAGA paper, Section IV-D.1).

Rules use glob-style patterns over the initiating agent's aid
(e.g. "*:calendar_agent", "alice:*", "alice:calendar_agent"). When
multiple rules match, the most specific one wins. We use "literal
character count" (pattern length minus wildcard characters) as the
specificity score -- a simplified stand-in for the paper's notion of
specificity, adequate for an MVP.
"""
from fnmatch import fnmatch


def _specificity(pattern: str) -> int:
    return len(pattern) - pattern.count("*")


def match_budget(contact_policy: list[dict], initiator_aid: str) -> int | None:
    """
    Returns the OTK budget for `initiator_aid` under `contact_policy`,
    or None if no rule matches at all (R = empty set in the paper's notation).
    A returned budget of -1 means the initiator is explicitly blocked.
    """
    matches = [r for r in contact_policy if fnmatch(initiator_aid, r["agents"])]
    if not matches:
        return None
    best = max(matches, key=lambda r: _specificity(r["agents"]))
    return best["budget"]
