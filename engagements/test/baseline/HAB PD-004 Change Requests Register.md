---
page-id: 3401221022
page-title: HAB PD-004 Change Requests Register
page-version: 
page-url: https://example.atlassian.net/wiki/spaces/Restitch/pages/3401221022/HAB+PD-004+Change+Requests+Register
parent-page-id: 3401220005
pulled-on: 12 September 2026
---

# HAB PD-004 Change Requests Register

## Register: Change requests

Holds changes to agreed scope or design that cost time, money or effort.

One row per item. The conventions for adding or moving one by hand are in Register: Conventions.

## Legend

### Status

| Value | What it means |
|---|---|
| Proposed | Ours, and being reasoned. |
| Submitted | Handed to whoever will implement it. |
| Impact assessment | The estimate is back and we are deciding. |
| Approved | Agreed to go ahead. |
| Rejected | Considered and not taken. |
| Delivered | Built. |

### Phase

| Value | What it means |
|---|---|
| this phase | In scope for the current delivery. |
| next phase | Deliberately carried forward. |

## Change requests

| ID | Title | Status | Phase | Raised on | Raised by | Reason | Implemented by | Impact | Approved by | Approved on | Scope | Vendor ref | Links | Source |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| CR-001 | CR1 'Solution changes introduced during the HLD' — the approved change record updating the RDD v0.4 to v1.2 | Approved | this phase | 2026-05 |  | Baseline the solution changes agreed during the HLD | Vendor | Approved change record; the changes it introduced are still being built, so not Delivered |  |  | Solution scope and criteria | CR1 v1.2 |  | C0265 — CR1 v1.2 (Warp Bobbin HLD changes) - Change Description Table 3 |
| CR-002 | Users should get changes to their service configuration immediately | Approved | this phase | 2026-06 |  | Service changes take effect only after reconnecting; end-user quality impact from out-of-sync configuration (Lot/Till/Speed/ruleset) | Vendor | include (Option 1) |  |  | SubscriberTrimming | PL-02 | delivers REQ-030 | PD-004 Scope Register (page 3401221474) Loomtech Build CR Baseline 1, previously FG001; C0274 — CR1 v1.2 - Table 4 Item NFR:STR_06/FR:G4TR_MOD08 / PL-02 |
| CR-003 | Bay selection support for Customer Counter fulfilment | Approved | this phase | 2026-06 |  | Customer Counter fulfilment will not be able to assign a bay | Vendor | include (Option 3) |  |  | CustomerCounter | PL-01 | delivers REQ-031 | PD-004 Scope Register (page 3401221474) Loomtech Build CR Baseline 1, previously FG002; C0271 — CR1 v1.2 - Table 4 Item FR:CNTR_CON04 / PL-01 |
| CR-004 | Support for TOT process to onboard new wholesale clients from another Reseller | Rejected | this phase | 2026-06 |  | manual onboarding | Vendor | exclude (Option 2) |  |  | CarrierRibbon |  | delivers REQ-032 | PD-004 Scope Register (page 3401221474) Loomtech Build CR Baseline 1, previously FG003 |
| CR-005 | Support for service migrations to new Bolts | Proposed | this phase | 2026-06 |  | manual service migrations between Bolts |  | exclude (Option 2) |  |  | MillhouseG4Supply |  | delivers REQ-033 | PD-004 Scope Register (page 3401221474) Loomtech Build CR Baseline 1, previously FG004 |
| CR-006 | Support transfer reversal for services incorrectly switched away | Proposed | this phase | 2026-06 |  | End user has no way of returning to T&T; loss of customer and bad customer experience | Vendor | Recommendation was "exclude Option 2, Day 2 requirement". REVERSED by the 2026-09-07 ruling that transfer reversal should be required for day 1; cost and time not yet re-estimated. |  |  | MillhouseG4Supply |  | delivers REQ-034 | PD-004 Scope Register (page 3401221474) Loomtech Build CR Baseline 1, previously FG005 |
| CR-007 | Support Finisher upgrades for multi-head and multi-bay use cases | Approved | this phase | 2026-06 |  | No support for Finisher upgrades | Vendor | include (Option 1) |  |  | MillhouseG4Supply | PL-07 | delivers REQ-035 | PD-004 Scope Register (page 3401221474) Loomtech Build CR Baseline 1, previously FG006; C0277 — CR1 v1.2 - Table 4 Item PL-07 |
| CR-008 | Support service disconnect due to switching away | Approved | this phase | 2026-06 |  | Services remain active when a customer switches away | Vendor | include (Option 2) |  |  | MillhouseG4Supply | PL-03 | delivers REQ-036 | PD-004 Scope Register (page 3401221474) Loomtech Build CR Baseline 1, previously FG007; C0273 — CR1 v1.2 - Table 4 Item SR_WARP_02 |
| CR-009 | Dynamically calculate Winder returnline fitting | Approved | this phase | 2026-06 |  | Cannot calculate the returnline fitting for Tallyboard config | Vendor | include (Option 1) |  |  | SubscriberTrimming | PL-08 | delivers REQ-037 | PD-004 Scope Register (page 3401221474) Loomtech Build CR Baseline 1, previously FG008; C0275 — CR1 v1.2 - Table 4 Item PL-08 |
| CR-010 | Support multiple Shared Tills per Winder | Approved | this phase | 2026-06 |  | Cannot select the Shared Lot pool correctly | Vendor | include (Option 1) |  |  | SubscriberTrimming | PL-09 | delivers REQ-038 | PD-004 Scope Register (page 3401221474) Loomtech Build CR Baseline 1, previously FG009; C0276 — CR1 v1.2 - Table 4 Item PL-09 |
| CR-011 | Support for customer Counter suspend and resume via bay admin shutdown | Approved | this phase | 2026-06 |  | Manual process and Bobbin updates required | Vendor | include (Option 1) |  |  | CustomerCounter | PL-04 | delivers REQ-039 | PD-004 Scope Register (page 3401221474) Loomtech Build CR Baseline 1, previously FG010; C0269 — CR1 v1.2 - Table 4 Item SR_WARP_02 / PL-04 |
| CR-012 | Consume service sync status from Loom and use it for display and notifications in the Backroom | Approved | this phase | 2026-06 |  | No service workshop sync view or out-of-sync alerts in the Backroom | Vendor | include (depends on complexity) |  |  | CarrierRibbon |  | delivers REQ-040 | PD-004 Scope Register (page 3401221474) Loomtech Build CR Baseline 1, previously FG011 |
| CR-013 | GDA640 SubscriberDispatch support for workshop ops to make configuration changes to services | Rejected | this phase | 2026-06 |  |  |  |  |  |  | SubscriberTrimming | PL-05 | delivers REQ-041 | PD-004 Scope Register (page 3401221474) Loomtech Build CR Baseline 1, previously FG012 |
| CR-014 | GDA640 Ribbon support for workshop ops to make configuration changes to services | Rejected | this phase | 2026-06 |  |  |  |  |  |  | CarrierRibbon | PL-06 | delivers REQ-042 | PD-004 Scope Register (page 3401221474) Loomtech Build CR Baseline 1, previously FG013 |
| CR-015 | GDA640 Customer Counter support for workshop ops to make configuration changes to services | Rejected | this phase | 2026-06 |  |  |  |  |  |  | CustomerCounter | PL-06 | delivers REQ-043 | PD-004 Scope Register (page 3401221474) Loomtech Build CR Baseline 1, previously FG014 |
| CR-016 | Service migrations to new machines / Counters | Approved | this phase | 2026-06 |  | Unable to upgrade machines or move customer Counters (workshop augmentation use cases) | Vendor | Recommendation was "exclude Option 3". Ruled include 2026-09-07. Approved but NOT delivered: the Counter machine-migration open item records no designed workflow, and the CR-14 bulk-migration exclusion still stands. |  |  | G4 CarrierRibbon Handoff |  | delivers REQ-044 | PD-004 Scope Register (page 3401221474) Loomtech Build CR Baseline 1, previously FG015 |
| CR-017 | GDA641 supports a separate relatedParty channel for operations-initiated orders | Approved | this phase | 2026-06 |  | Needed to allow workshop engineering changes without Shopfront involvement | Vendor | include |  |  | Order handling | PL-11 | delivers REQ-041, REQ-042, REQ-043 | PD-004 Scope Register (page 3401221474) Loomtech Build CR Baseline 1, previously FG016; C0280 — CR1 v1.2 - Table 4 Item PL-11 |
| CR-018 | Support for portability of Lot lots | Approved | this phase | 2026-06 | Ines Duarte |  | Vendor | include |  |  | SubscriberTrimming |  | delivers REQ-046 | PD-004 Scope Register (page 3401221474) Loomtech Build CR Baseline 1, previously FG018 |
| CR-019 | Support for multiple feeder routes (lots) per service - one fitting (Wide) Lot, static IPs only | Approved | this phase | 2026-06 | Tomas Reed |  | Vendor | include |  |  | SubscriberTrimming |  | delivers REQ-047 | PD-004 Scope Register (page 3401221474) Loomtech Build CR Baseline 1, previously FG019 |
| CR-020 | Support for correlation ID and Order ID in header for tracing and wholesale | Approved | this phase | 2026-06 |  |  | Vendor | include |  |  | Upstream Shopfront integration |  | delivers REQ-048 | PD-004 Scope Register (page 3401221474) Loomtech Build CR Baseline 1, previously FG020 |
| CR-021 | Millhouse Appointment re-scheduling during Order to Activate | Approved | this phase | 2026-06 |  |  | Vendor | include (Option 2) |  |  | MillhouseG4Supply |  | delivers REQ-049 | PD-004 Scope Register (page 3401221474) Loomtech Build CR Baseline 1, previously FG021 |
| CR-022 | Support for disabling a service as a privileged order with permission control | Proposed | this phase |  |  | Without this cannot execute police requests during police operations to shut down service. Agency requests that need to look like a standard fault … | Vendor | include |  |  | SubscriberTrimming |  | delivers REQ-050 | PD-004 Scope Register (page 3401221474) New Requirements, previously FG017; C0364 — HAB PD-004 Scope Register - New Requirements FG017 |
| CR-023 | Must have a way of completing orders that lack automation rules and drop to fallout (e.g. Finisher capacity exceeded) | Proposed | this phase |  |  | Modify and connect scenarios we do not automate fall out to MendingBench; without a way to complete them the order is stuck |  | include |  |  | Fallout and intervention |  | delivers REQ-051 | PD-004 Scope Register (page 3401221474) New Requirements, previously FG022 |
| CR-024 | Manually change a service configuration and re-sync | Proposed | this phase |  |  | Needed for ops team to troubleshoot services |  | include |  |  | Fallout and intervention |  | delivers REQ-052 | PD-004 Scope Register (page 3401221474) New Requirements, previously FG023 |
| CR-025 | Support for GDA674 GeographicSite for Shopfront calls to read site information | Proposed | this phase |  |  | GDA641 requires the supplier address to be a reference; we need an API to create the address in the Backroom before submitting the order | Both | include (Option 1 - extending GDA641 creates upstream Shopfront dependencies) |  |  | Order handling |  | delivers REQ-053 | PD-004 Scope Register (page 3401221474) New Requirements, previously FG024 |
| CR-026 | Reel Reservation | Rejected | this phase |  |  | Manually allocated Reels may get rejected when a Carrier Ribbon order is placed |  | exclude (Option 1) |  |  | CustomerCounter |  | delivers REQ-054 | PD-004 Scope Register (page 3401221474) New Requirements, previously FG025 |
| CR-027 | Support for Dedicated Bolts | Proposed | next phase |  |  | Clients with a dedicated Bolt would not be supported | Vendor |  |  |  | MillhouseG4Supply | CR-01 | delivers REQ-055 | PD-004 Scope Register (page 3401221474) Customer Segment Changes, previously FC001 |
| CR-028 | Service Migration to Bobbin and Inflight Order Migration to Warp | Proposed | next phase |  |  | Required for bringing on board existing customers | Both |  |  |  | Bobbin service and resource model | CR-02 | delivers REQ-056 | PD-004 Scope Register (page 3401221474) Customer Segment Changes, previously FC002 |
| CR-029 | Wide Lot design | Proposed | next phase |  |  | Required to support customers in certain segments/domains | Vendor |  |  |  | Solution scope and criteria | CR-03 | delivers REQ-057 | PD-004 Scope Register (page 3401221474) Customer Segment Changes, previously FC003 |
| CR-030 | Chart automation and support | Proposed | next phase |  |  | Required to support customers in certain segments/domains | Vendor |  |  |  | SubscriberTrimming | CR-04 | delivers REQ-058 | PD-004 Scope Register (page 3401221474) Customer Segment Changes, previously FC004 |
| CR-031 | NamedAuth manual auth | Proposed | next phase |  |  | Required to support Source BT&W customers | Vendor |  |  |  | SubscriberTrimming | CR-05 | delivers REQ-059 | PD-004 Scope Register (page 3401221474) Customer Segment Changes, previously FC005 |
| CR-032 | RepairsDesk AssetLedger Integration | Proposed | next phase |  |  | Required to support BT&W customers | Vendor |  |  |  | Solution scope and criteria |  | delivers REQ-060 | PD-004 Scope Register (page 3401221474) Customer Segment Changes, previously FC006 |
| CR-033 | Support for business connect with Millhouse Account Management | Proposed | next phase |  |  | Required to support business customers in Tillbook | Vendor |  |  |  | MillhouseG4Supply |  | delivers REQ-061 | PD-004 Scope Register (page 3401221474) Customer Segment Changes, previously FC007 |
| CR-034 | Explicit feed management on delete | Submitted | this phase | 2026-08-06 | Marta Quill | Explicit feed management on delete is promoted to a phase 1 requirement: Loomtech will add it to phase 1. | Vendor |  |  |  | SubscriberTrimming |  |  | C2204 — Live page edit, HAB PD-004 Phase 1 Design Open Items (3401221361) v4, marta.quill 2026-08-06 - the OI-SI-09 response, reconciled inbound (commit 9ab41c2) |
| CR-035 | subscriberProtocol modify path | Submitted | this phase | 2026-08-06 | Marta Quill | A subscriberProtocol modify path is now a requirement: Loomtech has taken it as new work and will raise a phase 1 CR to implement it. | Vendor |  |  |  | SubscriberTrimming |  |  | C2206 — Live page edit, HAB PD-004 Phase 1 Design Open Items (3401221361) v4, marta.quill 2026-08-06 - the OI-SI-12 response, reconciled inbound (commit 9ab41c2) |
| CR-036 | WRG-aware Winder feed management, legacy and WRG-member Winders | Submitted | this phase | 2026-08-06 | Marta Quill | WRG-aware Winder feed management is now a requirement: Loomtech will deliver it in phase 1 via a CR supporting both legacy Winders (no WRG) and handling … | Vendor |  |  |  | SubscriberTrimming |  |  | C2207 — Live page edit, HAB PD-004 Phase 1 Design Open Items (3401221361) v4, marta.quill 2026-08-06 - the OI-SI-20 response, reconciled inbound (commit 9ab41c2) |
| CR-037 | Service Transfer: supply the SITEids and the CutId on a transfer-in connect | Proposed | this phase | 2026-09-07 | Marta Quill | A transfer-in connect has no designed path today | Vendor |  |  |  | MillhouseG4Supply |  | delivers REQ-089; triggered by OI-068 | Marta Quill, solution architect, 2026-09-07; previously SUP-CR-01 |
| CR-038 | Connect Outstanding: connect a service where the customer does not know the CutId | Proposed | this phase | 2026-09-07 | Marta Quill | Customers frequently do not hold their CutId, so a connect keyed on it cannot proceed | Vendor |  |  |  | MillhouseG4Supply |  | delivers REQ-090; triggered by OI-068 | Marta Quill, solution architect, 2026-09-07; previously SUP-CR-02 |

