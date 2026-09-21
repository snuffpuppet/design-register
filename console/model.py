"""Register model 2.35 as data: types, states, transitions, the fields each move demands, the supports each state implies, and special entry conditions.

This is the only place the console knows the model. It mirrors sections 4.2, 4.4, 9 (I2, I20)
and SUPPORTS (4.4 and 5 as implications) of solution-register-model.md. Field keys are the
frontmatter keys of section 7; long fields (body headings) are lower-cased heading names.
Contains SPECIAL_ON_ENTRY, WITHDRAWS, BACKWARD, and FORWARD for entry rules and provenance tracking.
"""

MODEL_VERSION = "2.35"
CHANGE_SET_CONTRACT = "2.35"
REVIEW_OUTCOMES = ["confirmed", "corrected", "merged", "excluded", "needs clarification", "retyped", "split"]

DIRS = {
    "REQ": "requirements", "DEC": "decisions", "LIM": "limitations",
    "RSK": "risks", "OI": "open-items", "CP": "change-proposals",
}
NAMES = {
    "REQ": "Requirement", "DEC": "Decision", "LIM": "Limitation",
    "RSK": "Risk", "OI": "Open item", "CP": "Change proposal",
}

STATES = {
    "REQ": ["Draft", "Agreed", "Designed", "Delivered", "Verified", "Withdrawn"],
    "DEC": ["Proposed", "Accepted", "Superseded", "Rejected"],
    "LIM": ["Identified", "Under assessment", "Accepted", "Change requested", "Resolved", "Withdrawn"],
    "RSK": ["Identified", "Mitigating", "Realised", "Retired"],
    "OI":  ["Open", "Blocked", "Closed"],
    "CP":  ["Proposed", "For approval", "Approved", "Submitted", "Deferred", "Delivered", "Withdrawn", "Rejected"],
}
TERMINAL = {
    "REQ": {"Verified", "Withdrawn"},
    "DEC": {"Superseded", "Rejected"},
    "LIM": {"Accepted", "Change requested", "Resolved", "Withdrawn"},
    "RSK": {"Realised", "Retired"},
    "OI":  {"Closed"},
    "CP":  {"Delivered", "Withdrawn", "Rejected"},
}
# States that set Closed on: terminal ones plus the approved states.
CLOSES = {t: set(s) for t, s in TERMINAL.items()}
CLOSES["DEC"] |= {"Accepted"}
CLOSES["CP"] |= {"Approved", "Deferred"}

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
    "CP": {
        "Proposed": ["For approval", "Withdrawn"],
        "For approval": ["Approved", "Deferred", "Rejected", "Withdrawn"],
        "Approved": ["Submitted"], "Submitted": ["Delivered"], "Deferred": ["Proposed"],
    },
}

# Short (frontmatter) and long (body) fields per type, in file order.
SHORT = {
    "REQ": ["scope", "moscow", "phase", "owner", "implemented-by"],
    "DEC": ["scope", "owner", "consulted", "approved-by", "implemented-by"],
    "LIM": ["scope", "owner", "chosen-option", "implemented-by"],
    "RSK": ["scope", "risk-kind", "owner", "likelihood", "impact", "due"],
    "OI":  ["scope", "owner", "due"],
    "CP":  ["scope", "owner", "chosen-option", "estimate", "approved-by", "phase", "implemented-by", "vendor-ref"],
}
LONG = {
    "REQ": ["options", "source", "notes"],
    "DEC": ["rationale", "source", "notes"],
    "LIM": ["impact", "options", "source", "notes"],
    "RSK": ["trigger", "mitigation", "source", "notes"],
    "OI":  ["next action", "source", "notes"],
    "CP":  ["reason", "source", "notes"],
}
LABELS = {
    "risk-kind": "Kind", "moscow": "MoSCoW", "phase": "Phase", "scope": "Scope", "owner": "Owner", "implemented-by": "Implemented by",
    "vendor-ref": "Vendor ref", "consulted": "Consulted", "approved-by": "Approved by",
    "chosen-option": "Chosen option", "likelihood": "Likelihood", "impact": "Impact", "due": "Due",
    "estimate": "Estimate", "rationale": "Rationale", "options": "Options", "trigger": "Trigger",
    "mitigation": "Mitigation", "next action": "Next action", "reason": "Reason", "source": "Source",
    "notes": "Notes", "links": "Links", "title": "Title", "status": "Status", "raised-on": "Raised on", "closed-on": "Closed on", "updated": "Updated",
}
CHOICES = {
    "moscow": ["Must", "Should", "Could", "Won't"],
    "implemented-by": ["Vendor", "Internal", "Both"],
    "likelihood": ["L", "M", "H"], "impact": ["L", "M", "H"], "risk-kind": ["Risk", "Assumption", "Dependency"],
}

