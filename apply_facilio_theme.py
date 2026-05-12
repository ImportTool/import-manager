#!/usr/bin/env python3
"""
apply_facilio_theme.py

Re-skins index.html to match Facilio's light theme.

What changes:
  - Background switches from charcoal to off-white
  - Cards are white with subtle borders + 1-pixel shadow
  - Primary accent is Facilio blue (#2563eb), active tabs get a blue
    underline instead of teal
  - Status pills use pastel backgrounds (green/red/amber/blue)
  - Logs panel stays monospace but on a light surface, dark text
  - Buttons, inputs, panels, tables, toasts all updated to match

Functionality is untouched — only the <style>…</style> block at the top
of the document is replaced.

How to run:
  Put next to your index.html, then:
    python3 apply_facilio_theme.py

Backup: index.html.before-facilio-theme.bak

To revert later, just `mv index.html.before-facilio-theme.bak index.html`.
"""

import sys
from pathlib import Path

INDEX = Path(__file__).parent / "index.html"
BACKUP = Path(__file__).parent / "index.html.before-facilio-theme.bak"


NEW_STYLE = """<style>
  /* FACILIO_THEME_APPLIED — light theme matching Facilio Intranet/Console */
  :root {
    --bg: #f7f8fb;
    --panel: #ffffff;
    --panel2: #f9fafb;
    --panel-hover: #f3f4f6;
    --line: #e5e7eb;
    --line-strong: #d1d5db;
    --text: #1f2937;
    --text-strong: #111827;
    --muted: #6b7280;
    --muted-soft: #9ca3af;
    --accent: #2563eb;
    --accent-hover: #1d4ed8;
    --accent-soft: #eff6ff;
    --accent2: #10b981;
    --accent2-hover: #059669;
    --warn: #f59e0b;
    --warn-soft: #fef3c7;
    --warn-text: #92400e;
    --err: #ef4444;
    --err-soft: #fee2e2;
    --err-text: #b91c1c;
    --ok: #10b981;
    --ok-soft: #d1fae5;
    --ok-text: #065f46;
    --info-soft: #dbeafe;
    --info-text: #1e40af;
    --shadow-sm: 0 1px 2px rgba(15, 23, 42, .04);
    --shadow-md: 0 4px 12px rgba(15, 23, 42, .06);
    --shadow-lg: 0 12px 28px rgba(15, 23, 42, .08);
  }
  *{ box-sizing: border-box; }
  html,body{ margin:0; padding:0; background:var(--bg); color:var(--text);
    font: 14px/1.45 -apple-system, BlinkMacSystemFont, "Inter", "Segoe UI", Roboto, Helvetica, Arial, sans-serif; }
  a{ color: var(--accent); text-decoration: none; }
  a:hover{ text-decoration: underline; }
  button{ font: inherit; cursor: pointer; }
  input, select, textarea {
    font: inherit; color: var(--text);
    background: #ffffff; border:1px solid var(--line); border-radius:6px;
    padding:7px 9px; outline: none; width:100%;
    transition: border-color .15s ease, box-shadow .15s ease;
  }
  input::placeholder, textarea::placeholder{ color: var(--muted-soft); }
  input:focus, select:focus, textarea:focus{
    border-color: var(--accent);
    box-shadow: 0 0 0 3px rgba(37, 99, 235, .12);
  }
  textarea{ resize: vertical; min-height: 60px; }
  label.field{ display:block; margin-bottom: 10px; }
  label.field > .lbl{ display:block; color:var(--muted); margin-bottom:4px; font-size:12px; font-weight: 500; }
  label.field > .lbl .req{ color: var(--err); margin-left:2px; }
  .btn{
    background:var(--accent); color:#fff; border:0; padding:9px 14px; border-radius:6px;
    font-weight: 500; transition: background .15s ease, box-shadow .15s ease;
  }
  .btn:hover{ background: var(--accent-hover); }
  .btn:active{ transform: translateY(1px); }
  .btn.secondary{ background: var(--panel-hover); color: var(--text-strong); border: 1px solid var(--line); }
  .btn.secondary:hover{ background: var(--line); }
  .btn.danger{ background: var(--err-soft); color: var(--err-text); border:1px solid #fecaca; }
  .btn.danger:hover{ background: #fecaca; }
  .btn.success{ background: var(--accent2); }
  .btn.success:hover{ background: var(--accent2-hover); }
  .btn.ghost{ background: #ffffff; color:var(--text); border:1px solid var(--line); }
  .btn.ghost:hover{ background: var(--panel-hover); }
  .btn:disabled{ opacity:.5; cursor:not-allowed; }
  .row{ display:flex; gap:12px; flex-wrap:wrap; }
  .row > *{ flex:1 1 220px; min-width: 180px; }
  .grid-2{ display:grid; grid-template-columns: 1fr 1fr; gap: 0 14px; }
  .grid-3{ display:grid; grid-template-columns: 1fr 1fr 1fr; gap: 0 14px; }
  .grid-4{ display:grid; grid-template-columns: repeat(4, 1fr); gap: 0 14px; }
  @media (max-width: 900px){ .grid-2, .grid-3, .grid-4{ grid-template-columns: 1fr; } }

  /* App layout */
  .topbar{
    display:flex; align-items:center; justify-content:space-between;
    padding:12px 22px; border-bottom:1px solid var(--line);
    background: #ffffff;
  }
  .brand{ display:flex; align-items:center; gap:10px; font-weight:600; letter-spacing:.2px; color: var(--text-strong); font-size: 15px; }
  .brand .logo{
    width:28px; height:28px; border-radius:6px;
    background: conic-gradient(from 200deg, var(--accent), var(--accent2), var(--accent));
  }
  .conn-pill{
    display:inline-flex; align-items:center; gap:8px; padding:5px 10px;
    background: var(--ok-soft); border:1px solid #bbf7d0; border-radius:99px; font-size:12px; color: var(--ok-text); font-weight: 500;
  }
  .conn-pill .dot{ width:8px; height:8px; border-radius:50%; background: var(--ok); }
  .conn-pill.bad{ background: var(--err-soft); border-color: #fecaca; color: var(--err-text); }
  .conn-pill.bad .dot{ background: var(--err); }
  .topbar-actions{ display:flex; gap:8px; align-items:center; }

  .tabs{
    display:flex; gap:0; padding: 0 22px; border-bottom:1px solid var(--line);
    background: #ffffff;
  }
  .tab{
    background: transparent; color: var(--muted); border:0;
    padding: 13px 16px; border-bottom: 2px solid transparent; font-weight: 500; font-size: 13.5px;
    transition: color .15s ease, border-color .15s ease;
  }
  .tab:hover{ color: var(--text-strong); }
  .tab.active{ color: var(--accent); border-bottom-color: var(--accent); }
  .subtab{
    background: transparent; color: var(--muted); border: 0;
    padding: 10px 14px; border-bottom: 2px solid transparent; cursor: pointer; font: inherit; font-weight: 500;
  }
  .subtab.active{ color: var(--accent); border-bottom-color: var(--accent); }
  .subtab:hover{ color: var(--text-strong); }

  .panel{
    background: var(--panel); border:1px solid var(--line); border-radius:10px;
    padding: 16px; margin: 14px; box-shadow: var(--shadow-sm);
  }
  .panel h2, .panel h3{ margin: 0 0 10px; color: var(--text-strong); font-weight: 600; }
  .muted{ color: var(--muted); }
  .small{ font-size:12px; }

  .card-actions{ display:flex; gap:8px; flex-wrap:wrap; margin-top: 12px; }

  /* Login */
  .login-wrap{
    min-height:100vh; display:flex; align-items:center; justify-content:center; padding:20px;
    background: var(--bg);
  }
  .login-card{
    width:min(560px, 100%); background:var(--panel); border:1px solid var(--line);
    border-radius:14px; padding:28px;
    box-shadow: var(--shadow-lg);
  }
  .login-card h1{ margin:0 0 6px; font-size:22px; color: var(--text-strong); font-weight: 600; }
  .login-card .sub{ color: var(--muted); margin: 0 0 18px; }

  /* Queue table */
  .queue-table{
    width:100%; border-collapse: collapse; font-size: 12.5px; margin-top:10px;
  }
  .queue-table th, .queue-table td{
    padding:6px 8px; border-bottom:1px solid var(--line);
    text-align:left; vertical-align: top; white-space: nowrap;
    max-width: 200px; overflow: hidden; text-overflow: ellipsis;
  }
  .queue-table th{ color: var(--muted); font-weight: 600; background: var(--panel2); position: sticky; top: 0;}
  .queue-table tr:hover{ background: var(--panel-hover); }
  .table-scroll{
    overflow:auto; max-height: 360px; border:1px solid var(--line); border-radius:8px;
  }
  .status-badge{
    display:inline-block; padding:2px 8px; border-radius:99px; font-size:11px; font-weight: 500;
  }
  .s-pending{ background: var(--panel-hover); color: var(--muted); }
  .s-valid{   background: var(--ok-soft); color: var(--ok-text); }
  .s-error{   background: var(--err-soft); color: var(--err-text); }
  .s-running{ background: var(--info-soft); color: var(--info-text); }
  .s-success{ background: var(--ok-soft); color: var(--ok-text); }
  .s-warn{    background: var(--warn-soft); color: var(--warn-text); }
  .row-actions button{ font-size:11px; padding:3px 6px; }

  /* Logs */
  .logs{
    margin: 14px; height: 220px; overflow:auto;
    background: #f9fafb; border:1px solid var(--line); border-radius:10px; padding:12px;
    font: 12px/1.45 ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
    color: #475569;
  }
  .logs .l-info  { color: #2563eb; }
  .logs .l-ok    { color: #15803d; }
  .logs .l-err   { color: #dc2626; }
  .logs .l-warn  { color: #c2410c; }
  .logs .l-dim   { color: #94a3b8; }

  /* Tooltips inline help */
  details.help{ margin: 6px 0 12px; }
  details.help summary{ cursor:pointer; color: var(--muted); font-size: 12px; font-weight: 500; }
  details.help summary:hover{ color: var(--text-strong); }
  details.help .help-body{
    margin-top:6px; padding:12px; background: var(--panel2); border:1px solid var(--line); border-radius:8px;
    color: var(--text); font-size:12px;
  }

  .pill-row{ display:flex; gap:6px; flex-wrap:wrap; }
  .pill{
    display:inline-flex; align-items:center; gap:6px;
    background: var(--panel2); border:1px solid var(--line); padding:3px 10px;
    border-radius:99px; font-size:11px; color: var(--text);
  }
  .hidden{ display:none !important; }

  /* Editable spreadsheet grid */
  .grid-scroll{
    overflow:auto; max-height: calc(100vh - 360px); min-height: 320px;
    border-top:1px solid var(--line); border-bottom:1px solid var(--line);
    background: var(--panel);
  }
  table.grid{
    border-collapse: separate; border-spacing: 0;
    font-size: 12.5px;
    table-layout: fixed;
  }
  table.grid th, table.grid td{
    border-right: 1px solid var(--line);
    border-bottom: 1px solid var(--line);
    padding: 0; vertical-align: top;
    background: var(--panel);
  }
  table.grid thead th{
    background: var(--panel2); color: var(--muted);
    font-weight: 600;
    padding: 9px 10px;
    position: sticky; top: 0; z-index: 5;
    text-align: left; white-space: nowrap;
    font-size: 11.5px; text-transform: uppercase; letter-spacing: .03em;
  }
  table.grid th.sticky-left, table.grid td.sticky-left{
    position: sticky; left: 0; z-index: 4;
    background: var(--panel2);
    border-right: 2px solid var(--line);
  }
  table.grid thead th.sticky-left{ z-index: 6; }
  table.grid td input, table.grid td select{
    width: 100%; border: 0; border-radius: 0;
    background: transparent; padding: 7px 9px;
    color: var(--text);
    box-shadow: none;
  }
  table.grid td input:focus, table.grid td select:focus{
    outline: 2px solid var(--accent); outline-offset: -2px;
    background: #ffffff;
    box-shadow: none;
  }
  table.grid tr:hover td{ background: var(--panel2); }
  table.grid tr:hover td.sticky-left{ background: var(--panel-hover); }
  table.grid td.cell-row-num{
    color: var(--muted-soft); padding: 7px 10px; text-align: right;
    font-variant-numeric: tabular-nums; font-size: 11.5px;
  }
  table.grid td.cell-actions{
    padding: 4px 6px; white-space: nowrap;
  }
  table.grid td.cell-actions button{
    font-size:11px; padding:3px 7px; margin-right:3px;
  }
  table.grid td.cell-status{
    padding: 5px 8px; font-size: 11px;
  }
  table.grid td.cell-readonly{
    color: var(--muted); padding: 7px 9px;
    font-variant-numeric: tabular-nums;
  }
  /* Column widths */
  table.grid col.w-num{ width: 42px; }
  table.grid col.w-status{ width: 200px; }
  table.grid col.w-actions{ width: 110px; }
  table.grid col.w-sm{ width: 100px; }
  table.grid col.w-md{ width: 150px; }
  table.grid col.w-lg{ width: 220px; }

  /* Frequency sub-tabs */
  .freq-tab{
    background:transparent; border:0; color: var(--muted);
    padding: 9px 16px; border-bottom: 2px solid transparent; cursor: pointer;
    font: inherit; font-weight: 500;
    transition: color .15s ease, border-color .15s ease;
  }
  .freq-tab.active{ color: var(--accent); border-bottom-color: var(--accent); }
  .freq-tab:hover{ color: var(--text-strong); }

  /* Expandable asset sub-grid */
  tr.asset-row td{
    background: var(--panel2); padding: 12px;
  }
  table.subgrid{
    width: 100%; border-collapse: collapse;
    background: var(--panel); border:1px solid var(--line); border-radius: 8px;
    overflow: hidden;
  }
  table.subgrid th, table.subgrid td{
    padding: 6px 8px; border-bottom: 1px solid var(--line); font-size: 12.5px;
  }
  table.subgrid th{ color: var(--muted); background: var(--panel2); text-align: left; font-weight: 600; }
  table.subgrid input{
    width: 100%; border: 0; background: transparent; padding: 4px 6px; color: var(--text);
  }
  table.subgrid input:focus{ background:#ffffff; outline:2px solid var(--accent); outline-offset:-2px; }
  .config-cell{ display:flex; align-items:center; gap:6px; padding: 0 8px; }
  .config-cell .count{
    background: var(--panel2); border: 1px solid var(--line); padding: 2px 8px;
    border-radius: 99px; font-size: 11px; color: var(--muted);
  }

  /* Toast */
  .toast{
    position: fixed; right: 22px; bottom: 22px; max-width: 360px;
    background: #ffffff; color: var(--text); border:1px solid var(--line); border-left:4px solid var(--accent2);
    border-radius:10px; padding:12px 14px; box-shadow: var(--shadow-lg);
    transform: translateY(20px); opacity:0; pointer-events:none; transition: all .2s ease;
    font-size: 13px;
  }
  .toast.show{ transform:none; opacity:1; pointer-events:auto; }
  .toast.err{ border-left-color: var(--err); }
  .toast.warn{ border-left-color: var(--warn); }

  /* Connection text/area in topbar — keep monospace base URLs readable */
  .topbar #connText{ font-weight: 500; }

  /* Headings above sections in the body */
  h3{ font-size: 14px; font-weight: 600; color: var(--text-strong); }
</style>"""


