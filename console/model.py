"""Register model 2.22 as data: types, states, transitions and the fields each move demands.

This is the only place the console knows the model. It mirrors sections 4.2, 4.4, 9 (I2, I20)
of solution-register-model.md. Field keys are the frontmatter keys of section 7; long fields
(body headings) are lower-cased heading names.
"""

DIRS = {
    "REQ": "requirements", "DEC": "decisions", "LIM": "limitations",
    "RSK": "risks", "OI": "open-items", "CR": "change-requests",
}
NAMES = {
    "REQ": "Requirement", "DEC": "Decision", "LIM": "Limitation",
    "RSK": "Risk", "OI": "Open item", "CR": "Change request",
}

STATES = {
    "REQ": ["Draft", "Agreed", "Designed", "Delivered", "Verified", "Withdrawn"],
    "DEC": ["Proposed", "Accepted", "Superseded", "Rejected"],
    "LIM": ["Identified", "Under assessment", "Accepted", "Change requested", "Resolved", "Withdrawn"],
    "RSK": ["Identified", "Mitigating", "Realised", "Retired"],
    "OI":  ["Open", "Blocked", "Closed"],
    "CR":  ["Proposed", "For approval", "Approved", "Submitted", "Deferred", "Delivered", "Withdrawn", "Rejected"],
}
TERMINAL = {
    "REQ": {"Verified", "Withdrawn"},
    "DEC": {"Superseded", "Rejected"},
    "LIM": {"Accepted", "Change requested", "Resolved", "Withdrawn"},
    "RSK": {"Realised", "Retired"},
    "OI":  {"Closed"},
    "CR":  {"Delivered", "Withdrawn", "Rejected"},
}
# States that set Closed on: terminal ones plus the approved states.
CLOSES = {t: set(s) for t, s in TERMINAL.items()}
CLOSES["DEC"] |= {"Accepted"}
CLOSES["CR"] |= {"Approved", "Deferred"}

# 4.4 arrows plus the I20 return moves.
TRANSITIONS = {
    "REQ": {
        "Draft": ["Agreed", "Withdrawn"], "Agreed": ["Designed", "Withdrawn"],
        "Designed": ["Delivered", "Withdrawn"], "Delivered": ["Verified", "Withdrawn"],
    },
    "DEC": {"Proposed": ["Accepted", "Rejected"], "Accepted": ["Superseded"]},
    "LIM": {
        "Identified": ["Under assessment", "Withdrawn"],
        "Under assessment": ["Accepted", "Change requested", "Resolved", "Withdrawn"],
        "Change requested": ["Under assessment"],
    },
    "RSK": {"Identified": ["Mitigating", "Realised", "Retired"], "Mitigating": ["Realised", "Retired"]},
    "OI": {"Open": ["Blocked", "Closed"], "Blocked": ["Open", "Closed"]},
    "CR": {
        "Proposed": ["For approval", "Withdrawn"],
        "For approval": ["Approved", "Deferred", "Rejected", "Withdrawn"],
        "Approved": ["Submitted"], "Submitted": ["Delivered"], "Deferred": ["Proposed"],
    },
}

# Short (frontmatter) and long (body) fields per type, in file order.
SHORT = {
    "REQ": ["moscow", "phase", "owner", "implemented-by", "vendor-ref"],
    "DEC": ["owner", "consulted", "approved-by", "implemented-by"],
    "LIM": ["owner", "chosen-option", "implemented-by", "vendor-ref"],
    "RSK": ["owner", "likelihood", "impact", "due"],
    "OI":  ["owner", "due"],
    "CR":  ["owner", "chosen-option", "estimate", "approved-by", "phase", "implemented-by", "vendor-ref"],
}
LONG = {
    "REQ": ["source", "notes"],
    "DEC": ["rationale", "source", "notes"],
    "LIM": ["impact", "options", "source", "notes"],
    "RSK": ["trigger", "mitigation", "source", "notes"],
    "OI":  ["next action", "source", "notes"],
    "CR":  ["reason", "source", "notes"],
}
LABELS = {
    "moscow": "MoSCoW", "phase": "Phase", "owner": "Owner", "implemented-by": "Implemented by",
    "vendor-ref": "Vendor ref", "consulted": "Consulted", "approved-by": "Approved by",
    "chosen-option": "Chosen option", "likelihood": "Likelihood", "impact": "Impact", "due": "Due",
    "estimate": "Estimate", "rationale": "Rationale", "options": "Options", "trigger": "Trigger",
    "mitigation": "Mitigation", "next action": "Next action", "reason": "Reason", "source": "Source",
    "notes": "Notes", "links": "Links", "title": "Title", "status": "Status",
}
CHOICES = {
    "moscow": ["Must", "Should", "Could", "Won't"],
    "implemented-by": ["Vendor", "Internal", "Both"],
    "likelihood": ["L", "M", "H"], "impact": ["L", "M", "H"],
}

