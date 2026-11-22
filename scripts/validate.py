#!/usr/bin/env python3
"""Validate sanitized n8n exports and scan the repository for sensitive data.

Checks
  S2b  no repository file is byte-identical to a private source export
  S3   allowlist of keys: unknown or forbidden keys fail (credentials, webhookId,
       cachedResultUrl, instanceId, errorWorkflow, staticData, workflow id/versionId);
       pinData and nodeGroups must be empty
  S4   no value taken from the private source (credential/workflow/tag ids, sheet id,
       Telegram ids, calendar id, webhook ids, instance/version ids, internal URLs, e-mails)
       appears in any repository file                                  [needs --source]
  S5   pattern scan of every repository file: e-mails outside example.com, URLs outside
       the allowlist, numbers with 7+ digits, API keys/tokens/JWT/private keys, IPv4,
       16-character n8n-style ids, personal tokens given with --deny
  S6   structure: node/edge counts, node names and connections unchanged, every $('...')
       reference resolves                                              [names: needs --source]
  S7   the only differences to the source are the approved map paths A1-C2 (incl. B6)
                                                                       [needs --source]
  S8   active = false and settings.availableInMCP = false
  S9   placeholder counts equal the approved map
  S10  synthetic test data: flagged synthetic, example.com only, CSV header = sheet schema

Values are never printed: only file names, JSON paths and categories.
Automatic checks are not proof that no sensitive data remains; a manual review is required.

Usage:
  python3 -I scripts/validate.py --repo . \
      --workflow workflows/tool-calendar-create-event.json [--source PRIVATE_TOOL.json] \
      --workflow workflows/gmail-triage.json [--source PRIVATE_MAIN.json] \
      [--deny TOKEN ...] [--report evidence/validation-report.txt] [--overwrite]
"""
import argparse
import csv
import hashlib
import json
import re
import sys
from datetime import datetime
from pathlib import Path

SHEET = "REPLACE_WITH_YOUR_SHEET_ID"
SHEET_NAME = "REPLACE_WITH_YOUR_SHEET_NAME"
CHAT = "REPLACE_WITH_TELEGRAM_CHAT_ID"
APPROVER = "REPLACE_WITH_TELEGRAM_APPROVER_ID"
TOOL = "REPLACE_WITH_CALENDAR_TOOL_ID"
NAME = "[Your Name]"
CALENDAR = "primary"

EXPECT = {
    "📧GmailTriage": {"nodes": 43, "edges": 45, "calendar_primary": 2,
                     "placeholders": {SHEET: 9, SHEET_NAME: 9, CHAT: 2, APPROVER: 1, TOOL: 1, NAME: 3}},
    "📅TOOL — Calendar Create Event": {"nodes": 3, "edges": 2, "calendar_primary": 2,
                                      "placeholders": {SHEET: 0, SHEET_NAME: 0, CHAT: 0, APPROVER: 0, TOOL: 0, NAME: 0}},
}

TOP_ALLOWED = {"name", "nodes", "pinData", "connections", "active", "settings", "meta", "nodeGroups", "tags"}
NODE_ALLOWED = {"parameters", "type", "typeVersion", "position", "id", "name",
                "alwaysOutputData", "retryOnFail", "waitBetweenTries"}
SETTINGS_ALLOWED = {"executionOrder", "binaryMode", "availableInMCP", "timeSavedMode", "callerPolicy"}
FORBIDDEN_KEYS = {"credentials", "webhookId", "cachedResultUrl", "instanceId", "errorWorkflow",
                  "staticData", "versionId", "templateCredsSetupCompleted"}
SAFE_16 = {"autoMapInputData"}
URL_HOSTS_ALLOWED = {"gmail.googleapis.com", "example.com"}

EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
URL = re.compile(r"https?://[^\s\"'<>)\]]+")
LONG_NUMBER = re.compile(r"(?<![\w-])\d{7,}(?![\w-])")
IPV4 = re.compile(r"(?<![\d.])(?:\d{1,3}\.){3}\d{1,3}(?![\d.])")
SECRETS = {
    "openai-style key": re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    "github token": re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}"),
    "google api key": re.compile(r"AIza[0-9A-Za-z_-]{30,}"),
    "slack token": re.compile(r"xox[abprs]-[A-Za-z0-9-]{10,}"),
    "telegram bot token": re.compile(r"\d{8,10}:[A-Za-z0-9_-]{30,}"),
    "jwt": re.compile(r"eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}"),
    "private key": re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    "bearer token": re.compile(r"[Bb]earer\s+[A-Za-z0-9._-]{20,}"),
}

