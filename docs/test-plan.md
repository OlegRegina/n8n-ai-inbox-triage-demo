# Testplan – n8n AI Inbox Triage (Demo)

> **Eigenprojekt / Demo, kein Kundenauftrag.** Alle Testdaten sind synthetisch: [`test-data/synthetic-emails.json`](../test-data/synthetic-emails.json).
> Stand: 21.11.2026. Die Demo-Workflows sind **inaktiv**; in der Demo wurde **noch nichts ausgeführt**.

## Status-Legende

| Status | Bedeutung |
|---|---|
| **DOKUMENTIERT** | Im privaten Live-System des Autors getestet und intern protokolliert; teils mit früheren Versionen (in der Tabelle vermerkt). Öffentliche Nachweise (Screenshots, Executions) liegen in diesem Repository **nicht** vor. |
| **NICHT GETESTET** | In der Umgebung der jeweiligen Spalte (Live-System bzw. Demo) nicht geprüft. |
| **OFFEN** | Bekannter Fehler, nicht behoben. |

Ein erfolgreicher lokaler Import ist **kein Funktionstest**: Gmail, Google Sheets, Telegram, Google Calendar und OpenAI werden dabei nicht aufgerufen.

## Testumgebung (Voraussetzungen)

- **Eigenes Test-Postfach**, kein produktives Postfach. Der Gmail-Trigger hat keinen Filter und verarbeitet jede neue E-Mail im verbundenen Postfach (siehe E1).
- Google Sheet mit den Spalten aus [`test-data/sheet-template.csv`](../test-data/sheet-template.csv).
- Testkalender mit dem synthetischen Blocker am 09.12.2026, 10:00–11:00 (für T04).
- Telegram-Testchat; Freigabe nur durch die eingetragene Person.
- n8n-Instanz, deren Webhook-Adresse die Antwort auf die Telegram-Freigabe empfangen kann (siehe [`docs/setup.md`](setup.md); in dieser Demo nicht geprüft).
- Beide Workflows nur für die Dauer eines Tests aktivieren und danach wieder deaktivieren.

## Testfälle

| ID | E-Mail | Erwarteter Ablauf | Erwartetes Ergebnis | Live-System | Demo |
|---|---|---|---|---|---|
| T01 | syn-01 | urgent → Telegram-Alarm → Sheets | Alarm in Telegram, Status `urgent_notified` | DOKUMENTIERT (frühere Version) | NICHT GETESTET |
| T02 | syn-02 | needs_reply → Kalender nicht geprüft → Entwurf → Freigabe ✅ → Versand | Entwurf in Gmail, nach ✅ versendet; Status `sent` | Versand nach Freigabe in einer früheren Version ohne Kalenderzweig DOKUMENTIERT; in der aktuellen Version ✅ bei `not_checked` und Status `sent` NICHT GETESTET | NICHT GETESTET |
| T03 | syn-03 | Termin mit Start und Ende → Kalender frei → Entwurf bestätigt → ✅ | Versand und genau ein Kalendereintrag 14:00–15:00 | DOKUMENTIERT (11.11.2026) | NICHT GETESTET |
| T04 | syn-04 | Termin → Kalender belegt → Entwurf bittet um anderen Zeitpunkt → ✅ | nur Versand, **kein** Kalendereintrag | Entwurf und Telegram-Hinweis DOKUMENTIERT; ✅ bei `conflict` NICHT GETESTET | NICHT GETESTET |
| T05 | syn-05 | Termin ohne genaue Zeit → Kalender nicht geprüft | Entwurf fragt nach passenden Tagen und Zeiten | DOKUMENTIERT (11.11.2026) | NICHT GETESTET |
| T06 | syn-06 | Start ohne Ende → Intervall mit 60 Minuten → Kalender frei → ✅ | ein Kalendereintrag 09:30–10:30 | DOKUMENTIERT (13.11.2026, nach Korrektur) | NICHT GETESTET |
| T07 | syn-07 | informational | Status `informational_logged` | DOKUMENTIERT (11.11.2026) | NICHT GETESTET |
| T08 | syn-08 | ignore | Status `ignored` | DOKUMENTIERT (frühere Version) | NICHT GETESTET |
| T09 | syn-09 | Duplikat (gleiche `message_id` wie syn-07) | Stopp, keine neue Zeile | DOKUMENTIERT (frühere Version) | NICHT GETESTET |
| T10 | syn-10 | weitergeleitete Nachricht ohne Details | Entwurf bittet um die vollständige Nachricht, kein Datum erfunden | DOKUMENTIERT (11.11.2026) | NICHT GETESTET |
| T11 | syn-02 | wie T02, aber Ablehnung ❌ | Status `rejected`, kein Versand; der Entwurf bleibt in Gmail | DOKUMENTIERT | NICHT GETESTET |
| T12 | (jede needs_reply-E-Mail) | Entwurf erstellt → `draft_id` in Sheets | laut Design `draft_created` und `draft_id` | **OFFEN** (E4): wird nicht geschrieben | NICHT GETESTET |
| T13 | syn-11 | Termin mit Start und Dauer (30 Minuten) | unklar, siehe E5 | NICHT GETESTET | NICHT GETESTET |

