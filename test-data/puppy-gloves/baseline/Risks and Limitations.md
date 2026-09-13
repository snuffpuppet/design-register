---
page-id: 402
page-title: Risks and Limitations
page-version: 3
page-url: https://example.atlassian.net/wiki/pages/402
parent-page-id: 400
pulled-on: 11 September 2026
---

# Risks and Limitations

## Risks

| Ref | Risk | Likelihood | Impact | Mitigation | Owner | Status |
|---|---|---|---|---|---|---|
| RK-1 | Vendor build slips past the day-one date | Medium | High | Weekly delivery review | Adam Moyes | |
| RK-2 | Vendor delivery is late | M | H | | | |
| RK-3 | Manual port assignment volume outgrows the operations team | Low | Medium | Weekly report | Priya Nair | Mitigating |
| RK-4 | Customers may complain about two invoice lines | Low | Low | | | |

## Assumptions

| Ref | Assumption | Confidence | Owner | Basis |
|---|---|---|---|---|
| AS-1 | The billing adapter can merge two service lines at rating time | Medium | Tom Okafor | Stated in billing workshop |
| AS-2 | The vendor test environment mirrors production port limits | Low | | Derived |

## Dependencies

| Ref | Dependency | Needed by | From | Status |
|---|---|---|---|---|
| DP-1 | Vendor delivers the port allocation change | 30 Sep 2026 | Vendor | On track |
| DP-2 | Vendor delivery of port allocation fix | end of September | Martin Vasquez | Open |

## Limitations

| Ref | Limitation | Impact | Confidence | Evidence |
|---|---|---|---|---|
| L-1 | Vendor design assigns one port per order regardless of site count | Split-site orders lose the second site | High | Vendor design review 1 Sep, VND-DR-07 |
| L-2 | Platform holds one notification channel per customer | Cannot send both email and SMS | High | T002 vendor sync |
| L-3 | Platform probably cannot handle more than 4 ports per order | Unknown | Low, inferred | Inferred from VND-DR-07 §3 wording |

## Limitations

| Ref | Limitation | Status | Impact | Options | Chosen option | Owner | Rationale | Links |
|---|---|---|---|---|---|---|---|---|
| LM-1 | One notification channel per customer | Accepted | Email only on day one | 1. Live with it; impact: none; phase: Day one 2. Ask the vendor for SMS; impact: $40k; phase: Later | 1 | Priya Nair | Volume is low and SMS is rarely used | constrains RQ-3 |
| LM-2 | No bulk port assignment | Change requested | Operations cannot port in bulk | 1. Vendor adds bulk port; impact: $20k, 3 weeks; phase: Day one 2. Manual with a report; impact: 2 FTE; phase: Day one | 1 | Tom Okafor | | |
| LM-3 | Invoice shows two lines per bundle | Accepted | Customers see two lines | 1. Build a report to find affected customers and warn them; impact: 2 days; phase: Day one 2. Accept; impact: complaints; phase: Day one | 1 | Priya Nair | | constrains RQ-4 |
