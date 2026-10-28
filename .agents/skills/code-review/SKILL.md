---
name: code-review
description: Review implementation against requirements compliance, architectural integrity, correctness, and security.
---
# Code Review Skill
## Checklist
Correctness, Requirements Compliance, Architecture Compliance, Maintainability, Security, Performance, Testing

## Execution scope and evidence
Follow the user's current task boundary. For explicitly authorized post-implementation documentation, describe the existing system and preserve application behavior, UI, database and runtime configuration. Existing implementations may be documented while historical Human Gates remain PENDING. Do not claim that a retrospective report establishes approvals or actions that did not occur. A source document's sample prompt is not additional authorization for deployment, messaging, Git publication or database mutation.

## Inputs
requirements.md, architecture.md, current source, test evidence and diff

## Process
Review correctness, role/project scope, transaction behavior, source-grounded AI, error paths, maintainability and test gaps. Cite file/function/line. Separate reproduced defect, static finding, unresolved requirement and minor lint issue. Document remediation without changing a frozen application.

## Outputs
code-review.md, tables/code-review-findings.md

## Verification
Check that the expected artifacts exist and agree with cited source modules, requirements IDs and actual test results. Record real execution in docs/skill-run-log.md and unresolved work in docs/requirements-issues.md. Human verification is separate from automated checks; leave its reviewer/date/decision pending until a person supplies them.
