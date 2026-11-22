# n8n AI Inbox Triage – Demo

> **Eigenprojekt / Demo, kein Kundenauftrag.**
> Bereinigte Kopie eines privat betriebenen n8n-Workflows. Alle Testdaten sind synthetisch. Die Workflows in diesem Repository sind **inaktiv** und wurden in der Demo **nicht ausgeführt**.
> English version: [README.en.md](README.en.md)

## Was der Workflow macht

1. Eine neue E-Mail trifft im verbundenen Gmail-Postfach ein (Abfrage jede Minute).
2. Duplikatprüfung über die `message_id` im Google Sheet; bereits verarbeitete E-Mails werden gestoppt.
3. Ein Sprachmodell (OpenAI, `gpt-5.4-mini`) ordnet die E-Mail einer von vier Kategorien zu: `urgent`, `needs_reply`, `informational`, `ignore`. Das Ergebnis wird im Sheet protokolliert.
4. `urgent` → Alarm in Telegram. `informational` und `ignore` → nur Status im Sheet.
5. `needs_reply` → das Modell prüft, ob nach einem Termin gefragt wird. Bei genauer Datums- und Zeitangabe wird Google Calendar auf Verfügbarkeit geprüft (`free` / `conflict`), sonst `not_checked`.
6. Ein KI-Agent schreibt einen Antwortentwurf, der als Entwurf in Gmail gespeichert wird.
7. **Menschliche Freigabe in Telegram:** ✅ oder ❌. Ohne ✅ wird nichts versendet und kein Termin angelegt.
8. Nach ✅: Versand des Entwurfs; bei `free` zusätzlich ein Kalendereintrag über den TOOL-Workflow (der Agent ist angewiesen, genau einen anzulegen). Nach ❌: Status `rejected`, kein Versand.

Ablaufdiagramm und Node-Übersicht: [docs/architecture.md](docs/architecture.md).

## Inhalt

| Pfad | Inhalt |
|---|---|
| [`workflows/tool-calendar-create-event.json`](workflows/tool-calendar-create-event.json) | Sub-Workflow «📅TOOL — Calendar Create Event» (3 Nodes) – **zuerst importieren** |
| [`workflows/gmail-triage.json`](workflows/gmail-triage.json) | Haupt-Workflow «📧GmailTriage» (43 Nodes, 45 Verbindungen) |
| [`docs/setup.md`](docs/setup.md) | Einrichtung: Zugänge, Platzhalter, Importreihenfolge |
| [`docs/architecture.md`](docs/architecture.md) | Ablauf und Zuordnung aller Nodes |
| [`docs/test-plan.md`](docs/test-plan.md) | Testfälle T01–T13 mit Status |
| [`docs/datenschutz.md`](docs/datenschutz.md) | Datenflüsse und Datenschutzhinweise |
| [`test-data/`](test-data/) | Synthetische E-Mails und Sheet-Vorlage |
| [`evidence/`](evidence/) | Automatischer Prüfbericht, manuelle Ergänzungen und lokaler Importtest |
| [`scripts/`](scripts/) | Bereinigung (`sanitize.py`) und Prüfung (`validate.py`) der Exporte |
| [`SECURITY.md`](SECURITY.md) | Was entfernt wurde, Risiken durch nicht vertrauenswürdige E-Mail-Inhalte, Meldung von Problemen |

## Import in Kürze

1. **Zuerst** `workflows/tool-calendar-create-event.json` importieren und die neue Workflow-ID notieren.
2. In `workflows/gmail-triage.json` den Platzhalter `REPLACE_WITH_CALENDAR_TOOL_ID` durch diese ID ersetzen (oder den Sub-Workflow nach dem Import in der Node auswählen).
3. Haupt-Workflow importieren, eigene Zugänge verbinden, übrige Platzhalter ersetzen.
4. Workflows nur für einen Test aktivieren – mit einem eigenen Test-Postfach (siehe E1).