ALLOWED_DIFF = [  # (regex on path, kind, required new value or None)
    (re.compile(r"^nodes\[.*\]\.credentials\."), "removed", None),              # A1
    (re.compile(r"^nodes\[.*\]\.webhookId$"), "removed", None),                 # A2
    (re.compile(r"^meta\.(instanceId|templateCredsSetupCompleted)$"), "removed", None),  # A3
    (re.compile(r"^meta$"), "added", {}),                                        # A3 (meta now empty)
    (re.compile(r"^(id|versionId)$"), "removed", None),                         # A4
    (re.compile(r"^settings\.errorWorkflow$"), "removed", None),                # A5
    (re.compile(r"\.cachedResultUrl$"), "removed", None),                       # A6, B4
    (re.compile(r"^tags(\[|\.|$)"), "removed", None),                           # A7
    (re.compile(r"\.parameters\.documentId\.value$"), "changed", SHEET),        # B1
    (re.compile(r"\.parameters\.documentId\.cachedResultName$"), "changed", SHEET_NAME),  # B6
    (re.compile(r"\.parameters\.chatId$"), "changed", CHAT),                    # B2
    (re.compile(r"\.parameters\.approverIds$"), "changed", APPROVER),           # B2
    (re.compile(r"\.parameters\.calendar\.(value|cachedResultName)$"), "changed", CALENDAR),  # B3
    (re.compile(r"\.parameters\.workflowId\.value$"), "changed", TOOL),         # B4
    (re.compile(r"^settings\.availableInMCP$"), "changed", False),              # C1
    (re.compile(r"^active$"), "changed", False),                                # C2
]


class Report:
    def __init__(self):
        self.lines, self.failed = [], 0

    def add(self, check, status, detail=""):
        if status == "FAIL":
            self.failed += 1
        self.lines.append(f"{status:7} {check:5} {detail}".rstrip())


def flat(obj, prefix=""):
    if isinstance(obj, dict):
        if not obj and prefix:
            yield prefix, {}
        for k, v in obj.items():
            yield from flat(v, f"{prefix}.{k}" if prefix else k)
    elif isinstance(obj, list):
        if not obj and prefix:
            yield prefix, []
        for i, v in enumerate(obj):
            yield from flat(v, f"{prefix}[{i}]")
    else:
        yield prefix, obj


def keyed(wf):
    out = dict(flat({k: v for k, v in wf.items() if k != "nodes"}))
    for node in wf.get("nodes", []):
        out.update(flat(node, f"nodes[{node.get('name')}]"))
    return out


