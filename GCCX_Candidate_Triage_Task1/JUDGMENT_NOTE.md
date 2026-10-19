# Judgment Note — Candidate Triage Tool

## What I would build first
For a two-week rollout supporting roughly 3,000 candidates per week, I would first harden the core workflow: reliable candidate ingestion, searchable and filterable records, auditable shortlist/tag changes, pagination, and integration tests. I would add operational logging, backups, role-based access, and a clear retention policy before exposing candidate data to multiple client teams. I would test query latency against a representative dataset rather than assume the current 48-record mock dataset predicts production performance.

## What I would explicitly defer
I would defer automated candidate scoring, semantic search, bulk outreach, complex analytics, model fine-tuning, and integrations with multiple applicant-tracking systems. These features increase scope and can create false confidence before we validate data quality, recruiter workflow, and measurable benefit.

## The main risk I would flag
The primary risk is that recruiters may treat an AI-generated fit summary as an objective hiring recommendation, even when source notes are incomplete or biased. I would keep the summary evidence-grounded, label it as decision support, preserve human review, test for unsupported claims, and monitor how recruiters use it. I would not deploy the tool for consequential automated hiring decisions without privacy, security, fairness, and legal review.

> Before submission, edit this note so it accurately reflects the decisions you made in your own implementation.