def fail(msg):
    print(f"\n[ERROR] {msg}\n\nNo changes written.")
    sys.exit(1)


def main():
    if not INDEX.exists():
        fail(f"index.html not found at {INDEX}.")
    original = INDEX.read_text(encoding="utf-8")
    print(f"Read {INDEX} ({len(original):,} bytes)")

    if "FACILIO_THEME_APPLIED" in original:
        fail("Already applied (sentinel present).")

    # Find the first <style>…</style> block (the top-of-document one).
    start = original.find("<style>")
    end = original.find("</style>")
    if start < 0 or end < 0 or end < start:
        fail("Couldn't locate the <style>…</style> block at the top of the document.")

    # Sanity check: this should be the THEME block — it'll contain our known
    # CSS variable. If not, bail rather than wiping a random style tag.
    snippet = original[start:end + len("</style>")]
    if "--accent" not in snippet or ":root" not in snippet:
        fail("The first <style> block doesn't look like the theme block (no :root / --accent). Aborting.")

    new_text = original[:start] + NEW_STYLE + original[end + len("</style>"):]

    BACKUP.write_text(original, encoding="utf-8")
    INDEX.write_text(new_text, encoding="utf-8")
    delta = len(new_text) - len(original)
    print(f"\n✓ Light theme applied.")
    print(f"  Backup: {BACKUP.name}")
    print(f"  New size: {len(new_text):,} bytes (delta: {delta:+,})")
    print()
    print("Restart `python3 start.py` and hard-refresh the browser (Cmd+Shift+R).")
    print()
    print("To revert: mv index.html.before-facilio-theme.bak index.html")


if __name__ == "__main__":
    main()
