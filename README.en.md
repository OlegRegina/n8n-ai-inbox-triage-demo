# n8n AI Inbox Triage – Demo

> **Personal demo project, not client work.**
> Sanitized copy of a privately operated n8n workflow. All test data is synthetic. The workflows in this repository are **inactive** and have **not been executed** as part of this demo.
> Deutsche Version: [README.md](README.md)

## What the workflow does

1. A new e-mail arrives in the connected Gmail inbox (polled every minute).
2. Duplicate check via `message_id` in the Google Sheet; already processed e-mails are stopped.
3. A language model (OpenAI, `gpt-5.4-mini`) assigns one of four categories: `urgent`, `needs_reply`, `informational`, `ignore`. The result is logged in the sheet.
4. `urgent` → alert in Telegram. `informational` and `ignore` → status in the sheet only.
5. `needs_reply` → the model checks whether a meeting is requested. If an exact date and time are given, Google Calendar is checked for availability (`free` / `conflict`), otherwise `not_checked`.
6. An AI agent writes a reply, which is saved as a Gmail draft.
7. **Human approval in Telegram:** ✅ or ❌. Without ✅ nothing is sent and no event is created.
8. After ✅: the draft is sent; for `free`, a calendar event is also created through the TOOL workflow (the agent is instructed to create exactly one). After ❌: status `rejected`, nothing is sent.

Flow diagram and node overview: [docs/architecture.md](docs/architecture.md) (German).

## Contents

| Path | Content |
|---|---|
| [`workflows/tool-calendar-create-event.json`](workflows/tool-calendar-create-event.json) | Sub-workflow "📅TOOL — Calendar Create Event" (3 nodes) – **import first** |
| [`workflows/gmail-triage.json`](workflows/gmail-triage.json) | Main workflow "📧GmailTriage" (43 nodes, 45 connections) |
| [`docs/setup.md`](docs/setup.md) | Setup: credentials, placeholders, import order (German) |
| [`docs/architecture.md`](docs/architecture.md) | Flow and mapping of all nodes (German) |
| [`docs/test-plan.md`](docs/test-plan.md) | Test cases T01–T13 with status (German) |
| [`docs/datenschutz.md`](docs/datenschutz.md) | Data flows and data protection notes (German) |
| [`test-data/`](test-data/) | Synthetic e-mails and sheet template |
| [`evidence/`](evidence/) | Automatic validation report, manual notes and local import test (notes and import test in German) |
| [`scripts/`](scripts/) | Sanitization (`sanitize.py`) and validation (`validate.py`) of the exports |
| [`SECURITY.md`](SECURITY.md) | What was removed, risks from untrusted e-mail content, how to report issues (German) |

## Import in short

1. Import `workflows/tool-calendar-create-event.json` **first** and note its new workflow ID.
2. In `workflows/gmail-triage.json`, replace the placeholder `REPLACE_WITH_CALENDAR_TOOL_ID` with that ID (or select the sub-workflow in the node after import).
3. Import the main workflow, connect your own credentials, replace the remaining placeholders.
4. Activate the workflows only for a test – with a dedicated test inbox (see E1).

Details: [docs/setup.md](docs/setup.md).

## Placeholders

| Placeholder | Where | Count |
|---|---|---:|
| `REPLACE_WITH_YOUR_SHEET_ID` | all Google Sheets nodes | 9 |
| `REPLACE_WITH_YOUR_SHEET_NAME` | all Google Sheets nodes (display name only, optional) | 9 |
| `REPLACE_WITH_TELEGRAM_CHAT_ID` | `Telegramm  - Urgent Alert`, `Telegram — Approval Request` | 2 |
| `REPLACE_WITH_TELEGRAM_APPROVER_ID` | `Telegram — Approval Request` (configured approver) | 1 |
| `REPLACE_WITH_CALENDAR_TOOL_ID` | `Call '📅TOOL — Calendar Create Event'` | 1 |
| `[Your Name]` | closing rule in the system prompt of `AI Agent — Draft Reply` | 3 |
| `primary` | calendar in `Calendar — Check Availability` and in the TOOL workflow (primary calendar of the connected account) | 2 + 2 |

## Status & limitations

### Verification status (2026-11-21)

