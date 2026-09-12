---
page-id: 3401220909
page-title: HAB PD-004 Requirements Register
page-version: 
page-url: https://example.atlassian.net/wiki/spaces/Restitch/pages/3401220909/HAB+PD-004+Requirements+Register
parent-page-id: 3401220005
pulled-on: 12 September 2026
---

# HAB PD-004 Requirements Register

## Register: Requirements

Holds what we need the solution to do, and whether each need is agreed, designed or met.

One row per item. The conventions for adding or moving one by hand are in Register: Conventions.

## Legend

### Status

| Value | What it means |
|---|---|
| Draft | Stated, not yet agreed. |
| Agreed | Agreed as a need. Not yet designed. |
| Designed | A design document covers it. |
| Delivered | Built, not yet verified. |
| Verified | Confirmed met. |
| Deferred | Carried to a later phase. |
| Withdrawn | Agreed as out of this project. Recorded, not deleted. |

### MoSCoW

| Value | What it means |
|---|---|
| Must | Required for this phase. |
| Should | Wanted, and not required. |
| Could | Taken if it is cheap. |
| Won't | Agreed as out of scope. Recorded, not deleted. |

### Phase

| Value | What it means |
|---|---|
| this phase | In scope for the current delivery. |
| next phase | Deliberately carried forward. |

## Requirements

