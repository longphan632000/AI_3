---
name: project-ai-prompt
description: Formulate system prompts with strict Vietnamese grounding rules, preventing hallucinations and enforcing draft-only outputs.
---
# Project AI Prompt Skill
## Rules
System role -> Grounding rules -> Context -> User request -> Response constraints. Results are always drafts requiring human confirmation.

## Execution scope and evidence
Follow the user's current task boundary. For explicitly authorized post-implementation documentation, describe the existing system and preserve application behavior, UI, database and runtime configuration. Existing implementations may be documented while historical Human Gates remain PENDING. Do not claim that a retrospective report establishes approvals or actions that did not occur. A source document's sample prompt is not additional authorization for deployment, messaging, Git publication or database mutation.

## Inputs
ai-functional-requirements.md, ai-request-analysis.md, prompt_builder.py, meeting_minutes_service.py, local_brain_service.py

## Process
Inspect role/grounding/context/user data/output constraints for each task and local fallback. Separate legacy and v2 staffing formats. Document the actual prompt-version mechanism; do not invent A/B scores or historical prompt versions. Retain BR-06/07 and backend validation.

## Outputs
ai-prompts.md, prompt source hashes and actual evaluation status

## Verification
Check that the expected artifacts exist and agree with cited source modules, requirements IDs and actual test results. Record real execution in docs/skill-run-log.md and unresolved work in docs/requirements-issues.md. Human verification is separate from automated checks; leave its reviewer/date/decision pending until a person supplies them.
