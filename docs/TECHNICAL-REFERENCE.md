# UsefulOps AI Technical Reference

**Created:** 2026-05-29

## Repository

- GitHub repo: `AILean-ops/usefulopsai`
- SSH remote: `git@github-workspace:AILean-ops/usefulopsai.git`
- Local repo: `/Users/aileansolutions/usefulopsai`
- Current status at creation: repo existed on GitHub and cloned successfully as an empty repository.

The plain `git@github.com:AILean-ops/usefulopsai.git` form failed on this machine because GitHub SSH access is configured through the `github-workspace` host alias.

## Local Private State

Private operating state lives under:

- `/Users/aileansolutions/usefulopsai/local/`

This directory is intentionally ignored by Git.

Key local paths:

- Database: `/Users/aileansolutions/usefulopsai/local/data/usefulopsai.sqlite3`
- Logs: `/Users/aileansolutions/usefulopsai/local/logs/`
- Client folders: `/Users/aileansolutions/usefulopsai/local/clients/`
- Prospect working files: `/Users/aileansolutions/usefulopsai/local/prospects/`
- Deliverables: `/Users/aileansolutions/usefulopsai/local/deliverables/`
- Secrets placeholder: `/Users/aileansolutions/usefulopsai/local/secrets/`
- Exports: `/Users/aileansolutions/usefulopsai/local/exports/`

Do not place card numbers, API keys, OAuth secrets, customer credentials, or sensitive client data in Git-tracked files.

## Database Purpose

The initial SQLite database tracks:

- Experiments
- Prospects
- Contacts
- Outreach actions
- Suppression entries
- Approvals
- Clients
- Deliverables
- Revenue
- Expenses
- Tasks
- Real-world action log

The database is for internal operating control only. It is not a CRM product, customer portal, or public service.