| ID | Title | Status | MoSCoW | Phase | Raised on | Owner | Scope | Implemented by | Vendor ref | Links | Source |
|---|---|---|---|---|---|---|---|---|---|---|---|
| REQ-001 | The Loom service pattern model is authoritative for the Ribbon service data model | Draft |  | this phase | 2026-07-16 |  | CarrierRibbon | Vendor | RQ014, RQ015 |  | C0999 — HAB PD-004.7 - Carrier Ribbon |
| REQ-002 | ZoneType is provided on the Ribbon order by the Shopfront | Draft |  | this phase | 2026-07-16 |  | CarrierRibbon | Both | RQ023 |  | C1000 — HAB PD-004.7 - Carrier Ribbon |
| REQ-003 | Ribbon connect provisioning waits for the clabel from supply design | Draft |  | this phase | 2026-07-16 |  | CarrierRibbon | Vendor | RQ026 |  | C1001 — HAB PD-004.7 - Carrier Ribbon |
| REQ-004 | The Shopfront prevents orphaned supply services after a Ribbon cancellation | Draft |  | this phase | 2026-07-16 |  | CarrierRibbon | Both | RQ027 |  | C1002 — HAB PD-004.7 - Carrier Ribbon |
| REQ-005 | Gauging rates are validated against physical fitting capacity | Draft |  | this phase | 2026-07-16 |  | CarrierRibbon | Vendor | RQ022 |  | C0995 — HAB PD-004.7 - Carrier Ribbon |
| REQ-006 | Per-endpoint Reel translation with push, pop and swap for fold-in-fold | Draft |  | this phase | 2026-07-16 |  | CarrierRibbon | Vendor | RQ007, RQ008 |  | C0987 — HAB PD-004.7 - Carrier Ribbon |
| REQ-007 | The next available Counter Reel is selected when the order supplies none | Draft |  | this phase | 2026-07-16 |  | CarrierRibbon | Vendor | RQ009 |  | C0988 — HAB PD-004.7 - Carrier Ribbon |
| REQ-008 | Ribbon Reel ids are range-checked and rejected if already allocated on the Counter | Draft |  | this phase | 2026-07-16 |  | CarrierRibbon | Vendor | RQ020, RQ021 |  | C0989 — HAB PD-004.7 - Carrier Ribbon |
| REQ-009 | A manual connect step holds machine configuration until threading is confirmed | Draft |  | this phase | 2026-07-16 |  | CustomerCounter | Vendor | RQ016, RQ017 |  | C1027 — HAB PD-004.8 - Customer Counter Supply |
| REQ-010 | A redundant CustomerCounter may name the same Depot in both place entries | Agreed |  | this phase | 2026-08-19 | Vendor: Nadia Frost | CustomerCounter | Vendor |  |  | C2351 — MS Teams message, Nadia Frost, 2026-08-19 09:44 |
| REQ-011 | Customer Counters bulk-import from legacy via a versioned CSV with per-row validation | Draft |  | this phase | 2026-07-16 |  | CustomerCounter | Vendor | RQ030, RQ031 |  | C1039 — HAB PD-004.8 - Customer Counter Supply |
| REQ-012 | A facility to perform service migrations through Loomtech | Agreed |  | this phase | 2026-08-07 | Cormac Blythe | CustomerCounter | Vendor |  |  | C2264 — sources/backroom/TT-Loomtech-Technical-Sync-Up-20260805.vtt @ 00:54:39 |
| REQ-013 | Bay to machine to DEPOT hierarchy is enforced and validated at provisioning | Draft |  | this phase | 2026-07-16 |  | CustomerCounter | Vendor | RQ002 |  | C1004 — HAB PD-004.8 - Customer Counter Supply |
| REQ-014 | All Bundle member bays run at the same speed for symmetric failover | Draft |  | this phase | 2026-07-16 |  | CustomerCounter | Vendor | RQ009 |  | C1008 — HAB PD-004.8 - Customer Counter Supply |
| REQ-015 | The Counter is a GDA638 service with a GDA633 specification, ordered via GDA641 | Draft |  | this phase | 2026-07-16 |  | CustomerCounter | Vendor | RQ026, RQ027 |  | C1013 — HAB PD-004.8 - Customer Counter Supply |
| REQ-016 | The Counter is a Spindle Loom service package rendering bay, Bundle and subfitting config | Draft |  | this phase | 2026-07-16 |  | CustomerCounter | Vendor | RQ028, RQ029 |  | C1014 — HAB PD-004.8 - Customer Counter Supply |
| REQ-017 | A queryable bay allocation audit log, reachable without external log aggregation | Draft |  | this phase | 2026-07-16 |  | CustomerCounter | Vendor | RQ024, RQ025 |  | C1015 — HAB PD-004.8 - Customer Counter Supply |
| REQ-018 | Redundancy type changes between active-active and active-passive without termination | Draft |  | this phase | 2026-07-16 |  | CustomerCounter | Vendor | RQ018, DE002 |  | C1016 — HAB PD-004.8 - Customer Counter Supply |
| REQ-019 | Bays are added and removed subject to speed symmetry and diversity validity | Draft |  | this phase | 2026-07-16 |  | CustomerCounter | Vendor | RQ020, RQ021, RQ034 |  | C1018 — HAB PD-004.8 - Customer Counter Supply |
| REQ-020 | Automatic best-fit Counter bay selection against diversity, DEPOT and speed | Draft |  | this phase | 2026-07-16 |  | CustomerCounter | Vendor | RQ013, RQ014 |  | C1021 — HAB PD-004.8 - Customer Counter Supply |
| REQ-021 | A manual bay selection workflow constrained to validated capability and diversity | Draft |  | this phase | 2026-07-16 |  | CustomerCounter | Vendor | RQ015 |  | C1026 — HAB PD-004.8 - Customer Counter Supply |
| REQ-022 | Legacy Reel operations divert to Bobbin per-Counter without a bulk cutover | Draft |  | this phase | 2026-07-16 |  | CustomerCounter | Both | RQ012, RQ032 |  | C1029 — HAB PD-004.8 - Customer Counter Supply |
| REQ-023 | Number allocation rejects a Reel that conflicts on that Counter | Draft |  | this phase | 2026-07-16 |  | CustomerCounter | Vendor | RQ037 |  | C1030 — HAB PD-004.8 - Customer Counter Supply |
| REQ-024 | The Reel-mode model must extend beyond default-mapped and capture the actual label | Agreed |  | this phase | 2026-08-07 | Marta Quill | MillhouseG4Supply | Vendor |  |  | C2251 — sources/backroom/TT-Loomtech-Technical-Sync-Up-20260805.vtt @ 00:43:27 |
| REQ-025 | Counter bay selection is based on Depot, speed, diversity and bay count | Draft |  | this phase | 2026-06-11 |  | Bay allocation | Vendor |  |  | C0198 — Bobbin HLD v1.0.1 2.8 Customer Counter Bay Allocation |
| REQ-026 | External Reel identifiers record both System Name and Service Id | Draft |  | this phase | 2026-06-11 |  | Identifier and Reel management | Vendor |  |  | C0188 — Bobbin HLD v1.0.1 2.7.2 Reel Management |
| REQ-027 | Explicit feed management on delete | Agreed |  | this phase | 2026-08-06 | Marta Quill | SubscriberTrimming | Vendor |  |  | C2204 — Live page edit, HAB PD-004 Phase 1 Design Open Items (3401221361) v4, marta.quill 2026-08-06 - the OI-SI-09 response, reconciled inbound (commit 9ab41c2) |
| REQ-028 | A subscriberProtocol modify path | Agreed |  | this phase | 2026-08-06 | Marta Quill | SubscriberTrimming | Vendor |  |  | C2206 — Live page edit, HAB PD-004 Phase 1 Design Open Items (3401221361) v4, marta.quill 2026-08-06 - the OI-SI-12 response, reconciled inbound (commit 9ab41c2) |
| REQ-029 | WRG-aware Winder feed management across legacy and WRG-member Winders | Agreed |  | this phase | 2026-08-06 | Marta Quill | SubscriberTrimming | Vendor |  |  | C2207 — Live page edit, HAB PD-004 Phase 1 Design Open Items (3401221361) v4, marta.quill 2026-08-06 - the OI-SI-20 response, reconciled inbound (commit 9ab41c2) |
| REQ-030 | Users should get changes to their service configuration immediately | Agreed | Must | this phase |  |  | SubscriberTrimming | Vendor | PL-02 |  | PD-004 Scope Register (page 3401221474), previously FG001 |
| REQ-031 | Bay selection support for Customer Counter fulfilment | Agreed | Must | this phase |  |  | CustomerCounter | Vendor | PL-01 |  | PD-004 Scope Register (page 3401221474), previously FG002 |
| REQ-032 | Support for TOT process to onboard new wholesale clients from another Reseller | Withdrawn | Could | this phase |  |  | CarrierRibbon | Vendor |  |  | PD-004 Scope Register (page 3401221474), previously FG003 |
| REQ-033 | Support for service migrations to new Bolts | Draft | Could | this phase |  |  | MillhouseG4Supply |  |  |  | PD-004 Scope Register (page 3401221474), previously FG004 |
| REQ-034 | Support transfer reversal for services incorrectly switched away | Draft | Must | this phase |  |  | MillhouseG4Supply | Vendor |  | contradicted by the EX-16 exclusion requirement REQ-087 (EX-16, out of scope); OI-033 (post-phase-1); REQ-067; Loomtech CR-06 | PD-004 Scope Register (page 3401221474), previously FG005; ruled by Marta Quill, solution architect, 2026-09-07 |
| REQ-035 | Support Finisher upgrades for multi-head and multi-bay use cases | Agreed | Must | this phase |  |  | MillhouseG4Supply | Vendor | PL-07 |  | PD-004 Scope Register (page 3401221474), previously FG006 |
| REQ-036 | Support service disconnect due to switching away | Agreed | Must | this phase |  |  | MillhouseG4Supply | Vendor | PL-03 |  | PD-004 Scope Register (page 3401221474), previously FG007 |
| REQ-037 | Dynamically calculate Winder returnline fitting | Agreed | Must | this phase |  |  | SubscriberTrimming | Vendor | PL-08 |  | PD-004 Scope Register (page 3401221474), previously FG008 |
| REQ-038 | Support multiple Shared Tills per Winder | Agreed | Must | this phase |  |  | SubscriberTrimming | Vendor | PL-09 |  | PD-004 Scope Register (page 3401221474), previously FG009 |
| REQ-039 | Support for customer Counter suspend and resume via bay admin shutdown | Agreed | Must | this phase |  |  | CustomerCounter | Vendor | PL-04 |  | PD-004 Scope Register (page 3401221474), previously FG010 |
| REQ-040 | Consume service sync status from Loom and use it for display and notifications in the Backroom | Agreed | Could | this phase |  |  | CarrierRibbon | Vendor |  |  | PD-004 Scope Register (page 3401221474), previously FG011 |
| REQ-041 | GDA640 SubscriberDispatch support for workshop ops to make configuration changes to services | Draft | Should | this phase |  |  | SubscriberTrimming |  | PL-05 |  | PD-004 Scope Register (page 3401221474), previously FG012 |
| REQ-042 | GDA640 Ribbon support for workshop ops to make configuration changes to services | Draft | Should | this phase |  |  | CarrierRibbon |  | PL-06 |  | PD-004 Scope Register (page 3401221474), previously FG013 |
| REQ-043 | GDA640 Customer Counter support for workshop ops to make configuration changes to services | Draft | Should | this phase |  |  | CustomerCounter |  | PL-06 |  | PD-004 Scope Register (page 3401221474), previously FG014 |
| REQ-044 | Service migrations to new machines / Counters | Agreed | Must | this phase |  |  | G4 CarrierRibbon Handoff | Vendor |  | contradicted by the CR-14 exclusion requirement REQ-088 (CR-14 bulk Counter migration excluded); OI-012; OI-013; REQ-071; REQ from C2264 | PD-004 Scope Register (page 3401221474), previously FG015; ruled 2026-09-07 (include) |
| REQ-045 | GDA641 support for a different relatedParty channel for workshop/systems operations-initiated orders. Shopfront- and operations-initiated orders can have different notification destinations, configured in the Warp notification service. | Agreed | Must | this phase |  |  | Order handling | Vendor | PL-11 |  | PD-004 Scope Register (page 3401221474), previously FG016 |
| REQ-046 | Support for portability of Lot lots | Agreed |  | this phase |  | Ines Duarte | SubscriberTrimming | Vendor |  |  | PD-004 Scope Register (page 3401221474), previously FG018 |
| REQ-047 | Support for multiple feeder routes (lots) per service - one fitting (Wide) Lot, static IPs only | Agreed |  | this phase |  | Tomas Reed | SubscriberTrimming | Vendor |  |  | PD-004 Scope Register (page 3401221474), previously FG019 |
| REQ-048 | Support for correlation ID and Order ID in header for tracing and wholesale | Agreed |  | this phase |  |  | Upstream Shopfront integration | Vendor |  |  | PD-004 Scope Register (page 3401221474), previously FG020 |
| REQ-049 | Millhouse Appointment re-scheduling during Order to Activate | Agreed |  | this phase |  |  | MillhouseG4Supply | Vendor |  |  | PD-004 Scope Register (page 3401221474), previously FG021 |
| REQ-050 | Support for disabling a service as a privileged order with permission control | Draft |  | this phase |  |  | SubscriberTrimming | Vendor |  |  | PD-004 Scope Register (page 3401221474), previously FG017 |
| REQ-051 | Must have a way of completing orders that lack automation rules and drop to fallout (e.g. Finisher capacity exceeded) | Draft |  | this phase |  |  | Fallout and intervention |  |  |  | PD-004 Scope Register (page 3401221474), previously FG022 |
| REQ-052 | Manually change a service configuration and re-sync | Draft |  | this phase |  |  | Fallout and intervention |  |  |  | PD-004 Scope Register (page 3401221474), previously FG023 |
| REQ-053 | Support for GDA674 GeographicSite for Shopfront calls to read site information | Draft |  | this phase |  |  | Order handling | Both |  |  | PD-004 Scope Register (page 3401221474), previously FG024 |
| REQ-054 | Reel Reservation | Withdrawn |  | this phase |  |  | CustomerCounter |  |  |  | PD-004 Scope Register (page 3401221474), previously FG025 |
| REQ-055 | Support for Dedicated Bolts | Draft |  | next phase |  |  | MillhouseG4Supply | Vendor | CR-01 |  | PD-004 Scope Register (page 3401221474), previously FC001 |
| REQ-056 | Service Migration to Bobbin and Inflight Order Migration to Warp | Draft |  | next phase |  |  | Bobbin service and resource model | Both | CR-02 |  | PD-004 Scope Register (page 3401221474), previously FC002 |
| REQ-057 | Wide Lot design | Draft |  | next phase |  |  | Solution scope and criteria | Vendor | CR-03 |  | PD-004 Scope Register (page 3401221474), previously FC003 |
| REQ-058 | Chart automation and support | Draft |  | next phase |  |  | SubscriberTrimming | Vendor | CR-04 |  | PD-004 Scope Register (page 3401221474), previously FC004 |
| REQ-059 | NamedAuth manual auth | Draft |  | next phase |  |  | SubscriberTrimming | Vendor | CR-05 |  | PD-004 Scope Register (page 3401221474), previously FC005 |
| REQ-060 | RepairsDesk AssetLedger Integration | Draft |  | next phase |  |  | Solution scope and criteria | Vendor |  |  | PD-004 Scope Register (page 3401221474), previously FC006 |
| REQ-061 | Support for business connect with Millhouse Account Management | Draft |  | next phase |  |  | MillhouseG4Supply | Vendor |  |  | PD-004 Scope Register (page 3401221474), previously FC007 |
| REQ-062 | Role based TradeCounters | Draft |  | next phase |  |  | CustomerCounter |  |  |  | PD-004 Scope Register (page 3401221474), previously FC008 |
| REQ-063 | Future WRG redundancy | Draft | Could | next phase |  |  | SubscriberTrimming |  |  |  | PD-004 Scope Register (page 3401221474), previously FC009 |
| REQ-064 | Order fallout management | Draft |  | next phase |  |  | Fallout and intervention |  |  |  | PD-004 Scope Register (page 3401221474), previously FC010 |
| REQ-065 | Support for TOT process to onboard new wholesale clients from another Reseller | Draft |  | next phase |  |  | CarrierRibbon |  |  |  | PD-004 Scope Register (page 3401221474), previously FC011 |
| REQ-066 | Support for service migrations to new Bolts | Draft |  | next phase |  |  | MillhouseG4Supply |  |  |  | PD-004 Scope Register (page 3401221474), previously FC012 |
| REQ-067 | Support transfer reversal for services incorrectly switched away | Draft |  | next phase |  |  | MillhouseG4Supply |  |  |  | PD-004 Scope Register (page 3401221474), previously FC013 |
| REQ-068 | Support full Finisher / multi-head upgrade workflows as per Pinwheel / Tillbook | Draft |  | next phase |  |  | MillhouseG4Supply |  |  |  | PD-004 Scope Register (page 3401221474), previously FC014 |
| REQ-069 | Full Loom service discovery for service config health visibility | Draft |  | next phase |  |  | Bobbin service and resource model |  |  |  | PD-004 Scope Register (page 3401221474), previously FC015 |
| REQ-070 | Alerting / ticketing for service health discrepancies | Draft |  | next phase |  |  | Bobbin service and resource model |  |  |  | PD-004 Scope Register (page 3401221474), previously FC016 |
| REQ-071 | Customer Counter migration support for machine / redundancy changes | Draft |  | next phase |  |  | CustomerCounter |  |  |  | PD-004 Scope Register (page 3401221474), previously FC017 |
| REQ-072 | GDA640 Millhouse G4 support for workshop ops to make configuration changes to the Millhouse Cut (e.g. change Bolt) | Draft |  | next phase |  |  | MillhouseG4Supply |  |  |  | PD-004 Scope Register (page 3401221474), previously FC018 |
| REQ-073 | Generate LOA document for customer Counter provisioning | Draft |  | next phase |  |  | CustomerCounter |  |  |  | PD-004 Scope Register (page 3401221474), previously FC019 |
| REQ-074 | RepairsDesk Integration | Withdrawn | Won't | this phase |  |  | Solution scope and criteria |  | RDD v0.4 - NFR:REPD_01 |  | PD-004 Scope Register (page 3401221474), previously DR001 |
| REQ-075 | Bobbin Discovery | Draft | Won't | this phase |  |  | Bobbin service and resource model |  | SOW - Table 2 (High level scope) - p12 |  | PD-004 Scope Register (page 3401221474), previously DR002 |
| REQ-076 | Connect: Transfer Service from other Supplier (Defection) | Draft | Won't | this phase |  |  | MillhouseG4Supply |  | RDD v0.4 - SR_WARP_02 |  | PD-004 Scope Register (page 3401221474), previously DR003 |
| REQ-077 | Connect: Internal Defection (IPM) Service Import | Withdrawn | Won't | this phase |  |  | MillhouseG4Supply |  | RDD v0.4 - SR_WARP_02 |  | PD-004 Scope Register (page 3401221474), previously DR004 |
| REQ-078 | Modify: Change Technology | Withdrawn | Won't | this phase |  |  | MillhouseG4Supply |  | RDD v0.4 - SR_WARP_02 |  | PD-004 Scope Register (page 3401221474), previously DR005 |
| REQ-079 | Modify: Change Bench Finisher | Draft | Won't | this phase |  |  | MillhouseG4Supply |  | RDD v0.4 - SR_WARP_02 |  | PD-004 Scope Register (page 3401221474), previously DR006 |
| REQ-080 | Modify: Indoor Transfer | Withdrawn | Won't | this phase |  |  | MillhouseG4Supply |  | RDD v0.4 - SR_WARP_02 |  | PD-004 Scope Register (page 3401221474), previously DR007 |
| REQ-081 | Modify: Change TradeCounter + Bolt | Withdrawn | Won't | this phase |  |  | MillhouseG4Supply |  | RDD v0.4 - SR_WARP_02 |  | PD-004 Scope Register (page 3401221474), previously DR008 |
| REQ-082 | The Millhouse supply run passive / active inventory is not managed by Bobbin | Withdrawn | Won't | this phase | 2026-07-27 |  | MillhouseG4Supply | Vendor | EX-02 |  | previously RAID-020; C0305 |
| REQ-083 | Migration of orders from Pinwheel and Tillbook is out of scope | Withdrawn | Won't | this phase | 2026-07-27 |  | Order handling | Vendor | EX-07 |  | previously RAID-021; C0305 |
| REQ-084 | Modification and cease of services provisioned outside Warp is out of scope | Withdrawn | Won't | this phase | 2026-07-27 |  | Solution scope and criteria | Vendor | EX-08 |  | previously RAID-022; C0305 |
| REQ-085 | Decommissioning of legacy source systems post-implementation is out of scope | Withdrawn | Won't | this phase | 2026-07-27 |  | Solution scope and criteria | Vendor | EX-09 |  | previously RAID-023; C0305 |
| REQ-086 | Address API search to MillPortal to generate the location Id for SQ is excluded | Withdrawn | Won't | this phase | 2026-07-27 |  | MillhouseG4Supply | Vendor | EX-15 |  | previously RAID-024; C0305 |
| REQ-087 | Transfer Reversal is out of scope | Withdrawn | Won't | this phase | 2026-07-27 |  | MillhouseG4Supply | Vendor | EX-16 |  | previously RAID-025; C0305, C1047 |
| REQ-088 | Bulk Counter migration and Counter machine / layout migration are excluded | Withdrawn | Won't | this phase | 2026-07-27 |  | CustomerCounter | Vendor | CR-14 |  | previously RAID-026; C0294, C1017, C1985, C2127 |
| REQ-089 | Service Transfer: a transfer-in connect supplies the SITEids and the CutId | Draft |  | this phase | 2026-09-07 | Marta Quill | MillhouseG4Supply | Vendor |  |  | Marta Quill, solution architect, 2026-09-07; previously SUP-REQ-01 |
| REQ-090 | Connect Outstanding: a connect where the customer does not know the CutId | Draft |  | this phase | 2026-09-07 | Marta Quill | MillhouseG4Supply | Vendor |  |  | Marta Quill, solution architect, 2026-09-07; previously SUP-REQ-02 |
| REQ-091 | Appointments are included in GDA645 | Draft |  | this phase | 2026-09-07 | Marta Quill | Order handling | Vendor |  |  | Marta Quill, solution architect, 2026-09-07; previously SUP-REQ-03 |
| REQ-092 | Bolt tenancy for wholesale-Cut-only services | Draft |  | next phase | 2026-09-07 | Marta Quill | MillhouseG4Supply | Vendor |  | dispositions LIM-019 | Marta Quill, solution architect, 2026-09-07; previously SUP-REQ-04 |