def walk_keys(obj):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield k
            yield from walk_keys(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from walk_keys(v)


def string_values(obj):
    if isinstance(obj, dict):
        for v in obj.values():
            yield from string_values(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from string_values(v)
    elif isinstance(obj, str):
        yield obj


def edges(wf):
    return sum(len(t) for outs in wf.get("connections", {}).values() for o in outs.values() for t in o)


def sensitive_values(src):
    vals = {}

    def add(value, category):
        if value is None:
            return
        value = str(value).strip()
        if value and value not in {SHEET, SHEET_NAME, CHAT, APPROVER, TOOL, NAME, CALENDAR}:
            vals[value] = category

    add(src.get("id"), "workflow id")
    add(src.get("versionId"), "version id")
    add(src.get("meta", {}).get("instanceId"), "instance id")
    add(src.get("settings", {}).get("errorWorkflow"), "error workflow id")
    for tag in src.get("tags") or []:
        add(tag.get("id"), "tag id")
    for node in src.get("nodes", []):
        for cred in (node.get("credentials") or {}).values():
            add(cred.get("id"), "credential id")
        add(node.get("webhookId"), "webhook id")
        p = node.get("parameters", {})
        if isinstance(p.get("documentId"), dict):
            add(p["documentId"].get("value"), "sheet id")
        add(p.get("chatId"), "telegram id")
        add(p.get("approverIds"), "telegram id")
        if isinstance(p.get("calendar"), dict):
            add(p["calendar"].get("value"), "calendar id")
        if isinstance(p.get("workflowId"), dict):
            add(p["workflowId"].get("value"), "sub-workflow id")
    for path, value in flat(src):
        if path.endswith("cachedResultUrl"):
            add(value, "internal url")
    for email in EMAIL.findall(json.dumps(src, ensure_ascii=False)):
        add(email, "e-mail")
    return vals


def repo_files(repo):
    for path in sorted(repo.rglob("*")):
        if path.is_file() and ".git" not in path.relative_to(repo).parts:
            yield path


def name_patterns(tokens):
    return [re.compile(rf"(?<!\w){re.escape(t)}(?!\w)", re.IGNORECASE) for t in tokens]


def check_workflow(rep, rel, wf, src, deny, tool_name):
    name = wf.get("name")
    exp = EXPECT.get(name)
    tag = f"[{rel}]"
    if exp is None:
        rep.add("S6", "FAIL", f"{tag} workflow name is not part of the approved map")
        return

    # S3 allowlist
    problems = []
    if set(wf) - TOP_ALLOWED:
        problems.append(f"top-level keys {sorted(set(wf) - TOP_ALLOWED)}")
    if wf.get("pinData") not in ({}, None):
        problems.append("pinData not empty")
    if wf.get("nodeGroups") not in ([], None):
        problems.append("nodeGroups not empty")
    if wf.get("tags") not in ([], None):
        problems.append("tags not empty")
    if wf.get("meta") not in ({}, None):
        problems.append("meta not empty")
    if set(wf.get("settings", {})) - SETTINGS_ALLOWED:
        problems.append(f"settings keys {sorted(set(wf['settings']) - SETTINGS_ALLOWED)}")
    for node in wf.get("nodes", []):
        extra = set(node) - NODE_ALLOWED
        if extra:
            problems.append(f"node '{node.get('name')}' keys {sorted(extra)}")
    forbidden = sorted(set(walk_keys(wf)) & FORBIDDEN_KEYS)
    if forbidden:
        problems.append(f"forbidden keys present {forbidden}")
    rep.add("S3", "FAIL" if problems else "PASS", f"{tag} " + ("; ".join(problems) if problems else "allowlist of keys respected"))

    # S6 structure
    n_nodes, n_edges = len(wf.get("nodes", [])), edges(wf)
    ok = n_nodes == exp["nodes"] and n_edges == exp["edges"]
    rep.add("S6", "PASS" if ok else "FAIL", f"{tag} nodes {n_nodes}/{exp['nodes']}, edges {n_edges}/{exp['edges']}")
    names = [n.get("name") for n in wf.get("nodes", [])]
    refs = set(re.findall(r"\$\('([^']+)'\)", json.dumps(wf, ensure_ascii=False)))
    missing = sorted(r for r in refs if r not in names)
    rep.add("S6", "FAIL" if missing else "PASS", f"{tag} {len(refs)} $('...') references, unresolved: {missing or 0}")
    if src is not None:
        same = names == [n.get("name") for n in src.get("nodes", [])] and wf.get("connections") == src.get("connections")
        rep.add("S6", "PASS" if same else "FAIL", f"{tag} node names, order and connections identical to source")
    else:
        rep.add("S6", "SKIPPED", f"{tag} comparison with source (no --source)")
    for node in wf.get("nodes", []):
        if node.get("type") == "@n8n/n8n-nodes-langchain.toolWorkflow" and tool_name:
            linked = node.get("parameters", {}).get("workflowId", {}).get("cachedResultName") == tool_name
            rep.add("S6", "PASS" if linked else "FAIL", f"{tag} sub-workflow reference names the TOOL workflow")

    # S7 diff-limited
    if src is not None:
        a, b = keyed(src), keyed(wf)
        patterns = name_patterns(deny)
        bad = []
        for path in sorted(set(a) | set(b)):
            if path in a and path in b and a[path] == b[path]:
                continue
            kind = "removed" if path not in b else "added" if path not in a else "changed"
            allowed = False
            for rx, rule_kind, required in ALLOWED_DIFF:
                if rx.search(path) and rule_kind == kind and (required is None or b.get(path) == required):
                    allowed = True
                    break
            if not allowed and kind == "changed" and isinstance(a[path], str) and patterns:
                rebuilt = a[path]
                for p in patterns:
                    rebuilt = p.sub(NAME, rebuilt)
                allowed = rebuilt == b[path]  # B5: only name tokens replaced
            if not allowed:
                bad.append(f"{kind}:{path}")
        rep.add("S7", "FAIL" if bad else "PASS", f"{tag} " + (f"unexpected differences: {bad}" if bad else "only approved map paths differ from source"))
    else:
        rep.add("S7", "SKIPPED", f"{tag} diff against source (no --source)")

    # S8 flags
    flags_ok = wf.get("active") is False and wf.get("settings", {}).get("availableInMCP") is False
    rep.add("S8", "PASS" if flags_ok else "FAIL", f"{tag} active=false, availableInMCP=false")

    # S9 placeholders
    strings = list(string_values(wf))
    got = {ph: (sum(s.count(ph) for s in strings) if ph == NAME else sum(1 for s in strings if s == ph))
           for ph in exp["placeholders"]}
    cal = sum(1 for n in wf.get("nodes", []) if n.get("type") == "n8n-nodes-base.googleCalendar"
              for k in ("value", "cachedResultName") if n.get("parameters", {}).get("calendar", {}).get(k) == CALENDAR)
    diff = {k: (got[k], v) for k, v in exp["placeholders"].items() if got[k] != v}
    if cal != exp["calendar_primary"]:
        diff["calendar primary"] = (cal, exp["calendar_primary"])
    rep.add("S9", "FAIL" if diff else "PASS", f"{tag} " + (f"count mismatch {diff}" if diff else "placeholder counts match the approved map"))

    # S5 (workflow-specific) n8n-style 16-character ids
    ids = sorted({s for s in strings if re.fullmatch(r"[A-Za-z0-9]{16}", s) and s not in SAFE_16})
    rep.add("S5", "FAIL" if ids else "PASS", f"{tag} 16-character id-like values: {len(ids)}")


def scan_repo(rep, repo, secrets, deny, source_hashes):
    files = list(repo_files(repo))
    patterns = name_patterns(deny)
    findings = {}
    leaked = {}
    identical = []
    for path in files:
        rel = str(path.relative_to(repo))
        raw = path.read_bytes()
        if hashlib.sha256(raw).hexdigest() in source_hashes:
            identical.append(rel)
        text = raw.decode("utf-8", errors="replace")
        hits = []
        for email in EMAIL.findall(text):
            if not email.lower().endswith("@example.com"):
                hits.append("e-mail outside example.com")
        for url in URL.findall(text):
            host = re.sub(r"^https?://", "", url).split("/")[0].split(":")[0].lower()
            if host not in URL_HOSTS_ALLOWED:
                hits.append("url host not allowlisted")
        if LONG_NUMBER.search(text):
            hits.append("number with 7+ digits")
        if IPV4.search(text):
            hits.append("ipv4 address")
        for label, rx in SECRETS.items():
            if rx.search(text):
                hits.append(label)
        if any(p.search(text) for p in patterns):
            hits.append("personal deny token")
        if hits:
            findings[rel] = sorted(set(hits))
        cats = sorted({cat for value, cat in secrets.items() if value in text})
        if cats:
            leaked[rel] = cats
    rep.add("S2b", "FAIL" if identical else ("PASS" if source_hashes else "SKIPPED"),
            f"repository files identical to a private source: {identical or 0}" if source_hashes else "no --source given")
    if secrets:
        rep.add("S4", "FAIL" if leaked else "PASS",
                f"{len(secrets)} source values checked in {len(files)} files" + (f"; found: {leaked}" if leaked else "; none found"))
    else:
        rep.add("S4", "SKIPPED", "no --source given")
    rep.add("S5", "FAIL" if findings else "PASS",
            f"pattern scan of {len(files)} files" + (f"; findings: {findings}" if findings else "; no findings"))


def check_test_data(rep, repo, main_wf):
    emails_file = repo / "test-data" / "synthetic-emails.json"
    csv_file = repo / "test-data" / "sheet-template.csv"
    if not emails_file.exists() or not csv_file.exists():
        rep.add("S10", "FAIL", "test-data files missing")
        return
    data = json.loads(emails_file.read_text(encoding="utf-8"))
    problems = []
    if data.get("synthetic") is not True:
        problems.append("file not flagged synthetic")
    emails = data.get("emails", [])
    ids = [e.get("id") for e in emails]
    if len(ids) != len(set(ids)):
        problems.append("duplicate record ids")
    for e in emails:
        if e.get("synthetic") is not True:
            problems.append(f"{e.get('id')}: not flagged synthetic")
        for field in ("id", "from", "to", "subject", "body", "expected"):
            if field not in e:
                problems.append(f"{e.get('id')}: missing {field}")
        if e.get("duplicate_of") and e["duplicate_of"] not in ids:
            problems.append(f"{e.get('id')}: duplicate_of unknown id")
        for addr in EMAIL.findall(json.dumps(e, ensure_ascii=False)):
            if not addr.lower().endswith("@example.com"):
                problems.append(f"{e.get('id')}: address outside example.com")
    rep.add("S10", "FAIL" if problems else "PASS",
            f"{len(emails)} synthetic e-mails" + (f"; problems: {problems}" if problems else "; all flagged, example.com only"))
    header = next(csv.reader(csv_file.read_text(encoding="utf-8").splitlines()))
    schema = []
    if main_wf is not None:
        for node in main_wf.get("nodes", []):
            if node.get("name") == "Sheets - Log New Email":
                schema = [c.get("id") for c in node["parameters"]["columns"]["schema"]]
    rep.add("S10", "PASS" if header == schema and schema else "FAIL",
            f"sheet-template.csv header ({len(header)} columns) equals the logging schema of the workflow")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", default=".")
    ap.add_argument("--workflow", action="append", default=[])
    ap.add_argument("--source", action="append", default=[], help="private export, same order as --workflow")
    ap.add_argument("--deny", action="append", default=[], help="personal token that must not appear (repeatable)")
    ap.add_argument("--report")
    ap.add_argument("--overwrite", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo).resolve()
    if args.source and len(args.source) != len(args.workflow):
        sys.exit("--source must be given once per --workflow, in the same order")
    rep = Report()
    loaded = []
    secrets, source_hashes = {}, set()
    for i, wf_path in enumerate(args.workflow):
        wf_path = Path(wf_path).resolve()
        wf = json.loads(wf_path.read_text(encoding="utf-8"))
        src = None
        if args.source:
            src_path = Path(args.source[i])
            source_hashes.add(hashlib.sha256(src_path.read_bytes()).hexdigest())
            src = json.loads(src_path.read_text(encoding="utf-8"))
            secrets.update(sensitive_values(src))
        loaded.append((str(wf_path.relative_to(repo)), wf, src))
    tool_name = next((wf["name"] for _, wf, _ in loaded if wf.get("name", "").startswith("📅TOOL")), None)
    for rel, wf, src in loaded:
        check_workflow(rep, rel, wf, src, args.deny, tool_name)
    scan_repo(rep, repo, secrets, args.deny, source_hashes)
    main_wf = next((wf for _, wf, _ in loaded if wf.get("name") == "📧GmailTriage"), None)
    check_test_data(rep, repo, main_wf)

    head = [
        "n8n AI Inbox Triage Demo - validation report",
        f"generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "tool: scripts/validate.py",
        f"workflows: {', '.join(rel for rel, _, _ in loaded)}",
        f"private sources: {len(args.source)} provided for comparison (not part of this repository; paths and hashes not recorded)",
        f"personal deny tokens: {len(args.deny)} provided (values not recorded)",
        "note: automatic checks are not proof that no sensitive data remains; a manual review is required.",
        "",
    ]
    summary = ["", f"result: {'FAIL' if rep.failed else 'PASS'} ({rep.failed} failed checks)"]
    text = "\n".join(head + rep.lines + summary) + "\n"
    print(text, end="")
    if args.report:
        out = Path(args.report)
        if out.exists() and not args.overwrite:
            sys.exit(f"STOP: {out} exists (use --overwrite)")
        out.write_text(text, encoding="utf-8")
    sys.exit(1 if rep.failed else 0)


if __name__ == "__main__":
    main()
