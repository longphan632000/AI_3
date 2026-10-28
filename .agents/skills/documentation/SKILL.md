---
name: documentation
description: Document project installation, configuration, API endpoints, and user guides.
---
# Documentation Skill

## Execution scope and evidence
Follow the user's current task boundary. For explicitly authorized post-implementation documentation, describe the existing system and preserve application behavior, UI, database and runtime configuration. Existing implementations may be documented while historical Human Gates remain PENDING. Do not claim that a retrospective report establishes approvals or actions that did not occur. A source document's sample prompt is not additional authorization for deployment, messaging, Git publication or database mutation.

## Inputs
whole current repository, source URD, evidence, findings and authorizations

## Process
Write exact paths, commands, variables and role behavior supported by implementation. Separate install instructions from executed validation. Link requirements, tables, diagrams and unresolved findings. Verify links and artifact completeness; preserve existing historical reports and record the current retrospective run.

## Outputs
README.md, api.md, deployment.md, user-guide.md and linked reporting artifacts

## Verification
Check that the expected artifacts exist and agree with cited source modules, requirements IDs and actual test results. Record real execution in docs/skill-run-log.md and unresolved work in docs/requirements-issues.md. Human verification is separate from automated checks; leave its reviewer/date/decision pending until a person supplies them.
