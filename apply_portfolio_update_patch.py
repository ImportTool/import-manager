#!/usr/bin/env python3
"""
apply_portfolio_update_patch.py

Adds **Update mode** to the Portfolio tab (Sites / Buildings / Floors /
Spaces) of index.html. Same pattern as Update PPM and Update Assets.

How to run:
  1. Put this script in the SAME FOLDER as your `index.html` (the GitHub
     repo folder is fine — that's the one GitHub Desktop manages).
  2. Open Terminal and `cd` into that folder.
     (Or: Right-click the folder → Open Terminal at folder.)
  3. Run:   python3 apply_portfolio_update_patch.py
  4. The script writes a backup to index.html.before-portfolio-update.bak
     and modifies index.html in place.
  5. Open index.html in your browser (or commit + push via GitHub Desktop)
     to use the new Update mode.

If the script can't find one of the expected patterns it stops with a clear
message and DOES NOT modify the file.
"""

import sys
import os
import re
from pathlib import Path

INDEX = Path(__file__).parent / "index.html"
BACKUP = Path(__file__).parent / "index.html.before-portfolio-update.bak"


def fail(msg):
    print(f"\n[ERROR] {msg}")
    print("\nNo changes were written. Your index.html is untouched.")
    sys.exit(1)


def find_or_die(haystack, needle, label):
    if needle not in haystack:
        # Helpful diagnostic — try to find the closest line
        first_line = needle.strip().split("\n", 1)[0][:80]
        approx = haystack.find(first_line)
        approx_ctx = ""
        if approx != -1:
            ctx_start = max(0, approx - 60)
            ctx_end = min(len(haystack), approx + 200)
            approx_ctx = f"\n\nFound similar text at offset {approx}:\n  …{haystack[ctx_start:ctx_end]!r}…"
        fail(f"Couldn't find the expected text for: {label}\n"
             f"\nLooking for (first line):\n  {first_line!r}{approx_ctx}\n"
             f"\nYour index.html might be a different version than this patch expects. "
             f"If you've edited index.html manually, the patch's find-strings won't match.")
    return haystack


def replace_once(text, old, new, label):
    find_or_die(text, old, label)
    count = text.count(old)
    if count > 1:
        fail(f"Found the search string for '{label}' {count} times — expected exactly 1. "
             f"Either the file changed or this script is out of date.")
    return text.replace(old, new, 1)


