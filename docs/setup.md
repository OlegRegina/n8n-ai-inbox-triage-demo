# Einrichtung

> **Eigenprojekt / Demo, kein Kundenauftrag.** Der lokale Import wurde mit n8n **2.43.7** geprüft ([`evidence/import-test.md`](../evidence/import-test.md)); die Einrichtung der Zugänge und ein Testlauf sind in dieser Demo **nicht geprüft**.

## Voraussetzungen

- n8n (geprüft: Import in Version 2.43.7).
- Ein **eigenes Test-Postfach** in Gmail – kein produktives Postfach (siehe E1 im [README](../README.md)).
- Ein Google Sheet mit den Spalten aus [`test-data/sheet-template.csv`](../test-data/sheet-template.csv).
- Ein Google Kalender für Tests.
- Ein Telegram-Bot und ein Chat für Alarme und Freigaben; dazu die Chat-ID und die Telegram-Benutzer-ID der freigebenden Person.
- Für die Freigabe per Telegram: eine n8n-Instanz, deren Webhook-Adresse die Antwort auf die Freigabe empfangen kann (siehe [Telegram-Freigabe](#telegram-freigabe-erreichbarkeit-der-instanz)).
- Ein OpenAI-API-Zugang.

## Benötigte Zugänge in n8n

| Zugangstyp | Nodes |
|---|---|
| Gmail OAuth2 | `Gmail-New Email`, `Gmail - Create Draft`, `Gmail API — Send Approved Draft` |
| Google Sheets OAuth2 | 9 Sheets-Nodes |
| Google Calendar OAuth2 | `Calendar — Check Availability`; im TOOL-Workflow `GOOGLE CALENDAR — Create Event` |
| Telegram API | `Telegramm  - Urgent Alert`, `Telegram — Approval Request` |
| OpenAI API | `OpenAI Chat Model`, `OpenAI Chat Model1`, `OpenAI Chat Model2`, `Calendar Event` |

## Schritte

1. **Sheet anlegen:** neues Google Sheet, erstes Tabellenblatt mit der Kopfzeile aus `test-data/sheet-template.csv`.
2. **TOOL-Workflow zuerst importieren:** `workflows/tool-calendar-create-event.json` (in der Oberfläche über «Import from File» oder per CLI `n8n import:workflow --input=<Datei>`).
3. **Neue ID notieren:** n8n vergibt beim Import eine neue Workflow-ID.
4. **ID eintragen:** in einer Kopie von `workflows/gmail-triage.json` den Platzhalter `REPLACE_WITH_CALENDAR_TOOL_ID` genau einmal ersetzen – oder nach dem Import in der Node `Call '📅TOOL — Calendar Create Event'` den Sub-Workflow auswählen.
5. **Haupt-Workflow importieren.**
6. **Zugänge verbinden** (Tabelle oben).
7. **Platzhalter ersetzen:** Sheet-ID (9×), Telegram-Chat-ID (2×), Telegram-Freigabe-ID (1×), `[Your Name]` in der Grussregel von `AI Agent — Draft Reply` (3×). Kalender `primary` bezeichnet den Hauptkalender des verbundenen Kontos und kann bei Bedarf geändert werden. Der Anzeigename `REPLACE_WITH_YOUR_SHEET_NAME` (9×) ist optional; nach Auswahl des Sheets in der Liste zeigt n8n dessen Namen an (nicht geprüft).
8. **Optional:** einen eigenen Error-Workflow in den Workflow-Einstellungen verbinden (der Verweis auf den privaten Error-Workflow wurde entfernt).
9. **Prüfen vor dem ersten Test:** Telegram- und Gmail-Nodes öffnen und speichern. Beim Import fehlt die `webhookId` dieser Nodes; ob n8n sie dabei ergänzt, ist nicht geprüft (siehe [Telegram-Freigabe](#telegram-freigabe-erreichbarkeit-der-instanz)).
10. **Test:** Workflows nur für die Dauer eines Tests aktivieren; synthetische E-Mails aus [`test-data/synthetic-emails.json`](../test-data/synthetic-emails.json) an das Test-Postfach senden und die Ergebnisse mit [`docs/test-plan.md`](test-plan.md) vergleichen.
11. **Danach:** Workflows deaktivieren; Testtermine und Entwürfe manuell entfernen.

## Telegram-Freigabe: Erreichbarkeit der Instanz

`Telegram — Approval Request` nutzt die Operation «Send and Wait». Die Ausführung wartet, bis die Antwort (✅/❌) über eine Webhook-Adresse der n8n-Instanz zurückkommt. Welche Adresse n8n dafür verwendet, legt die Einstellung `WEBHOOK_URL` fest. Diese Adresse muss auf dem Weg der Antwort erreichbar sein – je nach Umsetzung vom Gerät der freigebenden Person oder von Telegram aus; in der Regel ist dafür eine öffentlich erreichbare HTTPS-Adresse nötig. Eine nur lokal erreichbare Instanz reicht dafür voraussichtlich nicht.

**In dieser Demo nicht geprüft:** welchen Weg n8n 2.43.7 hier verwendet, welche Adresse genügt und ob die beim Import fehlende `webhookId` (Schritt 9) ergänzt wird. Das Öffnen von Ports oder das Ändern von Netzwerkeinstellungen ist nicht Teil dieser Anleitung; dafür gelten die Sicherheitsregeln der eigenen Umgebung.

## Was der Import nicht ersetzt

> **Lokaler Import ≠ Funktionstest der Integrationen.**

Ob Gmail, Google Sheets, Telegram, Google Calendar und OpenAI nach der Einrichtung wie beschrieben zusammenarbeiten, ist für diese Demo nicht geprüft.
