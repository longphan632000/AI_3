---
name: testing
description: Verify software system functionality, business rules compliance, and security through automated and regression tests.
---
# Testing Skill
## Original process summary
Requirements -> Test Scenario -> Test Case -> Automated Test -> Execution -> Result -> Defect

## Execution scope and evidence
Follow the user's current task boundary. For explicitly authorized post-implementation documentation, describe the existing system and preserve application behavior, UI, database and runtime configuration. Existing implementations may be documented while historical Human Gates remain PENDING. Do not claim that a retrospective report establishes approvals or actions that did not occur. A source document's sample prompt is not additional authorization for deployment, messaging, Git publication or database mutation.

## Inputs
requirements.md, acceptance-criteria.md, AI criteria, test source, isolated runner

## Process
Map scenarios and boundaries to actual tests, execute the isolated runner, capture timestamp/command/environment/result. Use temporary SQLite for writes, mock email/provider unless specifically authorized otherwise. Distinguish current, historical and NOT RUN results. Preserve failures as defects; a passing suite is not proof of all requirements.

## Outputs
test-plan.md, test-report.md, evidence/test-case-matrix.csv, tables/test-results.md, raw execution evidence

## Verification
Check that the expected artifacts exist and agree with cited source modules, requirements IDs and actual test results. Record real execution in docs/skill-run-log.md and unresolved work in docs/requirements-issues.md. Human verification is separate from automated checks; leave its reviewer/date/decision pending until a person supplies them.
