# LinkedIn policy and limits

_Last checked: November 2026. LinkedIn changes these without notice — re-check before relying on them._

## Policy

- LinkedIn's User Agreement (section 8.2) and the help page "Prohibited software and extensions" prohibit third-party software that scrapes LinkedIn, or that automates activity such as connecting, messaging, commenting or posting. Members using such tools risk restriction or permanent shutdown of their account. The rule applies to the member using the tool, not only to the tool's maker.
- Posting to your **own personal profile** through the official API is self-serve: the "Share on LinkedIn" product with scope `w_member_social`.
- Posting to a **Company Page** (Community Management API) and **messaging** APIs require LinkedIn partner approval.
- LinkedIn has no scheduling API.

## Commonly observed limits (not official)

| Limit                  | Observed value                                            | Mulaqat's safe setting                                            |
| ---------------------- | --------------------------------------------------------- | ----------------------------------------------------------------- |
| Connection requests    | ~100 per rolling 7 days (some high-SSI accounts get more) | ≤80/week, ≤20/day; 20–30/week for accounts under ~500 connections |
| Connection note length | 300 characters (some mobile versions ~200)                | ≤200                                                              |
| Pending invitations    | ~1,500 before sending is blocked                          | Withdraw invites pending > 21 days                                |
| Weekly window          | Rolling, resets 7 days after each request                 | Tracker counts the last 7 days                                    |

## Sources

- LinkedIn Help — Prohibited software and extensions: https://www.linkedin.com/help/linkedin/answer/a1341387
- Microsoft Learn — Getting access to LinkedIn APIs: https://learn.microsoft.com/en-us/linkedin/shared/authentication/getting-access
- Salesforge — LinkedIn connection request limit in 2026: https://www.salesforge.ai/blog/linkedin-connection-request-limit
- FirstSales — LinkedIn connection request limits in 2026: https://firstsales.io/blog/linkedin-connection-request-limits-2026/
- Overloop — LinkedIn outreach limits & safety, 2026: https://overloop.com/blog/linkedin-limits
