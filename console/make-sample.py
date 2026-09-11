#!/usr/bin/env python3
"""Writes a sample engagement in model 2.22 layout under test-data/puppy-gloves.

The items tell the edge-case story from the artifact "Two Ways Into the Registers", plus enough
other items to make the outstanding view interesting. Re-run to reset. Change sets under
change-sets/ are removed too, except the seeded CS-0001.
"""
import os, shutil, sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "test-data", "puppy-gloves")
ROOT = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else ROOT)
DIRS = {"REQ": "requirements", "DEC": "decisions", "LIM": "limitations", "RSK": "risks", "OI": "open-items", "CR": "change-requests", "STK": "stakeholders"}


def item(id, title, status, fm, body, links=()):
    kind = id.split("-")[0]
    lines = ["---", f"id: {id}", f"title: {title}", f"status: {status}"]
    for k, v in fm.items():
        lines.append(f"{k}: {v}")
    lines.append("links:")
    lines += [f"  - {l}" for l in links]
    lines += ["---", ""]
    for h, v in body.items():
        lines += [f"## {h}", "", v.strip(), ""]
    p = os.path.join(ROOT, DIRS[kind], id + ".md")
    open(p, "w", encoding="utf-8").write("\n".join(lines))


def stk(id, name, role, org, standing):
    open(os.path.join(ROOT, "stakeholders", id + ".md"), "w", encoding="utf-8").write(
        f"---\nid: {id}\nname: {name}\nrole: {role}\norganisation: {org}\nstanding: {standing}\nstatus: Active\nupdated: 8 September 2026\n---\n")


if os.path.exists(ROOT):
    shutil.rmtree(ROOT)
for d in list(DIRS.values()) + ["change-sets", "index"]:
    os.makedirs(os.path.join(ROOT, d), exist_ok=True)

open(os.path.join(ROOT, "engagement.md"), "w", encoding="utf-8").write("""# Engagement: puppy-gloves

Version 0.4, 11 September 2026.

- Client: puppy-gloves (sanitised name)
- Domain: order and provisioning
- Model version: 2.22

## Phases

- Day one (current)
- Release 2
- Later phase
""")

stk("STK-0001", "Elena Marchetti", "Product owner", "Us", "Decides on order requirements")
stk("STK-0002", "Martin Vasquez", "Solution architect", "Vendor", "Vendor design authority")
stk("STK-0003", "Priya Nair", "Operations lead", "Us", "Decides on manual process")
stk("STK-0004", "Adam Moyes", "Solution architect", "Us", "Design authority")
stk("STK-0005", "Change board", "Forum", "Us", "Approves change requests and cost")
stk("STK-0006", "Tom Okafor", "Billing SME", "Us", "Advises on billing")

C = {"implemented-by": "Vendor"}
# --- Requirements ---
item("REQ-0014", "Provision multi-gig orders with the correct port count", "Designed",
     {"moscow": "Must", "phase": "Day one", "owner": "Elena Marchetti", "implemented-by": "Vendor", "vendor-ref": "VND-118", "raised-on": "20 August 2026", "closed-on": "", "updated": "3 September 2026"},
     {"Source": "T001/412:0-2 | Elena Marchetti | 00:21:07 | \"every multi-gig order has to land with the right number of ports\"\nDesign doc §4.2", "Notes": "Edge case for split-site orders found in vendor design review, see LIM-0021."},
     ["worked by OI-0031"])
item("REQ-0015", "Send order confirmation by email and SMS on day one", "Agreed",
     {"moscow": "Must", "phase": "Day one", "owner": "Elena Marchetti", "implemented-by": "Vendor", "vendor-ref": "VND-121", "raised-on": "20 August 2026", "closed-on": "", "updated": "1 September 2026"},
     {"Source": "T001/530:1 | Elena Marchetti | 00:29:44 | \"they get an email and a text, day one\"", "Notes": ""},
     ["worked by OI-0033"])
