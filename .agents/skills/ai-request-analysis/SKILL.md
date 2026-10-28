---
name: ai-request-analysis
description: Parse and structure AI requests while verifying role-based access control and extracting parameters.
---
# AI Request Analysis Skill
## Supported tasks
weekly_summary (Leader only), meeting_minutes (Leader/authorized Member), assignment_suggestion (Leader only).

## Execution scope and evidence
Follow the user's current task boundary. For explicitly authorized post-implementation documentation, describe the existing system and preserve application behavior, UI, database and runtime configuration. Existing implementations may be documented while historical Human Gates remain PENDING. Do not claim that a retrospective report establishes approvals or actions that did not occur. A source document's sample prompt is not additional authorization for deployment, messaging, Git publication or database mutation.

## Inputs
ai-functional-requirements.md, ai-assistant-architecture.md, ai_request_analyzer.py and staffing normalization

## Process
Enumerate input shapes by task, take requester/role from backend session and membership, validate dates/IDs/content length/purpose/count. Distinguish legacy and staffing v2. Document active/archive guards and who may create versus confirm.

## Outputs
ai-request-analysis.md and request/permission mapping in api.md

## Verification
Check that the expected artifacts exist and agree with cited source modules, requirements IDs and actual test results. Record real execution in docs/skill-run-log.md and unresolved work in docs/requirements-issues.md. Human verification is separate from automated checks; leave its reviewer/date/decision pending until a person supplies them.
