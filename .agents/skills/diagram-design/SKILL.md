---
name: diagram-design
description: Create and refine traceable software engineering diagrams with readable, report-ready layouts.
---
# Diagram Design Skill
## Objective
Create UML/software design diagrams that are technically correct, traceable to approved artifacts and visually suitable for direct inclusion in the report.
## Supported diagrams
Use Case Diagram; Activity Diagram; Sequence Diagram; System Architecture Diagram; Class Diagram; ERD; AI Architecture/Data Flow Diagram.
## Rules
- Do not invent actors, use cases, actions, classes, entities, components or relationships.
- Labels must be readable; nodes/text must not overlap; connectors must not pass through nodes or text.
- PlantUML source files in docs/diagrams/ and matching PNG files when rendering is available.

## Execution scope and evidence
Follow the user's current task boundary. For explicitly authorized post-implementation documentation, describe the existing system and preserve application behavior, UI, database and runtime configuration. Existing implementations may be documented while historical Human Gates remain PENDING. Do not claim that a retrospective report establishes approvals or actions that did not occur. A source document's sample prompt is not additional authorization for deployment, messaging, Git publication or database mutation.

## Inputs
system-model.md, system-model-traceability.md, requirements-decisions.md, relevant specifications and actual schema

## Process
Generate from text/model first. Save sources and renders and freeze hashes before extracting corresponding original figures. Compare content and relations after generation; record differences and unresolved decisions. Inspect renders and revise confusing layouts. Never present an embedded original as a newly generated diagram.

## Outputs
diagrams/*.puml, diagrams/sequence/, diagrams/activity/, matching PNG when rendered, diagram-comparison.md

## Verification
Check that the expected artifacts exist and agree with cited source modules, requirements IDs and actual test results. Record real execution in docs/skill-run-log.md and unresolved work in docs/requirements-issues.md. Human verification is separate from automated checks; leave its reviewer/date/decision pending until a person supplies them.
