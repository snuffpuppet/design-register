# Solution register model

Version 2.28, 15 September 2026. Owner: Adam Moyes.

Version 2.28 lets an import be written into the registers before its review is complete and rationalised in place. Section 11 says a row that was neither rejected nor folded becomes an item and the review continues over the items, with the tool keeping its own record of what is still unreviewed. Section 7 says what a merge or a delete leaves behind in History and in version control. Nothing in sections 4, 5 or 9 changes.

Version 2.27 gives the item a Scope. Section 6 has said since 2.17 that a way of filtering by service or domain could be added when an engagement has several services to name, and an engagement with four technical services now does. Scope is declared per engagement rather than by this document: an engagement that names no scopes carries none and is checked by no scope rule, so nothing changes for a single-service engagement. Section 9 adds I24.

Version 2.26 lets a tool write item files directly. Section 7 adds an optional History section, one line per write, and section 11 says change sets are one of two ways a tool may write, chosen per engagement. The ingester's apply stage is unchanged and serves the change set mode.

Version 2.25 adds the supports rules. Sections 4.4 and 5 already say what must exist beside an item in a given state; a tool may read them as implications and offer the missing record prefilled, in its first state, with Approved by empty. Two link words are added for cases the sections implied without naming: a risk's mitigation actions are open items linked "mitigated by", and an accepted workaround that needs something built raises a requirement linked "needs". Rules I21 to I23 check them. Nothing changes for an item that already meets 4.4.

Version 2.24 narrows Vendor ref to the change request. It was the one field on a requirement or a limitation that pointed at a vendor document rather than describing our own item, and the vendor's own numbering for those lives in their specifications, which Source already cites. A change request keeps it because the vendor assigns a number to the change itself and we chase it by that number. A vendor reference on any other type goes in Source, as it already did for risks and open items.

Version 2.23 gives the risk a Kind: Risk, Assumption or Dependency. All three share the risk lifecycle and fields, so a programme manager can list the dependencies and assumptions from one register while nothing new needs working. No new types or states.

Version 2.22 restores the change request as the artefact the business approves: a For approval state, an Estimate field carrying the cost and time being approved, and Reason as the business justification in the CR's own words. It also names imports from an existing register table as a use of the change set pathway (11). This repository is the only place the model changes; the ingester in `solution-register` is left as it is and reads this document when it is next ported.

Version 2.21 reconciles two copies of this document. The copy in `solution-register/ingester/` reached 2.20 on 10 September through review (Scope removed, change requests removed, four-digit ids, named phases, stakeholder register, Due as a warning). The copy in `solution-workflows/` was taken at 2.15 and carried the limitation lifecycle work of 11 September under a colliding number. 2.21 takes 2.20 as its base and adds, from the 11 September work: a limitation must constrain a requirement before it is dispositioned; Withdrawn as a limitation exit; the vendor conformance path; the test for when accepting a limitation raises a risk; a change request type, trimmed to what a lifecycle needs; a field trim across every type so that an item can be maintained in a minute; and section 11, change sets, the pathway by which a lifecycle tool feeds changes back into the engagement.

This file describes how we track the artifacts of solution architecture on a project where we are the design authority and a vendor builds the platform. It is tool-agnostic. It says what the item types are, how they relate, how each one moves, and what a healthy register looks like. It does not say how to build or populate the registers in any particular tool; that belongs in the ingester and in the lifecycle tool, each of which reads this document.

The lifecycle from both entry points is drawn in the artifact "Two Ways Into the Registers".

---

## 1. Purpose and context

We specify a solution. The solution is ours and is wider than the vendor's platform: some of it is designed and built internally. The vendor architects, designs and builds their platform in collaboration with us and is consulted on our decisions; our own stakeholder groups and SMEs are consulted too. Approval always sits with us.

Our architects produce solution design documents and need to track, from our perspective:

- requirements
- decisions
- limitations
- risks
- open items
- change requests

The vendor keeps their own registers with their own ids, costs and timelines. We do not mirror those. We hold our view and reference theirs.

The goal is a set of registers that a person can open during a meeting and see what is outstanding, that can be maintained by hand with a minute of effort per item, and that a tool can maintain without a person retyping anything.

## 2. Principles