# Fields that must be filled to enter a state (I2, 4.4). "link:<word>" means a Links entry with that word.
REQUIRED_ON_ENTRY = {
    "REQ": {"Draft": ["moscow", "owner"], "Agreed": ["phase"]},
    "DEC": {"Accepted": ["approved-by", "consulted"], "Rejected": ["approved-by", "consulted"]},
    "LIM": {
        "Under assessment": ["impact", "link:assessed by"],
        "Accepted": ["impact", "options", "chosen-option", "link:constrains", "link:dispositioned by"],
        "Change requested": ["impact", "options", "chosen-option", "link:constrains", "link:dispositioned by"],
        "Resolved": ["source"], "Withdrawn": ["source"],
    },
    "RSK": {"Mitigating": ["trigger", "mitigation"], "Realised": ["link:realised as"], "Retired": ["mitigation"]},
    "OI": {"Open": ["owner", "next action"], "Blocked": ["next action"], "Closed": ["link:resolves into"]},
    "CR": {
        "Proposed": ["reason", "link:triggered by"],
        "For approval": ["reason", "chosen-option", "estimate"],
        "Approved": ["approved-by", "phase"], "Deferred": ["approved-by", "phase"],
        "Rejected": ["approved-by"], "Withdrawn": ["approved-by"],
        "Submitted": ["approved-by", "phase"],
    },
}
# On creation every type needs these.
REQUIRED_ON_CREATE = {
    "REQ": ["title", "moscow", "owner", "implemented-by", "source"],
    "DEC": ["title", "owner", "rationale", "implemented-by", "source"],
    "LIM": ["title", "owner", "implemented-by", "source"],
    "RSK": ["title", "owner", "likelihood", "impact", "source"],
    "OI":  ["title", "owner", "next action", "source"],
    "CR":  ["title", "owner", "reason", "implemented-by", "source", "link:triggered by"],
}
FIRST_STATE = {"REQ": "Draft", "DEC": "Proposed", "LIM": "Identified", "RSK": "Identified", "OI": "Open", "CR": "Proposed"}

# Which link words may be written from each type (section 5), and what they may point at.
LINK_WORDS = {
    "REQ": {"replaces": "CLAIM", "preserves": "CLAIM", "worked by": "OI"},
    "DEC": {"addresses": "REQ", "introduces": "LIM", "raises": "RSK", "supersedes": "DEC", "superseded by": "DEC", "proposed by": "OI"},
    "LIM": {"constrains": "REQ", "dispositioned by": "DEC|CR", "previously dispositioned by": "DEC|CR", "assessed by": "OI", "introduced by": "DEC"},
    "RSK": {"realised as": "OI", "raised by": "DEC"},
    "OI":  {"resolves into": "ANY", "clarifies": "CLAIM"},
    "CR":  {"triggered by": "LIM|REQ", "delivers": "REQ", "part of": "CR", "worked by": "OI"},
}


def missing_for(kind, state, item):
    """Return the list of required fields (labels) that are empty for entering `state`."""
    req = REQUIRED_ON_ENTRY.get(kind, {}).get(state, [])
    out = []
    for f in req:
        if f.startswith("link:"):
            word = f[5:]
            if not any(l.lower().startswith(word) for l in item.get("links", [])):
                out.append(f"Links: {word} …")
        elif f == "options":
            opts = [l for l in item.get("options", "").splitlines() if l.strip()]
            if len(opts) < 2:
                out.append("Options (at least two)")
        elif not str(item.get(f, "")).strip():
            out.append(LABELS.get(f, f))
    return out
