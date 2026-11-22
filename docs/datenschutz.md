# Datenschutz

> **Eigenprojekt / Demo, kein Kundenauftrag.**
> **Keine Rechtsberatung, keine Konformitätszusage.** Diese Seite beschreibt die Datenflüsse des Workflows, damit eine Prüfung nach dem Schweizer Datenschutzgesetz (revDSG) und – wo anwendbar – der DSGVO vorbereitet werden kann.

## Datenflüsse

| Daten | Ziel | Zweck |
|---|---|---|
| Absender, Betreff, Snippet (Anfang) jeder neuen E-Mail; dazu Zwischenergebnisse der KI-Schritte | OpenAI | Klassifikation, Terminerkennung, Antwortentwurf, Terminanlage |
| `received_at`, `message_id`, `thread_id`, Absender, Betreff, Kategorie, Priorität, Zusammenfassung, `needs_reply`, vorgeschlagene Aktion (`suggested_action`), Status, `approved`, `sent_at`; `draft_id` ist vorgesehen, wird wegen E4 aber nicht geschrieben | Google Sheets | Protokoll und Duplikatprüfung |
| Alarm: Absender, Betreff, Priorität, Zusammenfassung, vorgeschlagene Aktion. Freigabe: Kalenderhinweis, Absender, Betreff, Zusammenfassung, Antwortentwurf | Telegram (Chat der freigebenden Person) | Alarm und Freigabe |
| Angefragter Zeitraum; bei Freigabe Titel, Start und Ende des Termins | Google Calendar | Verfügbarkeit prüfen, Termin anlegen |
| Antwortentwurf und Versand | Gmail | Entwurf speichern, nach Freigabe senden |
| Ein- und Ausgaben der Nodes einer Ausführung (E-Mail-Felder, KI-Ergebnisse, Entwurf, Freigabeantwort), je nach Einstellungen der Instanz | n8n-Instanz (Ausführungsdaten) | Ablauf, Fehlersuche, Fortsetzung nach der Freigabe |

## Aufbewahrung

Ein Löschkonzept ist nicht umgesetzt. Die Daten bleiben an folgenden Orten, bis sie gelöscht werden:

- **Google Sheet:** Protokollzeilen werden nicht automatisch gelöscht.
- **n8n-Ausführungsdaten:** Ob und wie lange n8n Ausführungen speichert, hängt von den Einstellungen der Instanz ab (Speichern erfolgreicher und fehlgeschlagener Ausführungen, automatisches Löschen nach Alter oder Anzahl). Der Workflow setzt dafür keine eigenen Einstellungen. Eine Ausführung, die auf die Telegram-Freigabe wartet, bleibt gespeichert, bis geantwortet wird; ein Zeitlimit ist in der Freigabe-Node nicht gesetzt.
- **Telegram:** Alarm- und Freigabenachrichten mit Absender, Betreff, Zusammenfassung und Entwurf bleiben im Chat, bis sie dort gelöscht werden.
- **Gmail:** Der Entwurf entsteht vor der Freigabe. Nach ❌ bleibt er als Entwurf im Postfach und muss manuell gelöscht werden; nach ✅ liegt er als gesendete Nachricht im Postfach.
- **Google Calendar:** Angelegte Termine bleiben bis zur manuellen Löschung.
- **OpenAI:** Aufbewahrung beim Anbieter nach dessen Bedingungen und den Einstellungen des verwendeten Kontos; nicht geprüft.

## Hinweise

- **Personenbezogene Daten Dritter:** Absender und Inhalte eingehender E-Mails stammen von Dritten, die über die Verarbeitung informiert sein sollten.
- **Anbieter ausserhalb der Schweiz:** OpenAI, Google und Telegram sind Anbieter mit Sitz ausserhalb der Schweiz. Vor einem Einsatz mit echten Daten sind Bekanntgabe ins Ausland, Verträge zur Auftragsbearbeitung und die Einstellungen der Anbieter zu prüfen.
- **Datenminimierung:** Aus der E-Mail gehen nur Absender, Betreff und Snippet an OpenAI, nicht der vollständige Text. Ohne Eingangsfilter betrifft das jedoch **jede** neue E-Mail des Postfachs (E1).
- **Zugriff:** Die Freigabe ist so konfiguriert, dass nur die in `REPLACE_WITH_TELEGRAM_APPROVER_ID` eingetragene Person freigeben soll; ob n8n das durchsetzt, ist nicht geprüft. Zugriff auf Sheet, Postfach, Kalender, Telegram-Chat und n8n-Instanz ist eigenverantwortlich zu beschränken.
- **Menschliche Kontrolle:** Versand und Kalendereintrag liegen im Workflow nur auf dem ✅-Zweig der Freigabe; in dieser Demo nicht ausgeführt.
- **Demo-Betrieb:** Für Tests nur synthetische Daten aus [`test-data/`](../test-data/) und ein eigenes Test-Postfach verwenden.

## Nicht geprüft

- Ob ein konkreter Einsatz die Anforderungen von revDSG oder DSGVO erfüllt; das hängt vom jeweiligen Einsatz ab.
- Welche Ausführungsdaten eine konkrete n8n-Instanz tatsächlich speichert und wie lange.