**Open items are the working queue. Everything else is a record.**
An open item closes only by creating or changing a record: a decision gets accepted, a limitation gets dispositioned, a change request gets raised, a requirement gets clarified, a risk gets retired. In a meeting we review one filtered list of open items. The registers behind them stay stable.

**A limitation is a gap against a requirement.**
A requirement says what we need and is owned by whoever stated the need. A limitation says what the solution cannot do, or does differently, and is a fact we or the vendor discovered. A limitation only matters because it leaves some need unmet, so every limitation that is assessed ends up linked to the requirement it constrains. If the need was never written down and the business confirms it is real, the assessment raises the requirement. If the business confirms there is no need, the limitation is withdrawn. A limitation never turns into a requirement; it reveals one or points at one. The requirement is what outlives the engagement.

**A limitation must be dispositioned, and each disposition links to a record.**
A limitation leaves Under assessment by exactly one path, and each path names the record that carries the outcome. The choice between living with it, working around it, holding the vendor to what was agreed, and asking for a change now or in a later phase is made on the limitation, in its Options. A change request exists only once that choice asks for a change, and it carries the change's whole life from there.

**One call, recorded once.**
A stakeholder makes one call per limitation. For a change, it is recorded as the change request's approval. For an acceptance, it is recorded as a decision. Never both.

**Registers and narrative are separate.**
Registers hold items. Solution design documents hold narrative and reference items by id. A design document never holds the master copy of an item. This is what lets design documents be split per service or combined without changing how tracking works.

**Every item traces to a source, and every change to a session.**
Not every item begins with a requirement. Each item records where it came from. Each change to an item arrives through a session, a transcript or a change set (11), that names who made it and when.

## 3. Entry points

Four kinds of thing come in, and the question beside each one picks the type.

| Entry | Question | Usually becomes |
|---|---|---|
| Requirement | We need the solution to do X. | REQ |
| Discovery | The platform does, or does not, do X. | LIM if a need is now unmet; DEC if we must now design a certain way; OI first if uncertain |
| Ask | A stakeholder wants X changed. | OI, then CR or REQ |
| Event | A risk lands, an assumption fails, a review finds a gap. | OI, then whatever record the work produces |
| Assumption | We are relying on X being true and have not confirmed it. | RSK, Kind Assumption; the verifying work is its mitigation open item |
| Dependency | We need X from another party, or Y cannot start until X. | RSK, Kind Dependency when the delivery is uncertain; otherwise a link, or a DEC that accepts the ordering |

Asks and events are work first and record later. Requirements and discoveries can go straight to a record.

## 4. Item types

### 4.1 Header fields (every item)

Every item carries these. The person field and the date fields have one name each across all types, so that a tool and a reader learn them once.

| Field | Rule |
|---|---|
| ID | Type prefix plus a four-digit zero-padded number: REQ-0014, DEC-0003, LIM-0021, RSK-0007, OI-0045, CR-0002. Never reused. Transcript ids are three digits (T001), episode ids are the transcript id plus E and a number (T001-E02), change set ids are CS plus four digits (CS-0003). |
| Title | One line, specific. |
| Status | One of the values for the type (4.2). |
| Owner | The one person field. On a requirement it is who stated the need and can say it is met. On an open item it is who does the work. On a decision, limitation, risk or change request it is who raised it, and the work that moves the item lives on an open item whose Owner is the worker. A named person on our side, "Vendor: <name>", "Joint", or a Forum row from the stakeholder register. Required while the item is not in a terminal state. |
| Implemented by | Vendor, Internal or Both. Whose build the item lands in. Required on requirements, decisions, limitations and change requests. Not used on risks or open items. |
| Scope | The service or area the item belongs to, from the engagement's Scopes list (6). One value, at the lowest level that applies. Required while the engagement declares scopes. Absent where it declares none. |
| Vendor ref | The vendor's number for the change itself, once they assign one. Used on change requests only. A vendor document reference on any other type goes in Source. |
| Links | Ids of related items, each with its relationship word (5). Links carries every relationship, including the disposition of a limitation and the resolution of an open item, so no type has a second column that repeats a link. |
| Raised on | Date the item was created, on every type. Replaces Identified on. |
| Closed on | Date the item entered its approved or terminal state, on every type. Replaces Decided on, Approved on and the open item's Closed on. Blank until then. |
| Source | Where the item came from: a design document and section, a claim id, a meeting date, a vendor document reference, or a transcript citation `Tnnn/utterance:fragments \| speaker \| timestamp \| quote`, one per exchange part. On an open item the same field carries the citation or meeting that raised it. |
| Updated | Date of last change. Stamped by the tool that writes the file, never by hand. |

