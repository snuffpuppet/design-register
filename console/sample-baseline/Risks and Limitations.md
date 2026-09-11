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

| Ref | Risk | Likelihood | Impact | Mitigation | Owner |
|---|---|---|---|---|---|
| RK-1 | Vendor build slips past the day-one date | Medium | High | Weekly delivery review | Adam Moyes |
| RK-2 | Vendor delivery is late | M | H | | |
| RK-3 | Manual port assignment volume outgrows the operations team | Low | Medium | Weekly report | Priya Nair |
| RK-4 | Customers may complain about two invoice lines | Low | Low | | |

## Limitations

| Ref | Limitation | Impact | Confidence | Evidence |
|---|---|---|---|---|
| L-1 | Vendor design assigns one port per order regardless of site count | Split-site orders lose the second site | High | Vendor design review 1 Sep, VND-DR-07 |
| L-2 | Platform holds one notification channel per customer | Cannot send both email and SMS | High | T002 vendor sync |
| L-3 | Platform probably cannot handle more than 4 ports per order | Unknown | Low, inferred | Inferred from VND-DR-07 §3 wording |