def main():
    if not INDEX.exists():
        fail(f"index.html not found at {INDEX}. Put this script next to your index.html.")

    original = INDEX.read_text(encoding="utf-8")
    print(f"Read {INDEX} ({len(original):,} bytes)")

    # Bail out if it looks like the patch was already applied.
    if "PORT_UPDATE_COLUMN_DEFS" in original:
        fail("Looks like the Portfolio Update patch is already applied "
             "(PORT_UPDATE_COLUMN_DEFS is already in index.html). Nothing to do.")

    text = original

    # ---------- EDIT 1: portfolio HTML — add the Add/Update mode toggle ----------
    edit1_old = """      <div class="freq-tabs" id="portSubTabs" style="display:flex; gap:0; margin-top:12px; border-bottom:1px solid var(--line);">
        <button class="freq-tab active" data-portsub="site">Sites</button>
        <button class="freq-tab" data-portsub="building">Buildings</button>
        <button class="freq-tab" data-portsub="floor">Floors</button>
        <button class="freq-tab" data-portsub="space">Spaces</button>
      </div>
      <div id="portFormSelector" style="margin-top: 8px; font-size: 12px;"></div>"""
    edit1_new = """      <div class="freq-tabs" id="portModeTabs" style="display:flex; gap:0; margin-top:12px; border-bottom:1px solid var(--line);">
        <button class="freq-tab active" data-portmode="add">Add</button>
        <button class="freq-tab" data-portmode="update">Update</button>
      </div>
      <div class="freq-tabs" id="portSubTabs" style="display:flex; gap:0; margin-top:0; border-bottom:1px solid var(--line);">
        <button class="freq-tab active" data-portsub="site">Sites</button>
        <button class="freq-tab" data-portsub="building">Buildings</button>
        <button class="freq-tab" data-portsub="floor">Floors</button>
        <button class="freq-tab" data-portsub="space">Spaces</button>
      </div>
      <div id="portFormSelector" style="margin-top: 8px; font-size: 12px;"></div>"""
    text = replace_once(text, edit1_old, edit1_new, "EDIT 1 — Portfolio mode toggle HTML")

    # ---------- EDIT 2: state — add portUpdQueue + activePortMode ----------
    edit2_old = """  // Portfolio queues
  portQueue: { site: [], building: [], floor: [], space: [] },
  activePort: "site","""
    edit2_new = """  // Portfolio queues (add mode + update mode)
  portQueue: { site: [], building: [], floor: [], space: [] },
  portUpdQueue: { site: [], building: [], floor: [], space: [] },
  activePort: "site",
  activePortMode: "add","""
    text = replace_once(text, edit2_old, edit2_new, "EDIT 2 — state portUpdQueue/activePortMode")

    # ---------- EDIT 3: PORT_UPDATE_COLUMN_DEFS + blankPortRow(kind, mode) ----------
    edit3_old = """const PORT_LABELS = { site:"Site", building:"Building", floor:"Floor", space:"Space" };

function blankPortRow(kind) {
  const base = { custom: {}, _recordId: "" };
  if (kind === "site")     return { ...base, name:"", description:"", address:"", city:"", state:"", country:"", zip:"", latitude:"", longitude:"", area:"" };
  if (kind === "building") return { ...base, name:"", site:"", description:"", address:"", city:"", state:"", country:"", zip:"", latitude:"", longitude:"", grossFloorArea:"" };
  if (kind === "floor")    return { ...base, name:"", site:"", building:"", floorLevel:"", area:"", description:"" };
  if (kind === "space")    return { ...base, name:"", site:"", building:"", floor:"", parentSpace:"", spaceCategory:"", area:"", capacity:"", description:"" };
  return base;
}"""
    edit3_new = """const PORT_LABELS = { site:"Site", building:"Building", floor:"Floor", space:"Space" };

// Update mode columns — leftmost is Record ID *, all other columns optional.
// Mirrors ASSET_COLUMN_DEFS_UPDATE pattern: blank cells = no change to that field.
const PORT_UPDATE_COLUMN_DEFS = {
  site: [
    { key:"_num",       label:"#",         kind:"num",    width:"w-num",    sticky:true },
    { key:"_status",    label:"Status",    kind:"status", width:"w-status", sticky:true },
    { key:"id",         label:"Site ID *", kind:"text",   width:"w-sm" },
    { key:"name",       label:"Name",      kind:"text",   width:"w-md" },
    { key:"description",label:"Description",kind:"text",  width:"w-lg" },
    { key:"address",    label:"Address",   kind:"text",   width:"w-lg" },
    { key:"city",       label:"City",      kind:"text",   width:"w-md" },
    { key:"state",      label:"State",     kind:"text",   width:"w-md" },
    { key:"country",    label:"Country",   kind:"text",   width:"w-md" },
    { key:"zip",        label:"Zip",       kind:"text",   width:"w-sm" },
    { key:"latitude",   label:"Latitude",  kind:"text",   width:"w-sm" },
    { key:"longitude",  label:"Longitude", kind:"text",   width:"w-sm" },
    { key:"area",       label:"Area",      kind:"text",   width:"w-sm" },
    { key:"_actions",   label:"",          kind:"actions", width:"w-actions" }
  ],
  building: [
    { key:"_num",       label:"#",            kind:"num",    width:"w-num",    sticky:true },
    { key:"_status",    label:"Status",       kind:"status", width:"w-status", sticky:true },
    { key:"id",         label:"Building ID *",kind:"text",   width:"w-sm" },
    { key:"name",       label:"Name",         kind:"text",   width:"w-md" },
    { key:"site",       label:"Site",         kind:"text",   width:"w-md", picklist:"site" },
    { key:"description",label:"Description",  kind:"text",   width:"w-lg" },
    { key:"address",    label:"Address",      kind:"text",   width:"w-lg" },
    { key:"city",       label:"City",         kind:"text",   width:"w-md" },
    { key:"state",      label:"State",        kind:"text",   width:"w-md" },
    { key:"country",    label:"Country",      kind:"text",   width:"w-md" },
    { key:"zip",        label:"Zip",          kind:"text",   width:"w-sm" },
    { key:"latitude",   label:"Latitude",     kind:"text",   width:"w-sm" },
    { key:"longitude",  label:"Longitude",    kind:"text",   width:"w-sm" },
    { key:"grossFloorArea", label:"Gross Floor Area", kind:"text", width:"w-sm" },
    { key:"_actions",   label:"",             kind:"actions", width:"w-actions" }
  ],
  floor: [
    { key:"_num",       label:"#",         kind:"num",    width:"w-num",    sticky:true },
    { key:"_status",    label:"Status",    kind:"status", width:"w-status", sticky:true },
    { key:"id",         label:"Floor ID *",kind:"text",   width:"w-sm" },
    { key:"name",       label:"Name",      kind:"text",   width:"w-md" },
    { key:"site",       label:"Site",      kind:"text",   width:"w-md", picklist:"site" },
    { key:"building",   label:"Building",  kind:"text",   width:"w-md", picklist:"building" },
    { key:"floorLevel", label:"Floor Level", kind:"text", width:"w-sm" },
    { key:"area",       label:"Area",      kind:"text",   width:"w-sm" },
    { key:"description",label:"Description",kind:"text",  width:"w-lg" },
    { key:"_actions",   label:"",          kind:"actions", width:"w-actions" }
  ],
  space: [
    { key:"_num",       label:"#",         kind:"num",    width:"w-num",    sticky:true },
    { key:"_status",    label:"Status",    kind:"status", width:"w-status", sticky:true },
    { key:"id",         label:"Space ID *",kind:"text",   width:"w-sm" },
    { key:"name",       label:"Name",      kind:"text",   width:"w-md" },
    { key:"site",       label:"Site",      kind:"text",   width:"w-md", picklist:"site" },
    { key:"building",   label:"Building",  kind:"text",   width:"w-md", picklist:"building" },
    { key:"floor",      label:"Floor",     kind:"text",   width:"w-md", picklist:"floor" },
    { key:"parentSpace",label:"Parent Space",kind:"text", width:"w-md", picklist:"space" },
    { key:"spaceCategory", label:"Space Category", kind:"text", width:"w-md", picklist:"spaceCategory" },
    { key:"area",       label:"Area",      kind:"text",   width:"w-sm" },
    { key:"capacity",   label:"Capacity",  kind:"text",   width:"w-sm" },
    { key:"description",label:"Description",kind:"text",  width:"w-lg" },
    { key:"_actions",   label:"",          kind:"actions", width:"w-actions" }
  ]
};

function blankPortRow(kind, mode) {
  const base = { custom: {}, _recordId: "" };
  if (mode === "update") {
    if (kind === "site")     return { ...base, id:"", name:"", description:"", address:"", city:"", state:"", country:"", zip:"", latitude:"", longitude:"", area:"" };
    if (kind === "building") return { ...base, id:"", name:"", site:"", description:"", address:"", city:"", state:"", country:"", zip:"", latitude:"", longitude:"", grossFloorArea:"" };
    if (kind === "floor")    return { ...base, id:"", name:"", site:"", building:"", floorLevel:"", area:"", description:"" };
    if (kind === "space")    return { ...base, id:"", name:"", site:"", building:"", floor:"", parentSpace:"", spaceCategory:"", area:"", capacity:"", description:"" };
    return { ...base, id:"" };
  }
  if (kind === "site")     return { ...base, name:"", description:"", address:"", city:"", state:"", country:"", zip:"", latitude:"", longitude:"", area:"" };
  if (kind === "building") return { ...base, name:"", site:"", description:"", address:"", city:"", state:"", country:"", zip:"", latitude:"", longitude:"", grossFloorArea:"" };
  if (kind === "floor")    return { ...base, name:"", site:"", building:"", floorLevel:"", area:"", description:"" };
  if (kind === "space")    return { ...base, name:"", site:"", building:"", floor:"", parentSpace:"", spaceCategory:"", area:"", capacity:"", description:"" };
  return base;
}"""
    text = replace_once(text, edit3_old, edit3_new, "EDIT 3 — PORT_UPDATE_COLUMN_DEFS + blankPortRow(kind, mode)")

    # ---------- EDIT 4a: portColumnsFor signature + standard selection ----------
    edit4a_old = """function portColumnsFor(kind) {
  const standard = PORT_COLUMN_DEFS[kind];
  const entry = state.formsByModule[kind];
  const formFields = entry?.fields || [];
  const manual = getManualCustomFields(kind);
  if (!formFields.length && !manual.length) return standard;"""
    edit4a_new = """function portColumnsFor(kind, mode) {
  const effectiveMode = mode || state.activePortMode || "add";
  const standard = effectiveMode === "update"
    ? PORT_UPDATE_COLUMN_DEFS[kind]
    : PORT_COLUMN_DEFS[kind];
  const entry = state.formsByModule[kind];
  const formFields = entry?.fields || [];
  const manual = getManualCustomFields(kind);
  if (!formFields.length && !manual.length) return standard;"""
    text = replace_once(text, edit4a_old, edit4a_new, "EDIT 4a — portColumnsFor mode-aware signature")

    # ---------- EDIT 4b: portColumnsFor tail index (handle update layout) ----------
    # Make tailIdx match _actions too, so custom fields land before _actions
    # when there's no _recordId column (update mode).
    edit4b_old = """  const standardLowerKeys = new Set(standard.map(c => c.key.toLowerCase()));
  const tailIdx = standard.findIndex(c => c.key === "_recordId");
  const head = standard.slice(0, tailIdx === -1 ? standard.length : tailIdx);
  const tail = standard.slice(tailIdx === -1 ? standard.length : tailIdx);
  const seenCustom = new Set();
  const extras = [];
  for (const f of formFields) {
    if (!f.name || standardLowerKeys.has(f.name.toLowerCase()) || seenCustom.has(f.name)) continue;
    seenCustom.add(f.name);
    extras.push({
      key: "custom__" + f.name,
      label: (f.label || f.name) + (f.required ? " *" : ""),
      kind: "text", width: "w-md",
      customFieldName: f.name
    });
  }
  for (const name of manual) {
    if (!name || standardLowerKeys.has(name.toLowerCase()) || seenCustom.has(name)) continue;
    seenCustom.add(name);
    extras.push({
      key: "custom__" + name,
      label: name,
      kind: "text", width: "w-md",
      customFieldName: name
    });
  }
  return [...head, ...extras, ...tail];
}

function renderPortQueue() {"""
    edit4b_new = """  const standardLowerKeys = new Set(standard.map(c => c.key.toLowerCase()));
  const tailIdx = standard.findIndex(c => c.key === "_recordId" || c.key === "_actions");
  const head = standard.slice(0, tailIdx === -1 ? standard.length : tailIdx);
  const tail = standard.slice(tailIdx === -1 ? standard.length : tailIdx);
  const seenCustom = new Set();
  const extras = [];
  for (const f of formFields) {
    if (!f.name || standardLowerKeys.has(f.name.toLowerCase()) || seenCustom.has(f.name)) continue;
    seenCustom.add(f.name);
    extras.push({
      key: "custom__" + f.name,
      label: (f.label || f.name) + (f.required ? " *" : ""),
      kind: "text", width: "w-md",
      customFieldName: f.name
    });
  }
  for (const name of manual) {
    if (!name || standardLowerKeys.has(name.toLowerCase()) || seenCustom.has(name)) continue;
    seenCustom.add(name);
    extras.push({
      key: "custom__" + name,
      label: name,
      kind: "text", width: "w-md",
      customFieldName: name
    });
  }
  return [...head, ...extras, ...tail];
}

function renderPortQueue() {"""
    text = replace_once(text, edit4b_old, edit4b_new, "EDIT 4b — portColumnsFor tail index (incl _actions)")

    # ---------- EDIT 5: renderPortQueue mode-aware ----------
    edit5_old = """function renderPortQueue() {
  const kind = state.activePort;
  const cols = portColumnsFor(kind);
  const head = $("#portGridHead");
  if (!head) return;
  const table = head.closest("table");
  const existingColgroup = table.querySelector(":scope > colgroup");
  if (existingColgroup) existingColgroup.remove();
  delete head.dataset.built;
  buildGridHead(head, cols);

  const queue = state.portQueue[kind];
  const tbody = $("#portGrid tbody");
  tbody.innerHTML = queue.map((row, idx) =>
    `<tr>` + cols.map(c => renderCell(c, row, idx)).join("") + `</tr>`
  ).join("");
  $("#portRowCount").textContent = `${queue.length} row${queue.length === 1 ? "" : "s"}`;
  $$("#portSubTabs .freq-tab").forEach(b => b.classList.toggle("active", b.dataset.portsub === kind));
}"""
    edit5_new = """function renderPortQueue() {
  const kind = state.activePort;
  const mode = state.activePortMode || "add";
  const cols = portColumnsFor(kind, mode);
  const head = $("#portGridHead");
  if (!head) return;
  const table = head.closest("table");
  const existingColgroup = table.querySelector(":scope > colgroup");
  if (existingColgroup) existingColgroup.remove();
  delete head.dataset.built;
  buildGridHead(head, cols);

  const queue = mode === "update" ? state.portUpdQueue[kind] : state.portQueue[kind];
  const tbody = $("#portGrid tbody");
  tbody.innerHTML = queue.map((row, idx) =>
    `<tr>` + cols.map(c => renderCell(c, row, idx)).join("") + `</tr>`
  ).join("");
  $("#portRowCount").textContent = `${queue.length} row${queue.length === 1 ? "" : "s"}`;
  $$("#portSubTabs .freq-tab").forEach(b => b.classList.toggle("active", b.dataset.portsub === kind));
  $$("#portModeTabs .freq-tab").forEach(b => b.classList.toggle("active", b.dataset.portmode === mode));
}"""
    text = replace_once(text, edit5_old, edit5_new, "EDIT 5 — renderPortQueue mode-aware")

    # ---------- EDIT 6: validatePortRow mode-aware ----------
    edit6_old = """async function validatePortRow(row, kind) {
  const errors = [];
  if (!row.name) errors.push("Name required");

  if (kind === "building") {
    if (!row.site) errors.push("Site required for Building");
    else {
      row._siteId = await portFindIdByName("site", row.site);
      if (!row._siteId) errors.push(`Site "${row.site}" not found`);
    }
  } else if (kind === "floor") {"""
    edit6_new = """async function validatePortRow(row, kind, mode) {
  const effectiveMode = mode || state.activePortMode || "add";
  const errors = [];

  if (effectiveMode === "update") {
    if (!row.id) errors.push("Record ID required");
    else if (!/^\\d+$/.test(String(row.id).trim())) errors.push("Record ID must be numeric");
    const FIELD_KEYS = ["name","description","address","city","state","country","zip",
      "latitude","longitude","area","grossFloorArea","capacity","floorLevel",
      "site","building","floor","parentSpace","spaceCategory"];
    const hasUpdate = FIELD_KEYS.some(k => row[k] && String(row[k]).trim() !== "");
    const hasCustom = row.custom && Object.values(row.custom).some(v => v != null && String(v).trim() !== "");
    if (!hasUpdate && !hasCustom) errors.push("Fill at least one field to update");

    // Resolve parent lookups only when supplied — empty means no change.
    if (row.site)        { row._siteId = await portFindIdByName("site", row.site);
      if (!row._siteId) errors.push(`Site "${row.site}" not found`); }
    if (row.building)    { row._buildingId = await portFindIdByName("building", row.building);
      if (!row._buildingId) errors.push(`Building "${row.building}" not found`); }
    if (row.floor)       { row._floorId = await portFindIdByName("floor", row.floor);
      if (!row._floorId) errors.push(`Floor "${row.floor}" not found`); }
    if (row.parentSpace) { row._parentSpaceId = await portFindIdByName("space", row.parentSpace);
      if (!row._parentSpaceId) errors.push(`Parent space "${row.parentSpace}" not found`); }
    if (row.spaceCategory) {
      row._spaceCategoryId = await portFindIdByName("spaceCategory", row.spaceCategory);
      if (!row._spaceCategoryId) errors.push(`Space category "${row.spaceCategory}" not found`);
    }

    if (row.custom && Object.keys(row.custom).length) {
      const customErrors = await resolveRowCustomFields(kind, row);
      errors.push(...customErrors);
    }
    if (errors.length) { row.status = { kind:"error", text: errors.join("; ") }; return false; }
    row.status = { kind:"valid", text:"Valid" };
    return true;
  }

  // ---- ADD MODE ----
  if (!row.name) errors.push("Name required");

  if (kind === "building") {
    if (!row.site) errors.push("Site required for Building");
    else {
      row._siteId = await portFindIdByName("site", row.site);
      if (!row._siteId) errors.push(`Site "${row.site}" not found`);
    }
  } else if (kind === "floor") {"""
    text = replace_once(text, edit6_old, edit6_new, "EDIT 6 — validatePortRow mode-aware")

    # ---------- EDIT 7a: buildPortRecord mode-aware ----------
    edit7a_old = """function buildPortRecord(row, kind) {
  const out = { name: row.name };
  if (row.description) out.description = row.description;"""
    edit7a_new = """function buildPortRecord(row, kind, mode) {
  const effectiveMode = mode || state.activePortMode || "add";
  const out = {};
  if (effectiveMode === "update") {
    if (row.id) out.id = Number(row.id);
    if (row.name) out.name = row.name;
  } else {
    out.name = row.name;
  }
  if (row.description) out.description = row.description;"""
    text = replace_once(text, edit7a_old, edit7a_new, "EDIT 7a — buildPortRecord mode-aware")

    # ---------- EDIT 7b: importPortBatch mode-aware ----------
    edit7b_old = """async function importPortBatch(rows, kind) {
  const records = rows.map(r => buildPortRecord(r, kind));
  // Attach the selected form's id so any custom fields land in the right form.
  const formId = state.formsByModule[kind]?.selectedFormId;
  if (formId) records.forEach(rec => { rec.formId = Number(formId); });
  log(`Sending ${records.length} ${kind}: ${JSON.stringify(records[0])}`, "dim");
  const payload = { moduleName: kind, data: { [kind]: records } };
  const r = await api("POST", "maintenance/api/v3/modules/bulkCreate", payload);
  const back = r?.data?.[kind] || r?.data?.list || [];
  const arr = Array.isArray(back) ? back : Object.values(back || {});
  for (let i = 0; i < rows.length; i++) {
    if (arr[i]?.id) rows[i]._recordId = arr[i].id;
    rows[i].status = { kind:"success", text:"Imported" };
  }
  // Invalidate parent picklist caches so newly-created records are visible
  // immediately in the next sub-tab's autocomplete.
  if (kind === "site") state.cache.site = null;
  if (kind === "building") state.cache.building = null;
  if (kind === "floor") state.cache.floor = null;
  if (kind === "space") state.cache.space = null;
  renderPortQueue();
}"""
    edit7b_new = """async function importPortBatch(rows, kind, mode) {
  const effectiveMode = mode || state.activePortMode || "add";
  const records = rows.map(r => buildPortRecord(r, kind, effectiveMode));
  const formId = state.formsByModule[kind]?.selectedFormId;
  if (formId) records.forEach(rec => { rec.formId = Number(formId); });
  log(`Sending ${records.length} ${kind} (${effectiveMode}): ${JSON.stringify(records[0])}`, "dim");

  if (effectiveMode === "update") {
    // PATCH per row — Facilio doesn't have a bulkPatch for portfolio modules.
    for (let i = 0; i < rows.length; i++) {
      const row = rows[i];
      try {
        await api("PATCH",
          `maintenance/api/v3/modules/${kind}/${row.id}`,
          { id: Number(row.id), data: records[i], moduleName: kind });
        row.status = { kind:"success", text: "Updated" };
      } catch (e) {
        row.status = { kind:"error", text: "Update failed: " + e.message };
      }
      renderPortQueue();
    }
    if (kind === "site") state.cache.site = null;
    if (kind === "building") state.cache.building = null;
    if (kind === "floor") state.cache.floor = null;
    if (kind === "space") state.cache.space = null;
    return;
  }

  // ---- ADD MODE — bulkCreate ----
  const payload = { moduleName: kind, data: { [kind]: records } };
  const r = await api("POST", "maintenance/api/v3/modules/bulkCreate", payload);
  const back = r?.data?.[kind] || r?.data?.list || [];
  const arr = Array.isArray(back) ? back : Object.values(back || {});
  for (let i = 0; i < rows.length; i++) {
    if (arr[i]?.id) rows[i]._recordId = arr[i].id;
    rows[i].status = { kind:"success", text:"Imported" };
  }
  if (kind === "site") state.cache.site = null;
  if (kind === "building") state.cache.building = null;
  if (kind === "floor") state.cache.floor = null;
  if (kind === "space") state.cache.space = null;
  renderPortQueue();
}"""
    text = replace_once(text, edit7b_old, edit7b_new, "EDIT 7b — importPortBatch mode-aware")

    # ---------- EDIT 8: Portfolio event handlers in DOMContentLoaded ----------
    edit8_old = """  // ==== Portfolio tab — initialise grid + handlers ====
  for (const k of Object.keys(state.portQueue)) {
    if (!state.portQueue[k].length) state.portQueue[k].push(blankPortRow(k));
  }
  bindGridInputs(
    "#portGrid",
    () => state.portQueue[state.activePort],
    () => portColumnsFor(state.activePort),
    () => blankPortRow(state.activePort),
    renderPortQueue
  );

  $$("#portSubTabs .freq-tab").forEach(b => b.addEventListener("click", () => {
    state.activePort = b.dataset.portsub;
    renderPortQueue();
    initModuleForms(state.activePort);
    renderFormSelector(state.activePort);
  }));

  const addNewPortRow = () => {
    state.portQueue[state.activePort].push(blankPortRow(state.activePort));
    renderPortQueue();
  };
  $("#btnPortNewRow").addEventListener("click", addNewPortRow);
  $("#btnPortNewRow2").addEventListener("click", addNewPortRow);

  $("#btnPortValidate").addEventListener("click", async () => {
    for (const r of state.portQueue[state.activePort]) {
      r.status = { kind:"running", text:"Validating…" }; renderPortQueue();
      await validatePortRow(r, state.activePort);
      renderPortQueue();
    }
  });

  $("#btnPortImport").addEventListener("click", async () => {
    const kind = state.activePort;
    const queue = state.portQueue[kind];
    const valid = [];
    for (const r of queue) {
      if (r.status?.kind === "success") continue;
      const ok = await validatePortRow(r, kind);
      if (ok) valid.push(r);
    }
    renderPortQueue();
    if (!valid.length) { showToast("Nothing valid to import"); return; }
    const BATCH = 50;
    for (let i = 0; i < valid.length; i += BATCH) {
      const slice = valid.slice(i, i + BATCH);
      slice.forEach(r => r.status = { kind:"running", text:"Importing…" });
      renderPortQueue();
      try { await importPortBatch(slice, kind); }
      catch (e) {
        slice.forEach(r => r.status = { kind:"error", text: "Batch failed: " + e.message });
        renderPortQueue();
      }
    }
    showToast("Portfolio import complete");
  });

  $("#btnPortRemoveDone").addEventListener("click", () => {
    state.portQueue[state.activePort] = state.portQueue[state.activePort].filter(r => r.status?.kind !== "success");
    if (!state.portQueue[state.activePort].length) state.portQueue[state.activePort].push(blankPortRow(state.activePort));
    renderPortQueue();
  });
  $("#btnPortClearAll").addEventListener("click", () => {
    if (confirm(`Clear all ${PORT_LABELS[state.activePort]} rows?`)) {
      state.portQueue[state.activePort] = [blankPortRow(state.activePort)];
      renderPortQueue();
    }
  });"""
    edit8_new = """  // ==== Portfolio tab — initialise grid + handlers (Add + Update modes) ====
  for (const k of Object.keys(state.portQueue)) {
    if (!state.portQueue[k].length) state.portQueue[k].push(blankPortRow(k, "add"));
  }
  for (const k of Object.keys(state.portUpdQueue)) {
    if (!state.portUpdQueue[k].length) state.portUpdQueue[k].push(blankPortRow(k, "update"));
  }

  // Pick the active queue + a blank row based on current mode.
  const portActiveQueue = () => {
    const mode = state.activePortMode || "add";
    return (mode === "update" ? state.portUpdQueue : state.portQueue)[state.activePort];
  };
  const portBlankRow = () => blankPortRow(state.activePort, state.activePortMode || "add");

  bindGridInputs(
    "#portGrid",
    portActiveQueue,
    () => portColumnsFor(state.activePort, state.activePortMode || "add"),
    portBlankRow,
    renderPortQueue
  );

  // Module sub-tabs (Sites / Buildings / Floors / Spaces)
  $$("#portSubTabs .freq-tab").forEach(b => b.addEventListener("click", () => {
    state.activePort = b.dataset.portsub;
    renderPortQueue();
    initModuleForms(state.activePort);
    renderFormSelector(state.activePort);
  }));

  // Mode toggle (Add / Update)
  $$("#portModeTabs .freq-tab").forEach(b => b.addEventListener("click", () => {
    state.activePortMode = b.dataset.portmode;
    renderPortQueue();
  }));

  const addNewPortRow = () => {
    portActiveQueue().push(portBlankRow());
    renderPortQueue();
  };
  $("#btnPortNewRow").addEventListener("click", addNewPortRow);
  $("#btnPortNewRow2").addEventListener("click", addNewPortRow);

  $("#btnPortValidate").addEventListener("click", async () => {
    const mode = state.activePortMode || "add";
    for (const r of portActiveQueue()) {
      r.status = { kind:"running", text:"Validating…" }; renderPortQueue();
      await validatePortRow(r, state.activePort, mode);
      renderPortQueue();
    }
  });

  $("#btnPortImport").addEventListener("click", async () => {
    const kind = state.activePort;
    const mode = state.activePortMode || "add";
    const queue = portActiveQueue();
    const valid = [];
    for (const r of queue) {
      if (r.status?.kind === "success") continue;
      const ok = await validatePortRow(r, kind, mode);
      if (ok) valid.push(r);
    }
    renderPortQueue();
    if (!valid.length) { showToast("Nothing valid to " + (mode === "update" ? "update" : "import")); return; }
    const BATCH = mode === "update" ? 1 : 50;
    for (let i = 0; i < valid.length; i += BATCH) {
      const slice = valid.slice(i, i + BATCH);
      slice.forEach(r => r.status = { kind:"running", text: mode === "update" ? "Updating…" : "Importing…" });
      renderPortQueue();
      try { await importPortBatch(slice, kind, mode); }
      catch (e) {
        slice.forEach(r => r.status = { kind:"error", text: "Batch failed: " + e.message });
        renderPortQueue();
      }
    }
    showToast(`Portfolio ${mode} complete`);
  });

  $("#btnPortRemoveDone").addEventListener("click", () => {
    const queue = portActiveQueue();
    const filtered = queue.filter(r => r.status?.kind !== "success");
    if (state.activePortMode === "update") state.portUpdQueue[state.activePort] = filtered;
    else state.portQueue[state.activePort] = filtered;
    if (!filtered.length) portActiveQueue().push(portBlankRow());
    renderPortQueue();
  });
  $("#btnPortClearAll").addEventListener("click", () => {
    const mode = state.activePortMode || "add";
    if (confirm(`Clear all ${PORT_LABELS[state.activePort]} ${mode === "update" ? "update " : ""}rows?`)) {
      if (mode === "update") state.portUpdQueue[state.activePort] = [portBlankRow()];
      else state.portQueue[state.activePort] = [portBlankRow()];
      renderPortQueue();
    }
  });"""
    text = replace_once(text, edit8_old, edit8_new, "EDIT 8 — Portfolio event handlers")

    # ---------- EDIT 9: Disconnect handler clears portUpdQueue + activePortMode ----------
    edit9_old = """    for (const k of Object.keys(state.portQueue)) state.portQueue[k] = [];
    state.jpQueue = [];"""
    edit9_new = """    for (const k of Object.keys(state.portQueue)) state.portQueue[k] = [];
    for (const k of Object.keys(state.portUpdQueue)) state.portUpdQueue[k] = [];
    state.activePortMode = "add";
    state.jpQueue = [];"""
    text = replace_once(text, edit9_old, edit9_new, "EDIT 9 — Disconnect handler wipes portUpdQueue")

    # ----------------------------------------------------------------------
    # All edits applied successfully — write backup + patched file.
    # ----------------------------------------------------------------------
    BACKUP.write_text(original, encoding="utf-8")
    INDEX.write_text(text, encoding="utf-8")
    delta = len(text) - len(original)
    print(f"\n✓ Patch applied successfully.")
    print(f"  Backup written to: {BACKUP.name}")
    print(f"  New size:          {len(text):,} bytes  (delta: {delta:+,})")
    print()
    print("Next steps:")
    print("  • Open index.html in your browser to test, or")
    print("  • Commit the change via GitHub Desktop to deploy.")
    print()
    print("If anything looks wrong, restore the backup:")
    print(f"  mv {BACKUP.name} index.html")


if __name__ == "__main__":
    main()
