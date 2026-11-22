# Nachweise

Stand: 21.11.2026. **Eigenprojekt / Demo, kein Kundenauftrag.**

| Datei | Art | Was sie zeigt | Was sie **nicht** zeigt |
|---|---|---|---|
| [`validation-report.txt`](validation-report.txt) | automatisch: Ausgabe von `scripts/validate.py` (Datum und Anzahl geprüfter Dateien im Kopf des Berichts) | Erlaubte Schlüssel, Musterprüfung aller Dateien des damaligen Stands, Struktur (Nodes, Verbindungen, Verweise), nur genehmigte Änderungen gegenüber dem privaten Export, Platzhalter, synthetische Testdaten | Keine Garantie, dass keine sensiblen Daten mehr enthalten sind; dafür ist zusätzlich eine manuelle Durchsicht nötig. Kein Funktionstest. Später geänderte oder neue Dateien sind nicht abgedeckt. |
| [`validation-notes.md`](validation-notes.md) | manuell | Zusammenfassung des Importtests, Abdeckung des automatischen Berichts, offene Punkte | Keine automatische Prüfung. |
| [`import-test.md`](import-test.md) | manuell: Protokoll des Autors | Ob sich beide Workflows lokal in n8n 2.43.7 importieren lassen und Struktur, Node-Parameter und Verbindungen erhalten bleiben; SHA-256 der getesteten und der aktuellen Fassung; Vergleichsmethode | **Lokaler Import ≠ Funktionstest der Integrationen.** Gmail, Google Sheets, Telegram, Google Calendar und OpenAI werden dabei nicht aufgerufen. Keine Rohlogs. Die aktuelle Fassung des Haupt-Workflows (ersetzte Sheet-Anzeigenamen) wurde nicht erneut importiert. |
| `screenshots/` | geplant, **noch nicht vorhanden** | – | – |

## Wer was nachprüfen kann

- **Alle**, ohne private Exporte: im Repository `python3 -I scripts/validate.py --repo . --workflow workflows/tool-calendar-create-event.json --workflow workflows/gmail-triage.json` ausführen. Das prüft S3, S5, S6 (ohne Quellvergleich), S8, S9 und S10; S2b, S4 und S7 werden übersprungen.
- **Nur der Autor**, mit den privaten Exporten (`--source`) und persönlichen Suchbegriffen (`--deny`): S2b, S4, S7 und den Quellvergleich in S6.
- **Importtest:** lässt sich mit Docker nach [`import-test.md`](import-test.md) wiederholen; eine unabhängige Wiederholung steht aus.

## Vor einer Veröffentlichung

`scripts/validate.py` muss mit `--source` und `--deny` auf dem endgültigen Dateistand erneut laufen; die neue Ausgabe ersetzt `validation-report.txt`. Ein Bericht deckt nur den Dateistand zum Zeitpunkt seiner Erzeugung ab; nach jeder späteren Änderung ist er erneut zu erzeugen (Details in [`validation-notes.md`](validation-notes.md)).

## Status

- Die Demo-Workflows sind inaktiv. In der Demo wurde noch nichts ausgeführt.
- Ergebnisse aus dem privaten Live-System sind in [`docs/test-plan.md`](../docs/test-plan.md) als **DOKUMENTIERT** markiert. Dafür gibt es in diesem Repository keine öffentlichen Nachweise.