Dropped from 2.20 and why: Identified on, Decided on and the old Closed on were one date under three names. Disposition record, Resolution and Blocked by each repeated a link or a sentence that Links or Next action already carries. Vendor ref on risks and open items was optional and never filled. Raised by is folded into Owner as the one person field, since each type had exactly one of them and the rule for which one was the only thing a reader had to remember.

### 4.2 Types, states and type-specific fields

Terminal states are marked *.

| Type | Prefix | States | Type-specific fields |
|---|---|---|---|
| Requirement | REQ | Draft, Agreed, Designed, Delivered, Verified*, Withdrawn* | MoSCoW (Must / Should / Could / Won't), Phase (a name from the engagement's Phases list) |
| Decision | DEC | Proposed, Accepted, Superseded*, Rejected* | Rationale (short, naming the rejected option where there was one), Consulted (vendor, SMEs, stakeholder groups who had input), Approved by (the person or forum on our side who made it stick) |
| Limitation | LIM | Identified, Under assessment, Accepted*, Change requested*, Resolved*, Withdrawn* | Impact (one line: what it means for the customer or the operation), Options (numbered list, each `n. <option>; impact: <cost and time, or effort and who>; phase: <phase>`), Chosen option (the option number) |
| Risk | RSK | Identified, Mitigating, Realised*, Retired* | Kind (Risk, Assumption or Dependency), Likelihood (L/M/H), Impact (L/M/H), Trigger (the observable event that says the risk has become real), Mitigation (what is being done, as text), Due (next review date) |
| Open item | OI | Open, Blocked, Closed* | Next action (one line; while Blocked it starts "Blocked: " and says by what), Due |
| Change request | CR | Proposed, For approval, Approved, Submitted, Deferred, Delivered*, Withdrawn*, Rejected* | Reason (the business justification, in one or two sentences: what the change buys and for whom, written for the approver even where the requirement says it at length), Chosen option (one line: what will be built, chosen from the options on the triggering limitation or requirement), Estimate (the cost and time being approved, as `<cost>; <duration>; <source and date of the estimate>`), Approved by (the person or forum that approved the estimate), Phase (the named phase the change lands in) |

Dropped from earlier versions and why: the requirement's Deferred state said what Phase already says. The open item's In progress state carried nothing that Next action does not. The change request's Options state, Options list, Consulted and CR page repeated the work already done on the limitation; the CR decides how, and the how is one line on the row with the design on a page named in Source. For approval stays, because the change request is what the business sees when it approves cost, and the register must show what is waiting on them.

### 4.3 Use it when

| Type | Use when |
|---|---|
| Requirement | We need the solution to do something. Owned by whoever stated the need, because they can say whether it has been met. |
| Decision | We chose how, or accepted a constraint or a shortfall. See 4.5. |
| Limitation | The solution will not do, or does differently, something we need. A fact about the solution, not a piece of work. Title says what the solution does; Impact says why we care; Options says what we could do about it and Chosen option says what we decided. |
| Risk | Something might go wrong. A record with a review date. Mitigation actions are open items with their own owners. Anyone who sees the trigger happen raises an open item and the risk moves to Realised. Kind says what sort of uncertainty it is, and the fields read accordingly: for a **Risk**, Trigger is the event, Mitigation is what is being done, Retired means no longer possible or worth tracking. For an **Assumption**, Trigger is evidence that it is false, Mitigation is how and when it will be verified, Realised means it was false, Retired means verified true or replaced by a decision. For a **Dependency**, Trigger is the date passing or the other party saying it slips, Mitigation is the chase plan and who chases, Realised means it slipped, Retired means delivered. Likelihood and Impact are the chance and cost of the assumption being wrong or the dependency slipping. The party and the needed-by date go in the Trigger text; a dependency on the vendor may have Owner "Vendor: <name>". |
| Open item | Someone must do something before a record can change. The only thing you work. |
| Change request | We have decided to ask for a change to agreed scope or design, now or in a named later phase, and it costs time, money or effort. One row for the whole life of the change, with the vendor's number in Vendor ref once they assign one. It is the artefact the business approves: Reason is the justification in the approver's terms, Estimate is the number they approve, and Approved by is who approved it. Whether to change at all is never a CR question: it was answered on the limitation's Options or by the requirement's open item. |