## Bekannte Grenzen mit Bezug zu den Tests

Die ausführliche Beschreibung folgt im README im Abschnitt **Status & Grenzen**. Keine dieser Grenzen ist behoben oder live nachgetestet.

- **E1 – kein Eingangsfilter.** Der Gmail-Trigger verarbeitet jede neue E-Mail des verbundenen Postfachs (Abfrage jede Minute) und sendet Absender, Betreff und Snippet an OpenAI. Deshalb nur ein eigenes Test-Postfach verwenden.
- **E2 – Sprache und Buttons.** Telegram-Texte, Buttons und ein Beispiel im Parser sind auf Russisch. Die Buttons lauten sinngemäss «Zeit bestätigen / Anderes vorschlagen» – auch bei E-Mails ohne Terminbezug (z. B. T02). ❌ lehnt nur ab und schlägt nichts vor.
- **E3 – Tippfehler in Node-Namen** (`Parser - Email Classificatuon`, `Telegramm  - Urgent Alert`) bleiben bewusst unverändert: Version 1 übernimmt Node-Namen und Verbindungen 1:1 aus dem privaten Export. Kein Ausdruck verweist auf diese Namen; die Verbindungen referenzieren Nodes aber per Namen.
- **E4 – `Sheets — Save Draft ID`.** Die Set-Node enthält die Literale `Expression:` / `Fixed:` statt Ausdrücken. Dadurch wird `draft_id` nicht in das Sheet geschrieben (T12). Versand nach Freigabe ist davon nicht betroffen, weil die Entwurfs-ID direkt aus `Gmail - Create Draft` gelesen wird.
- **E5 – widersprüchliche Regeln zur Endzeit.** Im Prompt von `AI Agent — Create Calendar Event` verlangt Regel 9, Start und Ende exakt aus dem geprüften Kalenderintervall zu übernehmen und nichts zu berechnen. Ein späterer Satz verlangt, bei Startzeit und Dauer die Endzeit zu berechnen. Bei «30 Minuten» (T13) würde der Kalender laut Workflow-Logik für 60 Minuten geprüft (ohne erkanntes Ende +60 Minuten); welches Ende der Agent setzt, ist nicht getestet.
- Das Modell sieht nur den Gmail-Snippet (Anfang der Nachricht), nicht den ganzen Text.
- Die Klassifikation ist probabilistisch; im Live-System wurde z. B. ein Newsletter einmal als `urgent` eingestuft.
- Nach einer Ablehnung bleibt der Entwurf in Gmail und muss manuell gelöscht werden.
- Der TOOL-Workflow prüft seine Eingaben nicht selbst und verlässt sich auf den Agenten.

## Ablauf eines Testlaufs

1. Workflows importieren: **zuerst** `workflows/tool-calendar-create-event.json`, danach `workflows/gmail-triage.json`; die neue ID des TOOL-Workflows beim Platzhalter `REPLACE_WITH_CALENDAR_TOOL_ID` eintragen.
2. Platzhalter ersetzen und eigene Zugänge verbinden.
3. Erwartetes Ergebnis vor dem Lauf festhalten.
4. Eine E-Mail aus `synthetic-emails.json` an das Test-Postfach senden.
5. Ergebnis in Telegram, Gmail, Sheet und Kalender mit der Erwartung vergleichen; Abweichungen dokumentieren.
6. Workflows deaktivieren; Testtermine und Entwürfe manuell entfernen.
