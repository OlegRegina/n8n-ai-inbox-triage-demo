# Sicherheit

Dieses Repository enthält bereinigte Kopien privater n8n-Exporte. **Eigenprojekt / Demo, kein Kundenauftrag.**

## Was entfernt oder ersetzt wurde

| Inhalt | Behandlung |
|---|---|
| Zugangsdaten-Verweise an Nodes (ID und Name) | entfernt |
| Webhook-IDs | entfernt |
| Instanz-ID, Workflow-ID, Versions-ID, Tags | entfernt |
| Verweis auf den privaten Error-Workflow | entfernt |
| Interne Links auf Google-Dokumente | entfernt |
| Google-Sheet-ID und Anzeigename des Sheets, Telegram-Chat- und Freigabe-ID, Kalender-ID, ID des Sub-Workflows | durch Platzhalter ersetzt |
| Personenname in der Grussregel | durch `[Your Name]` ersetzt |
| MCP-Zugriff und Aktivierung | `availableInMCP = false`, `active = false` |
| Interne UUIDs von Nodes, Zuweisungen und Bedingungen (85, zufällige UUID v4) | bewusst unverändert: gewähren keinen Zugriff; erlauben höchstens die Zuordnung zu Kopien des privaten Exports |

Hinterlegte Zugangsdaten (Credentials) speichert n8n getrennt vom Workflow; ein Workflow-Export enthält nur Verweise darauf (ID und Name), und diese wurden entfernt. Werte, die direkt in Node-Parameter eingetragen werden (z. B. ein API-Schlüssel in einem HTTP-Header, in einer URL oder in einem Code-Node), exportiert n8n dagegen im Klartext mit. In den bereinigten Dateien dieses Repositorys wurden keine solchen Werte gefunden (Musterprüfung von `validate.py`, manuelle Durchsicht). Die privaten Quell-Exporte sind nicht Teil des Repositorys; Aussagen über ihren Inhalt lassen sich hier nicht nachprüfen. Ausführungsdaten (Executions) sind nicht Teil dieses Repositorys.

## Wie geprüft wurde

- [`scripts/sanitize.py`](scripts/sanitize.py) wendet nur die genehmigten Änderungen an und bricht ab, wenn unbekannte Felder auftreten oder die Zahl der Änderungen abweicht.
- [`scripts/validate.py`](scripts/validate.py) prüft erlaubte Schlüssel, sucht in allen Dateien nach E-Mail-Adressen, Links, langen Nummern, Schlüsseln und Tokens, vergleicht mit den privaten Quell-Exporten und stellt sicher, dass sich nur genehmigte Felder geändert haben. Ergebnis: [`evidence/validation-report.txt`](evidence/validation-report.txt).
- Zusätzlich wurden alle Zeichenketten der Workflows manuell durchgesehen.

Automatische Prüfungen sind **kein Beweis**, dass keine sensiblen Daten mehr enthalten sind.

## Hinweise für die Nutzung

- Unbereinigte n8n-Exporte nie in ein Repository legen; `.gitignore` schliesst `*.raw.json`, `private/` und `exports/` aus.
- Zugangsdaten nur in n8n hinterlegen, nie in Workflow-Dateien, Node-Parametern, Screenshots oder Chats. Gelangt ein Token dorthin, sofort widerrufen und ersetzen.
- `n8n export:credentials` (insbesondere mit `--decrypted`) nie für Dateien dieses Repositorys verwenden.
- `REPLACE_WITH_TELEGRAM_APPROVER_ID` auf genau die Person setzen, die freigeben darf. Diese Beschränkung ist im Workflow nur konfiguriert (`approverIds`); ob n8n sie durchsetzt, ist nicht geprüft. Den Telegram-Chat deshalb nicht mit weiteren Personen teilen.
- Workflows erst nach vollständiger Einrichtung und nur mit einem Test-Postfach aktivieren (siehe E1 im [README](README.md)).
- `availableInMCP` nur aktivieren, wenn ein Zugriff über MCP wirklich nötig ist.

## Nicht vertrauenswürdige Eingaben (Untrusted Input / Prompt Injection)

- **Herkunft:** Absender, Betreff und Snippet jeder eingehenden E-Mail stammen von Dritten und sind nicht vertrauenswürdig.
- **Weg in die Prompts:** Diese Texte werden ungefiltert in die Prompts von `AI - Classify Email`, `AI - Detect Meeting Request`, `AI Agent — Draft Reply` und `AI Agent — Create Calendar Event` eingesetzt.
- **Mögliche Folgen:** Eine E-Mail kann Anweisungen enthalten, die ein Modell befolgt (Prompt Injection). Möglich sind z. B. eine falsche Kategorie (etwa `ignore` statt `urgent`, dann ohne Alarm), ein irreführender Antwortentwurf, eine falsch erkannte Terminanfrage oder ein unpassender Titel bzw. Zeitraum für den Kalendereintrag.
- **Menschliche Freigabe:** Versand und Kalendereintrag folgen erst nach ✅. Das verringert das Risiko, beseitigt es aber nicht: Klassifikation, Protokoll im Sheet, Alarm und Gmail-Entwurf entstehen ohne Freigabe, und bei der Freigabe kann ein manipulierter Entwurf übersehen werden.
- **Kalenderdaten:** Titel, Start und Ende des Termins werden der freigebenden Person vor ✅ nicht angezeigt und nicht gesondert geprüft. Der Titel wird aus der E-Mail abgeleitet; Start und Ende soll der Agent aus dem geprüften Intervall übernehmen (siehe E5 im [README](README.md)).
- **Nicht Teil dieser Version:** Eingangsfilter, regelbasierte Prüfung der Modellausgaben, Anzeige der Termindaten in der Freigabe.
- **Nicht geprüft:** Verhalten der Modelle gegenüber gezielter Prompt Injection.

## Probleme melden

Bitte ein Issue in diesem Repository eröffnen – **ohne** Zugangsdaten, IDs oder personenbezogene Daten. Für vertrauliche Hinweise die private Sicherheitsmeldung des Repositorys verwenden, sofern sie aktiviert ist.
