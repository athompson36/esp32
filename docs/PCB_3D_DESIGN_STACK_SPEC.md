# PCB & 3D Design Stack — Specification

**Purpose:** Define how the AI and lab get full access to the PCB design and 3D-printing/model design stacks: dimension-aware part mock-ups, AI-optimized enclosures, simple 3D previews, export in common formats, and optional upload to maker sites with account syncing.

**Status:** Spec / roadmap. Implements in phases.  
**Aligns with:** Project planning (BOM, pinouts, wiring, schematic, enclosure), [CYBERDECK_MANAGER_SPEC.md](CYBERDECK_MANAGER_SPEC.md) §10, inventory catalog, device registry.

---

## 1. Goals

| Goal | Description |
|------|--------------|
| **AI access to full stacks** | AI can reason over PCB design data (footprints, nets, layers, DRC) and 3D design data (enclosure geometry, part placement, printability). |
| **Dimension-aware mock-ups** | AI composes combinations of parts with known dimensions and placement; suggests layouts and clearances. |
| **AI-optimized enclosures** | Enclosure suggestions driven by project docs, use case, BOM, and part dimensions (size, cutouts, mounting). |
| **Simple 3D display** | UI shows simple 3D models of proposed parts and enclosure (primitives or lightweight meshes). |
| **Export all common formats** | PCB: Gerber, ODB++, KiCad project, netlist. 3D: STL, STEP, 3MF, OBJ. |
| **Maker site upload + sync** | Optional auto-upload to popular maker sites with stored account linking and sync of projects/versions. |

---

## 2. Data model (dimensions & placement)

### 2.1 Inventory / part dimensions

Parts in the catalog (and BOM) must expose **dimensions** so the AI and layout tools can use them.

**Source of truth:** Inventory items (`inventory/items/*.yaml`) and/or device registry. Add optional **specs** or a dedicated **dimensions** block.

**Proposed fields (per part):**

| Field | Type | Unit | Description |
|-------|------|------|-------------|
| `length_mm` | number | mm | Length (X). |
| `width_mm` | number | mm | Width (Y). |
| `height_mm` | number | mm | Height (Z). |
| `footprint` | string | — | PCB footprint name (e.g. `SOT-23-5`, `ESP32-WROOM-32`) for PCB stack. |
| `mounting` | string | — | `pcb`, `standoff`, `panel`, `none`. |
| `model_3d_url` | string | — | Optional URL or path to STEP/STL for 3D preview. |
| `model_3d_embed` | string | — | Optional inline primitive: `box`, `cylinder`, or reference to shared shape ID. |

Store in existing **specs** (e.g. `specs.length_mm`, `specs.footprint`) or extend schema with a **dimensions** object. AI and enclosure logic read these when composing mock-ups.

### 2.2 Placement and assembly

For each **project** (proposal), extend the design blob to include:

| Concept | Description |
|---------|-------------|
| **Part placements** | List of `{ part_id, x_mm, y_mm, z_mm, rotation_deg, ref_des }` for 3D/layout. |
| **Enclosure params** | Inner size, wall thickness, cutout list (rect/circle per face), mounting holes. |
| **PCB outline** | Optional board outline (polygon or L×W) for 2D/3D. |

AI suggests placements and enclosure params from BOM + dimensions + use case; user or tools can refine.

### 2.3 Enclosure representation

- **Parametric:** Width, depth, height, wall thickness, lid, cutouts, fillets (for AI and export to OpenSCAD/STEP).
- **Mesh:** Optional pre-generated STL/STEP for “baked” enclosure (e.g. from external CAD); store path or artifact ID.
- **AI output:** Enclosure block in project design (already exists as markdown); extend to structured JSON (dimensions, cutouts, material hints) plus optional generated files.

---

## 3. AI capabilities

### 3.1 Inputs the AI must have access to

