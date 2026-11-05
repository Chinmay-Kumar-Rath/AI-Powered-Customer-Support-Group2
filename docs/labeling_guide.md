<!-- # Severity Labeling Guide

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

Have two reviewers independently label a sample of 100 tickets. Compare their labels, document disagreements, and resolve them using this guide before using the labels for model training or evaluation. -->
# Severity Labeling Guide

## Purpose

This guide defines consistent severity labels for customer support tickets. It helps reviewers assign severity based on the actual business impact of an issue, rather than relying only on words used in the ticket.

## Severity Levels

| Severity | Definition | Examples (3 each) |
|---|---|---|
| Critical | Widespread outage, major business system unavailable, confirmed serious security incident, or major data loss. | 1. The production system is down for all users. 2. A confirmed ransomware attack affects company systems. 3. Major data loss prevents essential business operations. |
| High | An important service or business activity is seriously disrupted, affecting multiple users or a team. | 1. An entire team cannot access its required system. 2. A network outage prevents several employees from working. 3. An important business application is unavailable to multiple users, while other essential services remain operational. |
| Medium | A user's work is affected, but the issue is limited or a reasonable workaround exists. | 1. One user cannot access an application. 2. A user's VPN connection fails, but an approved alternative is available. 3. An application runs slowly for one employee. |
| Low | A minor inconvenience, routine request, or cosmetic issue has little business impact. | 1. A user requests installation of approved software. 2. An employee asks how to change an email signature. 3. A minor display issue does not affect application functionality. |

## Labeling Rules

1. Consider business impact, the number of affected users, and the availability of a workaround.
2. Do not assign severity based only on words such as "urgent", "important", "high", or "critical".
3. A security-related ticket is not automatically Critical. Assess the actual impact, scope, and risk.
4. If the impact is unclear, mark the ticket for human review instead of assuming its severity.
5. Use the same definitions consistently across all tickets.
6. Do not assign Critical severity solely because a ticket mentions a production system, security, or an outage. Evaluate the actual impact described.
7. If a ticket contains conflicting information or insufficient evidence, request clarification or human review.

## Priority Mapping

| Severity | Priority |
|---|---|
| Critical | P1 |
| High | P2 |
| Medium | P3 |
| Low | P4 |

Severity describes the impact of the issue. Priority describes how urgently the ticket should be handled.

The default mapping is Critical to P1, High to P2, Medium to P3, and Low to P4. Any department-based priority adjustments must be documented, approved, and applied consistently.

## Quality Review

1. Select a sample of 100 tickets for severity review.
2. Have two reviewers independently label the same tickets using this guide.
3. Compare their labels and document disagreements.
4. Discuss disagreements and resolve them using the definitions and examples in this guide.
5. Record the agreed labels before using the reviewed data for model training or evaluation.
6. Do not report reviewer agreement or model accuracy until the relevant comparisons and evaluations have actually been completed.
7. Distinguish informational requests from active incidents. A request for security advice, documentation, or general information is not automatically a security incident. For reported incidents, assess whether the threat is active, the data or services affected, the scope of exposure, and the actual business impact. If the evidence is insufficient, request human review.
## Important Note

The examples in this guide are illustrative. Reviewers must consider the context and actual impact of each ticket. A severity label should not be inferred from keywords alone. Tickets with unclear impact should be referred for human review.

## Department-Based Priority Escalation

For tickets assigned to the IT or Finance department, move the default priority up by one level:

| Default Priority | Escalated Priority |
|---|---|
| P4 | P3 |
| P3 | P2 |
| P2 | P1 |
| P1 | P1 |

Apply this adjustment only when severity is known. Tickets with unknown severity must be flagged for human review rather than automatically escalated. Apply the rule consistently and document any approved changes.