item("REQ-0016", "Operations can find split-site orders awaiting manual port assignment", "Draft",
     {"moscow": "Should", "phase": "Day one", "owner": "Priya Nair", "implemented-by": "Internal", "vendor-ref": "", "raised-on": "22 August 2026", "closed-on": "", "updated": "22 August 2026"},
     {"Source": "Stakeholder forum, 22 August 2026", "Notes": "Raised alongside the workaround discussion on LIM-0021. Stale in Draft: needs an owner conversation."},
     ["worked by OI-0040"])
item("REQ-0017", "Bill split-site orders as one invoice line", "Agreed",
     {"moscow": "Could", "phase": "Release 2", "owner": "Tom Okafor", "implemented-by": "Both", "vendor-ref": "", "raised-on": "25 August 2026", "closed-on": "", "updated": "25 August 2026"},
     {"Source": "Billing workshop, 25 August 2026", "Notes": "Later phase; excluded from the weekly view."}, [])
item("REQ-0018", "Retain legacy carrier handoff file format", "Withdrawn",
     {"moscow": "Won't", "phase": "Day one", "owner": "Elena Marchetti", "implemented-by": "Internal", "vendor-ref": "", "raised-on": "20 August 2026", "closed-on": "2 September 2026", "updated": "2 September 2026"},
     {"Source": "T001/701:0 | Elena Marchetti | 00:41:12 | \"we do not need the old handoff file any more\"", "Notes": "Legacy practice; recorded as Won't and withdrawn."}, [])

# --- Limitations ---
item("LIM-0021", "Vendor design assigns one port per order regardless of site count", "Under assessment",
     {"owner": "Adam Moyes", "chosen-option": "", "implemented-by": "Vendor", "vendor-ref": "VND-DR-07", "raised-on": "1 September 2026", "closed-on": "", "updated": "8 September 2026"},
     {"Impact": "A split-site multi-gig order lands with one port and the second site is left unprovisioned until someone notices. About three orders a month.",
      "Options": "1. Vendor changes the port allocation rule; impact: vendor estimate 6 weeks, cost TBC; phase: Day one\n2. Operations assigns the second port by hand from a weekly report; impact: 2 hours a week, Priya's team; phase: Day one\n3. Do nothing; impact: three customers a month get a delayed second site; phase: Day one",
      "Source": "Vendor design review, 1 September 2026, VND-DR-07 §3", "Notes": ""},
     ["constrains REQ-0014", "assessed by OI-0045"])
item("LIM-0022", "Platform holds one notification channel per customer", "Identified",
     {"owner": "Martin Vasquez", "chosen-option": "", "implemented-by": "Vendor", "vendor-ref": "", "raised-on": "9 September 2026", "closed-on": "", "updated": "9 September 2026"},
     {"Impact": "REQ-0015 needs email and SMS on day one; the platform can send to one channel.", "Options": "", "Source": "T002/88:0-1 | Martin Vasquez | 00:06:40 | \"one channel per customer, that is how the object is built\"", "Notes": "Not yet assessed. Needs an open item."}, ["constrains REQ-0015"])
item("LIM-0023", "Address validation rejects unit numbers with a slash", "Resolved",
     {"owner": "Adam Moyes", "chosen-option": "", "implemented-by": "Vendor", "vendor-ref": "VND-DEF-3", "raised-on": "26 August 2026", "closed-on": "5 September 2026", "updated": "5 September 2026"},
     {"Impact": "About 40 addresses a month failed validation.", "Options": "", "Source": "Vendor defect VND-DEF-3 closed 5 September 2026; retest passed", "Notes": "Vendor conformance path: held to the agreed requirement, no CR."}, ["constrains REQ-0014"])

# --- Decisions ---
item("DEC-0009", "Represent a customer service as two linked services, not a bundle", "Accepted",
     {"owner": "Adam Moyes", "consulted": "Martin Vasquez; Priya Nair", "approved-by": "Change board", "implemented-by": "Both", "raised-on": "27 August 2026", "closed-on": "3 September 2026", "updated": "3 September 2026"},
     {"Rationale": "Both work. The bundle object hides the access service from support tooling, so linked services were chosen.", "Source": "Design doc §3.1", "Notes": ""}, ["addresses REQ-0014"])