# Fields that must be filled to enter a state (I2, 4.4). "link:<word>" means a Links entry with that word.
REQUIRED_ON_ENTRY = {
    "REQ": {"Draft": ["moscow", "owner"], "Agreed": ["phase"]},
    "DEC": {"Accepted": ["approved-by", "consulted"], "Rejected": ["approved-by", "consulted"]},
    "LIM": {
        "Under assessment": ["impact", "link:assessed by"],
        "Accepted": ["impact", "options", "chosen-option", "implemented-by", "link:constrains", "link:dispositioned by"],
        "Change requested": ["impact", "options", "chosen-option", "implemented-by", "link:constrains", "link:dispositioned by"],
        "Resolved": ["source"], "Withdrawn": ["source"],
    },
    "RSK": {"Mitigating": ["trigger", "mitigation"], "Realised": ["link:realised as"], "Retired": ["mitigation"]},
    "OI": {"Open": ["owner", "next action"], "Blocked": ["next action"], "Closed": ["link:resolves into"]},
    "CP": {
        "Proposed": ["reason", "link:triggered by"],
        "For approval": ["reason", "chosen-option", "estimate"],
        "Approved": ["approved-by", "phase"], "Deferred": ["approved-by", "phase"],
        "Rejected": ["approved-by"], "Withdrawn": ["approved-by"],
        "Submitted": ["approved-by", "phase"],
    },
}
# On creation every type needs these.
REQUIRED_ON_CREATE = {
    "REQ": ["title", "scope", "moscow", "owner", "implemented-by", "source"],
    "DEC": ["title", "scope", "owner", "rationale", "implemented-by", "source"],
    "LIM": ["title", "scope", "owner", "source"],
    "RSK": ["title", "scope", "risk-kind", "owner", "likelihood", "impact", "source"],
    "OI":  ["title", "scope", "owner", "next action", "source"],
    "CP":  ["title", "scope", "owner", "reason", "implemented-by", "source", "link:triggered by"],
}
FIRST_STATE = {"REQ": "Draft", "DEC": "Proposed", "LIM": "Identified", "RSK": "Identified", "OI": "Open", "CP": "Proposed"}

# Which link words may be written from each type (section 5), and what they may point at.
LINK_WORDS = {
    "REQ": {"replaces": "CLAIM", "preserves": "CLAIM", "worked by": "OI"},
    "DEC": {"addresses": "REQ", "introduces": "LIM", "raises": "RSK", "supersedes": "DEC", "superseded by": "DEC", "proposed by": "OI"},
    "LIM": {"constrains": "REQ", "dispositioned by": "DEC|CP", "previously dispositioned by": "DEC|CP", "assessed by": "OI", "introduced by": "DEC", "needs": "REQ"},
    "RSK": {"realised as": "OI", "raised by": "DEC", "mitigated by": "OI"},
    "OI":  {"resolves into": "ANY", "clarifies": "CLAIM"},
    "CP":  {"triggered by": "LIM|REQ", "delivers": "REQ", "part of": "CP", "worked by": "OI", "based on": "DEC"},
}


