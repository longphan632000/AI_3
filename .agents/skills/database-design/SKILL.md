---
name: database-design
description: Design a normalized MySQL database schema and ERD from approved requirements and architecture while preserving traceability and business constraints.
---
# Database Design Skill
## Objective
Transform approved requirements and architecture into a consistent, normalized and traceable relational database design for MySQL.

## Execution scope and evidence
Follow the user's current task boundary. For explicitly authorized post-implementation documentation, describe the existing system and preserve application behavior, UI, database and runtime configuration. Existing implementations may be documented while historical Human Gates remain PENDING. Do not claim that a retrospective report establishes approvals or actions that did not occur. A source document's sample prompt is not additional authorization for deployment, messaging, Git publication or database mutation.

## Inputs
requirements.md, architecture.md, database/schema.sql, database/operational_schema.py, migrations.py

## Process
Extract physical types, nullability, keys, checks and indexes from DDL. Explain service-level invariants separately. Compare URD conceptual fields with physical fields. Do not execute DDL, reseed or alter data in documentation mode.

## Outputs
database-design.md, tables/data-dictionary.md, diagrams/erd.puml; existing database/schema.sql is an input in preservation mode

## Verification
Check that the expected artifacts exist and agree with cited source modules, requirements IDs and actual test results. Record real execution in docs/skill-run-log.md and unresolved work in docs/requirements-issues.md. Human verification is separate from automated checks; leave its reviewer/date/decision pending until a person supplies them.