item("DEC-0010", "Provision access before delivery because the platform enforces it", "Proposed",
     {"owner": "Adam Moyes", "consulted": "Martin Vasquez", "approved-by": "", "implemented-by": "Both", "raised-on": "24 August 2026", "closed-on": "", "updated": "24 August 2026"},
     {"Rationale": "Nothing is lost; the ordering is now fixed by the platform.", "Source": "T001/220:0 | Martin Vasquez | 00:12:03 | \"access has to exist first\"", "Notes": "Stale: Proposed for more than 14 days."}, ["proposed by OI-0038"])

# --- Risks ---
item("RSK-0002", "Vendor build slips past the day-one date", "Mitigating",
     {"kind": "Risk", "owner": "Adam Moyes", "likelihood": "M", "impact": "H", "due": "18 September 2026", "raised-on": "28 August 2026", "closed-on": "", "updated": "4 September 2026"},
     {"Trigger": "Vendor sprint burndown shows more than two weeks of scope remaining at sprint 6 review.", "Mitigation": "Weekly vendor delivery review; scope held to Must requirements.", "Source": "Delivery review, 28 August 2026", "Notes": ""}, [])
item("RSK-0003", "Manual port assignment volume outgrows the operations team", "Identified",
     {"kind": "Risk", "owner": "Priya Nair", "likelihood": "L", "impact": "M", "due": "2 September 2026", "raised-on": "22 August 2026", "closed-on": "", "updated": "22 August 2026"},
     {"Trigger": "More than 20 split-site orders in one week.", "Mitigation": "", "Source": "Stakeholder forum, 22 August 2026", "Notes": "Review date has passed."}, [])

item("RSK-0004", "Vendor delivers the port allocation change by 30 September", "Mitigating",
     {"kind": "Dependency", "owner": "Vendor: Martin Vasquez", "likelihood": "M", "impact": "H", "due": "23 September 2026", "raised-on": "5 September 2026", "closed-on": "", "updated": "5 September 2026"},
     {"Trigger": "30 September passes without the change in the test environment, or the vendor says it slips.", "Mitigation": "Adam checks the vendor sprint review each Tuesday; escalate to the change board at the first slip.", "Source": "Vendor sprint plan, 5 September 2026", "Notes": ""}, [])
item("RSK-0005", "The billing adapter can merge two service lines at rating time", "Identified",
     {"kind": "Assumption", "owner": "Tom Okafor", "likelihood": "L", "impact": "M", "due": "", "raised-on": "26 August 2026", "closed-on": "", "updated": "26 August 2026"},
     {"Trigger": "Billing SME confirms rating happens per service line with no merge hook.", "Mitigation": "", "Source": "Billing workshop, 26 August 2026", "Notes": "Underpins CR-0002. Not yet verified."}, [])

# --- Open items ---
item("OI-0031", "Write the design section for multi-gig port allocation", "Closed",
     {"owner": "Adam Moyes", "due": "29 August 2026", "raised-on": "21 August 2026", "closed-on": "3 September 2026", "updated": "3 September 2026"},
     {"Next action": "", "Source": "Stakeholder forum, 21 August 2026", "Notes": ""}, ["resolves into REQ-0014"])
item("OI-0033", "Write the design section for order notifications", "Open",
     {"owner": "Adam Moyes", "due": "16 September 2026", "raised-on": "1 September 2026", "closed-on": "", "updated": "1 September 2026"},
     {"Next action": "Draft §4.5 once LIM-0022 is assessed", "Source": "Design planning, 1 September 2026", "Notes": ""}, [])
item("OI-0038", "Get DEC-0010 to the change board", "Blocked",
     {"owner": "Adam Moyes", "due": "10 September 2026", "raised-on": "24 August 2026", "closed-on": "", "updated": "6 September 2026"},
     {"Next action": "Blocked: waiting on vendor written confirmation of the ordering rule", "Source": "Design planning, 24 August 2026", "Notes": ""}, [])