- **Project docs:** Title, description, BOM, pin_outs, wiring, schematic notes, enclosure notes (current project planning payload).
- **Inventory + dimensions:** For each BOM item (and catalog), part id, name, dimensions (L/W/H), footprint, mounting, optional 3D ref.
- **Use case:** Free text or structured “use case” (portable, desktop, IP rating, mounting style) from project or prompt.
- **Device/board context:** From registry and `devices/*/` (pinmaps, mechanical notes) when the project targets a known device.

### 3.2 AI outputs (extended design)

- **BOM** (existing) + **placement hints:** Suggested (x, y, z), ref_des, orientation for key parts.
- **Enclosure suggestion:** Parametric description (box size, cutouts for display/USB/antenna, vent holes, mounting); optionally short markdown rationale.
- **Structured design block:** Extend DESIGN to include e.g. `placements`, `enclosure_params`, `pcb_outline` so downstream tools and 3D preview can consume them.

### 3.3 System prompt / context

- Project planning system prompt must be extended so the AI:
  - Knows it can suggest part placements and enclosure parameters using part dimensions.
  - Knows enclosure suggestions should match use case and project docs (size, cutouts, mounting).
- Provide **part dimensions** (and optional 3D refs) in the context sent to the AI when a project has a BOM (resolve BOM items to catalog and inject dimensions).

---

## 4. Simple 3D display

- **Goal:** Show simple 3D models of proposed parts and enclosure in the web UI.
- **Options:**
  - **Primitive-based:** Each part is a box (or cylinder) from dimensions; enclosure is a box with cutouts as transparent/subtract regions. Render with Three.js (or similar) in the project planning / hardware design area.
  - **Mesh-based:** Where `model_3d_url` or generated STL/STEP exists, load and display (Three.js + STLLoader/DRACOLoader; STEP may require conversion to STL or use a backend).
- **Scope (phase 1):** Primitive-only (boxes from L/W/H) for parts and enclosure; no full PCB 3D. Place parts in 3D space from placement list; allow rotate/pan/zoom.
- **Artifacts:** Generated enclosure STL/STEP can live under `artifacts/projects/<id>/enclosure.stl` (or similar) and be linked from the UI.

---

## 5. Export formats

### 5.1 PCB

| Format | Use | How |
|--------|-----|-----|
| **Gerber** | Fabrication (JLCPCB, PCBWay, etc.) | Export from KiCad/other EDA; or generate via script from netlist + footprint list. |
| **ODB++** | Alternative fab format | From EDA or converter. |
| **KiCad project** | Edit in KiCad | Generate/round-trip schematic + PCB from netlist, BOM, placements (scripts or plugin). |
| **Netlist** | Schematic/PCB import | Already have wiring (netlist-like); export as IPC-2581, or EDA-specific netlist. |

**Implementation:** Prefer integration with KiCad (headless or scripted) or SKiDL → KiCad so that “export” produces real Gerber/ODB++; netlist and pinout/wiring CSV already exist.

### 5.2 3D / enclosure

| Format | Use | How |
|--------|-----|-----|
| **STL** | 3D printing, slicing | Generate from parametric enclosure (OpenSCAD/FreeCAD script or internal generator). |
| **STEP** | CAD exchange, mechanical | Export from FreeCAD/OpenSCAD or parametric kernel. |
| **3MF** | Modern 3D print (multi-body, metadata) | Generate or convert from STL/STEP. |
| **OBJ** | Simple 3D viewers, some slicers | Convert from STL or generate. |

**Implementation:** Parametric enclosure (from AI or user) → script (OpenSCAD/FreeCAD Python) → STL/STEP; then optional conversion to 3MF/OBJ. Existing “export enclosure” as markdown stays; add “Export enclosure STL/STEP/3MF” in UI and API.

### 5.3 UI and API

- **Project planning / Hardware design:** Buttons or dropdown “Export as” for:
  - Pinout CSV, Wiring CSV, Schematic .md, Enclosure .md (existing).
  - **New:** Enclosure STL, Enclosure STEP, Enclosure 3MF (when enclosure geometry exists).
  - **New:** PCB Gerber (zip), Netlist (when PCB stack is present).
