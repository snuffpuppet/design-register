---
page-id: 3401220683
page-title: HAB PD-004 Outstanding
page-version: 
page-url: https://example.atlassian.net/wiki/spaces/Restitch/pages/3401220683/HAB+PD-004+Outstanding
parent-page-id: 3401220005
pulled-on: 12 September 2026
---

# HAB PD-004 Outstanding

## Register: Outstanding

The meeting view, regenerated from the six registers on 2026-09-07. Items with Phase = next phase are excluded and appear on Register: Next phase instead.

A row here without an owner, a next action and a due date is a defect in the register, not a discussion point. The gaps below are known and are being filled by hand; they are listed rather than hidden.

## Legend

### Status - open items

| Value | What it means |
|---|---|
| Open | Raised, not yet started. |
| In progress | Someone is working it. |

### Status - limitations

| Value | What it means |
|---|---|
| Identified | Recorded, not yet assessed. |

### Status - risks

| Value | What it means |
|---|---|
| Mitigating | Actively managed, and reviewed on its due date. |

### Likelihood and Impact

| Value | What it means |
|---|---|
| high | As judged at the last review. |
| medium | As judged at the last review. |

### Status - change requests

| Value | What it means |
|---|---|
| Proposed | Ours, and being reasoned. |
| Submitted | Handed to whoever will implement it. |

### MoSCoW

| Value | What it means |
|---|---|
| Must | Required for this phase. |
| Should | Wanted, and not required. |
| Could | Taken if it is cheap. |
| Won't | Agreed as out of scope. Recorded, not deleted. |

## 1. Open items not closed

55 of 75. Grouped by owner, then by due date.

### Marta Quill — 8

| ID | Title | Status | Scope | Next action | Due | Blocked by |
|---|---|---|---|---|---|---|
| OI-028 | How an operator abandons a Retry-only fallout is unruled | Open | Fallout and intervention | Rule whether an operator working a Retry-only fallout task can deliberately route the order onto the jeopardy-and-Shopfront-cancellation path, or whether that path … | — |  |
| OI-068 | Validate phase 1 CR prioritisation | Open | Solution scope and criteria | Meet to discuss phase 1 CR prioritisation | — |  |
| OI-069 | Query Appointment API: confirm delivery timing and priority | Open | Order handling | Establish with Loomtech when the Query Appointment API lands and what priority it carries | — |  |
| OI-070 | Customer Counter change matrix | Open | CustomerCounter | Run the change matrix past Cormac Blythe, then past Nadia Frost | — |  |
| OI-071 | Police requests: temporarily disable a Home or BT&W Subscriber Trimming service using suspension gauges | Open | SubscriberTrimming | Run the gauging and handoff solution past the team | — |  |
| OI-072 | Police requests: wholesale services punted to the wholesaler | Open | MillhouseG4Supply | Establish whether punting the request to the wholesaler is acceptable | — |  |
| OI-073 | Police requests: the T&W Carrier Ribbon approach | Open | CarrierRibbon | Decide whether to address this now or defer it | — |  |
| OI-074 | Design Millhouse organisation creation via MillPortal | Open | MillhouseG4Supply | Take the proposed cache-and-create approach through ingest so it becomes design truth, then design it with Loomtech | — |  |

### Vendor — 32