38 items.

## Prior ids

Ids were minted on 2026-09-07 and are never reused. These are the ids these items carried before, which are still quoted elsewhere. Each row also carries its prior id in Source.

| Prior | Now |
|---|---|
| CR:CR1 | CR-001 |
| FG001 | CR-002 |
| FG002 | CR-003 |
| FG003 | CR-004 |
| FG004 | CR-005 |
| FG005 | CR-006 |
| FG006 | CR-007 |
| FG007 | CR-008 |
| FG008 | CR-009 |
| FG009 | CR-010 |
| FG010 | CR-011 |
| FG011 | CR-012 |
| FG012 | CR-013 |
| FG013 | CR-014 |
| FG014 | CR-015 |
| FG015 | CR-016 |
| FG016 | CR-017 |
| FG018 | CR-018 |
| FG019 | CR-019 |
| FG020 | CR-020 |
| FG021 | CR-021 |
| FG017 | CR-022 |
| FG022 | CR-023 |
| FG023 | CR-024 |
| FG024 | CR-025 |
| FG025 | CR-026 |
| FC001 | CR-027 |
| FC002 | CR-028 |
| FC003 | CR-029 |
| FC004 | CR-030 |
| FC005 | CR-031 |
| FC006 | CR-032 |
| FC007 | CR-033 |
| CR:C2204 | CR-034 |
| CR:C2206 | CR-035 |
| CR:C2207 | CR-036 |
| SUP-CR-01 | CR-037 |
| SUP-CR-02 | CR-038 |
