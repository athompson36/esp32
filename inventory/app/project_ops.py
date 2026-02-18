"""Project proposals: persist in artifacts/project_proposals (Docker mount)."""
import json
import os
import re
import time
import uuid

from config import PROJECT_PROPOSALS_DIR

# Order and keywords for inferring controller type from inventory (name, model, manufacturer).
# Used to default the project planning Controller dropdown to what the user has in stock.
CONTROLLER_ID_ORDER = ["esp32", "raspberry_pi", "teensy", "arduino", "pine64", "esp32_sbc", "other"]
INVENTORY_CONTROLLER_KEYWORDS = [
    ("esp32", ["esp32", "espressif", "t-beam", "t-deck", "heltec"]),
    ("raspberry_pi", ["raspberry", "rpi", "bcm271", "pi 4", "pi 5", "pi zero", "pico"]),
    ("teensy", ["teensy", "pjrc"]),
    ("arduino", ["arduino", "atmega", "nano", "uno", "mega", "leonardo"]),
    ("pine64", ["pine64", "pine 64", "rock64", "rockpro64", "rock 64"]),
]


def ensure_proposals_dir():
    os.makedirs(PROJECT_PROPOSALS_DIR, exist_ok=True)


def _safe_id(s):
    return re.sub(r"[^\w\-]", "_", (s or "").strip())[:80] or "project"


def list_proposals():
    """Return list of { id, title, updated_at } sorted by updated_at desc."""
    ensure_proposals_dir()
    out = []
    for name in os.listdir(PROJECT_PROPOSALS_DIR):
        if not name.endswith(".json"):
            continue
        path = os.path.join(PROJECT_PROPOSALS_DIR, name)
        if not os.path.isfile(path):
            continue
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            out.append({
                "id": data.get("id") or name[:-5],
                "title": data.get("title") or name[:-5],
                "updated_at": data.get("updated_at") or str(int(os.path.getmtime(path))),
            })
        except (json.JSONDecodeError, OSError):
            continue
    out.sort(key=lambda x: x.get("updated_at") or "0", reverse=True)
    return out


def load_proposal(proposal_id):
    """Load full proposal by id. Returns dict or None."""
    ensure_proposals_dir()
    path = os.path.join(PROJECT_PROPOSALS_DIR, proposal_id + ".json")
    if not os.path.isfile(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def save_proposal(data):
    """Save proposal. data must have 'id' or we generate one; 'title' used for filename. Returns id."""
    ensure_proposals_dir()
    proposal_id = (data.get("id") or "").strip()
    if not proposal_id:
        proposal_id = _safe_id(data.get("title") or "project") + "_" + str(uuid.uuid4())[:8]
        data["id"] = proposal_id
    data["updated_at"] = str(int(time.time()))
    if "created_at" not in data:
        data["created_at"] = data["updated_at"]
    path = os.path.join(PROJECT_PROPOSALS_DIR, proposal_id + ".json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return proposal_id


def get_controllers_in_inventory(conn):
    """
    Infer which project controller types (esp32, raspberry_pi, etc.) the user has in inventory.
    Queries items in category 'controller' or 'sbc' and matches name/model/manufacturer to keywords.
    Returns list of controller_ids in CONTROLLER_ID_ORDER (so UI can default to first in list).
    """
    if not conn:
        return []
    try:
        rows = conn.execute(
            "SELECT name, model, manufacturer FROM items WHERE category IN (?, ?)",
            ("controller", "sbc"),
        ).fetchall()
    except Exception:
        return []
    found = set()
    for row in rows:
        name = (row[0] or "").lower()
        model = (row[1] or "").lower()
        mfr = (row[2] or "").lower()
        combined = " ".join([name, model, mfr])
        for cid, keywords in INVENTORY_CONTROLLER_KEYWORDS:
            if any(kw in combined for kw in keywords):
                found.add(cid)
                break
    return [cid for cid in CONTROLLER_ID_ORDER if cid in found]


def check_bom_against_inventory(conn, bom_rows):
    """
    For each BOM row (dict with name, part_number optional, quantity), look up in items.
    Returns list of dicts: name, part_number, quantity (needed), in_stock (bool), qty_on_hand, shortfall.
    """
    if not conn or not bom_rows:
        return []
    result = []
    for row in bom_rows:
        name = (row.get("name") or "").strip()
        part_number = (row.get("part_number") or "").strip()
        qty_need = int(row.get("quantity") or 0)
        qty_have = 0
        # Prefer part_number match, then name match
        if part_number:
            cur = conn.execute(
                "SELECT id, name, quantity FROM items WHERE part_number = ? OR part_number LIKE ?",
                (part_number, f"%{part_number}%"),
            )
            r = cur.fetchone()
            if r:
                qty_have = int(r[2] or 0)
        if qty_have == 0 and name:
            cur = conn.execute(
                "SELECT id, name, quantity FROM items WHERE name LIKE ? OR id = ?",
                (f"%{name}%", _safe_id(name).replace("_", " ")),
            )
            r = cur.fetchone()
            if r:
                qty_have = int(r[2] or 0)
        shortfall = max(0, qty_need - qty_have)
        result.append({
            "name": name or part_number or "?",
            "part_number": part_number,
            "quantity": qty_need,
            "in_stock": qty_have >= qty_need,
            "qty_on_hand": qty_have,
            "shortfall": shortfall,
        })
    return result


def bom_csv_digikey(bom_rows):
    """CSV suitable for Digi-Key BOM upload: Manufacturer Part Number, Quantity (and optional Description)."""
    lines = ["Manufacturer Part Number,Quantity,Description"]
    for row in bom_rows:
        pn = (row.get("part_number") or "").strip()
        if not pn:
            continue
        qty = int(row.get("quantity") or 0)
        desc = (row.get("name") or "").replace('"', '""')
        lines.append(f'"{pn}",{qty},"{desc}"')
    return "\n".join(lines)


def bom_csv_mouser(bom_rows):
    """CSV suitable for Mouser BOM import: Manufacturer Part Number, Quantity (and optional Description)."""
    lines = ["Manufacturer Part Number,Quantity,Description"]
    for row in bom_rows:
        pn = (row.get("part_number") or "").strip()
        if not pn:
            continue
        qty = int(row.get("quantity") or 0)
        desc = (row.get("name") or "").replace('"', '""')
        lines.append(f'"{pn}",{qty},"{desc}"')
    return "\n".join(lines)
