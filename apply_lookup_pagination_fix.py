#!/usr/bin/env python3
"""
apply_lookup_pagination_fix.py

Fixes the "Floor X not found" / "Building X not found" / "Site X not found"
class of errors that hit accounts with more than 200 portfolio records.

Root cause:
  portFindIdByName loaded the picklist endpoint with perPage=200. On large
  accounts (hundreds of floors), the target record was simply not in the
  first 200 — so the client said "not found" even though Facilio has it.

Fix:
  1. portFindIdByName now does a SERVER-SIDE name filter first
     (GET /modules/{module}/view/all?filters={"name":{...}}). This finds
     a single record by name regardless of account size.
  2. Falls back to the cached picklist for backwards compatibility (and to
     reuse the cache when the same name is looked up repeatedly).
  3. Picklist perPage is bumped from 200 → 1000 as a secondary safety net.

How to run:
  Put next to your index.html, then:
    python3 apply_lookup_pagination_fix.py

Writes backup to index.html.before-lookup-pagination-fix.bak.
"""

import sys
from pathlib import Path

INDEX = Path(__file__).parent / "index.html"
BACKUP = Path(__file__).parent / "index.html.before-lookup-pagination-fix.bak"


def fail(msg):
    print(f"\n[ERROR] {msg}")
    print("\nNo changes were written.")
    sys.exit(1)


def replace_once(text, old, new, label):
    if old not in text:
        first_line = old.strip().split("\n", 1)[0][:80]
        fail(f"Couldn't find expected text for: {label}\n  Looking for: {first_line!r}")
    if text.count(old) > 1:
        fail(f"'{label}' matched {text.count(old)} places — expected 1.")
    return text.replace(old, new, 1)


def main():
    if not INDEX.exists():
        fail(f"index.html not found at {INDEX}.")
    original = INDEX.read_text(encoding="utf-8")
    print(f"Read {INDEX} ({len(original):,} bytes)")

    if "// LOOKUP_PAGINATION_FIX_APPLIED" in original:
        fail("Already applied (sentinel present).")

    text = original

    # ---------- FIX 1: portFindIdByName — server-side filter first ----------
    fix1_old = """async function portFindIdByName(picklistKey, name) {
  if (!name) return null;
  if (/^\\d+$/.test(String(name).trim())) return Number(String(name).trim());
  try {
    const items = await loadFullPicklist(picklistKey, picklistKey);
    const target = name.trim().toLowerCase();
    const hit = items.find(it => (it.name || "").toLowerCase().trim() === target);
    return hit ? hit.id : null;
  } catch { return null; }
}"""
    fix1_new = """async function portFindIdByName(picklistKey, name) {
  // LOOKUP_PAGINATION_FIX_APPLIED — robust name → id lookup that works on
  // accounts with thousands of records (previous version only checked the
  // first 200 picklist entries).
  if (!name) return null;
  const trimmed = String(name).trim();
  if (/^\\d+$/.test(trimmed)) return Number(trimmed);

  // Strategy 1: cached picklist (fast path — no extra API call when we've
  // already loaded the list and the target happens to be in it).
  try {
    if (state.cache[picklistKey] && state.cache[picklistKey].length) {
      const target = trimmed.toLowerCase();
      const hit = state.cache[picklistKey].find(it => (it.name || "").toLowerCase().trim() === target);
      if (hit) return hit.id;
    }
  } catch (_) {}

  // Strategy 2: server-side filtered view/all — the authoritative answer.
  // Tries a couple of operator IDs since Facilio's name-filter operator
  // varies between regions (3 on AU/AE, 36 on some others).
  const moduleName = picklistKey;
  for (const operatorId of [36, 3]) {
    const filt = encodeURIComponent(JSON.stringify({
      name: { operatorId, value: [trimmed] }
    }));
    try {
      const r = await api("GET",
        `maintenance/api/v3/modules/${moduleName}/view/all` +
        `?moduleName=${moduleName}&viewName=all&page=1&perPage=20&filters=${filt}`);
      const root = r?.data || {};
      let arr = root[moduleName] || root.list || [];
      if (!Array.isArray(arr)) {
        for (const k of Object.keys(root)) if (Array.isArray(root[k])) { arr = root[k]; break; }
      }
      const target = trimmed.toLowerCase();
      const matches = (arr || []).filter(it =>
        (it.name || it.displayName || "").toLowerCase().trim() === target);
      if (matches.length === 1) return matches[0].id;
      if (matches.length > 1) {
        const ids = matches.slice(0, 6).map(m => m.id).join(", ");
        log(`Multiple ${moduleName}s named "${name}" (IDs: ${ids}). Picking the first one.`, "warn");
        return matches[0].id;
      }
    } catch (_) { /* try next operator */ }
  }

  // Strategy 3: full picklist fallback (loads up to perPage=1000 after the
  // earlier fix). Slow on huge accounts but works as a last resort.
  try {
    const items = await loadFullPicklist(picklistKey, picklistKey);
    const target = trimmed.toLowerCase();
    const hit = items.find(it => (it.name || "").toLowerCase().trim() === target);
    return hit ? hit.id : null;
  } catch { return null; }
}"""
    text = replace_once(text, fix1_old, fix1_new, "FIX 1 — portFindIdByName server-side filter")

    # ---------- FIX 2: bump default picklist perPage 200 → 1000 ----------
    fix2_old = """async function loadFullPicklist(key, endpoint, query="?page=1&perPage=200&viewName=hidden-all") {"""
    fix2_new = """async function loadFullPicklist(key, endpoint, query="?page=1&perPage=1000&viewName=hidden-all") {"""
    text = replace_once(text, fix2_old, fix2_new, "FIX 2 — bump picklist perPage to 1000")

    # ---------- FIX 3: bump view/all fallback inside loadFullPicklist 500 → 2000 ----------
    fix3_old = """    const data = await api("GET",
      `maintenance/api/v3/modules/${endpoint}/view/all?moduleName=${endpoint}&viewName=all&page=1&perPage=500`);"""
    fix3_new = """    const data = await api("GET",
      `maintenance/api/v3/modules/${endpoint}/view/all?moduleName=${endpoint}&viewName=all&page=1&perPage=2000`);"""
    text = replace_once(text, fix3_old, fix3_new, "FIX 3 — bump view/all fallback to 2000")

    BACKUP.write_text(original, encoding="utf-8")
    INDEX.write_text(text, encoding="utf-8")
    delta = len(text) - len(original)
    print(f"\n✓ Applied.")
    print(f"  Backup: {BACKUP.name}")
    print(f"  New size: {len(text):,} bytes (delta: {delta:+,})")
    print()
    print("Restart `python3 start.py` to pick up the new HTML.")


if __name__ == "__main__":
    main()
