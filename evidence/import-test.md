# Lokaler Importtest – n8n 2.43.7

Stand: 21.11.2026. **Eigenprojekt / Demo, kein Kundenauftrag.**

> **Lokaler Import ≠ Funktionstest der Integrationen.**
> Geprüft wurde nur, ob sich die bereinigten Workflows in eine leere, isolierte n8n-Instanz importieren lassen und Struktur und Logik dabei erhalten bleiben. Gmail, Google Sheets, Telegram, Google Calendar und OpenAI wurden nicht aufgerufen. Kein Workflow wurde aktiviert oder ausgeführt.

> **Getestete Fassung:** Dieses Protokoll gilt für die Fassung der Workflows **vor** dem Ersetzen der 9 Sheet-Anzeigenamen (Regel B6, 21.11.2026). Die aktuelle Fassung des Haupt-Workflows wurde **nicht** erneut importiert oder getestet; siehe [Prüfbare Werte](#prüfbare-werte).

## Umgebung

| Punkt | Wert |
|---|---|
| n8n-Version (`n8n --version` im Container) | **2.43.7** |
| Image | `n8nio/n8n:2.43.7` (Docker Hub, Namespace `n8nio`) |
| Image-Digest (Index) | `sha256:3db21366be1d3c77c1708963129c051948573019659e8873e0294be035ffc1b2` |
| Digest der verwendeten Plattform `linux/arm64` | `sha256:d4797c5c1cfee2a9cbb86ce5274f48f745cb680c8dc771a60a6151b18a249179` |
| Image erstellt | 2026-10-16 |
| Docker | Docker Desktop, Client/Server 29.8.2, `linux/arm64` |

Das Image lag bereits lokal vor; `docker pull` meldete «Image is up to date». Der lokale Digest entspricht dem Digest des Tags in der Registry.

## Isolation

- `--network none`: kein Netzwerkzugang des Containers.
- Keine veröffentlichten Ports, keine Editor-Oberfläche, kein Benutzerkonto; nur CLI-Befehle.
- `--cap-drop ALL`, `--security-opt no-new-privileges`, `--pull never`, `--rm`.
- Kein Docker-Socket, kein Home-Verzeichnis, kein Cloud-Laufwerk eingebunden.
- Eingebunden: ein leeres Testverzeichnis für die n8n-Datenbank (`$SCRATCH/n8n-data`), `workflows/` **nur lesend**, ein Arbeitsverzeichnis mit der temporären Kopie **nur lesend**, ein Exportverzeichnis.
- Keine Zugangsdaten, keine Secrets.
- Umgebungsvariablen: `N8N_DIAGNOSTICS_ENABLED=false`, `N8N_VERSION_NOTIFICATIONS_ENABLED=false`, `N8N_TEMPLATES_ENABLED=false`, `N8N_PERSONALIZATION_ENABLED=false`, `N8N_HIRING_BANNER_ENABLED=false`.

## Befehle

`$REPO` = dieses Repository, `$SCRATCH` = temporäres Testverzeichnis ausserhalb des Repositorys.

```bash
n8n_cli() {
  docker run --rm --pull never --network none --cap-drop ALL --security-opt no-new-privileges \
    -e N8N_DIAGNOSTICS_ENABLED=false -e N8N_VERSION_NOTIFICATIONS_ENABLED=false \
    -e N8N_TEMPLATES_ENABLED=false -e N8N_PERSONALIZATION_ENABLED=false -e N8N_HIRING_BANNER_ENABLED=false \
    -v "$SCRATCH/n8n-data:/home/node/.n8n" -v "$REPO/workflows:/import:ro" \
    -v "$SCRATCH/work:/work:ro" -v "$SCRATCH/export:/export" \
    n8nio/n8n:2.43.7 "$@"
}

n8n_cli --version
n8n_cli import:workflow --input=/import/tool-calendar-create-event.json   # 1. zuerst TOOL
n8n_cli export:workflow --all --pretty --output=/export/after-tool.json  # neue TOOL-ID auslesen
# 2. Kopie von workflows/gmail-triage.json nach $SCRATCH/work:
#    REPLACE_WITH_CALENDAR_TOOL_ID genau 1-mal durch die neue TOOL-ID ersetzen
#    (die Datei im Repository bleibt unverändert)
n8n_cli import:workflow --input=/work/gmail-triage.with-tool-id.json      # 3. Haupt-Workflow
n8n_cli export:workflow --all --pretty --output=/export/after-all.json   # 4. Rücklesen
```

## Ergebnisse

| Prüfung | Ergebnis |
|---|---|
| Import TOOL | PASS – «Successfully imported 1 workflow» |
| Import Haupt-Workflow | PASS – «Successfully imported 1 workflow» |
| Export beider Workflows | PASS – «Successfully exported 2 workflows» |
| Haupt-Workflow: 43 Nodes, 45 Verbindungen | PASS |
| TOOL: 3 Nodes, 2 Verbindungen | PASS |
| Alle 8 `$('…')`-Verweise lösen auf | PASS |
| Haupt-Workflow verweist auf das importierte TOOL | PASS |
| Beide Workflows inaktiv | PASS |
| `availableInMCP = false` (Feld wird von 2.43.7 zurückgegeben) | PASS (beide) |
| Keine Zugangsdaten an Nodes | PASS (0 Nodes) |
| Logik unverändert: Node-Parameter, Typen, Versionen, Positionen, Verbindungen gleich der importierten Datei | PASS – keine unerwarteten Unterschiede |
| Test-Datenbank: Zugangsdaten / Ausführungen / aktive Workflows | 0 / 0 / 0 |
| Dateien in `workflows/` nach dem Test | unverändert (SHA-256 gleich; Werte damals nicht protokolliert, siehe [Prüfbare Werte](#prüfbare-werte)) |

### Erwartete, servicebedingte Unterschiede

Der Export ist nicht byteidentisch mit der importierten Datei. n8n ergänzt beim Import auf oberster Ebene: `id` (neu vergeben), `versionId`, `versionCounter`, `versionMetadata`, `createdAt`, `updatedAt`, `isArchived`, `triggerCount`, `shared` (lokales Projekt), beim Haupt-Workflow zusätzlich `tags: []`. In den Nodes und Verbindungen gab es keine Änderungen.

## Prüfbare Werte

SHA-256 der Workflow-Dateien. «Getestete Fassung»: berechnet am 21.11.2026 nach dem Test. «Aktuelle Fassung»: Stand im Repository nach dem Ersetzen der Sheet-Anzeigenamen (B6).

| Datei | Getestete Fassung | Aktuelle Fassung |
|---|---|---|
| `workflows/gmail-triage.json` | `8ab550775a766305ca61d403090572f6cd526333468bbf93f7caad8c8f54850b` | `babbbbe8931f8fba97b3d1d1d179a654568a6557673ce3c7de8634367c11efaa` – nicht erneut importiert |
| `workflows/tool-calendar-create-event.json` | `da7a963804d31e429a7393af8bb8b3fdb80d69f09b7d6bc047881501772863da` | unverändert |

Nachprüfen im Repository (zeigt die aktuelle Fassung): `shasum -a 256 workflows/*.json` (macOS) bzw. `sha256sum workflows/*.json` (Linux).

Unterschied zwischen getesteter und aktueller Fassung: Die aktuelle Fassung wurde mit `scripts/sanitize.py` (inklusive Regel B6) aus denselben privaten Exporten erzeugt. Gegenüber der getesteten Fassung unterscheiden sich genau 9 Zeilen, jeweils `documentId.cachedResultName` → `REPLACE_WITH_YOUR_SHEET_NAME`; alle übrigen Node-Werte, die Verbindungen und der TOOL-Workflow sind unverändert. Daraus folgt nicht, dass die aktuelle Fassung importiert oder getestet wurde.

Der Test hat die Hashwerte vor und nach dem Lauf verglichen (gleich), die Werte selbst aber nicht protokolliert. Dass genau diese Dateien importiert wurden, ist deshalb nicht belegt, sondern nur plausibel: Laut Änderungszeiten im Dateisystem des Autors wurden die Workflow-Dateien zuletzt am 21.11.2026 um 10:54 geändert, das Protokoll dieses Tests entstand um 11:06.

## Vergleichsmethode

Laut Testprotokoll wurde der Rückexport (`after-all.json`) mit den importierten Dateien verglichen: für jede Node `type`, `typeVersion`, `position` und `parameters`, dazu `connections`. Für den Haupt-Workflow war die importierte Datei die temporäre Kopie mit eingetragener TOOL-ID. Das damals verwendete Vergleichsskript ist nicht Teil des Repositorys.

Gleichwertiger Vergleich zum Nachprüfen (nicht das ursprüngliche Skript; Variablen wie oben; erwartet den Rückexport von `export:workflow --all` als JSON-Liste). Exit-Code 0 nur, wenn alle Dateien GLEICH sind; bei ABWEICHUNG oder fehlendem Workflow im Rückexport 1:

```bash
python3 -I - "$SCRATCH/export/after-all.json" \
  "$SCRATCH/work/gmail-triage.with-tool-id.json" \
  "$REPO/workflows/tool-calendar-create-event.json" <<'EOF'
import json, sys
exported = {wf["name"]: wf for wf in json.load(open(sys.argv[1], encoding="utf-8"))}
def core(wf):
    nodes = {n["name"]: [n.get(k) for k in ("type", "typeVersion", "position", "parameters")]
             for n in wf["nodes"]}
    return nodes, wf["connections"]
ok = True
for path in sys.argv[2:]:
    wf = json.load(open(path, encoding="utf-8"))
    same = core(wf) == core(exported[wf["name"]])
    ok = ok and same
    print("GLEICH    " if same else "ABWEICHUNG", wf["name"])
sys.exit(0 if ok else 1)
EOF
```

## Grenzen dieses Nachweises

- Die Ergebnisse oben fassen den Test des Autors zusammen. Konsolenausgaben, Exportdateien und Test-Datenbank wurden nicht ins Repository übernommen; Rohlogs liegen nicht vor.
- Der Test wurde bisher nicht unabhängig wiederholt.
- Der Vergleichsbefehl oben wurde nur mit Dateien dieses Repositorys ausprobiert, nicht mit einem echten Rückexport aus n8n 2.43.7.

## Hinweise und Warnungen

- Beim ersten Start legte n8n eine neue SQLite-Datenbank an (Migrationen) und erzeugte einen Schlüssel nur für diese Testinstanz. Beides liegt ausschliesslich im temporären Testverzeichnis.
- «license SDK: Skipping renewal» – erwartet ohne Netzwerk.
- Die Test-Datenbank enthält einen internen Platzhalter-Benutzer ohne E-Mail-Adresse, den n8n selbst anlegt. Ein Login wurde nicht eingerichtet.
- Der CLI-Import hat bei den Telegram- und Gmail-Nodes **keine** neue `webhookId` erzeugt. Ob n8n sie beim Öffnen oder Speichern im Editor ergänzt, wurde nicht geprüft.

## Nicht geprüft

- Funktion der Integrationen (Gmail, Google Sheets, Telegram, Google Calendar, OpenAI) und damit alle Testfälle aus [`docs/test-plan.md`](../docs/test-plan.md).
- Aktivierung und Ausführung der Workflows; Verhalten der Freigabe per Telegram.
- Öffnen im Editor, Verbinden von Zugangsdaten, Verhalten der Platzhalter im Modus `list`, Kalender `primary`.
- Erzeugung der `webhookId` für `sendAndWait`.
- Andere n8n-Versionen und die Plattform `linux/amd64`.
- Die bekannten Grenzen E1–E5 bestehen unverändert.