- **API:** e.g. `GET /api/projects/<id>/export/enclosure?format=stl|step|3mf` and `GET /api/projects/<id>/export/pcb?format=gerber|netlist` returning file or redirect to artifact.

---

## 6. Maker websites — upload and account sync

### 6.1 PCB

| Site | Typical use | Sync concept |
|------|-------------|--------------|
| **JLCPCB** | Fabrication + assembly | Account; upload Gerber + BOM; order. Sync = store project/revision link. |
| **PCBWay** | Fabrication | Upload Gerber; get quote. Sync = project/revision. |
| **OSHPark** | Quick-turn boards | Upload Gerber; shared project link. |

### 6.2 3D

| Site | Typical use | Sync concept |
|------|-------------|--------------|
| **Printables** | STL sharing, slicing, print logs | Account; upload STL/3MF; project page. Sync = project ID + version. |
| **Thingiverse** | STL sharing | Upload; project ID. |
| **Thangs** | Search + share | Upload; project ID. |

### 6.3 Account syncing (spec)

- **Stored credentials:** Per-site tokens or API keys in **artifacts** (e.g. `artifacts/maker_sites.json` or per-site encrypted store). Never log passwords; use OAuth or API keys where possible.
- **Sync semantics:** “Sync” = push current project export (Gerber zip or STL/STEP) to the site as a new revision or new project; store back the site’s project ID and revision/URL in the lab (e.g. in project proposal or `artifacts/projects/<id>/maker_links.json`).
- **UI:** “Upload to…” dropdown (JLCPCB, PCBWay, Printables, etc.); optional “Link account” flow; after upload show link to the site’s project page.
- **Implementation:** Phase 2+; depends on each site’s API (if any) or controlled browser automation; start with “export file + open site upload page” and manual paste, then add API integration where available.

---

## 7. Implementation phases

| Phase | Scope | Deliverables |
|-------|--------|---------------|
| **1 – Data & AI** | Dimensions in catalog/specs; extend project design with placements and enclosure_params; extend AI context and DESIGN block; prompt updates. | Schema/docs for dimensions; project design schema; AI suggests placements and enclosure from BOM + dimensions + use case. |
| **2 – 3D preview** | Simple 3D viewer in project planning UI: boxes for parts from dimensions, box for enclosure, placement list. | Three.js (or equivalent) viewer; load placements + dimensions; export enclosure STL/STEP from parametric or script. |
| **3 – Export** | Enclosure export STL/STEP/3MF/OBJ; PCB netlist/Gerber export (via KiCad or script). | API + UI “Export as”; artifacts for generated files. |
| **4 – Maker upload** | Link accounts (stored tokens); “Upload to JLCPCB/Printables/…” from current project export; store project/revision links. | artifacts config; upload flow; maker_links in project. |

---

## 8. File and API summary

| Item | Location / API |
|------|-----------------|
| Part dimensions | `inventory/items/*.yaml` → specs or dimensions; resolve in app when building AI context. |
| Placements / enclosure_params | Project proposal JSON (e.g. `design.placements`, `design.enclosure_params`). |
| Enclosure mesh | `artifacts/projects/<id>/enclosure.stl` (or .step, .3mf). |
| PCB export | `artifacts/projects/<id>/pcb_gerber.zip` (or similar). |
| Maker links | `artifacts/projects/<id>/maker_links.json` or inside proposal. |
| Export API | `GET /api/projects/<id>/export/enclosure?format=stl|step|3mf`; `GET /api/projects/<id>/export/pcb?format=gerber|netlist`. |
| Upload API | `POST /api/projects/<id>/upload-to?site=jlcpcb|printables|...` (phase 4). |

---

## 9. References

- Project planning (BOM, DESIGN): `inventory/app/app.py` (PROJECT_PLANNING_SYSTEM, export routes), `inventory/app/project_ops.py`.
- Inventory schema: `inventory/SCHEMA.md`.
- Cyberdeck CAD mention: `docs/CYBERDECK_MANAGER_SPEC.md` §10.
- Enclosure export (current): `GET /api/projects/<id>/export/enclosure` (markdown).
