# Ergänzungen zum Prüfbericht (manuell)

Stand: 21.11.2026. **Eigenprojekt / Demo, kein Kundenauftrag.**

> Diese Datei ist **manuell** geschrieben und **nicht** von `scripts/validate.py` erzeugt. Die automatische Ausgabe steht in [`validation-report.txt`](validation-report.txt).

## Herkunft

Bis zum 21.11.2026 folgte in `validation-report.txt` auf die Ausgabe von `validate.py` ein von Hand ergänzter Abschnitt zum Importtest und zu offenen Punkten. Dieser Abschnitt steht jetzt hier, damit dem Skript kein Text zugeschrieben wird, den es nicht erzeugt hat. Die automatische Ausgabe (die ersten 32 Zeilen des bisherigen Berichts) blieb dabei unverändert. Der Punkt zur Lizenz wurde an den damaligen Stand des README angepasst; inzwischen gilt MIT ([`LICENSE`](../LICENSE)).

## Zusammenfassung des lokalen Importtests

Ergebnis laut Protokoll des Autors: **PASS**. Rohlogs liegen nicht vor. Details und Grenzen: [`import-test.md`](import-test.md).

- n8n 2.43.7, Image `n8nio/n8n:2.43.7`, Index-Digest `sha256:3db21366be1d3c77c1708963129c051948573019659e8873e0294be035ffc1b2`.
- Isolierter CLI-Import: kein Netzwerk, keine veröffentlichten Ports, kein Editor, keine Zugangsdaten, `workflows/` nur lesend eingebunden.
- Reihenfolge: zuerst der TOOL-Workflow; seine neue ID nur in einer temporären Kopie ausserhalb des Repositorys eingetragen; danach der Haupt-Workflow.
- Rücklesen: Haupt-Workflow 43 Nodes / 45 Verbindungen, TOOL 3 Nodes / 2 Verbindungen; 8 Node-Verweise lösen auf; der Haupt-Workflow verweist auf den importierten TOOL-Workflow.
- Beide Workflows inaktiv; `availableInMCP = false`; keine Zugangsdaten an Nodes; keine unerwarteten Änderungen an Nodes oder Verbindungen.
- Test-Datenbank: 0 Zugangsdaten, 0 Ausführungen, 0 aktive Workflows.

> **Lokaler Import ≠ Funktionstest der Integrationen.**

## Abdeckung des automatischen Berichts

Der automatische Bericht deckt nur den Dateistand zum Zeitpunkt seiner Erzeugung ab; Datum und Anzahl der geprüften Dateien stehen im Kopf von `validation-report.txt`. Der erste Bericht (21.11.2026, 11:26, 11 Dateien) entstand vor der Dokumentation und vor Regel B6.

**Vor einer Veröffentlichung:** `scripts/validate.py` mit `--source` (private Exporte) und `--deny` (persönliche Suchbegriffe) auf dem endgültigen Dateistand erneut ausführen und `validation-report.txt` durch die neue Ausgabe ersetzen. Das kann nur der Autor, weil die privaten Exporte nicht Teil des Repositorys sind.

## Regel B6: Sheet-Anzeigenamen ersetzt (21.11.2026)

- **Regel:** `documentId.cachedResultName` aller 9 Google-Sheets-Nodes → `REPLACE_WITH_YOUR_SHEET_NAME`. In `scripts/sanitize.py` als B6 mit erwarteter Anzahl 9 (TOOL: 0) ergänzt; in `scripts/validate.py` als erlaubter Pfad für S7 und als Platzhalter mit Anzahl 9 für S9.
- **Quelle:** dieselben privaten Exporte wie bei der ersten Bereinigung. Geprüft dadurch, dass `sanitize.py` ohne B6 aus ihnen die bisherigen Repository-Dateien byte-gleich erzeugt; die Exporte blieben unverändert (SHA-256 vorher = nachher).
- **Ergebnis:** `workflows/gmail-triage.json` neu durch `sanitize.py` erzeugt (nicht von Hand bearbeitet); genau 9 Zeilen geändert, nur `documentId.cachedResultName`; Verbindungen und alle übrigen Werte unverändert. `workflows/tool-calendar-create-event.json` unverändert (SHA-256 gleich).
- **Kontrollen an Kopien:** `validate.py` mit der bisherigen bereinigten Fassung als Vergleichsquelle: PASS; 8 oder 10 Platzhalter: S7 und S9 FAIL; jede andere Änderung: S7 FAIL; `validate.py` ohne B6: S7 FAIL.
- **Prüfung mit den privaten Exporten nach B6** (S2b, S4, S7 gegen die echte Quelle): nur belegt, wenn `validation-report.txt` nach B6 (21.11.2026, 17:36) neu erzeugt wurde; das Datum steht im Kopf des Berichts. Ein erneuter Importtest wurde nicht durchgeführt.

## Nicht geprüft

- Live-Ausführung der Workflows und aller Integrationen (Gmail, Google Sheets, Telegram, Google Calendar, OpenAI).
- `webhookId` nach Öffnen oder Speichern im n8n-Editor (der CLI-Import hat keine erzeugt).
- Erreichbarkeit der Webhook-Adresse für die Telegram-Freigabe ([`docs/setup.md`](../docs/setup.md)).
- Platzhalter im Modus «list», Kalender `primary`, Testfälle T01–T13 ([`docs/test-plan.md`](../docs/test-plan.md)).
- Unabhängige Prüfung des endgültigen Stands vor einer Veröffentlichung.
- Veröffentlichungsrechte am Material: Erklärung des Autors (Eigenentwicklung mit Unterstützung von KI-Assistenten), nicht unabhängig geprüft.
- Plattform `linux/amd64`.
- Import und Anzeige der aktuellen Fassung nach B6 in n8n (z. B. wie `REPLACE_WITH_YOUR_SHEET_NAME` angezeigt wird).