### 4.4 Transition rules

- **Requirement.** MoSCoW is required from Draft onwards. Won't means agreed as out of this project and is recorded rather than deleted; a need wanted later is Must, Should or Could with Phase set to a later phase. A requirement carries no next action: work to get it agreed, designed or verified is an open item in Links, and a requirement in Draft must have one. Designed means a section of a design document, ours or the vendor's, covers it, and Source or Links points at that section. A decision link is needed only where a real choice was made. Most requirements never have a decision. An accepted limitation adds no state to the requirement: the "constrains" link and the accepting DEC are the record of the shortfall, and the requirement keeps moving to Delivered and Verified with that shortfall known. Only when the accepted option leaves the need wholly unmet does the requirement change: MoSCoW Won't if the need is out of this project, or Phase set to the later phase alongside the limitation's Deferred CR.
- **Decision.** While Proposed, an open item in Links carries the worker and next action. Accepted or Rejected needs Approved by, Closed on and at least one Consulted entry, and Approved by is ours. Accepted is immutable. To change an accepted decision, create a new one, mark the old one Superseded, and write "superseded by DEC-nnnn" in the old one's Links.
- **Limitation.** Under assessment needs an open item in Links carrying the worker and next action. The first job of that open item is to find the requirement the limitation constrains and write "constrains REQ-nnnn" in Links. Three cases: an Agreed requirement already covers it, and the link is written; no requirement covers it and the stakeholder confirms the need, and the open item raises a REQ in Draft with that stakeholder as Owner; no requirement covers it and the stakeholder confirms there is no need, and the limitation goes to Withdrawn with the reason in Source. A limitation cannot leave assessment by Accepted or Change requested without a constrains link. The link also settles who pays: a limitation against an Agreed requirement the vendor has already accepted, with Implemented by Vendor, is a non-conformance. The usual Options then include "hold the vendor to the requirement; impact: none to us; phase: this phase", and if that option is chosen the assessing open item tracks the vendor fix and the limitation goes to Resolved with the evidence, without a DEC or a CR. Impact, at least two Options, each with an impact and a phase, and a Chosen option must be filled before the limitation leaves assessment by Accepted or Change requested; a vendor estimate is an input to Options, not a state. From Under assessment, exactly one of: Accepted (the chosen option is to live with it or to work around it; Links gains "dispositioned by DEC-nnnn"), Change requested (the chosen option asks for a change; Links gains "dispositioned by CR-nnnn", the CR created in Proposed for this phase or in Deferred with Phase set for a later one), Resolved (evidence in Source or Links; no options needed), Withdrawn (the discovery was wrong or there is no need; reason in Source; no options needed). A limitation in Change requested whose CR ends Withdrawn or Rejected returns to Under assessment with a new open item, keeps the old link as "previously dispositioned by CR-nnnn", and is dispositioned again, usually Accepted with a DEC.
- **Risk.** Kind is set when the row is created and does not change; a dependency that turns out to be an assumption is a new row. Mitigating needs Trigger, Mitigation and Due filled; the review happens in the weekly routine, and whoever runs it updates Likelihood, Impact, Mitigation and the next Due. Realised is set when the Trigger is observed and must create an OI, linked "realised as". Retired needs a one-line reason in Mitigation. Where the mitigation is a decision, the DEC carries "raises RSK-nnnn" and that is enough.
- **Open item.** Blocked means Next action starts "Blocked: " and names the id or reason; it is cleared when the item leaves Blocked. Closed needs Closed on and a "resolves into" link to the record it produced or changed. If nothing was produced, Links carries "resolves into none: <reason>"; acceptable but rare.
- **Change request.** Links carries "triggered by" the limitation or requirement whose chosen option asked for the change. Proposed means ours and being shaped: Reason and Chosen option are written, the design for the chosen option is put on a page named in Source, and the estimate is obtained. For approval means the CR is with the business: Reason, Chosen option and Estimate must be filled before it enters, and it stays there until the approver acts. Approved needs Approved by, Closed on and Phase. Submitted means handed to whoever will implement it; with Implemented by Vendor, Submitted needs a Vendor ref. Delivered is set when the change is built and the requirement it delivers moves. Deferred means the change will be made in a named later phase and is waiting for it: it needs Phase, Approved by and Closed on, carries no open item, and is reviewed at phase planning, when it moves to Proposed and the work resumes on the same row. Withdrawn means we chose not to pursue the change after all, usually because the estimate made a workaround the better option; the triggering limitation returns to Under assessment, or the triggering requirement's open item reopens. Rejected means whoever approves or implements it said no; the same return applies. Approved, Deferred, Withdrawn and Rejected each need Approved by and Closed on. A CR in Proposed, For approval or Submitted must have an open item in Links carrying the worker and next action; while For approval, the open item's next action is the approval meeting or the chase. A change with Implemented by Both stays one row unless the vendor part and the internal part are approved separately, in which case it is two rows linked "part of".

