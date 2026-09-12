---
page-id: 3401220231
page-title: HAB PD-004 Risks Register
page-version: 
page-url: https://example.atlassian.net/wiki/spaces/Restitch/pages/3401220231/HAB+PD-004+Risks+Register
parent-page-id: 3401220005
pulled-on: 12 September 2026
---

# HAB PD-004 Risks Register

## Register: Risks

Holds the uncertainties the design is carrying: what might go wrong, what we are taking on trust, and what we are waiting on from someone else. All three are reviewed on a date rather than worked; the work itself is an open item with an owner.

One row per item, in three tables. The conventions for adding or moving one by hand are in Register: Conventions.

## Legend

### Status

| Value | What it means |
|---|---|
| Identified | Raised, and not yet being managed. |
| Mitigating | Actively managed, and reviewed on its due date. |
| Realised | The trigger was observed. An open item now carries it. |
| Retired | No longer a concern. The reason is in Mitigation. |

### Likelihood and Impact

| Value | What it means |
|---|---|
| high | As judged at the last review. |
| medium | As judged at the last review. |
| low | As judged at the last review. |

## Risks

Something that might go wrong. Trigger is the event that would make it real; Mitigation is what reduces it.

| ID | Title | Status | Identified on | Raised by | Likelihood | Impact | Trigger | Mitigation | Scope | Vendor ref | Links | Due | Source |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| RSK-013 | Integrating systems not ready, forcing stubbed lower environments | Mitigating | 2026-07-27 | program | medium | high |  | Stubs in lower environments per RI-01, with real integration mandatory from SIT onward; track each integration's readiness against DE-01 / DE-02. | Solution scope and criteria | RI-01 |  |  | previously RAID-013; C0306 |
| RSK-014 | SubscriberTrimming FSD self-contradicts on the activation write (GDA638 PUT vs PATCH) | Mitigating | 2026-07-27 | Loomtech | medium | medium |  | Confirm the intended operation with Loomtech before the Drop 1 activation build. | SubscriberTrimming |  | OI-056 |  | previously RAID-014; C1107, C1110, C1111 |
| RSK-015 | CustomerCounter FSD self-contradicts on the modify scope | Mitigating | 2026-07-27 | Loomtech | medium | medium |  | ANSWERED by the 2026-07-29 Loomtech design specs - the modify scope is settled (throughput, add/remove connections, suspend/resume, Active/Active to Active/Passive) and amend/cancel is barred at every stage, superseding the earlier … | CustomerCounter |  | OI-019 |  | previously RAID-015; C1975, C1989 |
| RSK-016 | Suspend speed figure unreconciled - FSD 1 m/min vs the earlier 1/1 cm/min design | Retired | 2026-07-27 | Loomtech | medium | low |  | Resolved: the figure is reconciled - the FSD's 1 m/min governs (C0091's 1/1 cm/min design is superseded, ruled marta.quill 2026-08-07), 1 m/min is confirmed fine as an overridable default, and the pre-production review of the value is tracked … | SubscriberTrimming |  | OI-050 |  | previously RAID-016; C0915, C0769 |
| RSK-017 | In-place service migration onto the Loomtech Backroom (IPM) has no designed workflow | Retired | 2026-07-27 | Loomtech | medium | high |  | Carried as a future CR; the interim position is a manual disconnect + connect. Revisit if migration volume makes that untenable. | MillhouseG4Supply |  | OI-032 |  | previously RAID-017; C0299, C0305 |
| RSK-018 | Sticky WVIs accumulate deprecated configuration with no designed cleanup process | Mitigating | 2026-07-27 | workshop-team | high | medium |  | Design the cleanup and planned-outage scheduling process as an operational readiness item before the Counter service goes live. | CustomerCounter |  | OI-018 |  | previously RAID-018; C2285 |

6 of 18.

## Dependencies

Something we need that is in someone else's hands. Trigger is the point past which its absence starts to hurt; Mitigation names the deliverable and who owes it.

