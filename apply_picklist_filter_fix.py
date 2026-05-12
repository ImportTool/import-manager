#!/usr/bin/env python3
"""
apply_picklist_filter_fix.py

Adds a server-side name-filter to portFindIdByName. Instead of downloading
the whole picklist (which on accounts with > 25,000 spaces hits our
50-page safety cap and misses recent records), we ask Facilio directly
for the named record via /picklist/{module}?filters={name:{...}}.

Also bumps the safety cap in loadFullPicklist from 50 → 200 pages so the
fallback can handle larger accounts.

How to run:
  Put next to your index.html, then:
    python3 apply_picklist_filter_fix.py

Backup: index.html.before-picklist-filter-fix.bak
"""

import sys
from pathlib import Path

INDEX = Path(__file__).parent / "index.html"
BACKUP = Path(__file__).parent / "index.html.before-picklist-filter-fix.bak"


def fail(msg):
    print(f"\n[ERROR] {msg}\n\nNo changes written.")
    sys.exit(1)


def replace_once(text, old, new, label):
    if old not in text:
        first = old.strip().split("\n", 1)[0][:80]
        fail(f"Couldn't find expected text for: {label}\n  Looking for: {first!r}")
    if text.count(old) > 1:
        fail(f"'{label}' matched {text.count(old)} places — expected 1.")
    return text.replace(old, new, 1)


def main():
    if not INDEX.exists():
        fail(f"index.html not found at {INDEX}.")
    original = INDEX.read_text(encoding="utf-8")
    print(f"Read {INDEX} ({len(original):,} bytes)")

    if "// PICKLIST_FILTER_FIX_APPLIED" in original:
        fail("Already applied (sentinel present).")

    text = original

    # ---------- FIX 1: portFindIdByName — try filtered picklist FIRST ----------
    fix1_old = """async function portFindIdByName(picklistKey, name) {
  // Lookup-by-name backed by the fully-paginated picklist cache (see
  // loadFullPicklist). Numeric input bypasses the cache as a direct ID.
  if (!name) return null;
  const trimmed = String(name).trim();
  if (/^\\d+$/.test(trimmed)) return Number(trimmed);
  try {
    const items = await loadFullPicklist(picklistKey, picklistKey);
    const target = trimmed.toLowerCase();
    const hit = items.find(it => (it.name || \"\").toLowerCase().trim() === target);
    return hit ? hit.id : null;
  } catch { return null; }
}"""
    fix1_new = """async function portFindIdByName(picklistKey, name) {
  // PICKLIST_FILTER_FIX_APPLIED — for accounts with > 25k records of a
  // given kind, a full pagination download is both slow and misses recent
  // records that fall past the page-count cap. Strategy:
  //   1. If input is numeric, use as ID directly.
  //   2. Check existing in-memory cache (free hit).
  //   3. Ask Facilio's picklist endpoint for THIS specific name. Tries
  //      operatorId 3 (AU/AE), 36, and 9 since Facilio's name-filter
  //      operator varies by region.
  //   4. Fall back to the full paginated cache as a last resort.
  if (!name) return null;
  const trimmed = String(name).trim();
  if (/^\\d+$/.test(trimmed)) return Number(trimmed);

  // 2. Cached?
  try {
    if (state.cache[picklistKey] && state.cache[picklistKey].length) {
      const target = trimmed.toLowerCase();
      const hit = state.cache[picklistKey].find(it => (it.name || \"\").toLowerCase().trim() === target);
      if (hit) return hit.id;
    }
  } catch (_) {}

  // 3. Server-side filtered picklist.
  for (const operatorId of [3, 36, 9]) {
    const filt = encodeURIComponent(JSON.stringify({
      name: { operatorId, value: [trimmed] }
    }));
    try {
      const r = await api(\"GET\",
        `maintenance/api/v3/picklist/${picklistKey}?page=1&perPage=20&viewName=hidden-all&filters=${filt}`);
      const root = r?.data || {};
      let arr = root.pickList || root[picklistKey] || root.list || [];
      if (!Array.isArray(arr)) {
        for (const k of Object.keys(root)) if (Array.isArray(root[k])) { arr = root[k]; break; }
      }
      // Normalise (picklist responses use {value,label}, view/all uses {id,name}).
      const normalised = (arr || []).map(it => ({
        id: it.value ?? it.id,
        name: ((it.label ?? it.name ?? \"\") + \"\").trim()
      })).filter(x => x.id != null && x.name);
      const target = trimmed.toLowerCase();
      const matches = normalised.filter(it => it.name.toLowerCase() === target);
      if (matches.length === 1) return matches[0].id;
      if (matches.length > 1) {
        const ids = matches.slice(0, 6).map(m => m.id).join(\", \");
        log(`Multiple ${picklistKey} named \"${name}\" (IDs: ${ids}). Using the first.`, \"warn\");
        return matches[0].id;
      }
      // If the endpoint accepted the filter but returned 0 rows, no point
      // trying another operatorId — the record genuinely doesn't exist.
      if (Array.isArray(arr) && arr.length === 0) break;
    } catch (_) { /* try next operatorId */ }
  }

  // 4. Fallback — full paginated cache.
  try {
    const items = await loadFullPicklist(picklistKey, picklistKey);
    const target = trimmed.toLowerCase();
    const hit = items.find(it => (it.name || \"\").toLowerCase().trim() === target);
    return hit ? hit.id : null;
  } catch { return null; }
}"""
    text = replace_once(text, fix1_old, fix1_new, "FIX 1 — portFindIdByName filtered picklist first")

    # ---------- FIX 2: loadFullPicklist — raise page cap 50 → 200 ----------
    # Two locations (picklist loop + view/all loop).
    fix2_old_a = "    for (let page = 1; page <= 50; page++) {\n      const url = `maintenance/api/v3/picklist/${endpoint}?page=${page}&perPage=${PAGE_SIZE}&viewName=hidden-all`;"
    fix2_new_a = "    for (let page = 1; page <= 200; page++) {\n      const url = `maintenance/api/v3/picklist/${endpoint}?page=${page}&perPage=${PAGE_SIZE}&viewName=hidden-all`;"
    text = replace_once(text, fix2_old_a, fix2_new_a, "FIX 2a — picklist loop cap → 200")

    fix2_old_b = "    for (let page = 1; page <= 50; page++) {\n      const url = `maintenance/api/v3/modules/${endpoint}/view/all?moduleName=${endpoint}&viewName=all&page=${page}&perPage=${PAGE_SIZE}`;"
    fix2_new_b = "    for (let page = 1; page <= 200; page++) {\n      const url = `maintenance/api/v3/modules/${endpoint}/view/all?moduleName=${endpoint}&viewName=all&page=${page}&perPage=${PAGE_SIZE}`;"
    text = replace_once(text, fix2_old_b, fix2_new_b, "FIX 2b — view/all loop cap → 200")

    BACKUP.write_text(original, encoding="utf-8")
    INDEX.write_text(text, encoding="utf-8")
    delta = len(text) - len(original)
    print(f"\n✓ Applied.")
    print(f"  Backup: {BACKUP.name}")
    print(f"  New size: {len(text):,} bytes (delta: {delta:+,})")
    print()
    print("Restart `python3 start.py`. Then in the app:")
    print("  1. Settings → Clear lookup cache")
    print("  2. Validate one row first to confirm the filter works.")
    print("     You should see a quick `GET .../picklist/space?...&filters=...` call")
    print("     instead of the 50-page slog.")


if __name__ == "__main__":
    main()