### 4.5 When to write a decision

A requirement says what the solution must do. A decision records a choice or an accepted trade-off. Write a decision only when at least one of these is true:

- There was a real choice between viable options, and you picked one.
- It constrains later design, such as a principle or standard other decisions must follow.
- It accepts something: a limitation you live with or work around, a risk you carry knowingly, a vendor constraint you design around. The decision's Rationale names the limitation's chosen option and the options it beat.
- Someone will later ask "why did we do it this way?" and the answer is more than "the requirement said so".

Do not write a decision to restate a requirement, to put a requirement in or out of a phase, for the vendor's routine implementation detail, or to approve a change request. The CR's Approved by is that decision.

**Discovery: decision or limitation?** Ask one question: after this, is something we need now not going to happen? If yes, it is a limitation, and a decision appears only if the limitation is later accepted. If no, but we must now design a certain way, it is a decision that accepts a constraint. If the discovery is not yet certain, raise an open item to confirm it with the vendor first. If the discovery is certain but nobody can say whether we need the thing, because no requirement mentions it, raise the limitation anyway: the assessing open item asks the stakeholder, and the answer either raises the requirement or withdraws the limitation.

**Accepting a limitation: does it raise a risk?** A limitation is a fact and a risk is an uncertain future event. Most accepted limitations have a certain consequence, and that consequence is already written in the limitation's Impact and the decision's Rationale. A risk is raised from the accepting DEC only when the residual consequence is uncertain enough to need a trigger and a review date: accepting a manual workaround, say, with the risk that volume outgrows the team. Fixing a limitation raises no risk from the limitation itself.

**A workaround that needs tooling** is a need in its own right. If the accepted option requires something to be built internally, such as a report to find the affected cases, raise a REQ with Implemented by Internal, owned by whoever will use it. It gets its own design like any other requirement.

Examples:

- The platform requires an access service to exist before a delivery service is provisioned. Nothing is lost, the ordering is now fixed. Decision: "Provision access before delivery, because the platform enforces it." Consulted: vendor. Implemented by: Both.
- The platform can represent a customer service as a bundle object or as two linked services. Both work. We choose linked services because the bundle hides the access service from support tooling. Decision, recording the rejected option.
- The platform holds one notification channel per customer and a Must requirement needs email and SMS on day one. Limitation constraining that requirement, assessed through an open item. A decision appears only if we accept the shortfall; a change request appears if we ask the vendor to add the second channel.

## 5. Relationships

Links are written as `<relationship> <ID>`, several per item as a list. A link only needs to be written on one side; the index derives the reverse.

| From | Relationship | To |
|---|---|---|
| DEC | addresses | REQ (only when a real choice was made) |
| DEC | introduces | LIM |
| DEC | raises | RSK |
| DEC | supersedes | DEC (the old decision also carries "superseded by") |
| LIM | constrains | REQ (required before Accepted or Change requested; the REQ may be raised by the assessment) |
| LIM | dispositioned by | DEC or CR (a later disposition keeps the earlier one as "previously dispositioned by") |
| LIM, DEC, CR, REQ | assessed by, proposed by, worked by | OI (the open item carrying the work while the record is not terminal) |
| RSK | realised as | OI |
| OI | resolves into | any, or "none: <reason>" |
| CR | triggered by | LIM or REQ |
| CR | delivers | REQ |
| CR | part of | CR (when a Both change is split into a vendor row and an internal row) |
| REQ | replaces | A current-state claim, PRC-nnnn.sN or SYS-nnnn.fN |
| REQ | preserves | A current-state claim |
| OI | clarifies | A current-state claim that is Hedged or Contested, or a question on a process |
| RSK | mitigated by | OI (one per mitigation action) |
| LIM | needs | REQ with Implemented by Internal (the tooling an accepted workaround requires) |

