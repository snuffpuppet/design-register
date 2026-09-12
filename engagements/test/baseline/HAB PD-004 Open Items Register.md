---
page-id: 3401220796
page-title: HAB PD-004 Open Items Register
page-version: 
page-url: https://example.atlassian.net/wiki/spaces/Restitch/pages/3401220796/HAB+PD-004+Open+Items+Register
parent-page-id: 3401220005
pulled-on: 12 September 2026
---

# HAB PD-004 Open Items Register

## Register: Open items

Holds the working queue: everything someone must do before a record can change.

One row per item. The conventions for adding or moving one by hand are in Register: Conventions.

This register is the working queue. Everything else is a record. An open item closes only by creating or changing a record, and the id it produced goes in Resolution.

## Legend

### Status

| Value | What it means |
|---|---|
| Open | Raised, not yet started. |
| In progress | Someone is working it. |
| Blocked | Waiting on what is named in Blocked by. |
| Closed | Done. What it produced is in Resolution. |

## Open items

| ID | Title | Status | Owner | Scope | Raised on | Raised by | Blocked by | Vendor ref | Links | Resolution | Next action | Due | Closed on |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| OI-001 | No Loomtech Carrier Ribbon / Ribbon FSD authored yet | Closed | Vendor | CarrierRibbon | 2026-07-19 | PD-004 CarrierRibbon parent page |  |  |  | CLOSED 2026-07-31. Loomtech (Nadia Frost) handed over three CarrierRibbon / RibbonVirtualConnection design specifications on 2026-07-29 - Connect (Create) v1.13, Modify v1 and … |  |  | 2026-07-31 |
| OI-002 | GDA638 endpoint representation does not match RQ018's requested shape | Open | Vendor | CarrierRibbon | 2026-07-19 | PD-004 CarrierRibbon parent page |  |  |  |  | RQ018 asks for each Ribbon endpoint to be modelled as a service relationship or embedded characteristic on the parent GDA638 service, preserving the … |  |  |
| OI-003 | Run-id audit query shape and storage (RQ024/RQ025) unspecified | Open | Vendor | CarrierRibbon | 2026-07-19 | HAB PD-004.7.4-operational-items |  |  |  | ? | Confirm how the Ribbon run-id audit trail is realised in Bobbin / Warp / Loom - the query shape, and where the audit record is held. |  |  |
| OI-004 | Downstream Software Architecture (SE SA-xxx) build target for the Ribbon service | Closed |  | CarrierRibbon | 2026-07-19 | PD-004 CarrierRibbon parent page |  |  |  | RESOLVED 2026-07-31 by reading the live page. Its own Software Design section names SE SA-005 - New Build: Ribbon Loom Service, which the refreshed Downstream Software … |  |  | 2026-07-31 |
| OI-005 | Shopfront-side orphaned-supply safeguard (RQ027), and no terminate-time guard on MillhouseG4Supply | Open |  | CarrierRibbon | 2026-07-19 | HAB PD-004.7.3-disconnect |  |  |  | ? | Confirm with Loomtech whether the absent terminate-time orphaned-supply guard on MillhouseG4Supply is deliberate, CustomerCounter carrying the reciprocal guard. (The … |  |  |
| OI-006 | Fallout is out of scope of the design specs, and the Fail path contradicts point-of-no-return | Open | Vendor | CarrierRibbon | 2026-07-31 | PD-004 CarrierRibbon parent page |  |  |  |  | Confirm or replace the CarrierRibbon fallout profile, and rule the contradiction between the framework's Fail path ending in a Shopfront cancellation request and … |  |  |
| OI-007 | GDA685 payload convention not settled, so no pool-draw or release payload is specified | Open | Vendor | CarrierRibbon | 2026-07-31 | C1881 |  |  |  | ? | Confirm the GDA685 payload convention so the CREEL and tapeId pool-draw and release request bodies can be stated. |  |  |
| OI-008 | Whether runId and the RB- / RBEP- naming convention remain in scope | Closed | Vendor | CarrierRibbon | 2026-07-31 | C2186 |  |  |  | RESOLVED 2026-09-08 by the corpus. The question was whether runId and the RB-/RBEP- naming convention remain in scope, and the answer is that they do not: C0983 and C0984 (the … |  |  | 2026-09-08 |
| OI-009 | Limiter override values are illustrative, and the fractional ebs rounding is assumed | Open | Vendor | CarrierRibbon | 2026-07-31 | C1847 |  |  |  | This is a production readiness item. | Supply the agreed per-endpoint limiter override table, and confirm the rounding rule for a fractional ebs. | before the Carrier Ribbon build |  |
| OI-010 | Principle P001 (supply-agnostic delivery) is not satisfied by the delivered scope | Open |  | CarrierRibbon | 2026-07-31 | PD-004 CarrierRibbon parent page |  |  |  |  | Decide whether principle P001 (a Ribbon delivery must be supply agnostic, allowing arbitrary supplies to be connected) is restated as forward-looking, scoped … |  |  |
| OI-011 | RQ022 fitting-capacity validation of the gauging rate is L4-only, not restated at L1 | Open | Vendor | CarrierRibbon | 2026-07-31 | PD-004 CarrierRibbon parent page |  |  |  |  | Confirm the RQ022 fitting-capacity validation of the gauging rate exists in the implemented design, the L1 specifications bounding only the orderable enum … |  |  |
| OI-012 | Counter machine migration and single<->bundle layout change have no designed workflow | Open | Vendor | CustomerCounter | 2026-07-19 | HAB PD-004.8.5-migration |  |  |  |  | Supply the designed workflow for an Counter layout change (adding or removing a strand, changing bundling mode) and the resulting customer service migrations … |  |  |
| OI-013 | Customer engagement and outage coordination for Counter layout migrations | Open | Vendor | CustomerCounter | 2026-07-19 | HAB PD-004.8.5-migration |  |  |  |  | Confirm how customer impact and the outage are handled during an Counter layout-change migration from a workflow perspective - is an extra manual process … |  |  |
| OI-014 | Bobbin Number Management storage of 10-byte octal-string WSI values | Closed | Vendor | CustomerCounter | 2026-07-19 | PD-004 CustomerCounter parent page |  |  |  | RESOLVED 2026-08-06 via live page edit: Loomtech confirmed (Bert) that Bobbin Number Management can store the 10-byte octal-string WSI values in its identifier pools. |  |  | 2026-08-06 |
| OI-015 | Effect of customer-labelled legacy Millhouse services on Depot handoffs | Open | Vendor: Nadia Frost | CustomerCounter | 2026-07-19 | PD-004 CustomerCounter parent page |  |  |  |  | Follow up legacy Bench labelling with Nadia Frost |  |  |
| OI-016 | Bay-allocation audit log mechanism (RQ024/RQ025) unspecified | Open | Vendor | CustomerCounter | 2026-07-19 | PD-004 CustomerCounter parent page |  |  |  |  | Confirm how the RQ024 / RQ025 bay-allocation audit log is realised in Bobbin / Warp - where it is held, and the query shape. |  |  |
| OI-017 | T&W Customer Counters unsupported by the migration automation | Open |  | CustomerCounter | 2026-07-19 | HAB PD-004.8.5-migration |  |  |  |  |  | before the Bobbin Counter migration batches are planned |  |
| OI-018 | Sticky-WVI cleanup under planned outages needs an operational process | Open |  | CustomerCounter | 2026-07-19 | PD-004 CustomerCounter parent page |  |  |  |  |  | pre-go-live - the process must exist before the first planned-outage cleanup |  |
| OI-019 | CustomerCounter FSD self-contradicts on the modify scope | Closed | Vendor | CustomerCounter | 2026-07-25 | HAB PD-004.8.2-modify |  |  |  | CLOSED 2026-07-31. The 2026-07-29 CustomerCounter design specs settle the contradiction and the three claims this item was built on are superseded, so there is nothing left to … |  |  | 2026-07-31 |
| OI-020 | Edge distinctness when both place entries name the same Depot | Open | Vendor | CustomerCounter | 2026-08-19 | C2352 |  |  |  |  | When a redundant CustomerCounter order names the same Depot under both Primary_Depot and Secondary_Depot, does the bay-selection algorithm guarantee the two legs land … |  |  |
| OI-021 | Shopfront-side realisation of the fallout / jeopardy queue hat is unconfirmed | Open |  | Fallout and intervention | 2026-07-31 | PD-004 Fallout and intervention parent page |  |  | Shopfront impact; BR-002 |  |  |  |  |
| OI-022 | Counter bay-selection fallout offers cancel, contradicting the CustomerCounter Retry-only profile | Closed | Marta Quill | Fallout and intervention | 2026-07-31 | PD-004 Fallout and intervention parent page |  |  |  | Ruled marta.quill 2026-08-07 (audit re-visit): C1025 is superseded by C1624/C2012. The CustomerCounter profile governs - manual fallout offers Retry only, and amend / cancel are not … |  |  | 2026-08-07 |
| OI-023 | CarrierRibbon fallout and cancellation handling is not designed | Open | Vendor | Fallout and intervention | 2026-07-31 | PD-004 Fallout and intervention parent page |  |  |  |  | Supply an FSD-level CarrierRibbon fallout profile naming exactly which operator options exist, as the other three services carry. (Service-side view … |  |  |
| OI-024 | No CarrierRibbon_E4_Winder exception-flow diagram exists | Open | Vendor | Fallout and intervention | 2026-07-31 | PD-004 Fallout and intervention parent page |  |  |  |  | Provide the CarrierRibbon_E4_Winder exception-flow diagram the framework routes a Winder feed-management callback failure to, or confirm the route was never … |  |  |
| OI-025 | Reason-code normalisation into the Shopfront contract is semi-deferred and unmapped | Open | Vendor | Fallout and intervention | 2026-07-31 | PD-004 Fallout and intervention parent page |  |  |  |  | Supply the supplier reason-code outcome mappings and their note / jeopardy / error classification, so the Shopfront can know which signal a given supplier failure … |  |  |
| OI-026 | No Backroom validation prevents orphaned supply services after cancellation | Open |  | Fallout and intervention | 2026-07-31 | PD-004 Fallout and intervention parent page |  |  | Shopfront impact; BR-012 |  |  |  |  |
| OI-027 | The per-flow failure-detection layer is not yet in the declared coverage set | Closed |  | Fallout and intervention | 2026-07-31 | PD-004 Fallout and intervention parent page |  |  |  | CLOSED 2026-07-31 (Wave 3). PD-004.11.1 exists, so the detection layer is now IN the declared coverage set: 34 further claims were added to coverage.claims and are represented … |  |  | 2026-07-31 |
| OI-028 | How an operator abandons a Retry-only fallout is unruled | Open | Marta Quill | Fallout and intervention | 2026-07-31 | PD-004 Fallout and intervention parent page |  |  |  |  | Rule whether an operator working a Retry-only fallout task can deliberately route the order onto the jeopardy-and-Shopfront-cancellation path, or whether that path … |  |  |
| OI-029 | Two Millhouse validation failures assert the terminal-rejection path without a claim naming it | Open | Vendor | Fallout and intervention | 2026-07-31 | HAB PD-004.pd-004.11.1-failure-scenarios |  |  |  |  | Confirm which handler each of the two Millhouse validation failures invokes, in which phase, and what the Shopfront receives. |  |  |
| OI-030 | TPI cotton-pair rule and supplyTechnology -> millProduct mapping pending FSD | Open | Vendor | MillhouseG4Supply | 2026-07-17 | HAB PD-004.5.1-connect |  |  |  | MCAS is correct | Confirm the supplyTechnology -> millProduct.productType mapping, and that millProduct MCAS covers the cotton-terminating technologies CTB / CTN / CTC the TPI … |  |  |
| OI-031 | Backroom-emitted ServiceOrderJeopardyEvent on connect fallout vs jeopardy = Shopfront | Closed |  | MillhouseG4Supply | 2026-07-17 | HAB PD-004.5.1-connect |  |  |  | Resolved 2026-07-25 by the MillhouseG4Supply FSD refresh. Approved CR C1052 states the fallout rule for Millhouse rejections/failures of the ProductOfferingQualification and ProductOrder … |  |  |  |
| OI-032 | IPM (service moving to Loomtech from another T&T system) has no designed workflow | Open | Vendor | MillhouseG4Supply | 2026-07-17 | PD-004 MillhouseG4Supply parent page |  |  | resolves into REQ-056 (IPM / in-place service migration, next phase) |  |  |  |  |
| OI-033 | Transfer reversal (undo switch-away) and address retention | Open | Vendor | MillhouseG4Supply | 2026-07-17 | PD-004 MillhouseG4Supply parent page |  |  | resolves into REQ-034 (transfer reversal, ruled day 1 2026-09-07) |  |  |  |  |
| OI-034 | Backroom-handled Millhouse ProductOrderReasonCode classification list not in the corpus | Open | Vendor | MillhouseG4Supply | 2026-07-17 | PD-004 MillhouseG4Supply parent page |  |  |  |  |  | pre-go-live - blocks configuring the Millhouse callback error-code routing |  |
| OI-035 | FRD003 bulk Millhouse location federation / upload not evidenced | Open | Vendor | MillhouseG4Supply | 2026-07-17 | PD-004 MillhouseG4Supply parent page |  |  |  | Millhouse locations are created on demand as orders come in. These are linked to DSAs which are pre-populated in Bobbin | Confirm how Millhouse locations are populated in bulk (pre-seeding or federation) so a GDA641 order can reference a SiteId that already exists. |  |  |
| OI-036 | FRB006 Change SLA enumerated but mechanism unspecified | Open | Vendor | MillhouseG4Supply | 2026-07-17 | PD-004 MillhouseG4Supply parent page |  |  |  |  | Confirm the Millhouse-side change mechanism for Service Restoration SLA on an in-flight service: which productOrder is raised, and whether the Millhouse lifecycle re-runs. |  |  |
| OI-037 | selectBolt target - MLI (validate) vs MILL_PORTAL (add) in the corpus | Closed | Vendor | MillhouseG4Supply | 2026-07-17 | PD-004 MillhouseG4Supply parent page |  |  |  | Resolved 2026-07-20 (marta.quill): not a design conflict but an extraction error. A re-check of the add Process Flow diagram (image-20260630-000554.png) shows step 4 selectBolt … |  |  |  |
| OI-038 | FRB007 Customer Authority Date - no standalone change-CAD modify scenario | Closed | Vendor | MillhouseG4Supply | 2026-07-17 | PD-004 MillhouseG4Supply parent page |  |  |  | Resolved 2026-07-25 by the MillhouseG4Supply FSD refresh: order-supplied only. The FSD now states the modifiable attributes definitively as Service Restoration SLA, Bench Bay, Bolt and … |  |  |  |
| OI-039 | MillhouseG4Supply FSD Modify and Delete sections document no workflows | In progress | Vendor: Nadia Frost | MillhouseG4Supply | 2026-08-06 | PD-004 MillhouseG4Supply parent page |  |  |  |  | Nadia Frost is authoring the Finisher workflows |  |  |
| OI-040 | FRP001 feed-config reset has no solution mechanism | Closed | Vendor | SubscriberTrimming | 2026-07-17 | HAB PD-004.6.5-operational-items |  |  |  | Resolved 2026-07-17 (user L0 C1042): an T&T-authored script or UI performs the reset out-of-band, direct to the Loomtech platform APIs (bypasses Warp, an accepted config-authority … |  |  |  |
| OI-041 | FRP002 disable service has no solution mechanism | Open | Vendor | SubscriberTrimming | 2026-07-17 | HAB PD-004.6.5-operational-items |  |  |  |  | Specify the order pattern and the restoration semantics for the FRP002 police-request disable capability. |  |  |
| OI-042 | Cycle Lot RFS-side sequence unspecified at FSD level | Closed | Vendor | SubscriberTrimming | 2026-07-17 | HAB PD-004.6.4-cycle-lot |  |  |  | Resolved 2026-07-25 by the SubscriberDispatch FSD refresh. cycleLotA / cycleLotB is now one of the six named SubscriberDispatch update scenarios (C1099), invoked as a GDA640 PATCH … |  |  |  |
| OI-043 | Cycle Lot scope - static re-allocation vs the FSD's "dynamic" wording | Open | Vendor | SubscriberTrimming | 2026-07-17 | HAB PD-004.6.4-cycle-lot |  |  |  |  | Confirm which path a STATIC Lot re-allocation rides - cycleLot, lotAllocationFunction or the lots scenario - given the FSD scopes cycleLotA / cycleLotB to a … |  |  |
| OI-044 | modifyBolt downstream RFS flow unspecified | Closed | Vendor | SubscriberTrimming | 2026-07-17 | HAB PD-004.6.2-modify |  |  |  | Resolved 2026-07-25 by the SubscriberDispatch FSD refresh. modifyBolt is one of the six named SubscriberDispatch update scenarios (C1099), invoked as a GDA640 PATCH setting … |  |  |  |
| OI-045 | lots (gauge) downstream RFS flow unspecified | Closed | Vendor | SubscriberTrimming | 2026-07-17 | HAB PD-004.6.2-modify |  |  |  | Resolved 2026-07-25 by the SubscriberDispatch FSD refresh. lots is one of the six named SubscriberDispatch update scenarios (C1099), invoked as a GDA640 PATCH of the lots … |  |  |  |
| OI-046 | SubscriberDispatch update invocation mode presumed synchronous | Closed | Vendor | SubscriberTrimming | 2026-07-17 | HAB PD-004.6.2-modify |  |  |  | RESOLVED 2026-08-06 via live page edit (marta.quill): not an T&T issue - SubscriberDispatch is a Loomtech-internal RFS that Loomtech manages, so the update invocation mode is theirs to … |  |  | 2026-08-06 |
| OI-047 | Disconnect LotRegistry decommission fallout handling presumed | Open | Vendor | SubscriberTrimming | 2026-07-17 | HAB PD-004.6.3-disconnect |  |  |  |  | Confirm the disconnect flow's LotRegistry decommission failure handling mirrors the connect-side HTTP-code rules to MendingBench. |  |  |
| OI-048 | FeedManagement not invoked on delete - feed drop assumption | Closed | Vendor | SubscriberTrimming | 2026-07-17 | HAB PD-004.6.3-disconnect |  |  |  | PROMOTED 2026-08-06 via live page edit (marta.quill): the feed-drop assumption is settled by making explicit feed management on delete a requirement - Loomtech will add it to … |  |  | 2026-08-06 |
| OI-049 | Transfer reversal / re-connect within the LotRegistry quarantine window | Closed | Vendor | SubscriberTrimming | 2026-07-17 | HAB PD-004.6.3-disconnect |  |  |  | Resolved 2026-07-25 by approved CR C1047: the Shopfront can request a specific Lot lot (lotA_if, lotA_fr, lotB_na, lotB_pd) on connect AND modify orders by passing the LotRegistry … |  |  |  |
| OI-050 | Suspend speed figure - FSD 1 m/min vs earlier 1/1 cm/min | Closed | Vendor | SubscriberTrimming | 2026-07-17 | HAB PD-004.6.5-operational-items |  |  |  | RESOLVED 2026-08-06 via live page edit (marta.quill): 1 m/min is fine as the default and can be overridden. The pre-production review of the value is spawned as OI-061. |  |  | 2026-08-06 |
| OI-051 | FRB004 subscriberProtocol modify path not evidenced | Open | Vendor | SubscriberTrimming | 2026-07-17 | PD-004 SubscriberTrimming parent page |  |  |  | This needs to be added as a requirement. Loomtech has taken this as a new piece of work and will be creating a new phase 1 CR to implement this | Confirm the intended subscriberProtocol modify path, given the FSD's definitive six update scenarios exclude it while decision DE014 intends GDA640. |  |  |
| OI-052 | No-inflight-order precondition generalised to all modifies | Open | Vendor | SubscriberTrimming | 2026-07-17 | HAB PD-004.6.2-modify |  |  |  |  | Confirm the no-concurrent-inflight-order precondition applies to every modify scenario, not only disconnect, suspend and the approved concurrent Supply + … |  |  |
| OI-053 | Suspend/Resume page placement (6.5 vs 6.2) | Open |  | SubscriberTrimming | 2026-07-17 | HAB PD-004.6.5-operational-items |  |  |  |  | Confirm the preferred page placement for Suspend / Resume - PD-004.6.5, or PD-004.6.2 since it is mechanically a pure speed change. |  |  |
| OI-054 | Shopfront operations / service delivery actor roles to confirm | Open |  | SubscriberTrimming | 2026-07-17 | PD-004 SubscriberTrimming parent page |  |  | Shopfront impact; BR-016 |  |  |  |  |
| OI-055 | LotRegistry restore-from-quarantine not evidenced (FRB005 / FRB006 / FRB007 / FRB008) | Closed | Vendor | SubscriberTrimming | 2026-07-20 | PD-004 SubscriberTrimming parent page |  |  |  | Resolved 2026-07-25 with OI-049 by approved CR C1047: a specific lot is recovered by passing its LotRegistry allocationId on the connect or modify order while the lot is still … |  |  |  |
| OI-056 | SubscriberTrimming FSD self-contradicts on the activation write (GDA638 PUT vs PATCH) | Open | Vendor | SubscriberTrimming | 2026-07-25 | C1110 |  |  |  |  | Confirm whether the CFS is set active with a GDA638 PUT or a PATCH, the FSD page text and its own process-flow diagram disagreeing. |  |  |
| OI-057 | Dispenser update (reservation-upsert) ASYNC correlation key not stated | Open | Vendor | SubscriberTrimming | 2026-07-25 | C1077 |  |  |  |  | Confirm the ASYNC correlation key for the Dispenser update (reservation-upsert) operation, presumed to be the create form, so the phase-2 callback correlation is … |  |  |
| OI-058 | LotRegistryConfiguration reallocate - a Service Order operation or an internal composite step | Open | Vendor | SubscriberTrimming | 2026-07-25 | C1082 |  |  |  |  |  |  |  |
| OI-059 | WRG failover handling for machine-targeted Winder feed requests | Open |  | SubscriberTrimming | 2026-07-29 | PD-004 SubscriberTrimming parent page |  |  |  | This should now become a requirement and Loomtech will deliver it in phase 1 via a CR to support both legacy Winders (no WRG) and handling both WRG Winders for feed management | Confirm with Workshops how a machine-targeted Winder feed request is handled under an WRG failover - two requests, one per member machine, or a layout-aware … |  |  |
| OI-060 | Non-Millhouse feed-based services requiring feed clearing - scope | Closed |  | SubscriberTrimming | 2026-07-29 | PD-004 SubscriberTrimming parent page |  |  |  | RESOLVED 2026-08-06 via live page edit (marta.quill): Millhouse-related services only are in scope for phase 1, so non-Millhouse feed clearing needs no item. |  |  | 2026-08-06 |
| OI-061 | Review the suspend configuredSpeed default (1 m/min) before production | Open |  | SubscriberTrimming | 2026-08-06 | HAB PD-004.6.5-operational-items |  |  |  |  |  | pre-production |  |
| OI-062 | Some T&W Customer Counters are unsupported by the migration automation and will be delayed | Open |  | CustomerCounter | 2026-07-27 | PD-004 solution RAID register |  |  | the same underlying item as OI-017 |  | Enumerate the unsupported configurations and agree the manual fallback path and its effort with the workshop team. |  |  |
| OI-067 | Decide whether G4 Wholesale includes dedicated customer Bolt use cases | Open |  | MillhouseG4Supply | 2026-09-07 | PD-004 Scope Register Historic Scoping History, SR-004 |  |  | resolves into the DEC-057 decision |  | Convene Ruth Calder, Ines Duarte and Cormac Blythe to choose between a pinned Bolt and a ribbon tunnel for the service |  |  |
| OI-063 | Shared conventions document absent from the handover, and its KDD-6 relationship-merge rule unverifiable | Open | Vendor | CarrierRibbon | 2026-09-07 | sources/backroom/FSD-2026-07-29/CarrierRibbon-RBVC-Connect-Design-Spec_1_ … |  |  |  |  | Two service-agnostic design items moved out of this specification into a shared conventions document that is absent from the handover, and that document's … |  |  |
| OI-064 | CNTB baySpeed presence and CustomerCounter bundleSkein type disagree between the FSD and TTModel v0.72 | Open | Vendor | CustomerCounter | 2026-09-07 | User ruling (marta.quill) 2026-07-28: sweep pair 13 registered as an … |  |  |  |  | Whether the CNTB resource carries baySpeed, and whether CustomerCounter bundleSkein is a boolean or a String, are unresolved: the CustomerCounter FSD v6 places … |  |  |
| OI-065 | Whether GDA645 appointmentRequired must account for HYB Finisher-bay availability | Open | Vendor | MillhouseG4Supply | 2026-09-07 | kb-resolve feed 2026-08-06 (ruling-audit-resolve-2026-08-06) … |  |  |  |  | Whether the GDA645 appointmentRequired answer should account for HYB Finisher-bay availability is unresolved: the GDA645 mapping derives it solely from Millhouse … |  |  |
| OI-066 | Source of the legacy Bench label value — Millhouse order/response or manual entry | Open | Vendor: Nadia Frost | MillhouseG4Supply | 2026-09-07 | sources/backroom/TT-Loomtech-Technical-Sync-Up-20260805.vtt @ 00:47:47 |  |  |  |  | Follow up legacy Bench labelling with Nadia Frost |  |  |
| OI-068 | Validate phase 1 CR prioritisation | Open | Marta Quill | Solution scope and criteria | 2026-09-07 | Marta Quill, solution architect, 2026-09-07 |  |  | REQ-034, REQ-089, REQ-090, OI-069, REQ-091, REQ-092 |  | Meet to discuss phase 1 CR prioritisation |  |  |
| OI-069 | Query Appointment API: confirm delivery timing and priority | Open | Marta Quill | Order handling | 2026-09-07 | Marta Quill, solution architect, 2026-09-07 |  |  |  |  | Establish with Loomtech when the Query Appointment API lands and what priority it carries |  |  |
| OI-070 | Customer Counter change matrix | Open | Marta Quill | CustomerCounter | 2026-09-07 | Marta Quill, solution architect, 2026-09-07 |  |  |  |  | Run the change matrix past Cormac Blythe, then past Nadia Frost |  |  |
| OI-071 | Police requests: temporarily disable a Home or BT&W Subscriber Trimming service using suspension gauges | Open | Marta Quill | SubscriberTrimming | 2026-09-07 | Marta Quill, solution architect, 2026-09-07 |  |  | REQ-050, OI-041 |  | Run the gauging and handoff solution past the team |  |  |
| OI-072 | Police requests: wholesale services punted to the wholesaler | Open | Marta Quill | MillhouseG4Supply | 2026-09-07 | Marta Quill, solution architect, 2026-09-07 |  |  | REQ-050 |  | Establish whether punting the request to the wholesaler is acceptable |  |  |
| OI-073 | Police requests: the T&W Carrier Ribbon approach | Open | Marta Quill | CarrierRibbon | 2026-09-07 | Marta Quill, solution architect, 2026-09-07 |  |  | REQ-050 |  | Decide whether to address this now or defer it |  |  |
| OI-074 | Design Millhouse organisation creation via MillPortal | Open | Marta Quill | MillhouseG4Supply | 2026-09-07 | Marta Quill, solution architect, 2026-09-07 |  |  |  |  | Take the proposed cache-and-create approach through ingest so it becomes design truth, then design it with Loomtech |  |  |
| OI-075 | Dispenser and Tallyboard ingester blacklisting recovery: cancelling or restarting a workflow after a failed task | Open | Vendor | SubscriberTrimming | 2026-09-07 | Marta Quill, solution architect, 2026-09-07 |  |  |  |  | Establish with Loomtech how a workflow is cancelled or restarted when a previous task failed, e.g. LotRegistry bad data causing a Dispenser failure with no way to cancel or edit the data |  |  |

75 items.

## Prior ids

Ids were minted on 2026-09-07 and are never reused. These are the ids these items carried before, which are still quoted on four published Confluence pages and in the registers' own cross-references. This register has no Source column, so the mapping lives here.

| Prior | Now |
|---|---|
| OI:OI-CE-01 | OI-001 |
| OI:OI-CE-02 | OI-002 |
| OI:OI-CE-03 | OI-003 |
| OI:OI-CE-04 | OI-004 |
| OI:OI-CE-05 | OI-005 |
| OI:OI-CE-06 | OI-006 |
| OI:OI-CE-07 | OI-007 |
| OI:OI-CE-08 | OI-008 |
| OI:OI-CE-09 | OI-009 |
| OI:OI-CE-10 | OI-010 |
| OI:OI-CE-11 | OI-011 |
| OI:OI-Counter-01 | OI-012 |
| OI:OI-Counter-02 | OI-013 |
| OI:OI-Counter-03 | OI-014 |
| OI:OI-Counter-04 | OI-015 |
| OI:OI-Counter-05 | OI-016 |
| OI:OI-Counter-06 | OI-017 |
| OI:OI-Counter-07 | OI-018 |
| OI:OI-Counter-08 | OI-019 |
| OI:OI-Counter-09 | OI-020 |
| OI:OI-FI-01 | OI-021 |
| OI:OI-FI-02 | OI-022 |
| OI:OI-FI-03 | OI-023 |
| OI:OI-FI-04 | OI-024 |
| OI:OI-FI-05 | OI-025 |
| OI:OI-FI-06 | OI-026 |
| OI:OI-FI-07 | OI-027 |
| OI:OI-FI-08 | OI-028 |
| OI:OI-FI-09 | OI-029 |
| OI:OI-Millhouse-01 | OI-030 |
| OI:OI-Millhouse-02 | OI-031 |
| OI:OI-Millhouse-03 | OI-032 |
| OI:OI-Millhouse-04 | OI-033 |
| OI:OI-Millhouse-05 | OI-034 |
| OI:OI-Millhouse-06 | OI-035 |
| OI:OI-Millhouse-07 | OI-036 |
| OI:OI-Millhouse-09 | OI-037 |
| OI:OI-Millhouse-08 | OI-038 |
| OI:OI-Millhouse-10 | OI-039 |
| OI:OI-SI-01 | OI-040 |
| OI:OI-SI-02 | OI-041 |
| OI:OI-SI-03 | OI-042 |
| OI:OI-SI-04 | OI-043 |
| OI:OI-SI-05 | OI-044 |
| OI:OI-SI-06 | OI-045 |
| OI:OI-SI-07 | OI-046 |
| OI:OI-SI-08 | OI-047 |
| OI:OI-SI-09 | OI-048 |
| OI:OI-SI-10 | OI-049 |
| OI:OI-SI-11 | OI-050 |
| OI:OI-SI-12 | OI-051 |
| OI:OI-SI-13 | OI-052 |
| OI:OI-SI-14 | OI-053 |
| OI:OI-SI-15 | OI-054 |
| OI:OI-SI-16 | OI-055 |
| OI:OI-SI-17 | OI-056 |
| OI:OI-SI-18 | OI-057 |
| OI:OI-SI-19 | OI-058 |
| OI:OI-SI-20 | OI-059 |
| OI:OI-SI-21 | OI-060 |
| OI:OI-SI-22 | OI-061 |
| OI:OI-RAID-019 | OI-062 |
| OI:OI-SR004 | OI-067 |
| OI:OI-CE-12 | OI-063 |
| OI:OI-Counter-10 | OI-064 |
| OI:OI-Millhouse-11 | OI-065 |
| OI:OI-Millhouse-12 | OI-066 |
| OI:SUP-OI-01 | OI-068 |
| OI:SUP-OI-02 | OI-069 |
| OI:SUP-OI-03 | OI-070 |
| OI:SUP-OI-04 | OI-071 |
| OI:SUP-OI-05 | OI-072 |
| OI:SUP-OI-06 | OI-073 |
| OI:SUP-OI-07 | OI-074 |
| OI:SUP-OI-08 | OI-075 |
