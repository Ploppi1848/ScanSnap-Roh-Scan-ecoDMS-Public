from __future__ import annotations

import html
import os
import importlib.util
import json
import re
import shutil
import csv
import zipfile
from urllib.parse import quote
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Iterable

from fastapi import FastAPI, Form, HTTPException, Request, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse, PlainTextResponse, FileResponse, Response
from fastapi.staticfiles import StaticFiles

APP_VERSION = "4.0.0-alpha Build 16"
BASE_DIR = Path(r"C:\ScanSnap_Roh-Scan-ecoDMS")
SERVICE_DIR = BASE_DIR / "_service"
CONFIG_DIR = BASE_DIR / "_config"
LOG_DIR = BASE_DIR / "_logs"
DEBUG_TEXT_DIR = BASE_DIR / "_debug_text"
TEST_DIR = BASE_DIR / "_web_test"
BOX_CONFIG_FILE = CONFIG_DIR / "box_konfiguration.txt"
ZAEHLER_CONFIG_FILE = CONFIG_DIR / "zaehler.txt"
TEST_ZAEHLER_CONFIG_FILE = CONFIG_DIR / "test_zaehler.txt"
EXPECTED_DIR = TEST_DIR / "_expected"
REPORTS_DIR = TEST_DIR / "_reports"
STATUS_DIR = TEST_DIR / "_status"

# Separater Massentestbereich fuer Altarchiv-Bestaende.
# Wichtig: Dieser Bereich ist bewusst vollstaendig vom Produktivsystem getrennt.
MASSTEST_DIR = BASE_DIR / "_massentest"
MASSTEST_ZIP_DIR = MASSTEST_DIR / "eingang_zip"
MASSTEST_UNPACKED_DIR = MASSTEST_DIR / "entpackt"
MASSTEST_DONE_DIR = MASSTEST_DIR / "verarbeitet"
MASSTEST_ERROR_DIR = MASSTEST_DIR / "fehler"
MASSTEST_LOG_DIR = MASSTEST_DIR / "logs"
MASSTEST_RESULTS_DIR = MASSTEST_DIR / "ergebnisse"
MASSTEST_RESULTS_JSON = MASSTEST_RESULTS_DIR / "massentest_ergebnisse.json"
MASSTEST_RESULTS_CSV = MASSTEST_RESULTS_DIR / "massentest_ergebnisse.csv"
MASSTEST_SNAPSHOT_DIR = MASSTEST_RESULTS_DIR / "snapshots"
# Ab 3.5.8: dauerhafte Referenz-/Sollwertablage.
# Diese Datei darf bei Ergebnis löschen / Reset NICHT entfernt werden.
MASSTEST_REFERENCES_JSON = MASSTEST_RESULTS_DIR / "massentest_sollwerte.json"
MASSTEST_PROGRESS_JSON = MASSTEST_RESULTS_DIR / "massentest_fortschritt.json"
DATEINAME_CONFIG_FILE = CONFIG_DIR / "dateiname_konfiguration.txt"

FOLDERS = {
    "Scan-Eingang": BASE_DIR / "ecodms_scan_input",
    "Mail-Eingang": BASE_DIR / "mail_input",
    "Arbeit": BASE_DIR / "_arbeit",
    "Erledigt": BASE_DIR / "_erledigt",
    "Fehler": BASE_DIR / "_fehler",
    "Gefiltert": BASE_DIR / "_gefiltert",
}

FOLDER_NOTES = {
    "ecodms_scan_input": "Eingangsordner ohne Unterstrich",
    "mail_input": "Eingangsordner ohne Unterstrich",
}

CONFIG_FILES = [
    "box_konfiguration.txt",
    "zaehler.txt",
    "test_zaehler.txt",
    "lieferanten_konfiguration.txt",
    "dokumenttypen_konfiguration.txt",
    "felder_konfiguration.txt",
    "meta_konfiguration.txt",
    "import_optionen_konfiguration.txt",
    "dateiname_konfiguration.txt",
    "dokumentfilter_konfiguration.txt",
    "benachrichtigung_konfiguration.txt",
]
LEARNING_FILES = {
    "lieferanten": {
        "learn": "lieferanten_lernliste.txt",
        "target": "lieferanten_konfiguration.txt",
        "label": "Lieferanten-Lernliste",
    },
    "dokumenttypen": {
        "learn": "dokumenttypen_lernliste.txt",
        "target": "dokumenttypen_konfiguration.txt",
        "label": "Dokumenttypen-Lernliste",
    },
}
LOG_FILES = ["ecodms_scan_service.log", "outlook_mail_watcher.log"]


def ensure_dirs() -> None:
    """Legt alle von der WebUI verwendeten Standardordner an.

    Diese Funktion war in 2.7.32/2.7.33 versehentlich nicht mehr vorhanden,
    wurde aber von Dashboard, Testcenter, Logs und Projektcenter aufgerufen.
    """
    for p in [
        BASE_DIR, SERVICE_DIR, CONFIG_DIR, LOG_DIR, DEBUG_TEXT_DIR,
        TEST_DIR, EXPECTED_DIR, REPORTS_DIR, STATUS_DIR, MASSTEST_DIR, MASSTEST_ZIP_DIR, MASSTEST_UNPACKED_DIR, MASSTEST_DONE_DIR, MASSTEST_ERROR_DIR, MASSTEST_LOG_DIR, MASSTEST_RESULTS_DIR, MASSTEST_SNAPSHOT_DIR, *FOLDERS.values()
    ]:
        try:
            p.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass

def list_log_files() -> list[str]:
    """Alle auswählbaren Logdateien aus _logs ermitteln, auch in Unterordnern."""
    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        files = []
        for p in LOG_DIR.rglob("*"):
            if p.is_file() and p.suffix.lower() in {".log", ".txt", ".csv"}:
                try:
                    files.append(p.relative_to(LOG_DIR).as_posix())
                except Exception:
                    files.append(p.name)
        known = [x for x in LOG_FILES if x in files or (LOG_DIR / x).exists()]
        rest = sorted([x for x in files if x not in known], key=str.lower)
        out = known + rest
        # Massentest-Log liegt bewusst im getrennten Massentestbereich,
        # soll aber zentral im Bereich „Logs“ auswählbar sein.
        try:
            if (MASSTEST_LOG_DIR / "massentest.log").exists():
                out.append("Massentest/massentest.log")
        except Exception:
            pass
        return out
    except Exception:
        return LOG_FILES


def read_text(path: Path, max_chars: int | None = None) -> str:
    if not path.exists():
        return ""
    data = path.read_text(encoding="utf-8", errors="replace")
    return data[-max_chars:] if max_chars else data


def write_text_backup(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup = path.with_suffix(path.suffix + f".{stamp}.bak")
        shutil.copy2(path, backup)
    path.write_text(content.replace("\r\n", "\n"), encoding="utf-8")


def esc(s: object) -> str:
    return html.escape(str(s or ""))


def render_navbar(active: str = "") -> str:
    """Zentrale Hauptnavigation fuer WebUI 4.0 Final.

    Bestehende Routen bleiben erhalten; die Navigation ordnet sie nur klarer.
    """
    active_norm = (active or "").strip().lower()
    items = [
        ("/", "Dashboard", "dashboard"),
        ("/projekt", "Projekt", "projektcenter"),
        ("/regression", "Produktiv", "produktivcenter"),
        ("/test", "Dokumentenprüfung", "qualitaetscenter"),
        ("/config", "Einstellungen", "einstellungen"),
    ]
    links = []
    for href, label, key in items:
        classes = []
        if key == active_norm:
            classes.append("active")
        class_attr = f' class="{" ".join(classes)}"' if classes else ""
        links.append(f'<a{class_attr} href="{href}">{label}</a>')
    return "".join(links)


def render_message_box(text: str, title: str = "", kind: str = "info", small: bool = False) -> str:
    """Einheitliche Hinweisbox als kuenftiger Ersatz fuer verstreute flash/hint-Bloecke."""
    text = str(text or "").strip()
    if not text:
        return ""
    kind_norm = (kind or "info").strip().lower()
    if kind_norm not in {"info", "success", "warning", "danger"}:
        kind_norm = "info"
    title_html = f"<b>{esc(title)}</b><br>" if str(title or "").strip() else ""
    size_class = " small" if small else ""
    return f"<div class='message-box message-{kind_norm}{size_class}'>{title_html}{esc(text)}</div>"


def webui_active_nav_key(title: str) -> str:
    title_norm = (title or "").strip().lower()
    if title_norm in {"dashboard"}:
        return "dashboard"
    if "projekt" in title_norm or "aufgaben" in title_norm:
        return "projektcenter"
    if any(x in title_norm for x in ["massentest", "qualitätscenter", "qualitaetscenter", "qualität", "qualitaet", "dokumentenprüfung", "dokumentenpruefung", "fachliche validierung", "testcenter", "testergebnis", "regressionstest", "sollwerte"]):
        return "qualitaetscenter"
    if any(x in title_norm for x in ["regressionen", "produktiv"]):
        return "produktivcenter"
    if any(x in title_norm for x in ["einstellungen", "konfiguration", "import-optionen", "pdf-dateinamen", "benachrichtigung"]):
        return "einstellungen"
    if "lernlisten" in title_norm:
        return "einstellungen"
    if "logs" in title_norm:
        return "einstellungen"
    if any(x in title_norm for x in ["ablage", "zähler", "zaehler", "wartung", "system"]):
        return "einstellungen"
    return ""


def render_area_badges(title: str) -> str:
    title_norm = (title or "").strip().lower()
    badges = [("ALPHA", "alpha")]
    if any(x in title_norm for x in ["testcenter", "testergebnis", "regressionstest", "sollwerte"]):
        badges.append(("TEST", "test"))
    if any(x in title_norm for x in ["massentest", "qualitätscenter", "qualitaetscenter", "dokumentenprüfung", "dokumentenpruefung", "fachliche validierung"]):
        badges.append(("TEST", "test"))
        badges.append(("Massentest", "massentest"))
    if any(x in title_norm for x in ["regressionen", "produktiv"]):
        badges.append(("PRODUKTIV", "produktiv"))
        badges.append(("Regression", "regression"))
    # Reihenfolge beibehalten, aber Dubletten vermeiden.
    seen: set[str] = set()
    parts = []
    for label, kind in badges:
        key = label.lower()
        if key in seen:
            continue
        seen.add(key)
        parts.append(f"<span class='area-badge badge-{kind}'>{esc(label)}</span>")
    return "".join(parts)


def layout(title: str, body: str) -> HTMLResponse:
    nav = render_navbar(webui_active_nav_key(title))
    area_badges = render_area_badges(title)
    css = """
    <style>
    :root{--bg:#edf2f7;--card:#fff;--text:#111827;--muted:#64748b;--line:#e5e7eb;--primary:#2563eb;--primary2:#dbeafe;--danger:#dc2626;--warn:#d97706;--ok:#16a34a;--dark:#0f172a;--shadow:0 14px 34px rgba(15,23,42,.09)}
    *{box-sizing:border-box}html{scroll-behavior:smooth}body{font-family:Segoe UI,Arial,sans-serif;margin:0;background:linear-gradient(180deg,#f8fafc 0%,var(--bg) 100%);color:var(--text)}
    .top{background:radial-gradient(circle at top left,#1d4ed8,#0f172a 55%,#020617);color:white;padding:24px 32px}.top h1{margin:0;font-size:24px;letter-spacing:.2px}.top .muted{color:#cbd5e1}.top-line{display:flex;align-items:flex-start;justify-content:space-between;gap:16px;flex-wrap:wrap}.area-badges{display:flex;gap:7px;flex-wrap:wrap;justify-content:flex-end}.area-badge{display:inline-flex;align-items:center;border-radius:999px;padding:5px 10px;font-size:12px;font-weight:950;letter-spacing:.04em;border:1px solid rgba(255,255,255,.28);background:rgba(255,255,255,.12);color:white}.badge-alpha{background:#312e81}.badge-test{background:#9a3412}.badge-produktiv{background:#14532d}.badge-massentest{background:#1e40af}.badge-regression{background:#6d28d9}
    .nav{background:rgba(255,255,255,.94);backdrop-filter:blur(10px);padding:12px 30px;border-bottom:1px solid var(--line);position:sticky;top:0;z-index:10;display:flex;gap:6px;flex-wrap:wrap}.nav a{color:#1e40af;text-decoration:none;font-weight:800;padding:9px 13px;border-radius:999px}.nav a:hover{background:var(--primary2)}.nav a.active{background:#1d4ed8;color:white;box-shadow:0 6px 16px rgba(29,78,216,.18)}.nav a.nav-secondary{color:#64748b;background:#f8fafc;border:1px solid #e2e8f0}.nav a.nav-secondary.active{background:#475569;color:white;border-color:#475569}
    .wrap{padding:24px;max-width:1280px;margin:0 auto}.card{background:var(--card);border:1px solid var(--line);border-radius:20px;padding:20px;margin:0 0 18px 0;box-shadow:var(--shadow)}.hero{display:grid;grid-template-columns:1.2fr .8fr;gap:18px}.metric{background:linear-gradient(180deg,#fff,#f8fafc);border:1px solid var(--line);border-radius:18px;padding:18px}.metric .num{font-size:30px;font-weight:900;margin:4px 0}.metric .label{color:var(--muted);font-weight:700}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:14px}.ok{color:var(--ok);font-weight:900}.bad{color:var(--danger);font-weight:900}.warntext{color:var(--warn);font-weight:900}.muted{color:var(--muted)}h2{margin-top:0}.btn,.btn2{border:0;border-radius:12px;padding:9px 13px;text-decoration:none;display:inline-flex;align-items:center;gap:6px;cursor:pointer;font-weight:800;line-height:1.2;justify-content:center}.btn{background:var(--primary);color:white}.btn:hover,.btn2:hover{filter:brightness(.97)}.btn2{background:#f8fafc;color:#1e40af;border:1px solid #c7d2fe}.btn-primary,.btn.save,.btn.apply{background:#16a34a;color:white}.btn-nav,.btn.open,.btn.edit{background:#2563eb;color:white}.btn-warning,.btn.warn,.btn2.warn,.warn{background:#fef3c7;color:#92400e;border-color:#fde68a}.btn-danger,.btn.danger,.btn2.danger,.danger{background:#fee2e2;color:#991b1b;border-color:#fecaca}.btn-secondary,.btn2.secondary{background:#f8fafc;color:#334155;border:1px solid #cbd5e1}.success,.btn.success,.btn2.success{background:#dcfce7;color:#166534;border-color:#bbf7d0}
    .dashboard-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:18px;align-items:stretch}.dashboard-card{display:flex;flex-direction:column;min-height:220px}.dashboard-card .dashboard-grow{flex:1}.dashboard-card .dashboard-actions{margin-top:auto;padding-top:14px}.counter-pair{display:grid;grid-template-columns:repeat(auto-fit,minmax(360px,1fr));gap:18px;margin-bottom:18px}.hub-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:18px}.hub-card{display:flex!important;flex-direction:column;min-height:170px}.hub-card .hub-action{margin-top:auto;padding-top:12px}
    .settings-page{display:grid;gap:14px}.settings-section{background:#fff;border:1px solid #dbe3ef;border-radius:18px;box-shadow:0 8px 24px rgba(15,23,42,.055);overflow:hidden}.settings-section>summary{cursor:pointer;list-style:none;padding:16px 18px;display:flex;align-items:center;justify-content:space-between;gap:12px;font-weight:950}.settings-section>summary::-webkit-details-marker{display:none}.settings-section>summary:after{content:'⌄';color:#64748b;font-size:18px}.settings-section[open]>summary:after{content:'⌃'}.settings-title{display:flex;align-items:center;gap:10px}.settings-icon{width:24px;height:24px;border-radius:8px;display:inline-flex;align-items:center;justify-content:center;background:#eff6ff;color:#2563eb;font-weight:950}.settings-badge{border-radius:999px;padding:4px 9px;font-size:12px;font-weight:950;background:#eef2ff;color:#3730a3}.settings-badge.info{background:#f1f5f9;color:#475569}.settings-badge.maintenance{background:#f3e8ff;color:#6d28d9}.settings-badge.care{background:#dbeafe;color:#1e40af}.settings-body{padding:0 18px 18px}.settings-card-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:14px}.settings-mini-card{border:1px solid #dbe3ef;border-radius:14px;background:#fff;padding:14px;min-height:112px;display:flex;flex-direction:column;gap:8px}.settings-mini-card .settings-actions{margin-top:auto}.settings-mini-card h3{font-size:15px;margin:0}.settings-counter-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(360px,1fr));gap:14px}.settings-counter{border:1px solid #dbe3ef;border-radius:16px;padding:14px;background:#fff;display:flex;flex-direction:column;min-height:250px}.settings-counter.productive{border-left:6px solid #2563eb;background:linear-gradient(180deg,#eff6ff,#fff)}.settings-counter.test{border-left:6px solid #f97316;background:linear-gradient(180deg,#fff7ed,#fff)}.settings-counter-head{display:flex;align-items:center;justify-content:space-between;gap:10px;margin-bottom:12px}.settings-counter-head h3{margin:0;font-size:17px}.settings-counter-fields{display:grid;grid-template-columns:minmax(180px,.92fr) minmax(180px,1fr);gap:14px;align-items:start}.settings-counter-side{display:grid;gap:0}.settings-line{display:grid;grid-template-columns:minmax(95px,.75fr) minmax(80px,1fr);gap:10px;align-items:center;padding:9px 0;border-bottom:1px solid #e5e7eb}.settings-line:last-child{border-bottom:0}.settings-line label,.settings-line .settings-label{font-weight:850}.settings-line small{display:block;color:#64748b;font-weight:500;line-height:1.2}.settings-line input{width:100%;min-width:0}.settings-line-value{font-weight:850;overflow-wrap:anywhere}.settings-preview{display:flex;gap:12px;align-items:center;border-radius:14px;padding:12px;margin-top:auto;font-family:Consolas,monospace;font-weight:950;font-size:18px}.settings-preview small{font-family:Segoe UI,Arial,sans-serif;font-size:12px;font-weight:850}.settings-preview.productive{background:#eff6ff;color:#1d4ed8}.settings-preview.test{background:#fff7ed;color:#ea580c}.settings-preview-symbol{font-family:Segoe UI,Arial,sans-serif;font-size:25px;line-height:1}.settings-folder-table{overflow:auto}.settings-folder-table table{min-width:720px}@media(max-width:768px){.settings-counter-grid{grid-template-columns:1fr}.settings-counter-fields{grid-template-columns:1fr}.settings-card-grid{grid-template-columns:1fr}.settings-section>summary{align-items:flex-start}.settings-title{align-items:flex-start}}
    textarea{width:100%;height:62vh;font-family:Consolas,monospace;font-size:14px;border:1px solid var(--line);border-radius:14px;padding:12px}.logbox{white-space:pre-wrap;background:#0b1220;color:#dbeafe;padding:14px;border-radius:14px;overflow:auto;height:67vh;font-family:Consolas,monospace;font-size:13px;line-height:1.45;border:1px solid #1e293b}.logline.info{color:#dbeafe}.logline.warning{color:#fde68a}.logline.error{color:#fecaca;font-weight:900}pre{white-space:pre-wrap;background:#0f172a;color:#e5e7eb;padding:14px;border-radius:14px;overflow:auto;max-height:65vh}table{border-collapse:collapse;width:100%}th,td{border-bottom:1px solid #eef2f7;text-align:left;padding:10px;vertical-align:top}.pill{padding:4px 9px;border-radius:999px;background:#eef2ff;display:inline-block}.folder-name{font-family:Consolas,monospace;font-weight:900}.folder-note{display:inline-block;margin-left:8px;padding:3px 8px;border-radius:999px;background:#f1f5f9;color:#475569;font-size:12px}.small{font-size:13px}input[type=text],input[type=number],select,input[type=file]{padding:9px 10px;border:1px solid #d0d5dd;border-radius:10px;background:white}.checkrow{display:block;padding:12px;border-bottom:1px solid #eef2f7}.checkrow input{transform:scale(1.15);margin-right:8px}.fieldrow{display:grid;grid-template-columns:260px 1fr;gap:12px;align-items:center;padding:12px;border-bottom:1px solid #eef2f7}.fieldrow small{display:block;color:var(--muted);font-weight:400;margin-top:3px}.fieldrow input{width:100%}.flash{background:#eff6ff;border-left:4px solid var(--primary);padding:12px;margin-bottom:12px;border-radius:12px}.message-box{background:#eff6ff;border:1px solid #bfdbfe;border-left:5px solid #2563eb;border-radius:14px;padding:12px;margin-bottom:12px;color:#1e3a8a}.message-success{background:#ecfdf5;border-color:#bbf7d0;border-left-color:#16a34a;color:#166534}.message-warning{background:#fffbeb;border-color:#fde68a;border-left-color:#d97706;color:#92400e}.message-danger{background:#fef2f2;border-color:#fecaca;border-left-color:#dc2626;color:#991b1b}.learn-list{display:grid;gap:12px}.learn-item{border:1px solid var(--line);border-radius:16px;background:#fbfdff;padding:14px;display:grid;grid-template-columns:1fr auto;gap:14px;align-items:center}.learn-title{font-weight:900;margin-bottom:6px}.learn-fields{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:8px;margin-top:8px}.learn-field{background:#f8fafc;border:1px solid #e2e8f0;border-radius:12px;padding:9px}.learn-field span{display:block;color:#64748b;font-size:12px;font-weight:800;text-transform:uppercase;letter-spacing:.04em}.learn-field b{display:block;margin-top:3px;word-break:break-word}.learn-raw{font-family:Consolas,monospace;background:#f1f5f9;border:1px solid #e2e8f0;border-radius:10px;padding:8px;color:#334155}.learn-actions{display:flex;flex-wrap:wrap;gap:8px;justify-content:flex-end}.learn-actions form{display:inline-flex;gap:7px;align-items:center}.learn-actions input[type=text]{min-width:220px}.section-head{display:flex;align-items:center;justify-content:space-between;gap:12px}.count-badge{background:#eef2ff;color:#3730a3;border-radius:999px;padding:5px 10px;font-weight:900;font-size:12px}.hint{background:#f8fafc;border:1px dashed #cbd5e1;border-radius:14px;padding:12px}.toolbar{display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin:8px 0 12px}.toolbar.nowrap,.test-actions.nowrap{flex-wrap:nowrap;overflow-x:visible;white-space:nowrap}.toolbar.nowrap form,.test-actions.nowrap form{display:inline-flex;flex:0 0 auto}.toolbar.nowrap .btn,.toolbar.nowrap .btn2,.test-actions.nowrap .btn,.test-actions.nowrap .btn2{flex:0 0 auto;padding:7px 9px;font-size:12.5px}.mini-actions{display:inline-flex;gap:6px;align-items:center;margin-left:6px}.mini-actions .btn2{padding:5px 7px;font-size:11.5px}.btn-sub{display:block;font-size:11px;font-weight:700;opacity:.82;line-height:1.05;margin-top:2px}.btn-stack{display:inline-flex;flex-direction:column;align-items:center;gap:0}.resultbar{display:flex;gap:8px;align-items:center;flex-wrap:nowrap;overflow:visible;white-space:nowrap}.resultbar form{display:inline-flex}.resultbar .spacer{flex:1}.kbd{font-family:Consolas,monospace;background:#e2e8f0;border-radius:6px;padding:2px 6px;font-size:12px}.config-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:14px}.config-card{background:linear-gradient(180deg,#ffffff,#f8fafc);border:1px solid var(--line);border-radius:18px;padding:16px;box-shadow:0 8px 22px rgba(15,23,42,.055)}.config-card h3{margin:0 0 6px 0}.config-card p{margin:6px 0}.config-actions{display:flex;gap:8px;flex-wrap:wrap;margin-top:12px}.top-actions{position:sticky;top:58px;z-index:8;background:rgba(255,255,255,.92);backdrop-filter:blur(8px);border:1px solid var(--line);border-radius:16px;padding:10px;margin-bottom:14px;display:flex;gap:8px;align-items:center;justify-content:space-between;flex-wrap:wrap}.soft-title{font-size:14px;text-transform:uppercase;letter-spacing:.08em;color:#64748b;font-weight:900;margin:18px 0 10px}.file-path{font-size:12px;color:#64748b;font-family:Consolas,monospace;word-break:break-all}.copyarea{width:100%;height:220px;font-family:Consolas,monospace;font-size:13px;background:#f8fafc;color:#0f172a;border:1px solid #cbd5e1;border-radius:14px;padding:12px}.legend{display:flex;gap:8px;flex-wrap:wrap;margin:12px 0}.legend span{display:inline-flex;align-items:center;gap:6px;border:1px solid #dbe3ef;background:#f8fafc;border-radius:999px;padding:6px 10px;font-weight:800;font-size:13px}.status-symbol{font-size:18px;font-weight:900;display:inline-block;min-width:24px}.row-current{background:#e0f2fe}.row-expected{background:#f0fdf4;color:#166534}.row-missing{background:#fef9c3}.row-untested{background:#fff}.done-box{border-left:6px solid #16a34a;background:linear-gradient(180deg,#ffffff,#f0fdf4);opacity:.82}.open-box{border-left:6px solid #d97706}.active-filter-note{background:#eff6ff;border:1px solid #bfdbfe;border-radius:14px;padding:10px;margin-bottom:12px;color:#1e3a8a;font-weight:700}.progress-wrap{height:14px;background:#e5e7eb;border-radius:999px;overflow:hidden;border:1px solid #cbd5e1}.progress-bar{height:100%;background:#60a5fa}
    .working-overlay{display:none;position:fixed;inset:0;background:rgba(15,23,42,.38);backdrop-filter:blur(2px);z-index:9999;align-items:center;justify-content:center}.working-box{background:white;border:1px solid var(--line);border-radius:20px;padding:22px 26px;box-shadow:var(--shadow);display:flex;gap:14px;align-items:center;max-width:420px}.spinner{width:32px;height:32px;border:4px solid #dbeafe;border-top-color:#2563eb;border-radius:50%;animation:spin .8s linear infinite}@keyframes spin{to{transform:rotate(360deg)}}.working-title{font-weight:900}.working-sub{color:var(--muted);font-size:13px;margin-top:3px}

    .learn-item{border:1px solid #dbe3ef;border-radius:22px;background:linear-gradient(180deg,#ffffff,#f8fafc);padding:18px;display:grid;grid-template-columns:minmax(0,1fr) auto;gap:18px;align-items:start;box-shadow:0 10px 26px rgba(15,23,42,.065)}
    .learn-item.suspect{border-color:#fde68a;background:linear-gradient(180deg,#fff,#fffbeb)}
    .learn-title{font-size:20px;font-weight:950;margin:0 0 8px 0;line-height:1.2;color:#0f172a}.learn-subtitle{color:#64748b;font-weight:700;margin-bottom:10px}.learn-kind-pill{display:inline-flex;align-items:center;gap:6px;border-radius:999px;padding:5px 10px;background:#eef2ff;color:#3730a3;font-weight:900;font-size:12px;text-transform:uppercase;letter-spacing:.04em}.learn-source{display:inline-flex;align-items:center;gap:6px;border-radius:999px;padding:5px 10px;background:#f1f5f9;color:#334155;font-weight:800;font-size:12px;margin-left:6px}.learn-actions{display:flex;flex-direction:column;gap:10px;min-width:260px}.learn-actions form{display:flex;gap:8px;align-items:center}.learn-actions input[type=text]{width:100%;min-width:230px;border-radius:12px}.actionbar{display:flex;gap:8px;flex-wrap:wrap}.action-btn{border:0;border-radius:14px;padding:10px 13px;text-decoration:none;display:inline-flex;align-items:center;gap:7px;cursor:pointer;font-weight:950;line-height:1.1;box-shadow:0 8px 18px rgba(15,23,42,.08);transition:transform .12s ease,filter .12s ease}.action-btn:hover{transform:translateY(-1px);filter:brightness(.98)}.action-accept{background:linear-gradient(135deg,#16a34a,#22c55e);color:white}.action-ignore{background:linear-gradient(135deg,#f59e0b,#facc15);color:#422006}.action-delete{background:linear-gradient(135deg,#ef4444,#dc2626);color:white}.action-add{background:linear-gradient(135deg,#2563eb,#3b82f6);color:white}.learn-valuebox{border:1px solid #dbe3ef;background:white;border-radius:16px;padding:12px;margin-top:10px}.learn-valuebox .caption{font-size:12px;font-weight:900;color:#64748b;text-transform:uppercase;letter-spacing:.06em}.learn-valuebox .value{font-size:18px;font-weight:950;margin-top:4px;word-break:break-word}.learn-empty{border:1px dashed #cbd5e1;background:#f8fafc;border-radius:18px;padding:18px;color:#64748b;font-weight:800}.learning-intro{background:linear-gradient(135deg,#eff6ff,#ffffff);border-left:6px solid #2563eb}.mini-help{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:10px;margin-top:12px}.mini-help div{background:#fff;border:1px solid #dbe3ef;border-radius:15px;padding:12px}.mini-help b{display:block;margin-bottom:4px}


    .counter-split{display:grid;grid-template-columns:1fr;gap:12px;margin:12px 0}.counter-card{border-radius:18px;padding:14px 15px;border:1px solid #dbe3ef;background:#f8fafc}.counter-card .counter-head{display:flex;justify-content:space-between;align-items:center;gap:8px;margin-bottom:8px}.counter-card .counter-title{font-size:13px;text-transform:uppercase;letter-spacing:.08em;font-weight:950}.counter-card .counter-code{font-family:Consolas,monospace;font-size:16px;font-weight:950;word-break:break-all}.counter-card .counter-sub{font-size:12px;color:#64748b;margin-top:5px}.counter-card.productive{background:linear-gradient(180deg,#eff6ff,#ffffff);border-left:7px solid #2563eb}.counter-card.test{background:linear-gradient(180deg,#fff7ed,#ffffff);border-left:7px solid #f97316}.counter-badge{border-radius:999px;padding:4px 9px;font-size:12px;font-weight:950}.counter-badge.productive{background:#dbeafe;color:#1e40af}.counter-badge.test{background:#ffedd5;color:#9a3412}.counter-form-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:16px;margin-top:14px}.counter-form-card{border:1px solid #dbe3ef;border-radius:20px;padding:16px;background:#fff;box-shadow:0 8px 22px rgba(15,23,42,.045)}.counter-form-card.productive{border-left:7px solid #2563eb;background:linear-gradient(180deg,#eff6ff,#fff)}.counter-form-card.test{border-left:7px solid #f97316;background:linear-gradient(180deg,#fff7ed,#fff)}.counter-form-card h3{margin-top:0}.test-note{background:#fff7ed;border:1px solid #fed7aa;border-radius:14px;padding:10px;color:#9a3412;font-weight:800}

    .test-steps{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:10px;margin:12px 0}.test-steps div{background:#f8fafc;border:1px solid #dbe3ef;border-radius:14px;padding:10px;font-weight:800}.test-steps b{display:inline-flex;align-items:center;justify-content:center;width:24px;height:24px;border-radius:999px;background:#dbeafe;color:#1e40af;margin-right:6px}
    .result-grid{display:grid;grid-template-columns:1fr;gap:14px}.result-card{border:1px solid #e5e7eb;border-radius:16px;padding:14px;background:#fff}
    .workflow-bar{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:10px;margin:14px 0}.workflow-step{border:1px solid #dbe3ef;background:#f8fafc;border-radius:16px;padding:12px}.workflow-step b{display:block;color:#1e40af;margin-bottom:4px}.workflow-step.current{background:#eff6ff;border-color:#93c5fd;box-shadow:0 0 0 3px rgba(37,99,235,.08)}.workflow-step.done{background:#ecfdf5;border-color:#86efac}.workflow-step.done b{color:#166534}.workflow-step.pending{background:#f8fafc;border-color:#dbe3ef;opacity:.92}.workflow-step.blocked{background:#fff7ed;border-color:#fed7aa}.workflow-step.blocked b{color:#9a3412}.test-panel{border:1px solid var(--line);border-radius:18px;padding:12px;margin:8px 0;background:#fff}.test-panel.compact h3{font-size:16px;margin-bottom:4px}.test-start-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:10px;margin:10px 0 12px}.test-top-status{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:8px;margin:8px 0}.test-top-status .metric{padding:12px;border-radius:14px}.test-top-status .metric .num{font-size:24px}.test-focus-anchor{scroll-margin-top:95px}.test-panel h3{margin:0 0 8px 0}.sticky-workbar{position:sticky;top:58px;z-index:9;background:rgba(255,255,255,.96);backdrop-filter:blur(8px);border:1px solid var(--line);border-radius:18px;padding:12px;margin-bottom:14px;box-shadow:0 10px 26px rgba(15,23,42,.07)}.mini-tag{display:inline-flex;align-items:center;gap:6px;border-radius:999px;padding:5px 10px;font-size:12px;font-weight:900;background:#eef2ff;color:#3730a3}.result-focus{border:2px solid #bfdbfe}.test-actions{display:flex;gap:8px;flex-wrap:wrap;align-items:center}.workflow-note{background:#f8fafc;border:1px dashed #cbd5e1;border-radius:14px;padding:10px;margin:10px 0;color:#475569;font-size:13px}

    .project-task-card{display:grid;grid-template-columns:72px minmax(0,1fr) minmax(190px,230px);gap:14px;align-items:start;max-width:100%;overflow:hidden}.project-task-main{min-width:0;overflow-wrap:anywhere;word-break:break-word}.project-task-note{max-height:190px;overflow:auto;background:#f8fafc;border:1px solid #e2e8f0;border-radius:12px;padding:10px}.project-task-actions{min-width:0;display:flex;flex-direction:column;gap:8px}.project-task-actions form{width:100%}.project-task-actions button,.project-task-actions select{width:100%}.created-backbar{display:flex;gap:8px;align-items:center;justify-content:space-between;flex-wrap:wrap;background:#ecfdf5;border:1px solid #bbf7d0;border-left:6px solid #16a34a;border-radius:16px;padding:12px;margin-bottom:14px}.test-summary-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:10px;margin:12px 0}.test-summary-tile{border:1px solid #dbe3ef;background:#f8fafc;border-radius:16px;padding:12px}.test-summary-tile b{display:block;font-size:22px}.test-doc-sections{display:grid;gap:12px}.test-doc-section{border:1px solid #dbe3ef;border-radius:18px;background:#fff;overflow:hidden}.test-doc-section summary{cursor:pointer;padding:14px 16px;font-weight:950;background:#f8fafc}.test-doc-section.open-priority summary{background:#fff7ed;color:#9a3412}.test-doc-section table{margin:0}.test-table-wrap{overflow-x:visible;max-width:100%}.test-table-compact{table-layout:fixed;width:100%}.test-table-compact th,.test-table-compact td{padding:8px;font-size:13px;overflow-wrap:anywhere;word-break:break-word}.test-table-compact td:last-child{min-width:0}.test-table-compact .btn,.test-table-compact .btn2{padding:7px 9px;font-size:12px;margin-bottom:4px}.massentest-filelink{color:#0f172a;text-decoration:none}.massentest-filelink:hover{text-decoration:underline;color:#1d4ed8}.massentest-actions{display:flex;flex-wrap:wrap;gap:8px;align-items:center}.task-badge{display:inline-block;background:#eef2ff;color:#3730a3;border:1px solid #c7d2fe;border-radius:999px;padding:3px 8px;font-weight:950;text-decoration:none;margin-top:4px}.massentest-statuscell{max-width:260px}.massentest-action-row td{padding-top:6px;padding-bottom:10px}


    /* WebUI 3.3.7: Massentest-Pruefliste als Kartenlayout statt breiter Tabelle */
    .test-doc-sections .test-table-wrap{overflow-x:hidden!important;width:100%}
    .test-doc-sections table.test-table-compact,
    .test-doc-sections table.test-table-compact tbody,
    .test-doc-sections table.test-table-compact tr,
    .test-doc-sections table.test-table-compact td{display:block!important;width:100%!important;box-sizing:border-box!important}
    .test-doc-sections table.test-table-compact th{display:none!important}
    .test-doc-sections table.test-table-compact tr.massentest-main-row{border-top:1px solid #e5e7eb;padding:12px 12px 2px 12px;display:grid!important;grid-template-columns:minmax(220px,1.7fr) minmax(80px,.45fr) minmax(140px,.75fr) minmax(110px,.55fr) minmax(180px,1fr);gap:10px;align-items:start;overflow-wrap:anywhere;word-break:break-word}
    .test-doc-sections table.test-table-compact tr.massentest-action-row{display:block!important;border-bottom:1px solid #fde68a;padding:0 12px 12px 12px}
    .test-doc-sections table.test-table-compact tr.massentest-action-row td{padding:0!important;border-bottom:0!important}
    .test-doc-sections table.test-table-compact tr.massentest-main-row td{border-bottom:0!important;padding:4px!important;min-width:0!important;max-width:100%!important;overflow-wrap:anywhere!important;word-break:break-word!important}
    .test-doc-sections table.test-table-compact tr.massentest-main-row td:last-child{display:none!important}
    .massentest-filecell{font-size:13px;line-height:1.35}
    .massentest-actions{display:flex!important;flex-wrap:wrap!important;gap:8px!important;overflow:visible!important;max-width:100%!important;white-space:normal!important}
    .massentest-actions form,.massentest-actions a{display:inline-flex!important;max-width:100%}
    .massentest-actions .btn2,.massentest-actions .btn{white-space:normal!important;text-align:center!important;line-height:1.15}
    .massentest-statuscell{max-width:100%!important;font-size:12.5px;line-height:1.35}
    @media (max-width:900px){.test-doc-sections table.test-table-compact tr.massentest-main-row{grid-template-columns:1fr!important}.test-doc-sections table.test-table-compact tr.massentest-main-row td:not(:first-child)::before{display:inline-block;font-weight:900;color:#64748b;margin-right:6px}.test-doc-sections table.test-table-compact tr.massentest-main-row td:nth-child(2)::before{content:'Größe:'}.test-doc-sections table.test-table-compact tr.massentest-main-row td:nth-child(3)::before{content:'Geändert:'}.test-doc-sections table.test-table-compact tr.massentest-main-row td:nth-child(4)::before{content:'Sollwerte:'}.test-doc-sections table.test-table-compact tr.massentest-main-row td:nth-child(5)::before{content:'Status:'}}

    .eco-modal-backdrop{display:none;position:fixed;inset:0;background:rgba(15,23,42,.46);backdrop-filter:blur(3px);z-index:10000;align-items:center;justify-content:center;padding:18px}.eco-modal{max-width:560px;width:100%;background:#fff;border:1px solid #dbe3ef;border-radius:22px;box-shadow:0 28px 70px rgba(15,23,42,.28);overflow:hidden}.eco-modal-head{padding:18px 20px;background:linear-gradient(135deg,#eff6ff,#ffffff);border-bottom:1px solid #e5e7eb}.eco-modal-title{font-size:20px;font-weight:950;color:#0f172a;margin:0}.eco-modal-body{padding:18px 20px;color:#334155;line-height:1.45}.eco-modal-message{font-weight:850;color:#0f172a;margin-bottom:10px}.eco-modal-details{background:#f8fafc;border:1px solid #e2e8f0;border-radius:14px;padding:12px;font-size:13px;white-space:pre-wrap}.eco-modal-actions{display:flex;gap:10px;justify-content:flex-end;padding:16px 20px;background:#f8fafc;border-top:1px solid #e5e7eb}.eco-modal-actions button{border:0;border-radius:13px;padding:10px 15px;font-weight:950;cursor:pointer}.eco-modal-cancel{background:#e5e7eb;color:#334155}.eco-modal-ok{background:#2563eb;color:white}.eco-modal-danger .eco-modal-head{background:linear-gradient(135deg,#fee2e2,#ffffff)}.eco-modal-danger .eco-modal-ok{background:#dc2626}.eco-modal-success .eco-modal-head{background:linear-gradient(135deg,#dcfce7,#ffffff)}.eco-modal-success .eco-modal-ok{background:#16a34a}

    .massentest-actions{display:flex;gap:8px;flex-wrap:wrap;align-items:center;min-width:0;max-width:100%;padding:8px 10px;background:#fffdf2;border-top:1px solid #fde68a}.massentest-actions form{display:inline-flex;margin:0}.massentest-actions .btn2,.massentest-actions .btn{white-space:nowrap;margin:0}.massentest-action-row td{padding:0!important;border-bottom:2px solid #fde68a}.massentest-main-row td{border-bottom:0}.massentest-main-row td:last-child{min-width:auto}.massentest-test-hint{display:block;margin-top:4px;color:#92400e;font-size:12px;font-weight:800}.massentest-filecell{min-width:280px}.massentest-statuscell{min-width:220px}

    .massentest-main-row:target,.massentest-action-row:target{outline:3px solid #2563eb;background:#eff6ff!important}
    .task-badge{display:inline-flex;align-items:center;border-radius:999px;background:#e2e8f0;color:#334155;font-weight:950;font-size:12px;padding:4px 8px;text-decoration:none;margin-top:4px}.task-badge:hover{background:#cbd5e1;color:#0f172a}.tech-note{color:#64748b;font-size:12px;font-weight:700}

    .massentest-detail-preview{margin-top:16px;background:#f8fafc;border:1px solid #dbe3ef;border-radius:16px;padding:14px;overflow:hidden}
    .massentest-detail-preview iframe{width:100%;height:560px;border:1px solid #cbd5e1;border-radius:14px;background:white;margin-top:10px}
    .massentest-detail-preview-actions{display:flex;gap:8px;flex-wrap:wrap;margin-top:10px}
    @media(max-width:820px){.project-task-card{grid-template-columns:1fr}.project-task-actions{flex-direction:row;flex-wrap:wrap}.project-task-actions form{flex:1 1 180px}.hero{grid-template-columns:1fr}.learn-item{grid-template-columns:1fr}.learn-actions{justify-content:flex-start}.fieldrow{grid-template-columns:1fr}.massentest-preview{grid-template-columns:1fr}.massentest-preview iframe{height:320px}.wrap{padding:14px}.nav{padding:10px 14px}.top{padding:18px 16px}}


    /* WebUI 3.6.9: Detailansicht / Soll-Ist-Layout gegen lange Dateinamen absichern */
    .result-grid{display:grid;grid-template-columns:1fr;gap:14px;max-width:100%;overflow:hidden}
    .result-card{max-width:100%;overflow:hidden}
    .result-card table{table-layout:fixed;width:100%}
    .result-card th,.result-card td{min-width:0;max-width:100%;overflow-wrap:anywhere;word-break:break-word;white-space:normal}
    .result-card input[type=text]{width:100%;max-width:100%;min-width:0;box-sizing:border-box}
    .result-card table th:nth-child(1),.result-card table td:nth-child(1){width:14rem}
    .result-card table th:nth-child(2),.result-card table td:nth-child(2),
    .result-card table th:nth-child(3),.result-card table td:nth-child(3){width:auto}
    .result-card table th:last-child,.result-card table td:last-child{width:7.5rem;white-space:nowrap;text-align:left}
    .result-card b,.result-card strong{overflow-wrap:anywhere;word-break:break-word}
    .tech-note{display:block;max-width:100%;overflow-wrap:anywhere;word-break:break-word;line-height:1.2}
    @media(max-width:900px){.result-card table,.result-card tbody,.result-card tr,.result-card td{display:block;width:100%}.result-card th{display:none}.result-card td:last-child{width:100%;white-space:normal}.result-card td:first-child{font-weight:900;background:#f8fafc;border-radius:8px;margin-top:8px}}


    /* WebUI 4.0 Build 9: Sollwerte bearbeiten lokal gegen breite Werte absichern */
    .massentest-review-card{max-width:100%;overflow-x:hidden!important}
    .massentest-review-card form{max-width:100%;overflow-x:hidden!important}
    .massentest-review-table{table-layout:fixed!important;width:100%!important;max-width:100%!important}
    .massentest-review-table th,.massentest-review-table td{min-width:0!important;max-width:100%!important;white-space:normal!important;overflow-wrap:anywhere!important;word-break:break-word!important;vertical-align:top!important}
    .massentest-review-table th:nth-child(1),.massentest-review-table td:nth-child(1){width:15%!important}
    .massentest-review-table th:nth-child(2),.massentest-review-table td:nth-child(2){width:33%!important}
    .massentest-review-table th:nth-child(3),.massentest-review-table td:nth-child(3){width:45%!important}
    .massentest-review-table th:nth-child(4),.massentest-review-table td:nth-child(4){width:7%!important}
    .massentest-review-card input,.massentest-review-card textarea,.massentest-review-card select{width:100%!important;max-width:100%!important;min-width:0!important;box-sizing:border-box!important}
    .massentest-review-card .folder-name{white-space:normal!important;overflow-wrap:anywhere!important;word-break:break-word!important}

    /* WebUI 4.0 Build 8: Fachliche Schnellpruefung, eigene Wrapper gegen globale Karten-/Grid-Regeln */
    .qc-fast-card{overflow-x:hidden!important}
    .qc-fast-review{display:grid!important;grid-template-columns:minmax(420px,48%) minmax(460px,52%)!important;gap:16px!important;align-items:start!important;width:100%!important;min-width:900px!important}
    .qc-fast-pdf{grid-column:1!important;min-width:0!important;position:sticky!important;top:72px!important;align-self:start!important}
    .qc-fast-pdf iframe{display:block!important;width:100%!important;height:calc(100vh - 118px)!important;min-height:560px!important;border:1px solid #dbe3ef!important;border-radius:14px!important;background:white!important;margin:0!important}
    .qc-fast-pdf .qc-pdf-pan-shell{position:relative!important;width:100%!important;height:calc(100vh - 118px)!important;min-height:560px!important;overflow:auto!important;overscroll-behavior:contain!important;scrollbar-gutter:stable both-edges!important;border:1px solid #dbe3ef!important;border-radius:14px!important;background:white!important;cursor:grab!important}
    .qc-fast-pdf .qc-pdf-pan-shell.dragging{cursor:grabbing!important;user-select:none!important}
    .qc-fast-pdf .qc-pdf-pan-shell iframe{width:calc(140% + 72px)!important;height:calc(126% + 56px)!important;min-width:calc(140% + 72px)!important;min-height:calc(126% + 56px)!important;border:0!important;border-radius:0!important;pointer-events:none!important}
    .qc-pdf-pan-capture{position:absolute!important;left:0!important;top:0!important;right:22px!important;bottom:22px!important;z-index:2!important;background:transparent!important;cursor:grab!important;touch-action:none!important}
    .qc-pdf-pan-shell.dragging .qc-pdf-pan-capture{cursor:grabbing!important}
    .qc-pdf-pan-hint{font-size:12px!important;color:#64748b!important;margin-top:6px!important}
    .qc-fast-panel{grid-column:2!important;min-width:0!important;position:sticky!important;top:72px!important;max-height:calc(100vh - 118px)!important;overflow-y:auto!important;overflow-x:hidden!important;padding-right:4px!important;align-self:start!important}
    .qc-fast-decision{margin-bottom:12px!important;position:sticky!important;top:0!important;z-index:3!important;background:#fff!important;border-color:#dbe3ef!important}
    .qc-fast-status{display:grid!important;grid-template-columns:1fr 1fr!important;gap:12px!important;margin-bottom:12px!important}
    .qc-fast-panel table{table-layout:fixed!important;width:100%!important;font-size:12.5px!important}
    .qc-fast-panel th,.qc-fast-panel td{white-space:normal!important;overflow-wrap:anywhere!important;word-break:break-word!important;padding:7px!important;line-height:1.25!important}
    .qc-fast-panel table th:nth-child(1),.qc-fast-panel table td:nth-child(1){width:24%!important}
    .qc-fast-panel table th:nth-child(2),.qc-fast-panel table td:nth-child(2){width:32%!important}
    .qc-fast-panel table th:nth-child(3),.qc-fast-panel table td:nth-child(3){width:32%!important}
    .qc-fast-panel table th:nth-child(4),.qc-fast-panel table td:nth-child(4){width:12%!important}
    .qc-fast-panel input,.qc-fast-panel textarea,.qc-fast-panel select{width:100%!important;max-width:100%!important;min-width:0!important;box-sizing:border-box!important}
    .qc-fast-panel .toolbar .btn,.qc-fast-panel .toolbar .btn2{width:auto!important;max-width:100%!important}
    .qc-fast-actions{display:grid!important;gap:10px!important}
    .qc-fast-action-group{display:flex!important;gap:8px!important;flex-wrap:wrap!important;align-items:center!important;padding:8px!important;border:1px solid #dbe3ef!important;border-radius:12px!important;background:#f8fafc!important}
    .qc-fast-action-group b{display:block!important;width:100%!important;font-size:12px!important;color:#475569!important;text-transform:uppercase!important;letter-spacing:.04em!important}
    .qc-fast-panel .folder-name{white-space:normal!important;overflow-wrap:anywhere!important;word-break:break-word!important}

    </style>"""
    scan_version = get_scan_service_version() if 'get_scan_service_version' in globals() else ''
    scan_version_text = f" · Scan-Service v{scan_version}" if scan_version else ''
    return HTMLResponse(f"<!doctype html><html lang='de'><head><meta charset='utf-8'><title>{esc(title)}</title>{css}<script>function copyText(id){{const el=document.getElementById(id); if(!el)return; el.select(); el.setSelectionRange(0,999999); navigator.clipboard?navigator.clipboard.writeText(el.value):document.execCommand('copy');}}let workingPoll=null;function updateWorkingProgress(d){{try{{const pct=document.getElementById('workingProgressText');const bar=document.getElementById('workingProgressBar');const file=document.getElementById('workingFile');if(!d)return;const p=Number(d.percent||0);if(pct){{const total=Number(d.total||0);const cur=Number(d.current||0);pct.textContent=total?('Dokument '+cur+' von '+total+' · '+p+' %'):(p+' %');}}if(bar)bar.style.width=Math.max(0,Math.min(100,p))+'%';if(file)file.textContent=d.current_file?('Aktuell: '+d.current_file):(d.message||'');}}catch(e){{}}}}function startWorkingProgress(){{if(workingPoll)clearInterval(workingPoll);workingPoll=setInterval(async()=>{{try{{const r=await fetch('/test/massentest/progress?ts='+Date.now(),{{cache:'no-store'}});if(r.ok)updateWorkingProgress(await r.json());}}catch(e){{}}}},900);}}function showWorking(text,useProgress=true){{const ov=document.getElementById('workingOverlay'); if(!ov)return; if(workingPoll){{clearInterval(workingPoll);workingPoll=null;}} const msg=document.getElementById('workingText'); if(msg&&text)msg.textContent=text; const pct=document.getElementById('workingProgressText'); if(pct)pct.textContent=useProgress?'Fortschritt wird vorbereitet ...':'Sollwerte für dieses Dokument werden gespeichert ...'; const bar=document.getElementById('workingProgressBar'); if(bar)bar.style.width='0%'; const file=document.getElementById('workingFile'); if(file)file.textContent=''; ov.style.display='flex'; if(useProgress)startWorkingProgress();}}document.addEventListener('DOMContentLoaded',()=>{{document.querySelectorAll('form').forEach(f=>{{f.addEventListener('submit',(e)=>{{setTimeout(()=>{{if(!e.defaultPrevented)showWorking(f.getAttribute('data-working')||'Bitte warten – die WebUI arbeitet ...',f.getAttribute('data-progress')!=='0');}},80);}});}});document.querySelectorAll('a[data-working]').forEach(a=>a.addEventListener('click',()=>showWorking(a.getAttribute('data-working'),a.getAttribute('data-progress')!=='0')));}});</script></head><body><div id='workingOverlay' class='working-overlay'><div class='working-box'><div class='spinner'></div><div><div class='working-title'>Verarbeitung läuft</div><div id='workingText' class='working-sub'>Bitte warten – die WebUI arbeitet ...</div><div id='workingProgressText' class='working-sub' style='margin-top:8px;font-weight:900'>Fortschritt wird vorbereitet ...</div><div class='progress-wrap' style='margin-top:8px;width:320px;max-width:100%'><div id='workingProgressBar' class='progress-bar' style='width:0%'></div></div><div id='workingFile' class='working-sub' style='margin-top:6px;max-width:340px;word-break:break-word'></div></div></div></div><div class='top'><div class='top-line'><h1>ecoDMS Control Center <span class='muted small'>WebUI {APP_VERSION}{scan_version_text}</span></h1><div class='area-badges'>{area_badges}</div></div></div><div class='nav'>{nav}</div><main class='wrap'>{body}</main><div id='ecoConfirmModal' class='eco-modal-backdrop' role='dialog' aria-modal='true' aria-hidden='true'><div id='ecoConfirmBox' class='eco-modal'><div class='eco-modal-head'><h2 id='ecoConfirmTitle' class='eco-modal-title'>Aktion bestätigen</h2></div><div class='eco-modal-body'><div id='ecoConfirmMessage' class='eco-modal-message'></div><div id='ecoConfirmDetails' class='eco-modal-details' style='display:none'></div></div><div class='eco-modal-actions'><button id='ecoConfirmNo' class='eco-modal-cancel' type='button'>Nein, abbrechen</button><button id='ecoConfirmYes' class='eco-modal-ok' type='button'>Ja, ausführen</button></div></div></div><script>let ecoPendingForm=null;let ecoPendingSubmitter=null;function ecoShowConfirm(form,submitter){{ecoPendingForm=form;ecoPendingSubmitter=submitter||null;const modal=document.getElementById('ecoConfirmModal');const box=document.getElementById('ecoConfirmBox');const title=document.getElementById('ecoConfirmTitle');const msg=document.getElementById('ecoConfirmMessage');const det=document.getElementById('ecoConfirmDetails');const yes=document.getElementById('ecoConfirmYes');if(!modal||!box)return false;const src=submitter||form;title.textContent=src.getAttribute('data-confirm-title')||form.getAttribute('data-confirm-title')||'Aktion bestätigen';msg.textContent=src.getAttribute('data-confirm-message')||form.getAttribute('data-confirm-message')||'Diese Aktion wirklich ausführen?';const details=src.getAttribute('data-confirm-details')||form.getAttribute('data-confirm-details')||'';det.textContent=details;det.style.display=details?'block':'none';box.className='eco-modal '+(src.getAttribute('data-confirm-kind')||form.getAttribute('data-confirm-kind')||'');yes.textContent=src.getAttribute('data-confirm-ok')||form.getAttribute('data-confirm-ok')||'Ja, ausführen';modal.style.display='flex';modal.setAttribute('aria-hidden','false');return false;}}function ecoCloseConfirm(){{const modal=document.getElementById('ecoConfirmModal');if(modal){{modal.style.display='none';modal.setAttribute('aria-hidden','true');}}ecoPendingForm=null;ecoPendingSubmitter=null;}}function initPdfPanning(){{document.querySelectorAll('[data-pdf-pan]').forEach(shell=>{{if(shell.dataset.panReady==='1')return;shell.dataset.panReady='1';const capture=shell.querySelector('.qc-pdf-pan-capture')||shell;let dragging=false;let lastX=0;let lastY=0;function startDrag(e){{if(e.button!==0)return;dragging=true;lastX=e.clientX;lastY=e.clientY;shell.classList.add('dragging');e.preventDefault();}}function stopDrag(){{if(!dragging)return;dragging=false;shell.classList.remove('dragging');}}capture.addEventListener('mousedown',startDrag);window.addEventListener('mousemove',e=>{{if(!dragging)return;const dx=lastX-e.clientX;const dy=lastY-e.clientY;lastX=e.clientX;lastY=e.clientY;shell.scrollLeft+=dx;shell.scrollTop+=dy;e.preventDefault();}});window.addEventListener('mouseup',stopDrag);window.addEventListener('blur',stopDrag);capture.addEventListener('wheel',e=>{{shell.scrollLeft+=e.deltaX;shell.scrollTop+=e.deltaY;e.preventDefault();}},{{passive:false}});}});}}document.addEventListener('DOMContentLoaded',()=>{{const no=document.getElementById('ecoConfirmNo');const yes=document.getElementById('ecoConfirmYes');const modal=document.getElementById('ecoConfirmModal');if(no)no.addEventListener('click',ecoCloseConfirm);if(modal)modal.addEventListener('click',(e)=>{{if(e.target===modal)ecoCloseConfirm();}});if(yes)yes.addEventListener('click',()=>{{if(!ecoPendingForm)return;const f=ecoPendingForm;const s=ecoPendingSubmitter;ecoPendingForm=null;ecoPendingSubmitter=null;const m=document.getElementById('ecoConfirmModal');if(m)m.style.display='none';f.setAttribute('data-confirmed','1');if(s){{s.click();}}else{{f.requestSubmit();}}setTimeout(()=>f.removeAttribute('data-confirmed'),300);}});document.querySelectorAll('form').forEach(f=>{{f.addEventListener('submit',(e)=>{{if(f.getAttribute('data-confirmed')==='1')return;const submitter=e.submitter;const needs=(submitter&&(submitter.hasAttribute('data-confirm-message')||submitter.hasAttribute('data-confirm-title')))||(f.hasAttribute('data-confirm-message')||f.hasAttribute('data-confirm-title'));if(needs){{e.preventDefault();ecoShowConfirm(f,submitter);}}}},true);}});initPdfPanning();}});</script></body></html>")




def read_ablagekennung() -> str:
    path = CONFIG_DIR / "box_konfiguration.txt"
    value = read_text(path).strip()
    return value or "BOX001"


def write_ablagekennung(value: str) -> None:
    value = (value or "").strip()
    if not value:
        value = "BOX001"
    # Nur ein Wert pro Datei. Leerzeilen und Kommentare sind hier absichtlich nicht nötig.
    write_text_backup(CONFIG_DIR / "box_konfiguration.txt", value + "\n")


def read_zaehler_preview(ablage: str) -> tuple[str, str]:
    path = CONFIG_DIR / "zaehler.txt"
    now = datetime.now()
    default = f"{ablage}-{now.month:02d}-{now.year}-0001"
    if not path.exists():
        return "nicht vorhanden", default
    try:
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            parts = [x.strip() for x in line.split("|")]
            if len(parts) == 4 and parts[0].lower() == ablage.lower():
                monat, jahr, nr = int(parts[1]), int(parts[2]), int(parts[3])
                return f"{monat:02d}/{jahr} → {nr:04d}", f"{ablage}-{monat:02d}-{jahr}-{nr:04d}"
            if len(parts) == 3:
                monat, jahr, nr = int(parts[0]), int(parts[1]), int(parts[2])
                return f"{monat:02d}/{jahr} → {nr:04d}", f"{ablage}-{monat:02d}-{jahr}-{nr:04d}"
    except Exception:
        pass
    return "nicht gefunden", default


def count_learning_entries(kind: str) -> int:
    try:
        cfg = LEARNING_FILES[kind]
        return len(parse_learning_lines(CONFIG_DIR / cfg["learn"]))
    except Exception:
        return 0


def count_config_entries(filename: str) -> int:
    path = CONFIG_DIR / filename
    try:
        return len([ln for ln in read_text(path).splitlines() if ln.strip() and not ln.strip().startswith("#")])
    except Exception:
        return 0


def regression_stats() -> dict[str, object]:
    """Kennzahlen für Testcenter 2.0 ohne teure OCR-Läufe."""
    ensure_dirs()
    pdfs = sorted(TEST_DIR.glob("*.pdf"), key=lambda x: x.name.lower())
    expected_count = sum(1 for p in pdfs if expected_path_for(p.name).exists())
    latest_report = None
    try:
        reports = sorted(REPORTS_DIR.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True)
        if reports:
            latest_report = json.loads(reports[0].read_text(encoding="utf-8"))
    except Exception:
        latest_report = None
    return {
        "pdfs": len(pdfs),
        "expected": expected_count,
        "missing": max(0, len(pdfs) - expected_count),
        "latest_report": latest_report,
    }


MODULE_HINTS = {
    "fitz": "PyMuPDF",
    "qrcode": "qrcode[pil]",
    "pytesseract": "pytesseract",
    "pdf2image": "pdf2image",
    "pyzbar": "pyzbar",
}


def check_python_modules() -> dict[str, bool]:
    """Prüft die wichtigsten Python-Module für Scan-Service/Testcenter."""
    result: dict[str, bool] = {}
    for module_name in MODULE_HINTS:
        try:
            result[module_name] = importlib.util.find_spec(module_name) is not None
        except Exception:
            result[module_name] = False
    return result


def dependency_hint_html() -> str:
    checks = check_python_modules()
    missing = [name for name, ok in checks.items() if not ok]
    if not missing:
        return "<div class='flash success'>Alle wichtigen Python-Module für das Testcenter wurden gefunden.</div>"
    rows = "".join(
        f"<tr><td><span class='folder-name'>{esc(name)}</span></td><td>{esc(MODULE_HINTS.get(name, name))}</td></tr>"
        for name in missing
    )
    packages = " ".join(MODULE_HINTS.get(name, name) for name in missing)
    return f"""
    <div class='flash warn'>
      <b>Testcenter-Hinweis:</b> In der Python-Umgebung der WebUI fehlen Module.
      <table>{rows}</table>
      <p class='small'>Installation in derselben Umgebung wie die WebUI:</p>
      <pre>python -m pip install {esc(packages)}</pre>
      <p class='small muted'>Danach WebUI neu starten.</p>
    </div>
    """

def process_running(script_name: str) -> bool:
    # Windows: über PowerShell CommandLine suchen. Fallback: False.
    try:
        cmd = ["powershell", "-NoProfile", "-Command", f"Get-CimInstance Win32_Process | Where-Object {{$_.CommandLine -like '*{script_name}*'}} | Select-Object -First 1 -ExpandProperty ProcessId"]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=5, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        return bool(result.stdout.strip())
    except Exception:
        return False


def count_pdfs(folder: Path) -> tuple[int, int]:
    if not folder.exists():
        return 0, 0
    try:
        files = [p for p in folder.iterdir() if p.is_file()]
        pdfs = [p for p in files if p.suffix.lower() == ".pdf"]
        return len(files), len(pdfs)
    except Exception:
        return 0, 0




# ============================================================
# KONFIGURATIONSCENTER / BOX-ZÄHLER - WebUI 2.4
# ============================================================

def lade_ablagekennung() -> str:
    try:
        wert = read_text(BOX_CONFIG_FILE).strip()
        return wert or "BOX001"
    except Exception:
        return "BOX001"


def speichere_ablagekennung(wert: str) -> None:
    wert = (wert or "").strip() or "BOX001"
    wert = re.sub(r"[^A-Za-z0-9_\-ÄÖÜäöüß]", "_", wert)
    write_text_backup(BOX_CONFIG_FILE, wert + "\n")


def lese_zaehlerstand() -> dict:
    box = lade_ablagekennung()
    jetzt = datetime.now()
    result = {
        "box": box,
        "monat": jetzt.month,
        "jahr": jetzt.year,
        "zaehler": 1,
        "gefunden": False,
        "format": "neu",
    }

    if not ZAEHLER_CONFIG_FILE.exists():
        return result

    try:
        for zeile in read_text(ZAEHLER_CONFIG_FILE).splitlines():
            z = zeile.strip()
            if not z or z.startswith("#"):
                continue
            teile = [t.strip() for t in z.split("|")]
            if len(teile) == 4:
                z_box, monat, jahr, zaehler = teile
                if z_box == box:
                    result.update({
                        "box": z_box,
                        "monat": int(monat),
                        "jahr": int(jahr),
                        "zaehler": int(zaehler),
                        "gefunden": True,
                        "format": "neu",
                    })
                    return result
            elif len(teile) == 3:
                monat, jahr, zaehler = teile
                result.update({
                    "box": box,
                    "monat": int(monat),
                    "jahr": int(jahr),
                    "zaehler": int(zaehler),
                    "gefunden": True,
                    "format": "alt",
                })
                return result
    except Exception:
        pass

    return result


def berechne_naechsten_barcode() -> str:
    z = lese_zaehlerstand()
    return f"{z['box']}-{int(z['monat']):02d}-{int(z['jahr'])}-{int(z['zaehler']):04d}"


def speichere_zaehlerstand(monat: int, jahr: int, zaehler: int) -> None:
    box = lade_ablagekennung()
    monat = max(1, min(12, int(monat)))
    jahr = int(jahr)
    zaehler = max(1, int(zaehler))

    vorhandene = []
    ersetzt = False
    if ZAEHLER_CONFIG_FILE.exists():
        for zeile in read_text(ZAEHLER_CONFIG_FILE).splitlines():
            z = zeile.strip()
            if not z or z.startswith("#"):
                vorhandene.append(zeile)
                continue
            teile = [t.strip() for t in z.split("|")]
            if len(teile) == 4 and teile[0] == box:
                vorhandene.append(f"{box}|{monat:02d}|{jahr}|{zaehler}")
                ersetzt = True
            elif len(teile) == 3:
                vorhandene.append(f"{box}|{monat:02d}|{jahr}|{zaehler}")
                ersetzt = True
            else:
                vorhandene.append(zeile)

    if not ersetzt:
        vorhandene.append(f"{box}|{monat:02d}|{jahr}|{zaehler}")

    write_text_backup(ZAEHLER_CONFIG_FILE, "\n".join(vorhandene).rstrip() + "\n")


def lese_test_zaehlerstand() -> dict:
    """Eigener Testzähler, getrennt vom produktiven zaehler.txt."""
    box = lade_ablagekennung()
    jetzt = datetime.now()
    result = {
        "box": box,
        "prefix": "TEST",
        "monat": jetzt.month,
        "jahr": jetzt.year,
        "zaehler": 1,
        "gefunden": False,
        "format": "test",
    }
    if not TEST_ZAEHLER_CONFIG_FILE.exists():
        return result
    try:
        for zeile in read_text(TEST_ZAEHLER_CONFIG_FILE).splitlines():
            z = zeile.strip()
            if not z or z.startswith("#"):
                continue
            teile = [t.strip() for t in z.split("|")]
            # Neues Format: TEST|Ordner003|06|2026|0001
            if len(teile) == 5:
                prefix, z_box, monat, jahr, zaehler = teile
                if z_box.lower() == box.lower():
                    result.update({
                        "prefix": prefix or "TEST",
                        "box": z_box,
                        "monat": int(monat),
                        "jahr": int(jahr),
                        "zaehler": int(zaehler),
                        "gefunden": True,
                    })
                    return result
            # Altes/kurzes Testformat: TEST|06|2026|0001
            elif len(teile) == 4:
                prefix, monat, jahr, zaehler = teile
                result.update({
                    "prefix": prefix or "TEST",
                    "box": box,
                    "monat": int(monat),
                    "jahr": int(jahr),
                    "zaehler": int(zaehler),
                    "gefunden": True,
                })
                return result
    except Exception:
        pass
    return result


def berechne_naechsten_test_barcode() -> str:
    z = lese_test_zaehlerstand()
    return f"{z['prefix']}-{z['box']}-{int(z['monat']):02d}-{int(z['jahr'])}-{int(z['zaehler']):04d}"


def berechne_test_barcode() -> str:
    """Kompatibilitäts-Alias für Testcenter-Templates.

    In WebUI 2.7.7 wurde im Testcenter versehentlich diese Funktion
    aufgerufen, obwohl die eigentliche Vorschaufunktion
    berechne_naechsten_test_barcode() heißt.
    """
    return berechne_naechsten_test_barcode()


def erhoehe_test_zaehler() -> str:
    """Erhöht nur den Testzähler und gibt den verbrauchten Test-Barcode zurück.

    Wichtig: Der produktive zaehler.txt bleibt dabei unberührt.
    Wird genutzt, wenn im Testcenter neue Test-PDFs hochgeladen werden, damit
    Testdokumente nachvollziehbare TEST-Barcodes bekommen und der Testzähler
    sichtbar weiterläuft.
    """
    z = lese_test_zaehlerstand()
    barcode = f"{z['prefix']}-{z['box']}-{int(z['monat']):02d}-{int(z['jahr'])}-{int(z['zaehler']):04d}"
    speichere_test_zaehlerstand(int(z['monat']), int(z['jahr']), int(z['zaehler']) + 1, str(z.get('prefix') or 'TEST'))
    return barcode


app = FastAPI(title="ecoDMS WebUI", version=APP_VERSION)

try:
    if (BASE_DIR / "_webservice").exists():
        app.mount("/static", StaticFiles(directory=str(BASE_DIR / "_webservice")), name="static")
except Exception:
    pass


@app.get("/test/massentest/progress")
def massentest_progress_endpoint():
    try:
        if MASSTEST_PROGRESS_JSON.exists():
            return json.loads(MASSTEST_PROGRESS_JSON.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {"aktion": "", "current": 0, "total": 0, "percent": 0, "current_file": "", "status": "idle", "message": ""}


def schreibe_test_upload_meta(pdf_path: Path, test_barcode: str) -> None:
    """Schreibt eine kleine Begleitdatei zum Testupload.

    Die Datei dient nur der Nachvollziehbarkeit im Testcenter. Der Scan-Service
    muss sie nicht zwingend auswerten.
    """
    try:
        meta_path = pdf_path.with_suffix(pdf_path.suffix + ".testmeta")
        meta_path.write_text(
            "TESTDOKUMENT=1\n"
            f"TEST_BARCODE={test_barcode}\n"
            f"UPLOAD_DATUM={datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n",
            encoding="utf-8",
        )
    except Exception:
        pass


def speichere_test_zaehlerstand(monat: int, jahr: int, zaehler: int, prefix: str = "TEST") -> None:
    box = lade_ablagekennung()
    prefix = re.sub(r"[^A-Za-z0-9_\-ÄÖÜäöüß]", "_", (prefix or "TEST").strip()) or "TEST"
    monat = max(1, min(12, int(monat)))
    jahr = int(jahr)
    zaehler = max(1, int(zaehler))
    vorhandene = []
    ersetzt = False
    if TEST_ZAEHLER_CONFIG_FILE.exists():
        for zeile in read_text(TEST_ZAEHLER_CONFIG_FILE).splitlines():
            z = zeile.strip()
            if not z or z.startswith("#"):
                vorhandene.append(zeile)
                continue
            teile = [t.strip() for t in z.split("|")]
            if len(teile) == 5 and teile[1].lower() == box.lower():
                vorhandene.append(f"{prefix}|{box}|{monat:02d}|{jahr}|{zaehler}")
                ersetzt = True
            elif len(teile) == 4:
                vorhandene.append(f"{prefix}|{box}|{monat:02d}|{jahr}|{zaehler}")
                ersetzt = True
            else:
                vorhandene.append(zeile)
    if not ersetzt:
        vorhandene.append(f"{prefix}|{box}|{monat:02d}|{jahr}|{zaehler}")
    write_text_backup(TEST_ZAEHLER_CONFIG_FILE, "\n".join(vorhandene).rstrip() + "\n")


@app.get("/", response_class=HTMLResponse)
def status() -> HTMLResponse:
    ensure_dirs()
    scan = process_running("ecodms_scan_service.py")
    mail = process_running("outlook_mail_watcher.py")
    ablage = read_ablagekennung()
    zaehler, next_code = read_zaehler_preview(ablage)
    z = lese_zaehlerstand()
    test_z = lese_test_zaehlerstand()
    test_next_code = berechne_naechsten_test_barcode()
    lieferanten_offen = count_learning_entries("lieferanten")
    doktypen_offen = count_learning_entries("dokumenttypen")
    lieferanten_count = count_config_entries("lieferanten_konfiguration.txt")
    doktypen_count = count_config_entries("dokumenttypen_konfiguration.txt")
    reg = regression_stats()
    try:
        mt_rows = massentest_read_results()
        mt_total, mt_summary = massentest_compact_status_html(mt_rows)
    except Exception:
        mt_total, mt_summary = 0, "Noch kein Massentestbestand"
    latest = reg.get("latest_report") or {}
    latest_text = "noch kein Testlauf"
    if latest:
        latest_text = f"{latest.get('timestamp', '')} · bestanden: {latest.get('passed', 0)} · Abweichung: {latest.get('failed', 0)}"

    rows = ""
    total_files = 0
    total_pdfs = 0
    for name, path in FOLDERS.items():
        files, pdfs = count_pdfs(path)
        total_files += files
        total_pdfs += pdfs
        folder_name = path.name
        note = FOLDER_NOTES.get(folder_name, "")
        note_html = f" <span class='folder-note'>{esc(note)}</span>" if note else ""
        rows += (
            f"<tr>"
            f"<td>{esc(name)}<br><span class='folder-name'>{esc(folder_name)}</span>{note_html}</td>"
            f"<td>{esc(path)}</td>"
            f"<td>{files}</td>"
            f"<td>{pdfs}</td>"
            f"</tr>"
        )

    projekt_stats = projekt_statistik()
    service_state = "läuft" if scan else "nicht erkannt"
    mail_state = "läuft" if mail else "nicht erkannt"
    body = f"""
    <div class='card'>
      <div class='section-head'><h2>Dashboard</h2><span class='count-badge'>Betriebsüberblick</span></div>
      <p class='muted'>Kurzer Tagesstatus. Pflege, Ordnerdetails und Zähleränderungen liegen unter <b>Einstellungen</b>.</p>
      <div class='grid'>
        <div class='metric'><div class='label'>Scan-Service</div><div class='{ 'ok' if scan else 'bad' }' style='font-size:22px;font-weight:900'>{esc(service_state)}</div><div class='muted small'>ecodms_scan_service.py</div></div>
        <div class='metric'><div class='label'>Outlook-Watcher</div><div class='{ 'ok' if mail else 'bad' }' style='font-size:22px;font-weight:900'>{esc(mail_state)}</div><div class='muted small'>outlook_mail_watcher.py</div></div>
        <div class='metric'><div class='label'>Fehlerstatus</div><div class='num'>{projekt_stats.get('hoch', 0)}</div><div class='muted small'>hohe Priorität offen · aktive Aufgaben: {projekt_stats.get('gesamt', 0)}</div><p><a class='btn2' href='/projekt'>Projekt öffnen</a></p></div>
        <div class='metric'><div class='label'>Warteschlange</div><div class='num'>{total_pdfs}</div><div class='muted small'>PDFs in überwachten Projektordnern</div><p><a class='btn2' href='/config'>Einstellungen öffnen</a></p></div>
      </div>
    </div>
    <div class='settings-counter-grid'>
      <div class='settings-counter productive'>
        <div class='settings-counter-head'><h3>Produktivzähler</h3><span class='counter-badge productive'>PRODUKTIV</span></div>
        <div class='settings-counter-fields'>
          <div class='settings-counter-side'>
            <div class='settings-line'><span class='settings-label'>Monat<small>Produktiver Zählerstand</small></span><span class='settings-line-value'>{int(z.get('monat', 0) or 0):02d}</span></div>
            <div class='settings-line'><span class='settings-label'>Jahr<small>Produktiver Zählerstand</small></span><span class='settings-line-value'>{int(z.get('jahr', 0) or 0)}</span></div>
            <div class='settings-line'><span class='settings-label'>Zähler<small>Nächster echter Archiv-Barcode</small></span><span class='settings-line-value'>{int(z.get('zaehler', 0) or 0)}</span></div>
          </div>
          <div class='settings-counter-side'>
            <div class='settings-line'><span class='settings-label'>Präfix / Ablagekennung<small>Aktuelle Ablage</small></span><span class='settings-line-value'>{esc(ablage)}</span></div>
            <div class='settings-line'><span class='settings-label'>Nächster echter Barcode<small>Monat/Jahr · Nummer</small></span><span class='settings-line-value'>{int(z.get('monat', 0) or 0):02d}/{int(z.get('jahr', 0) or 0)} · {int(z.get('zaehler', 0) or 0):04d}</span></div>
          </div>
        </div>
        <div class='settings-preview productive'><span class='settings-preview-symbol'>▣</span><div><small>Nächster Produktiv-Code</small><br>{esc(next_code)}</div></div>
      </div>
      <div class='settings-counter test'>
        <div class='settings-counter-head'><h3>Testzähler</h3><span class='counter-badge test'>TEST</span></div>
        <div class='settings-counter-fields'>
          <div class='settings-counter-side'>
            <div class='settings-line'><span class='settings-label'>Test-Monat<small>Testzählerstand</small></span><span class='settings-line-value'>{int(test_z.get('monat', 0) or 0):02d}</span></div>
            <div class='settings-line'><span class='settings-label'>Test-Jahr<small>Testzählerstand</small></span><span class='settings-line-value'>{int(test_z.get('jahr', 0) or 0)}</span></div>
            <div class='settings-line'><span class='settings-label'>Testzähler<small>Nächster Test-Barcode</small></span><span class='settings-line-value'>{int(test_z.get('zaehler', 0) or 0)}</span></div>
          </div>
          <div class='settings-counter-side'>
            <div class='settings-line'><span class='settings-label'>Test-Präfix<small>Aktuelles Präfix</small></span><span class='settings-line-value'>{esc(test_z.get('prefix','TEST'))}</span></div>
            <div class='settings-line'><span class='settings-label'>Nächster Test-Barcode<small>Monat/Jahr · Nummer</small></span><span class='settings-line-value'>{int(test_z.get('monat', 0) or 0):02d}/{int(test_z.get('jahr', 0) or 0)} · {int(test_z.get('zaehler', 0) or 0):04d}</span></div>
          </div>
        </div>
        <div class='settings-preview test'><span class='settings-preview-symbol'>▣</span><div><small>Nächster Test-Code</small><br>{esc(test_next_code)}</div></div>
      </div>
    </div>
    <div class='dashboard-grid'>
      <div class='card dashboard-card'>
        <h2>Dokumentenprüfung</h2>
        <p class='muted small dashboard-grow'>Einzeldokument, Massentest und Berichte/Auswertungen.</p>
        <p class='dashboard-actions'><a class='btn2' href='/test'>Dokumentenprüfung öffnen</a></p>
      </div>
      <div class='card dashboard-card'>
        <h2>Einstellungen</h2>
        <p class='num'>{lieferanten_offen + doktypen_offen}</p>
        <p class='muted small dashboard-grow'>offene Lernlisten-Vorschläge · Lieferanten: {lieferanten_offen} · Dokumenttypen: {doktypen_offen}</p>
        <p class='dashboard-actions'><a class='btn2' href='/config'>Einstellungen öffnen</a></p>
      </div>
    </div>
    <div class='card small muted'>Lokal erreichbar unter <b>http://127.0.0.1:8000</b>. Keine Cloud, keine Datenbank.</div>
    """
    return layout("Dashboard", body)


@app.get("/ablage", response_class=HTMLResponse)
def ablage_form() -> HTMLResponse:
    ensure_dirs()
    scan = process_running("ecodms_scan_service.py")
    mail = process_running("outlook_mail_watcher.py")
    z = lese_zaehlerstand()
    tz = lese_test_zaehlerstand()
    ablage = lade_ablagekennung()
    folder_rows = ""
    for name, path in FOLDERS.items():
        files, pdfs = count_pdfs(path)
        folder_rows += (
            f"<tr><td>{esc(name)}</td><td>{esc(str(path))}</td>"
            f"<td>{files}</td><td>{pdfs}</td></tr>"
        )
    body = f"""
    <div class='card'>
      <div class='section-head'><h2>System</h2><span class='count-badge'>Wartung</span></div>
      <p class='muted'>Pflegebereich für Wartung, Ablagekennung, Zähler, Ordnerstatus, Logs und Dienste. Das Dashboard zeigt diese Werte nur an.</p>
      <div class='grid'>
        <div class='metric'><div class='label'>Scan-Service</div><div class='{ 'ok' if scan else 'bad' }' style='font-size:22px;font-weight:900'>{'läuft' if scan else 'nicht erkannt'}</div><div class='muted small'>ecodms_scan_service.py</div></div>
        <div class='metric'><div class='label'>Outlook-Watcher</div><div class='{ 'ok' if mail else 'bad' }' style='font-size:22px;font-weight:900'>{'läuft' if mail else 'nicht erkannt'}</div><div class='muted small'>outlook_mail_watcher.py</div></div>
        <div class='metric'><div class='label'>Logs</div><div class='num'>→</div><div class='muted small'>System- und Serviceprotokolle</div><p><a class='btn2' href='/logs'>Logs öffnen</a></p></div>
      </div>
    </div>
    <div class='card'>
      <div class='section-head'><h2>Ablagekennung & Zähler</h2><span class='count-badge'>Pflege</span></div>
      <form method='post' action='/config-form/box'>
        {render_input('ABLAGEKENNUNG', 'Bezeichner / Ablagekennung', ablage, 'text', 'Beispiele: BOX001, ORDNER003, ARCHIV2026')}
        <div class='counter-form-grid'>
          <div class='counter-form-card productive'>
            <h3>Produktivzähler <span class='counter-badge productive'>PRODUKTIV</span></h3>
            {render_input('MONAT', 'Monat', f"{int(z['monat']):02d}", 'number', 'Monat für den produktiven Zählerstand.')}
            {render_input('JAHR', 'Jahr', str(int(z['jahr'])), 'number', 'Jahr für den produktiven Zählerstand.')}
            {render_input('ZAEHLER', 'Zähler', str(int(z['zaehler'])), 'number', 'Dieser Wert wird für den nächsten echten Archiv-Barcode verwendet.')}
            <div class='flash'><b>Vorschau:</b><br><span class='pill'>{esc(berechne_naechsten_barcode())}</span></div>
          </div>
          <div class='counter-form-card test'>
            <h3>Testzähler <span class='counter-badge test'>TEST</span></h3>
            {render_input('TEST_PREFIX', 'Test-Präfix', str(tz.get('prefix','TEST')), 'text', 'Standard: TEST')}
            {render_input('TEST_MONAT', 'Test-Monat', f"{int(tz['monat']):02d}", 'number', 'Monat für den Testzählerstand.')}
            {render_input('TEST_JAHR', 'Test-Jahr', str(int(tz['jahr'])), 'number', 'Jahr für den Testzählerstand.')}
            {render_input('TEST_ZAEHLER', 'Testzähler', str(int(tz['zaehler'])), 'number', 'Dieser Wert wird nur für Test-Barcodes verwendet.')}
            <div class='flash warn'><b>Vorschau:</b><br><span class='pill'>{esc(berechne_naechsten_test_barcode())}</span></div>
          </div>
        </div>
        <p><button class='btn' type='submit'>Speichern</button> <a class='btn2' href='/'>Zum Dashboard</a> <a class='btn2' href='/config-form/box'>Erweiterte Zählerseite</a></p>
      </form>
    </div>
    <div class='card'>
      <div class='section-head'><h2>Ordnerstatus</h2><span class='count-badge'>Wartung</span></div>
      <p class='muted small'>Technische Ablageorte und Dateizahlen. Dieser Bereich wurde vom Dashboard hierher verschoben.</p>
      <table><tr><th>Ordner</th><th>Pfad</th><th>Dateien</th><th>PDF</th></tr>{folder_rows}</table>
    </div>
    """
    return layout("Einstellungen", body)


@app.post("/ablage")
def save_ablage(kennung: str = Form("")):
    write_ablagekennung(kennung)
    return RedirectResponse("/ablage", status_code=303)




def parse_key_value_config(path: Path) -> tuple[dict[str, str], list[str]]:
    """Liest einfache KEY=VALUE-Konfigurationsdateien und merkt unbekannte Originalzeilen."""
    values: dict[str, str] = {}
    raw_lines = read_text(path).splitlines()
    for line in raw_lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        values[key.strip().upper()] = value.strip()
    return values, raw_lines


def merge_key_value_content(path: Path, ordered_values: dict[str, str], title: str) -> str:
    """Schreibt bekannte Werte sauber und hängt unbekannte bestehende KEYs am Ende an."""
    existing, _raw = parse_key_value_config(path)
    lines = [f"# {title}", "# Bearbeitet über die lokale ecoDMS-Weboberfläche", "# 0 = aus, 1 = ein", ""]
    for key, value in ordered_values.items():
        lines.append(f"{key}={value}")
    unknown = {k: v for k, v in existing.items() if k not in ordered_values}
    if unknown:
        lines += ["", "# Weitere bisher vorhandene Werte"]
        for key in sorted(unknown):
            lines.append(f"{key}={unknown[key]}")
    return "\n".join(lines) + "\n"


def checkbox_value(value: str | None) -> str:
    return "1" if value == "1" else "0"


def render_checkbox(name: str, label: str, value: str, hint: str = "") -> str:
    checked = "checked" if str(value).strip() == "1" else ""
    return (
        f"<label class='checkrow'><input type='checkbox' name='{esc(name)}' value='1' {checked}> "
        f"<b>{esc(label)}</b> <span class='muted small'>{esc(hint)}</span></label>"
    )


def render_input(name: str, label: str, value: str, input_type: str = "text", hint: str = "") -> str:
    return (
        f"<label class='fieldrow'><span><b>{esc(label)}</b><small>{esc(hint)}</small></span>"
        f"<input type='{esc(input_type)}' name='{esc(name)}' value='{esc(value)}'></label>"
    )

@app.get("/settings", response_class=HTMLResponse)
@app.get("/config", response_class=HTMLResponse)
def config_index() -> HTMLResponse:
    ensure_dirs()
    z = lese_zaehlerstand()
    tz = lese_test_zaehlerstand()
    scan = process_running("ecodms_scan_service.py")
    mail = process_running("outlook_mail_watcher.py")
    folder_rows = ""
    for name, path in FOLDERS.items():
        files, pdfs = count_pdfs(path)
        folder_rows += (
            f"<tr><td>{esc(name)}</td><td>{esc(str(path))}</td>"
            f"<td>{files}</td><td>{pdfs}</td></tr>"
        )
    primary_config = [
        ("box_konfiguration.txt", "Ablagekennung / BOX / Ordnername"),
        ("zaehler.txt", "Produktivzähler"),
        ("test_zaehler.txt", "Separater Testzähler mit TEST-Präfix"),
        ("lieferanten_konfiguration.txt", "Lieferanten und Suchwörter"),
    ]
    primary_files_html = ""
    for filename, desc in primary_config:
        primary_files_html += (
            f"<div class='settings-mini-card'><h3>{esc(filename)}</h3>"
            f"<p class='muted small'>{esc(desc)}</p>"
            f"<p class='settings-actions'><a class='btn2' href='/config/{esc(filename)}'>Als Text bearbeiten</a></p></div>"
        )
    other_files_html = ""
    primary_names = {x[0] for x in primary_config}
    for filename in CONFIG_FILES:
        if filename in primary_names:
            continue
        other_files_html += (
            f"<div class='settings-mini-card'><h3>{esc(filename)}</h3>"
            f"<p class='muted small'>Weitere Konfigurationsdatei.</p>"
            f"<p class='settings-actions'><a class='btn2' href='/config/{esc(filename)}'>Als Text bearbeiten</a></p></div>"
        )
    body = f"""
    <div class='settings-page'>
      <div class='card' style='margin-bottom:0'>
        <div class='section-head'><div><h2>Einstellungen</h2><p class='muted' style='margin:4px 0 0'>Gemeinsamer Bereich für Konfigurationsdateien, Ablagekennung/Zähler, Dienste, Logs und Wartung.</p></div><span class='count-badge'>Konfiguration / System</span></div>
      </div>

      <details class='settings-section' data-settings-key='system' open>
        <summary><span class='settings-title'><span class='settings-icon'>⚙</span>System <span class='settings-badge maintenance'>Wartung</span></span></summary>
        <div class='settings-body'>
          <div class='settings-card-grid'>
            <div class='settings-mini-card'>
              <h3>Scan-Service</h3>
              <div class='{ 'ok' if scan else 'bad' }' style='font-size:22px;font-weight:950'>{'läuft' if scan else 'nicht erkannt'}</div>
              <p class='muted small'>ecodms_scan_service.py</p>
            </div>
            <div class='settings-mini-card'>
              <h3>Outlook-Watcher</h3>
              <div class='{ 'ok' if mail else 'bad' }' style='font-size:22px;font-weight:950'>{'läuft' if mail else 'nicht erkannt'}</div>
              <p class='muted small'>outlook_mail_watcher.py</p>
            </div>
            <div class='settings-mini-card'>
              <h3>Logs</h3>
              <p class='muted small'>System- und Serviceprotokolle</p>
              <p class='settings-actions'><a class='btn2' href='/logs'>Logs öffnen</a></p>
            </div>
          </div>
        </div>
      </details>

      <details class='settings-section' data-settings-key='counter' open>
        <summary><span class='settings-title'><span class='settings-icon'>▦</span>Ablagekennung & Zähler <span class='settings-badge care'>Pflege</span></span></summary>
        <div class='settings-body'>
          <form method='post' action='/config-form/box'>
            <div class='settings-line' style='margin-bottom:14px'>
              <label>Bezeichner / Ablagekennung<small>Beispiele: BOX001, ORDNER003, ARCHIV2026</small></label>
              <input type='text' name='ABLAGEKENNUNG' value='{esc(lade_ablagekennung())}'>
            </div>
            <div class='settings-counter-grid'>
              <div class='settings-counter productive'>
                <div class='settings-counter-head'><h3>Produktivzähler</h3><span class='counter-badge productive'>PRODUKTIV</span></div>
                <div class='settings-counter-fields'>
                  <div class='settings-counter-side'>
                    <div class='settings-line'><label>Monat<small>Monat für den produktiven Zählerstand.</small></label><input type='number' name='MONAT' value='{int(z['monat']):02d}'></div>
                    <div class='settings-line'><label>Jahr<small>Jahr für den produktiven Zählerstand.</small></label><input type='number' name='JAHR' value='{int(z['jahr'])}'></div>
                    <div class='settings-line'><label>Zähler<small>Nächster echter Archiv-Barcode.</small></label><input type='number' name='ZAEHLER' value='{int(z['zaehler'])}'></div>
                  </div>
                  <div class='settings-counter-side'>
                    <div class='settings-line'><span class='settings-label'>Präfix / Ablagekennung<small>Aktuelle Ablage</small></span><span class='settings-line-value'>{esc(lade_ablagekennung())}</span></div>
                    <div class='settings-line'><span class='settings-label'>Nächster echter Barcode<small>Monat/Jahr · Nummer</small></span><span class='settings-line-value'>{int(z['monat']):02d}/{int(z['jahr'])} · {int(z['zaehler']):04d}</span></div>
                  </div>
                </div>
                <div class='settings-preview productive'><span class='settings-preview-symbol'>▣</span><div><small>Vorschau nächster Produktiv-Code</small><br>{esc(berechne_naechsten_barcode())}</div></div>
              </div>
              <div class='settings-counter test'>
                <div class='settings-counter-head'><h3>Testzähler</h3><span class='counter-badge test'>TEST</span></div>
                <div class='settings-counter-fields'>
                  <div class='settings-counter-side'>
                    <div class='settings-line'><label>Test-Monat<small>Monat für den Testzählerstand.</small></label><input type='number' name='TEST_MONAT' value='{int(tz['monat']):02d}'></div>
                    <div class='settings-line'><label>Test-Jahr<small>Jahr für den Testzählerstand.</small></label><input type='number' name='TEST_JAHR' value='{int(tz['jahr'])}'></div>
                    <div class='settings-line'><label>Testzähler<small>Nächster Test-Barcode.</small></label><input type='number' name='TEST_ZAEHLER' value='{int(tz['zaehler'])}'></div>
                  </div>
                  <div class='settings-counter-side'>
                    <div class='settings-line'><label>Test-Präfix<small>Standard: TEST</small></label><input type='text' name='TEST_PREFIX' value='{esc(str(tz.get('prefix','TEST')))}'></div>
                    <div class='settings-line'><span class='settings-label'>Nächster Test-Barcode<small>Monat/Jahr · Nummer</small></span><span class='settings-line-value'>{int(tz['monat']):02d}/{int(tz['jahr'])} · {int(tz['zaehler']):04d}</span></div>
                  </div>
                </div>
                <div class='settings-preview test'><span class='settings-preview-symbol'>▣</span><div><small>Vorschau nächster Test-Code</small><br>{esc(berechne_naechsten_test_barcode())}</div></div>
              </div>
            </div>
            <p class='toolbar'><button class='btn success' type='submit'>Speichern</button><a class='btn2' href='/'>Zum Dashboard</a><a class='btn2' href='/config-form/box'>Erweiterte Zählerseite</a></p>
          </form>
        </div>
      </details>

      <details class='settings-section' data-settings-key='more' open>
        <summary><span class='settings-title'><span class='settings-icon'>☷</span>Weitere Einstellungen</span></summary>
        <div class='settings-body'>
          <div class='settings-card-grid'>
            <div class='settings-mini-card'><h3>Importoptionen</h3><p class='muted small'>Outlook-Import, BOX-Code, Etikettendruck und Zählerverhalten.</p><p class='settings-actions'><a class='btn2' href='/config-form/import_optionen'>Bearbeiten</a></p></div>
            <div class='settings-mini-card'><h3>PDF-Dateinamen</h3><p class='muted small'>Sprechende Dateinamen nach erfolgreicher Verarbeitung.</p><p class='settings-actions'><a class='btn2' href='/config-form/dateiname'>Bearbeiten</a></p></div>
            <div class='settings-mini-card'><h3>Benachrichtigung</h3><p class='muted small'>Mail-/Outlook-Benachrichtigung für Lernlisten.</p><p class='settings-actions'><a class='btn2' href='/config-form/benachrichtigung'>Bearbeiten</a></p></div>
            <div class='settings-mini-card'><h3>Erkennung</h3><p class='muted small'>Lieferanten, Dokumenttypen, Felder und Filter.</p><p class='settings-actions'><a class='btn2' href='/config/lieferanten_konfiguration.txt'>Lieferanten</a> <a class='btn2' href='/config/dokumenttypen_konfiguration.txt'>Dokumenttypen</a> <a class='btn2' href='/config/felder_konfiguration.txt'>Felder</a></p></div>
            <div class='settings-mini-card'><h3>Lernlisten</h3><p class='muted small'>Vorschläge aus der Erkennung prüfen und übernehmen.</p><p class='settings-actions'><a class='btn2' href='/learning'>Lernlisten öffnen</a></p></div>
          </div>
        </div>
      </details>

      <details class='settings-section' data-settings-key='files' open>
        <summary><span class='settings-title'><span class='settings-icon'>□</span>Erweiterte Konfigurationsdateien</span></summary>
        <div class='settings-body'>
          <div class='settings-card-grid'>{primary_files_html}
            <div class='settings-mini-card'><h3>Weitere Dateien</h3><p class='muted small'>Weitere Konfigurationsdateien anzeigen.</p><details><summary class='btn2' style='display:inline-flex'>Dateien öffnen</summary><div class='settings-card-grid' style='margin-top:12px'>{other_files_html}</div></details></div>
          </div>
        </div>
      </details>

      <details class='settings-section' data-settings-key='folders'>
        <summary><span class='settings-title'><span class='settings-icon'>▰</span>Ordnerstatus <span class='settings-badge info'>Info</span></span></summary>
        <div class='settings-body'>
          <p class='muted small'>Übersicht über die wichtigsten Projektordner und deren Statusinformationen.</p>
          <div class='settings-folder-table'><table><tr><th>Ordner</th><th>Pfad</th><th>Dateien</th><th>PDF</th></tr>{folder_rows}</table></div>
        </div>
      </details>
    </div>
    <script>
    (function(){{
      const storageKey = 'settings_accordion_state';
      let state = {{}};
      try {{ state = JSON.parse(localStorage.getItem(storageKey) || '{{}}') || {{}}; }} catch(e) {{ state = {{}}; }}
      document.querySelectorAll('details.settings-section[data-settings-key]').forEach(function(section){{
        const key = section.getAttribute('data-settings-key');
        if (Object.prototype.hasOwnProperty.call(state, key)) section.open = !!state[key];
        section.setAttribute('aria-expanded', section.open ? 'true' : 'false');
        section.addEventListener('toggle', function(){{
          state[key] = section.open;
          section.setAttribute('aria-expanded', section.open ? 'true' : 'false');
          localStorage.setItem(storageKey, JSON.stringify(state));
        }});
      }});
    }})();
    </script>
    """
    return layout("Einstellungen", body)


@app.get("/config/{filename}", response_class=HTMLResponse)
def config_file_editor(filename: str, saved: str = "") -> HTMLResponse:
    ensure_dirs()
    if filename not in CONFIG_FILES:
        raise HTTPException(status_code=404)
    path = CONFIG_DIR / filename
    content = read_text(path) if path.exists() else ""
    saved_html = "<div class='flash success'>Konfigurationsdatei gespeichert.</div>" if saved else ""
    body = f"""
    <div class='top-actions'><div><b>{esc(filename)}</b><br><span class='muted small'>Konfigurationsdatei bearbeiten</span></div><a class='btn2' href='/config'>← Zurück zu Einstellungen</a></div>
    <div class='card'>
      {saved_html}
      <form method='post'>
        <textarea name='content' style='min-height:62vh'>{esc(content)}</textarea>
        <p><button class='btn success' type='submit'>Speichern</button> <a class='btn2' href='/config'>Abbrechen</a></p>
      </form>
      <p class='muted small'>Beim Speichern wird wie bisher eine Sicherung der Datei erzeugt.</p>
    </div>
    """
    return layout("Einstellungen", body)


@app.post("/config/{filename}")
def config_file_save(filename: str, content: str = Form("")):
    ensure_dirs()
    if filename not in CONFIG_FILES:
        raise HTTPException(status_code=404)
    write_text_backup(CONFIG_DIR / filename, content)
    return RedirectResponse(f"/config/{quote(filename)}?saved=1", status_code=303)




# ============================================================
# LERNLISTEN-HILFSFUNKTIONEN - Fix WebUI 2.5.1
# ============================================================

def parse_learning_lines(path: Path) -> list[tuple[int, str]]:
    """Liest Lernlisten robust ein.

    Rückgabe: Liste aus (Original-Zeilennummer, Inhalt).
    Leerzeilen und Kommentarzeilen werden übersprungen, die Zeilennummer
    bleibt aber erhalten, damit Übernehmen/Ignorieren/Löschen die richtige
    Originalzeile entfernt.
    """
    if not path.exists():
        return []
    result: list[tuple[int, str]] = []
    for idx, line in enumerate(read_text(path).splitlines()):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        result.append((idx, stripped))
    return result


def _ist_datum_oder_zeitstempel(text: str) -> bool:
    t = str(text or "").strip()
    return bool(re.match(r"^\d{4}-\d{2}-\d{2}(?:[ T]\d{2}:\d{2}:\d{2})?$", t) or re.match(r"^\d{1,2}\.\d{1,2}\.\d{2,4}", t))


def _ist_zu_langer_lernwert(text: str) -> bool:
    t = re.sub(r"\s+", " ", str(text or "").strip())
    return len(t) > 90 or len(t.split()) > 10


def _kurzer_lernwert(text: str, limit: int = 120) -> str:
    t = re.sub(r"\s+", " ", str(text or "").strip())
    if len(t) <= limit:
        return t
    return t[:limit].rstrip() + " …"


def parse_learning_candidate(line: str, kind: str = "") -> str:
    """Ermittelt den eigentlichen Vorschlagswert aus verschiedenen Lernlistenformaten.

    Unterstützt besonders das aktuelle Service-Format:
    Datum|Art|Wert|Datei|Zusatz
    Dadurch wird nicht mehr fälschlich das Datum oder die Datei als Vorschlag angezeigt.
    """
    raw = (line or "").strip()
    if not raw:
        return ""

    if raw.startswith("{") and raw.endswith("}"):
        try:
            data = json.loads(raw)
            for key in ("wert", "value", "lieferant", "dokumenttyp", "name", "candidate"):
                value = str(data.get(key, "")).strip()
                if value:
                    return value
        except Exception:
            pass

    key_patterns = {"LIEFERANT", "DOKUMENTTYP", "WERT", "VALUE", "NAME", "KANDIDAT", "CANDIDATE"}
    for sep in ("|", ";", "\t"):
        parts = [p.strip() for p in raw.split(sep)]
        clean = [p for p in parts if p]
        if len(clean) >= 5 and _ist_datum_oder_zeitstempel(clean[0]) and clean[1].lower() in {"lieferant", "dokumenttyp"}:
            return clean[2]
        if len(clean) >= 2 and _ist_datum_oder_zeitstempel(clean[0]):
            # Altes Format: Datum|Wert|Mail|Betreff|Datei
            return clean[1]
        for part in clean:
            if "=" in part:
                k, v = part.split("=", 1)
                if k.strip().upper() in key_patterns and v.strip():
                    return v.strip()
        if len(clean) >= 2 and clean[0].lower() in {"lieferant", "dokumenttyp", "wert", "unbekannt"}:
            return clean[1]
        if len(clean) >= 1 and sep in raw:
            return clean[0]

    if ":" in raw:
        left, right = raw.split(":", 1)
        if left.strip().lower() in {"lieferant", "dokumenttyp", "wert", "vorschlag"} and right.strip():
            return right.strip()

    return raw


def parse_learning_details(line: str, kind: str = "") -> dict[str, str]:
    """Bereitet eine Lernlisten-Zeile für die Kartenansicht auf.

    Rückgabe-Felder:
    - wert: der eigentliche Vorschlag
    - art: Lieferant/Dokumenttyp
    - datei: Quelldokument
    - zeit: Zeitpunkt
    - zusatz: Zusatzhinweis, nicht als Vorschlagswert verwenden
    - warnung: Hinweis bei verdächtig langem Vorschlag
    """
    raw = (line or "").strip()
    details = {"wert": parse_learning_candidate(raw, kind), "art": "", "datei": "", "zeit": "", "zusatz": "", "warnung": ""}

    if raw.startswith("{") and raw.endswith("}"):
        try:
            data = json.loads(raw)
            details["wert"] = str(data.get("wert") or data.get("value") or data.get("lieferant") or data.get("dokumenttyp") or details["wert"]).strip()
            details["art"] = str(data.get("art") or data.get("type") or kind).strip()
            details["datei"] = str(data.get("datei") or data.get("file") or data.get("filename") or "").strip()
            details["zeit"] = str(data.get("zeit") or data.get("timestamp") or data.get("datum") or "").strip()
            details["zusatz"] = str(data.get("zusatz") or data.get("details") or data.get("grund") or "").strip()
        except Exception:
            pass
    else:
        for sep in ("|", ";", "\t"):
            if sep not in raw:
                continue
            parts = [p.strip() for p in raw.split(sep)]
            clean = [p for p in parts if p]
            if len(clean) >= 5 and _ist_datum_oder_zeitstempel(clean[0]) and clean[1].lower() in {"lieferant", "dokumenttyp"}:
                # Aktuell: Datum|Art|Wert|Datei|Zusatz
                details.update({"zeit": clean[0], "art": clean[1], "wert": clean[2], "datei": clean[3], "zusatz": sep.join(clean[4:]).strip()})
                break
            if len(clean) >= 5 and _ist_datum_oder_zeitstempel(clean[0]):
                # Alt: Datum|Wert|Mail|Betreff|Datei
                details.update({"zeit": clean[0], "wert": clean[1], "zusatz": f"Mail/Betreff: {clean[2]} {clean[3]}".strip(), "datei": clean[4]})
                break
            if len(clean) >= 4:
                details.update({"wert": parse_learning_candidate(raw, kind), "datei": clean[1], "zeit": clean[2], "zusatz": sep.join(clean[3:]).strip()})
                break

    if not details.get("art"):
        details["art"] = "Lieferant" if kind == "lieferanten" else "Dokumenttyp" if kind == "dokumenttypen" else "Vorschlag"

    details["wert"] = _kurzer_lernwert(details.get("wert", ""), 160)
    if _ist_zu_langer_lernwert(details.get("wert", "")):
        details["warnung"] = "Vorschlag wirkt wie Fließtext – bitte vor Übernahme kürzen oder löschen."
    return details

def remove_line(path: Path, index: int) -> str:
    """Entfernt eine Originalzeile aus einer Lernliste und gibt deren Inhalt zurück."""
    if not path.exists():
        return ""
    lines = read_text(path).splitlines()
    if index < 0 or index >= len(lines):
        return ""
    removed = lines.pop(index).strip()
    write_text_backup(path, "\n".join(lines).rstrip() + ("\n" if lines else ""))
    return removed



def add_learning_entry(kind: str, value: str, source: str = "Manuell", hint: str = "") -> None:
    """Schreibt einen manuellen Vorschlag in die richtige Lernliste.

    Wichtig: Lieferanten und Dokumenttypen haben getrennte Lernlisten.
    Das Format ist bewusst kompatibel zur neuen Kartenansicht:
    YYYY-MM-DD HH:MM:SS|Art|Wert|Quelle|Hinweis
    """
    if kind not in LEARNING_FILES:
        raise HTTPException(status_code=404)
    value = (value or "").strip()
    if not value:
        raise HTTPException(status_code=400, detail="Kein Vorschlagswert angegeben")

    cfg = LEARNING_FILES[kind]
    learn = CONFIG_DIR / cfg["learn"]
    learn.parent.mkdir(parents=True, exist_ok=True)

    art = "Lieferant" if kind == "lieferanten" else "Dokumenttyp" if kind == "dokumenttypen" else "Vorschlag"
    source = (source or "Manuell").strip() or "Manuell"
    hint = (hint or "Manuell hinzugefügt").strip() or "Manuell hinzugefügt"

    # Duplikate in derselben Lernliste vermeiden, aber nicht gegen die andere Liste prüfen.
    existing = read_text(learn).lower()
    if value.lower() in existing:
        return

    if not learn.exists():
        learn.write_text(
            "# Lernliste - geprüfte Einträge bitte in die passende Konfiguration übernehmen\n"
            "# Format: Zeitpunkt|Art|Wert|Quelle|Hinweis\n",
            encoding="utf-8",
        )

    stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    safe_source = source.replace("|", "/")
    safe_hint = hint.replace("|", "/")
    safe_value = value.replace("|", "/")
    with open(learn, "a", encoding="utf-8") as f:
        f.write(f"{stamp}|{art}|{safe_value}|{safe_source}|{safe_hint}\n")


@app.post("/learning/{kind}/add")
def learning_add(kind: str, value: str = Form(""), source: str = Form("Manuell"), hint: str = Form("")):
    add_learning_entry(kind, value, source, hint)
    return RedirectResponse("/learning", status_code=303)

@app.get("/learning", response_class=HTMLResponse)
def learning_index() -> HTMLResponse:
    ensure_dirs()
    sections = []
    for key, cfg in LEARNING_FILES.items():
        path = CONFIG_DIR / cfg["learn"]
        entries = parse_learning_lines(path)
        cards = []
        art_default = "Lieferant" if key == "lieferanten" else "Dokumenttyp"
        ziel_datei = cfg.get("target", "")
        for idx, line in entries:
            details = parse_learning_details(line, key)
            candidate = (details.get("wert", "") or "").strip()
            art_html = details.get("art", "") or art_default
            file_html = details.get("datei", "") or "-"
            zeit_html = details.get("zeit", "") or "-"
            zusatz_html = details.get("zusatz", "") or "-"
            suspect = bool(details.get("warnung")) or _ist_zu_langer_lernwert(candidate)
            card_class = "learn-item suspect" if suspect else "learn-item"
            headline = "⚠ OCR-Text prüfen" if suspect else candidate
            warnung_html = f"<div class='flash warn small'><b>Bitte prüfen:</b> {esc(details.get('warnung') or 'Dieser Vorschlag wirkt wie ein OCR-Fließtext. Vor Übernahme bitte im Eingabefeld auf den echten Wert kürzen.')}</div>" if suspect else ""
            bedeutung = "Dieser Vorschlag wird als Lieferant übernommen." if key == "lieferanten" else "Dieser Vorschlag wird als Dokumenttyp übernommen."
            cards.append(f"""
            <div class='{card_class}'>
              <div>
                <div><span class='learn-kind-pill'>🧠 {esc(art_html)}</span><span class='learn-source'>📄 {esc(file_html)}</span></div>
                <h3 class='learn-title'>{esc(headline)}</h3>
                <div class='learn-subtitle'>{esc(bedeutung)} Ziel: <span class='folder-name'>{esc(ziel_datei)}</span></div>
                {warnung_html}
                <div class='learn-valuebox'>
                  <div class='caption'>Vorschlag</div>
                  <div class='value'>{esc(candidate or '—')}</div>
                </div>
                <div class='learn-fields'>
                  <div class='learn-field'><span>Gemeint ist</span><b>{esc(art_default)}</b></div>
                  <div class='learn-field'><span>Dokument / Quelle</span><b>{esc(file_html)}</b></div>
                  <div class='learn-field'><span>Zeitpunkt</span><b>{esc(zeit_html)}</b></div>
                  <div class='learn-field'><span>Kriterium / Hinweis</span><b>{esc(zusatz_html)}</b></div>
                </div>
                <details style='margin-top:10px'><summary class='muted small'>Originalzeile anzeigen</summary><div class='learn-raw'>{esc(line)}</div></details>
              </div>
              <div class='learn-actions'>
                <form method='post' action='/learning/{key}/{idx}/accept' data-working='Vorschlag wird übernommen ...'>
                  <input type='text' name='value' value='{esc(candidate)}' title='Diesen Wert vor dem Übernehmen bei Bedarf korrigieren'>
                  <button class='action-btn action-accept' type='submit'>✓ Übernehmen</button>
                </form>
                <div class='actionbar'>
                  <form method='post' action='/learning/{key}/{idx}/ignore' data-working='Vorschlag wird ignoriert ...'>
                    <button class='action-btn action-ignore' type='submit'>⚠ Ignorieren</button>
                  </form>
                  <form method='post' action='/learning/{key}/{idx}/delete' data-working='Vorschlag wird gelöscht ...' data-confirm-title='Lernlisten-Eintrag löschen?' data-confirm-message='Diesen Vorschlag wirklich aus der Lernliste entfernen?' data-confirm-details='Der Eintrag wird nur aus der Lernliste entfernt. Die Lieferanten-/Dokumenttypen-Konfiguration bleibt unverändert.' data-confirm-kind='eco-modal-danger' data-confirm-ok='Ja, löschen'>
                    <button class='action-btn action-delete' type='submit'>🗑 Löschen</button>
                  </form>
                </div>
              </div>
            </div>""")
        content = "<div class='learn-empty'>Keine offenen Einträge in dieser Lernliste.</div>" if not cards else f"<div class='learn-list'>{''.join(cards)}</div>"
        sections.append(f"""
        <div class='card'>
          <div class='section-head'><h2>{esc(cfg['label'])}</h2><span class='count-badge'>{len(entries)} offen</span></div>
          <p class='small muted'>Lernliste: <code>{esc(str(path))}</code><br>Ziel beim Übernehmen: <code>{esc(ziel_datei)}</code></p>
          <details class='hint' style='margin-bottom:14px'>
            <summary><b>＋ Manuell zur {esc(art_default)}-Lernliste hinzufügen</b></summary>
            <form method='post' action='/learning/{key}/add' class='toolbar' data-working='Vorschlag wird in die Lernliste geschrieben ...'>
              <input type='text' name='value' placeholder='{esc(art_default)} eingeben' required style='min-width:320px'>
              <input type='text' name='source' value='Manuell' placeholder='Quelle/Datei' style='min-width:160px'>
              <input type='text' name='hint' placeholder='Suchwort/Kriterium, z. B. Logo, Text im Kopfbereich' style='min-width:300px'>
              <button class='action-btn action-add' type='submit'>＋ Hinzufügen</button>
            </form>
            <p class='small muted'>Der Eintrag landet nur in dieser Lernliste und wird erst mit „Übernehmen“ in die Konfiguration geschrieben.</p>
          </details>
          {content}
        </div>""")
    intro = """
    <div class='card learning-intro'>
      <div class='section-head'><div><h2>Lernlisten 2.0</h2><p class='muted'>„Vorschlag“ bedeutet jetzt eindeutig: In der Lieferanten-Lernliste ist es ein Lieferant, in der Dokumenttypen-Lernliste ein Dokumenttyp. OCR-Fließtext wird markiert und sollte vor dem Übernehmen gekürzt oder gelöscht werden.</p></div><a class='btn2' href='/'>Dashboard</a></div>
      <div class='mini-help'>
        <div><b>✓ Übernehmen</b><span class='muted small'>schreibt den korrigierbaren Wert in die passende Konfigurationsdatei.</span></div>
        <div><b>⚠ Ignorieren</b><span class='muted small'>verschiebt den Vorschlag in die Ignoriert-Liste.</span></div>
        <div><b>🗑 Löschen</b><span class='muted small'>entfernt nur diesen Lernlisten-Eintrag.</span></div>
      </div>
    </div>"""
    return layout("Lernlisten", intro + "".join(sections))

def append_config_line_clean(path: Path, line: str):
    """
    V1.2: Fügt Konfigurationszeilen ohne zusätzliche Leerzeilen an.
    Alte Versionen schrieben bewusst "\n" vor und nach dem Eintrag; dadurch
    entstanden zwischen Lieferanten/Dokumenttypen immer Leerzeilen.
    """
    line = (line or "").strip()
    if not line:
        return

    text = read_text(path)
    lines = text.splitlines()

    # Trailing-Leerzeilen entfernen, Inhalt sonst unverändert lassen.
    while lines and not lines[-1].strip():
        lines.pop()

    lines.append(line)
    write_text_backup(path, "\n".join(lines) + "\n")

@app.post("/learning/{kind}/{index}/accept")
def learning_accept(kind: str, index: int, value: str = Form(...)):
    if kind not in LEARNING_FILES:
        raise HTTPException(status_code=404)
    cfg = LEARNING_FILES[kind]
    learn = CONFIG_DIR / cfg["learn"]
    target = CONFIG_DIR / cfg["target"]
    original = remove_line(learn, index)

    # Wert aus Formular bevorzugen, aber gegen den alten v0.4.1-Fehler absichern.
    value = value.strip()
    if value.lower() in {"lieferant", "dokumenttyp", "unbekannt"}:
        value = parse_learning_candidate(original, kind).strip()

    if value and value.lower() not in {"lieferant", "dokumenttyp", "unbekannt"}:
        # Ziel-Format bleibt einfach: Anzeigename|Suchwort. Danach kann man es in Konfiguration feinbearbeiten.
        line = f"{value}|{value}"
        existing = read_text(target).lower()
        if line.lower() not in existing:
            append_config_line_clean(target, line)
    return RedirectResponse("/learning", status_code=303)


@app.post("/learning/{kind}/{index}/ignore")
def learning_ignore(kind: str, index: int):
    if kind not in LEARNING_FILES:
        raise HTTPException(status_code=404)
    learn = CONFIG_DIR / LEARNING_FILES[kind]["learn"]
    line = remove_line(learn, index)
    ignored = learn.with_name(learn.stem + "_ignoriert.txt")
    with open(ignored, "a", encoding="utf-8") as f:
        f.write(line + "\n")
    return RedirectResponse("/learning", status_code=303)


@app.post("/learning/{kind}/{index}/delete")
def learning_delete(kind: str, index: int):
    if kind not in LEARNING_FILES:
        raise HTTPException(status_code=404)
    remove_line(CONFIG_DIR / LEARNING_FILES[kind]["learn"], index)
    return RedirectResponse("/learning", status_code=303)






@app.get("/config-form/box", response_class=HTMLResponse)
def box_form() -> HTMLResponse:
    z = lese_zaehlerstand()
    tz = lese_test_zaehlerstand()
    body = f"""
    <div class='card'>
      <h2>Ablagekennung & Zähler</h2>
      <p class='muted'>Produktiv- und Testzähler sind getrennt. Der Testzähler erzeugt Barcodes mit TEST-Präfix und verändert den produktiven Zähler nicht.</p>
      <form method='post'>
        {render_input('ABLAGEKENNUNG', 'Ablagekennung', lade_ablagekennung(), 'text', 'Beispiele: BOX001, ORDNER003, ARCHIV2026')}
        <div class='counter-form-grid'>
          <div class='counter-form-card productive'>
            <h3>Produktivzähler <span class='counter-badge productive'>ECHT</span></h3>
            <p class='muted small'>Für Scanner und Outlook. Diese Nummern landen im echten Archiv.</p>
            {render_input('MONAT', 'Produktiv-Monat', f"{int(z['monat']):02d}", 'number', 'Monat für den produktiven Zählerstand.')}
            {render_input('JAHR', 'Produktiv-Jahr', str(int(z['jahr'])), 'number', 'Jahr für den produktiven Zählerstand.')}
            {render_input('ZAEHLER', 'Produktiver Zähler', str(int(z['zaehler'])), 'number', 'Dieser Wert wird für den nächsten echten Archiv-Barcode verwendet.')}
            <div class='flash'>
              <b>Nächster Produktiv-Barcode:</b><br>
              <span class='pill'>{esc(berechne_naechsten_barcode())}</span>
            </div>
          </div>
          <div class='counter-form-card test'>
            <h3>Testzähler <span class='counter-badge test'>TEST</span></h3>
            <p class='test-note'>Nur Testcenter. Verändert den produktiven Zähler nicht.</p>
            {render_input('TEST_PREFIX', 'Test-Präfix', str(tz.get('prefix','TEST')), 'text', 'Standard: TEST')}
            {render_input('TEST_MONAT', 'Test-Monat', f"{int(tz['monat']):02d}", 'number', 'Monat für den Testzählerstand.')}
            {render_input('TEST_JAHR', 'Test-Jahr', str(int(tz['jahr'])), 'number', 'Jahr für den Testzählerstand.')}
            {render_input('TEST_ZAEHLER', 'Testzähler', str(int(tz['zaehler'])), 'number', 'Dieser Wert wird nur für Test-Barcodes verwendet.')}
            <div class='flash warn'>
              <b>Nächster Test-Barcode:</b><br>
              <span class='pill'>{esc(berechne_naechsten_test_barcode())}</span>
            </div>
          </div>
        </div>
        <p><button class='btn' type='submit'>Speichern</button> <a class='btn2' href='/config'>Zurück zur Übersicht</a> <a class='btn2' href='/config/box_konfiguration.txt'>box_konfiguration.txt</a> <a class='btn2' href='/config/zaehler.txt'>zaehler.txt</a> <a class='btn2' href='/config/test_zaehler.txt'>test_zaehler.txt</a></p>
      </form>
      <p class='muted small'>Beim Speichern werden Sicherungen der geänderten Dateien erzeugt.</p>
    </div>
    """
    return layout("Ablagekennung & Zähler", body)


@app.post("/config-form/box")
def save_box_form(
    ABLAGEKENNUNG: str = Form("BOX001"),
    MONAT: str = Form("1"),
    JAHR: str = Form("2026"),
    ZAEHLER: str = Form("1"),
    TEST_PREFIX: str = Form("TEST"),
    TEST_MONAT: str = Form("1"),
    TEST_JAHR: str = Form("2026"),
    TEST_ZAEHLER: str = Form("1"),
):
    speichere_ablagekennung(ABLAGEKENNUNG)
    try:
        speichere_zaehlerstand(int(MONAT), int(JAHR), int(ZAEHLER))
    except Exception:
        pass
    try:
        speichere_test_zaehlerstand(int(TEST_MONAT), int(TEST_JAHR), int(TEST_ZAEHLER), TEST_PREFIX)
    except Exception:
        pass
    return RedirectResponse("/config-form/box", status_code=303)

@app.get("/config-form/import_optionen", response_class=HTMLResponse)
def import_optionen_form() -> HTMLResponse:
    path = CONFIG_DIR / "import_optionen_konfiguration.txt"
    values, _ = parse_key_value_config(path)
    defaults = {
        "OUTLOOK_BOXCODE": "0",
        "OUTLOOK_ETIKETTENDRUCK": "0",
        "OUTLOOK_ZAEHLER_ERHOEHEN": "0",
    }
    data = {**defaults, **values}
    body = f"""
    <div class='card'><h2>Import-Optionen</h2>
      <form method='post'>
        {render_checkbox('OUTLOOK_BOXCODE', 'BOX-Code für Outlook-Dokumente erzeugen', data.get('OUTLOOK_BOXCODE','0'), 'Normalerweise aus, wenn Mail-PDFs keinen Papier-BOX-Code brauchen.')}
        {render_checkbox('OUTLOOK_ETIKETTENDRUCK', 'Etikettendruck für Outlook-Dokumente erlauben', data.get('OUTLOOK_ETIKETTENDRUCK','0'), 'Nur aktivieren, wenn auch Mail-Dokumente ein Etikett bekommen sollen.')}
        {render_checkbox('OUTLOOK_ZAEHLER_ERHOEHEN', 'Zähler bei Outlook-Dokumenten erhöhen', data.get('OUTLOOK_ZAEHLER_ERHOEHEN','0'), 'Normalerweise aus, damit digitale Mail-Anhänge den Papier-Zähler nicht verbrauchen.')}
        <p><button class='btn' type='submit'>Speichern</button> <a class='btn2' href='/config'>Zurück zur Übersicht</a> <a class='btn2' href='/config/import_optionen_konfiguration.txt'>Als Text bearbeiten</a></p>
      </form>
      <p class='muted small'>Beim Speichern wird automatisch eine .bak-Sicherung erzeugt.</p>
    </div>"""
    return layout("Import-Optionen", body)


@app.post("/config-form/import_optionen")
def save_import_optionen(
    OUTLOOK_BOXCODE: str | None = Form(None),
    OUTLOOK_ETIKETTENDRUCK: str | None = Form(None),
    OUTLOOK_ZAEHLER_ERHOEHEN: str | None = Form(None),
):
    path = CONFIG_DIR / "import_optionen_konfiguration.txt"
    ordered = {
        "OUTLOOK_BOXCODE": checkbox_value(OUTLOOK_BOXCODE),
        "OUTLOOK_ETIKETTENDRUCK": checkbox_value(OUTLOOK_ETIKETTENDRUCK),
        "OUTLOOK_ZAEHLER_ERHOEHEN": checkbox_value(OUTLOOK_ZAEHLER_ERHOEHEN),
    }
    write_text_backup(path, merge_key_value_content(path, ordered, "Import-Optionen"))
    return RedirectResponse("/config-form/import_optionen", status_code=303)


@app.get("/config-form/dateiname", response_class=HTMLResponse)
def dateiname_form() -> HTMLResponse:
    path = CONFIG_DIR / "dateiname_konfiguration.txt"
    values, _ = parse_key_value_config(path)
    defaults = {
        "PDF_UMBENENNEN": "1",
        "PDF_DATEINAME_SCHEMA": "{DATUM}_{LIEFERANT}_{NUMMER}",
        "PDF_DATEINAME_FALLBACK_DATUM": "HEUTE",
        "PDF_DATEINAME_MAX_LAENGE": "160",
        "PDF_PRODUKTIV_ARCHIV_AKTIV": "1",
        "PDF_PRODUKTIV_ARCHIV_ORDNER": "_erledigt/_produktiv",
        "PDF_TEST_ARCHIV_AKTIV": "1",
        "PDF_TEST_ARCHIV_ORDNER": "_erledigt/_test",
        "PDF_DATEINAME_LOG": "_logs/pdf_dateinamen.log",
    }
    data = {**defaults, **values}
    body = f"""
    <div class='card'><h2>PDF-Dateinamen</h2>
      <p class='muted'>Hier steuerst du, ob der Scan-Service fertig verarbeitete PDFs mit Datum, Lieferant und Nummer benennt.</p>
      <form method='post'>
        {render_checkbox('PDF_UMBENENNEN', 'PDFs sprechend umbenennen', data.get('PDF_UMBENENNEN','1'), 'Globale Aktivierung für die automatische Dateinamenbildung.')}
        {render_input('PDF_DATEINAME_SCHEMA', 'Dateinamen-Schema', data.get('PDF_DATEINAME_SCHEMA','{DATUM}_{LIEFERANT}_{NUMMER}'), 'text', 'Platzhalter: {DATUM}, {LIEFERANT}, {DOKUMENTTYP}, {NUMMER}, {RECHNR}, {VERSICHERUNGSNR}, {AUFTRAGNR}, {BESTELLNR}, {LIEFERSCHEINNR}, {BOXCODE}')}
        {render_input('PDF_DATEINAME_MAX_LAENGE', 'Maximale Dateinamenlänge', data.get('PDF_DATEINAME_MAX_LAENGE', data.get('PDF_MAX_LAENGE','160')), 'number', 'Empfohlen: 120 bis 180 Zeichen.')}
        <div class='soft-title'>Ablage trennen</div>
        {render_checkbox('PDF_PRODUKTIV_ARCHIV_AKTIV', 'Produktive Kopie ablegen', data.get('PDF_PRODUKTIV_ARCHIV_AKTIV','1'), 'Produktive Scans/Outlook-PDFs werden zusätzlich umbenannt archiviert.')}
        {render_input('PDF_PRODUKTIV_ARCHIV_ORDNER', 'Produktiv-Archivordner', data.get('PDF_PRODUKTIV_ARCHIV_ORDNER','_erledigt/_produktiv'), 'text', 'Relativ zum Basisordner oder absoluter Pfad.')}
        {render_checkbox('PDF_TEST_ARCHIV_AKTIV', 'Test-PDFs getrennt archivieren', data.get('PDF_TEST_ARCHIV_AKTIV','1'), 'Testcenter-PDFs werden getrennt von echten Dokumenten abgelegt.')}
        {render_input('PDF_TEST_ARCHIV_ORDNER', 'Test-Archivordner', data.get('PDF_TEST_ARCHIV_ORDNER','_erledigt/_test'), 'text', 'Empfohlen: _erledigt/_test oder _regression/archiv.')}
        {render_input('PDF_DATEINAME_LOG', 'Protokolldatei alter/neuer Name', data.get('PDF_DATEINAME_LOG','_logs/pdf_dateinamen.log'), 'text', 'Protokolliert Quelle, alter Dateiname, neuer Dateiname und Zielpfad.')}
        <div class='hint'>
          <b>Beispiel:</b><br>
          <span class='kbd'>{{DATUM}}_{{LIEFERANT}}_{{NUMMER}}</span><br><br>
          ergibt z. B. <span class='kbd'>2026-05-13_EDEKA Foodservice_5560075991.pdf</span>
        </div>
        <p><button class='btn' type='submit'>Speichern</button> <a class='btn2' href='/config'>Zurück zur Übersicht</a> <a class='btn2' href='/config/dateiname_konfiguration.txt'>Als Text bearbeiten</a></p>
      </form>
      <p class='muted small'>Beim Speichern wird automatisch eine .bak-Sicherung erzeugt.</p>
    </div>"""
    return layout("PDF-Dateinamen", body)


@app.post("/config-form/dateiname")
def save_dateiname_optionen(
    PDF_UMBENENNEN: str | None = Form(None),
    PDF_DATEINAME_SCHEMA: str = Form("{DATUM}_{LIEFERANT}_{NUMMER}"),
    PDF_DATEINAME_MAX_LAENGE: str = Form("160"),
    PDF_PRODUKTIV_ARCHIV_AKTIV: str | None = Form(None),
    PDF_PRODUKTIV_ARCHIV_ORDNER: str = Form("_erledigt/_produktiv"),
    PDF_TEST_ARCHIV_AKTIV: str | None = Form(None),
    PDF_TEST_ARCHIV_ORDNER: str = Form("_erledigt/_test"),
    PDF_DATEINAME_LOG: str = Form("_logs/pdf_dateinamen.log"),
):
    path = CONFIG_DIR / "dateiname_konfiguration.txt"
    ordered = {
        "PDF_UMBENENNEN": checkbox_value(PDF_UMBENENNEN),
        "PDF_DATEINAME_SCHEMA": (PDF_DATEINAME_SCHEMA or "{DATUM}_{LIEFERANT}_{NUMMER}").strip(),
        "PDF_DATEINAME_FALLBACK_DATUM": "HEUTE",
        "PDF_DATEINAME_MAX_LAENGE": (PDF_DATEINAME_MAX_LAENGE or "160").strip(),
        "PDF_PRODUKTIV_ARCHIV_AKTIV": checkbox_value(PDF_PRODUKTIV_ARCHIV_AKTIV),
        "PDF_PRODUKTIV_ARCHIV_ORDNER": (PDF_PRODUKTIV_ARCHIV_ORDNER or "_erledigt/_produktiv").strip(),
        "PDF_TEST_ARCHIV_AKTIV": checkbox_value(PDF_TEST_ARCHIV_AKTIV),
        "PDF_TEST_ARCHIV_ORDNER": (PDF_TEST_ARCHIV_ORDNER or "_erledigt/_test").strip(),
        "PDF_DATEINAME_LOG": (PDF_DATEINAME_LOG or "_logs/pdf_dateinamen.log").strip(),
    }
    write_text_backup(path, merge_key_value_content(path, ordered, "PDF-Dateinamen"))
    return RedirectResponse("/config-form/dateiname", status_code=303)


@app.get("/config-form/benachrichtigung", response_class=HTMLResponse)
def benachrichtigung_form() -> HTMLResponse:
    path = CONFIG_DIR / "benachrichtigung_konfiguration.txt"
    values, _ = parse_key_value_config(path)
    defaults = {
        "BENACHRICHTIGUNG_AKTIV": "1",
        "BENACHRICHTIGUNG_PER_OUTLOOK": "1",
        "EMPFAENGER": "heinz-georg.hepp@t-online.de",
        "MAIL_BETREFF": "ecoDMS Lernliste - neuer Eintrag",
        "MAX_MAILS_PRO_LAUF": "3",
    }
    data = {**defaults, **values}
    body = f"""
    <div class='card'><h2>Benachrichtigung</h2>
      <form method='post'>
        {render_checkbox('BENACHRICHTIGUNG_AKTIV', 'Benachrichtigungen aktiv', data.get('BENACHRICHTIGUNG_AKTIV','1'), 'Schaltet die Lernlisten-Benachrichtigung grundsätzlich ein oder aus.')}
        {render_checkbox('BENACHRICHTIGUNG_PER_OUTLOOK', 'Per Outlook senden', data.get('BENACHRICHTIGUNG_PER_OUTLOOK','1'), 'Verwendet das lokale Outlook für die Meldung.')}
        {render_input('EMPFAENGER', 'Empfänger', data.get('EMPFAENGER',''), 'text', 'E-Mail-Adresse für Benachrichtigungen.')}
        {render_input('MAIL_BETREFF', 'Mail-Betreff', data.get('MAIL_BETREFF',''), 'text', 'Betreff der Benachrichtigung.')}
        {render_input('MAX_MAILS_PRO_LAUF', 'Max. Mails pro Lauf', data.get('MAX_MAILS_PRO_LAUF','3'), 'number', 'Begrenzt, wie viele Benachrichtigungen je Durchlauf erzeugt werden.')}
        <p><button class='btn' type='submit'>Speichern</button> <a class='btn2' href='/config'>Zurück zur Übersicht</a> <a class='btn2' href='/config/benachrichtigung_konfiguration.txt'>Als Text bearbeiten</a></p>
      </form>
      <p class='muted small'>Beim Speichern wird automatisch eine .bak-Sicherung erzeugt.</p>
    </div>"""
    return layout("Benachrichtigung", body)


@app.post("/config-form/benachrichtigung")
def save_benachrichtigung(
    BENACHRICHTIGUNG_AKTIV: str | None = Form(None),
    BENACHRICHTIGUNG_PER_OUTLOOK: str | None = Form(None),
    EMPFAENGER: str = Form(""),
    MAIL_BETREFF: str = Form(""),
    MAX_MAILS_PRO_LAUF: str = Form("3"),
):
    path = CONFIG_DIR / "benachrichtigung_konfiguration.txt"
    try:
        max_mails = str(max(0, int(str(MAX_MAILS_PRO_LAUF or "0"))))
    except ValueError:
        max_mails = "3"
    ordered = {
        "BENACHRICHTIGUNG_AKTIV": checkbox_value(BENACHRICHTIGUNG_AKTIV),
        "BENACHRICHTIGUNG_PER_OUTLOOK": checkbox_value(BENACHRICHTIGUNG_PER_OUTLOOK),
        "EMPFAENGER": EMPFAENGER.strip(),
        "MAIL_BETREFF": MAIL_BETREFF.strip(),
        "MAX_MAILS_PRO_LAUF": max_mails,
    }
    write_text_backup(path, merge_key_value_content(path, ordered, "Benachrichtigung bei neuen Lernlisten-Einträgen"))
    return RedirectResponse("/config-form/benachrichtigung", status_code=303)

def tail_lines_text(path: Path, max_lines: int = 500) -> str:
    text = read_text(path, max_chars=1_000_000)
    if max_lines <= 0:
        return text
    lines = text.splitlines()
    return "\n".join(lines[-max_lines:])


def render_log_lines(text: str) -> str:
    if not text:
        return esc("Noch keine Logdaten vorhanden.")
    out = []
    for ln in text.splitlines():
        cls = "info"
        if " - ERROR - " in ln or " ERROR " in ln:
            cls = "error"
        elif " - WARNING - " in ln or " WARNING " in ln:
            cls = "warning"
        out.append(f"<div class='logline {cls}'>{esc(ln)}</div>")
    return "".join(out)


@app.get("/logs", response_class=HTMLResponse)
def logs(log: str = "ecodms_scan_service.log", level: str = "ALLE", lines: int = 500, auto: str = "0", q: str = "") -> HTMLResponse:
    available_logs = list_log_files()
    if log not in available_logs:
        log = available_logs[0] if available_logs else "ecodms_scan_service.log"
    level = (level or "ALLE").upper()
    try:
        lines = int(lines)
    except Exception:
        lines = 500
    if lines not in [100, 500, 1000, 0]:
        lines = 500

    log_rel = Path(str(log).replace("\\", "/"))
    if log_rel.is_absolute() or ".." in log_rel.parts:
        log_rel = Path(available_logs[0]) if available_logs else Path("ecodms_scan_service.log")
    if str(log_rel).replace("\\", "/").lower() == "massentest/massentest.log":
        log_path = MASSTEST_LOG_DIR / "massentest.log"
    else:
        log_path = LOG_DIR / log_rel
    text = tail_lines_text(log_path, lines)

    if level in {"ERROR", "WARNING", "INFO"}:
        filtered = []
        for ln in text.splitlines():
            if f" - {level} - " in ln or f" {level} " in ln:
                filtered.append(ln)
        text = "\n".join(filtered)
    q = (q or "").strip()
    if q:
        q_low = q.lower()
        text = "\n".join([ln for ln in text.splitlines() if q_low in ln.lower()])

    options = "".join(f"<option value='{esc(f)}' {'selected' if f == log else ''}>{esc(f)}</option>" for f in available_logs)
    levels = "".join(f"<option value='{esc(x)}' {'selected' if x == level else ''}>{esc(x)}</option>" for x in ["ALLE", "ERROR", "WARNING", "INFO"])
    line_options = "".join(f"<option value='{n}' {'selected' if n == lines else ''}>{'Gesamte Datei' if n == 0 else 'Letzte ' + str(n) + ' Zeilen'}</option>" for n in [100, 500, 1000, 0])
    auto_checked = "checked" if auto == "1" else ""
    auto_js = "setInterval(()=>{ if(document.getElementById('auto').checked){ location.href = buildUrl(); } }, 5000);" if auto == "1" else ""
    body = f"""
    <div class='card'>
      <h2>Logs</h2>
      <form method='get' id='logForm' class='toolbar'>
        <select name='log' onchange='submitLogForm()'>{options}</select>
        <select name='level' onchange='submitLogForm()'>{levels}</select>
        <select name='lines' onchange='submitLogForm()'>{line_options}</select>
        <input type='text' name='q' value='{esc(q)}' placeholder='Logs durchsuchen ...' style='min-width:260px'>
        <label class='small'><input id='auto' name='auto' value='1' type='checkbox' {auto_checked} onchange='submitLogForm()'> Auto-Refresh 5s</label>
        <button class='btn2' type='submit'>Suchen / neu laden</button>
        <a class='btn2' href='/logs?log={esc(log)}&level=ALLE&lines=500'>Filter zurücksetzen</a>
        <button class='btn2' type='button' onclick='scrollBottom()'>Zum Ende</button>
        <button class='btn2' type='button' onclick='scrollTopLog()'>Zum Anfang</button>
      </form>
      <p class='muted small'>Aktive Logdatei: <b>{esc(log)}</b> · Suche: <b>{esc(q) if q else '—'}</b> · Pfad: <code>{esc(str(log_path))}</code> · Tastatur: <span class='kbd'>Strg</span>+<span class='kbd'>Ende</span>, <span class='kbd'>Strg</span>+<span class='kbd'>Pos1</span>, <span class='kbd'>Ende</span>, <span class='kbd'>Pos1</span></p>
      <div id='logbox' class='logbox' tabindex='0'>{render_log_lines(text)}</div>
    </div>
    <script>
      const box = document.getElementById('logbox');
      function scrollBottom(){{ box.scrollTop = box.scrollHeight; box.focus(); }}
      function scrollTopLog(){{ box.scrollTop = 0; box.focus(); }}
      function submitLogForm(){{ document.getElementById('logForm').submit(); }}
      function buildUrl(){{
        const f = document.getElementById('logForm');
        const params = new URLSearchParams(new FormData(f));
        return '/logs?' + params.toString();
      }}
      document.addEventListener('keydown', function(e){{
        if((e.ctrlKey && e.key === 'End') || (!e.ctrlKey && e.key === 'End')){{ e.preventDefault(); scrollBottom(); }}
        if((e.ctrlKey && e.key === 'Home') || (!e.ctrlKey && e.key === 'Home')){{ e.preventDefault(); scrollTopLog(); }}
      }});
      window.addEventListener('load', scrollBottom);
      {auto_js}
    </script>
    """
    return layout("Logs", body)


def import_scan_service():
    service_path = SERVICE_DIR / "ecodms_scan_service.py"
    if not service_path.exists():
        raise RuntimeError(f"Scan-Service nicht gefunden: {service_path}")

    # Schutz gegen versehentlich falsch kopierte Dateien: In _service muss der Scan-Service
    # liegen, nicht die WebUI. Sonst entstehen Fehler wie "name 'app' is not defined" beim Testlauf.
    try:
        service_text = service_path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        service_text = ""
    probe = service_text[:20000]
    if "FastAPI(" in probe or "@app." in probe or "HTMLResponse" in probe:
        raise RuntimeError(
            "In _service\\ecodms_scan_service.py liegt offenbar keine Scan-Service-Datei, "
            "sondern WebUI/FastAPI-Code. Bitte die aktuelle Scan-Service-Datei "
            "ecodms_scan_service_v5_7_26_lieferanten_isolation.py nach "
            "C:\\ScanSnap_Roh-Scan-ecoDMS\\_service\\ecodms_scan_service.py kopieren."
        )

    module_name = f"ecodms_scan_service_runtime_{int(time.time() * 1000)}"
    spec = importlib.util.spec_from_file_location(module_name, service_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Scan-Service konnte nicht geladen werden")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    try:
        spec.loader.exec_module(module)
    except NameError as e:
        if "app" in str(e):
            raise RuntimeError(
                "Scan-Service konnte nicht geladen werden: 'app' ist nicht definiert. "
                "Das deutet fast immer darauf hin, dass im _service-Ordner versehentlich eine WebUI-Datei "
                "oder eine beschädigte Datei als ecodms_scan_service.py gespeichert wurde."
            ) from e
        raise
    return module




def expected_path_for(pdf_name: str) -> Path:
    name = Path(pdf_name).name
    return EXPECTED_DIR / f"{name}.expected"


def parse_expected_text(text: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in (text or "").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip().upper()] = value.strip()
    return values


def expected_to_text(values: dict[str, str]) -> str:
    lines = ["# Sollwerte für den automatischen Testlauf", "# Format: FELD=WERT", ""]
    preferred = [
        "LIEFERANT", "DOKUMENTTYP", "DOKUMENTKLASSE", "OCR_QUALITAET", "RECHDATUM", "RECHNR", "KUNDENNR",
        "AUFTRAGNR", "BESTELLNR", "LIEFERSCHEINNR", "VERSICHERUNGSNR", "GESAMTBETRAG",
    ]
    done = set()
    for key in preferred:
        if key in values:
            lines.append(f"{key}={values.get(key,'')}")
            done.add(key)
    for key in sorted(k for k in values if k not in done):
        lines.append(f"{key}={values[key]}")
    return "\n".join(lines) + "\n"


def norm_compare(value: object) -> str:
    text = str(value or "").strip()
    text = text.replace("€", "")
    text = text.replace(" ", "")
    text = text.replace("\u00a0", "")
    return text.lower()



def status_path_for(pdf_name: str) -> Path:
    name = Path(pdf_name).name
    return STATUS_DIR / f"{name}.status.json"


def read_test_status(pdf_name: str) -> dict[str, object]:
    path = status_path_for(pdf_name)
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def write_test_status(pdf_name: str, status: str, details: str = "", service_version: str = "") -> None:
    ensure_dirs()
    data = {
        "status": status,
        "details": details,
        "timestamp": datetime.now().strftime("%d.%m.%Y %H:%M:%S"),
        "service_version": service_version or get_scan_service_version(),
        "webui_version": APP_VERSION,
    }
    try:
        status_path_for(pdf_name).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass


def delete_test_status(pdf_name: str) -> None:
    try:
        p = status_path_for(pdf_name)
        if p.exists():
            p.unlink()
    except Exception:
        pass


def is_manual_test_passed(pdf_name: str) -> bool:
    """True, wenn ein Testfall bewusst manuell freigegeben wurde.

    Wichtig: Solche Sonderfälle dürfen beim Volltest nicht wieder als
    Abweichung/Aufgabe auftauchen, solange der Nutzer die Freigabe nicht
    durch neue Sollwerte oder Statuslöschung aufhebt.
    """
    st = read_test_status(pdf_name)
    if str(st.get("status") or "") != "geprueft_ok":
        return False
    if bool(st.get("manual_passed")):
        return True
    details = str(st.get("details") or "").lower()
    return ("manuell bestanden" in details) or ("bewusst" in details and "bestanden" in details)


def write_manual_test_status(pdf_name: str, details: str = "Manuell bestanden: Referenz sind die aktuell gespeicherten Sollwerte", service_version: str = "") -> None:
    ensure_dirs()
    data = {
        "status": "geprueft_ok",
        "details": details,
        "manual_passed": True,
        "timestamp": datetime.now().strftime("%d.%m.%Y %H:%M:%S"),
        "service_version": service_version or get_scan_service_version(),
        "webui_version": APP_VERSION,
    }
    try:
        status_path_for(pdf_name).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass


def get_scan_service_version() -> str:
    try:
        service = import_scan_service()
        return str(getattr(service, "VERSION", ""))
    except Exception:
        return ""


STATUS_LABELS = {
    "ungeprueft": ("⬜", "Noch nicht geprüft", "row-untested"),
    "geprueft_ok": ("✓", "Erfolgreich geprüft", "row-expected"),
    "abweichung": ("⚠", "Abweichung gefunden", "row-missing"),
    "sollwerte_fehlen": ("?", "Sollwerte fehlen", "row-missing"),
    "fehler": ("⚠", "Fehler beim Test", "row-missing"),
    "bearbeitet": ("★", "Bearbeitet", "row-current"),
}


def test_status_display(pdf_name: str, has_expected: bool) -> tuple[str, str, str, str]:
    st = read_test_status(pdf_name)
    status = str(st.get("status") or "")
    if not status:
        status = "ungeprueft" if has_expected else "sollwerte_fehlen"
    symbol, label, row_class = STATUS_LABELS.get(status, STATUS_LABELS["ungeprueft"])
    timestamp = str(st.get("timestamp") or "")
    service_version = str(st.get("service_version") or "")
    info_parts = [label]
    if timestamp:
        info_parts.append(timestamp)
    if service_version:
        info_parts.append(f"Service {service_version}")
    return symbol, " · ".join(info_parts), row_class, status


def test_progress_stats(pdfs: list[Path]) -> dict[str, int]:
    stats = {"total": len(pdfs), "ok": 0, "abweichung": 0, "fehler": 0, "ohne_soll": 0, "offen": 0, "bearbeitet": 0}
    for p in pdfs:
        has_expected = expected_path_for(p.name).exists()
        _sym, _info, _cls, status = test_status_display(p.name, has_expected)
        if status == "geprueft_ok":
            stats["ok"] += 1
        elif status == "abweichung":
            stats["abweichung"] += 1
        elif status == "fehler":
            stats["fehler"] += 1
        elif status == "sollwerte_fehlen":
            stats["ohne_soll"] += 1
        elif status == "bearbeitet":
            stats["bearbeitet"] += 1
        else:
            stats["offen"] += 1
    return stats



def _trim_debug_for_delta(debug_text: str, max_chars: int = 1800) -> str:
    text = str(debug_text or '').strip()
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "\n... [gekürzt]"


def chatgpt_delta_text(filename: str, expected: dict[str, str] | None, actual: dict[str, str] | None, comparisons: list[tuple] | None = None, error: str | None = None, debug_text: str = "") -> str:
    expected = expected or {}
    actual = actual or {}
    comparisons = comparisons or []
    lines = [
        "=== REGRESSIONSTEST EINZELDOKUMENT ===",
        f"Dokument: {filename}",
        f"WebUI-Version: {APP_VERSION}",
        "",
    ]
    if error:
        lines += ["Status: FEHLER", f"Fehler: {error}", "", "=== ENDE ==="]
        return "\n".join(lines)
    diffs = [c for c in comparisons if len(c) >= 4 and not c[3]]
    if not expected:
        lines += ["Status: OHNE SOLLWERTE", "", "Ist-Werte:"]
        for k in sorted(actual):
            if str(actual.get(k, '')).strip():
                lines.append(f"{k}={actual.get(k,'')}")
        lines += ["", "=== ENDE ==="]
        return "\n".join(lines)
    if not diffs:
        lines += ["Status: BESTANDEN", "", "Keine Abweichungen gefunden.", "", "=== ENDE ==="]
        return "\n".join(lines)
    lines += ["Status: ABWEICHUNG", "", "Abweichungen:"]
    for field, exp, act, _ok in diffs:
        lines += [f"- {field}", f"  Soll: {exp}", f"  Ist : {act}"]
    lines += ["", "Sollwerte:"]
    for k, v in expected.items():
        lines.append(f"{k}={v}")
    lines += ["", "Ist-Werte:"]
    for k in sorted(actual):
        if str(actual.get(k, '')).strip():
            lines.append(f"{k}={actual.get(k,'')}")
    if debug_text:
        lines += ["", "OCR-/Debug-Auszug:", _trim_debug_for_delta(debug_text)]
    lines += ["", "=== ENDE ==="]
    return "\n".join(lines)


def chatgpt_delta_all_text(report_items: list[dict] | None) -> str:
    report_items = report_items or []
    lines = [
        "=== REGRESSIONSTEST GESAMT ===",
        f"WebUI-Version: {APP_VERSION}",
        f"Zeitpunkt: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}",
        "",
    ]
    any_problem = False
    for item in report_items:
        file = item.get('file', '')
        error = item.get('error', '')
        missing = item.get('missing_expected', False)
        diffs = item.get('diffs', []) or []
        if error:
            any_problem = True
            lines += [f"Dokument: {file}", "Status: FEHLER", f"Fehler: {error}", ""]
        elif missing:
            any_problem = True
            lines += [f"Dokument: {file}", "Status: OHNE SOLLWERTE", ""]
        elif diffs:
            any_problem = True
            lines += [f"Dokument: {file}", "Status: ABWEICHUNG"]
            for d in diffs:
                lines += [f"- {d.get('field','')}", f"  Soll: {d.get('expected','')}", f"  Ist : {d.get('actual','')}"]
            lines.append("")
    if not any_problem:
        lines += ["Status: BESTANDEN", "Keine Abweichungen gefunden.", ""]
    lines.append("=== ENDE ===")
    return "\n".join(lines)


PREFERRED_EXPECTED_FIELDS = [
    "LIEFERANT", "DOKUMENTTYP", "DOKUMENTKLASSE", "RECHDATUM", "RECHNR", "KUNDENNR",
    "AUFTRAGNR", "BESTELLNR", "LIEFERSCHEINNR", "VERSICHERUNGSNR", "GESAMTBETRAG",
]


def clean_actual_values(meta: dict[str, object], filled_only: bool = False) -> dict[str, str]:
    """Bereitet erkannte Ist-Werte als Sollwerte auf.

    Wichtig für Regressionstests:
    - Standardmäßig werden ALLE bevorzugten Felder gespeichert, auch leere.
    - So sieht man später auch Abweichungen wie Soll=leer / Ist=Wert.
    - Mit filled_only=True gibt es weiterhin die alte Kurzform.
    """
    cleaned: dict[str, str] = {}
    upper_meta = {str(k).upper(): str(v or "").strip() for k, v in (meta or {}).items()}
    for key in PREFERRED_EXPECTED_FIELDS:
        value = upper_meta.get(key, "").strip()
        if filled_only and not value:
            continue
        if value.lower() in {"unbekannt", "none", "null"}:
            value = ""
        cleaned[key] = value
    return cleaned


def save_expected_from_meta(pdf_name: str, meta: dict[str, object], overwrite: bool = True, filled_only: bool = False) -> tuple[bool, str]:
    """Speichert Ist-Werte als Sollwerte.

    Standard: vorhandene Datei wird überschrieben und alle bevorzugten Felder werden gespeichert.
    Dadurch funktionieren echte Regressionstests auch mit bewusst leeren Sollwerten.
    """
    exp_path = expected_path_for(pdf_name)
    if exp_path.exists() and not overwrite:
        return False, "Sollwerte bereits vorhanden"
    values = clean_actual_values(meta, filled_only=filled_only)
    exp_path.parent.mkdir(parents=True, exist_ok=True)
    write_text_backup(exp_path, expected_to_text(values))
    write_test_status(pdf_name, "bearbeitet", "Sollwerte gespeichert")
    return True, "Sollwerte erzeugt"



def ensure_test_barcode_for_pdf(pdf_path: Path) -> str:
    """Stellt sicher, dass jedes Testdokument genau eine TEST-Kennung bekommt.

    V2.6.4:
    - Neue Uploads bekommen die Kennung weiterhin sofort beim Upload.
    - Alte bereits vorhandene Testdokumente bekommen beim ersten Testlauf nachträglich
      eine TEST-Kennung. Dadurch zählt der Testzähler sichtbar hoch, ohne bei jedem
      erneuten Regressionstest endlos weiterzulaufen.
    """
    try:
        marker_files = [
            pdf_path.with_suffix(pdf_path.suffix + ".testmeta"),
            pdf_path.with_suffix(".testmeta"),
        ]
        for marker in marker_files:
            if marker.exists():
                data = read_text(marker)
                m = re.search(r"TEST_BARCODE=(.+)", data)
                if m:
                    return m.group(1).strip()
                return ""
        barcode = erhoehe_test_zaehler()
        schreibe_test_upload_meta(pdf_path, barcode)
        return barcode
    except Exception:
        return ""

def run_single_regression(pdf_path: Path) -> tuple[dict[str, str], dict[str, str], list[tuple[str, str, str, bool]], str | None]:
    """Liefert meta, expected, comparisons, error."""
    try:
        ensure_test_barcode_for_pdf(pdf_path)
        service = import_scan_service()
        meta = service.erzeuge_meta_daten(pdf_path)
        meta = {str(k).upper(): str(v or "") for k, v in meta.items()}
        expected = parse_expected_text(read_text(expected_path_for(pdf_path.name)))
        comparisons: list[tuple[str, str, str, bool]] = []
        for key, expected_value in expected.items():
            actual_value = meta.get(key, "")
            ok = norm_compare(actual_value) == norm_compare(expected_value)
            comparisons.append((key, expected_value, actual_value, ok))
        return meta, expected, comparisons, None
    except Exception as e:
        return {}, parse_expected_text(read_text(expected_path_for(pdf_path.name))), [], str(e)



# ============================================================
# MASSENTEST / ALTARCHIV 2.0 - getrennt vom Produktivsystem
# ============================================================

MASSTEST_VIEWER_DIR = MASSTEST_DIR / "viewer"
MASSTEST_DUPLICATE_DIR = MASSTEST_DIR / "dubletten"
MASSTEST_TRACE_FILE = MASSTEST_LOG_DIR / "massentest_testlauf_trace.log"

MASSTEST_FIELDS = [
    "id", "lauf_id", "alter_dateiname", "neuer_dateiname",
    "lieferant", "dokumenttyp", "dokumentdatum",
    "rechnr", "aktenzeichen", "kundennr", "auftragnr", "bestellnr", "lieferscheinnr", "versicherungsnr", "gesamtbetrag",
    "ocr_qualitaet", "status", "pruefstatus", "workflow_status", "vergleich_ok", "abweichungen",
    "notiz", "aufgabe_id", "pdf_datei", "hinweis", "zeitpunkt", "letzter_test", "workflow_updated",
    "fachlich_validiert", "fachlich_validiert_am", "fachlich_validiert_von", "fachlich_validiert_hinweis", "manuell_nicht_bestanden",
    "soll_lieferant", "soll_dokumenttyp", "soll_dokumentdatum", "soll_rechnr", "soll_aktenzeichen", "soll_kundennr",
    "soll_auftragnr", "soll_bestellnr", "soll_lieferscheinnr", "soll_versicherungsnr", "soll_gesamtbetrag",
    "soll_neuer_dateiname"
]

MASSTEST_COMPARE = [
    ("Neuer Dateiname", "neuer_dateiname", "soll_neuer_dateiname"),
    ("Lieferant", "lieferant", "soll_lieferant"),
    ("Dokumenttyp", "dokumenttyp", "soll_dokumenttyp"),
    ("Dokumentdatum", "dokumentdatum", "soll_dokumentdatum"),
    ("RECHNR", "rechnr", "soll_rechnr"),
    ("AKTENZEICHEN", "aktenzeichen", "soll_aktenzeichen"),
    ("KUNDENNR", "kundennr", "soll_kundennr"),
    ("AUFTRAGNR", "auftragnr", "soll_auftragnr"),
    ("BESTELLNR", "bestellnr", "soll_bestellnr"),
    ("LIEFERSCHEINNR", "lieferscheinnr", "soll_lieferscheinnr"),
    ("VERSICHERUNGSNR", "versicherungsnr", "soll_versicherungsnr"),
    ("GESAMTBETRAG", "gesamtbetrag", "soll_gesamtbetrag"),
]

MASSTEST_STATUS_ORDER = ["ungeprueft", "bearbeitung", "neu", "erkannt", "referenz", "geprueft_ok", "abweichung", "aufgabe", "ok", "ausreisser", "ignoriert"]
MASSTEST_STATUS_LABELS = {
    "alle": "Alle",
    "neu": "Neu",
    "erkannt": "Erkannt",
    "referenz": "Referenz vorhanden",
    "geprueft_ok": "Fehlerfrei geprüft",
    "abweichung": "Abweichung",
    "aufgabe": "Aufgabe",
    "ok": "Test bestanden",
    "ausreisser": "Sonderfall",
    "ignoriert": "Ignoriert",
    "ungeprueft": "Ungeprüft",
    "bearbeitung": "Referenz vorhanden",
}

MASSTEST_WORKFLOW_STATES = {"NEU", "ERKANNT", "REFERENZ", "GEPRUEFT_OK", "ABWEICHUNG", "AUFGABE", "TEST_BESTANDEN", "AUSREISSER", "IGNORIERT"}
MASSTEST_WORKFLOW_LABELS = {
    "NEU": "Neu",
    "ERKANNT": "Erkannt",
    "REFERENZ": "Referenz vorhanden",
    "GEPRUEFT_OK": "Fehlerfrei geprüft",
    "ABWEICHUNG": "Abweichung",
    "AUFGABE": "Aufgabe",
    "TEST_BESTANDEN": "Test bestanden",
    "AUSREISSER": "Sonderfall",
    "IGNORIERT": "Ignoriert",
}


def ensure_massentest_dirs() -> None:
    for p in [
        MASSTEST_DIR, MASSTEST_ZIP_DIR, MASSTEST_UNPACKED_DIR, MASSTEST_DONE_DIR,
        MASSTEST_ERROR_DIR, MASSTEST_LOG_DIR, MASSTEST_RESULTS_DIR, MASSTEST_VIEWER_DIR, MASSTEST_DUPLICATE_DIR,
    ]:
        try:
            p.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass


def massentest_log(text: str) -> None:
    try:
        ensure_massentest_dirs()
        with open(MASSTEST_LOG_DIR / "massentest.log", "a", encoding="utf-8") as f:
            f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {text}\n")
    except Exception:
        pass



def massentest_trace_reset(titel: str = "Testlauf-Trace") -> None:
    """Startet ein nachvollziehbares Trace-Protokoll für den nächsten Massentestlauf."""
    try:
        ensure_massentest_dirs()
        header = [
            "=" * 72,
            f"{titel} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"WebUI: {APP_VERSION}",
            "=" * 72,
            "",
        ]
        MASSTEST_TRACE_FILE.write_text("\n".join(header), encoding="utf-8")
    except Exception:
        pass


def massentest_trace(text: str) -> None:
    """Schreibt eine Trace-Zeile. Fehler im Trace dürfen den Test nie abbrechen."""
    try:
        ensure_massentest_dirs()
        with open(MASSTEST_TRACE_FILE, "a", encoding="utf-8") as f:
            f.write(f"{datetime.now().strftime('%H:%M:%S')} | {text}\n")
    except Exception:
        pass


def massentest_trace_list(title: str, values, limit: int = 300) -> None:
    try:
        vals = list(values or [])
        massentest_trace(f"{title}: {len(vals)}")
        for i, value in enumerate(vals[:limit], start=1):
            massentest_trace(f"  {i:04d}. {value}")
        if len(vals) > limit:
            massentest_trace(f"  ... {len(vals)-limit} weitere nicht angezeigt")
    except Exception as e:
        massentest_trace(f"TRACE-LIST-FEHLER {title}: {e}")


def massentest_trace_read(max_lines: int = 500) -> str:
    try:
        if not MASSTEST_TRACE_FILE.exists():
            return "Noch kein Testlauf-Trace vorhanden."
        lines = MASSTEST_TRACE_FILE.read_text(encoding="utf-8", errors="replace").splitlines()
        if len(lines) > max_lines:
            lines = [f"... gekürzt: letzte {max_lines} von {len(lines)} Zeilen ...", ""] + lines[-max_lines:]
        return "\n".join(lines)
    except Exception as e:
        return f"Trace konnte nicht gelesen werden: {e}"

def massentest_progress_write(aktion: str, current: int, total: int, current_file: str = "", status: str = "running", message: str = "") -> None:
    try:
        ensure_massentest_dirs()
        total = max(0, int(total or 0))
        current = max(0, int(current or 0))
        percent = int(round((current / total) * 100)) if total else 0
        data = {
            "aktion": aktion,
            "current": current,
            "total": total,
            "percent": max(0, min(100, percent)),
            "current_file": current_file or "",
            "status": status,
            "message": message or "",
            "updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        MASSTEST_PROGRESS_JSON.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass


def massentest_progress_start(aktion: str, total: int, message: str = "") -> None:
    massentest_progress_write(aktion, 0, total, "", "running", message or f"{aktion} gestartet")


def massentest_progress_finish(aktion: str, total: int, message: str = "") -> None:
    massentest_progress_write(aktion, total, total, "", "done", message or f"{aktion} abgeschlossen")


def massentest_safe_pdf_name(name: str) -> str:
    raw = Path(str(name or "dokument.pdf").replace("\\", "/")).name
    raw = re.sub(r"[<>:\"/\\|?*]+", "_", raw).strip(" ._-")
    if not raw.lower().endswith(".pdf"):
        raw += ".pdf"
    return raw or f"massentest_{int(time.time())}.pdf"


def massentest_safe_upload_name(name: str, default_ext: str = "") -> str:
    raw = Path(str(name or "upload").replace("\\", "/")).name
    raw = re.sub(r"[<>:\"/\\|?*]+", "_", raw).strip(" ._-")
    if not raw:
        raw = f"upload_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
    if default_ext and not Path(raw).suffix:
        raw += default_ext
    return raw


def massentest_unique_upload_path(folder: Path, filename: str, default_ext: str = "") -> Path:
    folder.mkdir(parents=True, exist_ok=True)
    filename = massentest_safe_upload_name(filename, default_ext=default_ext)
    p = folder / filename
    if not p.exists():
        return p
    stem, suffix = p.stem, p.suffix or default_ext or ""
    for i in range(2, 10000):
        k = folder / f"{stem}_{i:03d}{suffix}"
        if not k.exists():
            return k
    return folder / f"upload_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}{suffix}"


def massentest_unique_path(folder: Path, filename: str) -> Path:
    folder.mkdir(parents=True, exist_ok=True)
    filename = massentest_safe_pdf_name(filename)
    p = folder / filename
    if not p.exists():
        return p
    stem, suffix = p.stem, p.suffix or ".pdf"
    for i in range(2, 10000):
        k = folder / f"{stem}_{i:03d}{suffix}"
        if not k.exists():
            return k
    return folder / f"massentest_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.pdf"


def massentest_make_id(row: dict | None = None, index: int = 0) -> str:
    basis = str((row or {}).get("alter_dateiname") or (row or {}).get("pdf_datei") or "")
    clean = re.sub(r"[^A-Za-z0-9]+", "-", basis).strip("-").lower()[:48]
    return f"mt-{index+1:04d}-{clean or datetime.now().strftime('%Y%m%d%H%M%S%f')}"


def massentest_current_lauf_id() -> str:
    return datetime.now().strftime("MT-%Y%m%d-%H%M%S")


def massentest_normalize_row(row: dict | None, index: int = 0) -> dict[str, str]:
    row = row or {}
    out = {k: str(row.get(k, "")) for k in MASSTEST_FIELDS}
    if not out.get("id"):
        out["id"] = massentest_make_id(row, index)
    if not out.get("pruefstatus"):
        out["pruefstatus"] = "ungeprueft"
    if out["pruefstatus"] == "ok":
        # ok bleibt kompatibel mit Altbestand, wird in der Oberfläche als Freigegeben angezeigt.
        pass
    if not out.get("pdf_datei"):
        out["pdf_datei"] = out.get("alter_dateiname", "")
    if not out.get("lauf_id"):
        out["lauf_id"] = "ALT"
    return out


def massentest_soll_field_count(row: dict[str, str]) -> int:
    """Fachliche Sollwerte, ohne automatisch gebildeten Soll-Dateinamen."""
    return sum(1 for _label, _ist, soll in MASSTEST_COMPARE if soll != "soll_neuer_dateiname" and str(row.get(soll, "") or "").strip())


def massentest_has_reference(row: dict[str, str]) -> bool:
    return massentest_soll_field_count(row) > 0


def massentest_derive_workflow(row: dict[str, str]) -> str:
    """Leitet für Altbestände einen eindeutigen Workflow-Zustand ab."""
    ws = str(row.get("workflow_status") or "").strip().upper()
    if ws in MASSTEST_WORKFLOW_STATES:
        return ws
    ps = str(row.get("pruefstatus") or "").strip().lower()
    if ps == "ok":
        return "TEST_BESTANDEN"
    if ps == "geprueft_ok":
        return "GEPRUEFT_OK"
    if ps == "aufgabe":
        return "AUFGABE"
    if ps == "abweichung":
        return "ABWEICHUNG"
    if ps == "ausreisser":
        return "AUSREISSER"
    if ps == "ignoriert":
        return "IGNORIERT"
    if massentest_has_reference(row):
        return "REFERENZ"
    if str(row.get("status") or "").strip() or str(row.get("neuer_dateiname") or "").strip() or str(row.get("lieferant") or "").strip() or str(row.get("dokumenttyp") or "").strip():
        return "ERKANNT"
    return "NEU"


def massentest_pruefstatus_from_workflow(ws: str) -> str:
    return {
        "NEU": "ungeprueft",
        "ERKANNT": "ungeprueft",
        "REFERENZ": "bearbeitung",
        "GEPRUEFT_OK": "geprueft_ok",
        "ABWEICHUNG": "abweichung",
        "AUFGABE": "aufgabe",
        "TEST_BESTANDEN": "ok",
        "AUSREISSER": "ausreisser",
        "IGNORIERT": "ignoriert",
    }.get(str(ws or "").upper(), "ungeprueft")


def massentest_set_workflow(row: dict[str, str], ws: str, message: str = "") -> dict[str, str]:
    ws = str(ws or "NEU").upper()
    if ws not in MASSTEST_WORKFLOW_STATES:
        ws = "NEU"
    row["workflow_status"] = ws
    row["pruefstatus"] = massentest_pruefstatus_from_workflow(ws)
    row["workflow_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if message:
        row["letzter_test"] = message
    return row


def massentest_normalize_workflow(row: dict[str, str]) -> dict[str, str]:
    ws = massentest_derive_workflow(row)
    row["workflow_status"] = ws
    row["pruefstatus"] = massentest_pruefstatus_from_workflow(ws)
    return row





def massentest_canonical_pdf_key(name: str) -> str:
    """Kanonischer Schlüssel für Massentest-PDFs.

    Dateien, die durch wiederholtes Entpacken/Zurücklegen als *_002.pdf,
    *_003.pdf usw. entstanden sind, gelten als dasselbe Quelldokument.
    So werden beim erneuten Lauf keine 127er-Dubletten zu 254/381 Ergebnissen.
    """
    raw = Path(str(name or "").replace("\\", "/")).name
    raw = re.sub(r"\s+", " ", raw).strip().lower()
    if raw.endswith(".pdf"):
        stem = raw[:-4]
        stem = re.sub(r"_[0-9]{3}$", "", stem)
        raw = stem + ".pdf"
    return raw


def massentest_row_key(row: dict | None) -> str:
    """Stabiler Schlüssel pro Massentest-PDF.

    Wichtig für erneute Läufe: Ein PDF darf im Ergebnisbestand nur einmal
    vorkommen. Neue Erkennungsläufe aktualisieren den vorhandenen Datensatz,
    statt eine weitere Ergebniszeile anzuhängen.
    """
    row = row or {}
    for key in ("alter_dateiname", "pdf_datei"):
        value = str(row.get(key, "") or "").strip()
        if value:
            return massentest_canonical_pdf_key(value)
    return str(row.get("id", "") or "").strip().lower()


def massentest_dedupe_results(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    """Bereinigt Dubletten nach PDF-Schlüssel.

    Bei Konflikten gewinnt der neuere/spätere Datensatz, aber vorhandene
    Sollwerte, Notizen und Aufgaben-IDs aus älteren Datensätzen bleiben erhalten,
    wenn der neue Datensatz diese Felder leer lässt.
    """
    out: list[dict[str, str]] = []
    pos: dict[str, int] = {}
    for i, raw in enumerate(rows or []):
        row = massentest_normalize_row(raw, i)
        key = massentest_row_key(row)
        if not key:
            out.append(row)
            continue
        if key not in pos:
            pos[key] = len(out)
            out.append(row)
            continue
        old = out[pos[key]]
        merged = dict(old)
        merged.update(row)
        # Prüferdaten aus dem älteren Datensatz erhalten, wenn sie im neuen leer sind.
        for k in list(MASSTEST_FIELDS):
            if k.startswith("soll_") or k in {"notiz", "aufgabe_id", "fachlich_validiert", "fachlich_validiert_am", "fachlich_validiert_von", "fachlich_validiert_hinweis", "manuell_nicht_bestanden"}:
                if not str(merged.get(k, "") or "").strip() and str(old.get(k, "") or "").strip():
                    merged[k] = old.get(k, "")
        if not str(merged.get("pruefstatus", "") or "").strip():
            merged["pruefstatus"] = old.get("pruefstatus", "ungeprueft")
        out[pos[key]] = massentest_normalize_row(merged, pos[key])
    # IDs nach dem Bereinigen stabilisieren, falls durch Dubletten Lücken entstanden sind.
    return [massentest_normalize_row(r, i) for i, r in enumerate(out)]


def massentest_upsert_row(rows: list[dict[str, str]], new_row: dict[str, str]) -> list[dict[str, str]]:
    """Fügt Ergebnis ein oder ersetzt vorhandenes Ergebnis derselben PDF."""
    key = massentest_row_key(new_row)
    normalized_new = massentest_normalize_row(new_row, len(rows))
    for i, row in enumerate(rows):
        if massentest_row_key(row) == key:
            old = row
            merged = dict(old)
            merged.update(normalized_new)
            for k in list(MASSTEST_FIELDS):
                if k.startswith("soll_") or k in {"notiz", "aufgabe_id", "fachlich_validiert", "fachlich_validiert_am", "fachlich_validiert_von", "fachlich_validiert_hinweis", "manuell_nicht_bestanden"}:
                    if not str(merged.get(k, "") or "").strip() and str(old.get(k, "") or "").strip():
                        merged[k] = old.get(k, "")
            rows[i] = massentest_normalize_row(merged, i)
            return rows
    rows.append(normalized_new)
    return rows


# ============================================================
# MASSENTEST-MANAGER / REFERENZSICHERUNG 3.6.0
# ============================================================

def massentest_reference_payload(row: dict[str, str]) -> dict[str, str]:
    """Extrahiert nur dauerhaft gepflegte Referenzdaten aus einer Ergebniszeile."""
    row = row or {}
    payload: dict[str, str] = {}
    for k in MASSTEST_FIELDS:
        if k.startswith("soll_") or k in {"notiz"}:
            v = str(row.get(k, "") or "")
            if v.strip():
                payload[k] = v
    # Zur Lesbarkeit im JSON mitführen, aber beim Merge nicht als IST-Wert nutzen.
    for k in ["alter_dateiname", "pdf_datei", "id"]:
        v = str(row.get(k, "") or "")
        if v.strip():
            payload[k] = v
    return payload


def massentest_reference_has_values(row: dict[str, str]) -> bool:
    return any(str(row.get(k, "") or "").strip() for k in row if k.startswith("soll_"))


def massentest_read_references() -> dict[str, dict[str, str]]:
    ensure_massentest_dirs()
    if not MASSTEST_REFERENCES_JSON.exists():
        return {}
    try:
        data = json.loads(MASSTEST_REFERENCES_JSON.read_text(encoding="utf-8"))
        if isinstance(data, list):
            items = data
        elif isinstance(data, dict):
            items = list(data.values())
        else:
            return {}
        refs: dict[str, dict[str, str]] = {}
        for i, raw in enumerate(items):
            if not isinstance(raw, dict):
                continue
            row = massentest_normalize_row(raw, i)
            key = massentest_row_key(row)
            if key and massentest_reference_has_values(row):
                refs[key] = massentest_reference_payload(row)
        return refs
    except Exception as e:
        try:
            massentest_log(f"Referenzwerte konnten nicht gelesen werden: {e}")
        except Exception:
            pass
        return {}


def massentest_save_references_from_rows(rows: list[dict[str, str]]) -> int:
    """Speichert/aktualisiert Sollwerte getrennt von temporären Testergebnissen."""
    ensure_massentest_dirs()
    refs = massentest_read_references()
    changed = 0
    for i, raw in enumerate(rows or []):
        row = massentest_normalize_row(raw, i)
        if not massentest_reference_has_values(row):
            continue
        key = massentest_row_key(row)
        if not key:
            continue
        payload = massentest_reference_payload(row)
        old = refs.get(key, {})
        merged = dict(old)
        merged.update(payload)
        refs[key] = merged
        changed += 1
    if changed:
        ordered = [refs[k] for k in sorted(refs.keys())]
        MASSTEST_REFERENCES_JSON.write_text(json.dumps(ordered, ensure_ascii=False, indent=2), encoding="utf-8")
    return changed


def massentest_apply_references(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    """Fügt gespeicherte Sollwerte nach einem neuen Erkennungslauf wieder an."""
    refs = massentest_read_references()
    if not refs:
        return rows
    out: list[dict[str, str]] = []
    for i, raw in enumerate(rows or []):
        row = massentest_normalize_row(raw, i)
        ref = refs.get(massentest_row_key(row), {})
        if ref:
            for k, v in ref.items():
                if k.startswith("soll_") or k == "notiz":
                    # Referenzwerte gewinnen, wenn der aktuelle Lauf keine gepflegte Sollbasis enthält.
                    if str(v or "").strip() and not str(row.get(k, "") or "").strip():
                        row[k] = v
        out.append(row)
    return out

def massentest_read_results() -> list[dict[str, str]]:
    ensure_massentest_dirs()
    if not MASSTEST_RESULTS_JSON.exists():
        return []
    try:
        data = json.loads(MASSTEST_RESULTS_JSON.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            return []
        rows = [massentest_normalize_row(x, i) for i, x in enumerate(data)]
        rows = massentest_apply_references(rows)
        return [massentest_normalize_workflow(r) for r in massentest_dedupe_results(rows)]
    except Exception:
        return []


def massentest_write_results(rows: list[dict[str, str]], persist_references: bool = False) -> None:
    ensure_massentest_dirs()
    # Ergebnislaeufe duerfen Sollwert-Referenzen nicht ueberschreiben.
    # Referenzen werden nur bei bewussten Referenz-/Sollwertaktionen persistiert.
    if persist_references:
        try:
            massentest_save_references_from_rows(rows or [])
        except Exception as e:
            massentest_log(f"Referenzsicherung vor Ergebnis-Schreiben fehlgeschlagen: {e}")
    rows_with_refs = massentest_apply_references([massentest_normalize_row(row, i) for i, row in enumerate(rows or [])])
    normalized = [massentest_normalize_workflow(r) for r in massentest_dedupe_results(rows_with_refs)]
    if persist_references:
        try:
            massentest_save_references_from_rows(normalized)
        except Exception as e:
            massentest_log(f"Referenzsicherung nach Ergebnis-Schreiben fehlgeschlagen: {e}")
    MASSTEST_RESULTS_JSON.write_text(json.dumps(normalized, ensure_ascii=False, indent=2), encoding="utf-8")
    with open(MASSTEST_RESULTS_CSV, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=MASSTEST_FIELDS, delimiter=";")
        writer.writeheader()
        writer.writerows(normalized)


def massentest_truthy(value: object) -> bool:
    text = str(value or "").strip().lower()
    return text in {"1", "true", "wahr", "ja", "yes", "y", "ok", "x"}


def massentest_row_status(row: dict) -> str:
    """Zentrale 4.0-Statusableitung fuer Massentest-Zeilen."""
    row = row or {}
    workflow_status = str(row.get("workflow_status", "") or "").strip().lower()
    pruefstatus = str(row.get("pruefstatus", "") or "").strip().lower()
    abweichungen = str(row.get("abweichungen", "") or "").strip()

    if massentest_truthy(row.get("manuell_nicht_bestanden")):
        return "abweichung"
    if workflow_status in {"fehler", "abweichung", "nicht_bestanden"}:
        return "abweichung"
    if pruefstatus in {"fehler", "abweichung", "nicht_bestanden"}:
        return "abweichung"
    if abweichungen:
        return "abweichung"
    if massentest_truthy(row.get("vergleich_ok")):
        return "bestanden"
    if workflow_status in {"bestanden", "test_bestanden", "geprueft_ok", "geprüft_ok"}:
        return "bestanden"
    if pruefstatus in {"bestanden", "ok", "geprueft_ok", "geprüft_ok"}:
        return "bestanden"
    return "offen"


def massentest_load_view_rows() -> list[dict[str, str]]:
    """Laedt Massentest-Zeilen fuer Anzeige/Fehlerbereich/Export mit zentralem Status."""
    rows = massentest_read_results()
    view_rows: list[dict[str, str]] = []
    for row in rows:
        view_row = dict(row or {})
        task_id = str(view_row.get("aufgabe_id") or view_row.get("task_id") or "").strip()
        view_row["task_id"] = task_id
        view_row["aufgabe_id"] = task_id
        view_row["row_status"] = massentest_row_status(view_row)
        view_rows.append(view_row)
    return view_rows



# ============================================================
# Qualitätscenter 3.8.0 – fachliche Validierung
# ============================================================

def massentest_is_fachlich_validiert(row: dict[str, str]) -> bool:
    """Ein Dokument ist fachlich validiert, wenn es bewusst manuell freigegeben wurde.

    Wichtig: Das ist eine zweite Stufe neben 'Test bestanden'. Test bestanden heißt
    technisch Soll/Ist gleich. Fachlich validiert heißt: PDF wurde sichtbar geprüft.
    """
    return str(row.get("fachlich_validiert", "") or "").strip() == "1"


def massentest_set_fachlich_validiert(row: dict[str, str], validiert: bool, note: str = "") -> dict[str, str]:
    row = dict(row or {})
    now_ui = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
    if validiert:
        row["fachlich_validiert"] = "1"
        row["fachlich_validiert_am"] = now_ui
        row["fachlich_validiert_von"] = "manuell"
        row["fachlich_validiert_hinweis"] = note or "PDF fachlich gegen Werte geprüft"
        row["letzter_test"] = (str(row.get("letzter_test", "") or "") + f" | fachlich validiert {now_ui}").strip(" |")
    else:
        row["fachlich_validiert"] = "0"
        row["fachlich_validiert_am"] = ""
        row["fachlich_validiert_von"] = ""
        row["fachlich_validiert_hinweis"] = note or "Validierung zurückgenommen"
        row["letzter_test"] = (str(row.get("letzter_test", "") or "") + f" | fachliche Validierung zurückgenommen {now_ui}").strip(" |")
    return row


def massentest_validation_stats(rows: list[dict[str, str]] | None = None) -> dict[str, int]:
    if rows is None:
        rows = massentest_read_results()
    total = len(rows)
    active_task_ids: set[str] = set()
    task_state_known = False
    try:
        for a in projekt_lade_aufgaben():
            aid = str(a.get("id", "") or "").strip()
            if aid and _pc_status_aktiv_2727(a):
                active_task_ids.add(aid)
        task_state_known = True
    except Exception:
        active_task_ids = set()
        task_state_known = False
    special = 0
    valid = 0
    nacharbeit = 0
    active_errors = 0
    valid_with_error = 0
    for r in rows:
        ws = massentest_derive_workflow(r)
        if ws == "AUSREISSER":
            special += 1
            continue
        row_status = massentest_row_status(r)
        try:
            _soll_count, diffs = massentest_diff_details(r)
        except Exception:
            diffs = []
        if diffs:
            row_status = "abweichung"
        if row_status == "abweichung":
            active_errors += 1
            if massentest_is_fachlich_validiert(r):
                valid_with_error += 1
            continue
        task_id = str(r.get("aufgabe_id", "") or "").strip()
        task_active = bool(task_id) and ((task_id in active_task_ids) if task_state_known else True)
        fachliche_marker = " ".join([
            str(r.get("fachlich_validiert_hinweis", "") or ""),
            str(r.get("fachlich_status", "") or ""),
            str(r.get("fachlicher_status", "") or ""),
            str(r.get("fachstatus", "") or ""),
            str(r.get("review_status", "") or ""),
            str(r.get("pruefstatus", "") or ""),
            str(r.get("workflow_status", "") or ""),
            str(r.get("notiz", "") or ""),
        ]).lower().replace("_", " ")
        is_fachliche_nacharbeit = (
            ("fachliche" in fachliche_marker and "nicht bestanden" in fachliche_marker)
            or "fachlich nachzuarbeiten" in fachliche_marker
            or "fachlich nachzubearbeiten" in fachliche_marker
            or "nachzuarbeiten" in fachliche_marker
            or "nachzubearbeiten" in fachliche_marker
        )
        if task_active and is_fachliche_nacharbeit:
            nacharbeit += 1
            continue
        if massentest_is_fachlich_validiert(r):
            valid += 1
    open_valid = max(0, total - valid - special - nacharbeit - active_errors)
    progress = int(round((valid / total) * 100)) if total else 0
    return {"total": total, "valid": valid, "open": open_valid, "nacharbeit": nacharbeit, "special": special, "active_errors": active_errors, "valid_with_error": valid_with_error, "progress": progress}

def massentest_validation_badge(row: dict[str, str]) -> str:
    if massentest_is_fachlich_validiert(row):
        ts = esc(row.get("fachlich_validiert_am", ""))
        return f"<span class='mini-tag' style='background:#ecfdf5;color:#166534;border:1px solid #bbf7d0'>⭐ Fachlich validiert{(' · ' + ts) if ts else ''}</span>"
    return "<span class='mini-tag' style='background:#fff7ed;color:#9a3412;border:1px solid #fed7aa'>○ Noch fachlich zu prüfen</span>"


def massentest_validation_action_html(row_id: str, row: dict[str, str], source: str = "list") -> str:
    rid = quote(str(row_id or row.get("id", "")))
    if massentest_is_fachlich_validiert(row):
        return (
            f"<form method='post' action='/test/massentest/validate/{rid}' style='display:inline' "
            f"data-confirm-title='Fachliche Validierung zurücknehmen?' "
            f"data-confirm-message='Dieses Dokument wird wieder als noch fachlich zu prüfen markiert.' "
            f"data-confirm-ok='Ja, zurücknehmen'>"
            f"<input type='hidden' name='action' value='entziehen'><input type='hidden' name='source' value='{esc(source)}'>"
            f"<button class='btn2' type='submit'>⭐ zurücknehmen</button></form>"
        )
    return (
        f"<form method='post' action='/test/massentest/validate/{rid}' style='display:inline' "
        f"data-confirm-title='Fachlich validieren?' "
        f"data-confirm-message='Bestätigen, dass PDF-Vorschau und Werte fachlich geprüft wurden.' "
        f"data-confirm-kind='eco-modal-success' data-confirm-ok='Ja, fachlich validieren'>"
        f"<input type='hidden' name='action' value='validieren'><input type='hidden' name='source' value='{esc(source)}'>"
        f"<button class='btn2 success' type='submit'>⭐ Fachlich validiert</button></form>"
    )


def massentest_quality_row_card(row: dict[str, str]) -> str:
    rid_raw = str(row.get("id", ""))
    rid = quote(rid_raw)
    symbol, status_info, row_class, area = massentest_overview_status(row)
    row_status = massentest_row_status(row)
    title = esc(row.get("alter_dateiname") or row.get("pdf_datei") or "Massentest-Dokument")
    valid = massentest_validation_badge(row) if row_status == "bestanden" and area not in {"special", "fachliche_nacharbeit"} else ""
    validation_actions = (
        massentest_validation_action_html(str(row.get('id','')), row, 'list')
        + massentest_validation_action_html(rid_raw, row, 'quality')
    ) if row_status == "bestanden" else ""
    soll_count, diffs = massentest_diff_details(row)
    diff_txt = f"{len(diffs)} Abweichung(en)" if diffs else ("Soll/Ist ok" if soll_count else "keine Sollwerte")
    return f"""
    <div class='massentest-card {row_class}' style='border:1px solid #d9e2f1;border-radius:14px;padding:14px;margin:10px 0;background:#fff;overflow:hidden'>
      <div style='display:flex;gap:10px;justify-content:space-between;align-items:flex-start;flex-wrap:wrap'>
        <div style='min-width:260px;flex:1'><b><span class='status-symbol'>{symbol}</span> {title}</b><br>
          <span class='muted small'>{esc(row.get('neuer_dateiname',''))}</span><br>{valid}
        </div>
        <div class='muted small' style='text-align:right'>{esc(diff_txt)}<br>{status_info}</div>
      </div>
      <div class='toolbar' style='margin-top:10px'>
        <a class='btn2' href='/test/massentest/fachlich/{rid}'>Fachlich prüfen</a>
        <a class='btn2' href='/test/massentest/detail/{rid}?source=fachlich'>Sollwerte</a>
        {validation_actions}
      </div>
    </div>
    """

def massentest_stats(rows: list[dict[str, str]] | None = None) -> dict[str, int]:
    ensure_massentest_dirs()
    if rows is None:
        rows = massentest_read_results()
    counts = {k: 0 for k in MASSTEST_STATUS_ORDER}
    # Altbestände können noch pruefstatus=ungeprueft/bearbeitung oder ganz fremde Werte enthalten.
    counts.setdefault("ungeprueft", 0)
    counts.setdefault("bearbeitung", 0)
    for r in rows:
        ps = (r.get("pruefstatus") or "ungeprueft").strip().lower()
        if ps not in counts:
            ps = "ungeprueft"
        counts[ps] = counts.get(ps, 0) + 1
    return {
        "wartend": len(list(MASSTEST_UNPACKED_DIR.glob("*.pdf"))) if MASSTEST_UNPACKED_DIR.exists() else 0,
        "verarbeitet": len(list(MASSTEST_DONE_DIR.glob("*.pdf"))) if MASSTEST_DONE_DIR.exists() else 0,
        "fehler": len(list(MASSTEST_ERROR_DIR.glob("*.pdf"))) if MASSTEST_ERROR_DIR.exists() else 0,
        "ergebnisse": len(rows),
        "ungeprueft": counts.get("ungeprueft", 0),
        "bearbeitung": counts.get("bearbeitung", 0),
        "ok": counts.get("ok", 0),
        "ausreisser": counts.get("ausreisser", 0),
        "abweichung": counts.get("abweichung", 0),
        "aufgabe": counts.get("aufgabe", 0),
        "ignoriert": counts.get("ignoriert", 0),
    }



def massentest_quality_stats(rows: list[dict[str, str]] | None = None) -> dict[str, int | str]:
    """Projektkennzahlen aus der zentralen 4.0-Statusableitung."""
    if rows is None:
        rows = massentest_read_results()
    total = len(rows)
    passed = deviations = open_docs = missing = ignored = special = 0
    counts = {"bestanden": 0, "abweichung": 0, "offen": 0}
    for row in rows:
        if massentest_derive_workflow(row) == "AUSREISSER":
            special += 1
            passed += 1
            continue
        row_status = massentest_row_status(row)
        counts[row_status] = counts.get(row_status, 0) + 1
        if row_status == "bestanden":
            passed += 1
        elif row_status == "abweichung":
            deviations += 1
        else:
            open_docs += 1
            if not massentest_has_reference(row):
                missing += 1
    progress = int(round((passed / total) * 100)) if total else 0
    if total == 0:
        status = "NOCH KEIN PRÜFBESTAND"
    elif passed == total:
        status = "ABGESCHLOSSEN"
    elif deviations:
        status = "AKTION ERFORDERLICH"
    elif open_docs:
        status = "IN BEARBEITUNG"
    else:
        status = "IN BEARBEITUNG"
    return {
        "total": total, "passed": passed, "ready": 0, "tasks": 0,
        "deviations": deviations, "missing": missing, "open": open_docs,
        "ignored": ignored,
        "special": special, "progress": progress, "status": status,
        "bestanden": counts.get("bestanden", 0), "abweichung": counts.get("abweichung", 0),
        "offen": counts.get("offen", 0), "neu": 0, "erkannt": 0, "referenz": 0,
    }


def massentest_compact_status_html(rows: list[dict[str, str]] | None = None) -> tuple[int, str]:
    if rows is None:
        rows = massentest_read_results()
    qstats = massentest_quality_stats(rows)
    vstats = massentest_validation_stats(rows)
    total = int(qstats.get("total", 0) or 0)
    line1 = f"{int(qstats.get('passed', 0) or 0)} bestanden · {int(qstats.get('deviations', 0) or 0)} Abweichungen · {int(qstats.get('open', 0) or 0)} Offen"
    line2 = f"{int(vstats.get('valid', 0) or 0)} fachlich validiert · {int(vstats.get('open', 0) or 0)} noch zu prüfen"
    line3 = f"Nachzubearbeiten: {int(vstats.get('nacharbeit', 0) or 0)} · Sonderfälle: {int(vstats.get('special', 0) or 0)}"
    return total, f"{line1}<br>{line2}<br>{line3}"


def massentest_match_key_variants(name: str) -> set[str]:
    """Robuste Schlüsselvarianten für Referenz- und Ergebnisabgleich.

    Ab 3.6.4: Wiederholte Massentestläufe erzeugen Dateien wie
    *_002.pdf, *_003.pdf, *_005.pdf. Für die Testlauf-Diagnose müssen diese
    Kopien als dasselbe Referenzdokument zählen. Zusätzlich werden leichte
    Schreibvarianten, Leerzeichen und Pfadbestandteile neutralisiert.
    """
    raw = Path(str(name or "").replace("\\", "/")).name.strip()
    if not raw:
        return set()
    raw = re.sub(r"\s+", " ", raw)
    values = set()

    def add(v: str):
        v = str(v or "").strip()
        if not v:
            return
        base = massentest_canonical_pdf_key(v)
        if base:
            values.add(base)
            values.add(base.lower())
            stem = base[:-4] if base.lower().endswith(".pdf") else base
            values.add(stem)
            # Zusatzrobustheit: Nummernsuffixe auch ohne .pdf entfernen.
            values.add(re.sub(r"_[0-9]{3}$", "", stem))
            # Sehr robuster Vergleichsschlüssel nur aus Buchstaben/Zahlen.
            compact = re.sub(r"[^a-z0-9äöüß]+", "", stem.lower())
            if compact:
                values.add(compact)

    add(raw)
    if raw.lower().endswith(".pdf"):
        stem = raw[:-4]
        add(re.sub(r"_[0-9]{3}$", "", stem) + ".pdf")
    return {v for v in values if v}


def massentest_row_match_keys(row: dict | None) -> set[str]:
    row = row or {}
    keys: set[str] = set()
    for field in ("alter_dateiname", "pdf_datei", "original_dateiname", "dateiname", "filename"):
        keys.update(massentest_match_key_variants(str(row.get(field, "") or "")))
    direct = massentest_row_key(row)
    if direct:
        keys.update(massentest_match_key_variants(direct))
    return keys


def massentest_laufdiagnose(rows: list[dict[str, str]] | None = None) -> dict[str, object]:
    """Vergleicht dauerhafte Referenzen mit dem letzten Ergebnislauf.

    Ab 3.6.5 zusätzlich mit Matching-Diagnose:
    - je fehlender Referenz: Referenzname, Normalname/Suchschlüssel,
      ähnliche Ergebnisnamen und kurzer Grund
    - Liste der tatsächlich verarbeiteten Ergebnisdateien
    Dadurch kann man unterscheiden, ob Dateien wirklich fehlen oder nur nicht
    sauber gematcht werden.
    """
    if rows is None:
        rows = massentest_read_results()
    refs = massentest_read_references()

    result_aliases: set[str] = set()
    result_primary: set[str] = set()
    result_infos: list[dict[str, object]] = []

    for i, raw in enumerate(rows or []):
        try:
            row = massentest_normalize_row(raw, i)
            primary = massentest_row_key(row)
            aliases = massentest_row_match_keys(row)
            label = str(row.get('alter_dateiname') or row.get('pdf_datei') or row.get('dateiname') or primary or '').strip()
            if primary:
                result_primary.add(primary)
            result_aliases.update(aliases)
            result_infos.append({
                'label': label,
                'primary': primary,
                'aliases': aliases,
            })
        except Exception:
            continue

    ref_primary_keys = set(refs.keys())
    processed_ref_keys: set[str] = set()
    missing_keys: list[str] = []
    missing_details: list[dict[str, object]] = []

    def label_for(key: str) -> str:
        ref = refs.get(key, {}) or {}
        return (
            str(ref.get("alter_dateiname") or ref.get("pdf_datei") or ref.get("soll_neuer_dateiname") or key)
            .strip()
        )

    def compact_words(value: str) -> set[str]:
        text = re.sub(r"[^A-Za-zÄÖÜäöüß0-9]+", " ", str(value or "").lower())
        return {w for w in text.split() if len(w) >= 5}

    result_labels = [str(x.get('label') or '') for x in result_infos]

    for key, ref in refs.items():
        ref_aliases = set()
        ref_aliases.update(massentest_match_key_variants(key))
        ref_aliases.update(massentest_row_match_keys(ref))
        if ref_aliases & result_aliases:
            processed_ref_keys.add(key)
        else:
            missing_keys.append(key)
            label = label_for(key)
            words = compact_words(label)
            similar: list[str] = []
            if words:
                for result_label in result_labels:
                    if compact_words(result_label) & words:
                        similar.append(result_label)
                    if len(similar) >= 8:
                        break
            # Fallback: gleiche ersten 8 Zeichen im robusten Kompaktschlüssel.
            if not similar:
                compact_ref = re.sub(r"[^a-z0-9äöüß]+", "", label.lower())
                for result_label in result_labels:
                    compact_res = re.sub(r"[^a-z0-9äöüß]+", "", result_label.lower())
                    if compact_ref[:8] and compact_res.startswith(compact_ref[:8]):
                        similar.append(result_label)
                    if len(similar) >= 8:
                        break
            missing_details.append({
                'referenz': label,
                'normalname': massentest_canonical_pdf_key(label),
                'suchschluessel': sorted(ref_aliases)[:12],
                'aehnliche_ergebnisse': similar,
                'grund': 'Kein Alias/Suchschlüssel der Referenz kommt im letzten Ergebnislauf vor.',
            })

    # Ergebnis ohne Referenz ebenfalls über Aliasvergleich bestimmen.
    ref_aliases_all: set[str] = set()
    for key, ref in refs.items():
        ref_aliases_all.update(massentest_match_key_variants(key))
        ref_aliases_all.update(massentest_row_match_keys(ref))

    extra_count = 0
    extra_results: list[str] = []
    for info in result_infos:
        try:
            if not (set(info.get('aliases') or set()) & ref_aliases_all):
                extra_count += 1
                extra_results.append(str(info.get('label') or info.get('primary') or ''))
        except Exception:
            continue

    missing_labels = [label_for(k) for k in sorted(missing_keys)]
    processed_labels = [str(x.get('label') or x.get('primary') or '') for x in result_infos]
    return {
        "referenzen": len(ref_primary_keys),
        "verarbeitet": len(processed_ref_keys),
        "ergebnis_gesamt": len(result_primary),
        "nicht_verarbeitet": len(missing_keys),
        "ohne_referenz_im_lauf": extra_count,
        "nicht_verarbeitet_liste": missing_labels,
        "matching_details": missing_details,
        "verarbeitete_ergebnisse": processed_labels,
        "ergebnisse_ohne_referenz": extra_results,
    }


def massentest_extract_zip(zip_path: Path) -> tuple[int, list[str]]:
    ensure_massentest_dirs()
    count = 0
    errors: list[str] = []
    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            for info in zf.infolist():
                if info.is_dir() or not info.filename.lower().endswith(".pdf"):
                    continue
                target = massentest_unique_path(MASSTEST_UNPACKED_DIR, info.filename)
                try:
                    with zf.open(info, "r") as src, open(target, "wb") as dst:
                        shutil.copyfileobj(src, dst)
                    count += 1
                except Exception as e:
                    errors.append(f"{info.filename}: {e}")
    except Exception as e:
        errors.append(str(e))
    massentest_log(f"ZIP entpackt: {zip_path.name}, PDFs={count}, Fehler={len(errors)}")
    return count, errors



def massentest_lese_text(service, pdf_path: Path) -> str:
    """Liest Text für Massentest einmalig und nutzt vorhandene Service-Logik."""
    try:
        fn = getattr(service, "lese_text_aus_pdf", None)
        if callable(fn):
            return str(fn(pdf_path) or "")
    except Exception as e:
        massentest_log(f"WARN Textlesen fehlgeschlagen {pdf_path.name}: {e}")
    return ""


def massentest_normalize_supplier_name(value: str) -> str:
    """Normalisiert Lieferantennamen allgemein, ohne Lieferanten-Sonderfaelle."""
    text = html.unescape(str(value or ""))
    text = text.replace("\u00a0", " ").replace("_", " ")
    text = text.replace("–", "-").replace("—", "-")
    text = re.sub(r"[\r\n\t]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip(" .,:;|-")
    text = re.sub(r"^(lieferant|absender|firma|anbieter|rechnung\s+von)\s*[:\-]\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\b(GmbH|AG|KG|OHG|UG)\s*(?:u\.?|und|\+|&)?\s*Co\.?\s*(KG|KGaA)\b", r"\1 & Co. \2", text, flags=re.IGNORECASE)
    text = re.sub(r"\bCo\s+KG\b", "Co. KG", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*&\s*", " & ", text)
    text = re.sub(r"\s+", " ", text).strip(" .,:;|-")
    return text[:120].strip()


def massentest_filename_date(value: str) -> str:
    text = str(value or "").strip()
    if not text:
        return datetime.now().strftime("%Y_%m_%d")
    m = re.search(r"\b(\d{4})[-_.](\d{1,2})[-_.](\d{1,2})\b", text)
    if m:
        return f"{m.group(1)}_{int(m.group(2)):02d}_{int(m.group(3)):02d}"
    m = re.search(r"\b(\d{1,2})\.(\d{1,2})\.(\d{2,4})\b", text)
    if m:
        year = int(m.group(3))
        if year < 100:
            year += 2000
        return f"{year:04d}_{int(m.group(2)):02d}_{int(m.group(1)):02d}"
    safe = re.sub(r"[<>:\"/\\|?*\s]+", "_", text).strip("._-")
    return safe[:24] or datetime.now().strftime("%Y_%m_%d")


def massentest_filename_part(value: str, max_len: int = 64, require_digit: bool = False) -> str:
    text = massentest_normalize_supplier_name(value)
    if require_digit and not re.search(r"\d", text):
        return ""
    text = re.sub(r"[<>:\"/\\|?*\x00-\x1f]+", " ", text)
    text = re.sub(r"\s+", "_", text)
    text = re.sub(r"_+", "_", text).strip(" ._-")
    if not re.search(r"[A-Za-z0-9ÄÖÜäöüß]", text):
        return ""
    return text[:max_len].strip("._-")


def massentest_filename_identifier(value: str, max_len: int = 48) -> str:
    text = massentest_normalize_supplier_name(value)
    if not re.search(r"\d", text):
        return ""
    text = re.sub(r"[<>:\"\\|?*\x00-\x1f]+", " ", text)
    groups = [g for g in re.split(r"[\s._/,-]+", text) if g]
    if len(groups) > 4:
        return ""
    if any(len(g) > 18 and not re.search(r"\d", g) for g in groups):
        return ""
    if len(re.sub(r"\s+", "", text)) > max_len:
        return ""
    return massentest_filename_part(text, max_len, require_digit=True)


def massentest_postprocess_meta(text: str, meta: dict[str, str]) -> dict[str, str]:
    """Massentest-Nachkorrekturen ohne Änderung am produktiven Scan-Service.

    Ab WebUI 3.4.2:
    - Bank-/Kontoauszug-Korrektur greift nur noch bei echtem Bank-/Auszug-Kontext.
    - Reine Bankverbindungen (IBAN/BIC/Sparkasse als Kreditinstitut) dürfen einen
      klaren Dokumentkopf wie VfL Bochum nicht überschreiben.
    - VfL-Dokumente werden im Massentest zusätzlich geschützt, weil hier die alte
      Massentest-Nachkorrektur den Scan-Service-Finalfix wieder überschrieben hat.
    """
    meta = dict(meta or {})
    raw_text = str(text or "")
    t = re.sub(r"\s+", " ", raw_text).lower()
    first_lines = "\n".join([ln.strip() for ln in raw_text.splitlines()[:35] if ln.strip()])
    head = re.sub(r"\s+", " ", first_lines).lower()

    def has(pattern: str, value: str = "") -> bool:
        try:
            return re.search(pattern, value or t, re.IGNORECASE | re.DOTALL) is not None
        except Exception:
            return False

    # Harte Schutzregel: Wenn VfL im Dateikopf / Textkopf erkannt wurde, darf
    # Sparkasse nur Bankverbindung sein, aber niemals Lieferant/Dokumenttyp.
    if has(r"vfl\s+bochum\s+1848|vfl\s+bochum|dauerkartenreservierung|dauerkarte\s+vfl\s+bochum|tickets@vfl-bochum", head) or has(r"vfl\s+bochum\s+1848|dauerkartenreservierung|liga\s*1848"):
        meta["LIEFERANT"] = "VfL Bochum 1848"
        meta["LIEFERANT_STATUS"] = "BEKANNT"
        if has(r"dauerkartenreservierung|reservierungs[-\s]*nr|reservierungsnummer", t):
            meta["DOKUMENTTYP"] = "Reservierung"
        elif has(r"\bdauerkarte\b|\bdauerkarten\b|liga\s*1848", t):
            meta["DOKUMENTTYP"] = "Dauerkarte"
        else:
            meta["DOKUMENTTYP"] = "Information"
        meta["DOKUMENTTYP_STATUS"] = "BEKANNT"
        # Bankdaten / OCR-Zufallstreffer in VfL-Dokumenten nicht als Fachnummer raten.
        if str(meta.get("KUNDENNR", "")).strip() in {"372"}:
            meta["KUNDENNR"] = ""
        meta["MASSTEST_HINWEIS"] = "Massentest-Schutz: VfL-Dokumentkopf gewinnt vor Sparkasse/IBAN."
        return meta

    bank = ""
    if "sparkasse bochum" in t or "sparkasse-bochum" in t:
        bank = "Sparkasse Bochum"
    elif "sparda-bank west" in t or "sparda bank west" in t:
        bank = "Sparda-Bank West eG"
    elif re.search(r"\bkfw\b|kreditanstalt für wiederaufbau|kreditanstalt fuer wiederaufbau", t):
        bank = "KfW"

    # Nicht mehr IBAN/BIC allein als Kontoauszug werten. Das sind häufig nur
    # Bankverbindungen in Rechnungen, Formularen oder Reservierungen.
    starke_kontoauszug_marker = any(x in t for x in [
        "kontoauszug", "kontostand", "buchungstag", "wertstellung", "saldo",
        "darlehenskonto", "darlehensvertrag", "kontoumsätze", "kontoumsaetze"
    ])
    bank_im_kopf = bool(bank) and (
        bank.lower() in head
        or ("sparkasse bochum" in head if bank == "Sparkasse Bochum" else False)
        or ("sparda-bank west" in head or "sparda bank west" in head if bank == "Sparda-Bank West eG" else False)
    )

    if bank and starke_kontoauszug_marker and bank_im_kopf:
        alt_lieferant = meta.get("LIEFERANT", "")
        alt_typ = meta.get("DOKUMENTTYP", "")
        alt_betrag = meta.get("GESAMTBETRAG", "")
        meta["LIEFERANT"] = bank
        meta["DOKUMENTTYP"] = "Kontoauszug"
        meta["LIEFERANT_STATUS"] = "BEKANNT"
        meta["DOKUMENTTYP_STATUS"] = "BEKANNT"
        # Bei Kontoauszügen ist ein einzelner Gesamtbetrag fachlich nicht sinnvoll.
        meta["GESAMTBETRAG"] = ""
        if alt_lieferant and alt_lieferant != bank:
            meta["MASSTEST_HINWEIS"] = (
                f"Bank-/Kontoauszug-Korrektur: Lieferant aus Buchungsposten verworfen "
                f"({alt_lieferant} -> {bank})."
            )
        elif alt_typ and alt_typ != "Kontoauszug":
            meta["MASSTEST_HINWEIS"] = f"Bank-/Kontoauszug-Korrektur: Dokumenttyp {alt_typ} -> Kontoauszug."
        elif alt_betrag:
            meta["MASSTEST_HINWEIS"] = "Kontoauszug-Korrektur: Gesamtbetrag entfernt, da bei Kontoauszügen nicht sinnvoll."

    lieferant_norm = massentest_normalize_supplier_name(meta.get("LIEFERANT", ""))
    if lieferant_norm != str(meta.get("LIEFERANT", "") or "").strip():
        meta["LIEFERANT"] = lieferant_norm

    return meta


def massentest_reprocess_row(row: dict[str, str]) -> tuple[dict[str, str], str]:
    """Wendet die Erkennung auf ein bereits verarbeitetes Massentest-PDF erneut an."""
    p = massentest_pdf_path(row)
    if not p or not p.exists():
        return row, "PDF nicht gefunden – Erkennung konnte nicht erneut angewendet werden."
    service = import_scan_service()
    text = massentest_lese_text(service, p)
    try:
        meta_raw = service.erzeuge_meta_daten(p, text if text else None)
    except TypeError:
        meta_raw = service.erzeuge_meta_daten(p)
    meta = {str(k).upper(): str(v or "").strip() for k, v in (meta_raw or {}).items()}
    meta = massentest_postprocess_meta(text, meta)
    row["lieferant"] = meta.get("LIEFERANT", "")
    row["dokumenttyp"] = meta.get("DOKUMENTTYP", "")
    row["dokumentdatum"] = meta.get("RECHDATUM", "")
    row["rechnr"] = meta.get("RECHNR", "")
    row["aktenzeichen"] = meta.get("AKTENZEICHEN", "")
    row["kundennr"] = meta.get("KUNDENNR", "")
    row["auftragnr"] = meta.get("AUFTRAGNR", "")
    row["bestellnr"] = meta.get("BESTELLNR", "")
    row["lieferscheinnr"] = meta.get("LIEFERSCHEINNR", "")
    row["versicherungsnr"] = meta.get("VERSICHERUNGSNR", "")
    row["gesamtbetrag"] = meta.get("GESAMTBETRAG", "")
    row["ocr_qualitaet"] = meta.get("OCR_QUALITAET", row.get("ocr_qualitaet", ""))
    row["neuer_dateiname"] = massentest_build_new_name(service, meta)
    hinweis = meta.get("MASSTEST_HINWEIS", "")
    if hinweis:
        row["hinweis"] = hinweis
    row["zeitpunkt"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return row, "Erkennung wurde erneut angewendet."

def massentest_build_new_name(service, meta: dict[str, str]) -> str:
    datum = massentest_filename_date(str(meta.get("RECHDATUM") or ""))
    lieferant = massentest_filename_part(str(meta.get("LIEFERANT") or "Unbekannt"), 72) or "Unbekannt"
    nummer = ""
    for key in ["RECHNR", "AKTENZEICHEN", "KUNDENNR", "AUFTRAGNR", "BESTELLNR", "LIEFERSCHEINNR", "VERSICHERUNGSNR"]:
        nummer = massentest_filename_identifier(str(meta.get(key) or ""), 48)
        if nummer:
            break
    name = "_".join(x for x in [datum, lieferant, nummer] if x).strip("._-") or "Unbekannt"
    name = re.sub(r"_+", "_", name)
    return name[:160] + ".pdf"



def massentest_meta_aus_sollwerten(row: dict[str, str]) -> dict[str, str]:
    """Baut ein Meta-Dict aus den Sollwerten, damit der Soll-Dateiname automatisch
    nach der hinterlegten Dateinamen-Deklaration entsteht.

    Der Soll-Dateiname wird bewusst nicht mehr manuell eingegeben. Dadurch bleibt
    die Dateinamenlogik an einer Stelle: dateiname_konfiguration.txt bzw. die
    vorhandene Scan-Service-Funktion zur Zielnamenbildung.
    """
    return {
        "LIEFERANT": str(row.get("soll_lieferant") or row.get("lieferant") or "").strip(),
        "DOKUMENTTYP": str(row.get("soll_dokumenttyp") or row.get("dokumenttyp") or "").strip(),
        "RECHDATUM": str(row.get("soll_dokumentdatum") or row.get("dokumentdatum") or "").strip(),
        "RECHNR": str(row.get("soll_rechnr") or "").strip(),
        "AKTENZEICHEN": str(row.get("soll_aktenzeichen") or "").strip(),
        "KUNDENNR": str(row.get("soll_kundennr") or "").strip(),
        "AUFTRAGNR": str(row.get("soll_auftragnr") or "").strip(),
        "BESTELLNR": str(row.get("soll_bestellnr") or "").strip(),
        "LIEFERSCHEINNR": str(row.get("soll_lieferscheinnr") or "").strip(),
        "VERSICHERUNGSNR": str(row.get("soll_versicherungsnr") or "").strip(),
        "GESAMTBETRAG": str(row.get("soll_gesamtbetrag") or "").strip(),
    }


def massentest_aktualisiere_soll_dateiname(row: dict[str, str]) -> dict[str, str]:
    """Aktualisiert den Soll-Dateinamen automatisch anhand der Sollwerte."""
    try:
        service = import_scan_service()
        meta = massentest_meta_aus_sollwerten(row)
        row["soll_neuer_dateiname"] = massentest_build_new_name(service, meta)
    except Exception as e:
        # Fallback: vorhandenen Ist-Dateinamen nicht kaputt schreiben.
        if not str(row.get("soll_neuer_dateiname", "")).strip():
            row["soll_neuer_dateiname"] = str(row.get("neuer_dateiname", "") or "").strip()
        try:
            massentest_log(f"WARN Soll-Dateiname konnte nicht automatisch gebildet werden: {e}")
        except Exception:
            pass
    return row


def massentest_soll_keys_ohne_dateiname() -> list[str]:
    return [soll_key for _label, _ist_key, soll_key in MASSTEST_COMPARE if soll_key != "soll_neuer_dateiname"]

def massentest_process_pdf(pdf_path: Path, lauf_id: str = "") -> dict[str, str]:
    service = import_scan_service()
    text = massentest_lese_text(service, pdf_path)
    try:
        meta_raw = service.erzeuge_meta_daten(pdf_path, text if text else None)
    except TypeError:
        meta_raw = service.erzeuge_meta_daten(pdf_path)
    meta = {str(k).upper(): str(v or "").strip() for k, v in (meta_raw or {}).items()}
    meta = massentest_postprocess_meta(text, meta)
    new_name = massentest_build_new_name(service, meta)
    ziel = massentest_unique_path(MASSTEST_DONE_DIR, pdf_path.name)
    row = {
        "id": "",
        "lauf_id": lauf_id or massentest_current_lauf_id(),
        "alter_dateiname": pdf_path.name,
        "neuer_dateiname": new_name,
        "lieferant": meta.get("LIEFERANT", ""),
        "dokumenttyp": meta.get("DOKUMENTTYP", ""),
        "dokumentdatum": meta.get("RECHDATUM", ""),
        "rechnr": meta.get("RECHNR", ""),
        "aktenzeichen": meta.get("AKTENZEICHEN", ""),
        "kundennr": meta.get("KUNDENNR", ""),
        "auftragnr": meta.get("AUFTRAGNR", ""),
        "bestellnr": meta.get("BESTELLNR", ""),
        "lieferscheinnr": meta.get("LIEFERSCHEINNR", ""),
        "versicherungsnr": meta.get("VERSICHERUNGSNR", ""),
        "gesamtbetrag": meta.get("GESAMTBETRAG", ""),
        "ocr_qualitaet": meta.get("OCR_QUALITAET", ""),
        "status": "OK",
        "pruefstatus": "ungeprueft",
        "workflow_status": "ERKANNT",
        "notiz": "",
        "aufgabe_id": "",
        "pdf_datei": ziel.name,
        "hinweis": meta.get("MASSTEST_HINWEIS") or "Nur Massentest: keine ecoDMS-Ablage, kein Zähler, kein Etikettendruck.",
        "zeitpunkt": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    shutil.move(str(pdf_path), str(ziel))
    return row



def massentest_all_pdf_locations() -> dict[str, list[Path]]:
    """Indexiert alle bekannten Massentest-PDFs nach robusten Referenzschlüsseln."""
    ensure_massentest_dirs()
    folders = [
        MASSTEST_UNPACKED_DIR,
        MASSTEST_DONE_DIR,
        MASSTEST_ERROR_DIR,
        MASSTEST_DUPLICATE_DIR,
    ]
    index: dict[str, list[Path]] = {}
    for folder in folders:
        try:
            pdfs = sorted(folder.glob("*.pdf"), key=lambda p: p.name.lower())
        except Exception:
            pdfs = []
        for pdf in pdfs:
            keys = set()
            keys.add(massentest_canonical_pdf_key(pdf.name))
            keys.update(massentest_match_key_variants(pdf.name))
            for key in keys:
                if key:
                    index.setdefault(key, []).append(pdf)
    return index


def massentest_ref_label_and_keys(ref_key: str, ref: dict[str, str]) -> tuple[str, set[str]]:
    """Liefert den bevorzugten Referenznamen und alle Matching-Schlüssel."""
    label = str(
        (ref or {}).get("alter_dateiname")
        or (ref or {}).get("pdf_datei")
        or (ref or {}).get("soll_neuer_dateiname")
        or ref_key
        or ""
    ).strip()
    keys: set[str] = set()
    keys.update(massentest_match_key_variants(ref_key))
    keys.update(massentest_row_match_keys(ref))
    keys.update(massentest_match_key_variants(label))
    return label, {k for k in keys if k}


def massentest_prepare_full_testlauf_from_references() -> dict[str, object]:
    """Stellt vor 'Dokumente erkennen' sicher, dass alle Referenzdokumente wartend sind.

    Hintergrund 3.6.7:
    Bisher startete der Testlauf nur aus _massentest/entpackt. Dadurch wurden
    bereits verarbeitete Referenzen nicht neu eingeplant und der Lauf blieb bei
    93/127 stehen. Diese Routine synchronisiert vor dem Lauf die Warteschlange
    aus den dauerhaften Referenzen: Fehlt ein Referenz-PDF in entpackt, wird eine
    vorhandene Kopie aus verarbeitet/fehler/dubletten nach entpackt kopiert.
    Sollwerte bleiben unverändert.
    """
    ensure_massentest_dirs()
    refs = massentest_read_references()
    existing_index = massentest_all_pdf_locations()
    unpacked_index: dict[str, list[Path]] = {}
    for pdf in sorted(MASSTEST_UNPACKED_DIR.glob("*.pdf"), key=lambda p: p.name.lower()):
        keys = set([massentest_canonical_pdf_key(pdf.name)]) | massentest_match_key_variants(pdf.name)
        for key in keys:
            if key:
                unpacked_index.setdefault(key, []).append(pdf)

    copied = 0
    already_waiting = 0
    missing: list[str] = []
    planned_labels: list[str] = []
    copy_errors: list[str] = []

    for ref_key, ref in sorted(refs.items(), key=lambda kv: massentest_ref_label_and_keys(kv[0], kv[1])[0].lower()):
        label, keys = massentest_ref_label_and_keys(ref_key, ref)
        if not label:
            label = ref_key
        planned_labels.append(label)

        if any(k in unpacked_index for k in keys):
            already_waiting += 1
            continue

        candidates: list[Path] = []
        seen_paths: set[str] = set()
        for key in keys:
            for p in existing_index.get(key, []):
                sp = str(p).lower()
                if sp in seen_paths:
                    continue
                seen_paths.add(sp)
                if p.exists() and p.parent != MASSTEST_UNPACKED_DIR:
                    candidates.append(p)

        if not candidates:
            missing.append(label)
            continue

        # Bevorzugt die zuletzt erzeugte/verarbeitete Kopie, weil sie am ehesten vorhanden ist.
        candidates.sort(key=lambda p: (p.stat().st_mtime if p.exists() else 0), reverse=True)
        source = candidates[0]
        target_name = massentest_safe_pdf_name(label)
        target = massentest_unique_path(MASSTEST_UNPACKED_DIR, target_name)
        try:
            shutil.copy2(str(source), str(target))
            copied += 1
            for key in set([massentest_canonical_pdf_key(target.name)]) | massentest_match_key_variants(target.name):
                if key:
                    unpacked_index.setdefault(key, []).append(target)
            massentest_trace(f"REFERENZ ZURUECKGELEGT: {label} | Quelle={source.parent.name}/{source.name} | Ziel={target.name}")
        except Exception as e:
            msg = f"{label}: {e}"
            copy_errors.append(msg)
            massentest_trace(f"REFERENZ-ZURUECKLEGEN FEHLER: {msg}")

    massentest_trace(f"Vollstaendiger Testlauf vorbereitet: Referenzen={len(refs)} | bereits wartend={already_waiting} | zurueckkopiert={copied} | fehlend={len(missing)} | fehler={len(copy_errors)}")
    if missing:
        massentest_trace_list("Referenz-PDFs ohne auffindbare Datei", missing)
    if copy_errors:
        massentest_trace_list("Referenz-PDFs mit Kopierfehler", copy_errors)
    return {
        "referenzen": len(refs),
        "bereits_wartend": already_waiting,
        "zurueckkopiert": copied,
        "fehlend": missing,
        "kopierfehler": copy_errors,
        "geplant": planned_labels,
    }

def massentest_unique_pending_pdfs() -> tuple[list[Path], int]:
    """Liefert eindeutige wartende PDFs und legt Dubletten separat ab."""
    ensure_massentest_dirs()
    seen: set[str] = set()
    unique: list[Path] = []
    duplicates = 0
    pending = sorted(MASSTEST_UNPACKED_DIR.glob("*.pdf"), key=lambda p: p.name.lower())
    massentest_trace_list("Wartende PDFs vor Dublettenfilter", [p.name for p in pending])
    for pdf in pending:
        key = massentest_canonical_pdf_key(pdf.name)
        if key in seen:
            duplicates += 1
            try:
                ziel = massentest_unique_path(MASSTEST_DUPLICATE_DIR, pdf.name)
                shutil.move(str(pdf), str(ziel))
                massentest_log(f"DUBLETTE nicht verarbeitet: {pdf.name} -> {ziel.name}")
                massentest_trace(f"DUBLETTE übersprungen: {pdf.name} | key={key} | Ziel={ziel.name}")
            except Exception as e:
                massentest_log(f"DUBLETTE konnte nicht verschoben werden: {pdf.name}: {e}")
                massentest_trace(f"DUBLETTE-FEHLER: {pdf.name}: {e}")
            continue
        seen.add(key)
        unique.append(pdf)
        massentest_trace(f"EINPLANEN: {pdf.name} | key={key}")
    massentest_trace(f"Dublettenfilter Ergebnis: eindeutig={len(unique)} | dubletten={duplicates}")
    return unique, duplicates


def massentest_process_all() -> tuple[int, int]:
    ensure_massentest_dirs()
    massentest_trace_reset("Massentest Dokumente erkennen")
    try:
        refs = massentest_read_references()
        massentest_trace(f"Referenzen gefunden: {len(refs)}")
        ref_labels = []
        for key, ref in sorted(refs.items()):
            ref_labels.append(str(ref.get('alter_dateiname') or ref.get('pdf_datei') or key))
        massentest_trace_list("Referenzliste", ref_labels)
    except Exception as e:
        massentest_trace(f"Referenzliste konnte nicht gelesen werden: {e}")

    try:
        prep = massentest_prepare_full_testlauf_from_references()
        massentest_trace(f"Einplanung vor Dublettenfilter: {prep.get('referenzen', 0)} Referenzen, {prep.get('zurueckkopiert', 0)} zurueckkopiert, {len(prep.get('fehlend', []) or [])} fehlend")
    except Exception as e:
        massentest_trace(f"Vollstaendiger Testlauf konnte nicht vorbereitet werden: {e}")

    try:
        folder_counts = {
            "entpackt": len(list(MASSTEST_UNPACKED_DIR.glob("*.pdf"))),
            "verarbeitet": len(list(MASSTEST_DONE_DIR.glob("*.pdf"))),
            "fehler": len(list(MASSTEST_ERROR_DIR.glob("*.pdf"))),
            "dubletten": len(list(MASSTEST_DUPLICATE_DIR.glob("*.pdf"))) if MASSTEST_DUPLICATE_DIR.exists() else 0,
            "zip": len(list(MASSTEST_ZIP_DIR.glob("*.zip"))) if MASSTEST_ZIP_DIR.exists() else 0,
        }
        massentest_trace("Ordner vor Start: " + ", ".join(f"{k}={v}" for k, v in folder_counts.items()))
    except Exception as e:
        massentest_trace(f"Ordnerzählung fehlgeschlagen: {e}")

    rows = massentest_read_results()
    massentest_trace(f"Vorhandene Ergebniszeilen vor Lauf: {len(rows)}")
    ok = 0
    fail = 0
    lauf_id = massentest_current_lauf_id()
    pdfs, duplicates = massentest_unique_pending_pdfs()
    total = len(pdfs)
    massentest_trace(f"Start Lauf-ID={lauf_id} | zu verarbeiten={total} | Dubletten={duplicates}")
    if duplicates:
        massentest_log(f"{duplicates} Dublette(n) im Wartend-Ordner aussortiert.")
    massentest_progress_start("Dokumente erkennen", total, "Erkennung startet")
    massentest_log(f"Massentest gestartet: {total} eindeutige PDF(s), Lauf={lauf_id}")
    for nr, pdf in enumerate(pdfs, start=1):
        massentest_progress_write("Dokumente erkennen", nr, total, pdf.name, "running", "Dokument wird erkannt")
        massentest_trace(f"VERARBEITE {nr}/{total}: {pdf.name}")
        try:
            row = massentest_process_pdf(pdf, lauf_id=lauf_id)
            rows = massentest_upsert_row(rows, row)
            ok += 1
            massentest_trace(
                f"OK {nr}/{total}: {row.get('alter_dateiname','')} | pdf_datei={row.get('pdf_datei','')} | "
                f"Lieferant={row.get('lieferant','')} | Typ={row.get('dokumenttyp','')} | Neu={row.get('neuer_dateiname','')}"
            )
            massentest_log(f"OK {nr}/{total}: {pdf.name} -> {row.get('neuer_dateiname','')}")
        except Exception as e:
            fail += 1
            err = str(e)
            ziel = massentest_unique_path(MASSTEST_ERROR_DIR, pdf.name)
            try:
                shutil.move(str(pdf), str(ziel))
            except Exception:
                ziel = pdf
            rows = massentest_upsert_row(rows, {
                "id": "",
                "lauf_id": lauf_id,
                "alter_dateiname": pdf.name,
                "neuer_dateiname": "",
                "lieferant": "",
                "dokumenttyp": "",
                "dokumentdatum": "",
                "rechnr": "",
                "aktenzeichen": "",
                "kundennr": "",
                "auftragnr": "",
                "bestellnr": "",
                "lieferscheinnr": "",
                "versicherungsnr": "",
                "gesamtbetrag": "",
                "ocr_qualitaet": "",
                "status": "FEHLER",
                "pruefstatus": "aufgabe",
                "notiz": "",
                "aufgabe_id": "",
                "pdf_datei": ziel.name,
                "hinweis": err,
                "zeitpunkt": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            })
            massentest_trace(f"FEHLER {nr}/{total}: {pdf.name}: {err}")
            massentest_log(f"FEHLER {nr}/{total}: {pdf.name}: {err}")
    massentest_write_results(rows)
    try:
        final_rows = massentest_read_results()
        diag = massentest_laufdiagnose(final_rows)
        massentest_trace("--- Ergebnis nach Schreiben ---")
        massentest_trace(f"Ergebniszeilen: {len(final_rows)}")
        massentest_trace(f"Referenzen: {diag.get('referenzen')} | verarbeitet: {diag.get('verarbeitet')} | nicht verarbeitet: {diag.get('nicht_verarbeitet')} | Ergebnisse ohne Referenz: {diag.get('ohne_referenz_im_lauf')}")
        massentest_trace_list("Nicht verarbeitete Referenzen nach Lauf", diag.get('nicht_verarbeitet_liste') or [])
        massentest_trace_list("Verarbeitete Ergebnisdateien nach Lauf", diag.get('verarbeitete_ergebnisse') or [])
    except Exception as e:
        massentest_trace(f"Abschlussdiagnose fehlgeschlagen: {e}")
    massentest_progress_finish("Dokumente erkennen", total, f"Erkennung beendet: {ok} OK, {fail} Fehler")
    massentest_log(f"Massentest beendet: {ok} OK, {fail} Fehler")
    massentest_trace(f"ENDE: {ok} OK, {fail} Fehler")
    return ok, fail

def massentest_find_row(rows: list[dict[str, str]], row_id: str) -> tuple[int, dict[str, str]] | tuple[None, None]:
    for i, row in enumerate(rows):
        if str(row.get("id", "")) == str(row_id):
            return i, row
    return None, None


def massentest_pdf_path(row: dict[str, str]) -> Path | None:
    names = []
    for key in ["pdf_datei", "alter_dateiname"]:
        value = str(row.get(key, "") or "")
        if value and value not in names:
            names.append(value)
            safe = massentest_safe_pdf_name(value)
            if safe not in names:
                names.append(safe)
    for name in names:
        for folder in [MASSTEST_DONE_DIR, MASSTEST_UNPACKED_DIR, MASSTEST_ERROR_DIR]:
            p = folder / name
            if p.exists() and p.is_file():
                return p
    # Fallback: rekursiv nach Dateiname suchen, ohne Sonderzeichen zu erzwingen.
    for name in names:
        try:
            for p in MASSTEST_DIR.rglob(name):
                if p.is_file() and p.suffix.lower() == ".pdf":
                    return p
        except Exception:
            pass
    return None


def massentest_pruefstatus_label(status: str) -> str:
    return MASSTEST_STATUS_LABELS.get((status or "ungeprueft").strip().lower(), status or "Ungeprüft")


def massentest_status_badge(status: str) -> str:
    st = (status or "ungeprueft").strip().lower()
    cls = "pill"
    if st == "ok":
        cls = "pill success"
    elif st == "geprueft_ok":
        cls = "pill success"
    elif st == "ausreisser":
        cls = "pill warn"
    elif st in {"aufgabe", "abweichung"}:
        cls = "pill danger"
    elif st == "bearbeitung":
        cls = "pill warn"
    return f"<span class='{cls}'>{esc(massentest_pruefstatus_label(st))}</span>"


def massentest_has_soll(row: dict[str, str]) -> bool:
    return massentest_has_reference(row)


def massentest_expected_supplier_from_filename(name: str) -> str:
    """Ermittelt aus dem alten Dateinamen einen sehr vorsichtigen Plausibilitäts-Hinweis.

    Das ersetzt keine OCR-Erkennung. Es verhindert aber, dass offensichtliche Fälle
    wie "LVM Versicherungen ..." als "Amtsgericht Bochum" fehlerfrei durchlaufen,
    nur weil zuvor falsche Ist-Werte blind als Sollwerte übernommen wurden.
    """
    n = re.sub(r"\s+", " ", str(name or "").lower())
    rules = [
        (r"\blvm\b|lvm versicherung|lvm versicherungen", "LVM"),
        (r"westdeutsche allgemeine|\bwaz\b", "Westdeutsche Allgemeine Zeitung"),
        (r"vfl bochum", "VfL Bochum 1848"),
        (r"vorwerk", "Vorwerk"),
        (r"weicken.*schmidt|schmidt.*weicken", "Weicken & Schmidt GmbH"),
        (r"lexware|haufe", "Lexware"),
        (r"allianz", "Allianz"),
        (r"\baxa\b", "AXA"),
        (r"aida", "AIDA Cruises"),
        (r"amtsgericht bochum|amtsgericht", "Amtsgericht Bochum"),
        (r"sparkasse bochum", "Sparkasse Bochum"),
        (r"sparda", "Sparda-Bank West eG"),
        (r"kfw", "KfW"),
    ]
    for pattern, supplier in rules:
        if re.search(pattern, n, re.IGNORECASE):
            return supplier
    return ""


def massentest_supplier_matches(expected: str, actual: str) -> bool:
    exp = norm_compare(expected)
    act = norm_compare(actual)
    if not exp:
        return True
    if not act:
        return False
    # bewusst großzügig, damit "VfL Bochum 1848" vs. "VfL Bochum" ok ist.
    return exp in act or act in exp or any(part and part in act for part in exp.split() if len(part) >= 4)


def massentest_plausibility_diffs(row: dict[str, str]) -> list[tuple[str, str, str]]:
    """Zusätzliche Plausibilitätsprüfung unabhängig vom Soll/Ist-Vergleich."""
    diffs: list[tuple[str, str, str]] = []
    old_name = str(row.get("alter_dateiname") or row.get("pdf_datei") or "")
    expected_supplier = massentest_expected_supplier_from_filename(old_name)
    actual_supplier = str(row.get("lieferant") or "").strip()
    soll_supplier = str(row.get("soll_lieferant") or "").strip()

    forbidden_supplier_values = {
        "auftrag", "auftrag:", "bestellung", "bestellung:", "kunde", "kunde:",
        "kundennummer", "rechnung", "rechnung:", "rechnungsnummer", "ansprechpartner",
        "datum", "betreff", "anlagen", "anlagen:", "schließanlagen", "schliessanlagen",
    }
    actual_lower = actual_supplier.strip().lower()
    if actual_lower in forbidden_supplier_values:
        diffs.append(("Plausibilität Lieferant", "echter Lieferant", actual_supplier))

    # OCR übernimmt manchmal ganze Sätze als Lieferant. Ein echter Lieferant ist
    # in der Regel kein kompletter Satz mit Verbform. Solche Werte sollen nach
    # versehentlicher Referenzübernahme weiterhin auffällig bleiben.
    company_indicators = ("gmbh", "ag", "kg", "e.v", "ev", "versicherung", "bank", "sparkasse", "amtsgericht", "stadt", "vorwerk", "lexware", "lvm", "axa", "allianz")
    sentence_indicators = (" wird ", " werden ", " wurde ", " wurden ", " ist ", " sind ", " bitte ", " ihnen ", " mir ", " zugesendet", " zugangsdaten")
    if actual_supplier and len(actual_supplier) > 35 and not any(x in actual_lower for x in company_indicators):
        if actual_supplier.endswith(('.', '!', '?')) or any(x in actual_lower for x in sentence_indicators):
            diffs.append(("Plausibilität Lieferant", "echter Firmen-/Absendername", actual_supplier))

    if expected_supplier:
        # Wenn aus dem Dateinamen ein klarer Lieferantenhinweis hervorgeht, müssen Ist und
        # gespeicherter Soll-Lieferant zumindest grob dazu passen. Das verhindert
        # fehlerfreie Prüfungen nach versehentlich falscher Referenzübernahme.
        if actual_supplier and not massentest_supplier_matches(expected_supplier, actual_supplier):
            diffs.append(("Plausibilität Lieferant aus Dateiname", expected_supplier, actual_supplier))
        if soll_supplier and not massentest_supplier_matches(expected_supplier, soll_supplier):
            diffs.append(("Plausibilität Soll-Lieferant aus Dateiname", expected_supplier, soll_supplier))
    return diffs


def massentest_diff_details(row: dict[str, str]) -> tuple[int, list[tuple[str, str, str]]]:
    """Fachlicher Soll/Ist-Vergleich plus Plausibilitätsprüfung.

    Der neue Dateiname wird als berechnetes Ergebnis der Dateinamen-Logik
    mitbewertet. Damit bleiben Metadatenfehler sichtbar, die erst im
    Zielnamen auffallen.
    """
    soll_count = 0
    diffs: list[tuple[str, str, str]] = []
    for label, ist_key, soll_key in MASSTEST_COMPARE:
        ist = str(row.get(ist_key, "") or "").strip()
        soll = str(row.get(soll_key, "") or "").strip()
        if not soll:
            continue
        soll_count += 1
        if norm_compare(ist) != norm_compare(soll):
            diffs.append((label, soll, ist))
    # WebUI 3.5.0:
    # Plausibilitäts-Hinweise (z. B. Lieferant aus Dateiname) dürfen keine
    # fachliche Massentest-Aufgabe erzeugen, wenn Soll/Ist bereits identisch sind.
    # Sie bleiben als Hinweisfunktion erhalten, werden aber nicht mehr in den
    # fachlichen Soll/Ist-Vergleich eingerechnet. Das verhindert Alt-Aufgaben
    # trotz korrekter Referenzwerte.
    return soll_count, diffs

def massentest_compare_marker(row: dict[str, str]) -> str:
    soll_count, diffs = massentest_diff_details(row)
    if soll_count == 0:
        return "<span class='muted'>keine Referenz/Sollwerte</span>"
    if not diffs:
        return "<span class='ok'>Soll/Ist ok</span>"
    return f"<span class='warntext'>{len(diffs)} Abweichung(en)</span>"


def massentest_quality_ampel(diff_count: int) -> tuple[str, str, str]:
    """Einfache Sprint-2A-Ampel fuer Dokumentabweichungen."""
    if diff_count <= 0:
        return "gruen", "🟢", "keine Abweichungen"
    if diff_count <= 2:
        return "gelb", "🟡", "wenige Abweichungen"
    return "rot", "🔴", "viele Abweichungen"


def massentest_quality_snapshot(rows: list[dict[str, str]]) -> dict:
    """Stabiler Qualitaets-Snapshot fuer Buildvergleiche."""
    rows = list(rows or [])
    green = yellow = red = 0
    generated_at = datetime.now()
    snapshot: dict = {
        "schema": "massentest_quality_snapshot_v1",
        "generated_at": generated_at.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
        "app_version": APP_VERSION,
        "document_count": len(rows),
        "ampel": {"gruen": 0, "gelb": 0, "rot": 0},
        "documents": {},
        "fields": {},
    }
    for label, _ist_key, _soll_key in MASSTEST_COMPARE:
        snapshot["fields"][label] = {"checked": 0, "ok": 0, "abweichung": 0}
    for row in rows or []:
        row_id = str(row.get("id") or row.get("row_id") or row.get("alter_dateiname") or "").strip()
        if not row_id:
            continue
        diff_labels: set[str] = set()
        soll_count, diffs = massentest_diff_details(row)
        ampel_key, _ampel_symbol, _ampel_text = massentest_quality_ampel(len(diffs))
        if ampel_key == "gruen":
            green += 1
        elif ampel_key == "gelb":
            yellow += 1
        else:
            red += 1
        for label, _soll, _ist in diffs:
            diff_labels.add(label)
        field_state = {}
        for label, _ist_key, soll_key in MASSTEST_COMPARE:
            has_soll = bool(str(row.get(soll_key, "") or "").strip())
            if not has_soll:
                continue
            state = "abweichung" if label in diff_labels else "ok"
            field_state[label] = state
            snapshot["fields"].setdefault(label, {"checked": 0, "ok": 0, "abweichung": 0})
            snapshot["fields"][label]["checked"] += 1
            snapshot["fields"][label][state] += 1
        snapshot["documents"][row_id] = {
            "datei": str(row.get("alter_dateiname") or row.get("pdf_datei") or ""),
            "status": massentest_row_status(row),
            "sollfelder": soll_count,
            "abweichungen": len(diffs),
            "fields": field_state,
        }
    snapshot["ampel"] = {"gruen": green, "gelb": yellow, "rot": red}
    return snapshot


def massentest_quality_analysis(rows: list[dict[str, str]] | None = None) -> dict:
    """Automatische Sprint-2A-Qualitaetsanalyse auf Basis vorhandener Soll/Ist-Daten."""
    if rows is None:
        rows = massentest_read_results()
    rows = list(rows or [])

    def inc(bucket: dict[str, int], key: str, amount: int = 1) -> None:
        key = str(key or "").strip() or "nicht angegeben"
        bucket[key] = int(bucket.get(key, 0)) + amount

    field_docs: dict[str, set[str]] = {}
    field_checked: dict[str, int] = {}
    supplier_errors: dict[str, int] = {}
    supplier_docs: dict[str, set[str]] = {}
    doctype_errors: dict[str, int] = {}
    doctype_docs: dict[str, set[str]] = {}
    documents: list[dict] = []
    green = yellow = red = 0

    for row in rows:
        doc_id = str(row.get("id") or row.get("row_id") or row.get("alter_dateiname") or "").strip()
        name = str(row.get("alter_dateiname") or row.get("pdf_datei") or row.get("neuer_dateiname") or doc_id).strip()
        supplier = str(row.get("soll_lieferant") or row.get("lieferant") or "").strip() or "nicht angegeben"
        doctype = str(row.get("soll_dokumenttyp") or row.get("dokumenttyp") or "").strip() or "nicht angegeben"
        soll_count, diffs = massentest_diff_details(row)
        diff_count = len(diffs)
        ampel_key, ampel_symbol, ampel_text = massentest_quality_ampel(diff_count)
        if ampel_key == "gruen":
            green += 1
        elif ampel_key == "gelb":
            yellow += 1
        else:
            red += 1
        diff_labels = {label for label, _soll, _ist in diffs}
        for label, _ist_key, soll_key in MASSTEST_COMPARE:
            if str(row.get(soll_key, "") or "").strip():
                field_checked[label] = field_checked.get(label, 0) + 1
        for label, _soll, _ist in diffs:
            field_docs.setdefault(label, set()).add(doc_id or name)
        if diff_count:
            inc(supplier_errors, supplier, diff_count)
            supplier_docs.setdefault(supplier, set()).add(doc_id or name)
            inc(doctype_errors, doctype, diff_count)
            doctype_docs.setdefault(doctype, set()).add(doc_id or name)
        documents.append({
            "id": doc_id,
            "datei": name,
            "lieferant": supplier,
            "dokumenttyp": doctype,
            "sollfelder": soll_count,
            "abweichungen": diff_count,
            "ampel": ampel_key,
            "ampel_symbol": ampel_symbol,
            "ampel_text": ampel_text,
            "felder": sorted(diff_labels),
        })

    field_rows = []
    for label, _ist_key, _soll_key in MASSTEST_COMPARE:
        docs = field_docs.get(label, set())
        checked = int(field_checked.get(label, 0))
        deviations = len(docs)
        ok_count = max(0, checked - deviations)
        hit_rate = int(round(ok_count * 100 / checked)) if checked else 0
        field_rows.append({
            "feld": label,
            "geprueft": checked,
            "abweichende_dokumente": deviations,
            "ok": ok_count,
            "trefferquote": hit_rate,
            "trend": "Vergleich vorbereitet",
        })
    field_rows.sort(key=lambda x: (-int(x["abweichende_dokumente"]), str(x["feld"])))

    top_suppliers = [
        {"lieferant": k, "abweichungen": v, "dokumente": len(supplier_docs.get(k, set()))}
        for k, v in supplier_errors.items()
    ]
    top_suppliers.sort(key=lambda x: (-int(x["abweichungen"]), -int(x["dokumente"]), str(x["lieferant"])))
    top_doctypes = [
        {"dokumenttyp": k, "abweichungen": v, "dokumente": len(doctype_docs.get(k, set()))}
        for k, v in doctype_errors.items()
    ]
    top_doctypes.sort(key=lambda x: (-int(x["abweichungen"]), -int(x["dokumente"]), str(x["dokumenttyp"])))
    documents.sort(key=lambda x: (-int(x["abweichungen"]), str(x["datei"]).lower()))
    priority = [
        {"bereich": row["feld"], "potenzial_dokumente": row["abweichende_dokumente"]}
        for row in field_rows if int(row["abweichende_dokumente"]) > 0
    ]
    priority.sort(key=lambda x: (-int(x["potenzial_dokumente"]), str(x["bereich"])))

    return {
        "total": len(rows),
        "ampel": {"gruen": green, "gelb": yellow, "rot": red},
        "fields": field_rows,
        "suppliers": top_suppliers,
        "doctypes": top_doctypes,
        "documents": documents,
        "priority": priority,
        "buildvergleich": {
            "ready": True,
            "baseline_available": False,
            "snapshot_schema": "massentest_quality_snapshot_v1",
            "current_snapshot": massentest_quality_snapshot(rows),
        },
    }


def massentest_quality_analysis_table(rows: list[dict], columns: list[tuple[str, str]], empty: str = "Keine Daten.") -> str:
    if not rows:
        return f"<p class='muted small'>{esc(empty)}</p>"
    head = "".join(f"<th>{esc(label)}</th>" for label, _key in columns)
    body = ""
    for row in rows:
        body += "<tr>" + "".join(f"<td>{esc(row.get(key, ''))}</td>" for _label, key in columns) + "</tr>"
    return f"<table><tr>{head}</tr>{body}</table>"


def massentest_quality_snapshot_slug(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9]+", "_", str(value or "").strip()).strip("_").lower()
    return slug[:60] or "build"


def massentest_quality_snapshot_path(filename: str) -> Path:
    safe_name = Path(str(filename or "")).name
    if not safe_name or not safe_name.endswith(".json"):
        raise HTTPException(status_code=400, detail="Ungueltiger Snapshot")
    path = MASSTEST_SNAPSHOT_DIR / safe_name
    try:
        resolved = path.resolve()
        base = MASSTEST_SNAPSHOT_DIR.resolve()
        if base not in resolved.parents and resolved != base:
            raise HTTPException(status_code=400, detail="Ungueltiger Snapshot")
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=400, detail="Ungueltiger Snapshot")
    return path


def massentest_quality_snapshot_save(rows: list[dict[str, str]] | None = None) -> Path:
    ensure_dirs()
    rows = massentest_read_results() if rows is None else rows
    snapshot = massentest_quality_snapshot(list(rows or []))
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    build = massentest_quality_snapshot_slug(snapshot.get("app_version") or APP_VERSION)
    path = MASSTEST_SNAPSHOT_DIR / f"quality_snapshot_{stamp}_{build}.json"
    counter = 1
    while path.exists():
        path = MASSTEST_SNAPSHOT_DIR / f"quality_snapshot_{stamp}_{counter:02d}_{build}.json"
        counter += 1
    path.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def massentest_quality_snapshot_load(filename: str) -> dict:
    path = massentest_quality_snapshot_path(filename)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Snapshot nicht gefunden")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Snapshot nicht lesbar: {e}")
    if not isinstance(data, dict) or data.get("schema") != "massentest_quality_snapshot_v1":
        raise HTTPException(status_code=400, detail="Snapshot-Schema nicht passend")
    data["_filename"] = path.name
    return data


def massentest_quality_snapshot_list() -> list[dict]:
    ensure_dirs()
    out: list[dict] = []
    for path in sorted((p for p in MASSTEST_SNAPSHOT_DIR.glob("quality_snapshot_*.json") if p.is_file()), key=lambda p: p.stat().st_mtime, reverse=True):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            docs = data.get("documents") or {}
            out.append({
                "datei": path.name,
                "erstellt": data.get("generated_at", ""),
                "build": data.get("app_version", ""),
                "dokumente": data.get("document_count", len(docs)),
            })
        except Exception:
            out.append({"datei": path.name, "erstellt": "nicht lesbar", "build": "", "dokumente": ""})
    return out


def massentest_quality_snapshot_compare(base: dict, target: dict) -> dict:
    base_docs = base.get("documents") or {}
    target_docs = target.get("documents") or {}
    categories = {
        "verbessert": 0,
        "verschlechtert": 0,
        "unveraendert": 0,
        "neu_auffaellig": 0,
        "nicht_mehr_auffaellig": 0,
    }
    field_summary: dict[str, dict[str, int]] = {}
    doc_rows: list[dict] = []

    def field_bucket(label: str) -> dict[str, int]:
        return field_summary.setdefault(label, {"verbessert": 0, "verschlechtert": 0, "unveraendert": 0})

    for row_id in sorted(set(base_docs.keys()) | set(target_docs.keys())):
        old = base_docs.get(row_id) or {}
        new = target_docs.get(row_id) or {}
        old_diff = int(old.get("abweichungen") or 0)
        new_diff = int(new.get("abweichungen") or 0)
        old_bad = bool(old_diff > 0)
        new_bad = bool(new_diff > 0)
        if old_bad and not new_bad:
            category = "nicht_mehr_auffaellig"
        elif not old_bad and new_bad:
            category = "neu_auffaellig"
        elif new_diff < old_diff:
            category = "verbessert"
        elif new_diff > old_diff:
            category = "verschlechtert"
        else:
            category = "unveraendert"
        categories[category] += 1

        old_fields = old.get("fields") or {}
        new_fields = new.get("fields") or {}
        changed_fields: list[str] = []
        for label in sorted(set(old_fields.keys()) | set(new_fields.keys())):
            old_state = old_fields.get(label)
            new_state = new_fields.get(label)
            if old_state == "abweichung" and new_state == "ok":
                field_bucket(label)["verbessert"] += 1
                changed_fields.append(f"{label}: besser")
            elif old_state == "ok" and new_state == "abweichung":
                field_bucket(label)["verschlechtert"] += 1
                changed_fields.append(f"{label}: schlechter")
            elif old_state == new_state and old_state:
                field_bucket(label)["unveraendert"] += 1

        doc_rows.append({
            "row_id": row_id,
            "datei": new.get("datei") or old.get("datei") or row_id,
            "vorher": old_diff,
            "nachher": new_diff,
            "bewertung": category.replace("_", " "),
            "felder": ", ".join(changed_fields) or "-",
        })

    doc_rows.sort(key=lambda x: (
        0 if x["bewertung"] in {"verschlechtert", "neu auffaellig"} else 1,
        -int(x["nachher"]),
        str(x["datei"]).lower(),
    ))
    field_rows = [
        {"feld": label, **values}
        for label, values in field_summary.items()
        if values.get("verbessert") or values.get("verschlechtert")
    ]
    field_rows.sort(key=lambda x: (-int(x.get("verschlechtert", 0)), -int(x.get("verbessert", 0)), str(x.get("feld", ""))))
    return {
        "base": base.get("_filename", ""),
        "target": target.get("_filename", ""),
        "summary": categories,
        "documents": doc_rows,
        "fields": field_rows,
    }


def massentest_filter_rows(rows: list[dict[str, str]], pruefstatus: str = "alle", q: str = "") -> list[dict[str, str]]:
    out = rows[:]
    if pruefstatus and pruefstatus != "alle":
        out = [r for r in out if (r.get("pruefstatus") or "ungeprueft") == pruefstatus]
    q = (q or "").strip().lower()
    if q:
        def hit(r: dict[str, str]) -> bool:
            text = " ".join(str(r.get(k, "")) for k in [
                "alter_dateiname", "neuer_dateiname", "lieferant", "dokumenttyp", "dokumentdatum",
                "rechnr", "aktenzeichen", "kundennr", "auftragnr", "bestellnr", "lieferscheinnr", "gesamtbetrag", "notiz", "hinweis"
            ]).lower()
            return q in text
        out = [r for r in out if hit(r)]
    return out



def massentest_overview_status(row: dict[str, str], aufgaben_cache: list[dict] | None = None) -> tuple[str, str, str, str]:
    """Statusdarstellung aus der zentralen 4.0-Statusableitung."""
    row_status = massentest_row_status(row)
    ws = massentest_derive_workflow(row)
    try:
        _soll_count, diffs = massentest_diff_details(row)
    except Exception:
        diffs = []
    if ws != "AUSREISSER" and diffs:
        row_status = "abweichung"
    if ws == "AUSREISSER":
        info = row.get("notiz") or row.get("letzter_test") or "Dokument ist Sonderfall"
        return "⭐", f"Sonderfall: {esc(info)}<br>Technischer Status: Bestanden<br>Fachlicher Status: Sonderfall", "row-expected", "special"
    if row_status == "abweichung":
        info = row.get("hinweis") or row.get("notiz") or row.get("letzter_test") or row.get("abweichungen") or "Massentest-Abweichung / Aufgabe"
        return "✗", f"Technischer Status: Abweichung: {esc(info)}<br>Fachlicher Status: – (noch nicht möglich)", "row-missing", "error"
    task_active = bool(str(row.get("aufgabe_id", "") or "").strip())
    task_marker = ""
    try:
        aufgaben = aufgaben_cache if aufgaben_cache is not None else projekt_lade_aufgaben()
        existing_idx = massentest_existing_task_index(aufgaben, row)
        if existing_idx is not None:
            task = aufgaben[existing_idx]
            task_active = _pc_status_aktiv_2727(task)
            task_marker = " ".join(str(task.get(k, "") or "") for k in ["status", "titel", "quelle", "notiz"])
        else:
            task_active = False
    except Exception:
        task_active = bool(str(row.get("aufgabe_id", "") or "").strip())
    fachliche_marker = " ".join([
        str(row.get("fachlich_validiert_hinweis", "") or ""),
        str(row.get("fachlich_status", "") or ""),
        str(row.get("fachlicher_status", "") or ""),
        str(row.get("fachstatus", "") or ""),
        str(row.get("review_status", "") or ""),
        str(row.get("pruefstatus", "") or ""),
        str(row.get("workflow_status", "") or ""),
        str(row.get("notiz", "") or ""),
        task_marker,
    ]).lower().replace("_", " ")
    is_fachliche_nacharbeit = (
        ("fachliche" in fachliche_marker and "nicht bestanden" in fachliche_marker)
        or "fachlich nachzuarbeiten" in fachliche_marker
        or "fachlich nachzubearbeiten" in fachliche_marker
        or "nachzuarbeiten" in fachliche_marker
        or "nachzubearbeiten" in fachliche_marker
    )
    if task_active and is_fachliche_nacharbeit:
        info = row.get("notiz") or row.get("hinweis") or "Fachliche Prüfung nicht bestanden"
        return "!", f"Technischer Status: Bestanden<br>Fachlicher Status: Nachzubearbeiten: {esc(info)}", "row-untested", "fachliche_nacharbeit"
    if row_status == "bestanden":
        if massentest_is_fachlich_validiert(row):
            return "✓", "Technischer Status: Bestanden<br>Fachlicher Status: Fachlich validiert", "row-expected", "success_validated"
        return "✓", "Technischer Status: Bestanden<br>Fachlicher Status: Noch fachlich zu prüfen", "row-expected", "success_pending"
    if not massentest_has_reference(row):
        return "○", "Technischer Status: Offen: Referenz/Sollwerte fehlen<br>Fachlicher Status: – (noch nicht möglich)", "row-missing", "open"
    return "○", "Technischer Status: Offen: " + massentest_compare_marker(row).replace("<span class='", "").replace("</span>", "") + "<br>Fachlicher Status: – (noch nicht möglich)", "row-untested", "open"


def massentest_row_html(row: dict[str, str], only_area: str | None = None, aufgaben_cache: list[dict] | None = None) -> str:
    rid = quote(str(row.get("id", "")))
    symbol, status_info, row_class, area = massentest_overview_status(row, aufgaben_cache)
    row_status = massentest_row_status(row)
    validation_info = massentest_validation_badge(row) if row_status == "bestanden" and area not in {"special", "fachliche_nacharbeit"} else ""
    if only_area is not None and area != only_area:
        return ""
    p = massentest_pdf_path(row)
    try:
        size_kb = max(1, int(p.stat().st_size / 1024)) if p and p.exists() else 0
        mtime = datetime.fromtimestamp(p.stat().st_mtime).strftime("%d.%m.%Y %H:%M:%S") if p and p.exists() else str(row.get("zeitpunkt", ""))
    except Exception:
        size_kb = 0
        mtime = str(row.get("zeitpunkt", ""))
    soll_status = "✓ Sollwerte" if massentest_has_soll(row) else "? keine Sollwerte"
    task_badge = ""
    if row.get("aufgabe_id"):
        aid = esc(row.get("aufgabe_id"))
        task_badge = f" <a class='task-badge' href='/projekt?suche={aid}' title='Aufgabe im Projektcenter suchen'>{aid}</a>"
    if row.get("letzter_test"):
        status_info = f"{status_info}<br><span class='massentest-test-hint'>{esc(row.get('letzter_test'))}</span>"
    task_button_text = "Aufgabe aktualisieren" if row.get("aufgabe_id") else "Aufgabe anlegen"
    title = esc(row.get('alter_dateiname') or row.get('pdf_datei') or 'Massentest-PDF')
    new_name = esc(row.get('neuer_dateiname',''))
    primary_href = f"/test/massentest/fachlich/{rid}" if row_status == "bestanden" else f"/test/massentest/result/{rid}"
    primary_title = "Fachlich prüfen" if row_status == "bestanden" else "Testergebnis ansehen"
    actions = f"""
      <div class='massentest-actions' style='display:flex;gap:8px;flex-wrap:wrap;margin-top:12px'>
        <form method='post' action='/test/massentest/run-one/{rid}' data-working='Massentest-Einzeltest läuft...'><button class='btn2' type='submit'>Dokument prüfen</button></form>
        {"<a class='btn2' href='/test/massentest/fachlich/" + rid + "' title='Fachlich prüfen'>Fachlich prüfen</a>" if row_status == "bestanden" else "<a class='btn2' href='/test/massentest/result/" + rid + "' title='Testergebnis ansehen'>Testergebnis ansehen</a>"}
        <a class='btn2' href='/test/massentest/detail/{rid}?source=fachlich'>Sollwerte</a>
        <form method='post' action='/test/massentest/quick/{rid}'><button class='btn2 success' name='action' value='ist_uebernehmen' type='submit'>Ist-Werte übernehmen</button></form>
        <form method='post' action='/test/massentest/quick/{rid}' data-confirm-title='Bestanden markieren?' data-confirm-message='Dieses Massentest-Dokument wird mit den aktuell gespeicherten Sollwerten als Bestanden markiert.' data-confirm-kind='eco-modal-success' data-confirm-ok='Ja, Bestanden'><button class='btn2 success' name='action' value='ok' type='submit'>✓ Bestanden</button></form>
        <form method='post' action='/test/massentest/quick/{rid}' data-working='Aufgabe wird angelegt/aktualisiert...'><button class='btn2 warn' name='action' value='aufgabe' type='submit'>{task_button_text}</button></form>
        <form method='post' action='/test/massentest/delete/{rid}' data-confirm-title='Massentest-Dokument löschen?' data-confirm-message='Eintrag aus dem Massentest und PDF aus dem Massentestbereich wirklich löschen?' data-confirm-kind='eco-modal-danger' data-confirm-ok='Ja, löschen'><button class='btn2 danger' type='submit'>Löschen</button></form>
      </div>"""
    return f"""
    <div id='mtrow-{esc(row.get('id',''))}' class='massentest-card {row_class}' style='border:1px solid #d9e2f1;border-radius:14px;padding:14px;margin:10px 0;background:#fff;overflow:hidden'>
      <div style='display:grid;grid-template-columns:minmax(260px,1fr) auto;gap:12px;align-items:start'>
        <div style='min-width:0'>
          <div style='font-weight:900;word-break:break-word'><span class='status-symbol'>{symbol}</span> <a class='massentest-filelink' href='{primary_href}' title='{primary_title}'>{title}</a>{task_badge}</div>
          <div class='muted small' style='word-break:break-word;margin-top:4px'><a class='massentest-filelink muted' href='{primary_href}' title='{primary_title}'>Neu: {new_name}</a></div>
        </div>
        <div class='muted small' style='text-align:right;white-space:normal'>
          {size_kb} KB<br>{esc(mtime)}<br>{esc(soll_status)}
        </div>
      </div>
      <div class='massentest-statuscell' style='word-break:break-word;margin-top:10px'>{status_info}{('<br>' + validation_info) if validation_info else ''}</div>
      {actions}
    </div>"""

def massentest_section_html(title: str, area: str, rows: list[dict[str, str]], open_section: bool = False, aufgaben_cache: list[dict] | None = None) -> str:
    relevant = [r for r in rows if massentest_overview_status(r, aufgaben_cache)[3] == area]
    count = len(relevant)
    body_rows = "".join(massentest_row_html(r, only_area=area, aufgaben_cache=aufgaben_cache) for r in relevant)
    if not body_rows:
        body_rows = "<div class='muted' style='padding:12px'>Keine Dokumente in diesem Bereich.</div>"
    open_attr = " open" if open_section else ""
    priority_class = " open-priority" if area == "error" else ""
    if area == "special":
        section_id = "gruppe-sonderfaelle"
    elif area == "fachliche_nacharbeit":
        section_id = "gruppe-fachliche-nacharbeit"
    elif area == "success_pending":
        section_id = "gruppe-technisch-bestanden-noch-fachlich-zu-pruefen"
    elif area == "success_validated":
        section_id = "gruppe-technisch-bestanden-fachlich-validiert"
    elif area == "error":
        section_id = "gruppe-abweichung"
    elif area == "open":
        section_id = "gruppe-offen"
    else:
        section_id = f"gruppe-{area}"
    return f"""
    <details id='{section_id}' class='test-doc-section{priority_class}'{open_attr}>
      <summary>{title} ({count})</summary>
      <div class='massentest-card-list' style='overflow:visible'>{body_rows}</div>
    </details>
    """
def massentest_grouped_overview_html(rows: list[dict[str, str]], q: str = "") -> str:
    if q:
        rows = massentest_filter_rows(rows, "alle", q)
    if not rows:
        return "<div class='learn-empty'>Keine Massentest-Dokumente vorhanden.</div>"
    try:
        aufgaben_cache = projekt_lade_aufgaben()
    except Exception:
        aufgaben_cache = None
    # Neueste oben, analog zu den Testcenter-Listen.
    rows = list(reversed(rows[-500:]))
    return "".join([
        massentest_section_html("✗ Abweichung", "error", rows, open_section=True, aufgaben_cache=aufgaben_cache),
        massentest_section_html("! Nachzubearbeiten", "fachliche_nacharbeit", rows, open_section=True, aufgaben_cache=aufgaben_cache),
        massentest_section_html("○ Offen", "open", rows, open_section=True, aufgaben_cache=aufgaben_cache),
        massentest_section_html("⭐ Sonderfälle", "special", rows, open_section=True, aufgaben_cache=aufgaben_cache),
        massentest_section_html("✓ Technisch bestanden – noch fachlich zu prüfen", "success_pending", rows, open_section=True, aufgaben_cache=aufgaben_cache),
        massentest_section_html("✓ Technisch bestanden – fachlich validiert", "success_validated", rows, open_section=True, aufgaben_cache=aufgaben_cache),
    ])


@app.post("/test/massentest/analysis/snapshot")
def massentest_quality_snapshot_save_route() -> RedirectResponse:
    path = massentest_quality_snapshot_save()
    return RedirectResponse(f"/test/massentest/analysis?snapshot_saved={quote(path.name)}", status_code=303)


@app.get("/test/massentest/analysis", response_class=HTMLResponse)
def massentest_quality_analysis_page(snapshot_a: str = "", snapshot_b: str = "", snapshot_saved: str = "") -> HTMLResponse:
    rows = massentest_read_results()
    analysis = massentest_quality_analysis(rows)
    ampel = analysis.get("ampel", {})
    snapshots = massentest_quality_snapshot_list()
    field_table = massentest_quality_analysis_table(
        analysis.get("fields", [])[:20],
        [
            ("Feld", "feld"),
            ("Geprüft", "geprueft"),
            ("OK", "ok"),
            ("Abweichende Dokumente", "abweichende_dokumente"),
            ("Trefferquote %", "trefferquote"),
            ("Buildvergleich", "trend"),
        ],
    )
    supplier_table = massentest_quality_analysis_table(
        analysis.get("suppliers", [])[:15],
        [("Lieferant", "lieferant"), ("Abweichungen", "abweichungen"), ("Dokumente", "dokumente")],
        "Keine Lieferantenabweichungen.",
    )
    doctype_table = massentest_quality_analysis_table(
        analysis.get("doctypes", [])[:15],
        [("Dokumenttyp", "dokumenttyp"), ("Abweichungen", "abweichungen"), ("Dokumente", "dokumente")],
        "Keine Dokumenttypabweichungen.",
    )
    docs_for_table = []
    for row in analysis.get("documents", [])[:20]:
        docs_for_table.append({
            "ampel": f"{row.get('ampel_symbol','')} {row.get('ampel_text','')}",
            "datei": row.get("datei", ""),
            "abweichungen": row.get("abweichungen", 0),
            "felder": ", ".join(row.get("felder") or []),
            "lieferant": row.get("lieferant", ""),
            "dokumenttyp": row.get("dokumenttyp", ""),
        })
    docs_table = massentest_quality_analysis_table(
        docs_for_table,
        [
            ("Ampel", "ampel"),
            ("Dokument", "datei"),
            ("Abweichungen", "abweichungen"),
            ("Felder", "felder"),
            ("Lieferant", "lieferant"),
            ("Dokumenttyp", "dokumenttyp"),
        ],
        "Keine Dokumentabweichungen.",
    )
    priority_rows = []
    for item in analysis.get("priority", [])[:12]:
        priority_rows.append({
            "bereich": f"{item.get('bereich', '')} verbessern",
            "potenzial": f"{item.get('potenzial_dokumente', 0)} Dokument(e)",
        })
    priority_table = massentest_quality_analysis_table(
        priority_rows,
        [("Qualitätshebel", "bereich"), ("Potenzial", "potenzial")],
        "Aktuell kein priorisierbarer Qualitätshebel aus Abweichungen ableitbar.",
    )
    snapshot = analysis.get("buildvergleich", {}).get("current_snapshot", {})
    snapshot_summary = {
        "schema": snapshot.get("schema", ""),
        "documents": len((snapshot.get("documents") or {})),
        "fields": len((snapshot.get("fields") or {})),
        "baseline": f"{len(snapshots)} gespeicherte Snapshot(s)",
    }
    saved_msg = ""
    if snapshot_saved:
        saved_msg = render_message_box(f"Gespeichert: {snapshot_saved}", "Snapshot gespeichert", "success")
    snapshot_table = massentest_quality_analysis_table(
        snapshots,
        [("Snapshot", "datei"), ("Erstellt", "erstellt"), ("Build", "build"), ("Dokumente", "dokumente")],
        "Noch keine gespeicherten Snapshots.",
    )
    options = "".join(
        f"<option value='{quote(str(item.get('datei','')))}' {'selected' if item.get('datei') == snapshot_a else ''}>{esc(str(item.get('erstellt') or ''))} · {esc(str(item.get('build') or ''))} · {esc(str(item.get('datei') or ''))}</option>"
        for item in snapshots
    )
    options_b = "".join(
        f"<option value='{quote(str(item.get('datei','')))}' {'selected' if item.get('datei') == snapshot_b else ''}>{esc(str(item.get('erstellt') or ''))} · {esc(str(item.get('build') or ''))} · {esc(str(item.get('datei') or ''))}</option>"
        for item in snapshots
    )
    compare_form = ""
    compare_html = "<p class='muted small'>Für einen Buildvergleich werden mindestens zwei gespeicherte Snapshots benötigt.</p>"
    if len(snapshots) >= 1:
        compare_form = f"""
        <form method='get' action='/test/massentest/analysis' class='toolbar' style='align-items:end;gap:10px;flex-wrap:wrap'>
          <label class='small'><b>Basis</b><br><select name='snapshot_a' style='min-width:320px;max-width:100%'>{options}</select></label>
          <label class='small'><b>Vergleich</b><br><select name='snapshot_b' style='min-width:320px;max-width:100%'>{options_b}</select></label>
          <button class='btn' type='submit'>Snapshots vergleichen</button>
        </form>
        """
    if snapshot_a and snapshot_b and Path(snapshot_a).name == Path(snapshot_b).name:
        compare_html = render_message_box("Bitte zwei unterschiedliche Snapshots auswählen.", "Buildvergleich nicht möglich", "warning")
    elif snapshot_a and snapshot_b:
        try:
            base_snapshot = massentest_quality_snapshot_load(snapshot_a)
            target_snapshot = massentest_quality_snapshot_load(snapshot_b)
            cmp_result = massentest_quality_snapshot_compare(base_snapshot, target_snapshot)
            summary = cmp_result.get("summary", {})
            docs_table_compare = massentest_quality_analysis_table(
                cmp_result.get("documents", [])[:80],
                [
                    ("Bewertung", "bewertung"),
                    ("Dokument", "datei"),
                    ("Vorher", "vorher"),
                    ("Nachher", "nachher"),
                    ("Feldänderungen", "felder"),
                ],
                "Keine Dokumentänderungen.",
            )
            fields_compare = massentest_quality_analysis_table(
                cmp_result.get("fields", []),
                [
                    ("Feld", "feld"),
                    ("Verbessert", "verbessert"),
                    ("Verschlechtert", "verschlechtert"),
                    ("Unverändert", "unveraendert"),
                ],
                "Keine Feldänderungen zwischen den Snapshots.",
            )
            compare_html = f"""
            <div class='legend'>
              <span><b>Verbessert</b> {summary.get('verbessert', 0)}</span>
              <span><b>Verschlechtert</b> {summary.get('verschlechtert', 0)}</span>
              <span><b>Unverändert</b> {summary.get('unveraendert', 0)}</span>
              <span><b>Neu auffällig</b> {summary.get('neu_auffaellig', 0)}</span>
              <span><b>Nicht mehr auffällig</b> {summary.get('nicht_mehr_auffaellig', 0)}</span>
            </div>
            <h3>Betroffene Felder</h3>
            {fields_compare}
            <h3>Betroffene Dokumente</h3>
            {docs_table_compare}
            """
        except HTTPException as e:
            compare_html = render_message_box(str(e.detail), "Buildvergleich nicht möglich", "warning")
    body = f"""
    <div class='top-actions'><div><b>Qualitätsanalyse</b><br><span class='muted small'>Automatische Auswertung der vorhandenen Massentest-Ergebnisse.</span></div><a class='btn2' href='/test'>← Zurück zur Dokumentenprüfung</a></div>
    {saved_msg}
    <div class='card'>
      <div class='section-head'><h2>Automatische Qualitätsanalyse</h2><span class='count-badge'>Sprint 2B</span></div>
      <p class='muted'>Diese Auswertung nutzt nur vorhandene Massentest-Ergebnisse und gespeicherte Sollwerte. Es wird keine Erkennungslogik ausgeführt oder verändert.</p>
      <div class='grid'>
        <div class='metric'><div class='label'>Dokumente</div><div class='num'>{analysis.get('total', 0)}</div></div>
        <div class='metric'><div class='label'>🟢 keine Abweichungen</div><div class='num ok'>{ampel.get('gruen', 0)}</div></div>
        <div class='metric'><div class='label'>🟡 wenige Abweichungen</div><div class='num warntext'>{ampel.get('gelb', 0)}</div></div>
        <div class='metric'><div class='label'>🔴 viele Abweichungen</div><div class='num bad'>{ampel.get('rot', 0)}</div></div>
      </div>
      <p class='toolbar'><a class='btn2' href='/test/chatgpt-active?scope=active&bereich=Massentest'>Aufgabenexport öffnen</a> <a class='btn2' href='/test/massentest'>Massentest öffnen</a></p>
    </div>
    <div class='card'>
      <div class='section-head'><h2>Qualitäts-Snapshots</h2><span class='count-badge'>{len(snapshots)} Snapshot(s)</span></div>
      <p class='muted small'>Snapshots speichern den aktuellen Qualitätsstand separat unter _massentest/ergebnisse/snapshots. Die Massentest-Ergebnisdatei wird dadurch nicht verändert.</p>
      <form method='post' action='/test/massentest/analysis/snapshot' data-progress='0' data-working='Qualitäts-Snapshot wird gespeichert ...'>
        <button class='btn' type='submit'>Aktuellen Snapshot speichern</button>
      </form>
      <div style='margin-top:14px'>{snapshot_table}</div>
    </div>
    <div class='card'>
      <div class='section-head'><h2>Buildvergleich</h2><span class='count-badge'>Snapshot-Vergleich</span></div>
      <p class='muted small'>Vergleicht zwei gespeicherte Snapshots je Dokument und Feld: verbessert, verschlechtert, unverändert, neu auffällig oder nicht mehr auffällig.</p>
      {compare_form}
      {compare_html}
    </div>
    <div class='card'>
      <h2>Prioritätenliste</h2>
      <p class='muted small'>Automatisch berechnet: Ein Feld mit vielen abweichenden Dokumenten hat den größten möglichen Qualitätsgewinn.</p>
      {priority_table}
    </div>
    <div class='card'>
      <h2>Felder mit den meisten Abweichungen</h2>
      {field_table}
    </div>
    <div class='grid'>
      <div class='card'><h2>Lieferanten mit vielen Fehlern</h2>{supplier_table}</div>
      <div class='card'><h2>Dokumenttypen mit vielen Fehlern</h2>{doctype_table}</div>
    </div>
    <div class='card'>
      <h2>Dokumente mit den meisten Abweichungen</h2>
      {docs_table}
    </div>
    <div class='card'>
      <h2>Snapshot-Struktur</h2>
      <p class='muted'>Technische Übersicht der aktuell erzeugbaren Snapshot-Daten.</p>
      <div class='legend'>
        <span><b>Schema</b> {esc(snapshot_summary['schema'])}</span>
        <span><b>Dokumente</b> {snapshot_summary['documents']}</span>
        <span><b>Felder</b> {snapshot_summary['fields']}</span>
        <span><b>Baseline</b> {esc(snapshot_summary['baseline'])}</span>
      </div>
    </div>
    """
    return layout("Dokumentenprüfung", body)


@app.get("/test/massentest", response_class=HTMLResponse)
@app.get("/massentest", response_class=HTMLResponse)
def massentest_page(msg: str = "", pruefstatus: str = "alle", q: str = "") -> HTMLResponse:
    ensure_massentest_dirs()
    # 3.8.2: Oberfläche, Prüfliste und Export müssen aus derselben Datenbasis kommen.
    # Vor dem Anzeigen werden aktive Massentest-Abweichungen deshalb mit den Projektaufgaben synchronisiert.
    try:
        if 'massentest_reconcile_active_tasks_for_export_371' in globals():
            massentest_reconcile_active_tasks_for_export_371()
    except Exception as e:
        try:
            massentest_log(f"3.8.2 Reconcile vor Anzeige fehlgeschlagen: {e}")
        except Exception:
            pass
    rows = massentest_read_results()
    stats = massentest_stats(rows)
    qstats = massentest_quality_stats(rows)
    vstats = massentest_validation_stats(rows)
    progress = int(qstats.get("progress", 0))

    # Workflow-Kacheln bewusst nur nach echtem Projektzustand einfärben.
    # Vor Upload/Import ist Schritt 1 nicht blau/aktiv.
    step1_cls = "done" if qstats.get("total", 0) else ("current" if stats.get("wartend", 0) else "pending")
    step2_cls = "done" if qstats.get("missing", 0) == 0 and qstats.get("total", 0) else ("current" if qstats.get("total", 0) else "pending")
    step3_cls = "done" if (qstats.get("passed", 0) or qstats.get("deviations", 0)) else ("current" if qstats.get("total", 0) and qstats.get("missing", 0) == 0 else "pending")
    step4_cls = "done" if qstats.get("passed", 0) and qstats.get("passed", 0) == qstats.get("total", 0) else ("current" if qstats.get("open", 0) else "pending")
    # Sichtbare Workflow-Führung: aktive oder bereits erledigte Schritte bleiben als blaue Primärbuttons sichtbar.
    # Noch nicht sinnvolle Schritte bleiben neutral.
    step1_btn = "btn" if step1_cls in {"current", "done"} else "btn2"
    step2_btn = "btn" if step2_cls in {"current", "done"} else "btn2 success"
    step3_btn = "btn" if step3_cls in {"current", "done"} else "btn2 success"
    step4_btn = "btn" if step4_cls in {"current", "done"} else "btn2 success"
    with_ref = max(0, int(qstats.get('total', 0)) - int(qstats.get('missing', 0)))
    try:
        ref_count = len(massentest_read_references())
    except Exception:
        ref_count = 0
    # 3.6.2: Testdokumente nicht mehr aus dem Dateisystem zählen.
    # Dort liegen nach mehreren Läufen Kopien wie _002/_003/_004 und Viewer-/Arbeitsdateien,
    # wodurch aus 127 echten Testfällen schnell 600+ PDFs werden.
    # Maßgeblich sind nur die Ergebnis-/Referenzdatensätze.
    try:
        test_docs_total = max(
            int(qstats.get('total', 0)),
            int(ref_count),
        )
    except Exception:
        test_docs_total = int(qstats.get('total', 0) or 0)
    if qstats.get('total', 0):
        lauf_status_text = 'Testlauf vorhanden'
    elif test_docs_total:
        lauf_status_text = 'Bereit für neuen Testlauf'
    else:
        lauf_status_text = 'Noch keine Testdokumente'
    lauf_diag = massentest_laufdiagnose(rows)
    missing_list = lauf_diag.get('nicht_verarbeitet_liste', []) if isinstance(lauf_diag, dict) else []
    missing_html = ''
    if missing_list:
        details = lauf_diag.get('matching_details', []) if isinstance(lauf_diag, dict) else []
        detail_items = []
        for d in list(details)[:80]:
            try:
                similar = d.get('aehnliche_ergebnisse') or []
                similar_html = ''.join(f"<li>{esc(str(x))}</li>" for x in list(similar)[:8]) or "<li class='muted'>keine ähnlichen Ergebnisnamen gefunden</li>"
                keys = ', '.join(str(x) for x in list(d.get('suchschluessel') or [])[:6])
                detail_items.append(
                    f"<li style='margin-bottom:10px'><b>{esc(str(d.get('referenz','')))}</b>"
                    f"<div class='muted small'>Normalname: {esc(str(d.get('normalname','')))}<br>Suchschlüssel: {esc(keys)}<br>Grund: {esc(str(d.get('grund','')))}</div>"
                    f"<details><summary>ähnliche Ergebnisnamen</summary><ol>{similar_html}</ol></details></li>"
                )
            except Exception:
                continue
        items = ''.join(detail_items) or ''.join(f"<li>{esc(str(x))}</li>" for x in missing_list[:80])
        more = ''
        try:
            rest = len(missing_list) - 80
            if rest > 0:
                more = f"<li class='muted'>... und {rest} weitere</li>"
        except Exception:
            pass
        processed = lauf_diag.get('verarbeitete_ergebnisse', []) if isinstance(lauf_diag, dict) else []
        processed_items = ''.join(f"<li>{esc(str(x))}</li>" for x in list(processed)[:140])
        if len(processed) > 140:
            processed_items += f"<li class='muted'>... und {len(processed)-140} weitere</li>"
        processed_html = f"<details style='margin-top:12px'><summary><b>Tatsächlich verarbeitete Ergebnisdateien anzeigen</b> ({len(processed)})</summary><ol style='margin-top:10px'>{processed_items}</ol></details>"
        missing_html = f"<details class='hint small' style='margin-top:12px'><summary><b>Nicht verarbeitete Referenzen anzeigen</b> ({len(missing_list)})</summary><ol style='margin-top:10px'>{items}{more}</ol>{processed_html}</details>"
    trace_text = massentest_trace_read(700) if 'massentest_trace_read' in globals() else ''
    trace_html = f"<details class='hint small' style='margin-top:12px'><summary><b>Testlauf-Trace anzeigen</b></summary><textarea style='width:100%;min-height:340px;font-family:Consolas,monospace;font-size:12px' readonly>{esc(trace_text)}</textarea></details>"
    abw_count = int(qstats.get('deviations', 0) or 0)
    bestanden_count = int(qstats.get('passed', 0) or 0)
    offen_count = int(qstats.get('open', 0) or 0)
    abw_word = "Abweichung" if abw_count == 1 else "Abweichungen"
    dok_word = "Dokument" if bestanden_count == 1 else "Dokumente"
    if abw_count:
        qc_empfehlung = f"Zuerst die {abw_count} {abw_word} beheben. Anschließend die {bestanden_count} bestandenen {dok_word} schrittweise fachlich validieren."
    elif offen_count:
        qc_empfehlung = f"Es gibt keine Abweichungen. Kläre die {offen_count} offenen Dokumente und validiere die {bestanden_count} bestandenen {dok_word} schrittweise fachlich."
    else:
        qc_empfehlung = "Alle Dokumente haben den Status Bestanden. Beginne jetzt mit der fachlichen Validierung."
    # Kompatibilität: alte Filterlinks werden nicht mehr als eigene Bedienlogik genutzt.
    body = f"""
    <div class='card' id='qualitaetscenter'>
      <div class='section-head'><h2>Massentest</h2><span class='count-badge'>Dokumentenprüfung</span></div>
      <p><a class='btn2' href='/test'>← Zurück zur Dokumentenprüfung</a></p>
      <p class='muted'>Massentest-Arbeitsbereich für technischen Gesamtstatus, Abweichungen, fachliche Prüfung, Nacharbeit, Sonderfälle und die Prüfliste.</p>
      <p class='muted small'>Getrennter Testbereich unter <span class='folder-name'>C:\ScanSnap_Roh-Scan-ecoDMS\_massentest</span>. Keine ecoDMS-Ablage, kein Produktivzähler, kein Etikettendruck.</p>
      {f"<div class='flash'>{esc(msg)}</div>" if msg else ""}
      <div class='hint' style='margin-bottom:14px'>
        <div class='section-head'><div><b>Gesamtübersicht</b><div class='muted small'>Technischer Fortschritt</div></div><span class='count-badge'>{progress} %</span></div>
        <div class='progress-wrap' style='height:8px;margin-top:8px'><div class='progress-bar' style='width:{max(0,min(100,progress))}%'></div></div>
        <div class='legend' style='margin-top:10px'>
          <span><b>{qstats['total']}</b> Dokumente</span>
          <span><b>{qstats['passed']}</b> Technisch bestanden</span>
          <span><b>{qstats['deviations']}</b> Abweichung</span>
          <span><b>{qstats['open']}</b> Offen</span>
          <span><b>{vstats['valid']}</b> Fachlich validiert</span>
          <span><b>{vstats['open']}</b> Noch fachlich zu prüfen</span>
          <span><b>{vstats.get('nacharbeit',0)}</b> Nachzubearbeiten</span>
          <span><b>{qstats.get('special',0)}</b> Sonderfälle</span>
        </div>
      </div>
      {f"<p class='hint small'><b>Technische Abweichungen vorhanden:</b> {vstats['active_errors']} Dokumente<br><span class='muted'>Diese können unabhängig von der fachlichen Prüfung bearbeitet werden.</span></p>" if vstats.get('active_errors',0) else ""}
      <h3>Arbeitsbereiche</h3>
      <div class='grid'>
        <a class='hint' href='/test/massentest#gruppe-abweichung' style='display:block;text-decoration:none;color:inherit'><div class='section-head'><b>Abweichungen bearbeiten</b><span class='count-badge'>{qstats['deviations']}</span></div><div class='muted small'>Technische Abweichungen prüfen und korrigieren</div></a>
        <a class='hint' href='/test/massentest#gruppe-technisch-bestanden-noch-fachlich-zu-pruefen' style='display:block;text-decoration:none;color:inherit'><div class='section-head'><b>Noch fachlich zu prüfen</b><span class='count-badge'>{vstats['open']}</span></div><div class='muted small'>Dokumente prüfen</div></a>
        <a class='hint' href='/test/massentest#gruppe-fachliche-nacharbeit' style='display:block;text-decoration:none;color:inherit'><div class='section-head'><b>Nachzubearbeiten</b><span class='count-badge'>{vstats.get('nacharbeit',0)}</span></div><div class='muted small'>Fachliche Nacharbeit öffnen</div></a>
        <a class='hint' href='/test/massentest#gruppe-technisch-bestanden-fachlich-validiert' style='display:block;text-decoration:none;color:inherit'><div class='section-head'><b>Fachlich validiert</b><span class='count-badge'>{vstats['valid']}</span></div><div class='muted small'>Freigegebene Dokumente anzeigen</div></a>
        <a class='hint' href='/test/massentest#gruppe-sonderfaelle' style='display:block;text-decoration:none;color:inherit'><div class='section-head'><b>Sonderfälle</b><span class='count-badge'>{vstats.get('special',0)}</span></div><div class='muted small'>Sonderfälle anzeigen</div></a>
        <a class='hint' href='/test/massentest#pruefliste' style='display:block;text-decoration:none;color:inherit'><div class='section-head'><b>Alle Dokumente</b><span class='count-badge'>{qstats['total']}</span></div><div class='muted small'>Gesamte Prüfliste öffnen</div></a>
      </div>
      <p class='hint small'><b>Empfehlung:</b> {esc(qc_empfehlung)}</p>
    </div>

    <div class='card'>
      <h2 id='massentest-diagnose'>Massentest-Manager</h2>
      <div class='hint small' style='margin-bottom:12px'><b>Referenzsicherung:</b> Sollwerte und Testergebnisse sind getrennt. Sollwerte bleiben beim Neuerzeugen eines Testlaufs erhalten.</div>
      <div class='hint small' style='margin-bottom:12px'><b>Referenzen:</b> {test_docs_total} · <b>Sollwerte:</b> {ref_count} · <b>Letzter Testlauf:</b> {lauf_diag.get('ergebnis_gesamt', qstats['total']) if qstats.get('total',0) else '–'} · <b>Nicht verarbeitet:</b> {lauf_diag.get('nicht_verarbeitet', 0)}</div>
      {missing_html}
      {trace_html}
      <div class='toolbar' style='margin-top:12px;align-items:stretch'>
        <form method='post' action='/test/massentest/reset' data-working='Testergebnisse werden neu erzeugt vorbereitet...' data-confirm-title='Testergebnisse neu erzeugen?' data-confirm-message='IST-Werte, Aufgaben/Prüfergebnisse und temporäre Viewer-Dateien werden gelöscht. PDFs werden wieder auf wartend gelegt. Sollwerte bleiben erhalten.' data-confirm-details='Danach bitte Schritt 1 „Dokumente erkennen“ starten. Produktivordner, Zähler und ecoDMS bleiben unberührt.' data-confirm-kind='eco-modal-success' data-confirm-ok='Ja, neu erzeugen'><button class='btn' type='submit'>Testergebnisse neu erzeugen</button></form>
        <form method='post' action='/test/massentest/clear-results' data-confirm-title='Nur Testergebnisliste löschen?' data-confirm-message='Nur die aktuelle IST-/Ergebnisliste wird gelöscht. PDFs und Sollwerte bleiben erhalten.' data-confirm-kind='eco-modal-danger' data-confirm-ok='Ja, Ergebnisliste löschen'><button class='btn2' type='submit'>Nur Ergebnisliste löschen</button></form>
        <form method='post' action='/test/massentest/rebuild' data-working='PDF-Liste wird neu aufgebaut...'><button class='btn2' type='submit'>PDF-Liste reparieren</button></form>
        <a class='btn2' href='/test/massentest#massentest-diagnose'>Testlauf-Diagnose anzeigen</a>
      </div>
      <details class='hint small' style='margin-top:12px'><summary><b>Gefahrenbereich</b> – Referenzen vollständig löschen</summary>
        <div class='toolbar'>
          <form method='post' action='/test/massentest/full-clear' data-confirm-title='Sollwerte und Testergebnisse vollständig löschen?' data-confirm-message='Diese Aktion löscht auch die gesicherten Sollwerte/Referenzen. Das ist normalerweise NICHT nötig.' data-confirm-details='Nur verwenden, wenn das Prüfprojekt komplett neu aufgebaut werden soll. PDFs bleiben erhalten, aber alle Referenzwerte müssen neu gepflegt werden.' data-confirm-kind='eco-modal-danger' data-confirm-ok='Ja, Sollwerte endgültig löschen'><button class='btn2 danger' type='submit'>Sollwerte + Testergebnisse löschen</button></form>
        </div>
      </details>
    </div>

    <div class='card'>
      <h2>Arbeitsablauf</h2>
      <form method='post' action='/test/massentest/upload' enctype='multipart/form-data' data-working='Massentest-Upload läuft...'>
        <input type='file' name='files' multiple accept='.pdf,.zip,application/pdf,application/zip'>
        <button class='btn' type='submit'>Dokumente hinzufügen</button>
      </form>
      <div class='workflow-bar'>
        <div class='workflow-step {step1_cls}'><b>1. Technischer Test</b><form method='post' action='/test/massentest/run' data-working='Dokumente werden erkannt... Fortschritt: Verarbeitung läuft.'><button class='{step1_btn}' type='submit'>1. Dokumente erkennen</button></form><div class='muted small'>Startbasis ab 3.6.7: alle Referenzen, nicht nur entpackt.</div></div>
        <div class='workflow-step {step2_cls}'><b>2. Abweichungen beheben</b><form method='post' action='/test/massentest/bulk-istwerte' data-working='Neue Referenz wird übernommen ...' data-confirm-title='Neue Dokumente als Referenz übernehmen?' data-confirm-message='Für alle offenen Massentest-Dokumente werden die aktuellen Ist-Werte als Sollwerte gespeichert. Der Soll-Dateiname wird automatisch nach der Dateinamen-Konfiguration gebildet.' data-confirm-details='Es wird nichts gelöscht und nichts als bestanden markiert.' data-confirm-kind='eco-modal-success' data-confirm-ok='Ja, als Referenz übernehmen'><input type='hidden' name='mode' value='open_all'><button class='{step2_btn}' type='submit'>2. Neue Referenz übernehmen</button></form><div class='muted small'>Sollwerte werden im Massentest-Manager angezeigt.</div></div>
        <div class='workflow-step {step3_cls}'><b>3. Technisch bestanden</b><form method='post' action='/test/massentest/auto-check' data-working='Soll/Ist-Prüfung läuft...' data-confirm-title='Alle Dokumente prüfen?' data-confirm-message='Alle vorhandenen Massentest-Ergebnisse werden nur gegen gespeicherte Sollwerte geprüft. Es werden keine Sollwerte geschrieben und nichts automatisch als bestanden markiert.' data-confirm-details='Dokumente bleiben bis zur Entscheidung Offen. Danach kannst du sie bewusst als Bestanden markieren.' data-confirm-kind='eco-modal-success' data-confirm-ok='Ja, prüfen'><button class='{step3_btn}' type='submit'>3. Soll/Ist prüfen</button></form><div class='muted small'>Ergebnis wird im technischen Status oben angezeigt.</div></div>
        <div class='workflow-step {step4_cls}'><b>4. Fachlich validieren, dann produktiv freigeben</b><form method='post' action='/test/massentest/mark-clean-passed' data-working='Bestanden wird übernommen ...' data-confirm-title='Dokumente als Bestanden markieren?' data-confirm-message='Alle Dokumente mit vorhandenen Sollwerten und ohne Abweichung erhalten den Status Bestanden.' data-confirm-details='Dokumente ohne Sollwerte oder mit Abweichungen bleiben offen.' data-confirm-kind='eco-modal-success' data-confirm-ok='Ja, Bestanden'><button class='{step4_btn}' type='submit'>4. Bestanden übernehmen</button></form><div class='muted small'>Fachlicher Stand steht in der Dokumentenprüfung.</div></div>
      </div>
      <p class='hint small' style='margin-top:12px'><b>Ablauf:</b> Technischer Test → Abweichungen beheben → Technisch bestanden → Fachlich validieren → Produktiv freigeben.</p>
      <p class='hint small'><b>Reset/Werkzeuge</b> findest du jetzt oben im Massentest-Manager. Die Sollwerte werden dort getrennt von den aktuellen Testergebnissen behandelt.</p>
      <p class='muted small'>ZIP-Dateien werden nach <span class='folder-name'>eingang_zip</span> gespeichert und PDFs nach <span class='folder-name'>entpackt</span> extrahiert. Der CSV-Export ist aus der Hauptbedienung entfernt und bleibt nur intern/technisch vorhanden.</p>
    </div>

    <div id='pruefliste' class='card'>
      <div class='section-head'><h2>Prüfliste</h2><span class='count-badge'>eindeutige Gruppen</span></div>
      <div class='legend' aria-label='Legende Massenteststatus'>
        <span><b>✗</b> Abweichung</span>
        <span><b>○</b> Offen</span>
        <span><b>!</b> Nachzubearbeiten</span>
        <span><b>⭐</b> Sonderfälle</span>
        <span><b>✓</b> Technisch bestanden – noch fachlich zu prüfen</span>
        <span><b>✓</b> Technisch bestanden – fachlich validiert</span>
      </div>
      <p class='hint small'>Tipp: <b>Ist-Werte übernehmen</b> speichert die fachlichen Sollwerte. Der <b>Soll-Dateiname</b> wird automatisch aus diesen Sollwerten nach der hinterlegten Dateinamen-Konfiguration gebildet und nicht mehr händisch eingegeben.</p>
      <p class='hint small'><b>Wichtig:</b> Wenn du gerade erst alle Ist-Werte als Referenz übernommen hast, ist eine anschließende Soll/Ist-Prüfung erwartungsgemäß fehlerfrei. Echte Abweichungen entstehen erst, wenn vorhandene Referenzen mit einer neuen Erkennung verglichen werden oder du Sollwerte manuell korrigierst.</p>
      <form method='get' action='/test/massentest' class='toolbar'>
        <input type='text' name='q' value='{esc(q)}' placeholder='Suche: Lieferant, Dateiname, RECHNR, Betrag ...' style='min-width:360px'>
        <button class='btn2' type='submit'>Suchen</button>
        <a class='btn2' href='/test/massentest'>Zurücksetzen</a>
      </form>
      <p class='muted small'>Hinweis: Die Prüfliste zeigt jedes Dokument genau einmal: Abweichung, Nachzubearbeiten, Offen, Sonderfall, technisch bestanden und noch fachlich zu prüfen oder technisch bestanden und fachlich validiert.</p>
      <div class='test-doc-sections'>{massentest_grouped_overview_html(rows, q)}</div>
      <script>
      (function(){{
        const key = 'ecodms.massentest.groupState';
        const sections = Array.from(document.querySelectorAll('details.test-doc-section[id]'));
        const shouldRestore = !!window.location.hash || new URLSearchParams(window.location.search).has('msg');
        if (!shouldRestore) sessionStorage.removeItem(key);
        let state = {{}};
        if (shouldRestore) {{
          try {{ state = JSON.parse(sessionStorage.getItem(key) || '{{}}') || {{}}; }} catch(e) {{ state = {{}}; }}
        }}
        sections.forEach(function(section){{
          if (Object.prototype.hasOwnProperty.call(state, section.id)) section.open = !!state[section.id];
          section.addEventListener('toggle', function(){{
            let current = {{}};
            try {{ current = JSON.parse(sessionStorage.getItem(key) || '{{}}') || {{}}; }} catch(e) {{ current = {{}}; }}
            current[section.id] = section.open;
            sessionStorage.setItem(key, JSON.stringify(current));
          }});
        }});
      }})();
      </script>
    </div>

    """
    return layout("Massentest", body)


@app.post("/test/massentest/upload")
@app.post("/massentest/upload")
async def massentest_upload(request: Request, files: list[UploadFile] = File(default=[])):
    ensure_massentest_dirs()
    pdf_count = 0
    zip_count = 0
    saved_count = 0
    errors: list[str] = []
    if not files:
        try:
            form = await request.form()
            raw_files = form.getlist("files")
            files = [x for x in raw_files if hasattr(x, "filename")]
        except Exception as e:
            errors.append(f"Upload konnte nicht gelesen werden: {e}")
    if not files:
        msg = "Kein Upload empfangen. Bitte Datei erneut auswählen und ZIP/PDF hochladen klicken."
        massentest_log(msg)
        return RedirectResponse(url=f"/test/massentest?msg={quote(msg)}", status_code=303)
    for f in files:
        original = f.filename or "upload"
        lower = original.lower()
        try:
            if lower.endswith(".zip"):
                target = massentest_unique_upload_path(MASSTEST_ZIP_DIR, original, default_ext=".zip")
                with open(target, "wb") as out:
                    shutil.copyfileobj(f.file, out)
                saved_count += 1
                zip_count += 1
                massentest_log(f"ZIP gespeichert: {target}")
                extracted, zip_errors = massentest_extract_zip(target)
                pdf_count += extracted
                errors.extend(zip_errors)
            elif lower.endswith(".pdf"):
                target = massentest_unique_path(MASSTEST_UNPACKED_DIR, original)
                with open(target, "wb") as out:
                    shutil.copyfileobj(f.file, out)
                saved_count += 1
                pdf_count += 1
                massentest_log(f"PDF gespeichert: {target}")
            else:
                errors.append(f"{original}: übersprungen, keine PDF/ZIP-Datei")
        except Exception as e:
            errors.append(f"{original}: {e}")
            massentest_log(f"UPLOAD-FEHLER {original}: {e}")
        finally:
            try:
                await f.close()
            except Exception:
                pass
    msg = f"Upload abgeschlossen: {saved_count} Datei(en) gespeichert, {pdf_count} PDF(s) bereit, {zip_count} ZIP(s)."
    if errors:
        msg += " Hinweise: " + " | ".join(errors[:5])
    massentest_log(msg)
    return RedirectResponse(url=f"/test/massentest?msg={quote(msg)}", status_code=303)


@app.post("/massentest/upload_zip")
async def massentest_upload_zip(request: Request, files: list[UploadFile] = File(default=[])):
    return await massentest_upload(request, files)


@app.post("/massentest/upload-pdf")
async def massentest_upload_pdf(request: Request, files: list[UploadFile] = File(default=[])):
    return await massentest_upload(request, files)


@app.post("/test/massentest/run")
@app.post("/massentest/run")
def massentest_run():
    ensure_massentest_dirs()
    # Vor-Trace: zeigt, ob der Start überhaupt aus dem richtigen Ordner kommt.
    try:
        massentest_trace_reset("Massentest Start-Endpunkt")
        massentest_trace(f"Start /test/massentest/run | entpackt={len(list(MASSTEST_UNPACKED_DIR.glob('*.pdf')))} | verarbeitet={len(list(MASSTEST_DONE_DIR.glob('*.pdf')))} | fehler={len(list(MASSTEST_ERROR_DIR.glob('*.pdf')))} | zip={len(list(MASSTEST_ZIP_DIR.glob('*.zip')))}")
    except Exception:
        pass
    if not list(MASSTEST_UNPACKED_DIR.glob("*.pdf")):
        moved = 0
        extracted = 0
        for folder in [MASSTEST_DONE_DIR, MASSTEST_ERROR_DIR]:
            try:
                for pdf in sorted(folder.glob("*.pdf"), key=lambda p: p.name.lower()):
                    ziel = massentest_unique_path(MASSTEST_UNPACKED_DIR, pdf.name)
                    shutil.move(str(pdf), str(ziel))
                    moved += 1
            except Exception as e:
                massentest_log(f"AUTO-REBUILD-HINWEIS {folder}: {e}")
        if not list(MASSTEST_UNPACKED_DIR.glob("*.pdf")):
            for z in sorted(MASSTEST_ZIP_DIR.glob("*.zip"), key=lambda p: p.name.lower()):
                c, _errors = massentest_extract_zip(z)
                extracted += c
        if moved or extracted:
            massentest_log(f"Massentest vor Start automatisch neu aufgebaut: moved={moved}, extracted={extracted}")
    if not list(MASSTEST_UNPACKED_DIR.glob("*.pdf")):
        return RedirectResponse(url=f"/test/massentest?msg={quote('Keine wartenden PDFs gefunden. Bitte ZIP/PDF hochladen oder Massentest neu aufbauen klicken.')}", status_code=303)
    ok, fail = massentest_process_all()
    return RedirectResponse(url=f"/test/massentest?msg={quote(f'Massentest abgeschlossen: {ok} OK, {fail} Fehler.')}", status_code=303)




def massentest_prepare_sources_for_processing() -> tuple[int, int, list[str]]:
    """Sorgt dafür, dass ein Massentest aus vorhandenen Quellen wieder startbar ist.

    Rückgabe: (zurueckgelegte_pdfs, aus_zip_entpackte_pdfs, hinweise)
    """
    ensure_massentest_dirs()
    moved = 0
    extracted = 0
    hints: list[str] = []
    if not list(MASSTEST_UNPACKED_DIR.glob("*.pdf")) and not massentest_read_results():
        for folder in [MASSTEST_DONE_DIR, MASSTEST_ERROR_DIR]:
            try:
                for pdf in sorted(folder.glob("*.pdf"), key=lambda p: p.name.lower()):
                    ziel = massentest_unique_path(MASSTEST_UNPACKED_DIR, pdf.name)
                    shutil.move(str(pdf), str(ziel))
                    moved += 1
            except Exception as e:
                hints.append(f"{folder.name}: {e}")
        if not list(MASSTEST_UNPACKED_DIR.glob("*.pdf")):
            for z in sorted(MASSTEST_ZIP_DIR.glob("*.zip"), key=lambda p: p.name.lower()):
                c, es = massentest_extract_zip(z)
                extracted += c
                hints.extend(es)
    return moved, extracted, hints


@app.post("/test/massentest/auto-check")
@app.post("/massentest/auto-check")
def massentest_auto_check():
    """Schritt 3: reine Soll/Ist-Prüfung."""
    ensure_massentest_dirs()
    rows = massentest_read_results()
    total = len(rows)
    massentest_progress_start("Alle Dokumente prüfen", total, "Soll/Ist-Prüfung startet")
    clean = deviations = missing = errors = skipped = 0
    stamp = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
    for i, row in enumerate(rows):
        name = row.get("alter_dateiname", "") or row.get("pdf_datei", "")
        massentest_progress_write("Alle Dokumente prüfen", i + 1, total, name, "running", "Soll/Ist wird geprüft")
        ws = massentest_derive_workflow(row)
        if ws in {"TEST_BESTANDEN", "AUSREISSER", "IGNORIERT"}:
            skipped += 1
            rows[i] = row
            continue
        if str(row.get("status", "OK")).strip().upper() == "FEHLER":
            row = massentest_set_workflow(row, "ABWEICHUNG", f"Prüfung {stamp}: Verarbeitungsfehler")
            errors += 1
            rows[i] = row
            continue
        try:
            row = massentest_aktualisiere_soll_dateiname(row)
            soll_count, diffs = massentest_diff_details(row)
            if soll_count == 0:
                row = massentest_set_workflow(row, "ERKANNT", f"Prüfung {stamp}: Referenz/Sollwerte fehlen")
                row["vergleich_ok"] = ""
                row["abweichungen"] = ""
                missing += 1
            elif not diffs:
                closed_id = massentest_close_existing_task_if_clean(row, "Soll/Ist fehlerfrei")
                row = massentest_set_workflow(row, "GEPRUEFT_OK", f"Prüfung {stamp}: fehlerfrei, bereit für Test bestanden")
                row["vergleich_ok"] = "1"
                row["abweichungen"] = ""
                if closed_id:
                    row["aufgabe_id"] = ""
                    row["hinweis"] = ((row.get("hinweis", "") + " ").strip() + f"Aufgabe {closed_id} automatisch erledigt.").strip()
                clean += 1
            else:
                state = "AUFGABE" if row.get("aufgabe_id") else "ABWEICHUNG"
                row = massentest_set_workflow(row, state, f"Prüfung {stamp}: {len(diffs)} Abweichung(en)")
                row["vergleich_ok"] = "0"
                row["abweichungen"] = "; ".join(f"{label}: Soll={soll} / Ist={ist}" for label, soll, ist in diffs)
                deviations += 1
            rows[i] = row
        except Exception as e:
            row = massentest_set_workflow(row, "ABWEICHUNG", f"Prüfung {stamp}: Fehler {e}")
            row["vergleich_ok"] = "0"
            row["abweichungen"] = str(e)
            rows[i] = row
            errors += 1
    massentest_write_results(rows)
    massentest_progress_finish("Alle Dokumente prüfen", total, "Prüfung abgeschlossen")
    msg = f"Soll/Ist-Prüfung abgeschlossen: {total} Dokument(e), {clean} fehlerfrei, {deviations} Abweichung(en), {missing} ohne Referenz/Sollwerte, {errors} Fehler. Es wurde nichts als Test bestanden markiert."
    if skipped:
        msg += f" {skipped} bereits abgeschlossene/ignorierte Dokumente übersprungen."
    massentest_log(msg)
    return RedirectResponse(url=f"/test/massentest?msg={quote(msg)}", status_code=303)


@app.post("/test/massentest/mark-clean-passed")
@app.post("/massentest/mark-clean-passed")
def massentest_mark_clean_passed():
    """Schritt 4: nur bereits fehlerfrei geprüfte Dokumente abschließen."""
    ensure_massentest_dirs()
    rows = massentest_read_results()
    total = len(rows)
    massentest_progress_start("Test bestanden übernehmen", total, "Abschluss startet")
    marked = skipped = deviations = missing = 0
    stamp = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
    for i, row in enumerate(rows):
        name = row.get("alter_dateiname", "") or row.get("pdf_datei", "")
        massentest_progress_write("Test bestanden übernehmen", i + 1, total, name, "running", "Abschluss wird geprüft")
        ws = massentest_derive_workflow(row)
        if ws == "GEPRUEFT_OK":
            soll_count, diffs = massentest_diff_details(row)
            if soll_count == 0:
                row = massentest_set_workflow(row, "ERKANNT", f"Abschluss {stamp}: Referenz/Sollwerte fehlen")
                missing += 1
            elif diffs:
                row = massentest_set_workflow(row, "ABWEICHUNG", f"Abschluss {stamp}: {len(diffs)} Abweichung(en)")
                deviations += 1
            else:
                closed_id = massentest_close_existing_task_if_clean(row, "Test bestanden")
                row = massentest_set_workflow(row, "TEST_BESTANDEN", f"Abschluss {stamp}: Test bestanden")
                row["vergleich_ok"] = "1"
                if closed_id:
                    row["aufgabe_id"] = ""
                marked += 1
        else:
            skipped += 1
        rows[i] = row
    massentest_write_results(rows)
    massentest_progress_finish("Test bestanden übernehmen", total, "Abschluss abgeschlossen")
    msg = f"Abschluss: {marked} Dokument(e) als Test bestanden markiert. {deviations} Abweichung(en), {missing} ohne Referenz, {skipped} nicht bereit/übersprungen."
    massentest_log(msg)
    return RedirectResponse(url=f"/test/massentest?msg={quote(msg)}", status_code=303)


@app.get("/test/massentest/csv")
@app.get("/massentest/csv")
def massentest_csv():
    ensure_massentest_dirs()
    if not MASSTEST_RESULTS_CSV.exists():
        massentest_write_results(massentest_read_results())
    data = read_text(MASSTEST_RESULTS_CSV)
    headers = {"Content-Disposition": "attachment; filename=massentest_ergebnisse.csv"}
    return PlainTextResponse(data, media_type="text/csv; charset=utf-8", headers=headers)


@app.post("/test/massentest/clear-results")
@app.post("/massentest/clear-results")
def massentest_clear_results():
    ensure_massentest_dirs()
    gesichert = 0
    try:
        gesichert = massentest_save_references_from_rows(massentest_read_results())
    except Exception as e:
        massentest_log(f"Referenzsicherung vor Löschen fehlgeschlagen: {e}")
    for p in [MASSTEST_RESULTS_JSON, MASSTEST_RESULTS_CSV]:
        try:
            if p.exists():
                p.unlink()
        except Exception:
            pass
    massentest_log(f"Testergebnisse geloescht; Sollwerte/Referenzen bleiben erhalten ({gesichert} aktualisiert).")
    return RedirectResponse(url=f"/test/massentest?msg={quote('Testergebnisse gelöscht. Sollwerte bleiben erhalten.')}", status_code=303)


@app.post("/test/massentest/full-clear")
@app.post("/massentest/full-clear")
def massentest_full_clear():
    """Löscht Referenz-/Sollwerte UND Testergebnisse. PDFs bleiben erhalten."""
    ensure_massentest_dirs()
    for p in [MASSTEST_RESULTS_JSON, MASSTEST_RESULTS_CSV, MASSTEST_REFERENCES_JSON]:
        try:
            if p.exists():
                p.unlink()
        except Exception as e:
            massentest_log(f"FULL-CLEAR-HINWEIS {p}: {e}")
    try:
        if MASSTEST_VIEWER_DIR.exists():
            shutil.rmtree(MASSTEST_VIEWER_DIR)
        MASSTEST_VIEWER_DIR.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        massentest_log(f"FULL-CLEAR-HINWEIS Viewer: {e}")
    massentest_log("Massentest Sollwerte und Testergebnisse vollstaendig geloescht; PDFs bleiben erhalten.")
    return RedirectResponse(url=f"/test/massentest?msg={quote('Sollwerte und Testergebnisse gelöscht. PDFs bleiben erhalten.')}", status_code=303)


@app.post("/test/massentest/reset")
@app.post("/massentest/reset")
def massentest_reset():
    """Setzt den Massentest weich zurück.

    Wichtig ab 3.0.12:
    - PDFs werden NICHT gelöscht.
    - Bereits verarbeitete PDFs werden zurück nach _massentest\entpackt gelegt.
    - Ergebnisdateien und Viewer-Dateien werden gelöscht.
    - ZIP-Eingang bleibt erhalten.
    """
    ensure_massentest_dirs()
    moved = 0
    try:
        massentest_save_references_from_rows(massentest_read_results())
    except Exception as e:
        massentest_log(f"Referenzsicherung vor Reset fehlgeschlagen: {e}")
    # PDFs aus verarbeitet/fehler zurück in wartend legen, damit "Massentest starten" erneut funktioniert.
    for folder in [MASSTEST_DONE_DIR, MASSTEST_ERROR_DIR]:
        try:
            if folder.exists():
                for pdf in sorted(folder.glob("*.pdf"), key=lambda p: p.name.lower()):
                    ziel = massentest_unique_path(MASSTEST_UNPACKED_DIR, pdf.name)
                    shutil.move(str(pdf), str(ziel))
                    moved += 1
        except Exception as e:
            massentest_log(f"RESET-HINWEIS {folder}: {e}")
    for p in [MASSTEST_RESULTS_JSON, MASSTEST_RESULTS_CSV]:
        try:
            if p.exists():
                p.unlink()
        except Exception as e:
            massentest_log(f"RESET-HINWEIS {p}: {e}")
    for folder in [MASSTEST_VIEWER_DIR]:
        try:
            if folder.exists():
                shutil.rmtree(folder)
            folder.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            massentest_log(f"RESET-HINWEIS {folder}: {e}")
    # Logs nicht löschen, damit der Reset nachvollziehbar bleibt.
    massentest_log(f"Massentest weich zurueckgesetzt; PDFs behalten/zurueckgelegt: {moved}; ZIP-Eingang bleibt erhalten.")
    msg = f"Massentest zurückgesetzt. {moved} PDF(s) wurden wieder auf wartend gelegt. Es wurden keine PDFs gelöscht."
    return RedirectResponse(url=f"/test/massentest?msg={quote(msg)}", status_code=303)


@app.post("/test/massentest/rebuild")
@app.post("/massentest/rebuild")
def massentest_rebuild():
    """Baut den Massentest wieder aus vorhandenen Quellen auf.

    Hilft besonders nach alten Reset-Versionen, bei denen Ergebnisse/Index gelöscht
    wurden. Es werden zuerst PDFs aus verarbeitet/fehler zurückgelegt. Wenn dann
    keine wartenden PDFs vorhanden sind, werden ZIP-Dateien aus eingang_zip erneut
    entpackt.
    """
    ensure_massentest_dirs()
    moved = 0
    extracted = 0
    errors: list[str] = []
    for folder in [MASSTEST_DONE_DIR, MASSTEST_ERROR_DIR]:
        try:
            if folder.exists():
                for pdf in sorted(folder.glob("*.pdf"), key=lambda p: p.name.lower()):
                    ziel = massentest_unique_path(MASSTEST_UNPACKED_DIR, pdf.name)
                    shutil.move(str(pdf), str(ziel))
                    moved += 1
        except Exception as e:
            errors.append(f"{folder.name}: {e}")
    if not list(MASSTEST_UNPACKED_DIR.glob("*.pdf")):
        for z in sorted(MASSTEST_ZIP_DIR.glob("*.zip"), key=lambda p: p.name.lower()):
            c, es = massentest_extract_zip(z)
            extracted += c
            errors.extend(es)
    msg = f"Massentest neu aufgebaut: {moved} PDF(s) zurückgelegt, {extracted} PDF(s) aus ZIP entpackt."
    if errors:
        msg += " Hinweise: " + " | ".join(errors[:5])
    massentest_log(msg)
    return RedirectResponse(url=f"/test/massentest?msg={quote(msg)}", status_code=303)



def massentest_next_prev_links(rows: list[dict[str, str]], row_id: str) -> tuple[str, str]:
    """Erzeugt robuste Zurueck/Vor-Links fuer Massentest-Detailseiten."""
    try:
        ids = [str(r.get("id", "")) for r in rows or [] if str(r.get("id", "")).strip()]
        if row_id not in ids:
            return "", ""
        def ziel(r: dict[str, str]) -> str:
            status = massentest_row_status(r)
            rid = quote(str(r.get("id", "") or ""))
            if status == "bestanden":
                return f"/test/massentest/fachlich/{rid}"
            if status == "abweichung":
                return "/test/massentest#gruppe-abweichung"
            if status == "offen":
                return "/test/massentest#gruppe-offen"
            return f"/test/massentest/detail/{rid}"
        pos = ids.index(row_id)
        prev_html = ""
        next_html = ""
        if pos > 0:
            prev_html = f"<a class='btn2' href='{ziel(rows[pos - 1])}'>Zurueck</a>"
        if pos < len(ids) - 1:
            next_html = f"<a class='btn2' href='{ziel(rows[pos + 1])}'>Naechstes Dokument</a>"
        return prev_html, next_html
    except Exception:
        return "", ""


def massentest_pdf_response(row_id: str, disposition: str = "inline"):
    rows = massentest_read_results()
    _idx, row = massentest_find_row(rows, row_id)
    if not row:
        raise HTTPException(status_code=404, detail="Massentest-Eintrag nicht gefunden")
    p = massentest_pdf_path(row)
    if not p:
        raise HTTPException(status_code=404, detail="PDF nicht gefunden")
    safe_id = re.sub(r"[^A-Za-z0-9_-]+", "_", row_id)[:80] or "massentest"
    try:
        data = p.read_bytes()
    except PermissionError:
        # Fallback über neutrale Viewer-Kopie.
        try:
            target = MASSTEST_VIEWER_DIR / f"{safe_id}.pdf"
            shutil.copy2(p, target)
            data = target.read_bytes()
        except Exception:
            raise HTTPException(status_code=423, detail="PDF ist gesperrt oder Zugriff wurde verweigert")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF konnte nicht gelesen werden: {e}")
    headers = {
        "Content-Disposition": f'{disposition}; filename="massentest_{safe_id}.pdf"',
        "Cache-Control": "no-store",
        "X-Content-Type-Options": "nosniff",
    }
    return Response(content=data, media_type="application/pdf", headers=headers)


@app.get("/test/massentest/pdf/{row_id}")
def massentest_open_pdf(row_id: str):
    return massentest_pdf_response(row_id, "inline")


@app.get("/test/massentest/pdf-download/{row_id}")
def massentest_download_pdf(row_id: str):
    return massentest_pdf_response(row_id, "attachment")




@app.post("/test/massentest/open-reader/{row_id}")
def massentest_open_reader(row_id: str):
    rows = massentest_read_results()
    _idx, row = massentest_find_row(rows, row_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Massentest-Eintrag nicht gefunden")
    p = massentest_pdf_path(row)
    if not p or not p.exists():
        return RedirectResponse(url=f"/test/massentest/detail/{quote(row_id)}?msg={quote('PDF nicht gefunden.')}", status_code=303)
    try:
        if os.name == "nt":
            os.startfile(str(p))  # type: ignore[attr-defined]
        else:
            subprocess.Popen(["xdg-open", str(p)])
        msg = "PDF wurde im Standard-Reader geöffnet."
    except Exception as e:
        msg = f"PDF konnte nicht im Reader geöffnet werden: {e}"
    return RedirectResponse(url=f"/test/massentest/detail/{quote(row_id)}?msg={quote(msg)}", status_code=303)


@app.post("/test/massentest/open-reader-list/{row_id}")
def massentest_open_reader_list(row_id: str):
    rows = massentest_read_results()
    _idx, row = massentest_find_row(rows, row_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Massentest-Eintrag nicht gefunden")
    p = massentest_pdf_path(row)
    if not p or not p.exists():
        return RedirectResponse(url=f"/test/massentest?msg={quote('PDF nicht gefunden.')}", status_code=303)
    try:
        if os.name == "nt":
            os.startfile(str(p))  # type: ignore[attr-defined]
        else:
            subprocess.Popen(["xdg-open", str(p)])
        msg = "PDF wurde im Standard-Reader geöffnet."
    except Exception as e:
        msg = f"PDF konnte nicht im Reader geöffnet werden: {e}"
    return RedirectResponse(url=f"/test/massentest?msg={quote(msg)}", status_code=303)


def massentest_diff_count(row: dict[str, str]) -> tuple[int, int]:
    """Rückgabe: (Anzahl fachlicher Sollfelder, Anzahl Abweichungen)."""
    soll_count, diffs = massentest_diff_details(row)
    return soll_count, len(diffs)


@app.post("/test/massentest/run-one/{row_id}")
def massentest_run_one(row_id: str):
    rows = massentest_read_results()
    idx, row = massentest_find_row(rows, row_id)
    if row is None or idx is None:
        raise HTTPException(status_code=404, detail="Massentest-Eintrag nicht gefunden")
    old_task = row.get("aufgabe_id", "")
    row, msg = massentest_reprocess_row(row)
    if old_task and not row.get("aufgabe_id"):
        row["aufgabe_id"] = old_task
    soll_count, diff_count = massentest_diff_count(row)
    stamp = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
    if soll_count == 0:
        row["pruefstatus"] = "ungeprueft"
        row["letzter_test"] = f"Test {stamp}: keine Sollwerte vorhanden"
        msg = f"{msg} Keine Sollwerte vorhanden – Dokument bleibt bei 'Sollwerte fehlen'."
    elif diff_count == 0:
        closed_id = massentest_close_existing_task_if_clean(row, "Einzelprüfung fehlerfrei")
        row["pruefstatus"] = "geprueft_ok"
        row["letzter_test"] = f"Test {stamp}: fehlerfrei geprüft"
        if closed_id:
            row["aufgabe_id"] = ""
        msg = f"{msg} Fehlerfrei geprüft: Soll/Ist stimmen überein."
    else:
        # Wichtig: Nach erneutem Test bei Abweichungen nicht in 'offen' verschieben.
        # Der Eintrag bleibt wie im Einzeltest im Bereich Abweichung sichtbar.
        row["pruefstatus"] = "abweichung"
        row["letzter_test"] = f"Test {stamp}: {diff_count} Abweichung(en)"
        msg = f"{msg} Test abgeschlossen: {diff_count} Abweichung(en)."
    rows[idx] = row
    massentest_write_results(rows)
    massentest_log(f"EINZELTEST: {row.get('alter_dateiname','')} -> {msg}")
    return RedirectResponse(url=f"/test/massentest/result/{quote(row_id)}?msg={quote(msg)}", status_code=303)


def massentest_result_values_html(row: dict[str, str]) -> tuple[str, str, bool]:
    """HTML-Bausteine für Massentest-Testergebnis analog Einzeltest."""
    ist_rows = ""
    for label, ist_key, _soll_key in MASSTEST_COMPARE:
        value = str(row.get(ist_key, "") or "").strip()
        ist_rows += f"<tr><td>{esc(label.upper())}</td><td>{esc(value) if value else '<span class=\'muted\'>leer</span>'}</td></tr>"
    soll_count, diffs = massentest_diff_details(row)
    diff_keys = {str(label).lower() for label, _soll, _ist in diffs}
    if soll_count:
        comp_rows = ""
        # Neuer Dateiname ist technisch, nicht fachlicher Fehler.
        dn_ist = str(row.get("neuer_dateiname", "") or "").strip()
        dn_soll = str(row.get("soll_neuer_dateiname", "") or "").strip()
        if dn_ist or dn_soll:
            comp_rows += (
                f"<tr><td>NEUER DATEINAME</td><td>{esc(dn_soll) if dn_soll else '<span class=\'muted\'>automatisch</span>'}"
                f"<div class='tech-note'>technischer Hinweis, keine fachliche Abweichung</div></td>"
                f"<td>{esc(dn_ist) if dn_ist else '<span class=\'muted\'>leer</span>'}</td><td>ℹ️</td></tr>"
            )
        for label, ist_key, soll_key in MASSTEST_COMPARE:
            if soll_key == "soll_neuer_dateiname":
                continue
            ist = str(row.get(ist_key, "") or "").strip()
            soll = str(row.get(soll_key, "") or "").strip()
            if soll or ist:
                ok = (norm_compare(ist) == norm_compare(soll)) if soll else False
                icon = "✅" if ok else "❌"
                comp_rows += f"<tr><td>{esc(label.upper())}</td><td>{esc(soll) if soll else '<span class=\'muted\'>leer</span>'}</td><td>{esc(ist) if ist else '<span class=\'muted\'>leer</span>'}</td><td>{icon}</td></tr>"
        for label, soll, ist in diffs:
            if label.lower() not in {l.lower() for l, _i, _s in MASSTEST_COMPARE}:
                comp_rows += f"<tr><td>{esc(label.upper())}</td><td>{esc(soll)}</td><td>{esc(ist)}</td><td>❌</td></tr>"
        compare_html = f"<table><tr><th>Feld</th><th>Soll</th><th>Ist</th><th></th></tr>{comp_rows}</table>"
    else:
        compare_html = "<div class='flash warn'>Für dieses Massentest-Dokument gibt es noch keine fachlichen Sollwerte.</div>"
    return ist_rows, compare_html, bool(soll_count and diffs)


def massentest_pdf_review_panel_html(row_id: str, zoom: int = 90) -> str:
    rid = quote(row_id)
    return f"""
        <div class='qc-fast-pdf'>
          <div class='qc-pdf-pan-shell' data-pdf-pan>
            <iframe loading='lazy' src='/test/massentest/pdf/{rid}#page=1&zoom={int(zoom)}'></iframe>
            <div class='qc-pdf-pan-capture' aria-label='PDF mit gedrueckter Maustaste verschieben'></div>
          </div>
          <div class='qc-pdf-pan-hint'>PDF mit gedrueckter linker Maustaste verschieben. Scrollleisten bleiben nutzbar.</div>
        </div>
    """


def render_document_review(title: str, row_id: str, right_html: str, *, subtitle: str = "", badge: str = "Dokumentenprüfung", back_html: str = "", flash: str = "", zoom: int = 90) -> str:
    subtitle_html = f"<p class='muted small'>{esc(subtitle)}</p>" if subtitle else ""
    return f"""
    {back_html}
    {flash}
    <div class='card qc-fast-card'>
      <div class='section-head'><h2>{esc(title)}</h2><span class='count-badge'>{esc(badge)}</span></div>
      {subtitle_html}
      <div class='qc-fast-review'>
        {massentest_pdf_review_panel_html(row_id, zoom)}
        <div class='qc-fast-panel'>
          {right_html}
        </div>
      </div>
    </div>
    """


@app.get("/test/massentest/result/{row_id}", response_class=HTMLResponse)
def massentest_result(row_id: str, msg: str = "") -> HTMLResponse:
    rows = massentest_read_results()
    idx, row = massentest_find_row(rows, row_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Massentest-Eintrag nicht gefunden")
    if massentest_row_status(row) == "bestanden":
        return RedirectResponse(url=f"/test/massentest/fachlich/{quote(row_id)}{('?msg=' + quote(msg)) if msg else ''}", status_code=303)
    ist_rows, compare_html, has_deviation = massentest_result_values_html(row)
    flash = f"<div class='flash'>{esc(msg)}</div>" if msg else ""
    file_name = row.get('alter_dateiname', 'Massentest-Dokument')
    task_button_text = "Aufgabe aktualisieren" if row.get("aufgabe_id") else "Aufgabe anlegen"
    deviation_actions_html = f"""
        <a class='btn2' href='/test/massentest/detail/{quote(row_id)}'>Sollwerte bearbeiten</a>
        <span class='mini-actions'>
          <form method='post' action='/test/massentest/quick-result/{quote(row_id)}' style='display:inline'><button class='btn2 success' name='action' value='ist_uebernehmen' type='submit'>Ist-Werte übernehmen</button></form>
          <form method='post' action='/test/massentest/quick-result/{quote(row_id)}' style='display:inline' data-working='Aufgabe wird angelegt/aktualisiert...'><button class='btn2 warn' name='action' value='aufgabe' type='submit'>{task_button_text}</button></form>
        </span>
    """ if has_deviation or not any(str(row.get(soll, '')).strip() for _l,_i,soll in MASSTEST_COMPARE) else ""
    if not deviation_actions_html:
        # 3.5.1: Wenn die Detailprüfung fehlerfrei ist, wird der Eintrag sofort
        # in den sauberen Zwischenstatus "fehlerfrei geprüft" gebracht.
        # Erst der grüne Button setzt danach bewusst "Test bestanden".
        try:
            soll_count_tmp, diffs_tmp = massentest_diff_details(row)
            if soll_count_tmp > 0 and not diffs_tmp and massentest_derive_workflow(row) != "TEST_BESTANDEN":
                closed_id_tmp = massentest_close_existing_task_if_clean(row, "fehlerfrei geprüft")
                row = massentest_set_workflow(row, "GEPRUEFT_OK", f"Fehlerfrei geprüft {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
                row["vergleich_ok"] = "1"
                if closed_id_tmp:
                    row["aufgabe_id"] = ""
                rows[idx] = row
                massentest_write_results(rows)
        except Exception:
            pass
        auto_pass_html = f"""<div class='flash ok'><b>🟢 Fehlerfrei geprüft</b><br>Alle prüfbaren Sollwerte entsprechen den Ist-Werten. Die endgültige Entscheidung erfolgt oben in der Prüfentscheidungsleiste.</div>"""
    else:
        auto_pass_html = ""
    pdf_button = f"<form method='post' action='/test/massentest/open-reader/{quote(row_id)}' style='display:inline'><button class='btn2' type='submit'>PDF öffnen</button></form>"
    permanent_actions_html = f"""
      <div class='massentest-decisionbar'>
        <b>Prüfentscheidung:</b>
        <form method='post' action='/test/massentest/quick-result/{quote(row_id)}' style='display:inline'><button class='btn success' name='action' value='ok' type='submit'>✓ Bestanden</button></form>
        <form method='post' action='/test/massentest/quick-result/{quote(row_id)}' style='display:inline' data-working='Test nicht bestanden wird gespeichert...'><button class='btn2 danger' name='action' value='nicht_bestanden' type='submit'>✗ Test nicht bestanden</button></form>
        {massentest_validation_action_html(row_id, row, 'fachlich')}
        <a class='btn2' href='/test/massentest/detail/{quote(row_id)}'>Sollwerte bearbeiten</a>
        <span class='muted small'>Bleibt auch nach „PDF öffnen“ sichtbar.</span>
      </div>
    """
    quality_hint_html = ""
    try:
        lieferant_empty = not str(row.get('lieferant','')).strip()
        dokumenttyp_unknown = str(row.get('dokumenttyp','')).strip().lower() in {'', 'unbekannt'}
        if lieferant_empty or dokumenttyp_unknown:
            quality_hint_html = "<div class='massentest-alert'>Hinweis: Lieferant fehlt oder Dokumenttyp ist unbekannt. Bitte PDF-Vorschau prüfen und ggf. Sollwerte bearbeiten oder Test nicht bestanden wählen.</div>"
    except Exception:
        quality_hint_html = ""
    right_html = f"""
      <div class='resultbar'>
        <a class='btn2' href='/test/massentest#mtrow-{esc(row_id)}'>← Zurück zur Übersicht</a>
        {pdf_button}
        {deviation_actions_html}
      </div>
      {permanent_actions_html}
      {quality_hint_html}
      {auto_pass_html}
      <div class='result-card'><h3>1. Erkannte Ist-Werte</h3><table>{ist_rows}</table></div>
      <div class='result-card' style='margin-top:12px'><h3>2. Soll/Ist-Prüfung</h3>{compare_html}</div>
      <div class='massentest-detail-preview-actions'><a class='btn2' target='_blank' href='/test/massentest/pdf-view/{quote(row_id)}'>Große Vorschau / Lupe</a><form method='post' action='/test/massentest/open-reader/{quote(row_id)}' style='display:inline'><button class='btn2' type='submit'>PDF im Reader öffnen</button></form></div>
      <details class='card' style='box-shadow:none;margin-top:14px'><summary><b>Massentest-Daten</b></summary><table>
        <tr><td>Alter Dateiname</td><td>{esc(row.get('alter_dateiname',''))}</td></tr>
        <tr><td>Neuer Dateiname</td><td>{esc(row.get('neuer_dateiname',''))}</td></tr>
        <tr><td>Prüfstatus</td><td>{esc(row.get('pruefstatus',''))}</td></tr>
        <tr><td>Aufgabe</td><td>{esc(row.get('aufgabe_id',''))}</td></tr>
        <tr><td>Letzter Test</td><td>{esc(row.get('letzter_test',''))}</td></tr>
      </table></details>
    """
    body = render_document_review(
        f"Testergebnis: {file_name}",
        row_id,
        right_html,
        subtitle="Ergebnis prüfen, Sollwerte bearbeiten oder Aufgabe aktualisieren. Die PDF-Vorschau bleibt links im Blick.",
        badge="Massentest",
        flash=flash,
        zoom=90,
    )
    return layout("Massentest-Testergebnis", body)


@app.post("/test/massentest/quick-result/{row_id}")
def massentest_quick_result(row_id: str, action: str = Form("ok")):
    rows = massentest_read_results()
    idx, row = massentest_find_row(rows, row_id)
    if row is None or idx is None:
        raise HTTPException(status_code=404, detail="Massentest-Eintrag nicht gefunden")
    action = (action or "").strip().lower()
    if action == "ist_uebernehmen":
        if massentest_ist_kontoauszug(row):
            row["gesamtbetrag"] = ""
            row["soll_gesamtbetrag"] = ""
        for _label, ist_key, soll_key in MASSTEST_COMPARE:
            if soll_key == "soll_neuer_dateiname":
                continue
            row[soll_key] = str(row.get(ist_key, "") or "").strip()
        row = massentest_aktualisiere_soll_dateiname(row)
        row["pruefstatus"] = "bearbeitung"
        row["letzter_test"] = f"{datetime.now().strftime('%d.%m.%Y %H:%M:%S')}: Ist-Werte als Soll übernommen"
        msg = "Ist-Werte wurden als Sollwerte übernommen. Das Dokument bleibt offen/bearbeitet. Erst „Bestanden“ schließt den technischen Status ab."
    elif action == "ist_gefuellt":
        for _label, ist_key, soll_key in MASSTEST_COMPARE:
            if soll_key == "soll_neuer_dateiname":
                continue
            val = str(row.get(ist_key, "") or "").strip()
            if val:
                row[soll_key] = val
        row = massentest_aktualisiere_soll_dateiname(row)
        if massentest_ist_kontoauszug(row):
            row["gesamtbetrag"] = ""
            row["soll_gesamtbetrag"] = ""
        row["pruefstatus"] = "bearbeitung"
        row["letzter_test"] = f"{datetime.now().strftime('%d.%m.%Y %H:%M:%S')}: gefüllte Ist-Werte als Soll übernommen"
        msg = "Gefüllte Ist-Werte wurden als Sollwerte übernommen. Das Dokument bleibt offen/bearbeitet. Erst „Bestanden“ schließt den technischen Status ab."
    elif action in {"aufgabe", "nicht_bestanden"}:
        # Aufgabe direkt aus der Testergebnis-Seite anlegen/aktualisieren, ohne zweite Folgeseite.
        # 3.6.8: Manuell "Test nicht bestanden" wird eindeutig als Abweichung geführt.
        form_values = {"notiz": row.get("notiz", "")}
        for _label, _ist_key, soll_key in MASSTEST_COMPARE:
            if soll_key == "soll_neuer_dateiname":
                continue
            form_values[soll_key] = str(row.get(soll_key, "") or "")
        row, msg = massentest_apply_review(row, "aufgabe", form_values)
        if action == "nicht_bestanden":
            row = massentest_set_workflow(row, "ABWEICHUNG", f"Manuell nicht bestanden {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
            row["pruefstatus"] = "abweichung"
            row["workflow_status"] = "ABWEICHUNG"
            row["vergleich_ok"] = "0"
            row["manuell_nicht_bestanden"] = "1"
            row["abweichungen"] = row.get("abweichungen") or "Manuell als Test nicht bestanden markiert"
            msg = "Test nicht bestanden gespeichert. Das Dokument erscheint unter Abweichung und im Projektcenter."
    else:
        if action == "ok":
            soll_count, diffs = massentest_diff_details(row)
            if soll_count > 0 and not diffs:
                closed_id = massentest_close_existing_task_if_clean(row, "Test bestanden")
                row = massentest_set_workflow(row, "TEST_BESTANDEN", f"Test bestanden {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
                row["vergleich_ok"] = "1"
                if closed_id:
                    row["aufgabe_id"] = ""
                msg = "Bestanden gespeichert. Der Eintrag wurde abgeschlossen."
            elif diffs:
                row = massentest_set_workflow(row, "ABWEICHUNG", f"Test nicht bestanden: {len(diffs)} Abweichung(en)")
                msg = "Bestanden ist nicht möglich, solange Abweichungen vorhanden sind."
            else:
                row = massentest_set_workflow(row, "ERKANNT", "Test bestanden nicht möglich: Sollwerte fehlen")
                msg = "Bestanden ist nicht möglich, weil Sollwerte fehlen."
        else:
            row["pruefstatus"] = action if action in {"ausreisser", "bearbeitung", "ignoriert"} else "ungeprueft"
            row["workflow_status"] = ""
            row["letzter_test"] = f"{datetime.now().strftime('%d.%m.%Y %H:%M:%S')}: Status {massentest_pruefstatus_label(row['pruefstatus'])}"
            msg = "Status gespeichert."
    rows[idx] = row
    massentest_write_results(rows, persist_references=action in {"ist_uebernehmen", "ist_gefuellt"})
    if action == "ok" and massentest_derive_workflow(row) == "TEST_BESTANDEN":
        anchor = massentest_next_work_anchor(rows, row_id)
        return RedirectResponse(url=f"/test/massentest?msg={quote(msg)}{anchor}", status_code=303)
    target = f"/test/massentest/result/{quote(row_id)}"
    return RedirectResponse(url=f"{target}?msg={quote(msg)}", status_code=303)



@app.get("/test/massentest/quality", response_class=HTMLResponse)
def massentest_quality_center(status: str = "offen", q: str = "") -> HTMLResponse:
    ensure_massentest_dirs()
    rows = massentest_read_results()
    vstats = massentest_validation_stats(rows)
    status_norm = (status or "offen").strip().lower()
    q_norm = (q or "").strip().lower()
    try:
        aufgaben_cache = projekt_lade_aufgaben()
    except Exception:
        aufgaben_cache = None
    filtered = []
    for r in rows:
        valid = massentest_is_fachlich_validiert(r)
        area = massentest_overview_status(r, aufgaben_cache)[3]
        if status_norm in {"offen", "nicht_validiert", "unvalidiert"} and (valid or area == "fachliche_nacharbeit"):
            continue
        if status_norm in {"validiert", "valid"} and not valid:
            continue
        if q_norm:
            hay = " ".join(str(r.get(k, "")) for k in ["alter_dateiname", "neuer_dateiname", "lieferant", "dokumenttyp", "dokumentdatum", "rechnr", "aktenzeichen", "kundennr", "gesamtbetrag", "notiz"]).lower()
            if q_norm not in hay:
                continue
        filtered.append(r)
    # Abweichungen und noch fachlich zu pruefende Dokumente zuerst, dann alphabetisch.
    filtered.sort(key=lambda r: (0 if massentest_overview_status(r, aufgaben_cache)[3] == "error" else (1 if massentest_overview_status(r, aufgaben_cache)[3] == "fachliche_nacharbeit" else 2), 0 if not massentest_is_fachlich_validiert(r) else 1, str(r.get("alter_dateiname", "")).lower()))
    cards = "".join(massentest_quality_row_card(r) for r in filtered[:300]) or "<div class='hint'>Keine Dokumente in diesem Filter.</div>"
    body = f"""
    <div class='top-actions'><a class='btn2' href='/test/massentest#qualitaetscenter'>← Zurück zum Massentest</a></div>
    <div class='card'>
      <div class='section-head'><h2>Fachliche Prüfung</h2><span class='count-badge'>Arbeitsbereich</span></div>
      <p class='muted'>PDF prüfen, Korrekturen klären und fachlich freigeben.</p>
      {f"<p class='hint small'><b>Technische Abweichungen vorhanden:</b> {vstats['active_errors']} Dokumente<br><span class='muted'>Diese können unabhängig von der fachlichen Prüfung bearbeitet werden.</span></p>" if vstats.get('active_errors',0) else ""}
      <div class='grid'>
        <a class='hint' href='/test/massentest#gruppe-technisch-bestanden-noch-fachlich-zu-pruefen' style='display:block;text-decoration:none;color:inherit'><div class='section-head'><b>Noch fachlich zu prüfen</b><span class='count-badge'>{vstats['open']}</span></div><div class='muted small'>Dokumente prüfen</div></a>
        <a class='hint' href='/test/massentest#gruppe-fachliche-nacharbeit' style='display:block;text-decoration:none;color:inherit'><div class='section-head'><b>Nachzubearbeiten</b><span class='count-badge'>{vstats.get('nacharbeit',0)}</span></div><div class='muted small'>Fachliche Nacharbeit öffnen</div></a>
        <a class='hint' href='/test/massentest#gruppe-technisch-bestanden-fachlich-validiert' style='display:block;text-decoration:none;color:inherit'><div class='section-head'><b>Fachlich validiert</b><span class='count-badge'>{vstats['valid']}</span></div><div class='muted small'>Freigegebene Dokumente anzeigen</div></a>
        <a class='hint' href='/test/massentest#gruppe-sonderfaelle' style='display:block;text-decoration:none;color:inherit'><div class='section-head'><b>Sonderfälle</b><span class='count-badge'>{vstats.get('special',0)}</span></div><div class='muted small'>Sonderfälle anzeigen</div></a>
        <a class='hint' href='/test/massentest#pruefliste' style='display:block;text-decoration:none;color:inherit'><div class='section-head'><b>Alle Dokumente</b><span class='count-badge'>{vstats['total']}</span></div><div class='muted small'>Gesamte Prüfliste öffnen</div></a>
      </div>
      <form method='get' action='/test/massentest/quality' class='toolbar'>
        <select name='status'>
          <option value='offen' {'selected' if status_norm in {'offen','nicht_validiert','unvalidiert'} else ''}>Noch fachlich zu prüfen</option>
          <option value='validiert' {'selected' if status_norm in {'validiert','valid'} else ''}>Fachlich validiert</option>
          <option value='alle' {'selected' if status_norm == 'alle' else ''}>Alle Dokumente</option>
        </select>
        <input type='text' name='q' value='{esc(q)}' placeholder='Suche ...' style='min-width:320px'>
        <button class='btn2' type='submit'>Filtern</button>
        <a class='btn2' href='/test/massentest/quality?status=offen'>Zurücksetzen</a>
      </form>
    </div>
    <div class='card'><h2>Dokumente ({len(filtered)})</h2>{cards}</div>
    """
    return layout("Dokumentenprüfung", body)


@app.post("/test/massentest/validate/{row_id}")
def massentest_validate_row(row_id: str, action: str = Form("validieren"), source: str = Form("list")):
    rows = massentest_read_results()
    idx, row = massentest_find_row(rows, row_id)
    if row is None or idx is None:
        raise HTTPException(status_code=404, detail="Massentest-Eintrag nicht gefunden")
    act = (action or "validieren").strip().lower()
    valid = act not in {"entziehen", "zurueck", "zurück", "0", "false"}
    src = (source or "list").strip().lower()
    debug_focus = False
    debug_text = " ".join(str(row.get(k, "") or "") for k in ["alter_dateiname", "pdf_datei", "lieferant", "dokumenttyp", "neuer_dateiname"]).lower()
    debug_focus = src == "fachlich" and (("maingau" in debug_text) or ("stadtwerke bochum netz" in debug_text) or ("05.01.2024" in debug_text))
    if debug_focus:
        try:
            _dbg_soll_count, _dbg_diffs = massentest_diff_details(row)
            massentest_log(
                "FACHLICH-VALIDATE-DEBUG START "
                f"row_id={row_id} action={act} source={src} valid={valid} "
                f"datei={row.get('alter_dateiname','')} "
                f"workflow={row.get('workflow_status','')} pruefstatus={row.get('pruefstatus','')} "
                f"vergleich_ok={row.get('vergleich_ok','')} fachlich_validiert={row.get('fachlich_validiert','')} "
                f"diffs={len(_dbg_diffs)} soll_count={_dbg_soll_count}"
            )
        except Exception as e:
            massentest_log(f"FACHLICH-VALIDATE-DEBUG START FEHLER row_id={row_id}: {e}")
    if src == "fachlich" and valid and str(row.get("notiz", "") or "").strip() and massentest_overview_status(row, projekt_lade_aufgaben())[3] == "fachliche_nacharbeit":
        msg = "Fachliche Validierung nicht gespeichert: Es ist noch eine Notiz vorhanden. Bitte Notiz entfernen oder bewusst Fachlich nicht korrekt bzw. Dokument ist Sonderfall wählen."
        if debug_focus:
            massentest_log(f"FACHLICH-VALIDATE-DEBUG BLOCKED row_id={row_id} grund=notiz_vorhanden ziel=/test/massentest/fachlich/{quote(row_id)}")
        return RedirectResponse(url=f"/test/massentest/fachlich/{quote(row_id)}?msg={quote(msg)}", status_code=303)
    row = massentest_set_fachlich_validiert(row, valid)
    rows[idx] = row
    massentest_write_results(rows)
    if debug_focus:
        try:
            final_rows = massentest_read_results()
            _final_idx, final_row = massentest_find_row(final_rows, row_id)
            _final_soll_count, _final_diffs = massentest_diff_details(final_row or row)
            massentest_log(
                "FACHLICH-VALIDATE-DEBUG SAVED "
                f"row_id={row_id} final_idx={_final_idx} "
                f"workflow={(final_row or row).get('workflow_status','')} "
                f"pruefstatus={(final_row or row).get('pruefstatus','')} "
                f"vergleich_ok={(final_row or row).get('vergleich_ok','')} "
                f"fachlich_validiert={(final_row or row).get('fachlich_validiert','')} "
                f"row_status={massentest_row_status(final_row or row)} "
                f"diffs={len(_final_diffs)} soll_count={_final_soll_count}"
            )
        except Exception as e:
            massentest_log(f"FACHLICH-VALIDATE-DEBUG SAVED FEHLER row_id={row_id}: {e}")
    msg = "Fachliche Validierung gespeichert." if valid else "Fachliche Validierung zurückgenommen."
    if src == "result":
        target = f"/test/massentest/result/{quote(row_id)}?msg={quote(msg)}"
    elif src == "detail":
        target = f"/test/massentest/detail/{quote(row_id)}?msg={quote(msg)}"
    elif src == "quality":
        target = f"/test/massentest/quality?msg={quote(msg)}"
    elif src == "fachlich":
        response = massentest_redirect_next_fachlich(row_id, msg)
        if debug_focus:
            massentest_log(f"FACHLICH-VALIDATE-DEBUG REDIRECT row_id={row_id} ziel={response.headers.get('location','')}")
        return response
    else:
        target = f"/test/massentest?msg={quote(msg)}#mtrow-{quote(row_id)}"
    if debug_focus:
        massentest_log(f"FACHLICH-VALIDATE-DEBUG REDIRECT row_id={row_id} ziel={target}")
    return RedirectResponse(url=target, status_code=303)


@app.post("/test/massentest/delete/{row_id}")
def massentest_delete_row(row_id: str):
    rows = massentest_read_results()
    idx, row = massentest_find_row(rows, row_id)
    if row is None or idx is None:
        raise HTTPException(status_code=404, detail="Massentest-Eintrag nicht gefunden")
    p = massentest_pdf_path(row)
    try:
        if p and p.exists():
            p.unlink()
    except Exception as e:
        massentest_log(f"LOESCH-HINWEIS {row.get('alter_dateiname','')}: {e}")
    del rows[idx]
    massentest_write_results(rows)
    massentest_log(f"GELOESCHT: {row.get('alter_dateiname','')}")
    return RedirectResponse(url=f"/test/massentest?msg={quote('Massentest-Dokument gelöscht.')}", status_code=303)


@app.get("/test/massentest/pdf-view/{row_id}", response_class=HTMLResponse)
def massentest_pdf_view(row_id: str):
    body = f"""
    <div class='top-actions'><a class='btn2' href='/test/massentest/detail/{quote(row_id)}'>← Zurück zur Prüfung</a><a class='btn2' href='/test/massentest/pdf-download/{quote(row_id)}'>PDF herunterladen</a></div>
    <div class='card'>
      <h2>PDF-Anzeige</h2>
      <p class='muted small'>Anzeige direkt über die WebUI mit neutralem Dateinamen. Falls der Browser trotzdem Acrobat startet, bitte „PDF herunterladen“ nutzen.</p>
      <iframe src='/test/massentest/pdf/{quote(row_id)}' style='width:100%;height:78vh;border:1px solid #dbe3ef;border-radius:14px;background:white'></iframe>
    </div>
    """
    return layout("Massentest PDF", body)


@app.get("/test/massentest/fachlich/{row_id}", response_class=HTMLResponse)
def massentest_fachlich_view(row_id: str, msg: str = "") -> HTMLResponse:
    rows = massentest_read_results()
    _idx, row = massentest_find_row(rows, row_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Massentest-Eintrag nicht gefunden")
    rid = quote(row_id)
    flash = f"<div class='flash success'>{esc(msg)}</div>" if msg else ""
    if massentest_derive_workflow(row) != "AUSREISSER":
        _soll_count_view, _diffs_view = massentest_diff_details(row)
        if _diffs_view and massentest_row_status(row) != "abweichung":
            row = massentest_set_workflow(row, "ABWEICHUNG", f"Soll/Ist-Prüfung: {len(_diffs_view)} Abweichung(en)")
            row["vergleich_ok"] = "0"
            if _idx is not None:
                rows[_idx] = row
                massentest_write_results(rows)
            msg2 = "Das Dokument hat inzwischen eine technische Abweichung und wurde in die Abweichungsgruppe verschoben."
            return RedirectResponse(url=f"/test/massentest?msg={quote(msg2)}#gruppe-abweichung", status_code=303)
    status = massentest_row_status(row)
    workflow_status = massentest_derive_workflow(row)
    fachlich_validiert = massentest_is_fachlich_validiert(row)
    _overview_symbol, _overview_info, _overview_class, overview_area = massentest_overview_status(row)
    is_fachliche_nacharbeit = overview_area == "fachliche_nacharbeit"
    task_id = str(row.get("aufgabe_id", "") or "").strip()
    task_status = ""
    if task_id:
        try:
            aufgaben = projekt_lade_aufgaben()
            task_idx = massentest_existing_task_index(aufgaben, row)
            if task_idx is not None:
                task_status = str(aufgaben[task_idx].get("status", "offen") or "offen").strip() or "offen"
        except Exception:
            task_status = ""
    task_display_html = ""
    if task_id:
        task_label = esc(task_id)
        task_status_label = esc(task_status or "offen")
        task_display_html = f"<p><b>Aufgabe:</b><br><a class='task-badge' href='/projekt?suche={quote(task_id)}'>{task_label}</a> · {task_status_label}</p>"
    nacharbeit_note = str(row.get("notiz", "") or "").strip()
    nacharbeit_info_html = ""
    if is_fachliche_nacharbeit:
        note_html = f"<p><b>Notiz:</b><br><span style='white-space:pre-wrap'>{esc(nacharbeit_note)}</span></p>" if nacharbeit_note else "<p><b>Notiz:</b><br><span class='muted'>Keine Notiz gespeichert.</span></p>"
        nacharbeit_info_html = f"""
            <div class='hint' style='margin-top:10px'>
              <p><b>Status:</b><br><span class='warntext'>Nachzubearbeiten</span></p>
              {task_display_html}
              {note_html}
              <p class='muted small'>Dieses Dokument ist nachzubearbeiten.</p>
            </div>
        """
    if workflow_status == "AUSREISSER":
        tech_status_html = "<span class='ok'>✓ Bestanden</span>"
        fach_status_html = "<span class='warntext'>⭐ Dokument ist Sonderfall</span>"
    elif status == "abweichung":
        tech_status_html = "<span class='bad'>✗ Abweichung</span>"
        fach_status_html = "<span class='muted'>– (noch nicht möglich)</span>"
    elif status == "bestanden":
        tech_status_html = "<span class='ok'>✓ Bestanden</span>"
        if is_fachliche_nacharbeit:
            fach_status_html = "<span class='warntext'>Nachzubearbeiten</span>"
        else:
            fach_status_html = "<span class='ok'>✓ Fachlich validiert</span>" if fachlich_validiert else "<span class='muted'>○ Noch fachlich zu prüfen</span>"
    else:
        tech_status_html = "<span class='muted'>○ Offen</span>"
        fach_status_html = "<span class='muted'>– (noch nicht möglich)</span>"
    validate_action = ""
    decision_note = ""
    decision_actions = ""
    if status == "bestanden":
        validate_action = f"""
          <form method='post' action='/test/massentest/validate/{rid}' style='display:inline' data-progress='0' data-working='Fachliche Entscheidung wird gespeichert ...' data-confirm-title='Alles fachlich korrekt?' data-confirm-message='Dieses Dokument wird als fachlich validiert markiert. Danach wird automatisch das nächste noch fachlich zu prüfende Dokument geöffnet.' data-confirm-kind='eco-modal-success' data-confirm-ok='Ja, fachlich validieren'>
            <input type='hidden' name='action' value='validieren'>
            <input type='hidden' name='source' value='fachlich'>
            <button class='btn success' type='submit'>Alles fachlich korrekt</button>
          </form>
        """
        decision_note = f"""
            {nacharbeit_info_html}
            <label class='small' style='display:block;margin-top:10px'><b>Grund / Notiz</b><br><textarea form='fachlich-entscheidung-form' name='nacharbeit_notiz' placeholder='z.B. Dateiname zu lang, falscher Lieferant, falscher Betrag ...' style='height:72px'>{esc(nacharbeit_note)}</textarea></label>
        """
        decision_actions = f"""
          <form id='fachlich-entscheidung-form' method='post' action='/test/massentest/fachlich-nicht-korrekt/{rid}' style='display:inline-flex;gap:8px;flex-wrap:wrap;align-items:center' data-progress='0' data-working='Fachliche Entscheidung wird gespeichert ...' data-confirm-title='Fachlich nicht korrekt?' data-confirm-message='Dokument als fachlich nicht korrekt markieren und als nachzubearbeiten vormerken?' data-confirm-ok='Ja, vormerken'>
            <button class='btn2 warn' type='submit'>Fachlich nicht korrekt</button>
            <button class='btn2 warn' type='submit' formaction='/test/massentest/sonderfall/{rid}' data-confirm-title='Dokument ist Sonderfall?' data-confirm-message='Dokument als Sonderfall kennzeichnen? Es wird keine normale Fehleraufgabe angelegt.' data-confirm-ok='Ja, Sonderfall markieren'>⭐ Dokument ist Sonderfall</button>
          </form>
        """
    else:
        validate_action = "<span class='muted small'>Fachliche Freigabe ist erst nach technischem Bestand möglich.</span>"
    fields = [
        ("Alter Dateiname", "alter_dateiname"),
        ("Neuer Dateiname", "neuer_dateiname"),
        ("Lieferant", "lieferant"),
        ("Dokumenttyp", "dokumenttyp"),
        ("Dokumentdatum", "dokumentdatum"),
        ("Rechnungsnummer", "rechnr"),
        ("Aktenzeichen", "aktenzeichen"),
        ("Kundennummer", "kundennr"),
        ("Auftragsnummer", "auftragnr"),
        ("Bestellnummer", "bestellnr"),
        ("Lieferscheinnummer", "lieferscheinnr"),
        ("Versicherungsnummer", "versicherungsnr"),
        ("Gesamtbetrag", "gesamtbetrag"),
    ]
    value_rows = ""
    for label, key in fields:
        value = esc(str(row.get(key, "") or "")) or "<span class='muted'>leer</span>"
        value_rows += f"<tr><th>{esc(label)}</th><td>{value}</td></tr>"
    soll_rows = ""
    for label, ist_key, soll_key in MASSTEST_COMPARE:
        ist = str(row.get(ist_key, "") or "").strip()
        soll = str(row.get(soll_key, "") or "").strip()
        if not ist and not soll:
            continue
        if soll_key == "soll_neuer_dateiname":
            marker = "<span class='muted'>technisch</span>"
        elif soll and norm_compare(ist) == norm_compare(soll):
            marker = "<span class='ok'>✓</span>"
        elif soll:
            marker = "<span class='warntext'>Abweichung</span>"
        else:
            marker = "<span class='muted'>ohne Sollwert</span>"
        soll_html = esc(soll) if soll else "<span class='muted'>leer</span>"
        ist_html = esc(ist) if ist else "<span class='muted'>leer</span>"
        soll_rows += f"<tr><th>{esc(label)}</th><td>{soll_html}</td><td>{ist_html}</td><td>{marker}</td></tr>"
    if not soll_rows:
        soll_rows = "<tr><td colspan='4'><span class='muted'>Keine Soll-/Ist-Werte vorhanden.</span></td></tr>"
    body = f"""
    <div class='top-actions'><a class='btn2' href='/test/massentest#pruefliste'>← Zurück zur Prüfliste</a></div>
    {flash}
    <div class='card qc-fast-card'>
      <div class='section-head'><h2>Fachliche Validierung</h2><span class='count-badge'>Schnellprüfung</span></div>
      <div class='qc-fast-review'>
        {massentest_pdf_review_panel_html(rid, 90)}
        <div class='qc-fast-panel'>
          <div class='hint qc-fast-decision'>
            <b>Prüfentscheidung</b><br>
            {decision_note}
            <div class='qc-fast-actions' style='margin-top:10px'>
              <div class='qc-fast-action-group'><b>Freigabe</b>{validate_action}</div>
              <div class='qc-fast-action-group'><b>Nacharbeit / Sonderfall</b>{decision_actions}</div>
              <div class='qc-fast-action-group'><b>Sollwerte</b><a class='btn2' href='/test/massentest/detail/{rid}?source=fachlich'>Sollwerte korrigieren</a></div>
            </div>
          </div>
          <div class='qc-fast-status'>
            <div class='hint'><b>Technischer Status</b><br>{tech_status_html}</div>
            <div class='hint'><b>Fachlicher Status</b><br>{fach_status_html}</div>
          </div>
          <h3>Erkannte Ist-Werte</h3>
          <table><tr><th>Feld</th><th>Erkannter Wert</th></tr>{value_rows}</table>
          <h3 style='margin-top:14px'>Soll/Ist-Prüfung</h3>
          <table><tr><th>Feld</th><th>Soll</th><th>Ist</th><th>Status</th></tr>{soll_rows}</table>
        </div>
      </div>
    </div>
    """
    return layout("Fachliche Validierung", body)


@app.post("/test/massentest/fachlich-nicht-korrekt/{row_id}")
def massentest_fachlich_nicht_korrekt(row_id: str, nacharbeit_notiz: str = Form("")):
    rows = massentest_read_results()
    idx, row = massentest_find_row(rows, row_id)
    if row is None or idx is None:
        raise HTTPException(status_code=404, detail="Massentest-Eintrag nicht gefunden")
    row["fachlich_validiert"] = "0"
    row["fachlich_validiert_am"] = ""
    row["fachlich_validiert_von"] = ""
    row["fachlich_validiert_hinweis"] = "Fachliche Prüfung nicht bestanden"
    standardgrund = "Fachliche Prüfung nicht bestanden – Sollwerte oder erkannte Werte prüfen."
    grund = str(nacharbeit_notiz or "").strip() or standardgrund
    links = [
        f"Fachliche Prüfansicht: /test/massentest/fachlich/{row_id}",
        f"Sollwerte korrigieren: /test/massentest/detail/{row_id}?source=fachlich",
    ]
    bestehende_notiz = str(row.get("notiz", "") or "").strip()
    notiz_teile = [bestehende_notiz] if bestehende_notiz else []
    hinweis = "Fachliche Prüfung nicht bestanden"
    for eintrag in [hinweis, grund, *links]:
        if eintrag and eintrag not in bestehende_notiz and eintrag not in notiz_teile:
            notiz_teile.append(eintrag)
    row["notiz"] = "\n".join(t for t in notiz_teile if t).strip()
    row, meldung = massentest_apply_review(row, "aufgabe", {"notiz": row.get("notiz", "")})
    rows[idx] = row
    massentest_write_results(rows)
    msg = f"Nachzubearbeiten gespeichert. {meldung}"
    return massentest_redirect_next_fachlich(row_id, msg)


@app.post("/test/massentest/sonderfall/{row_id}")
def massentest_sonderfall(row_id: str, nacharbeit_notiz: str = Form("")):
    rows = massentest_read_results()
    idx, row = massentest_find_row(rows, row_id)
    if row is None or idx is None:
        raise HTTPException(status_code=404, detail="Massentest-Eintrag nicht gefunden")
    standardnotiz = "Dokument als Sonderfall gekennzeichnet. Nicht als Referenz für die allgemeine Dokumentenerkennung verwenden."
    row["fachlich_validiert"] = "0"
    row["fachlich_validiert_am"] = ""
    row["fachlich_validiert_von"] = ""
    row["fachlich_validiert_hinweis"] = "Dokument ist Sonderfall"
    row, meldung = massentest_apply_review(row, "ausreisser", {"notiz": str(nacharbeit_notiz or "").strip() or standardnotiz})
    rows[idx] = row
    massentest_write_results(rows)
    msg = f"Dokument ist als Sonderfall markiert. {meldung}"
    return massentest_redirect_next_fachlich(row_id, msg)


@app.get("/test/massentest/detail/{row_id}", response_class=HTMLResponse)
def massentest_detail(row_id: str, msg: str = "", source: str = "") -> HTMLResponse:
    rows = massentest_read_results()
    idx, row = massentest_find_row(rows, row_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Massentest-Eintrag nicht gefunden")
    p = massentest_pdf_path(row)
    prev_link, next_link = massentest_next_prev_links(rows, row_id)
    pdf_link = (
        f"<form method='post' action='/test/massentest/open-reader/{quote(row_id)}' style='display:inline'><button class='btn' type='submit'>PDF im Reader öffnen</button></form> "
        f"<a class='btn2' href='/test/massentest/pdf-download/{quote(row_id)}'>PDF herunterladen</a> "
        f"<a class='btn2' target='_blank' href='/test/massentest/pdf-view/{quote(row_id)}'>PDF im Browser anzeigen</a>"
    ) if p else "<span class='bad'>PDF nicht gefunden</span>"
    flash = f"<div class='flash success'>{esc(msg)}</div>" if msg else ""
    vergleich_rows = ""
    row = massentest_aktualisiere_soll_dateiname(row)
    for label, ist_key, soll_key in MASSTEST_COMPARE:
        ist = row.get(ist_key, "")
        soll = row.get(soll_key, "")
        marker = ""
        if soll_key == "soll_neuer_dateiname":
            marker = "<span class='muted'>technisch</span>"
        elif soll and norm_compare(ist) != norm_compare(soll):
            marker = "<span class='warntext'>abweichend</span>"
        elif soll:
            marker = "<span class='ok'>ok</span>"
        if soll_key == "soll_neuer_dateiname":
            soll_cell = (
                f"<span class='folder-name'>{esc(soll) if soll else '<span class=\'muted\'>wird automatisch gebildet</span>'}</span>"
                f"<div class='muted small'>automatisch nach Dateinamen-Konfiguration, keine Handeingabe</div>"
            )
        else:
            soll_cell = f"<input type='text' name='{esc(soll_key)}' value='{esc(soll)}' placeholder='{esc(ist)}' style='width:100%'>"
        vergleich_rows += (
            f"<tr><th>{esc(label)}</th>"
            f"<td>{esc(ist) or '<span class=\'muted\'>leer</span>'}</td>"
            f"<td>{soll_cell}</td>"
            f"<td>{marker}</td></tr>"
        )
    detail_row_status = massentest_row_status(row)
    if detail_row_status == "abweichung":
        tech_status_html = "<span class='bad'>✗ Abweichung</span>"
        fach_status_html = "<span class='muted'>– (noch nicht möglich)</span>"
    elif detail_row_status == "bestanden":
        tech_status_html = "<span class='ok'>✓ Bestanden</span>"
        fach_status_html = "<span class='ok'>✓ Fachlich validiert</span>" if massentest_is_fachlich_validiert(row) else "<span class='muted'>○ Noch fachlich zu prüfen</span>"
    else:
        tech_status_html = "<span class='muted'>○ Offen</span>"
        fach_status_html = "<span class='muted'>– (noch nicht möglich)</span>"
    detail_status_html = f"""
      <div class='grid' style='grid-template-columns:1fr 1fr'>
        <div class='hint'><b>Technischer Status:</b><br>{tech_status_html}</div>
        <div class='hint'><b>Fachlicher Status:</b><br>{fach_status_html}</div>
      </div>
    """
    source_norm = (source or "").strip().lower()
    if source_norm == "fachlich" and detail_row_status == "bestanden":
        back_href = f"/test/massentest/fachlich/{quote(row_id)}"
    elif detail_row_status == "abweichung":
        back_href = "/test/massentest#gruppe-abweichung"
    elif detail_row_status == "offen":
        back_href = "/test/massentest#gruppe-offen"
    else:
        back_href = f"/test/massentest#mtrow-{quote(row_id)}"
    if source_norm == "fachlich":
        body = f"""
    <div class='top-actions'><div><b>Sollwerte bearbeiten</b></div><a class='btn2' href='{back_href}'>← Zurück zur fachlichen Prüfung</a></div>
    {flash}
    <div class='card qc-fast-card'>
      <div class='section-head'><h2>Fachliche Validierung – Sollwerte bearbeiten</h2><span class='count-badge'>Schnellprüfung</span></div>
      <div class='qc-fast-review'>
        {massentest_pdf_review_panel_html(row_id, 90)}
        <div class='qc-fast-panel'>
          <div class='qc-fast-status'>
            <div class='hint'><b>Technischer Status</b><br>{tech_status_html}</div>
            <div class='hint'><b>Fachlicher Status</b><br>{fach_status_html}</div>
          </div>
          <div class='hint small'>Sollwerte werden rechts bearbeitet. Die PDF-Vorschau bleibt links im Blick.</div>
          <form method='post' action='/test/massentest/review/{quote(row_id)}' data-working='Sollwerte für dieses Dokument werden gespeichert ...' data-progress='0'>
            <input type='hidden' name='source' value='fachlich'>
            <table class='massentest-review-table'><tr><th>Feld</th><th>Ist-Wert</th><th>Soll-Wert</th><th>Status</th></tr>{vergleich_rows}</table>
            <div style='margin-top:12px'><button class='btn2 success' name='action' value='ist_uebernehmen' type='submit'>Ist-Werte übernehmen</button> <span class='muted small'>füllt alle Sollwerte mit den aktuellen Ist-Werten</span></div>
            <p><label><b>Notiz / Abweichung</b><br><textarea name='notiz' style='height:96px'>{esc(row.get('notiz',''))}</textarea></label></p>
            <div class='toolbar'>
              <button class='btn2 success' name='action' value='nur_notiz' type='submit'>Sollwerte speichern</button>
              <button class='btn2 warn' name='action' value='ausreisser' type='submit'>⭐ Dokument ist Sonderfall</button>
              <a class='btn2' href='/test/massentest/fachlich/{quote(row_id)}' title='Zurück zur fachlichen Schnellprüfung dieses Dokuments'>Zur fachlichen Schnellprüfung</a>
            </div>
          </form>
        </div>
      </div>
    </div>
    """
        return layout("Sollwerte bearbeiten", body)
    top_actions = f"<div class='top-actions'><div><b>Massentest-Sollwerte</b></div><div>{prev_link} {next_link} <a class='btn2' href='{back_href}'>← Zurück zur Prüfliste</a></div></div>"
    right_html = f"""
      {detail_status_html}
      <div class='grid' style='grid-template-columns:1fr 1fr'>
        <div class='hint'><b>Originaldatei</b><br><span class='folder-name'>{esc(row.get('alter_dateiname',''))}</span></div>
        <div class='hint'><b>Neuer Dateiname</b><br><span class='folder-name'>{esc(row.get('neuer_dateiname',''))}</span></div>
      </div>
      <div class='hint small' style='margin-top:10px'>Prüfentscheidung und Aufgabenstatus befinden sich gesammelt unterhalb der Soll-/Ist-Werte.</div>
      <div style='margin-top:12px'>{pdf_link}</div>
      <p class='muted small'>PDF-Pfad im Massentest: <span class='folder-name'>{esc(str(p) if p else '')}</span></p>
      <h3>Soll-/Ist-Werte</h3>
      <form method='post' action='/test/massentest/review/{quote(row_id)}' data-working='Prüfentscheidung wird gespeichert...'>
        <input type='hidden' name='source' value='{esc(source_norm)}'>
        <table class='massentest-review-table'><tr><th>Feld</th><th>Ist-Wert</th><th>Soll-Wert</th><th>Status</th></tr>{vergleich_rows}</table>
        <div style='margin-top:12px'><button class='btn2 success' name='action' value='ist_uebernehmen' type='submit'>Ist-Werte übernehmen</button> <span class='muted small'>füllt alle Sollwerte mit den aktuellen Ist-Werten</span></div>
        <p><label><b>Notiz / Abweichung</b><br><textarea name='notiz' style='height:120px'>{esc(row.get('notiz',''))}</textarea></label></p>
        <div class='toolbar'>
          <button class='btn2 success' name='action' value='ok' type='submit'>✓ Bestanden</button>
          <button class='btn2 danger' name='action' value='nicht_bestanden' type='submit'>✗ Test nicht bestanden</button>
          <button class='btn2 warn' name='action' value='aufgabe' type='submit'>Aufgabe anlegen/aktualisieren</button>
          <button class='btn2' name='action' value='bearbeitung' type='submit'>In Bearbeitung</button>
          <button class='btn2' name='action' value='nur_notiz' type='submit'>Nur speichern</button>
        </div>
      </form>
      <div class='massentest-detail-preview-actions'><a class='btn2' target='_blank' href='/test/massentest/pdf-view/{quote(row_id)}'>Große Vorschau / Lupe</a><form method='post' action='/test/massentest/open-reader/{quote(row_id)}' style='display:inline'><button class='btn2' type='submit'>PDF im Reader öffnen</button></form></div>
      <div class='card small muted' style='box-shadow:none;margin-top:12px'>Lauf: {esc(row.get('lauf_id',''))} · OCR: {esc(row.get('ocr_qualitaet',''))} · Verarbeitung: {esc(row.get('status',''))} · Aufgabe: {esc(row.get('aufgabe_id',''))} · Hinweis: {esc(row.get('hinweis',''))}</div>
    """
    body = render_document_review(
        str(row.get('alter_dateiname', 'Massentest-Dokument') or 'Massentest-Dokument'),
        row_id,
        right_html,
        subtitle="PDF links, Soll-/Ist-Werte und Entscheidungen rechts.",
        badge="Massentest",
        back_html=top_actions,
        flash=flash,
        zoom=90,
    )
    return layout("Massentest-Prüfung", body)


def massentest_ist_kontoauszug(row: dict[str, str]) -> bool:
    text = " ".join(str(row.get(k, "")) for k in ["dokumenttyp", "soll_dokumenttyp", "alter_dateiname", "neuer_dateiname", "notiz"]).lower()
    return "kontoauszug" in text or "kontoausz" in text



def massentest_close_existing_task_if_clean(row: dict[str, str], reason: str = "fehlerfrei geprüft") -> str:
    """Schließt eine vorhandene Massentest-Aufgabe automatisch, wenn keine fachliche Abweichung mehr vorliegt."""
    try:
        aufgaben = projekt_lade_aufgaben()
        idx = massentest_existing_task_index(aufgaben, row)
        if idx is None:
            return ""
        aufgabe = dict(aufgaben[idx])
        aufgabe_id = str(aufgabe.get("id", ""))
        if not aufgabe_id:
            return ""
        fachliche_marker = " ".join([
            str(row.get("fachlich_validiert_hinweis", "") or ""),
            str(row.get("fachlich_status", "") or ""),
            str(row.get("fachlicher_status", "") or ""),
            str(row.get("fachstatus", "") or ""),
            str(row.get("review_status", "") or ""),
            str(row.get("pruefstatus", "") or ""),
            str(row.get("workflow_status", "") or ""),
            str(row.get("notiz", "") or ""),
            str(aufgabe.get("notiz", "") or ""),
        ]).lower().replace("_", " ")
        if (
            ("fachliche" in fachliche_marker and "nicht bestanden" in fachliche_marker)
            or "fachlich nachzuarbeiten" in fachliche_marker
            or "fachlich nachzubearbeiten" in fachliche_marker
            or "nachzuarbeiten" in fachliche_marker
            or "nachzubearbeiten" in fachliche_marker
        ):
            return ""
        if str(aufgabe.get("status", "")).lower() != "erledigt":
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            aufgabe["status"] = "erledigt"
            aufgabe["aktualisiert"] = now
            note = str(aufgabe.get("notiz", "") or "")
            aufgabe["notiz"] = (note + f"\n\n[Automatisch erledigt {now}] {reason}").strip()
            aufgaben[idx] = aufgabe
            projekt_speichere_aufgaben(aufgaben)
        return aufgabe_id
    except Exception as e:
        massentest_log(f"AUFGABE AUTO-CLOSE FEHLER: {row.get('alter_dateiname','')} / {e}")
        return ""

def massentest_task_details(row: dict[str, str]) -> str:
    details = [
        "=== MASSENTEST AUFGABE ===",
        f"Alter Dateiname: {row.get('alter_dateiname','')}",
        f"Neuer Dateiname: {row.get('neuer_dateiname','')}",
        f"PDF im Massentest: {row.get('pdf_datei') or row.get('alter_dateiname','')}",
        f"Link WebUI: /test/massentest/detail/{row.get('id','')}",
        f"Fachlich validiert: {'Ja' if massentest_is_fachlich_validiert(row) else 'Nein'}",
        "",
        "IST-WERTE:",
    ]
    for label, ist_key, _soll_key in MASSTEST_COMPARE:
        details.append(f"{label.upper()}={row.get(ist_key,'')}")
    details += ["", "SOLL-WERTE:"]
    for label, _ist_key, soll_key in MASSTEST_COMPARE:
        details.append(f"{label.upper()}={row.get(soll_key,'')}")
    details += ["", "Notiz / Abweichung:", row.get("notiz", ""), "=== ENDE ==="]
    return "\n".join(details).strip()


def _mt_norm_task_text(value: object) -> str:
    """Robuste Normalisierung für Massentest-Aufgabenabgleich."""
    t = str(value or "").lower()
    t = re.sub(r"[^a-z0-9äöüß]+", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def massentest_existing_task_index(aufgaben: list[dict], row: dict[str, str]) -> int | None:
    """Findet eine bereits vorhandene Massentest-Aufgabe möglichst zuverlässig.

    Wichtig: Aufgaben dürfen beim erneuten Klick nicht doppelt entstehen.
    Wir suchen daher nicht nur nach aufgabe_id, sondern auch nach Massentest-ID,
    WebUI-Link, Originaldateiname und PDF-Dateiname in Titel/Quelle/Notiz.
    """
    row_id = str(row.get("id", "")).strip()
    pdf_name = str(row.get("alter_dateiname", "")).strip()
    pdf_file = str(row.get("pdf_datei", "")).strip()
    task_id = str(row.get("aufgabe_id", "")).strip()

    raw_needles = []
    if row_id:
        raw_needles += [row_id, f"/test/massentest/detail/{row_id}", f"/test/massentest/result/{row_id}"]
    for name in [pdf_name, pdf_file]:
        if name:
            raw_needles += [name, Path(name).name, f"Massentest {name}"]
    raw_needles = [n for n in dict.fromkeys(raw_needles) if n]
    norm_needles = [_mt_norm_task_text(n) for n in raw_needles if _mt_norm_task_text(n)]

    for i, a in enumerate(aufgaben):
        a_id = str(a.get("id", "")).strip()
        if task_id and a_id == task_id:
            return i

    # Zuerst Massentest-Aufgaben bevorzugen
    preferred = []
    others = []
    for i, a in enumerate(aufgaben):
        if str(a.get("bereich", "")).strip().lower() == "massentest" or "massentest" in str(a.get("quelle", "")).lower():
            preferred.append((i, a))
        else:
            others.append((i, a))

    for i, a in preferred + others:
        titel = str(a.get("titel", ""))
        notiz = str(a.get("notiz", ""))
        quelle = str(a.get("quelle", ""))
        hay_raw = "\n".join([titel, notiz, quelle])
        hay_norm = _mt_norm_task_text(hay_raw)
        if any(n and n in hay_raw for n in raw_needles):
            return i
        if any(n and n in hay_norm for n in norm_needles):
            return i
    return None

def massentest_sync_task_id_to_results(row: dict[str, str], aufgabe_id: str) -> None:
    """Speichert die Aufgaben-ID auch in der Ergebnisliste, damit spätere Klicks aktualisieren."""
    try:
        rows = massentest_read_results()
        rid = str(row.get("id", ""))
        pdf_name = str(row.get("alter_dateiname", ""))
        changed = False
        for r in rows:
            if (rid and str(r.get("id", "")) == rid) or (pdf_name and str(r.get("alter_dateiname", "")) == pdf_name):
                r["aufgabe_id"] = aufgabe_id
                r["pruefstatus"] = "aufgabe"
                r["workflow_status"] = "AUFGABE"
                changed = True
        if changed:
            massentest_write_results(rows)
    except Exception:
        pass


def massentest_apply_review(row: dict[str, str], action: str, form_values: dict[str, str]) -> tuple[dict[str, str], str]:
    action = (action or "nur_notiz").strip().lower()
    row["notiz"] = form_values.get("notiz", "").strip()
    if massentest_ist_kontoauszug(row):
        row["gesamtbetrag"] = ""
        row["soll_gesamtbetrag"] = ""
        if "Kontoauszug" in str(row.get("dokumenttyp", "")) and "Gesamtbetrag" not in str(row.get("hinweis", "")):
            row["hinweis"] = ((row.get("hinweis", "") + " ").strip() + "Gesamtbetrag bei Kontoauszügen entfernt.").strip()
    if action == "ist_uebernehmen":
        for _label, ist_key, soll_key in MASSTEST_COMPARE:
            if soll_key == "soll_neuer_dateiname":
                continue
            row[soll_key] = str(row.get(ist_key, "") or "").strip()
        row = massentest_aktualisiere_soll_dateiname(row)
        row["pruefstatus"] = "bearbeitung"
        return row, "Ist-Werte wurden als Sollwerte übernommen. Der Soll-Dateiname wurde automatisch nach Konfiguration gebildet. Das Dokument bleibt offen/bearbeitet."
    if action == "neu_erkennen":
        row, meldung = massentest_reprocess_row(row)
        row["pruefstatus"] = "bearbeitung"
        return row, meldung
    for _label, _ist_key, soll_key in MASSTEST_COMPARE:
        if soll_key == "soll_neuer_dateiname":
            continue
        if soll_key in form_values:
            row[soll_key] = form_values.get(soll_key, "").strip()
    row = massentest_aktualisiere_soll_dateiname(row)
    if action in {"ok", "ausreisser", "ignoriert", "bearbeitung"}:
        if action == "ok":
            soll_count, diffs = massentest_diff_details(row)
            if soll_count > 0 and not diffs:
                closed_id = massentest_close_existing_task_if_clean(row, "Test bestanden")
                row = massentest_set_workflow(row, "TEST_BESTANDEN", f"Test bestanden {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
                row["vergleich_ok"] = "1"
                row["abweichungen"] = ""
                if closed_id:
                    row["aufgabe_id"] = ""
                    row["hinweis"] = ((row.get("hinweis", "") + " ").strip() + f"Aufgabe {closed_id} automatisch erledigt.").strip()
                massentest_log(f"PRUEFUNG TEST_BESTANDEN: {row.get('alter_dateiname','')}")
                return row, "Test bestanden gespeichert. Aufgabe wurde erledigt und der Eintrag abgeschlossen."
            if diffs:
                row = massentest_set_workflow(row, "ABWEICHUNG", f"Test nicht bestanden: {len(diffs)} Abweichung(en)")
                massentest_log(f"PRUEFUNG ABWEICHUNG: {row.get('alter_dateiname','')}")
                return row, "Bestanden ist nicht möglich, solange Abweichungen vorhanden sind."
            row = massentest_set_workflow(row, "ERKANNT", "Test bestanden nicht möglich: Sollwerte fehlen")
            return row, "Bestanden ist nicht möglich, weil Sollwerte fehlen."
        if action == "bearbeitung":
            row = massentest_set_workflow(row, "REFERENZ", f"Bearbeitung {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
        elif action == "ausreisser":
            row = massentest_set_workflow(row, "AUSREISSER", f"Sonderfall markiert {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
        elif action == "ignoriert":
            row = massentest_set_workflow(row, "IGNORIERT", f"Ignoriert {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
        massentest_log(f"PRUEFUNG {action}: {row.get('alter_dateiname','')}")
        return row, "Bewertung wurde gespeichert."
    if action in {"aufgabe", "nicht_bestanden"}:
        aufgaben = projekt_lade_aufgaben()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        details = massentest_task_details(row)
        existing_idx = massentest_existing_task_index(aufgaben, row)
        if existing_idx is not None:
            aufgabe = dict(aufgaben[existing_idx])
            aufgabe_id = str(aufgabe.get("id", "")) or projekt_naechste_id(aufgaben)
            aufgabe.update({
                "id": aufgabe_id,
                "titel": f"Massentest prüfen: {row.get('alter_dateiname','PDF')}",
                "bereich": "Massentest",
                "status": "offen" if aufgabe.get("status") == "erledigt" else aufgabe.get("status", "offen"),
                "prioritaet": aufgabe.get("prioritaet", "mittel") or "mittel",
                "quelle": f"Massentest {row.get('alter_dateiname','')}",
                "notiz": details,
                "aktualisiert": now,
            })
            if not aufgabe.get("erstellt"):
                aufgabe["erstellt"] = now
            aufgaben[existing_idx] = aufgabe
            meldung = f"Aufgabe {aufgabe_id} wurde aktualisiert."
            log_action = "AKTUALISIERT"
        else:
            aufgabe_id = projekt_naechste_id(aufgaben)
            aufgaben.append({
                "id": aufgabe_id,
                "titel": f"Massentest prüfen: {row.get('alter_dateiname','PDF')}",
                "bereich": "Massentest",
                "status": "offen",
                "prioritaet": "mittel",
                "quelle": f"Massentest {row.get('alter_dateiname','')}",
                "notiz": details,
                "erstellt": now,
                "aktualisiert": now,
            })
            meldung = f"Aufgabe {aufgabe_id} wurde angelegt."
            log_action = "ANGELEGT"
        projekt_speichere_aufgaben(aufgaben)
        if action == "nicht_bestanden":
            row = massentest_set_workflow(row, "ABWEICHUNG", f"Manuell nicht bestanden {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
            row["pruefstatus"] = "abweichung"
            row["workflow_status"] = "ABWEICHUNG"
            row["vergleich_ok"] = "0"
            row["manuell_nicht_bestanden"] = "1"
            row["abweichungen"] = row.get("abweichungen") or "Manuell als Test nicht bestanden markiert"
            meldung = f"Test nicht bestanden gespeichert. Aufgabe {aufgabe_id} ist offen und der Eintrag wird unter Abweichung geführt."
        else:
            row["pruefstatus"] = "aufgabe"
            row["workflow_status"] = "AUFGABE"
        row["aufgabe_id"] = aufgabe_id
        massentest_sync_task_id_to_results(row, aufgabe_id)
        massentest_log(f"AUFGABE {log_action} {aufgabe_id}: {row.get('alter_dateiname','')}")
        return row, meldung
    return row, "Sollwerte für dieses Dokument gespeichert."


@app.post("/test/massentest/bulk-istwerte")
def massentest_bulk_istwerte(mode: str = Form("open_all")):
    """Schritt 2: Ist-Werte als Referenz/Sollwerte übernehmen."""
    rows = massentest_read_results()
    total = len(rows)
    massentest_progress_start("Neue Referenz übernehmen", total, "Referenzübernahme startet")
    changed = skipped = 0
    stamp = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
    for i, row in enumerate(rows):
        name = row.get("alter_dateiname", "") or row.get("pdf_datei", "")
        massentest_progress_write("Neue Referenz übernehmen", i + 1, total, name, "running", "Ist-Werte werden als Sollwerte gespeichert")
        ws = massentest_derive_workflow(row)
        if ws in {"TEST_BESTANDEN", "AUSREISSER", "IGNORIERT", "AUFGABE"} or str(row.get("status", "OK")).strip().upper() == "FEHLER":
            skipped += 1
            rows[i] = row
            continue
        if massentest_ist_kontoauszug(row):
            row["gesamtbetrag"] = ""
            row["soll_gesamtbetrag"] = ""
        for _label, ist_key, soll_key in MASSTEST_COMPARE:
            if soll_key == "soll_neuer_dateiname":
                continue
            row[soll_key] = str(row.get(ist_key, "") or "").strip()
        row = massentest_aktualisiere_soll_dateiname(row)
        row = massentest_set_workflow(row, "REFERENZ", f"Referenz {stamp}: Ist-Werte als Sollwerte übernommen")
        row["vergleich_ok"] = ""
        row["abweichungen"] = ""
        rows[i] = row
        changed += 1
    massentest_write_results(rows, persist_references=True)
    massentest_progress_finish("Neue Referenz übernehmen", total, f"Referenzübernahme fertig: {changed} aktualisiert")
    msg = f"{changed} Dokument(e): Ist-Werte wurden als Referenz/Sollwerte gespeichert. Soll-Dateinamen wurden automatisch gebildet. Es wurde nichts geprüft und nichts als bestanden markiert."
    if skipped:
        msg += f" {skipped} abgeschlossene/Aufgaben/Fehler wurden übersprungen."
    return RedirectResponse(url=f"/test/massentest?msg={quote(msg)}", status_code=303)


def massentest_next_work_anchor(rows: list[dict[str, str]], current_id: str) -> str:
    """Zielanker nach Abschluss: exakt im Arbeitsbereich bleiben.

    Nach "Test bestanden" soll nicht in den Bereich "Test bestanden" gesprungen
    werden. Die erledigte Karte verschwindet, die naechste noch bearbeitbare Karte
    rueckt an ihre Stelle. Genau diese Karte wird als Zielanker verwendet.
    """
    def is_work_item(r: dict[str, str]) -> bool:
        try:
            if str(r.get("status", "OK")).strip().upper() == "FEHLER":
                return True
            wf = massentest_derive_workflow(r)
            # Abgeschlossene oder bewusst ausgeblendete Bereiche nie als Ruecksprungziel.
            if wf in {"TEST_BESTANDEN", "AUSREISSER", "IGNORIERT"}:
                return False
            # Alles andere ist im Prueffluss noch relevant: Abweichung, Aufgabe,
            # fehlerfrei geprueft, offene Referenz, fehlende Sollwerte.
            return True
        except Exception:
            return False

    try:
        current_id = str(current_id or "")
        display_rows = list(reversed(rows[-500:]))
        ids = [str(r.get("id", "")) for r in display_rows]
        start = ids.index(current_id) if current_id in ids else -1
        # Erst unterhalb der gerade erledigten Karte suchen. Dadurch bleibt der
        # sichtbare Bearbeitungsbereich praktisch an derselben Stelle.
        for r in display_rows[start + 1:]:
            if is_work_item(r):
                rid = quote(str(r.get("id", "")))
                return f"#mtrow-{rid}" if rid else "#pruefliste"
        # Falls darunter nichts mehr offen ist, oberhalb weitermachen.
        for r in display_rows[:max(0, start)]:
            if is_work_item(r):
                rid = quote(str(r.get("id", "")))
                return f"#mtrow-{rid}" if rid else "#pruefliste"
    except Exception:
        pass
    return "#pruefliste"


def massentest_redirect_next_fachlich(row_id: str, msg: str) -> RedirectResponse:
    try:
        aufgaben_cache = projekt_lade_aufgaben()
    except Exception:
        aufgaben_cache = None
    queue_rows = massentest_read_results()
    queue_idx, _queue_row = massentest_find_row(queue_rows, row_id)
    if queue_idx is None:
        queue_idx = -1
    debug_focus = False
    if _queue_row:
        debug_text = " ".join(str(_queue_row.get(k, "") or "") for k in ["alter_dateiname", "pdf_datei", "lieferant", "dokumenttyp", "neuer_dateiname"]).lower()
        debug_focus = ("maingau" in debug_text) or ("stadtwerke bochum netz" in debug_text) or ("05.01.2024" in debug_text)
    if debug_focus:
        try:
            debug_soll_count, debug_diffs = massentest_diff_details(_queue_row or {})
            debug_overview = massentest_overview_status(_queue_row or {}, aufgaben_cache)[3] if _queue_row else "missing"
            massentest_log(
                "FACHLICH-REDIRECT-DEBUG START "
                f"row_id={row_id} queue_idx={queue_idx} "
                f"datei={(_queue_row or {}).get('alter_dateiname','')} "
                f"workflow={(_queue_row or {}).get('workflow_status','')} "
                f"pruefstatus={(_queue_row or {}).get('pruefstatus','')} "
                f"vergleich_ok={(_queue_row or {}).get('vergleich_ok','')} "
                f"diffs={len(debug_diffs)} soll_count={debug_soll_count} "
                f"row_status={massentest_row_status(_queue_row or {})} overview={debug_overview} "
                f"fachlich_validiert={(_queue_row or {}).get('fachlich_validiert','')}"
            )
        except Exception as e:
            massentest_log(f"FACHLICH-REDIRECT-DEBUG START FEHLER row_id={row_id}: {e}")
    current_keys = set()
    if _queue_row:
        for key in ["id", "alter_dateiname", "pdf_datei", "neuer_dateiname"]:
            value = str(_queue_row.get(key, "") or "").strip().lower()
            if value:
                current_keys.add(value)
    ordered = queue_rows[queue_idx + 1:] + queue_rows[:max(0, queue_idx)]
    for candidate in ordered:
        cid = str(candidate.get("id", "") or "")
        if not cid or cid == str(row_id):
            if debug_focus:
                massentest_log(f"FACHLICH-REDIRECT-DEBUG SKIP same-id cid={cid} datei={candidate.get('alter_dateiname','')}")
            continue
        candidate_keys = {
            str(candidate.get(key, "") or "").strip().lower()
            for key in ["id", "alter_dateiname", "pdf_datei", "neuer_dateiname"]
            if str(candidate.get(key, "") or "").strip()
        }
        if current_keys and current_keys.intersection(candidate_keys):
            if debug_focus:
                massentest_log(
                    "FACHLICH-REDIRECT-DEBUG SKIP same-key "
                    f"cid={cid} datei={candidate.get('alter_dateiname','')} "
                    f"keys={sorted(current_keys.intersection(candidate_keys))}"
                )
            continue
        candidate_status = massentest_row_status(candidate)
        candidate_valid = massentest_is_fachlich_validiert(candidate)
        candidate_overview = massentest_overview_status(candidate, aufgaben_cache)[3]
        if debug_focus:
            try:
                _candidate_soll_count, _candidate_diffs = massentest_diff_details(candidate)
                massentest_log(
                    "FACHLICH-REDIRECT-DEBUG CANDIDATE "
                    f"cid={cid} datei={candidate.get('alter_dateiname','')} "
                    f"workflow={candidate.get('workflow_status','')} pruefstatus={candidate.get('pruefstatus','')} "
                    f"vergleich_ok={candidate.get('vergleich_ok','')} diffs={len(_candidate_diffs)} "
                    f"row_status={candidate_status} overview={candidate_overview} "
                    f"fachlich_validiert={candidate.get('fachlich_validiert','')}"
                )
            except Exception as e:
                massentest_log(f"FACHLICH-REDIRECT-DEBUG CANDIDATE FEHLER cid={cid}: {e}")
        if candidate_status == "bestanden" and not candidate_valid and candidate_overview == "success_pending":
            if debug_focus:
                massentest_log(
                    "FACHLICH-REDIRECT-DEBUG SELECT "
                    f"cid={cid} datei={candidate.get('alter_dateiname','')} "
                    f"ziel=/test/massentest/fachlich/{quote(cid)}"
                )
            return RedirectResponse(url=f"/test/massentest/fachlich/{quote(cid)}?msg={quote(msg)}", status_code=303)
    if debug_focus:
        massentest_log(
            "FACHLICH-REDIRECT-DEBUG FALLBACK "
            f"row_id={row_id} ziel=/test/massentest#gruppe-technisch-bestanden-noch-fachlich-zu-pruefen"
        )
    return RedirectResponse(url=f"/test/massentest?msg={quote(msg)}#gruppe-technisch-bestanden-noch-fachlich-zu-pruefen", status_code=303)


@app.post("/test/massentest/quick/{row_id}")
def massentest_quick(row_id: str, action: str = Form("ok")):
    rows = massentest_read_results()
    idx, row = massentest_find_row(rows, row_id)
    if row is None or idx is None:
        raise HTTPException(status_code=404, detail="Massentest-Eintrag nicht gefunden")
    action = (action or "").strip().lower()
    if action == "ist_uebernehmen":
        if massentest_ist_kontoauszug(row):
            row["gesamtbetrag"] = ""
            row["soll_gesamtbetrag"] = ""
        for _label, ist_key, soll_key in MASSTEST_COMPARE:
            if soll_key == "soll_neuer_dateiname":
                continue
            row[soll_key] = str(row.get(ist_key, "") or "").strip()
        row = massentest_aktualisiere_soll_dateiname(row)
        row["pruefstatus"] = "bearbeitung"
        row["letzter_test"] = f"{datetime.now().strftime('%d.%m.%Y %H:%M:%S')}: Ist-Werte als Soll übernommen"
        msg = "Ist-Werte wurden als Sollwerte übernommen. Das Dokument bleibt offen/bearbeitet. Erst „Bestanden“ schließt den technischen Status ab."
    elif action == "ist_gefuellt":
        for _label, ist_key, soll_key in MASSTEST_COMPARE:
            if soll_key == "soll_neuer_dateiname":
                continue
            val = str(row.get(ist_key, "") or "").strip()
            if val:
                row[soll_key] = val
        row = massentest_aktualisiere_soll_dateiname(row)
        if massentest_ist_kontoauszug(row):
            row["gesamtbetrag"] = ""
            row["soll_gesamtbetrag"] = ""
        row["pruefstatus"] = "bearbeitung"
        row["letzter_test"] = f"{datetime.now().strftime('%d.%m.%Y %H:%M:%S')}: gefüllte Ist-Werte als Soll übernommen"
        msg = "Gefüllte Ist-Werte wurden als Sollwerte übernommen. Das Dokument bleibt offen/bearbeitet. Erst „Bestanden“ schließt den technischen Status ab."
    else:
        if action == "ok":
            soll_count, diffs = massentest_diff_details(row)
            if soll_count > 0 and not diffs:
                closed_id = massentest_close_existing_task_if_clean(row, "Test bestanden")
                row = massentest_set_workflow(row, "TEST_BESTANDEN", f"Test bestanden {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
                row["vergleich_ok"] = "1"
                if closed_id:
                    row["aufgabe_id"] = ""
                msg = "Bestanden gespeichert. Der Eintrag wurde abgeschlossen."
            elif diffs:
                row = massentest_set_workflow(row, "ABWEICHUNG", f"Test nicht bestanden: {len(diffs)} Abweichung(en)")
                msg = "Bestanden ist nicht möglich, solange Abweichungen vorhanden sind."
            else:
                row = massentest_set_workflow(row, "ERKANNT", "Test bestanden nicht möglich: Sollwerte fehlen")
                msg = "Bestanden ist nicht möglich, weil Sollwerte fehlen."
        else:
            row["pruefstatus"] = action if action in {"ausreisser", "bearbeitung", "ignoriert"} else "ungeprueft"
            row["workflow_status"] = ""
            row["letzter_test"] = f"{datetime.now().strftime('%d.%m.%Y %H:%M:%S')}: Status {massentest_pruefstatus_label(row['pruefstatus'])}"
            msg = "Status gespeichert."
    rows[idx] = row
    massentest_write_results(rows, persist_references=action in {"ist_uebernehmen", "ist_gefuellt"})
    anchor = massentest_next_work_anchor(rows, row_id) if action == "ok" and massentest_derive_workflow(row) == "TEST_BESTANDEN" else f"#mtrow-{quote(row_id)}"
    return RedirectResponse(url=f"/test/massentest?msg={quote(msg)}{anchor}", status_code=303)


@app.post("/test/massentest/review/{row_id}")
def massentest_review(
    row_id: str,
    action: str = Form("nur_notiz"),
    notiz: str = Form(""),
    soll_neuer_dateiname: str = Form(""),
    soll_lieferant: str = Form(""),
    soll_dokumenttyp: str = Form(""),
    soll_dokumentdatum: str = Form(""),
    soll_rechnr: str = Form(""),
    soll_aktenzeichen: str = Form(""),
    soll_kundennr: str = Form(""),
    soll_auftragnr: str = Form(""),
    soll_bestellnr: str = Form(""),
    soll_lieferscheinnr: str = Form(""),
    soll_versicherungsnr: str = Form(""),
    soll_gesamtbetrag: str = Form(""),
    source: str = Form(""),
):
    rows = massentest_read_results()
    idx, row = massentest_find_row(rows, row_id)
    if row is None or idx is None:
        raise HTTPException(status_code=404, detail="Massentest-Eintrag nicht gefunden")
    if (source or "").strip().lower() == "fachlich" and (action or "").strip().lower() == "ausreisser" and not str(notiz or "").strip():
        notiz = "Dokument als Sonderfall gekennzeichnet. Nicht als Referenz für die allgemeine Dokumentenerkennung verwenden."
    form_values = {
        "notiz": notiz,
        # Soll-Dateiname wird automatisch aus den Sollwerten nach dateiname_konfiguration.txt gebildet.
        "soll_lieferant": soll_lieferant,
        "soll_dokumenttyp": soll_dokumenttyp,
        "soll_dokumentdatum": soll_dokumentdatum,
        "soll_rechnr": soll_rechnr,
        "soll_aktenzeichen": soll_aktenzeichen,
        "soll_kundennr": soll_kundennr,
        "soll_auftragnr": soll_auftragnr,
        "soll_bestellnr": soll_bestellnr,
        "soll_lieferscheinnr": soll_lieferscheinnr,
        "soll_versicherungsnr": soll_versicherungsnr,
        "soll_gesamtbetrag": soll_gesamtbetrag,
    }
    row, meldung = massentest_apply_review(row, action, form_values)
    if (source or "").strip().lower() == "fachlich" and (action or "").strip().lower() == "nur_notiz" and str(notiz or "").strip():
        soll_count_note, diffs_note = massentest_diff_details(row)
        if diffs_note:
            row = massentest_set_workflow(row, "ABWEICHUNG", f"Sollwerte korrigiert: {len(diffs_note)} Abweichung(en)")
            row["vergleich_ok"] = "0"
            row["manuell_nicht_bestanden"] = "1"
            row["abweichungen"] = "; ".join(f"{label}: Soll={soll} / Ist={ist}" for label, soll, ist in diffs_note)
            rows[idx] = row
            massentest_write_results(rows, persist_references=True)
            final_rows = massentest_read_results()
            _final_idx, final_row = massentest_find_row(final_rows, row_id)
            massentest_log(f"FACHLICH-SAVE row_id={row_id} datei={row.get('alter_dateiname','')} diffs={len(diffs_note)} workflow={row.get('workflow_status','')} pruefstatus={row.get('pruefstatus','')} final_status={massentest_row_status(final_row or row)}")
            return massentest_redirect_next_fachlich(row_id, "Sollwerte für dieses Dokument gespeichert. Das Dokument hat eine technische Abweichung.")
        if soll_count_note > 0:
            row = massentest_set_workflow(row, "TEST_BESTANDEN", f"Sollwerte korrigiert: Test bestanden {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
            row["vergleich_ok"] = "1"
            row["manuell_nicht_bestanden"] = ""
            row["abweichungen"] = ""
        rows[idx] = row
        massentest_write_results(rows, persist_references=True)
        hinweis_msg = "Sollwerte für dieses Dokument gespeichert. Notiz ist vorhanden: Bitte bewusst Fachlich nicht korrekt, Dokument ist Sonderfall oder Notiz entfernen und fachlich validieren."
        return massentest_redirect_next_fachlich(row_id, hinweis_msg)
    if (source or "").strip().lower() == "fachlich" and (action or "").strip().lower() == "ausreisser":
        row["fachlich_validiert"] = "0"
        row["fachlich_validiert_am"] = ""
        row["fachlich_validiert_von"] = ""
        row["fachlich_validiert_hinweis"] = "Dokument ist Sonderfall"
    if (source or "").strip().lower() == "fachlich" and (action or "").strip().lower() in {"nur_notiz", "ist_uebernehmen", "bearbeitung"}:
        soll_count_tmp, diffs_tmp = massentest_diff_details(row)
        if diffs_tmp:
            row = massentest_set_workflow(row, "ABWEICHUNG", f"Sollwerte korrigiert: {len(diffs_tmp)} Abweichung(en)")
            row["vergleich_ok"] = "0"
            row["manuell_nicht_bestanden"] = "1"
            row["abweichungen"] = "; ".join(f"{label}: Soll={soll} / Ist={ist}" for label, soll, ist in diffs_tmp)
        elif soll_count_tmp > 0:
            row = massentest_set_workflow(row, "TEST_BESTANDEN", f"Sollwerte korrigiert: Test bestanden {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
            row["vergleich_ok"] = "1"
            row["manuell_nicht_bestanden"] = ""
            row["abweichungen"] = ""
    rows[idx] = row
    massentest_write_results(rows, persist_references=True)
    if (source or "").strip().lower() == "fachlich":
        final_rows = massentest_read_results()
        _final_idx, final_row = massentest_find_row(final_rows, row_id)
        try:
            _debug_soll_count, _debug_diffs = massentest_diff_details(final_row or row)
        except Exception:
            _debug_diffs = []
        massentest_log(f"FACHLICH-SAVE row_id={row_id} datei={row.get('alter_dateiname','')} diffs={len(_debug_diffs)} workflow={row.get('workflow_status','')} pruefstatus={row.get('pruefstatus','')} final_status={massentest_row_status(final_row or row)}")
        if massentest_derive_workflow(row) == "AUSREISSER":
            return massentest_redirect_next_fachlich(row_id, meldung)
        row_status_after = massentest_row_status(row)
        if row_status_after == "bestanden":
            return massentest_redirect_next_fachlich(row_id, meldung)
        if row_status_after == "abweichung":
            return massentest_redirect_next_fachlich(row_id, meldung)
        return massentest_redirect_next_fachlich(row_id, meldung)
    if (action or "").strip().lower() == "ok" and massentest_derive_workflow(row) == "TEST_BESTANDEN":
        anchor = massentest_next_work_anchor(rows, row_id)
        return RedirectResponse(url=f"/test/massentest?msg={quote(meldung)}{anchor}", status_code=303)
    return RedirectResponse(url=f"/test/massentest/detail/{quote(row_id)}?msg={quote(meldung)}", status_code=303)

def render_test_overview_rows(pdfs: list[Path], only_status: set[str] | None = None) -> str:
    rows = ""
    for p in pdfs:
        try:
            size_kb = max(1, int(p.stat().st_size / 1024))
            mtime = datetime.fromtimestamp(p.stat().st_mtime).strftime("%d.%m.%Y %H:%M:%S")
        except Exception:
            size_kb = 0
            mtime = ""
        exp = expected_path_for(p.name)
        has_expected = exp.exists()
        exp_status = "✓ vorhanden" if has_expected else "? fehlt"
        symbol, status_info, row_class, status = test_status_display(p.name, has_expected)
        if only_status is not None and status not in only_status:
            continue
        rows += f"""
        <tr class='{row_class}'>
          <td><span class='status-symbol'>{symbol}</span> <span class='folder-name'>{esc(p.name)}</span></td>
          <td>{size_kb} KB</td>
          <td>{esc(mtime)}</td>
          <td>{esc(exp_status)}</td>
          <td>{esc(status_info)}</td>
          <td style='white-space:nowrap'>
            <form method='post' action='/test/run' style='display:inline'><input type='hidden' name='filename' value='{esc(p.name)}'><button class='btn2' type='submit'>Dokument prüfen</button></form> <a class='btn2' href='/test/open-pdf?filename={esc(p.name)}' target='_blank' rel='noopener'>PDF öffnen</a>
            <a class='btn2' href='/test/expected?filename={esc(p.name)}'>Sollwerte</a>
            <form method='post' action='/test/expected/from-actual' style='display:inline'><input type='hidden' name='filename' value='{esc(p.name)}'><input type='hidden' name='overwrite' value='1'><input type='hidden' name='filled_only' value='0'><button class='btn2 success' type='submit'>Ist-Werte übernehmen</button></form>
            <form method='post' action='/test/mark-passed' style='display:inline' data-confirm-title='Test bestanden markieren?' data-confirm-message='Dieses Dokument wird mit den aktuell gespeicherten Sollwerten als Referenz bestanden markiert. Bei identischen Ist-/Sollwerten passiert das automatisch.' data-confirm-details='Wichtig: Die Ist-Werte werden dabei nicht automatisch übernommen. Wenn andere Referenzwerte gelten sollen, zuerst Sollwerte oder Ist→Soll.' data-confirm-kind='eco-modal-success' data-confirm-ok='Ja, Test bestanden'><input type='hidden' name='filename' value='{esc(p.name)}'><button class='btn2 success' type='submit'><span class='btn-stack'>✓ Test bestanden<span class='btn-sub'>mit Sollwerten</span></span></button></form>
            <form method='post' action='/test/delete' style='display:inline' data-confirm-title='Testdokument löschen?' data-confirm-message='Test-PDF und zugehörige Sollwerte wirklich löschen?' data-confirm-details='Diese Aktion entfernt das Testdokument aus dem Testcenter.' data-confirm-kind='eco-modal-danger' data-confirm-ok='Ja, löschen'><input type='hidden' name='filename' value='{esc(p.name)}'><button class='btn2 danger' type='submit'>Löschen</button></form>
          </td>
        </tr>"""
    return rows or "<tr><td colspan='6' class='muted'>Keine Dokumente in diesem Bereich.</td></tr>"


def render_project_hint_for_testcenter() -> str:
    try:
        alle = projekt_lade_aufgaben()
        stats = projekt_statistik()
        aktive = projekt_aktive_sichtbare_aufgaben(alle)
        offene_regression = [a for a in aktive if a.get('bereich') == 'Regressionstest']
        return f"""
        <div class='metric'>
          <div class='label'>Projektcenter</div>
          <div class='num'>{stats.get('offen', 0) + stats.get('in_arbeit', 0)}</div>
          <div class='muted small'>offen/in Arbeit · Regression: {len(offene_regression)}</div>
          <p><a class='btn2' href='/projekt?status=aktiv'>Offene Aufgaben öffnen</a> <a class='btn2' href='/projekt?status=alle'>Alle Aufgaben</a></p>
        </div>"""
    except Exception:
        return ""


@app.get("/test", response_class=HTMLResponse)
def testcenter_overview() -> HTMLResponse:
    ensure_dirs()
    stats = regression_stats()
    mt_rows = massentest_read_results()
    mt_total, mt_summary = massentest_compact_status_html(mt_rows)
    try:
        ref_count = len(massentest_read_references())
    except Exception:
        ref_count = 0
    body = f"""
    <div class='card'>
      <div class='section-head'><h2>Dokumentenprüfung</h2><span class='count-badge'>Prüfung / Tests</span></div>
      <p class='muted'>Zentraler Arbeitsbereich für Einzeldokumenttest, Massentest, Regression und Qualitätsberichte. Referenzen werden im Massentest gepflegt; Regressionen sind Teil der Auswertungen.</p>
      <div class='hub-grid'>
        <a class='hint hub-card' href='/test/einzeltest' style='text-decoration:none;color:inherit'><div class='section-head'><b>Einzeldokument</b><span class='count-badge'>{stats['pdfs']}</span></div><div class='muted small'>Einzelne PDFs testen und Soll/Ist prüfen.</div><div class='hub-action'><span class='btn2'>Einzeldokument öffnen</span></div></a>
        <a class='hint hub-card' href='/test/massentest' style='text-decoration:none;color:inherit'><div class='section-head'><b>Massentest</b><span class='count-badge'>{mt_total}</span></div><div class='muted small'>{mt_summary}<br>Referenzen und Sollwerte sind hier eingeordnet.</div><div class='hub-action'><span class='btn2'>Massentest öffnen</span></div></a>
        <a class='hint hub-card' href='/test/massentest/analysis' style='text-decoration:none;color:inherit'><div class='section-head'><b>Berichte / Auswertungen</b><span class='count-badge'>Analyse</span></div><div class='muted small'>Automatische Qualitätsanalyse, Prioritäten und Regression als Kopiervorlage.</div><div class='hub-action'><span class='btn2'>Berichte öffnen</span></div></a>
      </div>
    </div>
    """
    return layout("Dokumentenprüfung", body)


@app.get("/test/einzeltest", response_class=HTMLResponse)
def test_page(task_created: str = "") -> HTMLResponse:
    ensure_dirs()
    pdfs = sorted([p for p in TEST_DIR.glob("*.pdf")], key=lambda x: x.stat().st_mtime if x.exists() else 0, reverse=True)
    options = "".join(f"<option>{esc(p.name)}</option>" for p in pdfs)
    stats = regression_stats()
    mt_rows = massentest_read_results()
    mt_total, mt_summary = massentest_compact_status_html(mt_rows)
    status_stats = test_progress_stats(pdfs)
    latest = stats.get("latest_report") or {}
    latest_html = "<span class='muted'>Noch kein Testlauf vorhanden.</span>"
    if latest:
        latest_html = f"<b>{esc(latest.get('timestamp',''))}</b><br>Bestanden: <span class='ok'>{latest.get('passed',0)}</span> · Abweichung: <span class='bad'>{latest.get('failed',0)}</span> · Ohne Sollwerte: <span class='warntext'>{latest.get('missing_expected',0)}</span>"
    dep_html = dependency_hint_html()
    task_flash = ""
    if task_created:
        task_flash = f"<div class='flash success'><b>Aufgabe angelegt/aktualisiert:</b> {esc(Path(task_created).name)}<br><a class='btn' href='/projekt?status=aktiv&bereich=Regressionstest'>Projektaufgaben öffnen</a></div>"
    body = f"""
    <div class='card'><h2>Einzeltest / Regressionstest</h2>
      <p><a class='btn2' href='/test'>← Zurück zur Dokumentenprüfung</a></p>
      <p class='muted'>Dieser Prüfbereich ist separat geöffnet, analog zum Massentest.</p>
      <div class='grid'>
        <div class='metric'><div class='label'>Einzeltest / Regression</div><div class='num'>{stats['pdfs']}</div><div class='muted small'>PDF-Testdokumente mit Soll/Ist-Prüfung</div></div>
        <div class='metric'><div class='label'>Massentest Altarchiv</div><div class='num'>{mt_total}</div><div class='muted small'>{mt_summary}</div><p><a class='btn2' href='/test/massentest'>Massentest öffnen</a></p></div>
      </div>
    </div>

    <div class='card'><h2>Einzeltest / Regressionstest</h2>
      <p class='muted'>Test-PDFs hochladen, Ist-Werte als Sollwerte übernehmen und alle Dokumente automatisiert gegen die aktuell installierte Scan-Service-Version prüfen. Stimmen Ist- und Sollwerte überein, wird der Test automatisch als bestanden markiert.</p>
      {task_flash}
      <div class='workflow-bar'><div class='workflow-step active'><b>1 · Übersicht</b> Testdokumente und Status prüfen</div><div class='workflow-step'><b>2 · Testen</b> Einzeltest oder Gesamttest starten</div><div class='workflow-step'><b>3 · Ergebnis</b> Soll/Ist vergleichen</div><div class='workflow-step'><b>4 · Entscheiden</b> Sollwerte speichern oder Aufgabe anlegen</div></div>
      {dep_html}
      <div class='legend' aria-label='Legende Teststatus'>
        <span><b>➜</b> aktuell geöffnet</span>
        <span><b>★</b> in dieser Sitzung bearbeitet</span>
        <span><b>✓</b> erfolgreich geprüft</span>
        <span><b>★</b> bearbeitet</span>
        <span><b>⚠</b> Abweichung</span>
        <span><b>?</b> Sollwerte fehlen</span>
        <span><b>⬜</b> noch nicht geprüft</span>
      </div>
      <div class='test-start-grid counter-above-actions'>
        <div class='counter-card productive'>
          <div class='counter-head'><span class='counter-title'>Produktiv-Ablage</span><span class='counter-badge productive'>ECHT</span></div>
          <div class='counter-code'>{esc(berechne_naechsten_barcode())}</div>
          <div class='counter-sub'>Scanner/Outlook · produktiver Zähler</div>
        </div>
        <div class='counter-card test'>
          <div class='counter-head'><span class='counter-title'>Test-Ablage</span><span class='counter-badge test'>TEST</span></div>
          <div class='counter-code'>{esc(berechne_test_barcode())}</div>
          <div class='counter-sub'>Testcenter · eigener Testzähler</div>
        </div>
      </div>
      <div class='test-start-grid'>
        <div class='test-panel compact'><h3>+ Testdokument hinzufügen</h3><p class='muted small'>PDFs nur fürs Testcenter. Produktivzähler bleibt unberührt.</p><form method='post' action='/test/upload' enctype='multipart/form-data' class='toolbar'>
          <input type='file' name='pdfs' accept='application/pdf' multiple>
          <button class='btn2' type='submit'>PDF hochladen</button>
        </form></div>
        <div class='test-panel compact'><h3>▶ Testlauf starten</h3><p class='muted small'>Einzeldokument oder kompletten Regressionstest starten.</p><div class='toolbar'>
          <form method='post' action='/test/run'>
            <select name='filename'>{options}</select>
            <button class='btn' type='submit'>PDF testen</button>
          </form>
          <form method='post' action='/test/run-all'><button class='btn success' type='submit'>Alle Referenzdokumente testen</button></form>
          <form method='post' action='/test/expected/generate-missing' data-confirm-title='Fehlende Sollwerte erzeugen?' data-confirm-message='Für Dokumente ohne Sollwerte werden die aktuellen Ist-Werte als Vorschlag gespeichert.' data-confirm-details='Bitte danach die erzeugten Sollwerte prüfen, bevor du die Tests als bestanden freigibst.' data-confirm-kind='eco-modal-success' data-confirm-ok='Ja, erzeugen'><button class='btn2 success' type='submit'>Fehlende Sollwerte</button></form>
        </div></div>
      </div>
      <div class='test-top-status'>
        <div class='metric'><div class='label'>Testdokumente</div><div class='num'>{stats['pdfs']}</div></div>
        <div class='metric'><div class='label'>Sollwerte</div><div class='num ok'>{stats['expected']}</div></div>
        <div class='metric'><div class='label'>Fehlen</div><div class='num warntext'>{stats['missing']}</div></div>
        <div class='metric'><div class='label'>OK</div><div class='num ok'>{status_stats['ok']}</div><div class='muted small'>Abw.: {status_stats['abweichung']} · Offen: {status_stats['offen']}</div></div>
      </div>
      <div class='progress-wrap' title='Sollwert-Fortschritt'><div class='progress-bar' style='width:{0 if stats['pdfs']==0 else int(stats['expected']*100/stats['pdfs'])}%'></div></div>
      <p class='small muted'>Sollwert-Fortschritt: {stats['expected']} von {stats['pdfs']} Dokumenten. · Letzter Testlauf: {latest_html}</p>
      <div class='grid'>{render_project_hint_for_testcenter()}</div>
      <div class='workflow-note'>Tipp: <b>Ist-Werte übernehmen</b> steht auch bei fehlenden Sollwerten direkt in der Liste und speichert alle Felder inklusive leerer Werte. Für Änderungen am Testfall nutze zuerst „Sollwerte“, für Programmfehler „Aufgabe“.</div>
      <div id='offene-dokumente' class='test-doc-sections test-focus-anchor'>
        <details class='test-doc-section open-priority' open>
          <summary>⚠ Abweichung ({status_stats['abweichung'] + status_stats['fehler']})</summary>
          <div class='test-table-wrap'><table class='test-table-compact'><tr><th>Datei</th><th>Größe</th><th>Geändert</th><th>Sollwerte</th><th>Prüfstatus</th><th>Aktion</th></tr>{render_test_overview_rows(pdfs, {'abweichung', 'fehler'})}</table></div>
        </details>
        <details class='test-doc-section' open>
          <summary>⬜ Noch offen / bearbeitet ({status_stats['offen'] + status_stats['bearbeitet']})</summary>
          <div class='test-table-wrap'><table class='test-table-compact'><tr><th>Datei</th><th>Größe</th><th>Geändert</th><th>Sollwerte</th><th>Prüfstatus</th><th>Aktion</th></tr>{render_test_overview_rows(pdfs, {'ungeprueft', 'bearbeitet'})}</table></div>
        </details>
        <details class='test-doc-section'>
          <summary>? Sollwerte fehlen ({status_stats['ohne_soll']})</summary>
          <div class='test-table-wrap'><table class='test-table-compact'><tr><th>Datei</th><th>Größe</th><th>Geändert</th><th>Sollwerte</th><th>Prüfstatus</th><th>Aktion</th></tr>{render_test_overview_rows(pdfs, {'sollwerte_fehlen'})}</table></div>
        </details>
        <details class='test-doc-section done-box'>
          <summary>✓ Erfolgreich geprüft ({status_stats['ok']})</summary>
          <p class='muted small' style='padding:0 16px'>Diese Dokumente passen zur aktuell installierten Scan-Service-Version und dienen als Referenz.</p>
          <div class='test-table-wrap'><table class='test-table-compact'><tr><th>Datei</th><th>Größe</th><th>Geändert</th><th>Sollwerte</th><th>Prüfstatus</th><th>Aktion</th></tr>{render_test_overview_rows(pdfs, {'geprueft_ok'})}</table></div>
        </details>
      </div>
    </div>"""
    return layout("Testcenter 2.0", body)


def unique_test_target(filename: str) -> Path:
    base = Path(filename).name
    target = TEST_DIR / base
    if not target.exists():
        return target
    stem = target.stem
    suffix = target.suffix
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    i = 1
    while True:
        candidate = TEST_DIR / f"{stem}_{stamp}_{i}{suffix}"
        if not candidate.exists():
            return candidate
        i += 1



def _pfad_aus_dateiname_config_webui(wert: str, fallback: Path) -> Path:
    wert = str(wert or "").strip().replace("\\", "/")
    if not wert:
        return fallback
    p = Path(wert)
    if not p.is_absolute():
        p = BASE_DIR / p
    return p


def lade_dateiname_config_webui() -> dict[str, str]:
    defaults = {
        "PDF_UMBENENNEN": "1",
        "PDF_DATEINAME_SCHEMA": "{DATUM}_{LIEFERANT}_{NUMMER}",
        "PDF_DATEINAME_MAX_LAENGE": "160",
        "PDF_TEST_ARCHIV_AKTIV": "1",
        "PDF_TEST_ARCHIV_ORDNER": "_erledigt/_test",
        "PDF_DATEINAME_LOG": "_logs/pdf_dateinamen.log",
    }
    values, _ = parse_key_value_config(DATEINAME_CONFIG_FILE)
    return {**defaults, **values}


def eindeutiger_pfad_in_ordner(ordner: Path, name: str) -> Path:
    ordner.mkdir(parents=True, exist_ok=True)
    ziel = ordner / Path(name).name
    if not ziel.exists():
        return ziel
    stem, suffix = ziel.stem, ziel.suffix or ".pdf"
    for i in range(2, 1000):
        kandidat = ordner / f"{stem}_{i:02d}{suffix}"
        if not kandidat.exists():
            return kandidat
    return ordner / f"{stem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}{suffix}"


def schreibe_dateiname_log_webui(quelle: str, alt: str, neu: str, ziel: Path, status: str = "OK") -> None:
    try:
        cfg = lade_dateiname_config_webui()
        log_pfad = _pfad_aus_dateiname_config_webui(cfg.get("PDF_DATEINAME_LOG", "_logs/pdf_dateinamen.log"), LOG_DIR / "pdf_dateinamen.log")
        log_pfad.parent.mkdir(parents=True, exist_ok=True)
        zeile = "|".join([
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            str(quelle or ""),
            str(alt or ""),
            str(neu or ""),
            str(ziel or ""),
            str(status or ""),
        ])
        with open(log_pfad, "a", encoding="utf-8") as f:
            f.write(zeile + "\n")
    except Exception:
        pass


def archiviere_test_pdf_mit_metadaten(pdf_path: Path, meta: dict[str, str], test_barcode: str = "") -> None:
    cfg = lade_dateiname_config_webui()
    if cfg.get("PDF_UMBENENNEN", "1") != "1" or cfg.get("PDF_TEST_ARCHIV_AKTIV", "1") != "1":
        return
    try:
        service = import_scan_service()
        if hasattr(service, "erstelle_pdf_zielname_v5712"):
            zielname = service.erstelle_pdf_zielname_v5712(meta, test_barcode)
        else:
            zielname = pdf_path.name
        ziel_ordner = _pfad_aus_dateiname_config_webui(cfg.get("PDF_TEST_ARCHIV_ORDNER", "_erledigt/_test"), BASE_DIR / "_erledigt" / "_test")
        ziel = eindeutiger_pfad_in_ordner(ziel_ordner, zielname)
        shutil.copy2(str(pdf_path), str(ziel))
        schreibe_dateiname_log_webui("TEST-ARCHIV", pdf_path.name, ziel.name, ziel)
    except Exception as e:
        schreibe_dateiname_log_webui("TEST-ARCHIV", pdf_path.name, "", Path(""), f"FEHLER: {e}")

@app.post("/test/upload")
async def upload_test_pdf(pdfs: list[UploadFile] = File(...)):
    ensure_dirs()
    for pdf in pdfs:
        filename = pdf.filename or ""
        if not filename.lower().endswith(".pdf"):
            continue
        target = unique_test_target(filename)
        with open(target, "wb") as f:
            while chunk := await pdf.read(1024 * 1024):
                f.write(chunk)
        # Testcenter nutzt einen eigenen Zählerkreis. Jeder neue Upload verbraucht
        # genau eine TEST-Kennung, der produktive Zähler bleibt unverändert.
        test_barcode = erhoehe_test_zaehler()
        schreibe_test_upload_meta(target, test_barcode)
        # V2.7.11: Ist-Werte direkt beim Upload ermitteln. Wenn noch keine Sollwerte
        # vorhanden sind, werden die Ist-Werte als erster Sollwert-Vorschlag gespeichert.
        try:
            meta, expected, comparisons, error = run_single_regression(target)
            service_version = get_scan_service_version()
            try:
                archiviere_test_pdf_mit_metadaten(target, meta, test_barcode)
            except Exception:
                pass
            if error:
                write_test_status(target.name, "fehler", error, service_version)
            elif (not manual_passed) and not expected:
                save_expected_from_meta(target.name, meta, overwrite=True, filled_only=False)
                write_test_status(target.name, "bearbeitet", "Ist-Werte beim Upload als Sollwerte vorgeschlagen", service_version)
            else:
                ok_all = all(x[3] for x in comparisons)
                if ok_all:
                    write_test_status(target.name, "geprueft_ok", "Upload-Test bestanden", service_version)
                    projekt_markiere_regression_erledigt(target.name, "Upload-Test bestanden")
                else:
                    write_test_status(target.name, "abweichung", "Upload-Test: Soll/Ist-Abweichung gefunden", service_version)
                    projekt_regression_reaktivieren(target.name)
        except Exception as e:
            try:
                write_test_status(target.name, "fehler", f"Upload-Auswertung fehlgeschlagen: {e}", get_scan_service_version())
            except Exception:
                pass
    return RedirectResponse("/test/einzeltest#offene-dokumente", status_code=303)


@app.post("/test/delete")
def delete_test_pdf(filename: str = Form(...)):
    target = TEST_DIR / Path(filename).name
    if target.exists() and target.suffix.lower() == ".pdf":
        try:
            target.unlink()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Test-PDF konnte nicht gelöscht werden: {e}")
    exp = expected_path_for(filename)
    if exp.exists():
        try:
            exp.unlink()
        except Exception:
            pass
    for extra in [target.with_suffix(target.suffix + ".testmeta"), target.with_suffix(".testmeta")]:
        try:
            if extra.exists():
                extra.unlink()
        except Exception:
            pass
    delete_test_status(filename)
    return RedirectResponse("/test/einzeltest#offene-dokumente", status_code=303)



@app.get("/test/open-pdf")
def open_test_pdf(filename: str):
    """Öffnet ein Test-PDF auf dem Windows-Rechner im Standard-PDF-Reader."""
    pdf_name = Path(filename).name
    pdf_path = TEST_DIR / pdf_name
    if not pdf_path.exists() or pdf_path.suffix.lower() != ".pdf":
        raise HTTPException(status_code=404, detail="PDF nicht gefunden")
    try:
        if hasattr(os, "startfile"):
            os.startfile(str(pdf_path))  # type: ignore[attr-defined]
        else:
            subprocess.Popen(["xdg-open", str(pdf_path)])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF konnte nicht geöffnet werden: {e}")
    return HTMLResponse(f"""<!doctype html><html><head><meta charset='utf-8'><title>PDF geöffnet</title></head><body style='font-family:Arial,sans-serif;padding:20px'><h3>PDF wurde im Standard-Reader geöffnet</h3><p>{esc(pdf_name)}</p><p>Dieses Fenster kann geschlossen werden.</p><script>setTimeout(function(){{ try{{ window.close(); }}catch(e){{}} }}, 800);</script></body></html>""")

@app.get("/test/expected", response_class=HTMLResponse)
def edit_expected(filename: str) -> HTMLResponse:
    pdf_name = Path(filename).name
    pdf_path = TEST_DIR / pdf_name
    if not pdf_path.exists() or pdf_path.suffix.lower() != ".pdf":
        raise HTTPException(status_code=404, detail="PDF nicht gefunden")
    exp_path = expected_path_for(pdf_name)
    content = read_text(exp_path)
    if not content.strip():
        content = expected_to_text({
            "LIEFERANT": "", "DOKUMENTTYP": "", "DOKUMENTKLASSE": "", "RECHDATUM": "",
            "RECHNR": "", "KUNDENNR": "", "AUFTRAGNR": "", "BESTELLNR": "",
            "LIEFERSCHEINNR": "", "VERSICHERUNGSNR": "", "GESAMTBETRAG": "",
        })
    body = f"""
    <div class='sticky-workbar'><div><span class='mini-tag'>Schritt 4 · Sollwerte</span> <b>{esc(pdf_name)}</b></div><div class='test-actions nowrap' style='margin-top:10px'><a class='btn2' href='/test/einzeltest'>← Zurück zur Übersicht</a><form method='post' action='/test/run' style='display:inline'><input type='hidden' name='filename' value='{esc(pdf_name)}'><button class='btn2' type='submit'>Erneut testen</button></form></div></div>
    <div class='card result-focus'>
      <h2>Sollwerte</h2>
      <p class='muted'>Alle aufgeführten Felder werden im Regressionstest verglichen. Leere Werte sind bewusst erlaubt und bedeuten: Dieses Feld soll leer bleiben.</p>
      <form method='post' action='/test/expected'>
        <input type='hidden' name='filename' value='{esc(pdf_name)}'>
        <textarea name='content' style='height:46vh'>{esc(content)}</textarea>
        <p><button class='btn' type='submit' name='mark_passed' value='0'>Sollwerte speichern</button> <button class='btn success' type='submit' name='mark_passed' value='1' data-confirm-title='Sollwerte speichern und Test bestanden?' data-confirm-message='Die gerade bearbeiteten Sollwerte werden gespeichert und direkt als gültige Referenz freigegeben.' data-confirm-details='Damit besteht das Dokument mit diesen Sollwerten. Künftige Regressionstests vergleichen die Ist-Werte gegen genau diese gespeicherte Referenz.' data-confirm-kind='eco-modal-success' data-confirm-ok='Ja, speichern und freigeben'>✓ Speichern + Test bestanden</button> <a class='btn2' href='/test/einzeltest'>Zurück zur Übersicht</a></p>
      </form>
      <p class='small muted'>Datei: <span class='folder-name'>{esc(exp_path)}</span></p>
    </div>"""
    return layout("Sollwerte", body)


@app.post("/test/expected")
def save_expected(filename: str = Form(...), content: str = Form(""), mark_passed: str = Form("0")):
    pdf_name = Path(filename).name
    pdf_path = TEST_DIR / pdf_name
    if not pdf_path.exists() or pdf_path.suffix.lower() != ".pdf":
        raise HTTPException(status_code=404, detail="PDF nicht gefunden")
    exp_path = expected_path_for(pdf_name)
    exp_path.parent.mkdir(parents=True, exist_ok=True)
    write_text_backup(exp_path, content.strip() + "\n")
    if mark_passed == "1":
        write_test_status(pdf_name, "geprueft_ok", "Sollwerte gespeichert und manuell als bestanden markiert", get_scan_service_version())
        projekt_markiere_regression_erledigt(pdf_name, "Sollwerte gespeichert und manuell als bestanden markiert")
        return RedirectResponse("/test/einzeltest#erfolgreich", status_code=303)
    write_test_status(pdf_name, "bearbeitet", "Sollwerte manuell gespeichert")
    return RedirectResponse("/test/einzeltest#offene-dokumente", status_code=303)


@app.post("/test/expected/from-actual")
def expected_from_actual(filename: str = Form(...), overwrite: str = Form("1"), filled_only: str = Form("0")):
    pdf_name = Path(filename).name
    pdf_path = TEST_DIR / pdf_name
    if not pdf_path.exists() or pdf_path.suffix.lower() != ".pdf":
        raise HTTPException(status_code=404, detail="PDF nicht gefunden")
    meta, _expected, _comparisons, error = run_single_regression(pdf_path)
    if error:
        raise HTTPException(status_code=500, detail=error)
    save_expected_from_meta(pdf_name, meta, overwrite=(overwrite == "1"), filled_only=(filled_only == "1"))
    return RedirectResponse("/test/einzeltest#offene-dokumente", status_code=303)


@app.post("/test/expected/generate-missing", response_class=HTMLResponse)
def generate_missing_expected() -> HTMLResponse:
    ensure_dirs()
    pdfs = sorted(TEST_DIR.glob("*.pdf"), key=lambda x: x.name.lower())
    rows = ""
    created = 0
    skipped = 0
    errors = 0
    for p in pdfs:
        if expected_path_for(p.name).exists():
            skipped += 1
            rows += f"<tr><td class='folder-name'>{esc(p.name)}</td><td>übersprungen</td><td>Sollwerte vorhanden</td></tr>"
            continue
        meta, _expected, _comparisons, error = run_single_regression(p)
        if error:
            errors += 1
            rows += f"<tr><td class='folder-name'>{esc(p.name)}</td><td class='bad'>Fehler</td><td>{esc(error)}</td></tr>"
            continue
        ok, message = save_expected_from_meta(p.name, meta, overwrite=False, filled_only=False)
        if ok:
            created += 1
        else:
            skipped += 1
        rows += f"<tr><td class='folder-name'>{esc(p.name)}</td><td>{'✅ erzeugt' if ok else '— übersprungen'}</td><td>{esc(message)}</td></tr>"
    body = f"""
    <div class='top-actions'><div><b>Fehlende Sollwerte erzeugen</b></div><a class='btn2' href='/test'>← Zurück zur Dokumentenprüfung</a></div>
    <div class='card'>
      <h2>Automatische Sollwert-Erzeugung</h2>
      <div class='grid'>
        <div class='metric'><div class='label'>Erzeugt</div><div class='num ok'>{created}</div></div>
        <div class='metric'><div class='label'>Übersprungen</div><div class='num warntext'>{skipped}</div></div>
        <div class='metric'><div class='label'>Fehler</div><div class='num bad'>{errors}</div></div>
      </div>
      <p class='muted'>Bitte die neu erzeugten Sollwerte einmal stichprobenartig prüfen. Danach sind sie die Referenz für neue Scan-Service-Versionen.</p>
      <table><tr><th>Datei</th><th>Status</th><th>Details</th></tr>{rows}</table>
    </div>"""
    return layout("Sollwerte erzeugen", body)


@app.post("/test/run-all", response_class=HTMLResponse)
def run_all_tests() -> HTMLResponse:
    ensure_dirs()
    pdfs = sorted(TEST_DIR.glob("*.pdf"), key=lambda x: x.name.lower())
    rows = ""
    total = len(pdfs)
    passed = 0
    failed = 0
    missing_expected = 0
    error_count = 0
    report_items = []
    service_version = get_scan_service_version()

    for p in pdfs:
        manual_passed = is_manual_test_passed(p.name) and expected_path_for(p.name).exists()
        if manual_passed:
            expected = parse_expected_text(read_text(expected_path_for(p.name)))
            meta, comparisons, error = {}, [], ""
            status = "✓ manuell bestanden"
            detail = "<div class='flash ok'><b>Manuell freigegebener Sonderfall</b><br>Dieser Testfall wurde bewusst mit den gespeicherten Sollwerten als bestanden markiert und wird im Volltest nicht erneut als Abweichung gewertet.</div>"
            passed += 1
            projekt_markiere_regression_erledigt(p.name, "Manuell freigegebener Sonderfall")
        else:
            meta, expected, comparisons, error = run_single_regression(p)
        if (not manual_passed) and error:
            status = "⚠ Fehler"
            detail = f"<span class='bad'>{esc(error)}</span>"
            failed += 1
            error_count += 1
            write_test_status(p.name, "fehler", error, service_version)
        elif not expected:
            status = "? ohne Sollwerte"
            values = clean_actual_values(meta, filled_only=True)
            preview = "".join(f"<tr><td>{esc(k)}</td><td>{esc(v)}</td></tr>" for k, v in values.items()) or "<tr><td colspan='2' class='muted'>Keine Werte erkannt.</td></tr>"
            detail = f"<span class='warntext'>Keine Sollwerte hinterlegt.</span><table><tr><th>Erkanntes Feld</th><th>Ist</th></tr>{preview}</table>"
            missing_expected += 1
            write_test_status(p.name, "sollwerte_fehlen", "Keine Sollwerte vorhanden", service_version)
        elif not manual_passed:
            ok_all = all(x[3] for x in comparisons)
            status = "✓ bestanden" if ok_all else "⚠ Abweichung"
            if ok_all:
                passed += 1
                write_test_status(p.name, "geprueft_ok", "Alle Sollwerte stimmen", service_version)
                projekt_markiere_regression_erledigt(p.name, "Alle Sollwerte stimmen")
            else:
                failed += 1
                write_test_status(p.name, "abweichung", "Soll/Ist-Abweichung gefunden", service_version)
                projekt_regression_reaktivieren(p.name)
            comp_rows = "".join(
                f"<tr><td>{esc(k)}</td><td>{esc(exp) if str(exp).strip() else '<span class="muted">leer</span>'}</td><td>{esc(act) if str(act).strip() else '<span class="muted">leer</span>'}</td><td>{'✓' if ok else '⚠'}</td></tr>"
                for k, exp, act, ok in comparisons
            )
            detail = f"<table><tr><th>Feld</th><th>Soll</th><th>Ist</th><th></th></tr>{comp_rows}</table>"

        report_items.append({"file": p.name, "status": status, "error": error or "", "missing_expected": (not bool(expected)) and not manual_passed, "manual_passed": manual_passed, "meta": meta, "diffs": [] if manual_passed else [{"field": k, "expected": exp, "actual": act} for k, exp, act, ok in comparisons if not ok]})
        symbol, status_info, row_class, _stored_status = test_status_display(p.name, expected_path_for(p.name).exists())
        rows += f"""
        <tr class='{row_class}'>
          <td><span class='status-symbol'>{symbol}</span> <span class='folder-name'>{esc(p.name)}</span></td>
          <td>{status}<br><span class='small muted'>{esc(status_info)}</span></td>
          <td>{detail}</td>
          <td style='white-space:nowrap'>
            <a class='btn2' href='/test/expected?filename={esc(p.name)}'>Sollwerte</a>
            <form method='post' action='/test/expected/from-actual' style='display:inline'><input type='hidden' name='filename' value='{esc(p.name)}'><input type='hidden' name='overwrite' value='1'><input type='hidden' name='filled_only' value='0'><button class='btn2 success' type='submit'>Ist-Werte übernehmen</button></form>
            {"<form method='post' action='/projekt/aus-regression' style='display:inline'><input type='hidden' name='return_to' value='projekt'><input type='hidden' name='filename' value='" + esc(p.name) + "'><input type='hidden' name='delta' value='" + esc(chatgpt_delta_text(p.name, expected, meta, comparisons, error, '')) + "'><button class='btn2 warn' type='submit'>Aufgabe anlegen</button></form>" if ((not manual_passed) and (error or (expected and any(not x[3] for x in comparisons)))) else ""}
          </td>
        </tr>"""

    report = {
        "timestamp": datetime.now().strftime("%d.%m.%Y %H:%M:%S"),
        "service_version": service_version,
        "total": total,
        "passed": passed,
        "failed": failed,
        "missing_expected": missing_expected,
        "errors": error_count,
        "items": report_items,
    }
    try:
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        (REPORTS_DIR / (datetime.now().strftime("%Y%m%d_%H%M%S") + ".json")).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass
    body = f"""
    <div class='top-actions'><div><b>Regressionstest</b> <span class='muted'>{total} Testdateien</span></div><a class='btn2' href='/test'>← Zurück zur Dokumentenprüfung</a></div>
    <div class='card'>
      <h2>Automatischer Testlauf</h2>
      <div class='legend' aria-label='Legende Teststatus'>
        <span><b>✓</b> erfolgreich geprüft</span><span><b>★</b> bearbeitet</span><span><b>⚠</b> Abweichung</span><span><b>?</b> Sollwerte fehlen</span><span><b>⬜</b> noch nicht geprüft</span>
      </div>
      <div class='grid'>
        <div class='metric'><div class='label'>Bestanden</div><div class='num ok'>{passed}</div></div>
        <div class='metric'><div class='label'>Abweichung</div><div class='num bad'>{failed}</div></div>
        <div class='metric'><div class='label'>Ohne Sollwerte</div><div class='num warntext'>{missing_expected}</div></div>
        <div class='metric'><div class='label'>Zeitpunkt</div><div class='small'><b>{esc(report['timestamp'])}</b><br>Service: {esc(service_version)}</div></div>
      </div>
      <div class='toolbar'><form method='post' action='/test/expected/generate-missing'><button class='btn2 success' type='submit'>Fehlende Sollwerte erzeugen</button></form><button class='btn2' type='button' onclick="copyText('delta_all')">Alle Abweichungen für ChatGPT kopieren</button></div>
      <details class='card' style='box-shadow:none;margin:0 0 14px 0'><summary><b>Delta-Kopiervorlage für ChatGPT</b></summary><p class='muted small'>Diese Vorlage kannst du direkt in den Chat kopieren.</p><textarea id='delta_all' class='copyarea' readonly>{esc(chatgpt_delta_all_text(report_items))}</textarea></details>
      <table><tr><th>Datei</th><th>Status</th><th>Details</th><th>Aktion</th></tr>{rows or '<tr><td colspan="4" class="muted">Keine Test-PDFs vorhanden.</td></tr>'}</table>
    </div>"""
    return layout("Regressionstest", body)


@app.post("/test/run", response_class=HTMLResponse)
def run_test(filename: str = Form(...)) -> HTMLResponse:
    pdf_path = TEST_DIR / Path(filename).name
    if not pdf_path.exists() or pdf_path.suffix.lower() != ".pdf":
        raise HTTPException(status_code=404, detail="PDF nicht gefunden")
    try:
        service = import_scan_service()
        text = service.lese_text_aus_pdf(pdf_path)
        meta = service.erzeuge_meta_daten(pdf_path)
        meta = {str(k).upper(): str(v or "") for k, v in meta.items()}
        debug_name = f"{pdf_path.stem}_text.txt"
        debug_path = DEBUG_TEXT_DIR / debug_name
        debug_text = read_text(debug_path) or text
        display_meta = clean_actual_values(meta, filled_only=False)
        ocrq = str(meta.get("OCR_QUALITAET", "")).upper()
        ocr_warning = ""
        if ocrq == "UNLESERLICH":
            ocr_warning = "<div class='flash bad'><b>🔴 OCR-QUALITÄT: UNLESERLICH</b><br>Automatische Klassifizierung nicht zuverlässig möglich. Dokument manuell prüfen.</div>"
        elif ocrq == "SCHLECHT":
            ocr_warning = "<div class='flash warn'><b>🟠 OCR-QUALITÄT: SCHLECHT</b><br>Ergebnis bitte besonders prüfen.</div>"
        elif ocrq == "MITTEL":
            ocr_warning = "<div class='flash warn'><b>🟡 OCR-QUALITÄT: MITTEL</b><br>Ergebnis prüfen.</div>"
        meta_html = "".join(f"<tr><td>{esc(k)}</td><td>{esc(v) if str(v).strip() else '<span class="muted">leer</span>'}</td></tr>" for k, v in display_meta.items()) or "<tr><td colspan='2' class='muted'>Keine Metadaten erkannt.</td></tr>"
        expected = parse_expected_text(read_text(expected_path_for(filename)))
        manual_passed = is_manual_test_passed(filename)
        compare_html = ""
        if expected:
            comp_rows = "".join(f"<tr><td>{esc(k)}</td><td>{esc(ev)}</td><td>{esc(meta.get(k, ''))}</td><td>{'✅' if norm_compare(meta.get(k, '')) == norm_compare(ev) else '❌'}</td></tr>" for k, ev in expected.items() if str(ev or '').strip() or str(meta.get(k, '') or '').strip())
            compare_html = f"<table><tr><th>Feld</th><th>Soll</th><th>Ist</th><th></th></tr>{comp_rows}</table>"
        else:
            compare_html = "<div class='flash warn'>Für dieses Dokument gibt es noch keine Sollwerte.</div>"
        comparisons_for_delta = []
        if expected:
            comparisons_for_delta = [(k, ev, meta.get(k, ''), norm_compare(meta.get(k, '')) == norm_compare(ev)) for k, ev in expected.items()]
        if manual_passed:
            projekt_markiere_regression_erledigt(filename, "Manuell freigegebener Sonderfall")
        else:
            if ocrq == "UNLESERLICH":
                projekt_ocr_manuell_aufgabe(filename, debug_text)
            if not expected:
                write_test_status(filename, "sollwerte_fehlen", "Einzeltest ohne Sollwerte")
            elif all(x[3] for x in comparisons_for_delta):
                write_test_status(filename, "geprueft_ok", "Einzeltest erfolgreich")
                projekt_markiere_regression_erledigt(filename, "Einzeltest erfolgreich")
            else:
                write_test_status(filename, "abweichung", "Einzeltest mit Abweichung")
                projekt_regression_reaktivieren(filename)
        delta_text = chatgpt_delta_text(filename, expected, meta, comparisons_for_delta, None, debug_text if expected and any(not x[3] for x in comparisons_for_delta) else "")
        delta_html = f"""<details class='card' style='box-shadow:none;margin-top:14px'><summary><b>Delta für ChatGPT</b></summary><p class='muted small'>Bei Abweichungen hier kopieren und in den Chat einfügen.</p><button class='btn2' type='button' onclick="copyText('delta_single')">Delta kopieren</button><textarea id='delta_single' class='copyarea' readonly>{esc(delta_text)}</textarea></details>"""
        has_deviation = bool(expected and any(not x[3] for x in comparisons_for_delta))
        create_task_html = f"""<form method='post' action='/projekt/aus-regression' style='display:inline'><input type='hidden' name='return_to' value='projekt'><input type='hidden' name='filename' value='{esc(filename)}'><input type='hidden' name='delta' value='{esc(delta_text)}'><button class='btn2 warn' type='submit'>Aufgabe anlegen</button></form>""" if (has_deviation and not manual_passed) else ""
        if manual_passed:
            deviation_actions_html = f"""<a class='btn2' href='/test/expected?filename={esc(filename)}'>Sollwerte bearbeiten</a> <span class='mini-actions'><form method='post' action='/test/expected/from-actual' style='display:inline'><input type='hidden' name='filename' value='{esc(filename)}'><input type='hidden' name='overwrite' value='1'><input type='hidden' name='filled_only' value='0'><button class='btn2 success' type='submit'>Ist-Werte übernehmen</button></form></span>"""
            auto_pass_html = "<div class='flash ok'><b>🟢 Manuell als bestanden freigegeben</b><br>Dieser Sonderfall wird beim Volltest nicht erneut als Abweichung oder Aufgabe erzeugt.</div>"
        elif has_deviation or not expected:
            deviation_actions_html = f"""<a class='btn2' href='/test/expected?filename={esc(filename)}'>Sollwerte bearbeiten</a> <form method='post' action='/test/mark-passed' style='display:inline' data-confirm-title='Mit Sollwerten als Metadaten bestanden?' data-confirm-message='Das Dokument wird mit den aktuell gespeicherten Sollwerten als gültige Referenz bestanden markiert.' data-confirm-details='Die Sollwerte sind damit die maßgeblichen Metadaten für diesen Test. Die erkannten Ist-Werte werden nicht übernommen oder geändert. Die Projektaufgabe wird erledigt.' data-confirm-kind='eco-modal-success' data-confirm-ok='Ja, bewusst freigeben'><input type='hidden' name='filename' value='{esc(filename)}'><button class='btn success' type='submit'><span class='btn-stack'>✓ Test bestanden<span class='btn-sub'>Sollwerte übernehmen</span></span></button></form><span class='mini-actions'><form method='post' action='/test/expected/from-actual' style='display:inline'><input type='hidden' name='filename' value='{esc(filename)}'><input type='hidden' name='overwrite' value='1'><input type='hidden' name='filled_only' value='0'><button class='btn2 success' type='submit'>Ist-Werte übernehmen</button></form><form method='post' action='/test/expected/from-actual' style='display:inline'><input type='hidden' name='filename' value='{esc(filename)}'><input type='hidden' name='overwrite' value='1'><input type='hidden' name='filled_only' value='1'><button class='btn2' type='submit'>nur gefüllte Ist-Werte</button></form>{create_task_html}</span>"""
            auto_pass_html = ""
        else:
            deviation_actions_html = ""
            auto_pass_html = "<div class='flash ok'><b>🟢 Test automatisch bestanden</b><br>Alle prüfbaren Sollwerte entsprechen den Ist-Werten. Es ist keine manuelle Bestätigung nötig.</div>"
        body = f"""
        <div class='sticky-workbar'><div><a class='btn2' href='/test/einzeltest'>← Zurück zur Übersicht</a> <span class='mini-tag'>Schritt 3 · Testergebnis</span> <b>{esc(filename)}</b></div></div>
        <div class='card result-focus'><h2>Testergebnis: {esc(filename)}</h2><p class='muted small'>Bei vollständiger Übereinstimmung wird der Test automatisch bestanden. Bei Abweichungen kannst du Sollwerte korrigieren, Ist-Werte als neue Referenz übernehmen oder das Dokument bewusst mit den gespeicherten Sollwerten als Metadaten bestanden markieren.</p>
          <div class='resultbar'>
            <a class='btn2' href='/test/einzeltest'>← Zurück zur Übersicht</a>
            <a class='btn2' href='/test/open-pdf?filename={esc(filename)}' target='_blank' rel='noopener'>PDF öffnen</a>
            {deviation_actions_html}
          </div>
          {auto_pass_html}{ocr_warning}<div class="result-grid"><div class="result-card"><h3>1. Erkannte Ist-Werte</h3><table>{meta_html}</table></div><div class="result-card"><h3>2. Soll/Ist-Prüfung</h3>{compare_html}</div></div>{delta_html}<details id='ocr_debug' class="card" open><summary><b>OCR-/Debug-Text</b></summary><div class='toolbar nowrap'><button class='btn2' type='button' onclick="copyText('ocr_text_area')">Kopieren</button></div><textarea id='ocr_text_area' class='copyarea' readonly style='height:360px'>{esc(debug_text)}</textarea></details></div>"""
    except ModuleNotFoundError as e:
        write_test_status(filename, "fehler", str(e))
        missing = (e.name or str(e)).strip()
        package = MODULE_HINTS.get(missing, missing)
        body = f"""<div class='top-actions'><div><b>Testfehler</b></div><a class='btn2' href='/test'>← Zurück zur Dokumentenprüfung</a></div><div class='card'><h2>Testfehler</h2>
        <p class='bad'>Python-Modul fehlt: {esc(missing)}</p>
        <p>Installiere das Paket in der Python-Umgebung, mit der die WebUI gestartet wird:</p>
        <pre>python -m pip install {esc(package)}</pre>
        <p class='muted small'>Danach WebUI neu starten.</p>
        <p><a class='btn2' href='/test/einzeltest'>Zurück zur Übersicht</a></p></div>"""
    except Exception as e:
        write_test_status(filename, "fehler", str(e))
        body = f"<div class='top-actions'><div><b>Testfehler</b></div><a class='btn2' href='/test'>← Zurück zur Dokumentenprüfung</a></div><div class='card'><h2>Testfehler</h2><p class='bad'>{esc(e)}</p><p class='muted small'>Hinweis: Für OCR müssen Poppler, Tesseract und die Python-Pakete des Scan-Service installiert sein.</p><p><a class='btn2' href='/test/einzeltest'>Zurück zur Übersicht</a></p></div>"
    return layout("Testergebnis", body)




# ============================================================
# PROJEKTCENTER - WebUI 2.5
# ============================================================

PROJEKT_ORDNER = BASE_DIR / "_projektcenter"
PROJEKT_AUFGABEN_DATEI = PROJEKT_ORDNER / "aufgaben.json"
PROJEKT_ORDNER.mkdir(parents=True, exist_ok=True)


def projekt_lade_aufgaben() -> list[dict]:
    """Zentrale Aufgabenquelle: liest ausschliesslich _projektcenter/aufgaben.json."""
    if not PROJEKT_AUFGABEN_DATEI.exists():
        return []
    try:
        daten = json.loads(PROJEKT_AUFGABEN_DATEI.read_text(encoding="utf-8"))
        aufgaben = daten if isinstance(daten, list) else []
    except Exception:
        return []
    aufgaben = projekt_bereinige_zombie_aufgaben_beim_laden(aufgaben)
    return projekt_normalisiere_doppelte_regressionen_2727(aufgaben)


def projekt_bereinige_zombie_aufgaben_beim_laden(aufgaben: list[dict]) -> list[dict]:
    """V2.7.23: Harte Bereinigung von Zombie-/OCR-Testaufgaben.

    Diese Funktion läuft direkt beim Laden der Aufgaben-Datei. Sie setzt aktive
    OCR-/Regressionstest-Aufgaben auf erledigt, wenn das zugehörige Test-PDF im
    PDF-Testcenter nicht mehr existiert. Zusätzlich wird der bekannte alte
    Zombie-Fall pc-061 sicher abgefangen.
    """
    if not isinstance(aufgaben, list):
        return []

    vorhandene_pdfs = set()
    vorhandene_stems = set()
    try:
        if TEST_DIR.exists():
            for p in TEST_DIR.glob("*.pdf"):
                vorhandene_pdfs.add(p.name.strip().lower())
                vorhandene_stems.add(p.stem.strip().lower())
    except Exception:
        vorhandene_pdfs = set()
        vorhandene_stems = set()

    jetzt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    changed = False

    def norm_status(a: dict) -> str:
        return str(a.get("status", "offen")).strip().lower().replace(" ", "_")

    def blob(a: dict) -> str:
        return " ".join(str(a.get(k, "")) for k in ["id", "bereich", "titel", "quelle", "notiz"]).strip()

    def ist_test_oder_ocr(a: dict) -> bool:
        b = blob(a).lower()
        return any(m in b for m in [
            "regressionstest", "regression prüfen", "ocr-prüfung", "ocr manuell prüfen",
            "ocr-qualität", "ocr_qualitaet", "manuelle prüfung erforderlich"
        ])

    def finde_pdf_name(a: dict) -> str:
        b = blob(a)
        patterns = [
            r"Regressionstest\s+([^\n\r]+?\.pdf)",
            r"Regression prüfen:\s*([^\n\r]+?\.pdf)",
            r"OCR manuell prüfen:\s*([^\n\r]+?\.pdf)",
            r"Dokument:\s*([^\n\r]+?\.pdf)",
            r"Quelle:\s*Regressionstest\s+([^\n\r]+?\.pdf)",
            r"([^/\\\n\r]+?\.pdf)",
        ]
        for pat in patterns:
            m = re.search(pat, b, re.IGNORECASE)
            if m:
                return Path(m.group(1).strip()).name
        return ""

    def pdf_vorhanden(pdf_name: str) -> bool:
        if not pdf_name:
            return False
        p = Path(pdf_name)
        return p.name.strip().lower() in vorhandene_pdfs or p.stem.strip().lower() in vorhandene_stems

    for a in aufgaben:
        if not isinstance(a, dict):
            continue
        if not _pc_status_aktiv_2727(a):
            continue
        if not ist_test_oder_ocr(a):
            continue

        pdf_name = finde_pdf_name(a)
        # Bekannter Alt-Zombie pc-061 plus allgemeine OCR/Regression ohne vorhandenes Test-PDF.
        force_zombie = str(a.get("id", "")).strip().lower() == "pc-061"
        if force_zombie or not pdf_vorhanden(pdf_name):
            a["status"] = "erledigt"
            a["aktualisiert"] = jetzt
            notiz = str(a.get("notiz", ""))
            hinweis = f"\n\nAutomatisch erledigt: Zombie-/verwaiste Testaufgabe ohne sichtbares Test-PDF ({pdf_name or 'kein PDF-Name'}) am {jetzt}."
            if "Zombie-/verwaiste Testaufgabe" not in notiz[-2500:]:
                a["notiz"] = (notiz + hinweis).strip()
            changed = True

    if changed:
        try:
            PROJEKT_ORDNER.mkdir(parents=True, exist_ok=True)
            PROJEKT_AUFGABEN_DATEI.write_text(json.dumps(aufgaben, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception as exc:
            try:
                logging.warning("Konnte Zombie-Aufgaben nicht speichern: %s", exc)
            except Exception:
                pass
    return aufgaben

def projekt_speichere_aufgaben(aufgaben: list[dict]) -> None:
    PROJEKT_ORDNER.mkdir(parents=True, exist_ok=True)
    PROJEKT_AUFGABEN_DATEI.write_text(json.dumps(aufgaben, ensure_ascii=False, indent=2), encoding="utf-8")


def projekt_naechste_id(aufgaben: list[dict]) -> str:
    nr = 1
    for aufgabe in aufgaben:
        m = re.search(r"pc-(\d+)", str(aufgabe.get("id", "")))
        if m:
            nr = max(nr, int(m.group(1)) + 1)
    return f"pc-{nr:03d}"


def projekt_aktive_sichtbare_aufgaben(aufgaben: list[dict] | None = None) -> list[dict]:
    """Aktive Aufgaben, die wirklich in der Projektcenter-Aktivansicht erscheinen.

    Wichtig für V2.7.21: Kacheln, Dashboard und Testcenter benutzen dieselbe
    Logik wie die Aufgabenliste. Verwaiste Regression/OCR-Aufgaben ohne PDF
    werden deshalb weder angezeigt noch gezählt.
    """
    if aufgaben is None:
        aufgaben = projekt_lade_aufgaben()
    return [a for a in aufgaben if _pc_status_aktiv_2727(a)]


def projekt_statistik() -> dict:
    aufgaben = projekt_lade_aufgaben()
    aktive = projekt_aktive_sichtbare_aufgaben(aufgaben)
    return {
        # gesamt meint bewusst: aktuell sichtbare aktive Aufgaben, nicht Archiv/Zombie
        "gesamt": len(aktive),
        "offen": sum(1 for a in aktive if a.get("status") == "offen"),
        "in_arbeit": sum(1 for a in aktive if a.get("status") == "in_arbeit"),
        "erledigt": sum(1 for a in aufgaben if a.get("status") == "erledigt"),
        "hoch": sum(1 for a in aktive if a.get("prioritaet") == "hoch"),
        "verwaist": len(projekt_verwaiste_testaufgaben(aufgaben)),
        "alle": len(aufgaben),
    }


def projekt_task_pdf_name(a: dict) -> str:
    """Ermittelt den PDF-Dateinamen aus einer Projektaufgabe."""
    blob = " ".join(str(a.get(k, "")) for k in ["quelle", "titel", "notiz"])
    patterns = [
        r"Regressionstest\s+([^\n\r]+?\.pdf)",
        r"Regression prüfen:\s*([^\n\r]+?\.pdf)",
        r"OCR manuell prüfen:\s*([^\n\r]+?\.pdf)",
        r"([^/\\\n\r]+?\.pdf)",
    ]
    for pat in patterns:
        m = re.search(pat, blob, re.IGNORECASE)
        if m:
            return Path(m.group(1).strip()).name
    return ""


def projekt_ist_testaufgabe(a: dict) -> bool:
    """Erkennt Regressionstest-/OCR-Prüfaufgaben auch dann, wenn ältere
    WebUI-Versionen den Bereich nicht sauber gesetzt haben.
    """
    bereich = str(a.get("bereich", ""))
    if bereich in {"Regressionstest", "OCR-Prüfung"}:
        return True
    blob = " ".join(str(a.get(k, "")) for k in ["titel", "quelle", "notiz"]).lower()
    marker = [
        "regression prüfen",
        "regressionstest",
        "ocr manuell prüfen",
        "ocr-qualität",
        "ocr_qualitaet",
        "manuelle prüfung erforderlich",
    ]
    return any(m in blob for m in marker)


def projekt_test_pdf_existiert(pdf_name: str) -> bool:
    if not pdf_name:
        return False
    return (TEST_DIR / Path(pdf_name).name).exists()


def projekt_verwaiste_testaufgaben(aufgaben: list[dict] | None = None) -> list[dict]:
    """Aktive Regression/OCR-Aufgaben, deren PDF im Testcenter fehlt.

    V2.7.20: auch ältere/kaputte OCR-Aufgaben werden erkannt, wenn kein
    sauberer Bereich gesetzt wurde oder der Dateiname nur im langen Notiztext
    vorkommt. Falls gar kein PDF-Name mehr ableitbar ist, wird eine aktive
    OCR-/Regression-Aufgabe ebenfalls als verwaist gewertet, weil sie im
    Testcenter keinem Dokument mehr zugeordnet werden kann.
    """
    if aufgaben is None:
        aufgaben = projekt_lade_aufgaben()
    verwaist = []
    for a in aufgaben:
        if not projekt_ist_testaufgabe(a):
            continue
        if not _pc_status_aktiv_2727(a):
            continue
        pdf_name = projekt_task_pdf_name(a)
        if pdf_name:
            if not projekt_test_pdf_existiert(pdf_name):
                verwaist.append(a)
        else:
            # Alte OCR-Aufgaben ohne eindeutigen Dateinamen können nicht mehr
            # im Testcenter aufgelöst werden und sollen nicht dauerhaft aktiv bleiben.
            blob = " ".join(str(a.get(k, "")) for k in ["titel", "quelle", "notiz"]).lower()
            if any(m in blob for m in ["ocr-qualität", "ocr_qualitaet", "regression", "manuelle prüfung erforderlich"]):
                verwaist.append(a)
    return verwaist


def projekt_task_html(a: dict, current_status_filter: str = "alle", current_bereich_filter: str = "alle") -> str:
    status = str(a.get("status", "offen") or "offen")
    prioritaet = str(a.get("prioritaet", "mittel") or "mittel")
    aufgaben_id = str(a.get("id", ""))
    titel = str(a.get("titel", ""))
    icon = "⬜"
    card_class = ""
    if status == "in_arbeit":
        icon = "➜"
        card_class = "open-box"
    elif status == "erledigt":
        icon = "✓"
        card_class = "done-box"
    elif prioritaet == "hoch":
        icon = "⚠"
        card_class = "open-box"

    def opt(value: str, label: str) -> str:
        selected = " selected" if status == value else ""
        return f"<option value='{esc(value)}'{selected}>{esc(label)}</option>"

    regression_passed_button = ""
    if str(a.get("bereich", "")) == "Regressionstest" and status != "erledigt":
        regression_passed_button = (
            f"<form method='post' action='/projekt/regression-passed' style='margin-top:10px' "
            f"data-confirm-title='Regression bestanden markieren?' "
            f"data-confirm-message='Diese Regressionstest-Aufgabe wird als bestanden erledigt.' "
            f"data-confirm-details='Referenz sind die gespeicherten Sollwerte des Testdokuments. Die Aufgabe verschwindet anschließend aus den aktiven Regressionen.' "
            f"data-confirm-kind='eco-modal-success' data-confirm-ok='Ja, bestanden'>"
            f"<input type='hidden' name='id' value='{esc(aufgaben_id)}'>"
            f"<input type='hidden' name='return_status' value='{esc(current_status_filter)}'>"
            f"<input type='hidden' name='return_bereich' value='{esc(current_bereich_filter)}'>"
            f"<button class='btn success' type='submit'>✓ Test bestanden</button></form>"
        )

    return f"""
    <div class='card {card_class} project-task-card'>
      <div style='font-size:34px;text-align:center'>{icon}<div class='small muted'>{esc(status.replace("_", " "))}</div></div>
      <div class='project-task-main'>
        <h3 style='margin-top:0'>{esc(titel)}</h3>
        <p><span class='pill'>{esc(a.get("bereich", ""))}</span> <span class='pill'>Priorität: {esc(prioritaet)}</span> <span class='pill'>Status: {esc(status.replace("_", " "))}</span></p>
        <div class='project-task-note'>{esc(a.get("notiz", ""))}</div>
        <p class='small muted'>Quelle: {esc(a.get("quelle", ""))} · Aktualisiert: {esc(a.get("aktualisiert", ""))} · ID: {esc(aufgaben_id)}</p>
      </div>
      <div class='project-task-actions'>
        <form method='post' action='/projekt/status'>
          <input type='hidden' name='id' value='{esc(aufgaben_id)}'>
          <input type='hidden' name='return_status' value='{esc(current_status_filter)}'>
          <input type='hidden' name='return_bereich' value='{esc(current_bereich_filter)}'>
          <select name='status' style='width:100%'>
            {opt('offen', 'offen')}
            {opt('in_arbeit', 'in Arbeit')}
            {opt('erledigt', 'erledigt')}
          </select><br><br>
          <button class='btn2' type='submit'>Status speichern</button>
        </form>
        <form method='post' action='/projekt/delete' style='margin-top:10px' data-confirm-title='Aufgabe löschen?' data-confirm-message='Diese Aufgabe wirklich löschen?' data-confirm-details='{esc(titel)}' data-confirm-kind='eco-modal-danger' data-confirm-ok='Ja, löschen'>
          <input type='hidden' name='id' value='{esc(aufgaben_id)}'>
          <input type='hidden' name='return_status' value='{esc(current_status_filter)}'>
          <input type='hidden' name='return_bereich' value='{esc(current_bereich_filter)}'>
          <button class='btn2 danger' type='submit'>Löschen</button>
        </form>
      </div>
    </div>
    """


@app.get("/projekt", response_class=HTMLResponse)
def projektcenter(status: str = "aktiv", bereich: str = "alle", created: str = "", suche: str = "") -> HTMLResponse:
    alle = projekt_lade_aufgaben()
    verwaiste_aktive = projekt_verwaiste_testaufgaben(alle)
    verwaiste_ids = {str(a.get("id", "")) for a in verwaiste_aktive}
    aufgaben = list(alle)
    if status == "aktiv":
        aufgaben = projekt_aktive_sichtbare_aufgaben(alle)
    elif status != "alle":
        aufgaben = [a for a in aufgaben if a.get("status") == status]
    if bereich != "alle":
        aufgaben = [a for a in aufgaben if a.get("bereich") == bereich]
    suche_norm = (suche or "").strip()
    if suche_norm:
        needle = suche_norm.lower()
        aufgaben = [a for a in aufgaben if needle in " ".join(str(a.get(k, "")) for k in ["id", "titel", "bereich", "quelle", "notiz"]).lower()]

    stats = projekt_statistik()
    bereiche = sorted(set(a.get("bereich", "Sonstiges") for a in alle))
    bereich_options = "".join(f"<option value='{esc(b)}' {'selected' if bereich == b else ''}>{esc(b)}</option>" for b in bereiche)
    tasks = "".join(projekt_task_html(a, status, bereich) for a in aufgaben) if aufgaben else "<div class='card'><p class='muted'>Keine Aufgaben passend zum Filter.</p></div>"

    fachlich_back_html = ''
    if suche_norm:
        related_task = next((a for a in alle if str(a.get("id", "")).strip() == suche_norm), None)
        row_id = ""
        if related_task and (str(related_task.get("bereich", "")).strip().lower() == "massentest" or "massentest" in str(related_task.get("quelle", "")).lower()):
            try:
                for r in massentest_read_results():
                    if str(r.get("aufgabe_id", "")).strip() == suche_norm:
                        row_id = str(r.get("id", "") or "").strip()
                        break
            except Exception:
                row_id = ""
            if not row_id:
                m = re.search(r"/test/massentest/(?:fachlich|detail|result)/([^\s?]+)", str(related_task.get("notiz", "")))
                if m:
                    row_id = m.group(1).strip()
        if row_id:
            fachlich_back_html = f"<div class='created-backbar'><div><b>Massentest-Aufgabe:</b> {esc(suche_norm)}</div><div><a class='btn' href='/test/massentest/fachlich/{quote(row_id)}'>← Zur fachlichen Prüfung zurück</a></div></div>"

    created_html = ''
    if created:
        created_html = f"<div class='created-backbar'><div><b>Aufgabe angelegt/aktualisiert:</b> {esc(Path(created).name)}</div><div><a class='btn' href='/test'>← Zurück zur Dokumentenprüfung</a> <a class='btn2' href='/projekt?status=aktiv&bereich=Regressionstest'>Regressionstest-Aufgaben</a></div></div>"
    elif bereich == 'Regressionstest':
        created_html = "<div class='created-backbar'><div><b>Regressionstest-Aufgaben</b></div><div><a class='btn' href='/test'>← Zurück zur Dokumentenprüfung</a></div></div>"

    orphan_html = ''
    if verwaiste_aktive:
        details = '<br>'.join(esc(f"{a.get('id','')} · {projekt_task_pdf_name(a)} · {a.get('titel','')}") for a in verwaiste_aktive[:12])
        if len(verwaiste_aktive) > 12:
            details += f"<br>… und {len(verwaiste_aktive)-12} weitere"
        orphan_html = f"""
        <div class='card' style='border-left:6px solid #d97706;background:#fffbeb'>
          <h2>⚠ Verwaiste Testaufgaben</h2>
          <p>Es gibt {len(verwaiste_aktive)} aktive Regression/OCR-Aufgabe(n), deren PDF im Testcenter nicht mehr vorhanden ist. Diese werden in der aktiven Ansicht ausgeblendet und können hier gesammelt erledigt werden.</p>
          <div class='muted small'>{details}</div>
          <form method='post' action='/projekt/cleanup-orphans' data-confirm-title='Verwaiste Testaufgaben erledigen?' data-confirm-message='Alle aktiven Regression/OCR-Aufgaben ohne vorhandenes Test-PDF werden auf erledigt gesetzt.' data-confirm-details='Die Aufgaben werden nicht gelöscht, sondern mit Hinweis als erledigt markiert. Dadurch verschwinden sie aus den aktiven Aufgaben.' data-confirm-kind='eco-modal-warning' data-confirm-ok='Ja, erledigen'>
            <button class='btn warn' type='submit'>Verwaiste Aufgaben erledigen</button>
          </form>
        </div>
        """

    body = f"""
    {fachlich_back_html}
    {created_html}
    {orphan_html}
    <div class='card'>
      <div class='section-head'><h2>Projektcenter</h2><span class='count-badge'>Aufgaben / Planung</span></div>
      <p class='muted'>Zentraler Bereich für Aufgaben, Roadmap, Sprintplanung sowie Release- und Buildstände. Tests und fachliche Dokumentenarbeit liegen in der Dokumentenprüfung.</p>
    </div>
    <div class='grid'>
      <div class='card'><h2>{stats['offen']}</h2><p>Offen</p></div>
      <div class='card'><h2>{stats['in_arbeit']}</h2><p>In Arbeit</p></div>
      <div class='card'><h2>{stats['erledigt']}</h2><p>Erledigt / Archiv</p></div>
      <div class='card'><h2>{stats['hoch']}</h2><p>Hohe Priorität offen</p></div>
    </div>
    <div class='card'><h2>Legende</h2><p>⬜ offen &nbsp;&nbsp; ➜ in Arbeit &nbsp;&nbsp; ✓ erledigt &nbsp;&nbsp; ⚠ hohe Priorität</p></div>
    <div class='card' style='border-left:6px solid #2563eb'>
      <h2>Regressionen für ChatGPT</h2>
      <p class='muted'>Alle offenen und in Arbeit befindlichen Regressionstest-Aufgaben gesammelt als Kopiervorlage.</p>
      <p><a class='btn' href='/test/chatgpt-active'>📋 Aktive Regressionen für ChatGPT</a> <a class='btn2' href='/projekt?status=aktiv&bereich=Regressionstest'>Nur Regressionstest-Aufgaben</a></p>
    </div>
    <div class='card'>
      <h2>Filtern</h2>
      <form method='get'>
        <select name='status'>
          <option value='aktiv' {'selected' if status == 'aktiv' else ''}>Offen + in Arbeit</option>
          <option value='alle' {'selected' if status == 'alle' else ''}>Alle Status</option>
          <option value='offen' {'selected' if status == 'offen' else ''}>Offen</option>
          <option value='in_arbeit' {'selected' if status == 'in_arbeit' else ''}>In Arbeit</option>
          <option value='erledigt' {'selected' if status == 'erledigt' else ''}>Erledigt / Archiv</option>
        </select>
        <select name='bereich'><option value='alle' {'selected' if bereich == 'alle' else ''}>Alle Bereiche</option>{bereich_options}</select>
        <button class='btn2' type='submit'>Filtern</button>
      </form>
    </div>
    {"<div class='active-filter-note'>Angezeigt werden nur aktive Aufgaben: offen und in Arbeit. Erledigte Aufgaben findest du über den Filter „Alle Status“ oder „Erledigt / Archiv“.</div>" if status == "aktiv" else ""}
    <h2>Aufgaben</h2>
    {tasks}
    <details class='card'>
      <summary style='font-weight:800;font-size:18px;cursor:pointer'>+ Neue Aufgabe anlegen</summary>
      <div style='margin-top:14px'>
        <form method='post' action='/projekt/neu'>
          <p><input type='text' name='titel' placeholder='Titel' style='width:100%' required></p>
          <p><input type='text' name='bereich' value='Scan-Service'> <select name='prioritaet'><option value='hoch'>hoch</option><option value='mittel' selected>mittel</option><option value='niedrig'>niedrig</option></select></p>
          <p><input type='text' name='quelle' placeholder='Quelle, z.B. Regressionstest ADAC.pdf' style='width:100%'></p>
          <p><textarea name='notiz' placeholder='Notiz optional' style='height:48px;min-height:48px'></textarea></p>
          <button class='btn' type='submit'>Aufgabe anlegen</button>
        </form>
      </div>
    </details>
    """
    return layout("Projektcenter", body)


@app.post("/projekt/neu")
def projekt_neu(titel: str = Form(...), bereich: str = Form("Scan-Service"), prioritaet: str = Form("mittel"), quelle: str = Form(""), notiz: str = Form("")):
    aufgaben = projekt_lade_aufgaben()
    jetzt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    aufgaben.append({
        "id": projekt_naechste_id(aufgaben),
        "titel": titel.strip(),
        "bereich": bereich.strip() or "Sonstiges",
        "status": "offen",
        "prioritaet": prioritaet.strip() or "mittel",
        "quelle": quelle.strip(),
        "notiz": notiz.strip(),
        "erstellt": jetzt,
        "aktualisiert": jetzt,
    })
    projekt_speichere_aufgaben(aufgaben)
    return RedirectResponse("/projekt?status=aktiv", status_code=303)


def projekt_redirect_url(return_status: str = "alle", return_bereich: str = "alle") -> str:
    status = return_status if return_status in {"aktiv", "alle", "offen", "in_arbeit", "erledigt"} else "aktiv"
    bereich = (return_bereich or "alle").strip() or "alle"
    return f"/projekt?status={status}&bereich={bereich}"


@app.post("/projekt/status")
def projekt_status(
    id: str = Form(...),
    status: str = Form(...),
    return_status: str = Form("alle"),
    return_bereich: str = Form("alle"),
):
    erlaubte_status = {"offen", "in_arbeit", "erledigt"}
    if status not in erlaubte_status:
        raise HTTPException(status_code=400, detail="Ungültiger Aufgabenstatus")

    aufgaben = projekt_lade_aufgaben()
    gefunden = False
    for aufgabe in aufgaben:
        if str(aufgabe.get("id")) == str(id):
            aufgabe["status"] = status
            aufgabe["aktualisiert"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            gefunden = True
            break

    if not gefunden:
        raise HTTPException(status_code=404, detail="Aufgabe nicht gefunden")

    projekt_speichere_aufgaben(aufgaben)
    return RedirectResponse(projekt_redirect_url(return_status, return_bereich), status_code=303)


@app.post("/projekt/delete")
def projekt_delete(
    id: str = Form(...),
    return_status: str = Form("alle"),
    return_bereich: str = Form("alle"),
):
    aufgaben = projekt_lade_aufgaben()
    neue_aufgaben = [a for a in aufgaben if str(a.get("id")) != str(id)]

    if len(neue_aufgaben) == len(aufgaben):
        raise HTTPException(status_code=404, detail="Aufgabe nicht gefunden")

    projekt_speichere_aufgaben(neue_aufgaben)
    return RedirectResponse(projekt_redirect_url(return_status, return_bereich), status_code=303)




@app.post("/projekt/cleanup-orphans")
def projekt_cleanup_orphans():
    """Setzt verwaiste aktive Regression/OCR-Aufgaben auf erledigt."""
    aufgaben = projekt_lade_aufgaben()
    verwaiste = projekt_verwaiste_testaufgaben(aufgaben)
    ids = {str(a.get("id", "")) for a in verwaiste}
    jetzt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    changed = 0
    for a in aufgaben:
        if str(a.get("id", "")) in ids and str(a.get("status", "offen")) != "erledigt":
            a["status"] = "erledigt"
            a["aktualisiert"] = jetzt
            pdf_name = projekt_task_pdf_name(a)
            notiz = str(a.get("notiz", ""))
            hinweis = f"\n\nAutomatisch erledigt: Verwaiste Testaufgabe ohne vorhandenes Test-PDF ({pdf_name}) am {jetzt}."
            if "Verwaiste Testaufgabe" not in notiz[-1000:]:
                a["notiz"] = (notiz + hinweis).strip()
            changed += 1
    if changed:
        projekt_speichere_aufgaben(aufgaben)
    return RedirectResponse("/projekt?status=aktiv&bereich=alle", status_code=303)


def projekt_markiere_regression_erledigt(pdf_name: str, grund: str = "Regressionstest erfolgreich") -> int:
    """Setzt passende Test-Aufgaben automatisch auf erledigt.

    Wichtig für Sonderfälle: Wenn ein Dokument bewusst als bestanden markiert wird,
    müssen nicht nur Regressionstest-Aufgaben erledigt werden, sondern auch eventuell
    automatisch erzeugte OCR-Prüfaufgaben zum selben PDF. Erkannt wird robust über
    den PDF-Dateinamen in Titel, Quelle oder Notiz.
    """
    pdf_name = Path(pdf_name).name
    if not pdf_name:
        return 0

    needle = pdf_name.lower()
    stem = Path(pdf_name).stem.lower()
    jetzt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    aufgaben = projekt_lade_aufgaben()
    changed = 0

    for a in aufgaben:
        bereich = str(a.get("bereich", ""))
        if bereich not in {"Regressionstest", "OCR-Prüfung"}:
            continue

        blob = " ".join(str(a.get(k, "")) for k in ["titel", "quelle", "notiz"]).lower()
        passt = needle in blob or (stem and stem in blob)
        if not passt:
            continue

        if str(a.get("status", "offen")) != "erledigt":
            a["status"] = "erledigt"
            a["aktualisiert"] = jetzt
            hinweis = f"\n\nAutomatisch erledigt: {grund} am {jetzt}."
            notiz = str(a.get("notiz", ""))
            if "Automatisch erledigt:" not in notiz[-700:] and "Manuell als bestanden markiert" not in notiz[-700:]:
                a["notiz"] = (notiz + hinweis).strip()
            changed += 1

    if changed:
        projekt_speichere_aufgaben(aufgaben)
    return changed


def projekt_regression_reaktivieren(pdf_name: str) -> int:
    """Reaktiviert erledigte Regressionstest-Aufgaben bei erneuter Abweichung."""
    pdf_name = Path(pdf_name).name
    if not pdf_name:
        return 0
    if is_manual_test_passed(pdf_name):
        return 0
    needle = pdf_name.lower()
    jetzt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    aufgaben = projekt_lade_aufgaben()
    changed = 0
    for a in aufgaben:
        if str(a.get("bereich", "")) != "Regressionstest":
            continue
        blob = " ".join(str(a.get(k, "")) for k in ["titel", "quelle", "notiz"]).lower()
        if needle in blob and str(a.get("status", "offen")) == "erledigt":
            a["status"] = "offen"
            a["aktualisiert"] = jetzt
            changed += 1
    if changed:
        projekt_speichere_aufgaben(aufgaben)
    return changed

def projekt_finde_aufgabe_index(aufgaben: list[dict], titel: str, quelle: str) -> int | None:
    """Findet eine vorhandene Regressionstest-Aufgabe robuster.

    V2.6.4:
    Alte Aufgaben aus früheren WebUI-Versionen hatten teilweise leicht andere
    Titel/Quellen. Deshalb reicht jetzt derselbe PDF-Dateiname in Titel, Quelle
    oder Notiz. So wird die Aufgabe aktualisiert statt blockiert.
    """
    titel_n = (titel or "").strip().lower()
    quelle_n = (quelle or "").strip().lower()
    pdf_name = ""
    m = re.search(r"Regression(?: prüfen|stest)?[: ]+(.+?\.pdf)", titel or quelle, re.IGNORECASE)
    if m:
        pdf_name = Path(m.group(1)).name.lower()
    else:
        m = re.search(r"([^/\\]+\.pdf)", (titel or "") + " " + (quelle or ""), re.IGNORECASE)
        if m:
            pdf_name = Path(m.group(1)).name.lower()

    for i, a in enumerate(aufgaben):
        a_titel = str(a.get("titel", "")).strip().lower()
        a_quelle = str(a.get("quelle", "")).strip().lower()
        a_notiz = str(a.get("notiz", "")).strip().lower()
        if a_titel == titel_n and a_quelle == quelle_n:
            return i
        if pdf_name and (pdf_name in a_titel or pdf_name in a_quelle or pdf_name in a_notiz):
            if "regression" in (a_titel + " " + a_quelle + " " + a_notiz):
                return i
    return None


def projekt_ocr_manuell_aufgabe(filename: str, debug_text: str = "") -> None:
    """Legt/aktualisiert eine Aufgabe für unleserliche OCR an."""
    pdf_name = Path(filename).name
    titel = f"OCR manuell prüfen: {pdf_name}"
    quelle = f"Regressionstest {pdf_name}"
    notiz = (
        "OCR-QUALITÄT: UNLESERLICH\n"
        "Automatische Klassifizierung nicht zuverlässig möglich. Dokument manuell prüfen.\n\n"
        "Debug-Auszug:\n" + str(debug_text or "")[:5000]
    )
    aufgaben = projekt_lade_aufgaben()
    jetzt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    idx = projekt_finde_aufgabe_index(aufgaben, titel, quelle)
    if idx is None:
        aufgaben.append({
            "id": projekt_naechste_id(aufgaben),
            "titel": titel,
            "bereich": "OCR-Prüfung",
            "status": "offen",
            "prioritaet": "hoch",
            "quelle": quelle,
            "notiz": notiz,
            "erstellt": jetzt,
            "aktualisiert": jetzt,
        })
    else:
        aufgabe = aufgaben[idx]
        aufgabe["bereich"] = "OCR-Prüfung"
        aufgabe["prioritaet"] = "hoch"
        aufgabe["notiz"] = notiz
        aufgabe["aktualisiert"] = jetzt
        if str(aufgabe.get("status")) == "erledigt":
            aufgabe["status"] = "offen"
        aufgaben[idx] = aufgabe
    projekt_speichere_aufgaben(aufgaben)


@app.post("/projekt/aus-regression")
def projekt_aus_regression(filename: str = Form(...), delta: str = Form(""), return_to: str = Form("projekt")):
    """Übernimmt eine Regressionstest-Abweichung direkt ins Projektcenter.

    V2.6.3: Wiederholte Tests aktualisieren die vorhandene Aufgabe.
    Dadurch bleiben Testaufgaben aktuell und müssen nicht vorher gelöscht werden.
    """
    pdf_name = Path(filename).name
    titel = f"Regression prüfen: {pdf_name}"
    quelle = f"Regressionstest {pdf_name}"
    notiz = (delta or "").strip()
    if not notiz:
        notiz = "Aus dem Testcenter wurde eine Abweichung gemeldet. Bitte Soll-/Ist-Werte prüfen."
    if len(notiz) > 8000:
        notiz = notiz[:8000] + "\n... [gekürzt]"

    aufgaben = projekt_lade_aufgaben()
    jetzt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    idx = projekt_finde_aufgabe_index(aufgaben, titel, quelle)
    if idx is None:
        aufgaben.append({
            "id": projekt_naechste_id(aufgaben),
            "titel": titel,
            "bereich": "Regressionstest",
            "status": "offen",
            "prioritaet": "hoch",
            "quelle": quelle,
            "notiz": notiz,
            "erstellt": jetzt,
            "aktualisiert": jetzt,
        })
    else:
        aufgabe = aufgaben[idx]
        alt_status = str(aufgabe.get("status", "offen"))
        aufgabe["bereich"] = "Regressionstest"
        aufgabe["prioritaet"] = "hoch"
        aufgabe["notiz"] = notiz
        aufgabe["aktualisiert"] = jetzt
        # Wenn eine erledigte Aufgabe wieder eine Abweichung bekommt, wird sie reaktiviert.
        if alt_status == "erledigt":
            aufgabe["status"] = "offen"
        elif alt_status not in {"offen", "in_arbeit"}:
            aufgabe["status"] = "offen"
        aufgaben[idx] = aufgabe
    projekt_speichere_aufgaben(aufgaben)
    return RedirectResponse(f"/projekt?status=aktiv&bereich=Regressionstest&created={pdf_name}", status_code=303)



@app.post("/test/mark-passed")
def test_mark_passed(filename: str = Form(...), return_to: str = Form("test")):
    """Markiert einen Regressionstest bewusst als bestanden.

    Für Ausreißer mit unleserlicher OCR kann der Nutzer die Sollwerte manuell setzen
    und anschließend den Testfall bewusst freigeben. Die passende Projektaufgabe wird
    erledigt, der Teststatus wird als bestanden dokumentiert.
    """
    pdf_name = Path(filename).name
    write_manual_test_status(pdf_name, "Manuell bestanden: Referenz sind die aktuell gespeicherten Sollwerte", get_scan_service_version())
    projekt_markiere_regression_erledigt(pdf_name, "manuell als bestanden markiert")
    if return_to == "projekt":
        return RedirectResponse("/projekt?status=aktiv&bereich=Regressionstest", status_code=303)
    return RedirectResponse("/test/einzeltest#erfolgreich", status_code=303)


@app.post("/projekt/regression-passed")
def projekt_regression_passed(id: str = Form(...), return_status: str = Form("aktiv"), return_bereich: str = Form("Regressionstest")):
    """Setzt eine Regressionstest-Aufgabe manuell auf erledigt/bestanden."""
    aufgaben = projekt_lade_aufgaben()
    jetzt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    pdf_name = ""
    for a in aufgaben:
        if str(a.get("id", "")) == str(id):
            a["status"] = "erledigt"
            a["aktualisiert"] = jetzt
            notiz = str(a.get("notiz", ""))
            if "Manuell als bestanden markiert" not in notiz[-700:]:
                a["notiz"] = (notiz + f"\n\nManuell als bestanden markiert am {jetzt}.").strip()
            # PDF-Dateiname aus Quelle/Titel ableiten, soweit vorhanden.
            blob = str(a.get("quelle", "")) + " " + str(a.get("titel", ""))
            m = re.search(r"Regressionstest\s+(.+?\.pdf)", blob, re.IGNORECASE)
            if m:
                pdf_name = Path(m.group(1)).name
            break
    projekt_speichere_aufgaben(aufgaben)
    if pdf_name:
        write_test_status(pdf_name, "geprueft_ok", "Projektaufgabe bestanden: Referenz sind die gespeicherten Sollwerte", get_scan_service_version())
        # Auch mögliche OCR-Prüfaufgaben zum selben Dokument erledigen.
        projekt_markiere_regression_erledigt(pdf_name, "Projektaufgabe manuell als bestanden markiert")
    return RedirectResponse(f"/projekt?status={return_status}&bereich={return_bereich}", status_code=303)


@app.get("/regression", response_class=HTMLResponse)
def regression_page() -> HTMLResponse:
    """Sichere Platzhalterseite für den vorbereiteten Produktivbereich."""
    body = """
    <div class='card result-focus'>
      <div class='section-head'><h2>Produktivcenter</h2><span class='area-badge area-produktiv'>PRODUKTIV</span></div>
      <p class='hint'><b>Produktivbereich ist vorbereitet, produktive Aktionen sind noch gesperrt.</b></p>
      <p class='muted'>Diese Seite bündelt später Produktivfreigabe und Betriebsübergang. In der Alpha bleiben alle aktiven Tests und Regressionen in der Dokumentenprüfung.</p>
      <div class='grid'>
        <a class='hint' href='/test/massentest' style='display:block;text-decoration:none;color:inherit'><b>Massentest</b><br><span class='muted small'>Referenzen und fachliche Prüfung öffnen.</span></a>
        <a class='hint' href='/test/einzeltest' style='display:block;text-decoration:none;color:inherit'><b>Einzeldokument testen</b><br><span class='muted small'>Vorhandenen Testbereich für einzelne PDFs nutzen.</span></a>
        <a class='hint' href='/test/chatgpt-active' style='display:block;text-decoration:none;color:inherit'><b>Berichte / Auswertungen</b><br><span class='muted small'>Aufgaben- und Regressionsexport anzeigen.</span></a>
        <a class='hint' href='/projekt?status=aktiv&bereich=Regressionstest' style='display:block;text-decoration:none;color:inherit'><b>Regression-Aufgaben</b><br><span class='muted small'>Vorhandene Aufgaben im Projektcenter öffnen.</span></a>
      </div>
    </div>
    """
    return layout("Produktivcenter", body)



def massentest_cleanup_finished_tasks() -> int:
    """Schließt aktive Massentest-Aufgaben, wenn der zugehörige Massentest-Datensatz keine fachliche Abweichung mehr hat."""
    try:
        rows = massentest_read_results()
        aufgaben = projekt_lade_aufgaben()
        changed = 0
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for row in rows:
            soll_count, diffs = massentest_diff_details(row)
            if not soll_count or diffs:
                continue
            idx = massentest_existing_task_index(aufgaben, row)
            if idx is None:
                continue
            a = dict(aufgaben[idx])
            if str(a.get("bereich", "")).strip().lower() != "massentest" and "massentest" not in str(a.get("quelle", "")).lower():
                continue
            if _pc_status_aktiv_2727(a):
                aid = str(a.get("id", ""))
                a["status"] = "erledigt"
                a["aktualisiert"] = now
                note = str(a.get("notiz", "") or "")
                if "Automatisch erledigt" not in note[-1000:]:
                    a["notiz"] = (note + f"\n\n[Automatisch erledigt {now}] Massentest fehlerfrei: Soll/Ist identisch.").strip()
                aufgaben[idx] = a
                if str(row.get("aufgabe_id", "")) == aid:
                    row["aufgabe_id"] = ""
                changed += 1
        if changed:
            projekt_speichere_aufgaben(aufgaben)
            massentest_write_results(rows)
        return changed
    except Exception as e:
        try:
            massentest_log(f"AUFGABENBEREINIGUNG FEHLER: {e}")
        except Exception:
            pass
        return 0

@app.post("/test/massentest/cleanup-tasks")
def massentest_cleanup_tasks_route():
    changed = massentest_cleanup_finished_tasks()
    return RedirectResponse(url=f"/test/massentest?msg={quote(str(changed) + ' fehlerfreie Massentest-Aufgabe(n) wurden erledigt.')}", status_code=303)



def massentest_reconcile_active_tasks_for_export_371() -> int:
    """Synchronisiert Massentest-Ergebnisse und Projektaufgaben vor dem Export.

    Problem 3.7.0: Die Oberfläche zählt offene Massentest-Abweichungen direkt aus
    den Ergebniszeilen, der ChatGPT-Export liest dagegen nur Projektaufgaben.
    Dadurch konnte die Oberfläche z.B. 4 Fälle zeigen, der Export aber nur 3.

    Diese Funktion legt/aktualisiert fehlende Projektaufgaben für alle aktiven
    Massentest-Zeilen mit Abweichungen oder Prüfstatus Aufgabe/Abweichung.
    """
    try:
        rows = massentest_read_results()
        aufgaben = projekt_lade_aufgaben()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        changed = 0
        for row in rows:
            soll_count, diffs = massentest_diff_details(row)
            ps = str(row.get("pruefstatus", "") or "").strip().lower()
            active = bool(diffs) or ps in {"aufgabe", "abweichung", "fehler", "nicht_bestanden"}
            if not active:
                continue
            details = massentest_task_details(row)
            existing_idx = massentest_existing_task_index(aufgaben, row)
            if existing_idx is not None:
                a = dict(aufgaben[existing_idx])
                aid = str(a.get("id", "")) or projekt_naechste_id(aufgaben)
                new_status = str(a.get("status", "offen") or "offen").strip().lower()
                if new_status == "erledigt":
                    new_status = "offen"
                new_a = dict(a)
                new_a.update({
                    "id": aid,
                    "titel": f"Massentest prüfen: {row.get('alter_dateiname','PDF')}",
                    "bereich": "Massentest",
                    "status": new_status or "offen",
                    "prioritaet": a.get("prioritaet", "mittel") or "mittel",
                    "quelle": f"Massentest {row.get('alter_dateiname','')}",
                    "notiz": details,
                    "aktualisiert": now,
                })
                if not new_a.get("erstellt"):
                    new_a["erstellt"] = now
                if new_a != a:
                    aufgaben[existing_idx] = new_a
                    changed += 1
                row["aufgabe_id"] = aid
                row["pruefstatus"] = "aufgabe"
            else:
                aid = projekt_naechste_id(aufgaben)
                aufgaben.append({
                    "id": aid,
                    "titel": f"Massentest prüfen: {row.get('alter_dateiname','PDF')}",
                    "bereich": "Massentest",
                    "status": "offen",
                    "prioritaet": "mittel",
                    "quelle": f"Massentest {row.get('alter_dateiname','')}",
                    "notiz": details,
                    "erstellt": now,
                    "aktualisiert": now,
                })
                row["aufgabe_id"] = aid
                row["pruefstatus"] = "aufgabe"
                changed += 1
        if changed:
            projekt_speichere_aufgaben(aufgaben)
        massentest_write_results(rows)
        return changed
    except Exception as e:
        try:
            massentest_log(f"EXPORTGLEICHLAUF 3.7.1 FEHLER: {e}")
        except Exception:
            pass
        return 0

@app.get("/test/chatgpt-active", response_class=HTMLResponse)
def chatgpt_active_regressions(scope: str = "active", bereich: str = "Regressionstest") -> HTMLResponse:
    """Kopiervorlage für Projektcenter-Aufgaben.

    3.0.11: Der Export zeigt nun klar, welcher Bereich und welcher Umfang
    exportiert wird. Neben aktiven Regressionen können auch Massentest-Aufgaben
    oder alle Aufgaben exportiert werden.
    """
    if (scope or "active").strip().lower() == "active" and (bereich or "").strip().lower() in {"massentest", "alle", "all", ""}:
        massentest_cleanup_finished_tasks()
        massentest_reconcile_active_tasks_for_export_371()
    aufgaben = projekt_lade_aufgaben()
    scope = (scope or "active").strip().lower()
    bereich = (bereich or "Regressionstest").strip()

    def in_scope(a: dict) -> bool:
        if scope == "all":
            return True
        if scope == "done":
            return not _pc_status_aktiv_2727(a)
        return _pc_status_aktiv_2727(a)

    def in_bereich(a: dict) -> bool:
        if bereich.lower() in {"alle", "all", ""}:
            return True
        return str(a.get("bereich", "")).strip().lower() == bereich.lower()

    gefiltert = [a for a in aufgaben if in_scope(a) and in_bereich(a)]
    offene = [a for a in gefiltert if str(a.get("status", "offen")).strip().lower() == "offen"]
    in_arbeit = [a for a in gefiltert if str(a.get("status", "")).strip().lower() == "in_arbeit"]
    andere = [a for a in gefiltert if a not in offene and a not in in_arbeit]
    for gruppe in (offene, in_arbeit, andere):
        gruppe.sort(key=lambda a: (str(a.get("bereich", "")), str(a.get("quelle", "")), str(a.get("titel", ""))))

    def add_task(lines: list[str], a: dict) -> None:
        lines.extend([
            f"--- {a.get('id','')} · {a.get('status','')} · {a.get('bereich','')} ---",
            f"Titel: {a.get('titel','')}",
            f"Quelle: {a.get('quelle','')}",
            f"Priorität: {a.get('prioritaet','')}",
            f"Erstellt: {a.get('erstellt','')} · Aktualisiert: {a.get('aktualisiert','')}",
            "",
            str(a.get('notiz','')).strip(),
            "",
        ])

    title_scope = {"all":"ALLE", "done":"ERLEDIGTE", "active":"AKTIVE"}.get(scope, "AKTIVE")
    title_bereich = "ALLE BEREICHE" if bereich.lower() in {"alle", "all", ""} else bereich.upper()
    lines = [
        f"=== {title_scope} {title_bereich}-AUFGABEN ===",
        f"WebUI-Version: {APP_VERSION}",
        f"Scan-Service-Version: {get_scan_service_version()}",
        f"Zeitpunkt: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}",
        f"Export-Umfang: {scope}",
        f"Export-Bereich: {bereich}",
        f"Anzahl gesamt: {len(gefiltert)}",
        f"Neue/offene Aufgaben: {len(offene)}",
        f"In Arbeit: {len(in_arbeit)}",
        f"Weitere Status: {len(andere)}",
        "",
        "=== NEUE / OFFENE AUFGABEN ===",
    ]
    if offene:
        for a in offene:
            add_task(lines, a)
    else:
        lines += ["Keine neuen offenen Aufgaben.", ""]
    lines.append("=== IN ARBEIT ===")
    if in_arbeit:
        for a in in_arbeit:
            add_task(lines, a)
    else:
        lines += ["Keine Aufgaben in Arbeit.", ""]
    lines.append("=== WEITERE STATUS ===")
    if andere:
        for a in andere:
            add_task(lines, a)
    else:
        lines += ["Keine weiteren Aufgaben im gewählten Export.", ""]
    lines.append("=== ENDE ===")
    text = "\n".join(lines)

    def active_link(label: str, sc: str, be: str) -> str:
        cls = "btn" if sc == scope and be.lower() == bereich.lower() else "btn2"
        return f"<a class='{cls}' href='/test/chatgpt-active?scope={quote(sc)}&bereich={quote(be)}'>{esc(label)}</a>"

    body = f"""
    <div class='top-actions'><div><b>Aufgaben für ChatGPT</b><br><span class='muted small'>Export ist jetzt eindeutig nach Bereich und Umfang filterbar.</span></div><a class='btn2' href='/test'>← Zurück zur Dokumentenprüfung</a></div>
    <div class='card'>
      <h2>Export-Auswahl</h2>
      <div class='toolbar'>
        {active_link('Aktive Regressionen', 'active', 'Regressionstest')}
        {active_link('Aktive Massentest-Aufgaben', 'active', 'Massentest')}
        {active_link('Alle aktiven Aufgaben', 'active', 'alle')}
        {active_link('Alle Regressionen inkl. erledigt', 'all', 'Regressionstest')}
        {active_link('Alle Massentest-Aufgaben inkl. erledigt', 'all', 'Massentest')}
        {active_link('Alle Aufgaben komplett', 'all', 'alle')}
      </div>
    </div>
    <div class='grid'>
      <div class='card'><h2>{len(offene)}</h2><p>Neue / offene Aufgaben</p></div>
      <div class='card'><h2>{len(in_arbeit)}</h2><p>In Arbeit</p></div>
      <div class='card'><h2>{len(andere)}</h2><p>Weitere Status</p></div>
      <div class='card'><h2>{len(gefiltert)}</h2><p>Gesamt im Export</p></div>
    </div>
    <div class='card result-focus'>
      <h2>Kopiervorlage</h2>
      <p class='muted'>Gewählter Bereich: <b>{esc(bereich)}</b> · Umfang: <b>{esc(scope)}</b>. Es gibt keinen versteckten Filter mehr.</p>
      <p><button class='btn' type='button' onclick="copyText('active_regressions')">Alles für ChatGPT kopieren</button> <a class='btn2' href='/projekt?status=aktiv'>Projektaufgaben öffnen</a></p>
      <textarea id='active_regressions' class='copyarea' readonly>{esc(text)}</textarea>
    </div>
    """
    return layout("Aufgaben für ChatGPT", body)

def _pc_pdf_key_2727(a: dict) -> str:
    blob = " ".join(str(a.get(k, "")) for k in ["quelle", "titel", "notiz"])
    pats = [
        r"Regressionstest\s+([^\n\r]+?\.pdf)",
        r"Regression prüfen:\s*([^\n\r]+?\.pdf)",
        r"Dokument:\s*([^\n\r]+?\.pdf)",
        r"([^/\\\n\r]+?\.pdf)",
    ]
    for pat in pats:
        m = re.search(pat, blob, re.IGNORECASE)
        if m:
            return Path(m.group(1).strip()).name.lower()
    return ""


def _pc_sortwert_2727(a: dict) -> tuple:
    # Neuere/höhere IDs bevorzugen, weil sie aus aktuellem Testlauf stammen.
    aid = str(a.get("id", ""))
    m = re.search(r"pc-(\d+)", aid)
    nr = int(m.group(1)) if m else 0
    ts = str(a.get("aktualisiert") or a.get("erstellt") or "")
    return (ts, nr)



def _pc_status_aktiv_2727(a: dict) -> bool:
    """True, wenn eine Projektaufgabe noch aktiv ist.

    Nach dem Projektcenter-Umbau wurde diese Hilfsfunktion von der
    Duplikatbereinigung genutzt, war aber nicht in jeder Zwischenversion
    vorhanden. Ohne diese Funktion stürzt das Dashboard bereits beim
    Berechnen der Projektstatistik ab.
    """
    if not isinstance(a, dict):
        return False
    status = str(a.get("status", "offen") or "offen").strip().lower()
    return status not in {"erledigt", "done", "geschlossen", "closed", "archiv", "archiviert", "gelöscht", "geloescht"}

def projekt_normalisiere_doppelte_regressionen_2727(aufgaben: list[dict]) -> list[dict]:
    if not isinstance(aufgaben, list):
        return []
    changed = False
    jetzt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Aufgaben, die schon einen automatischen Erledigt-Hinweis tragen, aber noch aktiv sind, wirklich erledigen.
    for a in aufgaben:
        if not isinstance(a, dict) or not _pc_status_aktiv_2727(a):
            continue
        notiz = str(a.get("notiz", ""))
        if "Automatisch erledigt:" in notiz or "Zombie-/verwaiste Testaufgabe" in notiz:
            a["status"] = "erledigt"
            a["aktualisiert"] = jetzt
            changed = True

    # Doppelte aktive Regressionen je PDF: nur die aktuellste behalten.
    gruppen = {}
    for a in aufgaben:
        if not isinstance(a, dict) or not _pc_status_aktiv_2727(a):
            continue
        blob = " ".join(str(a.get(k, "")) for k in ["bereich", "titel", "quelle", "notiz"]).lower()
        if "regression" not in blob and "ocr" not in blob:
            continue
        key = _pc_pdf_key_2727(a)
        if not key:
            continue
        gruppen.setdefault(key, []).append(a)

    for key, items in gruppen.items():
        if len(items) <= 1:
            continue
        keep = max(items, key=_pc_sortwert_2727)
        for a in items:
            if a is keep:
                continue
            a["status"] = "erledigt"
            a["aktualisiert"] = jetzt
            notiz = str(a.get("notiz", ""))
            hinweis = f"\n\nAutomatisch erledigt: doppelte aktive Regression/OCR-Aufgabe zu {key}; behalten wurde {keep.get('id','')}."
            if "doppelte aktive Regression/OCR-Aufgabe" not in notiz[-1500:]:
                a["notiz"] = (notiz + hinweis).strip()
            changed = True

    if changed:
        try:
            projekt_speichere_aufgaben(aufgaben)
        except Exception:
            pass
    return aufgaben



# ============================================================
# WEBUI 3.7.0 - FEHLERBEREICH & PRUEFSTATUS
# ============================================================
# Manuell nicht bestandene Tests werden zusätzlich mit
# manuell_nicht_bestanden=1, pruefstatus=abweichung und workflow_status=ABWEICHUNG
# markiert. Dadurch können sie im Bereich "Abweichung" gezählt und angezeigt werden.

try:
    _massentest_pruefstatus_orig_370 = massentest_pruefstatus
    def massentest_pruefstatus(row: dict) -> str:
        if str(row.get("manuell_nicht_bestanden", "")).strip() == "1":
            return "abweichung"
        if str(row.get("workflow_status", "")).strip().upper() == "ABWEICHUNG":
            return "abweichung"
        return _massentest_pruefstatus_orig_370(row)
except Exception:
    pass

try:
    _massentest_status_badge_orig_370 = massentest_status_badge
    def massentest_status_badge(status: str) -> str:
        if str(status or "").strip().lower() in {"abweichung", "fehler", "nicht_bestanden"}:
            return "<span class='badge bad'>Abweichung / Fehler</span>"
        return _massentest_status_badge_orig_370(status)
except Exception:
    pass


# ============================================================
# WEBUI 3.8.2 - ARBEITSSTAND / STABILISIERUNG
# ============================================================
# Ziel: keine neue Funktion. Nur Stabilisierung der bestehenden Prüflogik:
# - Fachliche Validierung wird dauerhaft in massentest_ergebnisse.json/csv gespeichert.
# - Oberfläche und Export werden vor Anzeige/Export synchronisiert.
# - Manuell nicht bestandene Tests bleiben sichtbar als Aufgabe/Abweichung.
# - Alte Hotfix-Kaskaden werden nicht erweitert.

try:
    for _f in [
        "fachlich_validiert", "fachlich_validiert_am", "fachlich_validiert_von", "fachlich_validiert_hinweis", "manuell_nicht_bestanden"
    ]:
        if _f not in MASSTEST_FIELDS:
            MASSTEST_FIELDS.append(_f)
except Exception:
    pass

try:
    _mt_write_results_orig_382 = massentest_write_results
    def massentest_write_results(rows: list[dict[str, str]], persist_references: bool = False) -> None:
        # Vor dem normalen Schreiben Qualitätsfelder gegen versehentliches Verlieren absichern.
        old_by_key = {}
        try:
            for _old in massentest_read_results():
                old_by_key[massentest_row_key(_old)] = dict(_old)
        except Exception:
            old_by_key = {}
        merged_rows = []
        for _row in rows or []:
            _r = dict(_row or {})
            _old = old_by_key.get(massentest_row_key(_r), {})
            for _k in ["fachlich_validiert", "fachlich_validiert_am", "fachlich_validiert_von", "fachlich_validiert_hinweis", "manuell_nicht_bestanden", "aufgabe_id"]:
                if not str(_r.get(_k, "") or "").strip() and str(_old.get(_k, "") or "").strip():
                    _r[_k] = _old.get(_k, "")
            merged_rows.append(_r)
        return _mt_write_results_orig_382(merged_rows, persist_references=persist_references)
except Exception:
    pass

try:
    _mt_validate_orig_382 = massentest_validate_row
    def massentest_validate_row(row_id: str, action: str = Form("validieren"), source: str = Form("list")):
        rows = massentest_read_results()
        idx, row = massentest_find_row(rows, row_id)
        if row is None or idx is None:
            raise HTTPException(status_code=404, detail="Massentest-Eintrag nicht gefunden")
        act = (action or "validieren").strip().lower()
        valid = act not in {"entziehen", "zurueck", "zurück", "0", "false"}
        row = massentest_set_fachlich_validiert(row, valid)
        rows[idx] = row
        massentest_write_results(rows)
        msg = "Fachliche Validierung gespeichert." if valid else "Fachliche Validierung zurückgenommen."
        src = (source or "list").strip().lower()
        if src == "result":
            target = f"/test/massentest/fachlich/{quote(row_id)}?msg={quote(msg)}" if massentest_row_status(row) == "bestanden" else f"/test/massentest/result/{quote(row_id)}?msg={quote(msg)}"
        elif src == "detail":
            target = f"/test/massentest/fachlich/{quote(row_id)}?msg={quote(msg)}" if massentest_row_status(row) == "bestanden" else f"/test/massentest/detail/{quote(row_id)}?msg={quote(msg)}"
        elif src == "quality":
            target = f"/test/massentest/quality?msg={quote(msg)}"
        elif src == "fachlich":
            return massentest_redirect_next_fachlich(row_id, msg)
        else:
            target = f"/test/massentest?msg={quote(msg)}#mtrow-{quote(row_id)}"
        return RedirectResponse(url=target, status_code=303)
except Exception:
    pass