Current-state claims live in the engagement's current-state record, defined in `extraction-solution-design.md` section 4. A `replaces` or `preserves` link may target only a claim in Current or Current, not needed.

## 6. Scope

Scope names the service or area an item belongs to. The engagement declares its own values, because the useful split differs by engagement: one delivering four technical services splits by service, one delivering a single platform splits by nothing at all.

Each item carries one Scope, at the lowest level that applies. An integration issue between two technical services is tagged at the customer-service level above them. There is no programme level, because the registers sit inside the programme and the programme is implied.

An engagement with one service declares no scopes. Its items carry no Scope, nothing asks for one, and I24 never fires. Scope was removed in 2.17 for exactly that case and returns in 2.27 for the other one.

## 7. Register layout

One file per item, named by its id, in a folder per type: `requirements/REQ-0004.md`, `decisions/`, `limitations/`, `risks/`, `open-items/`, `change-requests/`. The file opens with a YAML frontmatter block holding the header fields in 4.1 and the short type-specific fields, in kebab-case (`raised-on`, `closed-on`, `implemented-by`, `vendor-ref`, `links` as a list). Long fields sit in the body under fixed headings: Source (one citation or reference per line), Rationale, Impact, Options, Reason, Trigger, Mitigation, Next action, Notes, and optionally History, one line per write made by a tool in the form `date | person | move | gist | evidence`. A change to one item is a change to one file, and the item's history is that section together with the file's history in version control.

When a tool merges one item into another or deletes one, the surviving item's History line says what was folded in or removed, every item whose Links named the removed id has that link rewritten or dropped with a History line of its own, and version control holds the removed file.

Frontmatter per type, in this order:

| Type | Frontmatter keys |
|---|---|
| REQ | id, title, status, scope, moscow, phase, owner, implemented-by, links, raised-on, closed-on, updated |
| DEC | id, title, status, scope, owner, consulted, approved-by, implemented-by, links, raised-on, closed-on, updated |
| LIM | id, title, status, scope, owner, chosen-option, implemented-by, links, raised-on, closed-on, updated |
| RSK | id, title, status, scope, kind, owner, likelihood, impact, due, links, raised-on, closed-on, updated |
| OI | id, title, status, scope, owner, due, links, raised-on, closed-on, updated |
| CR | id, title, status, scope, owner, chosen-option, estimate, approved-by, phase, implemented-by, vendor-ref, links, raised-on, closed-on, updated |

The meeting view is a set of generated index tables, one per type, rendered from the frontmatter and never edited by hand. Each index shows the frontmatter keys above, with Links rendered as text. One supporting page sits beside the indexes: a conventions page that condenses sections 2 to 5 and 8 for people adding items by hand.

## 8. What "outstanding" means

The meeting view is:

1. Open items not Closed, sorted by Due, grouped by Owner, with Blocked ones marked.
2. Limitations in Identified or Under assessment, oldest Raised on first.
3. Risks in Identified or Mitigating with Impact H, and any risk whose Due has passed, of every Kind.
4. Change requests in For approval first, then Proposed and Submitted.
5. Decisions in Proposed older than 14 days.
6. Requirements in Draft older than 14 days, measured from Raised on.

Requirements whose Phase is later than the current phase, and change requests in Deferred, are excluded from this view. They appear on a later-phase view: deferred CRs grouped by Phase, each with the limitation or requirement that triggered it, then requirements by Phase. That view is reviewed at phase planning, when each deferred CR for the starting phase moves to Proposed and gets an open item.

Anything on the outstanding view without an owner and a next action, on it or on its open item, is a defect in the register, not a discussion point.

## 9. Integrity rules

Run against a proposed set before writing it, and on request during maintenance. Each rule reports the ids that fail. Numbers are kept stable from 2.20; retired rules stay listed.