item("OI-0040", "Agree REQ-0016 wording and priority with Priya", "Open",
     {"owner": "Priya Nair", "due": "12 September 2026", "raised-on": "22 August 2026", "closed-on": "", "updated": "22 August 2026"},
     {"Next action": "Confirm whether a weekly report is enough or a queue is needed", "Source": "Stakeholder forum, 22 August 2026", "Notes": ""}, [])
item("OI-0045", "Assess LIM-0021 and take a chosen option to the change board", "Open",
     {"owner": "Adam Moyes", "due": "12 September 2026", "raised-on": "1 September 2026", "closed-on": "", "updated": "8 September 2026"},
     {"Next action": "Present the three options with the vendor estimate at the 11 September forum", "Source": "Vendor design review, 1 September 2026", "Notes": ""}, [])
item("OI-0046", "Assess LIM-0022 against REQ-0015", "Open",
     {"owner": "", "due": "", "raised-on": "9 September 2026", "closed-on": "", "updated": "9 September 2026"},
     {"Next action": "", "Source": "T002, 9 September 2026", "Notes": "Register defect on purpose: no owner, no next action."}, [])

# --- Change requests ---
item("CR-0001", "Add SMS as a second notification channel", "For approval",
     {"owner": "Adam Moyes", "chosen-option": "Vendor adds a channel list to the customer object and a second sender", "estimate": "$48,000; 5 weeks; vendor quote Q-2291, 8 September 2026", "approved-by": "", "phase": "Day one", "implemented-by": "Vendor", "vendor-ref": "", "raised-on": "5 September 2026", "closed-on": "", "updated": "8 September 2026"},
     {"Reason": "Day-one customers expect a text as well as an email; without it the contact centre handles the confirmation calls that the SMS would prevent.", "Source": "CR page: cr-0001-options.md", "Notes": ""},
     ["triggered by REQ-0015", "delivers REQ-0015", "worked by OI-0033"])
item("CR-0002", "Single invoice line for split-site orders", "Deferred",
     {"owner": "Tom Okafor", "chosen-option": "Billing adapter merges the two service lines at rating time", "estimate": "$20,000; 3 weeks; internal estimate, 26 August 2026", "approved-by": "Change board", "phase": "Release 2", "implemented-by": "Both", "vendor-ref": "", "raised-on": "26 August 2026", "closed-on": "2 September 2026", "updated": "2 September 2026"},
     {"Reason": "Customers with two sites receive two lines for one order and ring billing. Deferred to Release 2 with the board's approval.", "Source": "Change board, 2 September 2026", "Notes": ""},
     ["triggered by REQ-0017", "delivers REQ-0017"])

# --- a seeded change set, open, from an earlier console session, so the overlay shows on first load ---
open(os.path.join(ROOT, "change-sets", "CS-0001.md"), "w", encoding="utf-8").write("""# Change set: CS-0001

- Change set: CS-0001
- Session: solution-workflows console 0.1
- Session date: 10 September 2026
- Made by: Priya Nair
- Meeting: operations weekly
- Session closed: 10 September 2026
- Approver:
- Approved on:

### Item 1 | RSK | Confident
- Target: RSK-0003
- Grade: Confident
- Verdict:
- From: Identified
- Based on: 22 August 2026
- Status: Mitigating
- Mitigation: Weekly split-site report from the order system; second port assigned within two working days.
- Due: 8 October 2026
- Evidence:
  - 10 September 2026 | Priya Nair | operations weekly
- Gist: Ops has a report now, so the risk is being mitigated rather than just identified.

### Item 2 | OI | Confident
- Target: OI-0040
- Grade: Confident
- Verdict:
- Next action: Priya to confirm the weekly report is enough by 15 September
- Due: 15 September 2026
- Evidence:
  - 10 September 2026 | Priya Nair | operations weekly
- Gist: New next action after the weekly.

""")
# --- pulled Confluence pages for the baseline mode, as the runbook's pull step would write them ---
sb = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sample-baseline")
os.makedirs(os.path.join(ROOT, "baseline"), exist_ok=True)
for f in os.listdir(sb):
    shutil.copy(os.path.join(sb, f), os.path.join(ROOT, "baseline", f))
print("sample engagement written to", ROOT)
