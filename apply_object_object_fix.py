#!/usr/bin/env python3
"""
apply_object_object_fix.py

Fixes two related bugs in index.html:

1. Custom-field cells displaying "[object Object]" — happens whenever a
   Lookup-type custom field's value has been resolved into a {id: N} object.
   Now the renderer shows the resolved numeric ID instead.

2. Re-validating a row containing an already-resolved {id: N} value used to
   crash with `"[object Object]" not found in <module>`. Now validation
   treats any pre-resolved object as a passthrough.

How to run:
  1. Put this script in the same folder as index.html.
  2. cd into that folder.
  3. python3 apply_object_object_fix.py

Writes a backup to index.html.before-object-object-fix.bak then patches
index.html in place. Aborts cleanly if the expected text isn't found.
"""

import sys
from pathlib import Path

INDEX = Path(__file__).parent / "index.html"
BACKUP = Path(__file__).parent / "index.html.before-object-object-fix.bak"


def fail(msg):
    print(f"\n[ERROR] {msg}")
    print("\nNo changes were written. Your index.html is untouched.")
    sys.exit(1)


def replace_once(text, old, new, label):
    if old not in text:
        first_line = old.strip().split("\n", 1)[0][:80]
        fail(f"Couldn't find expected text for: {label}\n"
             f"\nLooking for (first line):\n  {first_line!r}\n"
             f"\nYour index.html may already have this fix applied, "
             f"or has been edited away from the version this script expects.")
    count = text.count(old)
    if count > 1:
        fail(f"Found '{label}' {count} times — expected exactly 1.")
    return text.replace(old, new, 1)


def main():
    if not INDEX.exists():
        fail(f"index.html not found at {INDEX}.")

    original = INDEX.read_text(encoding="utf-8")
    print(f"Read {INDEX} ({len(original):,} bytes)")

    if "// OBJECT_OBJECT_FIX_APPLIED" in original:
        fail("Looks like this fix is already applied (sentinel comment present).")

    text = original

    # ---------- FIX 1: renderCell — show object.id instead of "[object Object]" ----------
    fix1_old = """  // Custom fields are stored under row.custom[name]
  const isCustom = col.customFieldName != null;
  const v = isCustom ? (row.custom?.[col.customFieldName] ?? "") : (row[col.key] ?? "");
  if (col.kind === "select") {"""
    fix1_new = """  // Custom fields are stored under row.custom[name]
  const isCustom = col.customFieldName != null;
  let v = isCustom ? (row.custom?.[col.customFieldName] ?? "") : (row[col.key] ?? "");
  // OBJECT_OBJECT_FIX_APPLIED — already-resolved Lookup values come through
  // as {id: <number>}. Render the id, otherwise we'd stringify to "[object Object]".
  if (v && typeof v === "object" && v.id != null) v = v.id;
  if (col.kind === "select") {"""
    text = replace_once(text, fix1_old, fix1_new, "FIX 1 — renderCell handles {id} objects")

    # ---------- FIX 2: resolveCustomFieldValue — idempotent on {id:N} ----------
    fix2_old = """async function resolveCustomFieldValue(moduleName, fieldKey, rawValue) {
  const v = rawValue;
  if (v === "" || v == null) return undefined;
  // Pure number — assume it's already an ID (works for both lookup and number fields)
  if (/^\\d+$/.test(String(v).trim())) return Number(v);"""
    fix2_new = """async function resolveCustomFieldValue(moduleName, fieldKey, rawValue) {
  const v = rawValue;
  if (v === "" || v == null) return undefined;
  // Already-resolved Lookup value — pass through untouched so re-validation
  // doesn't try to look up an object as if it were a name.
  if (typeof v === "object" && v !== null) {
    return v.id != null ? v : undefined;
  }
  // Detect the literal string "[object Object]" — happens when a previous
  // round mutated the value to an object, the grid stringified it back to
  // the cell, and the user then re-validated. There's nothing useful we
  // can do with it; surface a clear error so they know to re-enter.
  if (String(v).trim().toLowerCase() === "[object object]") {
    throw new Error(`Custom field ${fieldKey} has a corrupted "[object Object]" value — clear the cell and re-enter the name or numeric ID`);
  }
  // Pure number — assume it's already an ID (works for both lookup and number fields)
  if (/^\\d+$/.test(String(v).trim())) return Number(v);"""
    text = replace_once(text, fix2_old, fix2_new, "FIX 2 — resolveCustomFieldValue idempotent")

    BACKUP.write_text(original, encoding="utf-8")
    INDEX.write_text(text, encoding="utf-8")
    delta = len(text) - len(original)
    print(f"\n✓ Both fixes applied.")
    print(f"  Backup: {BACKUP.name}")
    print(f"  New size: {len(text):,} bytes (delta: {delta:+,})")
    print()
    print("To restore:")
    print(f"  mv {BACKUP.name} index.html")


if __name__ == "__main__":
    main()
