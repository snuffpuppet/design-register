---
page-id: 3401220344
page-title: HAB PD-004 Decisions Register
page-version: 
page-url: https://example.atlassian.net/wiki/spaces/Restitch/pages/3401220344/HAB+PD-004+Decisions+Register
parent-page-id: 3401220005
pulled-on: 12 September 2026
---

# HAB PD-004 Decisions Register

## Register: Decisions

Holds the choices we made and the constraints we accepted, with the reasoning behind each.

One row per item. The conventions for adding or moving one by hand are in Register: Conventions.

Every row traces to a claim in the design knowledge base, to the PD-004 Scope Register, or to a recorded instruction from the solution architect. Source names which.

## Legend

### Status

| Value | What it means |
|---|---|
| Proposed | Reasoned, not yet approved. |
| Accepted | Approved. Change it by superseding, never by editing. |
| Superseded | Replaced by a later decision, named in Links. |
| Rejected | Considered and not taken. |

## Decisions

| ID | Title | Status | Rationale | Raised by | Consulted | Approved by | Decided on | Scope | Implemented by | Links | Source |
|---|---|---|---|---|---|---|---|---|---|---|---|
| DEC-001 | CarrierRibbon connect may be cancelled until the supply order completes, then PONR | Accepted | real choice — cancel allowed until supply completes, PONR after; resolves CONF-0089 | marta.quill |  | marta.quill | 2026-08-20 | CarrierRibbon | Vendor |  | C2357 — corpus/registers/conflicts.md#CONF-0089 - ruling by marta.quill 2026-08-20 on sources/backroom/FSD-Open-Issues-2026-08-11.vtt @ 00:25:37 (Nadia Frost, Loomtech) |
| DEC-002 | Derived RB properties live on the service, populated by RFS business rules | Accepted | real choice with stated rationale (service clarity, telemetry, naming) — DE012 |  |  |  |  | CarrierRibbon | Vendor |  | C0998 — HAB PD-004.7 - Carrier Ribbon |
| DEC-003 | Every configured Ribbon resource carries a human-readable unique id | Accepted | principle constraining later design — every RB resource needs a human-readable unique id (DE001/DE009) |  |  |  |  | CarrierRibbon | Vendor |  | C0985 — HAB PD-004.7 - Carrier Ribbon |
| DEC-004 | Appointment rescheduling is a GDA641 Modify, not an independent lifecycle object | SUPERSEEDED | explicit rejected option (appointments as independent lifecycle objects); endorsed and approved 2025-12-09 |  |  |  | 2025-12-09 | Order handling | Vendor |  | C0350 — HAB KDD-PD-004.OSF.2 - Appointment Rescheduling, Outcome Option 1 (ServiceOrder Modify) |
| DEC-005 | Inventory write order differs for characteristic-only and structural modifies | Accepted | design rule on write ordering; narrows C0220 | marta.quill |  | marta.quill | 2026-07-31 | Service model | Vendor |  | C2185 — User ruling (marta.quill) 2026-07-31: narrows C0220, which states the after-the-workshop-change rule unconditionally. Raised as the one same-level pair of the 2026-07-30 post-merge audit. KDD-3 keeps the rule as the default and carves out structural modifies; the narrowing states both halves so the unconditional form cannot be read as current truth. |
| DEC-006 | A Bolt error drops the order to MendingBench and re-triggers Bolt selection | Proposed | real choice on Bolt error handling (DE001, decided 2026-03-03) |  |  |  | 2026-03-03 | Fallout and intervention | Vendor |  | C0348 — HAB PD-004.4 - Orchestration, Decisions DE001 |
| DEC-007 | Manual fallout is raised at CFS level only; an atomic RFS rolls back silently | Accepted | principle — fallout raised at CFS level only, atomic RFS rolls back silently | marta.quill |  | marta.quill | 2026-07-28 | Fallout and intervention | Vendor |  | C1647 — User ruling (marta.quill) 2026-07-28: resolves the apparent contradiction between the four atomic-RFS fallout profiles ("offers no manual fallout option") and the RB3 claims asserting that a manual MendingBench fallout task IS raised on LotRegistry / Dispenser / Tallyboard / domain-controller-callback failures. It is a layer distinction, not a contradiction. |
| DEC-008 | Bench locations are supplier-specified and not grouped by address or site | Proposed | explicit choice: Bench locations NOT grouped by address or site (DE010) |  |  |  |  | Order handling | Vendor |  | C0359 — HAB PD-004.2 - Service Modelling, Location + Decisions DE010 |
| DEC-009 | Every RFS is a configuration service, and RFSs are reusable across CFSs | Proposed | principle other design must follow — every RFS is a configuration service (Pattern #3, DE006) |  |  |  |  | Service model | Vendor |  | C0354 — HAB PD-004.2 - Service Modelling, Pattern #3 + Decisions DE006 |
| DEC-010 | OrderStatus 'Held' introduced for orders parked in MendingBench or awaiting the Shopfront | Proposed | real choice — new OrderStatus 'Held' introduced (DE011, 2026-03-03) |  |  |  | 2026-03-03 | Service model | Vendor |  | C0357 — HAB PD-004.2 - Service Modelling, Decisions DE011 |
| DEC-011 | CFS is GDA641-orderable; RFS is not, and is modelled as a ConfigurationService | Accepted | the CFS/RFS standard the whole service model rests on | marta.quill |  | marta.quill | 2026-06-15 | Service model | Vendor |  | C0755 — User clarification 2026-06-15 (kb-resolve C0732): CFS vs RFS rule - RFS are not GDA641-orderable, generally ConfigurationServices (GDA640) |
| DEC-012 | No RFS is GDA641-orderable; an allocation RFS uses its own resource API | Accepted | narrows DEC-011: no RFS is GDA641-orderable; atomic RFS uses its own resource API | marta.quill |  | marta.quill | 2026-07-28 | Service model | Vendor | relates_to C0755 | C1652 — User ruling (marta.quill) 2026-07-28: restates C1040 narrowly. Its "strictly via GDA640 for ALL operations" was a drafting overreach - the ruling's real content was GDA641-vs-GDA640, and the GDA685-driven atomic-RFS case was not in view. The GDA641 prohibition is unchanged; the GDA640 assertion is scoped to ConfigurationService-style RFSes. |
| DEC-013 | Counter configured speed is the designed speed and excludes failover capacity | Accepted | accepts a semantic constraint — configured speed excludes failover capacity | marta.quill |  | marta.quill | 2026-07-25 | CustomerCounter | Vendor |  | C1118 — conversational ruling, fsd-refresh-2026-07 review |
| DEC-014 | SharedDepot modelling is not required for the Counter; the customer DEPOT is the only location input | Proposed | real choice — SharedDepot modelling not required for the Counter (DE003); supersedes C1010 |  |  |  |  | CustomerCounter | Vendor |  | C2356 — corpus/registers/conflicts.md#CONF-0088 - clarifying ruling on C1010, marta.quill 2026-08-20 (original: HAB PD-004.8 - Customer Counter Supply, page 3401221587 v35, DE003) |
| DEC-015 | Revenue bays are modelled multi-speed by capability, not by fixed fitting name | Proposed | real choice with rationale — capability field rather than fixed-speed fitting name (DE004/IS002) |  |  |  |  | CustomerCounter | Vendor |  | C1024 — HAB PD-004.8 - Customer Counter Supply |
| DEC-016 | On Counter decommission resource references are deleted and the service is left terminated | Proposed | real choice — resource refs deleted, service left terminated (DE001) |  |  |  |  | CustomerCounter | Vendor |  | C1036 — HAB PD-004.8 - Customer Counter Supply |
| DEC-017 | WVIs are sticky through machine change and released only at disconnect | Accepted | accepts a constraint — WVIs sticky through machine change (DE009); consequence tracked as a risk | peter.sund |  | peter.sund | 2026-08-14 | CustomerCounter | Vendor | the accumulating-deprecated-config consequence is RSK-018 | C2285 — kb-resolve feed 2026-08-14, ruling on CONF-0083 |
| DEC-018 | The system that places an order is responsible for cancelling it | Proposed | principle P001 — the system that places an order cancels it |  |  |  |  | Upstream Shopfront integration | Both |  | C0338 — HAB PD-004.10 - Upstream (Shopfront) Communications, Principles P001 |
| DEC-019 | The Backroom has full control over the lifecycle of its own orders | Proposed | principle P002 — the Backroom controls its own order lifecycle |  |  |  |  | Upstream Shopfront integration | Vendor |  | C0339 — HAB PD-004.10 - Upstream (Shopfront) Communications, Principles P002 |
| DEC-020 | The Backroom normalises supplier reason codes so the Shopfront carries no per-code logic | Proposed | principle — Backroom normalises supplier reason codes so the Shopfront carries no per-code logic |  |  |  |  | Upstream Shopfront integration | Both | Loomtech to provide the initial mappings — dependency RSK-010 | C0342 — HAB PD-004.10 - Normalised Upstream Communication |
| DEC-021 | Upstream order updates communicate intent broadly rather than supplier detail | Proposed | real choice — upstream updates communicate intent broadly (DE001, 2026-03-03) |  |  |  | 2026-03-03 | Upstream Shopfront integration | Both |  | C0343 — HAB PD-004.10 - Decisions DE001 |
| DEC-022 | Full normalisation of supplier messages into the Shopfront contract is semi-deferred | Proposed | accepts a deferral — full normalisation semi-deferred (DE002, 2026-03-03) |  |  |  | 2026-03-03 | Upstream Shopfront integration | Both |  | C0344 — HAB PD-004.10 - Decisions DE002 |
| DEC-023 | TPI cotton-pair selection applies to the MCAS cotton-terminating technologies | Accepted | accepts a reasoned inference as the TPI selection rule, explicitly re-openable; confirmed by C2201 | marta.quill |  | marta.quill | 2026-07-17 | MillhouseG4Supply | Vendor |  | C1041 — User ruling 2026-07-17 (kb-resolve C0981): TPI selection applies to any supply technology terminating at the premises on a cotton pair = MCAS membership (CTB/CTN/CTC); reasoned inference, no source states it + C2201 — Live page edit, HAB PD-004 Phase 1 Design Open Items (3401221361) v4, marta.quill 2026-08-06 - the OI-Millhouse-01 response, reconciled inbound (commit 9ab41c2) |
| DEC-024 | Jeopardy management is a Shopfront responsibility, not the Backroom | Proposed | principle — jeopardy management is a Shopfront responsibility (KDD OSF.5) |  |  |  |  | MillhouseG4Supply | Both |  | C0013 — KDD OSF.5 - Jeopardy Management |
| DEC-025 | Special processing and fallout are managed in the Shopfront via Conveyor events | Proposed | principle — special processing and fallout in the Shopfront via Conveyor (KDD OSF.7) |  |  |  |  | MillhouseG4Supply | Both |  | C0014 — KDD OSF.7 - Special Processing & Fallout Management |
| DEC-026 | Proof-of-Ownership is not passed to MillPortal; the earlier GDA641 carriage is rescinded | Proposed | real choice, and it rescinds an earlier decision (DI002 superseded by DI003) |  |  |  |  | MillhouseG4Supply | Vendor |  | C0982 — HAB PD-004.5 - Millhouse G4 Supply |
| DEC-027 | Backroom-classified Millhouse reason codes notify the Shopfront, move to MendingBench and set HELD | Proposed | real choice — Backroom-classified reason codes default to notify, MendingBench, HELD (DI004) |  |  |  |  | MillhouseG4Supply | Vendor |  | C0012 — HAB PD-004.5 - Millhouse G4 Supply (DI004) |
| DEC-028 | MillhouseG4Supply is both an SupplyService and a customer-facing service | Accepted | a ruling that fixes the service model and overrules part of C0009 | marta.quill |  | marta.quill | 2026-06-15 | MillhouseG4Supply | Vendor |  | C0754 — User clarification 2026-06-15 (kb-resolve C0732): MillhouseG4Supply is both an SupplyService and a CFS; CFS = GDA641-orderable, RFS = ConfigurationService/GDA640 |
| DEC-029 | WVI, WSI and TAPEID are single global pools, not per-Counter | Proposed | real choice with a rejected option — single global pools, not per-Counter | Vendor: Loomtech |  |  |  | Identifier and Reel management | Vendor |  | C0190 — Bobbin HLD v1.0.1 2.7.3 / Table 12 |
| DEC-030 | Terminated services are retained in inventory then batch-purged after a set period | Proposed | real choice — terminated objects retained for a configurable period then batch-purged | Vendor: Loomtech |  |  |  | Bobbin service and resource model | Vendor |  | C0215 — Bobbin HLD v1.0.1 2.9 Retention of Terminated Services |
| DEC-031 | Physical resources are released immediately on termination | Proposed | real choice — physical resources released immediately, independent of the logical purge | Vendor: Loomtech |  |  |  | Bobbin service and resource model | Vendor |  | C0216 — Bobbin HLD v1.0.1 2.9 Retention of Terminated Services |
| DEC-032 | Counter bay selection may target either a Bundle or a direct physical bay | Proposed | real choice — bay selection may target a Bundle or a direct physical bay; resolves Loomtech OI-12 | Vendor: Loomtech |  |  |  | Bay allocation | Vendor |  | C0200 — Bobbin HLD v1.0.1 Table 1 Open Issues OI-12 |
| DEC-033 | The model standardises on Bundle terminology rather than Bundle | Proposed | terminology standard other design must follow — Bundle, not Bundle; resolves Loomtech OI-11 | Vendor: Loomtech |  |  |  | Bay allocation | Vendor |  | C0201 — Bobbin HLD v1.0.1 Table 1 Open Issues OI-11 |
| DEC-034 | Bobbin manages SREELs and CREELs, and T&T uses single labelling | Proposed | real choice — T&T uses single labelling | Vendor: Loomtech |  |  |  | Identifier and Reel management | Both |  | C0185 — Bobbin HLD v1.0.1 2.7.2 Reel Management |
| DEC-035 | Reel Manager is authoritative for TradeCounter and Bolt Reel management, not Bobbin | Proposed | explicit rejected option — Reel Manager authoritative over Bobbin Number Management for TradeCounter/Bolt (DC-06) | Vendor: Loomtech |  |  |  | Identifier and Reel management | Both |  | C0326 — Orchestration HLD v1.0.1 - Design Decisions (DC-06) |
| DEC-036 | Bobbin is master for Counter and CarrierRibbon Reel allocation | Accepted | narrows DEC-035 — Bobbin is master for Counter/CarrierRibbon Reel allocation, coexisting with DC-06 | marta.quill |  | marta.quill | 2026-08-06 | Identifier and Reel management | Both |  | C2212 — kb-resolve feed 2026-08-06 (ruling-audit-resolve-2026-08-06), audit finding E; evidence sources/backroom/sequence-diagrams/L2VirtualConnectionDeliveryServiceConnect.png steps 6-10 |
| DEC-037 | A fresh Service Qualification check is performed inside the Connect workflows | Proposed | principle — a fresh SQ check inside the Connect workflows (DC-01) | Vendor: Loomtech |  |  |  | Solution scope and criteria | Vendor |  | C0295 — Orchestration HLD v1.0.1 - Design Decisions (DC-01) |
| DEC-038 | Supply order completion is the point of no return, except for disconnect | Proposed | principle — supply order completion is the PONR except for disconnect (DC-02) | Vendor: Loomtech |  |  |  | Solution scope and criteria | Vendor |  | C0296 — Orchestration HLD v1.0.1 - Design Decisions (DC-02) |
| DEC-039 | Error and fallout handling supports both approaches, configurable per failure | Proposed | real choice — both fallout approaches supported and configurable per failure (DC-03) | Vendor: Loomtech |  |  |  | Solution scope and criteria | Vendor |  | C0297 — Orchestration HLD v1.0.1 - Design Decisions (DC-03) |
| DEC-040 | Unremediable fallout emits a jeopardy event, opens a silent task and waits | Accepted | real choice on fallout that cannot be auto-remediated; jeopardy stays with the Shopfront | marta.quill |  | marta.quill | 2026-07-08 | Solution scope and criteria | Both |  | C0980 — User ruling (marta.quill) 2026-07-08 - resolves open-question C0307; reconciles the MillhouseG4Supply FSD fallout Process Flow (steps 13/21/27) with KDD OSF.5 (C0013) |
| DEC-041 | Loomtech implements on the model-driven framework, not the intent-driven one | Proposed | explicit rejected option — model-driven framework, not intent-driven (DC-04) | Vendor: Loomtech |  |  |  | Solution scope and criteria | Vendor |  | C0290 — Orchestration HLD v1.0.1 - Design Decisions (DC-04) |
| DEC-042 | Only Shopfront/Till-originated modify use cases are Loomtech-supported | Proposed | accepts a boundary — only Shopfront/Till-originated modifies are Loomtech-supported (DR-031) |  |  |  | 2025-10-24 | Solution scope and criteria | Vendor | the non-Till modify gap is a limitation | C0382 — HAB PD-004 Decisions Register DR-031 |
| DEC-043 | Bulk operations are not supported at Basket level and are submitted individually | Proposed | accepts a boundary — no bulk operations at Basket level (DR-032) |  |  |  | 2025-10-14 | Solution scope and criteria | Vendor | the bulk gap is a limitation | C0383 — HAB PD-004 Decisions Register DR-032 |
| DEC-044 | The SubscriberDispatch update invocation mode is Loomtech-internal | Accepted | accepts a vendor constraint — SubscriberDispatch invocation mode is Loomtech-internal; closes OI-046 | marta.quill |  | marta.quill | 2026-08-06 | SubscriberTrimming | Vendor |  | C2203 — Live page edit, HAB PD-004 Phase 1 Design Open Items (3401221361) v4, marta.quill 2026-08-06 - the OI-SI-07 response, reconciled inbound (commit 9ab41c2) |
| DEC-045 | The 1 m/min suspend speed default is accepted and overridable | Accepted | accepts a default (1 m/min suspend speed, overridable) with a pre-production review | marta.quill |  | marta.quill | 2026-08-06 | SubscriberTrimming | Vendor | review tracked as OI-061 | C2205 — Live page edit, HAB PD-004 Phase 1 Design Open Items (3401221361) v4, marta.quill 2026-08-06 - the OI-SI-11 response, reconciled inbound (commit 9ab41c2) |
| DEC-046 | Subscriber Trimming Tallyboard federation transport is Conveyor | Accepted | real choice — Tallyboard federation transport is Conveyor (KDD-CNI.2) | marta.quill |  | marta.quill | 2026-06-11 | SubscriberTrimming | Both |  | C0006 — KDD-CNI.2 - Tallyboard Configuration |
| DEC-047 | TrimAuto LotRegistry is authoritative for Lot management, not Bobbin Number Management | Proposed | explicit rejected option — TrimAuto LotRegistry authoritative over Bobbin Number Management (DC-05) | Vendor: Loomtech |  |  |  | SubscriberTrimming | Both |  | C0325 — Orchestration HLD v1.0.1 - Design Decisions (DC-05) |
| DEC-048 | Lot address management is centralised in TrimAuto LotRegistry | Proposed | principle 'there can be only one' LotRegistry (DR-033), with a stated dependency on Tillbook migrating |  |  |  | 2025-10-27 | SubscriberTrimming | Both | the Tillbook dependency is a risk | C0380 — HAB PD-004 Decisions Register DR-033 |
| DEC-049 | SubscriberTrimming is provisioned dual-lot, with LotB removable and re-addable | Accepted | real choice — dual-lot by default, LotB removable and re-addable | marta.quill |  | marta.quill | 2026-08-07 | SubscriberTrimming | Vendor |  | C2218 — kb-resolve re-visit feed 2026-08-07 (ruling-audit-supersede-2026-08-07), C0379/DR-026 refinement |
| DEC-050 | Feed-config reset is an T&T-authored script, not Warp orchestration | Accepted | real choice with a rejected option — an T&T script/UI rather than Warp orchestration (FRP001) | marta.quill |  | marta.quill | 2026-07-17 | SubscriberTrimming | Internal |  | C1042 — User ruling (marta.quill) 2026-07-17: FRP001 feed-config reset design - resolves the PD-004.6 FRP001 gap (open item OI-SI-01). T&T-built tool, direct (bypasses Warp), force re-push, COA always after Tallyboard |
| DEC-051 | Winder feed management is the WinderFeedManagement atomic RFS | Accepted | real choice — no FeedManagementConfiguration RFS; WinderFeedManagement atomic RFS instead | marta.quill |  | marta.quill | 2026-07-28 | SubscriberTrimming | Vendor |  | C1643 — User ruling (marta.quill) 2026-07-28: sweep pair 6 - the FeedManagementConfiguration RFS is no longer valid. Evidenced by the workflow diagrams in the current SubscriberDispatch FSD, which show a GDA640 PATCH to the Feed Management service handling feed updates and clears on the appropriate Winder. |
| DEC-052 | Phase 1 feed management covers Millhouse-related services only | Accepted | accepts a scope boundary — phase 1 feed management is Millhouse-related services only | marta.quill |  | marta.quill | 2026-08-06 | SubscriberTrimming | Vendor | the non-Millhouse exclusion is a Won't requirement | C2208 — Live page edit, HAB PD-004 Phase 1 Design Open Items (3401221361) v4, marta.quill 2026-08-06 - the OI-SI-21 response, reconciled inbound (commit 9ab41c2) |
| DEC-053 | The absence of a designed in-place IPM migration workflow is knowingly accepted | Accepted | Accepts the risk that in-place service migration onto the Loomtech Backroom has no designed workflow. The interim position is a manual disconnect plus connect, carried as a future change request. Rejected option: design the IPM workflow in phase 1. |  |  |  |  | MillhouseG4Supply | Vendor | accepts the IPM migration risk; the interim disconnect-plus-connect position is recorded on it | previously RAID-017 on the PD-004 RAID register, accepted; C0299, C0305 |
| DEC-054 | Loomtech onboards G4 Cut for retail and for wholesale onto Warp | Accepted | Loomtech will onboard the following services on Warp: G4 Cut for retail, G4 Cut for wholesale. T&T intends to launch G4 Cut capability with select friendly customers. Initial scope was to be refined during pre-engagement. Not Trimming specific. No standard G4 wholesale product currently defined. |  |  | Ruth Calder | 2025-09-15 | Solution scope and criteria | Both |  | PD-004 Scope Register (page 3401221474), previously SR-001 |
| DEC-055 | G4 Cut Retail decided to be Millhouse G4 Trimming | Accepted | Excludes Lot-level WideLot. Excludes Silkline G4. |  |  | Ruth Calder, Marta Quill |  | Solution scope and criteria | Both |  | PD-004 Scope Register (page 3401221474), previously SR-002 |
| DEC-056 | G4 wholesale decided to be modelled on the T&W wholesale product, with Cut handoff via RB tunnel | Accepted | Excludes the dedicated customer Bolt use case. Reel translation required day 1. Requires Reel management decision DR-008. |  |  | Ines Duarte, Cormac Blythe |  | Solution scope and criteria | Both |  | PD-004 Scope Register (page 3401221474), previously SR-003 |
| DEC-057 | G4 Wholesale should include dedicated customer Bolt use cases? | ACCEPTED | Ribbon delivery has two options: pinned Bolt (do nothing), or a ribbon tunnel for the service. |  |  | Ruth Calder, Ines Duarte, Cormac Blythe | December 9, 2025 | Solution scope and criteria | Both |  | PD-004 Scope Register (page 3401221474), previously SR-004 |
| DEC-058 | Any hardware dispatch done by us is out of scope. This includes advanced Finisher replacements, assuming we still do that. | ACCEPTED | Workflows that depend on hardware delivery by us |  |  | Ruth Calder | December 9, 2025 | Solution scope and criteria | Both |  | PD-004 Scope Register (page 3401221474), previously SR-005 |
| DEC-059 | Appointment queries will be supported via GDA646 GET calls into Warp | ACCEPTED | Shopfront needs some way to query available appts without contacting Millhouse directly | Tomas Reed | Peter Sund Marta Quill | Alina Roos |  | Millhouse G4 Supply | Vendor |  |  |

58 items.

## Prior ids

Ids were minted on 2026-09-07 and are never reused. These are the ids these items carried before, which are still quoted elsewhere. Each row also carries its prior id in Source.

| Prior | Now |
|---|---|
| DEC:DEC-p01 | DEC-001 |
| DEC:DEC-p02 | DEC-002 |
| DEC:DEC-p03 | DEC-003 |
| DEC:DEC-p04 | DEC-004 |
| DEC:DEC-p05 | DEC-005 |
| DEC:DEC-p06 | DEC-006 |
| DEC:DEC-p07 | DEC-007 |
| DEC:DEC-p08 | DEC-008 |
| DEC:DEC-p09 | DEC-009 |
| DEC:DEC-p10 | DEC-010 |
| DEC:DEC-p11 | DEC-011 |
| DEC:DEC-p12 | DEC-012 |
| DEC:DEC-p13 | DEC-013 |
| DEC:DEC-p14 | DEC-014 |
| DEC:DEC-p15 | DEC-015 |
| DEC:DEC-p16 | DEC-016 |
| DEC:DEC-p17 | DEC-017 |
| DEC:DEC-p18 | DEC-018 |
| DEC:DEC-p19 | DEC-019 |
| DEC:DEC-p20 | DEC-020 |
| DEC:DEC-p21 | DEC-021 |
| DEC:DEC-p22 | DEC-022 |
| DEC:DEC-p23 | DEC-023 |
| DEC:DEC-p24 | DEC-024 |
| DEC:DEC-p25 | DEC-025 |
| DEC:DEC-p26 | DEC-026 |
| DEC:DEC-p27 | DEC-027 |
| DEC:DEC-p28 | DEC-028 |
| DEC:DEC-p30 | DEC-029 |
| DEC:DEC-p31 | DEC-030 |
| DEC:DEC-p32 | DEC-031 |
| DEC:DEC-p34 | DEC-032 |
| DEC:DEC-p35 | DEC-033 |
| DEC:DEC-p36 | DEC-034 |
| DEC:DEC-p37 | DEC-035 |
| DEC:DEC-p38 | DEC-036 |
| DEC:DEC-p39 | DEC-037 |
| DEC:DEC-p40 | DEC-038 |
| DEC:DEC-p41 | DEC-039 |
| DEC:DEC-p42 | DEC-040 |
| DEC:DEC-p43 | DEC-041 |
| DEC:DEC-p44 | DEC-042 |
| DEC:DEC-p45 | DEC-043 |
| DEC:DEC-p46 | DEC-044 |
| DEC:DEC-p47 | DEC-045 |
| DEC:DEC-p48 | DEC-046 |
| DEC:DEC-p49 | DEC-047 |
| DEC:DEC-p50 | DEC-048 |
| DEC:DEC-p51 | DEC-049 |
| DEC:DEC-p52 | DEC-050 |
| DEC:DEC-p53 | DEC-051 |
| DEC:DEC-p54 | DEC-052 |
| RAID-017 | DEC-053 |
| SR-001 | DEC-054 |
| SR-002 | DEC-055 |
| SR-003 | DEC-056 |
| SR-004 | DEC-057 |
| SR-005 | DEC-058 |
