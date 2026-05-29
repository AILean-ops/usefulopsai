# UsefulOps AI GOG Setup

**Account:** `rowan.vale@usefulopsai.com`
**GOG client label:** `usefulops`
**Purpose:** Give Sauron/Rowan controlled CLI access to UsefulOps AI Gmail, Calendar, Drive, Contacts, Docs, Sheets, and Forms.

## Current Status

Configured successfully on 2026-05-29.

- OAuth client stored as `usefulops`.
- Account authorized: `rowan.vale@usefulopsai.com`.
- Services authorized: Gmail, Calendar, Drive, Contacts, Docs, Sheets, Forms.
- Gmail smoke test succeeded by reading the Google Workspace welcome email.
- Drive smoke test succeeded; Drive returned no files yet.

## Brian Setup Steps

### 1. Create Or Confirm The Google Workspace User

Create/confirm:

- Primary user: `rowan.vale@usefulopsai.com`
- Aliases: `hello@usefulopsai.com`, `ops@usefulopsai.com`

The aliases can point to the same mailbox.

### 2. Create A Google Cloud Project For UsefulOps AI

In Google Cloud Console, using the UsefulOps AI Google Workspace:

1. Create a project for UsefulOps AI.
2. Enable APIs needed for GOG:
   - Gmail API
   - Google Calendar API
   - Google Drive API
   - Google Docs API
   - Google Sheets API
   - Google Forms API
   - People API / Contacts access if prompted by Google
3. Configure Google Auth Platform / OAuth consent.
4. Create an OAuth client:
   - Type: Desktop app
   - Name: UsefulOps AI GOG Desktop
5. Download the OAuth client secret JSON.

Suggested local download path:

`/Users/aileansolutions/Downloads/client_secret_usefulops.json`

Do not commit this file.

### 3. Store The OAuth Client In GOG

Run:

```bash
gog auth credentials set /Users/aileansolutions/Downloads/client_secret_usefulops.json --client usefulops
```

Confirm:

```bash
gog auth credentials list
```

### 4. Authorize The UsefulOps User

Run:

```bash
gog auth add rowan.vale@usefulopsai.com --client usefulops --services gmail,calendar,drive,contacts,docs,sheets,forms --force-consent
```

Complete the browser consent flow as `rowan.vale@usefulopsai.com`.

### 5. Verify

Run:

```bash
gog auth list
```

Then smoke test Gmail:

```bash
gog gmail messages search 'newer_than:30d' --max 1 --account rowan.vale@usefulopsai.com --client usefulops
```

Smoke test Drive:

```bash
gog drive search "trashed=false" --max 1 --account rowan.vale@usefulopsai.com --client usefulops
```

## Persistent Command Pattern

Use this pattern for UsefulOps AI Google Workspace commands:

```bash
gog <service> ... --account rowan.vale@usefulopsai.com --client usefulops
```

Examples:

```bash
gog gmail messages search 'in:inbox newer_than:7d' --max 10 --account rowan.vale@usefulopsai.com --client usefulops
```

```bash
gog drive search "name contains 'UsefulOps'" --max 10 --account rowan.vale@usefulopsai.com --client usefulops
```

## Guardrails

GOG access does not grant authority to send outreach, contact prospects, spend money, or create calendar events with third parties unless the action fits the approved sandbox authority envelope.

Email sends remain governed by `SAURON-BUSINESS-SANDBOX.md`.