92 items.

## Prior ids

Ids were minted on 2026-09-07 and are never reused. These are the ids these items carried before, which are still quoted elsewhere. Each row also carries its prior id in Source.

| Prior | Now |
|---|---|
| REQ:REQ-p01 | REQ-001 |
| REQ:REQ-p02 | REQ-002 |
| REQ:REQ-p03 | REQ-003 |
| REQ:REQ-p04 | REQ-004 |
| REQ:REQ-p05 | REQ-005 |
| REQ:REQ-p06 | REQ-006 |
| REQ:REQ-p07 | REQ-007 |
| REQ:REQ-p08 | REQ-008 |
| REQ:REQ-p09 | REQ-009 |
| REQ:REQ-p10 | REQ-010 |
| REQ:REQ-p11 | REQ-011 |
| REQ:REQ-p12 | REQ-012 |
| REQ:REQ-p13 | REQ-013 |
| REQ:REQ-p14 | REQ-014 |
| REQ:REQ-p15 | REQ-015 |
| REQ:REQ-p16 | REQ-016 |
| REQ:REQ-p17 | REQ-017 |
| REQ:REQ-p18 | REQ-018 |
| REQ:REQ-p19 | REQ-019 |
| REQ:REQ-p20 | REQ-020 |
| REQ:REQ-p21 | REQ-021 |
| REQ:REQ-p22 | REQ-022 |
| REQ:REQ-p23 | REQ-023 |
| REQ:REQ-p24 | REQ-024 |
| REQ:REQ-p25 | REQ-025 |
| REQ:REQ-p26 | REQ-026 |
| REQ:REQ-p27 | REQ-027 |
| REQ:REQ-p28 | REQ-028 |
| REQ:REQ-p29 | REQ-029 |
| FG001 | REQ-030 |
| FG002 | REQ-031 |
| FG003 | REQ-032 |
| FG004 | REQ-033 |
| FG005 | REQ-034 |
| FG006 | REQ-035 |
| FG007 | REQ-036 |
| FG008 | REQ-037 |
| FG009 | REQ-038 |
| FG010 | REQ-039 |
| FG011 | REQ-040 |
| FG012 | REQ-041 |
| FG013 | REQ-042 |
| FG014 | REQ-043 |
| FG015 | REQ-044 |
| FG016 | REQ-045 |
| FG018 | REQ-046 |
| FG019 | REQ-047 |
| FG020 | REQ-048 |
| FG021 | REQ-049 |
| FG017 | REQ-050 |
| FG022 | REQ-051 |
| FG023 | REQ-052 |
| FG024 | REQ-053 |
| FG025 | REQ-054 |
| FC001 | REQ-055 |
| FC002 | REQ-056 |
| FC003 | REQ-057 |
| FC004 | REQ-058 |
| FC005 | REQ-059 |
| FC006 | REQ-060 |
| FC007 | REQ-061 |
| FC008 | REQ-062 |
| FC009 | REQ-063 |
| FC010 | REQ-064 |
| FC011 | REQ-065 |
| FC012 | REQ-066 |
| FC013 | REQ-067 |
| FC014 | REQ-068 |
| FC015 | REQ-069 |
| FC016 | REQ-070 |
| FC017 | REQ-071 |
| FC018 | REQ-072 |
| FC019 | REQ-073 |
| DR001 | REQ-074 |
| DR002 | REQ-075 |
| DR003 | REQ-076 |
| DR004 | REQ-077 |
| DR005 | REQ-078 |
| DR006 | REQ-079 |
| DR007 | REQ-080 |
| DR008 | REQ-081 |
| RAID-020 | REQ-082 |
| RAID-021 | REQ-083 |
| RAID-022 | REQ-084 |
| RAID-023 | REQ-085 |
| RAID-024 | REQ-086 |
| RAID-025 | REQ-087 |
| RAID-026 | REQ-088 |
| SUP-REQ-01 | REQ-089 |
| SUP-REQ-02 | REQ-090 |
| SUP-REQ-03 | REQ-091 |
| SUP-REQ-04 | REQ-092 |
