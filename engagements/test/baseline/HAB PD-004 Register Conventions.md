---
page-id: 3401220118
page-title: HAB PD-004 Register Conventions
page-version: 
page-url: https://example.atlassian.net/wiki/spaces/Restitch/pages/3401220118/HAB+PD-004+Register+Conventions
parent-page-id: 3401220005
pulled-on: 12 September 2026
---

# HAB PD-004 Register Conventions

## Register: Conventions

How to add or move an item by hand. This condenses the model (the solution register model, sections 2 to 5 and 8); the model is the authority and this page is the working summary.

## The one principle to remember

Open items are the working queue. Everything else is a record. An open item closes only by creating or changing a record: a decision gets accepted, a limitation gets dispositioned, a change request gets raised, a requirement gets clarified, a risk gets retired. In a meeting you review one filtered list of open items; the registers behind them stay stable.

A design document never holds the master copy of an item. It references items by id.

## Which register does this belong in

| You have | It goes in |
|---|---|
| We need the solution to do X | Requirements |
| We chose how, or accepted a constraint | Decisions |
| The solution will not do, or does differently, something we need | Limitations |
| Something might go wrong, is being taken on trust, or is owed by someone else | Risks, with Category saying which |
| Someone must do something before a record can change | Open items |
| Agreed scope or design must change, and it costs time, money or effort | Change requests |

Four kinds of thing come in, and the question beside each picks the type.

| Entry | Question | Usually becomes |
|---|---|---|
| Requirement | We need the solution to do X. | REQ |
| Discovery | The platform does, or does not, do X. | LIM if a need is now unmet; DEC if we must now design a certain way; OI first if uncertain |
| Ask | A stakeholder wants X changed. | OI, then CR or REQ |
| Event | A risk lands, an assumption fails, a review finds a gap. | OI, then whatever record the work produces |

## When to write a decision

Write one only when at least one of these is true:

there was a real choice between viable options and you picked one;

it constrains later design, such as a principle other decisions must follow;

it accepts something: a limitation you live with, a risk you carry knowingly, a vendor constraint;

someone will later ask "why did we do it this way?" and the answer is more than "the requirement said so".

Do not write a decision to restate a requirement, to put a requirement in or out of a phase (that is the requirement's Phase and Status), or for the vendor's routine implementation detail. That last rule is why this register holds 58 decisions rather than 209: the vendor's design-spec choices live in their documents and in the knowledge base, and are cited rather than copied.

Discovery: decision or limitation? Ask one question. After this, is something we need now not going to happen? If yes it is a limitation, and a decision appears only if the limitation is later accepted. If no, but we must now design a certain way, it is a decision that accepts a constraint. If the discovery is not yet certain, raise an open item to confirm it with the vendor first.

## States

| Type | States (terminal marked \*) |
|---|---|
| Requirement | Draft, Agreed, Designed, Delivered, Verified\, Deferred\, Withdrawn\* |
| Decision | Proposed, Accepted, Superseded\, Rejected\ |
| Limitation | Identified, Under assessment, Accepted\, Change requested\, Deferred\, Resolved\ |
| Risk | Identified, Mitigating, Realised\, Retired\ |
| Open item | Open, In progress, Blocked, Closed\* |
| Change request | Proposed, Submitted, Impact assessment, Approved, Rejected\, Delivered\ |

A limitation leaves Under assessment by exactly one path, and each path names the record carrying the outcome: Accepted needs a decision id, Change requested a change request id, Deferred a requirement id with Phase = next phase, Resolved needs evidence.

Accepted decisions are immutable. To change one, create a new decision, mark the old Superseded, and write "superseded by DEC-nnn" in the old one's Links.

## Relationships

Links are written as <relationship> <ID>, several separated by semicolons, and only need writing on one side.

| From | Relationship | To |
|---|---|---|
| DEC | addresses | REQ (only where a real choice was made) |
| DEC | introduces | LIM |
| DEC | raises | RSK |
| DEC | supersedes | DEC |
| LIM | constrains | REQ |
| LIM | dispositioned by | DEC, CR or REQ |
| LIM | assessed by | OI |
| RSK | realised as | OI |
| OI | resolves into | any |
| CR | triggered by | LIM or REQ |
| CR | delivers | REQ |
| CR | part of | CR |

Two link forms in use here that the model does not name: assessed by on a limitation, which model 4.4 sanctions in prose as "the assessing open item"; and one open item recorded as "the same underlying item as OI-nnn", for which the model has no vocabulary at all.

External ids are never rewritten and never resolve inside these registers: Loomtech's PL-nn, CR-nn, RQnnn, LInnn, DC-nn, AS-nn, EX-nn, and the Shopfront Responses register's BR-nnn and FS-nnn. They appear in Vendor ref, or in Links labelled as external.

## Two queries this register set answers

What is outstanding? Register: Outstanding, regenerated from the six registers. Open items not closed, grouped by owner; limitations still being assessed; high-impact or overdue risks; change requests not yet decided; stale proposals and drafts.

What is the Shopfront impact? Filter the Open items register's Links column on Shopfront impact. That list is also rendered at the foot of the outstanding view. Ruled 2026-09-07: Shopfront impact must stay queryable so the list can be generated for the Shopfront design phase.

## Where the ids came from

Ids were minted on 2026-09-07 and are never reused. Every register page carries a Prior ids appendix, and the generator keeps a high-water mark per prefix so a later run cannot renumber. Limitations are the exception: LIM-001 to LIM-017 keep their published numbering, and LIM-002 is retired and will not be reused.

## Known gaps, deliberately visible

| Gap | Items | Why |
|---|---|---|
| MoSCoW on requirements | 60 | the corpus holds design truth, not priority; the Scope Register records none for these |
| Owner, non-terminal requirements | 66 | the curated sources record groups, not people |
| Owner, non-closed open items | 12 | same - groups, not people |
| Owner is bare "Vendor", no named contact | 47 | a named vendor contact is wanted; Nadia Frost is named on three |
| Next action + Due, open open items | 54 | to be set in the first review |
| Due as review date, non-terminal risks | 15 | model 4.4 wants one before a risk is Mitigating; none is recorded upstream |
| Consulted, Accepted/Rejected decisions | 22 | genuinely unrecorded, and not inferred |
| Approved by + Approved on, CRs past assessment | 20 | the Scope Register records a status lozenge, never who approved it or when |
| Implemented by | 34 | mostly discovery-stage changes where nobody has decided who would build it |

Ruled 2026-09-07: none of these is invented. Blanks are filled by hand in the final document.

An item on the outstanding view without an owner, a next action and a due date is a defect in the register, not a discussion point. That is why the gaps are counted here rather than hidden.