| Rule | Check |
|---|---|
| I1 Unique ids | No id appears twice across all registers. |
| I2 Valid status and required fields | Every status is an exact 4.2 value for its type. Every item has Raised on. Every requirement has MoSCoW. Every limitation has Impact once past Identified, and at least two Options and a Chosen option once Accepted or Change requested. Every risk has Kind, and Trigger and Mitigation once Mitigating. Every change request has Reason, Chosen option and Estimate once past Proposed; Approved by and Phase once Approved, Submitted, Delivered or Deferred; and Vendor ref once Submitted with Implemented by Vendor. Every item in an approved or terminal state has Closed on. |
| I3 Owner present | Every non-terminal item has an Owner that resolves under I19. A requirement in Draft, a decision in Proposed, a limitation in Under assessment and a change request in Proposed, For approval or Submitted must each have an open item in Links whose Owner is set. |
| I4 Next action present | Every open item not Closed has Next action. Due is a warning on open items and risks: wanted, but a missing date does not block a write. |
| I5 Phase valid | Every requirement's Phase, and every change request's Phase once set, is a name in the engagement's Phases list. |
| I6 Link targets exist | Every id in Links exists in some register. |
| I7 Limitation disposition | Every LIM in Accepted has a "dispositioned by DEC-nnnn" link to a DEC in Accepted. Every LIM in Change requested has a "dispositioned by CR-nnnn" link to a CR not in Withdrawn or Rejected. Every LIM in Accepted or Change requested has a "constrains REQ-nnnn" link. No LIM in Identified or Under assessment has a dispositioned by link. Every LIM in Withdrawn has a reason in Source. A "previously dispositioned by" link names a DEC in Superseded or a CR in Withdrawn or Rejected. |
| I8 Decision supersession | Every DEC in Superseded has a "superseded by" link pointing at a DEC in Accepted or Proposed. |
| I9 Open item resolution | Every OI in Closed has Closed on and a "resolves into" link. Every OI in Blocked has a Next action starting "Blocked: ". |
| I10 Change request approval | Every CR in Approved, Submitted, Delivered, Deferred, Withdrawn or Rejected has Approved by and Closed on. Every CR has a "triggered by" link to a LIM or REQ, and a CR triggered by a LIM in Change requested is that LIM's disposition. |
| I11 Decision approval | Every DEC in Accepted or Rejected has Approved by, Closed on and at least one Consulted entry. |
| I12 Implemented by | Every REQ, DEC, LIM and CR has Implemented by set to Vendor, Internal or Both. |
| I13 Realised risk | Every RSK in Realised has a "realised as OI-nnnn" link. |
| I14 Source present | Every item has a Source. |
| I15 Stale proposals | DEC in Proposed and REQ in Draft older than 14 days are listed as warnings. |
| I16 Decision without requirement | A DEC with no "addresses REQ" link and no "accepts" wording in its Rationale is listed as a warning. |
| I17 Deferred change request | Every CR in Deferred has a Phase naming a later phase and no open item in Links. |
| I18 Current-state links | Every `replaces`, `preserves` and `clarifies` target exists in the current-state record, and no `replaces` or `preserves` target is Retired or Withdrawn. |
| I19 Known stakeholder | Every person named in Owner, Approved by and Consulted resolves to a row in the engagement's stakeholder register, or is "Vendor: <name>", "Joint" or a Forum row. A row with Role Mentioned cannot be Owner. |
| I20 Forward transitions | A change to an existing item's Status follows an arrow in 4.4. The allowed return moves are LIM from Change requested to Under assessment, CR from Deferred to Proposed, and OI between Open and Blocked. Anything else is a failure and needs a new item, not an edit. |
| I21 Mitigation actions | Every RSK in Mitigating whose Mitigation names an action has a "mitigated by OI-nnnn" link to an open item not Closed. |
| I22 Workaround tooling | A LIM in Accepted whose chosen option needs something built has a "needs REQ-nnnn" link to a requirement with Implemented by Internal. Warning. |
| I23 Delivered change | Every CR in Delivered has a "delivers REQ-nnnn" link. |
| I24 Scope | Every item's Scope is one of the engagement's Scopes, and no item is without one, where the engagement declares any. Where the engagement declares none, the rule does not apply. |

I1 to I14, I17 to I21, I23 and I24 are failures. I15, I16 and I22 are warnings.

## 10. Maintenance routine

Before each project meeting:
1. Regenerate the outstanding view (8) from the registers.
2. Run the integrity rules. Fix I3 and I4 failures before the meeting, since those are the ones that make the meeting unproductive.

