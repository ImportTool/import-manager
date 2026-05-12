#!/usr/bin/env python3
"""
apply_lookup_paginate_all.py

Replaces the previous server-side-filter approach (which returns 400 on
some Facilio versions) with a full-pagination loader for picklists.

What changes:
  - loadFullPicklist now walks every page (page=1,2,3,...) of either the
    /picklist/{m} endpoint or the /modules/{m}/view/all endpoint, until a
    page returns fewer rows than the page size — meaning we've got them
    all. Cached for the session, so 432 space rows hitting the same floor
    list = ~10 API calls total instead of 432.
  - portFindIdByName drops the per-row filtered API call (which 400's on
    this Facilio version anyway) and looks up against the fully-loaded
    cache. Numeric input is still treated as a direct ID shortcut.
  - perPage on each page is 500 (was 1000) — smaller pages but more of
    them, to stay well under any per-request size limit Facilio might
    enforce.

How to run:
  Put next to your index.html, then:
    python3 apply_lookup_paginate_all.py

Backup: index.html.before-lookup-paginate-all.bak
"""

import sys
from pathlib import Path

INDEX = Path(__file__).parent / "index.html"
BACKUP = Path(__file__).parent / "index.html.before-lookup-paginate-all.bak"


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

    if "// PAGINATE_ALL_FIX_APPLIED" in original:
        fail("Already applied (sentinel present).")

    text = original

    # ---------- FIX 1: loadFullPicklist — paginate through ALL pages ----------
    # Replace the whole function. We match the original signature line that
    # was set by either the original code (perPage=200) or our previous fix
    # (perPage=1000), and the closing `}` of the function. To make the find
    # robust, match the whole body up to and including the closing brace and
    # the blank line before the next function.
    fix1_old_a = """async function loadFullPicklist(key, endpoint, query=\"?page=1&perPage=1000&viewName=hidden-all\") {
  if (state.cache[key] && state.cache[key].length) return state.cache[key];

  const normalize = data => {
    let arr = [];
    const root = data && data.data ? data.data : data;
    if (Array.isArray(root)) arr = root;
    else if (root) {
      for (const k of Object.keys(root)) {
        if (Array.isArray(root[k])) { arr = root[k]; break; }
      }
    }
    return arr.map(it => ({
      id: it.id ?? it.value,
      name: (it.name ?? it.label ?? \"\").toString()
    })).filter(it => it.id != null && it.name);
  };

  // Try picklist first.
  try {
    const data = await api(\"GET\", `maintenance/api/v3/picklist/${endpoint}${query}`);
    const items = normalize(data);
    if (items.length) { state.cache[key] = items; return items; }
  } catch (e) { /* fall through */ }

  // Fallback: module view/all.
  try {
    const data = await api(\"GET\",
      `maintenance/api/v3/modules/${endpoint}/view/all?moduleName=${endpoint}&viewName=all&page=1&perPage=2000`);
    const items = normalize(data);
    if (items.length) {
      state.cache[key] = items;
      log(`Loaded ${items.length} ${endpoint} via view/all (picklist endpoint unavailable).`, \"dim\");
      return items;
    }
  } catch (e) { /* fall through */ }

  state.cache[key] = [];
  return [];
}"""
    # Same content but with perPage=200 (older un-patched version).
    fix1_old_b = fix1_old_a.replace("perPage=1000", "perPage=200").replace(
        "perPage=2000", "perPage=500"
    )

    fix1_new = """async function loadFullPicklist(key, endpoint, query=null) {
  // PAGINATE_ALL_FIX_APPLIED — walks every page until exhausted, then caches
  // the full list for the session. Replaces previous single-page-only logic
  // that missed records on accounts with more than the page size.
  if (state.cache[key] && state.cache[key].length) return state.cache[key];

  const PAGE_SIZE = 500;

  const normalize = data => {
    let arr = [];
    const root = data && data.data ? data.data : data;
    if (Array.isArray(root)) arr = root;
    else if (root) {
      for (const k of Object.keys(root)) {
        if (Array.isArray(root[k])) { arr = root[k]; break; }
      }
    }
    return arr.map(it => ({
      id: it.id ?? it.value,
      name: (it.name ?? it.label ?? \"\").toString()
    })).filter(it => it.id != null && it.name);
  };

  // Try /picklist/{endpoint} first, paginating all pages.
  let all = [];
  try {
    for (let page = 1; page <= 50; page++) {
      const url = `maintenance/api/v3/picklist/${endpoint}?page=${page}&perPage=${PAGE_SIZE}&viewName=hidden-all`;
      const data = await api(\"GET\", url);
      const items = normalize(data);
      if (!items.length) break;
      all.push(...items);
      if (items.length < PAGE_SIZE) break;
    }
    if (all.length) {
      state.cache[key] = all;
      log(`Loaded ${all.length} ${endpoint} via picklist (paginated).`, \"dim\");
      return all;
    }
  } catch (e) { /* fall through to view/all */ }

  // Fallback: /modules/{endpoint}/view/all, also paginated.
  all = [];
  try {
    for (let page = 1; page <= 50; page++) {
      const url = `maintenance/api/v3/modules/${endpoint}/view/all?moduleName=${endpoint}&viewName=all&page=${page}&perPage=${PAGE_SIZE}`;
      const data = await api(\"GET\", url);
      const items = normalize(data);
      if (!items.length) break;
      all.push(...items);
      if (items.length < PAGE_SIZE) break;
    }
    if (all.length) {
      state.cache[key] = all;
      log(`Loaded ${all.length} ${endpoint} via view/all (paginated, picklist unavailable).`, \"dim\");
      return all;
    }
  } catch (e) { /* fall through */ }

  state.cache[key] = [];
  return [];
}"""

    if fix1_old_a in text:
        text = replace_once(text, fix1_old_a, fix1_new, "FIX 1 — loadFullPicklist paginate all (post-pagination-fix)")
    elif fix1_old_b in text:
        text = replace_once(text, fix1_old_b, fix1_new, "FIX 1 — loadFullPicklist paginate all (un-patched)")
    else:
        fail("Couldn't find loadFullPicklist function — has the file been modified beyond what this patch expects?")

    # ---------- FIX 2: portFindIdByName — drop the doomed view/all filter,
    #                   rely on the full picklist cache. ----------
    # We need to replace the version that EXISTS in the file. There are two
    # possible shapes: the original (cache-only) version, or the previous-fix
    # version (with the server-side filter + sentinel comment).
    fix2_old_a = """async function portFindIdByName(picklistKey, name) {
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
      const hit = state.cache[picklistKey].find(it => (it.name || \"\").toLowerCase().trim() === target);
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
      const r = await api(\"GET\",
        `maintenance/api/v3/modules/${moduleName}/view/all` +
        `?moduleName=${moduleName}&viewName=all&page=1&perPage=20&filters=${filt}`);
      const root = r?.data || {};
      let arr = root[moduleName] || root.list || [];
      if (!Array.isArray(arr)) {
        for (const k of Object.keys(root)) if (Array.isArray(root[k])) { arr = root[k]; break; }
      }
      const target = trimmed.toLowerCase();
      const matches = (arr || []).filter(it =>
        (it.name || it.displayName || \"\").toLowerCase().trim() === target);
      if (matches.length === 1) return matches[0].id;
      if (matches.length > 1) {
        const ids = matches.slice(0, 6).map(m => m.id).join(\", \");
        log(`Multiple ${moduleName}s named \"${name}\" (IDs: ${ids}). Picking the first one.`, \"warn\");
        return matches[0].id;
      }
    } catch (_) { /* try next operator */ }
  }

  // Strategy 3: full picklist fallback (loads up to perPage=1000 after the
  // earlier fix). Slow on huge accounts but works as a last resort.
  try {
    const items = await loadFullPicklist(picklistKey, picklistKey);
    const target = trimmed.toLowerCase();
    const hit = items.find(it => (it.name || \"\").toLowerCase().trim() === target);
    return hit ? hit.id : null;
  } catch { return null; }
}"""

    fix2_old_b = """async function portFindIdByName(picklistKey, name) {
  if (!name) return null;
  if (/^\\d+$/.test(String(name).trim())) return Number(String(name).trim());
  try {
    const items = await loadFullPicklist(picklistKey, picklistKey);
    const target = name.trim().toLowerCase();
    const hit = items.find(it => (it.name || \"\").toLowerCase().trim() === target);
    return hit ? hit.id : null;
  } catch { return null; }
}"""

    fix2_new = """async function portFindIdByName(picklistKey, name) {
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

    if fix2_old_a in text:
        text = replace_once(text, fix2_old_a, fix2_new, "FIX 2 — portFindIdByName simplified (post-pagination-fix)")
    elif fix2_old_b in text:
        text = replace_once(text, fix2_old_b, fix2_new, "FIX 2 — portFindIdByName simplified (un-patched)")
    else:
        fail("Couldn't find portFindIdByName function.")

    BACKUP.write_text(original, encoding="utf-8")
    INDEX.write_text(text, encoding="utf-8")
    delta = len(text) - len(original)
    print(f"\n✓ Applied.")
    print(f"  Backup: {BACKUP.name}")
    print(f"  New size: {len(text):,} bytes (delta: {delta:+,})")
    print()
    print("Restart `python3 start.py` and try Validate again.")
    print()
    print("Note: the first floor/building/site/space row to validate will trigger")
    print("the full pagination load, which can take a few seconds for large accounts.")
    print("All subsequent rows reuse the cache — fast.")


if __name__ == "__main__":
    main()