Details: [docs/setup.md](docs/setup.md).

## Platzhalter

| Platzhalter | Wo | Anzahl |
|---|---|---:|
| `REPLACE_WITH_YOUR_SHEET_ID` | alle Google-Sheets-Nodes | 9 |
| `REPLACE_WITH_YOUR_SHEET_NAME` | alle Google-Sheets-Nodes (nur Anzeigename, optional) | 9 |
| `REPLACE_WITH_TELEGRAM_CHAT_ID` | `Telegramm  - Urgent Alert`, `Telegram — Approval Request` | 2 |
| `REPLACE_WITH_TELEGRAM_APPROVER_ID` | `Telegram — Approval Request` (konfigurierte freigebende Person) | 1 |
| `REPLACE_WITH_CALENDAR_TOOL_ID` | `Call '📅TOOL — Calendar Create Event'` | 1 |
| `[Your Name]` | Grussregel im System-Prompt von `AI Agent — Draft Reply` | 3 |
| `primary` | Kalender in `Calendar — Check Availability` und im TOOL-Workflow (Hauptkalender des verbundenen Kontos) | 2 + 2 |

## Status & Grenzen

### Stand der Prüfung (21.11.2026)

| Bereich | Status | Nachweis |
|---|---|---|
| Bereinigung der Exporte: erlaubte Schlüssel, Musterprüfung, Struktur, nur genehmigte Änderungen | PASS laut automatischem Bericht; Datum, Anzahl geprüfter Dateien und Ergebnis stehen im Kopf des Berichts. Gilt nur für den damaligen Dateistand | [`evidence/validation-report.txt`](evidence/validation-report.txt), [`evidence/validation-notes.md`](evidence/validation-notes.md) |
| Lokaler Import in n8n 2.43.7 (isoliert, ohne Netzwerk): Struktur, Node-Parameter und Verbindungen unverändert | PASS für die vorherige Fassung (Protokoll des Autors, ohne Rohlogs); die aktuelle Fassung mit ersetzten Sheet-Anzeigenamen wurde nicht erneut importiert | [`evidence/import-test.md`](evidence/import-test.md) |
| Testfälle im privaten Live-System des Autors | TEILWEISE DOKUMENTIERT (nur intern protokolliert, teils mit früheren Versionen; einzelne Zweige und T13 nicht getestet; keine öffentlichen Nachweise) | [`docs/test-plan.md`](docs/test-plan.md) |
| Testfälle T01–T13 in dieser Demo | NICHT GETESTET | [`docs/test-plan.md`](docs/test-plan.md) |
| Funktion der Integrationen Gmail, Google Sheets, Telegram, Google Calendar, OpenAI aus diesem Repository | NICHT GETESTET | – |

> **Lokaler Import ≠ Funktionstest der Integrationen.**

### Bekannte Grenzen E1–E5

Keine dieser Grenzen ist behoben oder live nachgetestet. Die Version 1 übernimmt das Verhalten des privat betriebenen Workflows bewusst unverändert; dort wurde es nur teilweise getestet (siehe [`docs/test-plan.md`](docs/test-plan.md)).

**E1 – kein Eingangsfilter.** Der Gmail-Trigger hat keinen Filter: Er verarbeitet **jede** neue E-Mail des verbundenen Postfachs (Abfrage jede Minute) und sendet Absender, Betreff und Snippet an OpenAI. Für Tests deshalb nur ein eigenes Test-Postfach verwenden. Ein Filter (z. B. nach Label) wäre eine Verhaltensänderung und ist nicht Teil dieser Version.

**E2 – Sprache der Texte und Buttons.** Telegram-Meldungen, die Button-Beschriftungen und ein Beispiel im Parser sind auf Russisch. Die Buttons lauten sinngemäss «Zeit bestätigen» / «Anderes vorschlagen» – auch bei E-Mails ohne Terminbezug. ❌ lehnt nur ab und schlägt nichts vor.