| ID | Title | Status | Scope | Next action | Due | Blocked by |
|---|---|---|---|---|---|---|
| OI-002 | GDA638 endpoint representation does not match RQ018's requested shape | Open | CarrierRibbon | RQ018 asks for each Ribbon endpoint to be modelled as a service relationship or embedded characteristic on the parent GDA638 service, preserving the … | — |  |
| OI-003 | Run-id audit query shape and storage (RQ024/RQ025) unspecified | Open | CarrierRibbon | Confirm how the Ribbon run-id audit trail is realised in Bobbin / Warp / Loom - the query shape, and where the audit record is held. | — |  |
| OI-006 | Fallout is out of scope of the design specs, and the Fail path contradicts point-of-no-return | Open | CarrierRibbon | Confirm or replace the CarrierRibbon fallout profile, and rule the contradiction between the framework's Fail path ending in a Shopfront cancellation request and … | — |  |
| OI-007 | GDA685 payload convention not settled, so no pool-draw or release payload is specified | Open | CarrierRibbon | Confirm the GDA685 payload convention so the CREEL and tapeId pool-draw and release request bodies can be stated. | — |  |
| OI-009 | Limiter override values are illustrative, and the fractional ebs rounding is assumed | Open | CarrierRibbon | Supply the agreed per-endpoint limiter override table, and confirm the rounding rule for a fractional ebs. | before the Carrier Ribbon build |  |
| OI-011 | RQ022 fitting-capacity validation of the gauging rate is L4-only, not restated at L1 | Open | CarrierRibbon | Confirm the RQ022 fitting-capacity validation of the gauging rate exists in the implemented design, the L1 specifications bounding only the orderable enum … | — |  |
| OI-012 | Counter machine migration and single<->bundle layout change have no designed workflow | Open | CustomerCounter | Supply the designed workflow for an Counter layout change (adding or removing a strand, changing bundling mode) and the resulting customer service migrations … | — |  |
| OI-013 | Customer engagement and outage coordination for Counter layout migrations | Open | CustomerCounter | Confirm how customer impact and the outage are handled during an Counter layout-change migration from a workflow perspective - is an extra manual process … | — |  |
| OI-016 | Bay-allocation audit log mechanism (RQ024/RQ025) unspecified | Open | CustomerCounter | Confirm how the RQ024 / RQ025 bay-allocation audit log is realised in Bobbin / Warp - where it is held, and the query shape. | — |  |
| OI-020 | Edge distinctness when both place entries name the same Depot | Open | CustomerCounter | When a redundant CustomerCounter order names the same Depot under both Primary_Depot and Secondary_Depot, does the bay-selection algorithm guarantee the two legs land … | — |  |
| OI-023 | CarrierRibbon fallout and cancellation handling is not designed | Open | Fallout and intervention | Supply an FSD-level CarrierRibbon fallout profile naming exactly which operator options exist, as the other three services carry. (Service-side view … | — |  |
| OI-024 | No CarrierRibbon_E4_Winder exception-flow diagram exists | Open | Fallout and intervention | Provide the CarrierRibbon_E4_Winder exception-flow diagram the framework routes a Winder feed-management callback failure to, or confirm the route was never … | — |  |
| OI-025 | Reason-code normalisation into the Shopfront contract is semi-deferred and unmapped | Open | Fallout and intervention | Supply the supplier reason-code outcome mappings and their note / jeopardy / error classification, so the Shopfront can know which signal a given supplier failure … | — |  |
| OI-029 | Two Millhouse validation failures assert the terminal-rejection path without a claim naming it | Open | Fallout and intervention | Confirm which handler each of the two Millhouse validation failures invokes, in which phase, and what the Shopfront receives. | — |  |
| OI-030 | TPI cotton-pair rule and supplyTechnology -> millProduct mapping pending FSD | Open | MillhouseG4Supply | Confirm the supplyTechnology -> millProduct.productType mapping, and that millProduct MCAS covers the cotton-terminating technologies CTB / CTN / CTC the TPI … | — |  |
| OI-032 | IPM (service moving to Loomtech from another T&T system) has no designed workflow | Open | MillhouseG4Supply | — | — |  |
| OI-033 | Transfer reversal (undo switch-away) and address retention | Open | MillhouseG4Supply | — | — |  |
| OI-034 | Backroom-handled Millhouse ProductOrderReasonCode classification list not in the corpus | Open | MillhouseG4Supply | — | pre-go-live - blocks configuring the Millhouse callback error-code routing |  |
| OI-035 | FRD003 bulk Millhouse location federation / upload not evidenced | Open | MillhouseG4Supply | Confirm how Millhouse locations are populated in bulk (pre-seeding or federation) so a GDA641 order can reference a SiteId that already exists. | — |  |
| OI-036 | FRB006 Change SLA enumerated but mechanism unspecified | Open | MillhouseG4Supply | Confirm the Millhouse-side change mechanism for Service Restoration SLA on an in-flight service: which productOrder is raised, and whether the Millhouse lifecycle re-runs. | — |  |
| OI-041 | FRP002 disable service has no solution mechanism | Open | SubscriberTrimming | Specify the order pattern and the restoration semantics for the FRP002 police-request disable capability. | — |  |
| OI-043 | Cycle Lot scope - static re-allocation vs the FSD's "dynamic" wording | Open | SubscriberTrimming | Confirm which path a STATIC Lot re-allocation rides - cycleLot, lotAllocationFunction or the lots scenario - given the FSD scopes cycleLotA / cycleLotB to a … | — |  |
| OI-047 | Disconnect LotRegistry decommission fallout handling presumed | Open | SubscriberTrimming | Confirm the disconnect flow's LotRegistry decommission failure handling mirrors the connect-side HTTP-code rules to MendingBench. | — |  |
| OI-051 | FRB004 subscriberProtocol modify path not evidenced | Open | SubscriberTrimming | Confirm the intended subscriberProtocol modify path, given the FSD's definitive six update scenarios exclude it while decision DE014 intends GDA640. | — |  |
| OI-052 | No-inflight-order precondition generalised to all modifies | Open | SubscriberTrimming | Confirm the no-concurrent-inflight-order precondition applies to every modify scenario, not only disconnect, suspend and the approved concurrent Supply + … | — |  |
| OI-056 | SubscriberTrimming FSD self-contradicts on the activation write (GDA638 PUT vs PATCH) | Open | SubscriberTrimming | Confirm whether the CFS is set active with a GDA638 PUT or a PATCH, the FSD page text and its own process-flow diagram disagreeing. | — |  |
| OI-057 | Dispenser update (reservation-upsert) ASYNC correlation key not stated | Open | SubscriberTrimming | Confirm the ASYNC correlation key for the Dispenser update (reservation-upsert) operation, presumed to be the create form, so the phase-2 callback correlation is … | — |  |
| OI-058 | LotRegistryConfiguration reallocate - a Service Order operation or an internal composite step | Open | SubscriberTrimming | — | — |  |
| OI-063 | Shared conventions document absent from the handover, and its KDD-6 relationship-merge rule unverifiable | Open | CarrierRibbon | Two service-agnostic design items moved out of this specification into a shared conventions document that is absent from the handover, and that document's … | — |  |
| OI-064 | CNTB baySpeed presence and CustomerCounter bundleSkein type disagree between the FSD and TTModel v0.72 | Open | CustomerCounter | Whether the CNTB resource carries baySpeed, and whether CustomerCounter bundleSkein is a boolean or a String, are unresolved: the CustomerCounter FSD v6 places … | — |  |
| OI-065 | Whether GDA645 appointmentRequired must account for HYB Finisher-bay availability | Open | MillhouseG4Supply | Whether the GDA645 appointmentRequired answer should account for HYB Finisher-bay availability is unresolved: the GDA645 mapping derives it solely from Millhouse … | — |  |
| OI-075 | Dispenser and Tallyboard ingester blacklisting recovery: cancelling or restarting a workflow after a failed task | Open | SubscriberTrimming | Establish with Loomtech how a workflow is cancelled or restarted when a previous task failed, e.g. LotRegistry bad data causing a Dispenser failure with no way to cancel or edit the data | — |  |

### Vendor: Nadia Frost — 3

| ID | Title | Status | Scope | Next action | Due | Blocked by |
|---|---|---|---|---|---|---|
| OI-015 | Effect of customer-labelled legacy Millhouse services on Depot handoffs | Open | CustomerCounter | Follow up legacy Bench labelling with Nadia Frost | — |  |
| OI-039 | MillhouseG4Supply FSD Modify and Delete sections document no workflows | In progress | MillhouseG4Supply | Nadia Frost is authoring the Finisher workflows | — |  |
| OI-066 | Source of the legacy Bench label value — Millhouse order/response or manual entry | Open | MillhouseG4Supply | Follow up legacy Bench labelling with Nadia Frost | — |  |

### (no owner yet) — 12

| ID | Title | Status | Scope | Next action | Due | Blocked by |
|---|---|---|---|---|---|---|
| OI-005 | Shopfront-side orphaned-supply safeguard (RQ027), and no terminate-time guard on MillhouseG4Supply | Open | CarrierRibbon | Confirm with Loomtech whether the absent terminate-time orphaned-supply guard on MillhouseG4Supply is deliberate, CustomerCounter carrying the reciprocal guard. (The … | — |  |
| OI-010 | Principle P001 (supply-agnostic delivery) is not satisfied by the delivered scope | Open | CarrierRibbon | Decide whether principle P001 (a Ribbon delivery must be supply agnostic, allowing arbitrary supplies to be connected) is restated as forward-looking, scoped … | — |  |
| OI-017 | T&W Customer Counters unsupported by the migration automation | Open | CustomerCounter | — | before the Bobbin Counter migration batches are planned |  |
| OI-018 | Sticky-WVI cleanup under planned outages needs an operational process | Open | CustomerCounter | — | pre-go-live - the process must exist before the first planned-outage cleanup |  |
| OI-021 | Shopfront-side realisation of the fallout / jeopardy queue hat is unconfirmed | Open | Fallout and intervention | — | — |  |
| OI-026 | No Backroom validation prevents orphaned supply services after cancellation | Open | Fallout and intervention | — | — |  |
| OI-053 | Suspend/Resume page placement (6.5 vs 6.2) | Open | SubscriberTrimming | Confirm the preferred page placement for Suspend / Resume - PD-004.6.5, or PD-004.6.2 since it is mechanically a pure speed change. | — |  |
| OI-054 | Shopfront operations / service delivery actor roles to confirm | Open | SubscriberTrimming | — | — |  |
| OI-059 | WRG failover handling for machine-targeted Winder feed requests | Open | SubscriberTrimming | Confirm with Workshops how a machine-targeted Winder feed request is handled under an WRG failover - two requests, one per member machine, or a layout-aware … | — |  |
| OI-061 | Review the suspend configuredSpeed default (1 m/min) before production | Open | SubscriberTrimming | — | pre-production |  |
| OI-062 | Some T&W Customer Counters are unsupported by the migration automation and will be delayed | Open | CustomerCounter | Enumerate the unsupported configurations and agree the manual fallback path and its effort with the workshop team. | — |  |
| OI-067 | Decide whether G4 Wholesale includes dedicated customer Bolt use cases | Open | MillhouseG4Supply | Convene Ruth Calder, Ines Duarte and Cormac Blythe to choose between a pinned Bolt and a ribbon tunnel for the service | — |  |

## 2. Limitations in Identified or Under assessment

17 of 19. Oldest first.

| ID | Title | Status | Identified on | Scope | Impact |
|---|---|---|---|---|---|
| LIM-003 | Customer Counter handoffs support single labelling only | Identified | 2026-07-16 | CarrierRibbon | Dual-to-single label rewrites are supported but there is no multi-label delivery for Ribbon services (LI001). Inherent to the chosen design. |
| LIM-004 | No Reel reservation on GDA641 Ribbon orders | Identified | 2026-07-16 | CarrierRibbon | Only direct Reel numbers are accepted; a Reel chosen via the GDA685 availability query can be taken before the order processes, rejecting the order. Auto-alloca |
| LIM-005 | Failover cannot be restricted per service on redundant Counter pairs | Identified | 2026-07-16 | CustomerCounter | Any service delivered to a redundant Counter pair always fails over (LI004, customer-counter). Inherent to the chosen design. |
| LIM-006 | No supplier-bay support on Counter bays in phase 1 | Identified | 2026-07-16 | CustomerCounter | supplierServiceId and Supplier are not modelled on Counter bays (LI005). Descoped for phase 1 rather than inherent to the design. |
| LIM-007 | Counter diversity is immutable after provisioning | Identified | 2026-07-16 | CustomerCounter | Changing diversity mode requires a new service order and a migration of services (RQ019, LI002 customer-counter). Inherent to the chosen design. |
| LIM-008 | Decommissioned strands cannot be reallocated | Identified | 2026-07-16 | CustomerCounter | Re-using strands for a different service requires a new provisioning order (LI001 customer-counter). Inherent to the chosen design. |
| LIM-010 | CarrierRibbon is single-homed on both sides | Identified | 2026-07-30 | CarrierRibbon | A CarrierRibbon connection relates to exactly one Customer Counter and one Millhouse Supply connection at a time. The data model permits several workshop handovers over |
| LIM-011 | CarrierRibbon is strictly point-to-point | Identified | 2026-07-30 | CarrierRibbon | Every connection has exactly two ends, one workshop-facing and one customer-facing. No multipoint layout is supported - one handover fanning out to several acc |
| LIM-012 | Only the Millhouse-Supply-to-Counter connection flavour is orderable | Identified | 2026-07-30 | CarrierRibbon | The data model recognises several Ribbon connection flavours for future use cases, but only the one joining an Millhouse Supply to a workshop handover is implemented |
| LIM-013 | No path back to automatic Reel assignment once a specific Reel is set | Identified | 2026-07-30 | CarrierRibbon | Once the workshop-facing Reel has been set to a specific value, every later change must also specify a value - the system will not revert to picking one automati |
| LIM-014 | The fourth CustomerCounter redundancy option is declared but not orderable | Identified | 2026-07-30 | CustomerCounter | single-active-dual-homed is present in the redundancyMode enum but is not implemented and must not be requested. BORDERLINE cause - classified time-constraint b |
| LIM-015 | No modify path between no-redundancy and a redundant mode | Identified | 2026-07-30 | CustomerCounter | Switching between Active/Active and Active/Passive is a supported modify, but moving into or out of no-redundancy is not, in either direction - it is structural |
| LIM-016 | One CustomerCounter maps to exactly one workshop configuration | Identified | 2026-07-30 | CustomerCounter | There is no scenario in the current design where a single customer handover maps to more than one underlying workshop configuration. |
| LIM-017 | At most two physical locations per CustomerCounter | Identified | 2026-07-30 | CustomerCounter | The redundancy and bundling rules assume a primary and a secondary location only; more than two is not supported by the model. Inherent to the chosen design. |
| LIM-018 | An MillhouseG4Supply order cannot specify a particular c-label | Identified | 2026-08-06 | MillhouseG4Supply | An MillhouseG4Supply order cannot specify a particular c-label; there is currently no requirement to do so. The claim calls it a phase 1 limitation, which is why cause |
| LIM-001 | Ribbon gauging supports symmetric speeds only | Identified | 2026-08-07 | CarrierRibbon | Phase 1 will not support asymmetric speed services (LI003). |
| LIM-020 | Millhouse organisation creation via MillPortal is not implemented | Identified | 2026-09-07 | MillhouseG4Supply | Business and residential users are both supported, but an organisation cannot be created in Millhouse MillPortal, so a business connect order that needs a new Millhouse organisat |

## 3. Risks that are high impact or overdue for review

15 of 18. A risk with no review date is included, because model 4.4 requires one before a risk is Mitigating and none is recorded yet.

| ID | Title | Status | Likelihood | Impact | Raised by | Due | Mitigation |
|---|---|---|---|---|---|---|---|
| RSK-001 | No in-flight orders are migrated to or processed in Warp | Mitigating | — | — | program | none set | Program cutover plan - the legacy order-drain approach and its cut-off date |
| RSK-002 | Disaster Recovery failover is manual and all-or-nothing | Mitigating | — | — | tt-internal | none set | T&T infrastructure team plus the Loomtech DR runbook and a tested failover |
| RSK-003 | CustomerCounter services are a prerequisite of the Millhouse G4 CarrierRibbon Handoff | Mitigating | — | — | Loomtech | none set | Loomtech Drop 3 design and the CarrierRibbon FSD, once authored |
| RSK-004 | The first service to execute Design and Assign creates the T&T Service Order object | Mitigating | — | — | Loomtech | none set | The MillhouseG4Supply and CarrierRibbon FSD order-object creation sequences |
| RSK-005 | On any Lot-changing modify the old Lot is always deallocated, even a static Lot | Mitigating | — | — | Loomtech | none set | The SubscriberDispatch and LotRegistryConfiguration FSD reallocate behaviour |
| RSK-006 | The GDA641 customer site address is already validated against the supplier | Mitigating | — | — | shopfront | none set | Shopfront order-capture validation of address against Supplier Location ID |
| RSK-007 | TrimAuto LotRegistry readiness and the Bobbin Lot Pool-to-Till lookup | Mitigating | — | — | workshop-team | none set | TrimAuto LotRegistry readiness + the Lot Pool-to-Till lookup in Bobbin |
| RSK-008 | T&T Conveyor Resiliency Project for the Dispenser / Tallyboard / Till / RepairsDesk integrations | Mitigating | — | — | tt-internal | none set | T&T Conveyor Resiliency Project |
| RSK-010 | MillPortal ProductOrderReasonCode classification mappings not yet provided | Mitigating | — | — | Loomtech | none set | MillPortal_Notification_WarpActions reason-code mappings from Loomtech |
| RSK-011 | Shopfront-side jeopardy handling of the Backroom jeopardy event | Mitigating | — | — | shopfront | none set | Shopfront handling of ServiceOrderJeopardyEvent and the resulting cancel / amend |
| RSK-012 | Shopfront-side orphaned-supply safeguard after a Ribbon cancellation (RQ027) | Mitigating | — | — | shopfront | none set | Shopfront-side orphaned-supply safeguard |
| RSK-013 | Integrating systems not ready, forcing stubbed lower environments | Mitigating | medium | high | program | none set | Stubs in lower environments per RI-01, with real integration mandatory from SIT onward; track each integration's readine |
| RSK-014 | SubscriberTrimming FSD self-contradicts on the activation write (GDA638 PUT vs PATCH) | Mitigating | medium | medium | Loomtech | none set | Confirm the intended operation with Loomtech before the Drop 1 activation build. |
| RSK-015 | CustomerCounter FSD self-contradicts on the modify scope | Mitigating | medium | medium | Loomtech | none set | ANSWERED by the 2026-07-29 Loomtech design specs - the modify scope is settled (throughput, add/remove connections, suspend |
| RSK-018 | Sticky WVIs accumulate deprecated configuration with no designed cleanup process | Mitigating | high | medium | workshop-team | none set | Design the cleanup and planned-outage scheduling process as an operational readiness item before the Counter service goes l |

## 4. Change requests in Proposed, Submitted or Impact assessment

11 of 38, this phase only.

| ID | Title | Status | Scope | Reason | Vendor ref |
|---|---|---|---|---|---|
| CR-005 | Support for service migrations to new Bolts | Proposed | MillhouseG4Supply | manual service migrations between Bolts |  |
| CR-006 | Support transfer reversal for services incorrectly switched away | Proposed | MillhouseG4Supply | End user has no way of returning to T&T; loss of customer and bad customer experience |  |
| CR-022 | Support for disabling a service as a privileged order with permission control | Proposed | SubscriberTrimming | Without this cannot execute police requests during police operations to shut down service. Agency requests that need to |  |
| CR-023 | Must have a way of completing orders that lack automation rules and drop to fallout (e.g. Finisher capacity exceeded) | Proposed | Fallout and intervention | Modify and connect scenarios we do not automate fall out to MendingBench; without a way to complete them the order is stuck |  |
| CR-024 | Manually change a service configuration and re-sync | Proposed | Fallout and intervention | Needed for ops team to troubleshoot services |  |
| CR-025 | Support for GDA674 GeographicSite for Shopfront calls to read site information | Proposed | Order handling | GDA641 requires the supplier address to be a reference; we need an API to create the address in the Backroom before submittin |  |
| CR-034 | Explicit feed management on delete | Submitted | SubscriberTrimming | Explicit feed management on delete is promoted to a phase 1 requirement: Loomtech will add it to phase 1. |  |
| CR-035 | subscriberProtocol modify path | Submitted | SubscriberTrimming | A subscriberProtocol modify path is now a requirement: Loomtech has taken it as new work and will raise a phase 1 CR to imp |  |
| CR-036 | WRG-aware Winder feed management, legacy and WRG-member Winders | Submitted | SubscriberTrimming | WRG-aware Winder feed management is now a requirement: Loomtech will deliver it in phase 1 via a CR supporting both legacy |  |
| CR-037 | Service Transfer: supply the SITEids and the CutId on a transfer-in connect | Proposed | MillhouseG4Supply | A transfer-in connect has no designed path today |  |
| CR-038 | Connect Outstanding: connect a service where the customer does not know the CutId | Proposed | MillhouseG4Supply | Customers frequently do not hold their CutId, so a connect keyed on it cannot proceed |  |

## 5. Decisions proposed and not accepted

36 of 58. Model 8 lists proposals older than 14 days; no proposal here records a date it was raised, so all are shown and all are older than 14 days by their source document's age.

| ID | Title | Scope | Raised by | Rationale |
|---|---|---|---|---|
| DEC-002 | Derived RB properties live on the service, populated by RFS business rules | CarrierRibbon | — | real choice with stated rationale (service clarity, telemetry, naming) — DE012 |
| DEC-003 | Every configured Ribbon resource carries a human-readable unique id | CarrierRibbon | — | principle constraining later design — every RB resource needs a human-readable unique id (DE001/DE009) |
| DEC-004 | Appointment rescheduling is a GDA641 Modify, not an independent lifecycle object | Order handling | — | explicit rejected option (appointments as independent lifecycle objects); endorsed and approved 2025-12-09 |
| DEC-006 | A Bolt error drops the order to MendingBench and re-triggers Bolt selection | Fallout and intervention | — | real choice on Bolt error handling (DE001, decided 2026-03-03) |
| DEC-008 | Bench locations are supplier-specified and not grouped by address or site | Order handling | — | explicit choice: Bench locations NOT grouped by address or site (DE010) |
| DEC-009 | Every RFS is a configuration service, and RFSs are reusable across CFSs | Service model | — | principle other design must follow — every RFS is a configuration service (Pattern #3, DE006) |
| DEC-010 | OrderStatus 'Held' introduced for orders parked in MendingBench or awaiting the Shopfront | Service model | — | real choice — new OrderStatus 'Held' introduced (DE011, 2026-03-03) |
| DEC-014 | SharedDepot modelling is not required for the Counter; the customer DEPOT is the only location input | CustomerCounter | — | real choice — SharedDepot modelling not required for the Counter (DE003); supersedes C1010 |
| DEC-015 | Revenue bays are modelled multi-speed by capability, not by fixed fitting name | CustomerCounter | — | real choice with rationale — capability field rather than fixed-speed fitting name (DE004/IS002) |
| DEC-016 | On Counter decommission resource references are deleted and the service is left terminated | CustomerCounter | — | real choice — resource refs deleted, service left terminated (DE001) |
| DEC-018 | The system that places an order is responsible for cancelling it | Upstream Shopfront integration | — | principle P001 — the system that places an order cancels it |
| DEC-019 | The Backroom has full control over the lifecycle of its own orders | Upstream Shopfront integration | — | principle P002 — the Backroom controls its own order lifecycle |
| DEC-020 | The Backroom normalises supplier reason codes so the Shopfront carries no per-code logic | Upstream Shopfront integration | — | principle — Backroom normalises supplier reason codes so the Shopfront carries no per-code logic |
| DEC-021 | Upstream order updates communicate intent broadly rather than supplier detail | Upstream Shopfront integration | — | real choice — upstream updates communicate intent broadly (DE001, 2026-03-03) |
| DEC-022 | Full normalisation of supplier messages into the Shopfront contract is semi-deferred | Upstream Shopfront integration | — | accepts a deferral — full normalisation semi-deferred (DE002, 2026-03-03) |
| DEC-024 | Jeopardy management is a Shopfront responsibility, not the Backroom | MillhouseG4Supply | — | principle — jeopardy management is a Shopfront responsibility (KDD OSF.5) |
| DEC-025 | Special processing and fallout are managed in the Shopfront via Conveyor events | MillhouseG4Supply | — | principle — special processing and fallout in the Shopfront via Conveyor (KDD OSF.7) |
| DEC-026 | Proof-of-Ownership is not passed to MillPortal; the earlier GDA641 carriage is rescinded | MillhouseG4Supply | — | real choice, and it rescinds an earlier decision (DI002 superseded by DI003) |
| DEC-027 | Backroom-classified Millhouse reason codes notify the Shopfront, move to MendingBench and set HELD | MillhouseG4Supply | — | real choice — Backroom-classified reason codes default to notify, MendingBench, HELD (DI004) |
| DEC-029 | WVI, WSI and TAPEID are single global pools, not per-Counter | Identifier and Reel management | Vendor: Loomtech | real choice with a rejected option — single global pools, not per-Counter |
| DEC-030 | Terminated services are retained in inventory then batch-purged after a set period | Bobbin service and resource model | Vendor: Loomtech | real choice — terminated objects retained for a configurable period then batch-purged |
| DEC-031 | Physical resources are released immediately on termination | Bobbin service and resource model | Vendor: Loomtech | real choice — physical resources released immediately, independent of the logical purge |
| DEC-032 | Counter bay selection may target either a Bundle or a direct physical bay | Bay allocation | Vendor: Loomtech | real choice — bay selection may target a Bundle or a direct physical bay; resolves Loomtech OI-12 |
| DEC-033 | The model standardises on Bundle terminology rather than Bundle | Bay allocation | Vendor: Loomtech | terminology standard other design must follow — Bundle, not Bundle; resolves Loomtech OI-11 |
| DEC-034 | Bobbin manages SREELs and CREELs, and T&T uses single labelling | Identifier and Reel management | Vendor: Loomtech | real choice — T&T uses single labelling |
| DEC-035 | Reel Manager is authoritative for TradeCounter and Bolt Reel management, not Bobbin | Identifier and Reel management | Vendor: Loomtech | explicit rejected option — Reel Manager authoritative over Bobbin Number Management for TradeCounter/Bolt (DC-06) |
| DEC-037 | A fresh Service Qualification check is performed inside the Connect workflows | Solution scope and criteria | Vendor: Loomtech | principle — a fresh SQ check inside the Connect workflows (DC-01) |
| DEC-038 | Supply order completion is the point of no return, except for disconnect | Solution scope and criteria | Vendor: Loomtech | principle — supply order completion is the PONR except for disconnect (DC-02) |
| DEC-039 | Error and fallout handling supports both approaches, configurable per failure | Solution scope and criteria | Vendor: Loomtech | real choice — both fallout approaches supported and configurable per failure (DC-03) |
| DEC-041 | Loomtech implements on the model-driven framework, not the intent-driven one | Solution scope and criteria | Vendor: Loomtech | explicit rejected option — model-driven framework, not intent-driven (DC-04) |
| DEC-042 | Only Shopfront/Till-originated modify use cases are Loomtech-supported | Solution scope and criteria | — | accepts a boundary — only Shopfront/Till-originated modifies are Loomtech-supported (DR-031) |
| DEC-043 | Bulk operations are not supported at Basket level and are submitted individually | Solution scope and criteria | — | accepts a boundary — no bulk operations at Basket level (DR-032) |
| DEC-047 | TrimAuto LotRegistry is authoritative for Lot management, not Bobbin Number Management | SubscriberTrimming | Vendor: Loomtech | explicit rejected option — TrimAuto LotRegistry authoritative over Bobbin Number Management (DC-05) |
| DEC-048 | Lot address management is centralised in TrimAuto LotRegistry | SubscriberTrimming | — | principle 'there can be only one' LotRegistry (DR-033), with a stated dependency on Tillbook migrating |
| DEC-057 | Should G4 Wholesale include dedicated customer Bolt use cases? | Solution scope and criteria | — | Ribbon delivery has two options: pinned Bolt (do nothing), or a ribbon tunnel for the service. |
| DEC-058 | Any hardware dispatch done by us is out of scope. This includes advanced Finisher replacements, assuming we still do that. | Solution scope and criteria | — | Workflows that depend on hardware delivery by us |

## 6. Requirements in Draft for more than 14 days

35 of 38 drafts this phase (92 requirements in all).

| ID | Title | MoSCoW | Raised on | Owner | Scope |
|---|---|---|---|---|---|
| REQ-025 | Counter bay selection is based on Depot, speed, diversity and bay count | — | 2026-06-11 | — | Bay allocation |
| REQ-026 | External Reel identifiers record both System Name and Service Id | — | 2026-06-11 | — | Identifier and Reel management |
| REQ-001 | The Loom service pattern model is authoritative for the Ribbon service data model | — | 2026-07-16 | — | CarrierRibbon |
| REQ-002 | ZoneType is provided on the Ribbon order by the Shopfront | — | 2026-07-16 | — | CarrierRibbon |
| REQ-003 | Ribbon connect provisioning waits for the clabel from supply design | — | 2026-07-16 | — | CarrierRibbon |
| REQ-004 | The Shopfront prevents orphaned supply services after a Ribbon cancellation | — | 2026-07-16 | — | CarrierRibbon |
| REQ-005 | Gauging rates are validated against physical fitting capacity | — | 2026-07-16 | — | CarrierRibbon |
| REQ-006 | Per-endpoint Reel translation with push, pop and swap for fold-in-fold | — | 2026-07-16 | — | CarrierRibbon |
| REQ-007 | The next available Counter Reel is selected when the order supplies none | — | 2026-07-16 | — | CarrierRibbon |
| REQ-008 | Ribbon Reel ids are range-checked and rejected if already allocated on the Counter | — | 2026-07-16 | — | CarrierRibbon |
| REQ-009 | A manual connect step holds machine configuration until threading is confirmed | — | 2026-07-16 | — | CustomerCounter |
| REQ-011 | Customer Counters bulk-import from legacy via a versioned CSV with per-row validation | — | 2026-07-16 | — | CustomerCounter |
| REQ-013 | Bay to machine to DEPOT hierarchy is enforced and validated at provisioning | — | 2026-07-16 | — | CustomerCounter |
| REQ-014 | All Bundle member bays run at the same speed for symmetric failover | — | 2026-07-16 | — | CustomerCounter |
| REQ-015 | The Counter is a GDA638 service with a GDA633 specification, ordered via GDA641 | — | 2026-07-16 | — | CustomerCounter |
| REQ-016 | The Counter is a Spindle Loom service package rendering bay, Bundle and subfitting config | — | 2026-07-16 | — | CustomerCounter |
| REQ-017 | A queryable bay allocation audit log, reachable without external log aggregation | — | 2026-07-16 | — | CustomerCounter |
| REQ-018 | Redundancy type changes between active-active and active-passive without termination | — | 2026-07-16 | — | CustomerCounter |
| REQ-019 | Bays are added and removed subject to speed symmetry and diversity validity | — | 2026-07-16 | — | CustomerCounter |
| REQ-020 | Automatic best-fit Counter bay selection against diversity, DEPOT and speed | — | 2026-07-16 | — | CustomerCounter |
| REQ-021 | A manual bay selection workflow constrained to validated capability and diversity | — | 2026-07-16 | — | CustomerCounter |
| REQ-022 | Legacy Reel operations divert to Bobbin per-Counter without a bulk cutover | — | 2026-07-16 | — | CustomerCounter |
| REQ-023 | Number allocation rejects a Reel that conflicts on that Counter | — | 2026-07-16 | — | CustomerCounter |
| REQ-033 | Support for service migrations to new Bolts | Could | — | — | MillhouseG4Supply |
| REQ-034 | Support transfer reversal for services incorrectly switched away | Must | — | — | MillhouseG4Supply |
| REQ-041 | GDA640 SubscriberDispatch support for workshop ops to make configuration changes to services | Should | — | — | SubscriberTrimming |
| REQ-042 | GDA640 Ribbon support for workshop ops to make configuration changes to services | Should | — | — | CarrierRibbon |
| REQ-043 | GDA640 Customer Counter support for workshop ops to make configuration changes to services | Should | — | — | CustomerCounter |
| REQ-050 | Support for disabling a service as a privileged order with permission control | — | — | — | SubscriberTrimming |
| REQ-051 | Must have a way of completing orders that lack automation rules and drop to fallout (e.g. Finisher capacity exceeded) | — | — | — | Fallout and intervention |
| REQ-052 | Manually change a service configuration and re-sync | — | — | — | Fallout and intervention |
| REQ-053 | Support for GDA674 GeographicSite for Shopfront calls to read site information | — | — | — | Order handling |
| REQ-075 | Bobbin Discovery | Won't | — | — | Bobbin service and resource model |
| REQ-076 | Connect: Transfer Service from other Supplier (Defection) | Won't | — | — | MillhouseG4Supply |
| REQ-079 | Modify: Change Bench Finisher | Won't | — | — | MillhouseG4Supply |

## Shopfront impact list

Queryable per the 2026-09-07 ruling: filter the Open items register's Links column on Shopfront impact. These are the items whose impact the Shopfront design phase must absorb.

| ID | Title | Owner | Scope | Shopfront destination |
|---|---|---|---|---|
| OI-021 | Shopfront-side realisation of the fallout / jeopardy queue hat is unconfirmed | — | Fallout and intervention | BR-002 |
| OI-026 | No Backroom validation prevents orphaned supply services after cancellation | — | Fallout and intervention | BR-012 |
| OI-054 | Shopfront operations / service delivery actor roles to confirm | — | SubscriberTrimming | BR-016 |
