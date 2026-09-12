---
page-id: 3401220570
page-title: HAB PD-004 Limitations Register
page-version: 
page-url: https://example.atlassian.net/wiki/spaces/Restitch/pages/3401220570/HAB+PD-004+Limitations+Register
parent-page-id: 3401220005
pulled-on: 12 September 2026
---

# HAB PD-004 Limitations Register

## Register: Limitations

Holds what the solution will not do, or does differently, and how each one is being dispositioned.

One row per item. The conventions for adding or moving one by hand are in Register: Conventions.

Every row traces to a claim in the design knowledge base, to the PD-004 Scope Register, or to a recorded instruction from the solution architect. Source names which.

## Legend

### Status

| Value | What it means |
|---|---|
| Identified | Recorded, not yet assessed. |
| Under assessment | Being worked, with an owner on the open item. |
| Accepted | We live with it. A decision says so. |
| Change requested | A change request carries the fix. |
| Deferred | Carried to a later phase as a requirement. |
| Resolved | No longer true. |

## Limitations

| ID | Title | Status | Identified on | Impact | Disposition record | Scope | Implemented by | Vendor ref | Links | Source |
|---|---|---|---|---|---|---|---|---|---|---|
| LIM-001 | Ribbon gauging supports symmetric speeds only | Identified | 2026-08-07 | Phase 1 will not support asymmetric speed services (LI003). |  | CarrierRibbon | Vendor | LI003 |  | C2217 — kb-resolve re-visit feed 2026-08-07 (ruling-audit-supersede-2026-08-07), C0993 narrowing |
| LIM-003 | Customer Counter handoffs support single labelling only | Identified | 2026-07-16 | Dual-to-single label rewrites are supported but there is no multi-label delivery for Ribbon services (LI001). Inherent to the chosen design. |  | CarrierRibbon | Vendor | LI001 |  | C0990 — HAB PD-004.7 - Carrier Ribbon |
| LIM-004 | No Reel reservation on GDA641 Ribbon orders | Identified | 2026-07-16 | Only direct Reel numbers are accepted; a Reel chosen via the GDA685 availability query can be taken before the order processes, rejecting the order. Auto-allocation avoids the race (LI004). SCOPED TO THE INITIAL RELEASE - the 2026-07-29 design specs have the order-level workflow reserve an ordered … |  | CarrierRibbon | Vendor | LI004 |  | C0991 — HAB PD-004.7 - Carrier Ribbon, C1045 — User ruling (marta.quill) 2026-07-17: initial release does not support Reel reservation on the GDA641 Carrier Ribbon payload (passing a Reel is … |
| LIM-005 | Failover cannot be restricted per service on redundant Counter pairs | Identified | 2026-07-16 | Any service delivered to a redundant Counter pair always fails over (LI004, customer-counter). Inherent to the chosen design. |  | CustomerCounter | Vendor | LI004 |  | C1011 — HAB PD-004.8 - Customer Counter Supply |
| LIM-006 | No supplier-bay support on Counter bays in phase 1 | Identified | 2026-07-16 | supplierServiceId and Supplier are not modelled on Counter bays (LI005). Descoped for phase 1 rather than inherent to the design. |  | CustomerCounter | Vendor | LI005 |  | C1012 — HAB PD-004.8 - Customer Counter Supply |
| LIM-007 | Counter diversity is immutable after provisioning | Identified | 2026-07-16 | Changing diversity mode requires a new service order and a migration of services (RQ019, LI002 customer-counter). Inherent to the chosen design. |  | CustomerCounter | Vendor | LI002 | assessed by OI-012 | C1017 — HAB PD-004.8 - Customer Counter Supply |
| LIM-008 | Decommissioned strands cannot be reallocated | Identified | 2026-07-16 | Re-using strands for a different service requires a new provisioning order (LI001 customer-counter). Inherent to the chosen design. |  | CustomerCounter | Vendor | LI001 |  | C1020 — HAB PD-004.8 - Customer Counter Supply |
| LIM-009 | No manual NamedAuth authentication (customer-supplied credentials) | Deferred | 2026-07-17 | All subscriber feeds use injected auth today; enterprise customers on non-Millhouse/Silkline suppliers need manual NamedAuth auth, planned as CR-05. | REQ-059 | SubscriberTrimming | Vendor | LI-CR-05 | dispositioned by REQ-059; change request CR-031; Loomtech future CR-05 | C1044 — User ruling (marta.quill) 2026-07-17: current-state limitation - manual NamedAuth auth (username/password) not supported; injected auth only (supplierServiceId username + fixed password); needed … |
| LIM-010 | CarrierRibbon is single-homed on both sides | Identified | 2026-07-30 | A CarrierRibbon connection relates to exactly one Customer Counter and one Millhouse Supply connection at a time. The data model permits several workshop handovers over time, but only one is ever active, so a change replaces rather than adds - there is no simultaneous dual-homing for redundancy. Inherent … |  | CarrierRibbon | Vendor |  |  | C1742 — sources/backroom/FSD-2026-07-29/CarrierRibbon-RBVC-Connect-Design-Spec_1_13.md, C1743 — sources/backroom/FSD-2026-07-29/CarrierRibbon-RBVC-Connect-Design-Spec_1_13.md, C1744 — … |
| LIM-011 | CarrierRibbon is strictly point-to-point | Identified | 2026-07-30 | Every connection has exactly two ends, one workshop-facing and one customer-facing. No multipoint layout is supported - one handover fanning out to several supplies, or the reverse, would be a substantive design change. |  | CarrierRibbon | Vendor |  |  | C1745 — sources/backroom/FSD-2026-07-29/CarrierRibbon-RBVC-Connect-Design-Spec_1_13.md |
| LIM-012 | Only the Millhouse-Supply-to-Counter connection flavour is orderable | Identified | 2026-07-30 | The data model recognises several Ribbon connection flavours for future use cases, but only the one joining an Millhouse Supply to a workshop handover is implemented. BORDERLINE cause - classified design because the specs frame the others as anticipated categories rather than work descoped for time … |  | CarrierRibbon | Vendor |  |  | C1746 — sources/backroom/FSD-2026-07-29/CarrierRibbon-RBVC-Connect-Design-Spec_1_13.md |
| LIM-013 | No path back to automatic Reel assignment once a specific Reel is set | Identified | 2026-07-30 | Once the workshop-facing Reel has been set to a specific value, every later change must also specify a value - the system will not revert to picking one automatically. Applies at connect and at modify alike. Inherent to the chosen design. |  | CarrierRibbon | Vendor |  |  | C1747 — sources/backroom/FSD-2026-07-29/CarrierRibbon-RBVC-Connect-Design-Spec_1_13.md, C1905 — sources/backroom/FSD-2026-07-29/CarrierRibbon-RBVC-Modify-Design-Spec_1.md |
| LIM-014 | The fourth CustomerCounter redundancy option is declared but not orderable | Identified | 2026-07-30 | single-active-dual-homed is present in the redundancyMode enum but is not implemented and must not be requested. BORDERLINE cause - classified time-constraint because the specs say "not yet available", implying intended later work rather than a permanent design boundary. |  | CustomerCounter | Vendor |  |  | C1972 — sources/backroom/FSD-2026-07-29/CustomerCounter-Counter-Connect-Design-Spec_8.md |
| LIM-015 | No modify path between no-redundancy and a redundant mode | Identified | 2026-07-30 | Switching between Active/Active and Active/Passive is a supported modify, but moving into or out of no-redundancy is not, in either direction - it is structural and impacts every Ribbon service riding the Counter. wsiId is untouched by a switch between the two redundant sub-modes and would only need … |  | CustomerCounter | Vendor |  |  | C1985 — sources/backroom/FSD-2026-07-29/CustomerCounter-Counter-Connect-Design-Spec_8.md, C2127 — sources/backroom/FSD-2026-07-29/CustomerCounter-Counter-Modify-Design-Spec_4.md, C2175 — … |
| LIM-016 | One CustomerCounter maps to exactly one workshop configuration | Identified | 2026-07-30 | There is no scenario in the current design where a single customer handover maps to more than one underlying workshop configuration. |  | CustomerCounter | Vendor |  |  | C1990 — sources/backroom/FSD-2026-07-29/CustomerCounter-Counter-Connect-Design-Spec_8.md |
| LIM-017 | At most two physical locations per CustomerCounter | Identified | 2026-07-30 | The redundancy and bundling rules assume a primary and a secondary location only; more than two is not supported by the model. Inherent to the chosen design. |  | CustomerCounter | Vendor |  |  | C1991 — sources/backroom/FSD-2026-07-29/CustomerCounter-Counter-Connect-Design-Spec_8.md |
| LIM-018 | An MillhouseG4Supply order cannot specify a particular c-label | Identified | 2026-08-06 | An MillhouseG4Supply order cannot specify a particular c-label; there is currently no requirement to do so. The claim calls it a phase 1 limitation, which is why cause is time-constraint rather than design - it is not stated to be a permanent boundary. |  | MillhouseG4Supply | Vendor |  |  | C2188 — sources/backroom/loomtech-technical-sync-up-2026-08-05-notes.md (Loomtech technical sync-up, 2026-08-05) |
| LIM-019 | Only shared Bolts are supported; dedicated Bolt tenancy is not | Deferred | 2026-08-06 | Only the shared Bolt pool is available (tenant 1 is the default tenancy, C2222). A wholesale-Cut-only customer needing a dedicated Bolt cannot be delivered, and a Bolt tenancy id is already an Backroom order requirement (C2187) with no dedicated tenancy behind it. | REQ-092 | MillhouseG4Supply | Vendor |  | dispositioned by REQ-092; change request CR-027 | C2200 — sources/backroom/loomtech-technical-sync-up-2026-08-05-notes.md (Loomtech technical sync-up, 2026-08-05) |
| LIM-020 | Millhouse organisation creation via MillPortal is not implemented | Identified | 2026-09-07 | Business and residential users are both supported, but an organisation cannot be created in Millhouse MillPortal, so a business connect order that needs a new Millhouse organisation has no path. |  | MillhouseG4Supply | Vendor |  | assessed by OI-074 | Marta Quill, solution architect, 2026-09-07 |

19 items.

## Prior ids

Ids were minted on 2026-09-07 and are never reused. These are the ids these items carried before, which are still quoted elsewhere. Each row also carries its prior id in Source.

| Prior | Now |
|---|---|
| LIM:LIM-001 | LIM-001 |
| LIM:LIM-003 | LIM-003 |
| LIM:LIM-004 | LIM-004 |
| LIM:LIM-005 | LIM-005 |
| LIM:LIM-006 | LIM-006 |
| LIM:LIM-007 | LIM-007 |
| LIM:LIM-008 | LIM-008 |
| LIM:LIM-009 | LIM-009 |
| LIM:LIM-010 | LIM-010 |
| LIM:LIM-011 | LIM-011 |
| LIM:LIM-012 | LIM-012 |
| LIM:LIM-013 | LIM-013 |
| LIM:LIM-014 | LIM-014 |
| LIM:LIM-015 | LIM-015 |
| LIM:LIM-016 | LIM-016 |
| LIM:LIM-017 | LIM-017 |
| LIM:LIM-018 | LIM-018 |
| LIM:LIM-019 | LIM-019 |
| LIM:LIM-020 | LIM-020 |
