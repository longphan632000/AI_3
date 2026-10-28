---
name: project-data-retrieval
description: Retrieve project data using parameterized SQL queries strictly within the requester's project scope.
---
# Project Data Retrieval Skill
## Rules
Always use parameterized SQL. Limit data to the minimum necessary. Never retrieve or expose passwords, secrets, or API keys.

## Execution scope and evidence
Follow the user's current task boundary. For explicitly authorized post-implementation documentation, describe the existing system and preserve application behavior, UI, database and runtime configuration. Existing implementations may be documented while historical Human Gates remain PENDING. Do not claim that a retrospective report establishes approvals or actions that did not occur. A source document's sample prompt is not additional authorization for deployment, messaging, Git publication or database mutation.

## Inputs
ai-request-analysis.md, database-design.md, project_data_retriever.py, staffing_service.py and member_profile_service.py

## Process
Track each query to scope and bound values. List minimum returned fields and source-reference IDs. Handle missing sources explicitly. For the user-approved system-wide staffing extension, expose professional profiles and aggregate workload only, not task text from other projects. Never return credentials.

## Outputs
ai-assistant-data-flow.md and verified source/field mapping

## Verification
Check that the expected artifacts exist and agree with cited source modules, requirements IDs and actual test results. Record real execution in docs/skill-run-log.md and unresolved work in docs/requirements-issues.md. Human verification is separate from automated checks; leave its reviewer/date/decision pending until a person supplies them.