**E3 – Tippfehler in Node-Namen.** `Parser - Email Classificatuon` und `Telegramm  - Urgent Alert` bleiben unverändert, weil die Version 1 alle Node-Namen und Verbindungen 1:1 aus dem privaten Export übernimmt. Kein Ausdruck im Workflow verweist auf diese beiden Namen; die Verbindungen (`connections`) referenzieren Nodes aber per Namen, und `scripts/validate.py` prüft, dass Namen und Verbindungen der Quelle entsprechen.

**E4 – `Sheets — Save Draft ID` schreibt keine Entwurfs-ID.** Die Set-Node enthält die Literale `Expression:` und `Fixed:` statt Ausdrücken. Dadurch werden `draft_id` und der Status `draft_created` nicht ins Sheet geschrieben (Testfall T12, OFFEN). Der Versand nach Freigabe ist nicht betroffen, weil die Entwurfs-ID direkt aus `Gmail - Create Draft` gelesen wird.

**E5 – widersprüchliche Regeln zur Endzeit eines Termins.** Im Prompt von `AI Agent — Create Calendar Event` verlangt Regel 9, Start und Ende exakt aus dem geprüften Kalenderintervall zu übernehmen und nichts zu berechnen. Ein späterer Satz verlangt, bei Startzeit und Dauer die Endzeit zu berechnen. Bei einer Anfrage wie «um 15:00 Uhr für 30 Minuten» würde der Kalender laut Workflow-Logik für 60 Minuten geprüft: Die Terminerkennung soll kein Ende berechnen, und `Prepare Calendar Interval` setzt ohne Ende +60 Minuten. Welches Ende der Agent setzt, ist nicht getestet (Testfall T13).

### Weitere Grenzen

- Das Modell sieht nur den Gmail-Snippet (Anfang der Nachricht), nicht den ganzen Text. Bei weitergeleiteten Nachrichten ohne Details bat der Entwurf im privaten System um die vollständige Nachricht (T10).
- Die Klassifikation ist probabilistisch; Fehlzuordnungen sind möglich.
- Nach einer Ablehnung bleibt der Entwurf in Gmail und muss manuell gelöscht werden.
- Der TOOL-Workflow prüft seine Eingaben nicht selbst und verlässt sich auf den Agenten.
- Der Workflow speichert Protokolldaten im Sheet ohne automatische Löschung.

### Nicht geprüft

- Ausführung und Aktivierung beider Workflows aus diesem Repository.
- Erneuter Import der aktuellen Fassung des Haupt-Workflows (nach dem Ersetzen der 9 Sheet-Anzeigenamen).
- Öffnen im Editor, Verbinden von Zugangsdaten, Verhalten der Platzhalter.
- Ob n8n beim Öffnen oder Speichern im Editor die beim Import fehlende `webhookId` der Telegram- und Gmail-Nodes ergänzt (relevant für die Freigabe per Telegram).
- Erreichbarkeit der n8n-Instanz für die Antwort auf die Telegram-Freigabe (`WEBHOOK_URL`, siehe [`docs/setup.md`](docs/setup.md)).
- Andere n8n-Versionen als 2.43.7 und die Plattform `linux/amd64`.

## Datenschutz

Der Workflow verarbeitet E-Mail-Daten Dritter und übermittelt Teile davon an Anbieter ausserhalb der Schweiz. Übersicht der Datenflüsse und Hinweise: [docs/datenschutz.md](docs/datenschutz.md). Keine Rechtsberatung, keine Konformitätszusage.

## Sicherheit

Was aus den Exporten entfernt wurde, Risiken durch nicht vertrauenswürdige E-Mail-Inhalte (Prompt Injection) und wie Probleme gemeldet werden: [SECURITY.md](SECURITY.md).

## Lizenz

MIT – siehe [LICENSE](LICENSE). Eigenentwicklung, mit Unterstützung von KI-Assistenten erstellt.
