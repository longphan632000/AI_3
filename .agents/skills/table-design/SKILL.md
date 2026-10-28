---
name: table-design
description: Create and refine traceable software engineering tables from approved project artifacts.
---
# Table Design Skill
## Objective
Create structured, consistent and traceable software-engineering tables that can be reviewed by humans and inserted into the final report.
## Supported tables
Actor specification; Use Case summary; detailed Use Case specification; requirements traceability; Class specification; data dictionary; test-case/result matrix; code-review/security finding tables.

## Execution scope and evidence
Follow the user's current task boundary. For explicitly authorized post-implementation documentation, describe the existing system and preserve application behavior, UI, database and runtime configuration. Existing implementations may be documented while historical Human Gates remain PENDING. Do not claim that a retrospective report establishes approvals or actions that did not occur. A source document's sample prompt is not additional authorization for deployment, messaging, Git publication or database mutation.

## Inputs
source-urd.md, relevant requirements/architecture/schema/tests/reviews

## Process
Define consistent columns; preserve original identifiers; include evidence and status. Number basic/alternative steps. Split long tables by domain. Unknown data remains PENDING/NOT RUN; do not fill an expected result as if observed.

## Outputs
tables/actor-specification.md, use-case-summary.md, use-case-specifications.md, requirements-traceability.md, class-specification.md, data-dictionary.md, test-case/results and finding tables

## Verification
Check that the expected artifacts exist and agree with cited source modules, requirements IDs and actual test results. Record real execution in docs/skill-run-log.md and unresolved work in docs/requirements-issues.md. Human verification is separate from automated checks; leave its reviewer/date/decision pending until a person supplies them.
