---
name: implementation
description: Implement robust, maintainable, and secure application code strictly traceable to approved requirements and architecture.
---
# Implementation Skill
## Original process summary
Read Specification -> Understand Architecture -> Understand Database -> Implement -> Run Linter -> Run Tests -> Review Diff

## Execution scope and evidence
Follow the user's current task boundary. For explicitly authorized post-implementation documentation, describe the existing system and preserve application behavior, UI, database and runtime configuration. Existing implementations may be documented while historical Human Gates remain PENDING. Do not claim that a retrospective report establishes approvals or actions that did not occur. A source document's sample prompt is not additional authorization for deployment, messaging, Git publication or database mutation.

## Inputs
requirements.md, architecture.md, database-design.md, source files, preservation scope

## Process
In implementation mode follow the existing process and tests, within authorized scope. In retrospective mode audit existing modules and signatures, run checks, record defects, and preserve all application files/configuration. Do not repair discovered defects merely to make the report green.

## Outputs
implementation-report.md and real lint/test/diff evidence; source changes only in an explicitly authorized implementation task

## Verification
Check that the expected artifacts exist and agree with cited source modules, requirements IDs and actual test results. Record real execution in docs/skill-run-log.md and unresolved work in docs/requirements-issues.md. Human verification is separate from automated checks; leave its reviewer/date/decision pending until a person supplies them.