During the meeting:
3. Walk the outstanding view top to bottom. Every open item gets a new Next action and Due, or gets Closed with a resolves into link.
4. New items raised in the meeting get an id from the next free number, Source = meeting date, and an owner before the meeting ends.

Weekly:
5. Check Limitations in Under assessment for more than 14 days. Each one either gets dispositioned, by choosing one of its Options, or the open item that is assessing it gets a new Due.
5a. Review every risk whose Due has passed. Update Likelihood, Impact and Mitigation, set the next Due, or Retire it with a reason. If the Trigger has been seen, move it to Realised and raise an open item.
6. Check vendor refs. Where the vendor has closed or changed an item we reference, update our item and add a note in Source.

When a design document changes:
7. Any new tracking table in a design document is a defect. Move its rows to the register and mark the table as superseded with a link to the register.

A tool that runs these rules should offer the missing record for each failing item, prefilled from the item that implies it, and leave approval to a person.

## 11. Change sets: the second ingestion pathway

The ingester in `solution-register` writes item files through a gated stage. Transcripts are its first pathway. A change set is its second. A tool that lets a person run the lifecycle, a web console or a script, writes in one of two ways chosen per engagement: directly, rewriting the item file, stamping Updated and appending a History line, with version control as the record; or as a change set the ingester applies through the stage below. The direct way suits an engagement the ingester is not yet part of; the change set way keeps the ingester as the single point of change.

**What a change set is.** One file per working session of the tool, `change-sets/CS-nnnn.md`, dated and signed, holding the changes the session made in the same item block shape a dossier uses (ingester format F4). Its header carries:

```
- Change set: CS-0003
- Session: <tool name and version>
- Session date: 11 September 2026
- Made by: <person using the tool>
- Meeting: <meeting date or name, if the session was a meeting>
- Approver:
- Approved on:
```

Each block is `### Item n | <kind> | Confident` with `- Target: new` or an existing id, the field lines that are set or changed, and in place of transcript citations one or more `- Evidence:` lines in the form `<date> | <person> | <meeting, document or note>`. A block that changes Status also carries `- From: <status>` and `- Based on: <the target's Updated value as read>`. The `- Gist:` line says why, in one sentence, for the approver.

**How it is applied.** A new stage, apply change set, runs the same gates as the transcript write stage with two substitutions. The citation check is replaced by an evidence check: every Evidence line has a date and a person resolving under I19. The integrity check runs on the proposed set as now, with I20 enforcing that every status change is a forward move from the recorded From. A conflict is a block whose Based on differs from the target file's Updated, meaning the item changed after the tool read it; the block's Verdict is blanked and the approver settles it in the file. Approval is the same as for a dossier: Approver and Approved on filled, no blank verdict. On success the ingester writes the items, stamps Updated, logs one session log row per id, and re-renders the index. On failure it restores everything, as now.

**Imports.** An existing register held elsewhere, such as a table on a Confluence page or a row set in a claims-based knowledge base, comes in the same way: one change set per source page, every block `- Target: new`, the source's own id kept in Vendor ref or Source, the original column values mapped onto 4.1 and 4.2 fields, and an Evidence line naming the page, its version and the claim id where one exists. Columns the source has and this model does not are written into Notes, never into new fields. Items that cannot be mapped to a valid status are imported in the first state for their type with a Gist saying why, so the approver sees them.

An import may be written into the registers before its review is complete. Every row that was neither rejected nor folded into another becomes an item, in the mapped status where the source's status is one of the type's own states and otherwise in the first state, and the review continues over the items: duplicates are merged, rows that were never register items are deleted, and the records the states imply are created or linked. A tool that does this keeps its own record of which items are still unreviewed and shows it; the record is the tool's, never a field on the item.

**Why this shape.** The tool and the ingester share nothing but a folder and this document. The tool can be replaced or run in parallel with another. Every change carries who made it, when, on what evidence and against what version of the item, and the ingester's approval step is where conflicts are resolved, by the person who owns the engagement rather than by the tool. Nothing about the transcript pathway changes.

---

## Appendix. Source references

- MADR template primer: ozimmer.ch/practices/2022/11/22/MADRTemplatePrimer.html
- arc42 section 11, risks and technical debt: docs.arc42.org/section-11/
- Google Cloud architecture decision records overview: cloud.google.com/architecture/architecture-decision-records
- RAID log guide: smartsheet.com/content/raid-project-management