# 4.4 and 5 read as implications: an item in `when` states must have `unless`; if it does not, offer
# the item in `offer`, linked by `link` (word written on the trigger, word written on the offer or None
# because section 5 derives the reverse). Rows with no offer are prompts: a field or a linked item's
# state that the reviewer must fix by hand. `check` names the section 9 rule the row serves.
# Templates may use any trigger field key plus {id}, {title}, {chosen} and {beaten}.
SUPPORTS = [
    dict(rule="S1", check="I3", level="fail", when=("REQ", ["Draft"]), unless="link:worked by", only_if=None,
         offer=("OI", "Open"), link=("worked by", None),
         fields={"title": "Agree REQ: {title}", "owner": "{owner}", "next action": "Confirm the need with {owner} and set Phase"}),
    dict(rule="S2", check="I3", level="fail", when=("DEC", ["Proposed"]), unless="link:proposed by", only_if=None,
         offer=("OI", "Open"), link=("proposed by", None),
         fields={"title": "Decide: {title}", "owner": "{owner}", "next action": "Take {id} to the approver"}),
    dict(rule="S3", check="I3", level="fail", when=("LIM", ["Under assessment"]), unless="link:assessed by", only_if=None,
         offer=("OI", "Open"), link=("assessed by", None),
         fields={"title": "Assess LIM: {title}", "owner": "{owner}", "next action": "Find the requirement this constrains; write constrains REQ-nnnn"}),
    dict(rule="S4", check="I7", level="fail", when=("LIM", ["Under assessment", "Accepted", "Change requested"]), unless="link:constrains", only_if=None,
         offer=("REQ", "Draft"), link=("constrains", None),
         fields={"title": "Need behind: {title}", "owner": "", "moscow": "Must", "implemented-by": "{implemented-by}"}),
    dict(rule="S5", check="I7", level="fail", when=("LIM", ["Accepted"]), unless="link:dispositioned by:DEC", only_if=None,
         offer=("DEC", "Proposed"), link=("dispositioned by", None),
         fields={"title": "Accept: {title}", "owner": "{owner}", "consulted": "Vendor", "implemented-by": "{implemented-by}",
                 "rationale": "Accepts {id} with option {chosen-option}: {chosen}. Beat: {beaten}"}),
    dict(rule="S6", check="I7", level="fail", when=("LIM", ["Change requested"]), unless="link:dispositioned by:CP", only_if=None,
         offer=("CP", "Proposed"), link=("dispositioned by", "triggered by"),
         fields={"title": "{chosen}", "owner": "{owner}", "reason": "{impact}", "chosen-option": "{chosen}", "implemented-by": "{implemented-by}"}),
    dict(rule="S7", check="I3", level="fail", when=("CP", ["Proposed", "For approval", "Submitted"]), unless="link:worked by", only_if=None,
         offer=("OI", "Open"), link=("worked by", None),
         fields={"title": "Progress CP: {title}", "owner": "{owner}", "next action": "Shape, estimate and take {id} to approval"}),
    dict(rule="S8", check="I10", level="fail", when=("CP", None), unless="link:triggered by", only_if=None,
         offer=("LIM", "Identified"), link=("triggered by", None),
         fields={"title": "Behind {id}: {title}", "owner": "{owner}", "impact": "{reason}", "implemented-by": "{implemented-by}",
                 "source": "Implied by {id}; vendor ref {vendor-ref}"}),
    dict(rule="S9", check="I13", level="fail", when=("RSK", ["Realised"]), unless="link:realised as", only_if=None,
         offer=("OI", "Open"), link=("realised as", None),
         fields={"title": "Respond: {title}", "owner": "{owner}", "next action": "{mitigation}"}),
    dict(rule="S10", check="I9", level="fail", when=("OI", ["Closed"]), unless="link:resolves into", only_if=None,
         offer=None, link=(None, None), fields={}, prompt="Add a resolves into link, or 'resolves into none: <reason>'."),
    dict(rule="S11", check="I8", level="fail", when=("DEC", ["Superseded"]), unless="link:superseded by", only_if=None,
         offer=("DEC", "Proposed"), link=("superseded by", "supersedes"),
         fields={"title": "{title}", "owner": "{owner}", "rationale": "{rationale}", "consulted": "{consulted}", "implemented-by": "{implemented-by}"}),
    dict(rule="S12", check="I7", level="fail", when=("LIM", ["Accepted"]), unless="linked:dispositioned by:DEC:Accepted", only_if="link:dispositioned by:DEC",
         offer=None, link=(None, None), fields={}, prompt="The accepting decision is not yet Accepted."),
    dict(rule="S13", check="I7", level="fail", when=("LIM", ["Change requested"]), unless="linked:dispositioned by:CP:Proposed|For approval|Approved|Submitted|Deferred|Delivered", only_if="link:dispositioned by:CP",
         offer=None, link=(None, None), fields={}, prompt="The change proposal was withdrawn or rejected: move this limitation back to Under assessment."),
    dict(rule="S14", check="I10", level="fail", when=("CP", ["Approved", "Submitted", "Delivered", "Deferred", "Withdrawn", "Rejected"]), unless="field:approved-by", only_if=None,
         offer=None, link=(None, None), fields={}, prompt="Approved by is empty."),
    dict(rule="S15", check="I2", level="fail", when=("LIM", ["Accepted", "Change requested"]), unless="field:chosen-option", only_if=None,
         offer=None, link=(None, None), fields={}, prompt="Impact, at least two Options and a Chosen option are needed."),
    dict(rule="S16", check="4.4", level="warn", when=("REQ", ["Designed", "Delivered", "Verified"]), unless="field:source", only_if=None,
         offer=None, link=(None, None), fields={}, prompt="Source or Links should name the design section."),
    dict(rule="S17", check="I21", level="fail", when=("RSK", ["Mitigating"]), unless="link:mitigated by", only_if="field:mitigation",
         offer=("OI", "Open"), link=("mitigated by", None),
         fields={"title": "Mitigate: {title}", "owner": "{owner}", "next action": "{mitigation}", "due": "{due}"}),
    dict(rule="S18", check="I22", level="warn", when=("LIM", ["Accepted"]), unless="link:needs", only_if="tooling",
         offer=("REQ", "Draft"), link=("needs", None),
         fields={"title": "{chosen}", "owner": "{owner}", "moscow": "Must", "implemented-by": "Internal"}),
    dict(rule="S19", check="I23", level="fail", when=("CP", ["Delivered"]), unless="link:delivers", only_if=None,
         offer=None, link=(None, None), fields={}, prompt="Add a delivers link to the requirement, then move that requirement."),
    dict(rule="S21", check="I7", level="warn", when=("LIM", ["Accepted"]), unless="linked:constrains:REQ:Withdrawn", only_if="unmet",
         offer=None, link=(None, None), fields={}, prompt="The chosen option leaves the need unmet: set the requirement to Won't or a later Phase, with a Deferred CP."),
]

