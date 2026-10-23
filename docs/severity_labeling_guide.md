# Severity Labeling Guide

## Purpose
This guide defines consistent severity labels for customer support tickets.

## Severity Levels

| Severity | Definition | Example |
|---|---|---|
| Critical | Widespread outage, major business system unavailable, confirmed serious security incident, or major data loss | Production system is down for all users |
| High | Important service or business work is seriously disrupted, affecting multiple users or a team | An entire team cannot access its required system |
| Medium | A user's work is affected, but the issue is limited or a reasonable workaround exists | One user cannot access an application |
| Low | Minor inconvenience, routine request, or cosmetic issue with little business impact | Request to install approved software |

## Labeling Rules

1. Consider business impact, number of affected users, and availability of a workaround.
2. Do not assign severity based only on words such as "urgent", "important", "high", or "critical".
3. A security-related ticket is not automatically Critical; assess the actual impact and risk.
4. If impact is unclear, mark the ticket for human review instead of assuming its severity.
5. Apply the same definitions consistently to all tickets.

## Priority Mapping

| Severity | Priority |
|---|---|
| Critical | P1 |
| High | P2 |
| Medium | P3 |
| Low | P4 |

Severity describes the impact of the issue. Priority describes how urgently the ticket should be handled. Any department-based priority adjustments must be documented and approved separately.

## Quality Review

Have two reviewers independently label a sample of 100 tickets. Compare their labels, document disagreements, and resolve them using this guide before using the labels for model training or evaluation.


## Additional decision rules

- **Security incidents:** Distinguish an attempted attack from confirmed unauthorized access, confirmed data exposure, and a widespread ongoing compromise. Escalate suspected security incidents for appropriate human triage. Do not assign Critical solely because the words "hospital", "breach", "unauthorized", or "medical data" appear.
- **Informational requests:** Requests for security guidance, compliance information, or recommendations without an active incident are not automatically High or Critical.
- **Uncertain impact:** If the text does not establish whether an attack succeeded, how many users or records are affected, or whether a workaround exists, mark the ticket for human review rather than inventing impact.
- **Operational incidents:** Base severity on actual service disruption, affected scope, business impact, and available workarounds—not just urgent wording.
- **Reviewer independence:** Reviewers must label tickets independently before discussing disagreements. Suggested labels must not be treated as reviewer-confirmed labels.