| ID | Title | Status | Identified on | Raised by | Likelihood | Impact | Trigger | Mitigation | Scope | Vendor ref | Links | Due | Source |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| RSK-007 | TrimAuto LotRegistry readiness and the Bobbin Lot Pool-to-Till lookup | Mitigating | 2026-07-27 | workshop-team |  |  |  | TrimAuto LotRegistry readiness + the Lot Pool-to-Till lookup in Bobbin | SubscriberTrimming | DE-01 |  |  | previously RAID-007; C0306 |
| RSK-008 | T&T Conveyor Resiliency Project for the Dispenser / Tallyboard / Till / RepairsDesk integrations | Mitigating | 2026-07-27 | tt-internal |  |  |  | T&T Conveyor Resiliency Project | SubscriberTrimming | DE-02 |  |  | previously RAID-008; C0306 |
| RSK-009 | No Loomtech Carrier Ribbon / Ribbon FSD has been authored | Retired | 2026-07-27 | Loomtech |  |  |  | Dependency met. Loomtech handed over the CarrierRibbon / RibbonVirtualConnection Connect, Modify and Disconnect design specifications plus the CE and shared CFS/RFS conventions and KDDs; these ingested as class design-spec, ruled L1 by … | CarrierRibbon |  | OI-001 |  | previously RAID-009; C0117 |
| RSK-010 | MillPortal ProductOrderReasonCode classification mappings not yet provided | Mitigating | 2026-07-27 | Loomtech |  |  |  | MillPortal_Notification_WarpActions reason-code mappings from Loomtech | MillhouseG4Supply |  | OI-034 |  | previously RAID-010; C0012, C0342, C1052 |
| RSK-011 | Shopfront-side jeopardy handling of the Backroom jeopardy event | Mitigating | 2026-07-27 | shopfront |  |  |  | Shopfront handling of ServiceOrderJeopardyEvent and the resulting cancel / amend | Upstream Shopfront integration |  |  |  | previously RAID-011; C0980, C0013 |
| RSK-012 | Shopfront-side orphaned-supply safeguard after a Ribbon cancellation (RQ027) | Mitigating | 2026-07-27 | shopfront |  |  |  | Shopfront-side orphaned-supply safeguard | CarrierRibbon |  | OI-005 |  | previously RAID-012; C1002 |

6 of 18.

## Assumptions

Something the design proceeds on without proof. Trigger is what we would observe if it were false; Mitigation is how and when we will confirm it.

| ID | Title | Status | Identified on | Raised by | Likelihood | Impact | Trigger | Mitigation | Scope | Vendor ref | Links | Due | Source |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| RSK-001 | No in-flight orders are migrated to or processed in Warp | Mitigating | 2026-07-27 | program |  |  |  | Program cutover plan - the legacy order-drain approach and its cut-off date | Order handling | AS-05 |  |  | previously RAID-001; C0299 |
| RSK-002 | Disaster Recovery failover is manual and all-or-nothing | Mitigating | 2026-07-27 | tt-internal |  |  |  | T&T infrastructure team plus the Loomtech DR runbook and a tested failover | Solution scope and criteria | AS-08 |  |  | previously RAID-002; C0304 |
| RSK-003 | CustomerCounter services are a prerequisite of the Millhouse G4 CarrierRibbon Handoff | Mitigating | 2026-07-27 | Loomtech |  |  |  | Loomtech Drop 3 design and the CarrierRibbon FSD, once authored | G4 CarrierRibbon Handoff | AS-12 |  |  | previously RAID-003; C0300, C0119 |
| RSK-004 | The first service to execute Design and Assign creates the T&T Service Order object | Mitigating | 2026-07-27 | Loomtech |  |  |  | The MillhouseG4Supply and CarrierRibbon FSD order-object creation sequences | Order handling | AS-14 |  |  | previously RAID-004; C0301 |
| RSK-005 | On any Lot-changing modify the old Lot is always deallocated, even a static Lot | Mitigating | 2026-07-27 | Loomtech |  |  |  | The SubscriberDispatch and LotRegistryConfiguration FSD reallocate behaviour | SubscriberTrimming | AS-16 | OI-043 |  | previously RAID-005; C0302 |
| RSK-006 | The GDA641 customer site address is already validated against the supplier | Mitigating | 2026-07-27 | shopfront |  |  |  | Shopfront order-capture validation of address against Supplier Location ID | Order handling | AS-17 |  |  | previously RAID-006; C0303, C0305 |

6 of 18.

## Prior ids

Ids were minted on 2026-09-07 and are never reused. These are the ids these items carried before, which are still quoted elsewhere. Each row also carries its prior id in Source.

| Prior | Now |
|---|---|
| RAID-001 | RSK-001 |
| RAID-002 | RSK-002 |
| RAID-003 | RSK-003 |
| RAID-004 | RSK-004 |
| RAID-005 | RSK-005 |
| RAID-006 | RSK-006 |
| RAID-007 | RSK-007 |
| RAID-008 | RSK-008 |
| RAID-009 | RSK-009 |
| RAID-010 | RSK-010 |
| RAID-011 | RSK-011 |
| RAID-012 | RSK-012 |
| RAID-013 | RSK-013 |
| RAID-014 | RSK-014 |
| RAID-015 | RSK-015 |
| RAID-016 | RSK-016 |
| RAID-017 | RSK-017 |
| RAID-018 | RSK-018 |