# Section 9 rules. One short line each, condensed from the model document, so the console can print
# a rule beside a failure or a suggestion.
RULES = {
    "I1": "No id appears twice across all registers.",
    "I2": "Every status is a valid 4.2 value and the fields required for that status and type are set.",
    "I3": "Every non-terminal item has an Owner, or an open item in Links whose Owner is set where the type requires it.",
    "I4": "Every open item not Closed has Next action, and Due is expected on open items and risks.",
    "I5": "Every requirement's Phase, and every change proposal's Phase once set, is one of the engagement's Phases.",
    "I6": "Every id named in Links exists in some register.",
    "I7": "Every limitation's disposition links and Source match its status under the model's limitation rules.",
    "I8": "Every DEC in Superseded has a superseded by link to a DEC in Accepted or Proposed.",
    "I9": "Every OI in Closed has Closed on and a resolves into link, and every OI in Blocked has a Next action starting Blocked.",
    "I10": "Every CP past Proposed has Approved by and Closed on, and a triggered by link that matches its status.",
    "I11": "Every DEC in Accepted or Rejected has Approved by, Closed on and at least one Consulted entry.",
    "I12": "Every REQ, DEC and CP, and every LIM in Accepted or Change requested, has Implemented by set to Vendor, Internal or Both.",
    "I13": "Every RSK in Realised has a realised as link to an open item.",
    "I14": "Every item has a Source.",
    "I15": "A DEC in Proposed or REQ in Draft older than 14 days is a warning.",
    "I16": "A DEC with no addresses link and no accepts wording in its Rationale is a warning.",
    "I17": "Every CP in Deferred has a later Phase and no open item in Links.",
    "I18": "Every replaces, preserves and clarifies target exists and is not Retired or Withdrawn.",
    "I19": "Every person named in Owner, Approved by and Consulted resolves to a known stakeholder.",
    "I20": "A status change follows an arrow in 4.4, with only the named return moves allowed.",
    "I21": "Every RSK in Mitigating whose Mitigation names an action has a mitigated by link to an open item.",
    "I22": "Every LIM in Accepted whose chosen option needs something built has a needs link to an internal REQ (warning).",
    "I23": "Every CP in Delivered has a delivers link to the requirement it delivered.",
    "I24": "Every item's Scope is one of the engagement's Scopes, and no item is without one, where the engagement declares any.",
}

# Conditions on entry that are not a plain "field is filled". `prefix`: the field must start with `value`.
# `required_if`: the field is required when the item's `when` field equals `equals`.
SPECIAL_ON_ENTRY = [
    dict(kind="OI", state="Blocked", field="next action", check="prefix", value="Blocked: ",
         text='Next action starting "Blocked: "'),
    dict(kind="CP", state="Submitted", field="vendor-ref", check="required_if", when="implemented-by", equals="Vendor",
         text="Vendor ref"),
]

# The withdrawing terminal state per type, for the bulk bar's Withdraw.
WITHDRAWS = {"REQ": "Withdrawn", "LIM": "Withdrawn", "CP": "Withdrawn", "DEC": "Rejected", "RSK": "Retired", "OI": "Closed"}

# Link words that read as provenance. BACKWARD walks to what an item came from; FORWARD to what it produced.
BACKWARD = {
    "REQ": ["replaces"], "DEC": ["proposed by"], "LIM": ["introduced by", "constrains"],
    "RSK": ["raised by"], "OI": [], "CP": ["triggered by", "part of", "based on"],
}
FORWARD = {
    "REQ": ["worked by"], "DEC": ["addresses", "introduces", "raises", "supersedes"],
    "LIM": ["dispositioned by", "assessed by", "needs"], "RSK": ["realised as", "mitigated by"],
    "OI": ["resolves into"], "CP": ["delivers", "worked by"],
}


def missing_for(kind, state, item):
    """Return the list of required fields (labels) that are empty for entering `state`, including the special conditions."""
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
    for sp in SPECIAL_ON_ENTRY:
        if sp["kind"] != kind or sp["state"] != state:
            continue
        val = str(item.get(sp["field"], "") or "")
        if sp["check"] == "prefix" and not val.startswith(sp["value"]):
            out.append(sp["text"])
        if sp["check"] == "required_if" and item.get(sp["when"]) == sp["equals"] and not val.strip():
            out.append(sp["text"])
    return out
