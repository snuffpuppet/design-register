---
page-id: 3401220457
page-title: HAB PD-004 Scope Taxonomy
page-version: 
page-url: https://example.atlassian.net/wiki/spaces/Restitch/pages/3401220457/HAB+PD-004+Scope+Taxonomy
parent-page-id: 3401220005
pulled-on: 12 September 2026
---

# HAB PD-004 Scope Taxonomy

## Register: Scope taxonomy

The allowed values for the Scope column on every register. Each item is labelled once, at the lowest level that applies. An integration issue between two technical services is labelled at the customer-service level. There is no programme level: the registers live inside the programme's area, so the programme is implied.

Services delivered this phase MillhouseG4Supply technical service (supply) SubscriberTrimming technical service (delivery) CarrierRibbon technical service (delivery, Ribbon) CustomerCounter technical service (supply / handover) G4 Trimming customer service = MillhouseG4Supply + SubscriberTrimming G4 CarrierRibbon Handoff customer service = MillhouseG4Supply + CarrierRibbon + CustomerCounter Cross-service design Service model Order handling Fallout and intervention Upstream Shopfront integration Inventory and resources Bobbin service and resource model Identifier and Reel management Bay allocation Solution scope and criteria

The four technical services and their two compositions come from the solution scope itself: the supported services were updated to four by CR1 (SR_WARP_01), and CustomerCounter is a prerequisite of the Millhouse G4 CarrierRibbon Handoff service.

## Items per scope value

| Scope | REQ | DEC | LIM | RSK | OI | CR | Total |
|---|---|---|---|---|---|---|---|
| CarrierRibbon | 12 | 3 | 7 | 2 | 13 | 3 | 40 |
| CustomerCounter | 23 | 5 | 8 | 2 | 12 | 4 | 54 |
| Fallout and intervention | 3 | 2 | 0 | 0 | 9 | 2 | 16 |
| Identifier and Reel management | 1 | 4 | 0 | 0 | 0 | 0 | 5 |
| MillhouseG4Supply | 24 | 7 | 3 | 2 | 15 | 9 | 60 |
| Upstream Shopfront integration | 1 | 5 | 0 | 1 | 0 | 1 | 8 |
| Order handling | 4 | 2 | 0 | 3 | 1 | 2 | 12 |
| Bay allocation | 1 | 2 | 0 | 0 | 0 | 0 | 3 |
| Service model | 0 | 5 | 0 | 0 | 0 | 0 | 5 |
| Solution scope and criteria | 5 | 12 | 0 | 2 | 1 | 3 | 23 |
| SubscriberTrimming | 13 | 9 | 1 | 5 | 24 | 12 | 64 |
| G4 CarrierRibbon Handoff | 1 | 0 | 0 | 1 | 0 | 1 | 3 |
| Bobbin service and resource model | 4 | 2 | 0 | 0 | 0 | 1 | 7 |

A scope value carrying no items is still allowed: G4 Trimming has none because no candidate was judged to be an integration issue between MillhouseG4Supply and SubscriberTrimming specifically. Open items keep the service their previous id encoded, which is why the four service values dominate that register.
