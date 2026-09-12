---
page-id: 3401221135
page-title: HAB PD-004 Next Phase
page-version: 
page-url: https://example.atlassian.net/wiki/spaces/Restitch/pages/3401221135/HAB+PD-004+Next+Phase
parent-page-id: 3401220005
pulled-on: 12 September 2026
---

# HAB PD-004 Next Phase

## Register: Next phase

Reviewed at phase planning rather than in the weekly meeting. This is the chain from a limitation we are living with to its planned fix.

## Legend

### Status - requirements

| Value | What it means |
|---|---|
| Draft | Stated, not yet agreed. |

### MoSCoW

| Value | What it means |
|---|---|
| Could | Taken if it is cheap. |

### Status - change requests

| Value | What it means |
|---|---|
| Proposed | Ours, and being reasoned. |

## 1. Deferred limitations and their disposition requirement

2.

| ID | Title | Disposition record | Scope | Impact |
|---|---|---|---|---|
| LIM-009 | No manual NamedAuth authentication (customer-supplied credentials) | REQ-059 | SubscriberTrimming | All subscriber feeds use injected auth today; enterprise customers on non-Millhouse/Silkline suppliers need manual NamedAuth auth, planned as CR-05. |
| LIM-019 | Only shared Bolts are supported; dedicated Bolt tenancy is not | REQ-092 | MillhouseG4Supply | Only the shared Bolt pool is available (tenant 1 is the default tenancy, C2222). A wholesale-Cut-only customer needing a dedicated Bolt cannot be delive |

## 2. Requirements with Phase = next phase

20 of 92.

| ID | Title | Status | MoSCoW | Owner | Scope | Source |
|---|---|---|---|---|---|---|
| REQ-055 | Support for Dedicated Bolts | Draft | — | — | MillhouseG4Supply | PD-004 Scope Register (page 3401221474), previously FC001 |
| REQ-056 | Service Migration to Bobbin and Inflight Order Migration to Warp | Draft | — | — | Bobbin service and resource model | PD-004 Scope Register (page 3401221474), previously FC002 |
| REQ-057 | Wide Lot design | Draft | — | — | Solution scope and criteria | PD-004 Scope Register (page 3401221474), previously FC003 |
| REQ-058 | Chart automation and support | Draft | — | — | SubscriberTrimming | PD-004 Scope Register (page 3401221474), previously FC004 |
| REQ-059 | NamedAuth manual auth | Draft | — | — | SubscriberTrimming | PD-004 Scope Register (page 3401221474), previously FC005 |
| REQ-060 | RepairsDesk AssetLedger Integration | Draft | — | — | Solution scope and criteria | PD-004 Scope Register (page 3401221474), previously FC006 |
| REQ-061 | Support for business connect with Millhouse Account Management | Draft | — | — | MillhouseG4Supply | PD-004 Scope Register (page 3401221474), previously FC007 |
| REQ-062 | Role based TradeCounters | Draft | — | — | CustomerCounter | PD-004 Scope Register (page 3401221474), previously FC008 |
| REQ-063 | Future WRG redundancy | Draft | Could | — | SubscriberTrimming | PD-004 Scope Register (page 3401221474), previously FC009 |
| REQ-064 | Order fallout management | Draft | — | — | Fallout and intervention | PD-004 Scope Register (page 3401221474), previously FC010 |
| REQ-065 | Support for TOT process to onboard new wholesale clients from another Reseller | Draft | — | — | CarrierRibbon | PD-004 Scope Register (page 3401221474), previously FC011 |
| REQ-066 | Support for service migrations to new Bolts | Draft | — | — | MillhouseG4Supply | PD-004 Scope Register (page 3401221474), previously FC012 |
| REQ-067 | Support transfer reversal for services incorrectly switched away | Draft | — | — | MillhouseG4Supply | PD-004 Scope Register (page 3401221474), previously FC013 |
| REQ-068 | Support full Finisher / multi-head upgrade workflows as per Pinwheel / Tillbook | Draft | — | — | MillhouseG4Supply | PD-004 Scope Register (page 3401221474), previously FC014 |
| REQ-069 | Full Loom service discovery for service config health visibility | Draft | — | — | Bobbin service and resource model | PD-004 Scope Register (page 3401221474), previously FC015 |
| REQ-070 | Alerting / ticketing for service health discrepancies | Draft | — | — | Bobbin service and resource model | PD-004 Scope Register (page 3401221474), previously FC016 |
| REQ-071 | Customer Counter migration support for machine / redundancy changes | Draft | — | — | CustomerCounter | PD-004 Scope Register (page 3401221474), previously FC017 |
| REQ-072 | GDA640 Millhouse G4 support for workshop ops to make configuration changes to the Millhouse Cut (e.g. change Bolt) | Draft | — | — | MillhouseG4Supply | PD-004 Scope Register (page 3401221474), previously FC018 |
| REQ-073 | Generate LOA document for customer Counter provisioning | Draft | — | — | CustomerCounter | PD-004 Scope Register (page 3401221474), previously FC019 |
| REQ-092 | Bolt tenancy for wholesale-Cut-only services | Draft | — | Marta Quill | MillhouseG4Supply | Marta Quill, solution architect, 2026-09-07; previously SUP-REQ-04 |

## 3. Change requests with Phase = next phase

7 of 38.

| ID | Title | Status | Scope | Vendor ref | Delivers |
|---|---|---|---|---|---|
| CR-027 | Support for Dedicated Bolts | Proposed | MillhouseG4Supply | CR-01 | delivers REQ-055 |
| CR-028 | Service Migration to Bobbin and Inflight Order Migration to Warp | Proposed | Bobbin service and resource model | CR-02 | delivers REQ-056 |
| CR-029 | Wide Lot design | Proposed | Solution scope and criteria | CR-03 | delivers REQ-057 |
| CR-030 | Chart automation and support | Proposed | SubscriberTrimming | CR-04 | delivers REQ-058 |
| CR-031 | NamedAuth manual auth | Proposed | SubscriberTrimming | CR-05 | delivers REQ-059 |
| CR-032 | RepairsDesk AssetLedger Integration | Proposed | Solution scope and criteria |  | delivers REQ-060 |
| CR-033 | Support for business connect with Millhouse Account Management | Proposed | MillhouseG4Supply |  | delivers REQ-061 |

## 4. Open items whose outcome lands in the next phase

Ruled 2026-09-07: post-phase-1 is a delivery phase, so the phase is carried by the record the open item resolves into rather than by the open item itself, which has no Phase field (model section 7).

| ID | Title | Owner | Resolves into |
|---|---|---|---|
| OI-032 | IPM (service moving to Loomtech from another T&T system) has no designed workflow | Vendor | resolves into REQ-056 (IPM / in-place service migration, next phase) |