| Area | Status | Evidence |
|---|---|---|
| Sanitization of the exports: allowed keys, pattern scan, structure, approved changes only | PASS according to the automatic report; date, number of checked files and result are in the report header. Valid only for the file set at that time | [`evidence/validation-report.txt`](evidence/validation-report.txt), [`evidence/validation-notes.md`](evidence/validation-notes.md) |
| Local import into n8n 2.43.7 (isolated, no network): structure, node parameters and connections unchanged | PASS for the previous version (author's test record, no raw logs); the current version with replaced sheet display names was not imported again | [`evidence/import-test.md`](evidence/import-test.md) |
| Test cases in the author's private live system | PARTLY DOCUMENTED (logged internally only, partly with earlier versions; some branches and T13 not tested; no public evidence) | [`docs/test-plan.md`](docs/test-plan.md) |
| Test cases T01–T13 in this demo | NOT TESTED | [`docs/test-plan.md`](docs/test-plan.md) |
| Function of the Gmail, Google Sheets, Telegram, Google Calendar and OpenAI integrations from this repository | NOT TESTED | – |

> **Lokaler Import ≠ Funktionstest der Integrationen.** (A local import is not a functional test of the integrations.)

### Known limitations E1–E5

None of these limitations has been fixed or re-tested live. Version 1 deliberately keeps the behaviour of the privately operated workflow unchanged; it was only partly tested there (see [`docs/test-plan.md`](docs/test-plan.md)).

**E1 – no inbox filter.** The Gmail trigger has no filter: it processes **every** new e-mail of the connected inbox (polled every minute) and sends sender, subject and snippet to OpenAI. Use a dedicated test inbox for tests. A filter (e.g. by label) would change the behaviour and is not part of this version.

**E2 – language of texts and buttons.** Telegram messages, button labels and one example in the parser are in Russian. The buttons mean "confirm time" / "suggest another" – also for e-mails that are not about a meeting. ❌ only rejects and suggests nothing.

**E3 – typos in node names.** `Parser - Email Classificatuon` and `Telegramm  - Urgent Alert` are kept unchanged because version 1 takes all node names and connections 1:1 from the private export. No expression in the workflow refers to these two names; the connections (`connections`), however, reference nodes by name, and `scripts/validate.py` checks that names and connections match the source.

**E4 – `Sheets — Save Draft ID` does not write the draft ID.** The Set node contains the literals `Expression:` and `Fixed:` instead of expressions. As a result, `draft_id` and the status `draft_created` are not written to the sheet (test case T12, OPEN). Sending after approval is not affected, because the draft ID is read directly from `Gmail - Create Draft`.

**E5 – contradictory rules for the end time of a meeting.** In the prompt of `AI Agent — Create Calendar Event`, rule 9 requires start and end to be taken exactly from the checked calendar interval without any calculation. A later sentence asks to calculate the end time from start time and duration. For a request such as "at 15:00 for 30 minutes", the calendar would be checked for 60 minutes according to the workflow logic: meeting detection is told not to calculate an end, and `Prepare Calendar Interval` adds 60 minutes when no end is given. Which end time the agent sets is not tested (test case T13).

### Further limitations

- The model only sees the Gmail snippet (beginning of the message), not the full text. For forwarded messages without details, the draft asked for the full message in the private system (T10).
- Classification is probabilistic; misclassification is possible.
- After a rejection, the draft stays in Gmail and has to be deleted manually.
- The TOOL workflow does not validate its inputs and relies on the agent.
- The workflow keeps log data in the sheet without automatic deletion.

### Not verified

- Execution and activation of both workflows from this repository.
- A new import of the current version of the main workflow (after replacing the 9 sheet display names).
- Opening in the editor, connecting credentials, behaviour of the placeholders.
- Whether n8n adds the `webhookId` that is missing after import to the Telegram and Gmail nodes when opening or saving them in the editor (relevant for approval via Telegram).
- Reachability of the n8n instance for the reply to the Telegram approval (`WEBHOOK_URL`, see [`docs/setup.md`](docs/setup.md), German).
- n8n versions other than 2.43.7 and the platform `linux/amd64`.

## Data protection

The workflow processes e-mail data of third parties and transfers parts of it to providers outside Switzerland. Data flows and notes: [docs/datenschutz.md](docs/datenschutz.md) (German). No legal advice, no compliance statement.

## Security

What was removed from the exports, risks from untrusted e-mail content (prompt injection) and how to report issues: [SECURITY.md](SECURITY.md) (German).

## License

MIT – see [LICENSE](LICENSE). Developed independently with the help of AI assistants.
