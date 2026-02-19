"""
Datasheet upload, PDF text extraction, AI analysis, and design context for PCB/3D AI.
Design context files (dimensions, pinout, layout) are written to design_context/<id>.md
so the AI in charge of PCB and 3D print design can use them.
"""
import json
import os
import re
import tempfile

# Load config at runtime to avoid circular import
def _repo_root():
    from config import REPO_ROOT
    return REPO_ROOT


def _design_context_dir():
    from config import DESIGN_CONTEXT_DIR
    return DESIGN_CONTEXT_DIR


MAX_PDF_TEXT_CHARS = 80_000  # Keep under typical context limits; first pages usually have specs


def extract_text_from_pdf(file_path: str) -> str:
    """Extract text from a PDF file. Returns first MAX_PDF_TEXT_CHARS characters."""
    try:
        from pypdf import PdfReader
    except ImportError:
        return ""
    if not file_path or not os.path.isfile(file_path):
        return ""
    try:
        reader = PdfReader(file_path)
        parts = []
        n = 0
        for page in reader.pages:
            if n >= 100:  # Cap pages
                break
            try:
                text = page.extract_text()
                if text:
                    parts.append(text)
                    n += 1
            except Exception:
                continue
        raw = "\n\n".join(parts)
        return raw[:MAX_PDF_TEXT_CHARS].strip() if raw else ""
    except Exception:
        return ""


def analyze_datasheet_with_ai(text: str, existing_items: list, openai_client, model: str = "gpt-4o-mini") -> dict:
    """
    Use AI to analyze datasheet text. existing_items: list of {id, name, category}.
    Returns dict with: action ("assign"|"create"), matched_item_id?, suggested_id, name,
    category, dimensions, pinout, layout_notes, mcu?, manufacturer?, part_number?.
    """
    if not text.strip():
        return {"action": "create", "error": "No text extracted from PDF"}
    items_blob = "\n".join(
        f"- id={it.get('id')} name={it.get('name')} category={it.get('category')}"
        for it in (existing_items or [])[:200]
    )
    system = (
        "You are a hardware lab assistant. Given datasheet text and a list of existing inventory items (id, name, category), "
        "decide whether this datasheet matches an existing item or describes a new device/component. "
        "Reply with a single JSON object only, no markdown. Use this exact structure:\n"
        '{"action": "assign"|"create", "matched_item_id": "id or null", "suggested_id": "slug_id", "name": "Display name", '
        '"category": "controller|sbc|sensor|accessory|component", "dimensions": "LxWxH mm, mounting, etc.", '
        '"pinout": "pin table or summary", "layout_notes": "footprint, placement, mechanical", '
        '"mcu": "MCU or chip if applicable", "manufacturer": "", "part_number": ""}'
    )
    user = f"Existing inventory items:\n{items_blob}\n\n--- Datasheet excerpt ---\n{text[:60000]}"
    try:
        resp = openai_client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            max_tokens=2000,
        )
        raw = (resp.choices[0].message.content or "").strip()
        # Strip markdown code block if present
        if raw.startswith("```"):
            raw = re.sub(r"^```\w*\n?", "", raw)
            raw = re.sub(r"\n?```\s*$", "", raw)
        data = json.loads(raw)
        data.setdefault("action", "create")
        data.setdefault("suggested_id", data.get("name", "device").replace(" ", "_").lower()[:40])
        data["suggested_id"] = re.sub(r"[^a-z0-9_\-]", "_", (data.get("suggested_id") or "").lower()).strip("_") or "device"
        return data
    except json.JSONDecodeError as e:
        return {"action": "create", "error": f"AI response parse error: {e}", "suggested_id": "device"}
    except Exception as e:
        return {"action": "create", "error": str(e)[:200], "suggested_id": "device"}


def write_design_context(device_or_item_id: str, extracted: dict, extra_md: str = "") -> str:
    """
    Write design_context/<id>.md with dimensions, pinout, layout for PCB/3D AI.
    Returns relative path (design_context/<id>.md).
    """
    root = _repo_root()
    ctx_dir = _design_context_dir()
    device_or_item_id = (device_or_item_id or "").strip()
    if not device_or_item_id:
        return ""
    device_or_item_id = re.sub(r"[^a-z0-9_\-]", "_", device_or_item_id.lower()).strip("_") or "device"
    os.makedirs(ctx_dir, exist_ok=True)
    path = os.path.join(ctx_dir, f"{device_or_item_id}.md")
    name = extracted.get("name") or device_or_item_id
    lines = [
        f"# Design context — {name}",
        "",
        f"**ID:** `{device_or_item_id}`",
        f"**Category:** {extracted.get('category') or '—'}",
        f"**Manufacturer:** {extracted.get('manufacturer') or '—'}",
        f"**Part number:** {extracted.get('part_number') or '—'}",
        "",
        "---",
        "",
        "## Dimensions & mechanical",
        "",
        (extracted.get("dimensions") or "*(Extract from datasheet: length, width, height, mounting holes, keepouts.)*"),
        "",
        "---",
        "",
        "## Pinout",
        "",
        (extracted.get("pinout") or "*(Pin | Function | Notes — from datasheet.)*"),
        "",
        "---",
        "",
        "## Layout & footprint",
        "",
        (extracted.get("layout_notes") or "*(Footprint, placement, mechanical constraints for PCB/3D.)*"),
        "",
    ]
    if extra_md:
        lines.extend(["---", "", extra_md, ""])
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        return os.path.relpath(path, root).replace("\\", "/")
    except OSError:
        return ""


def save_datasheet_to_design_context(file_path: str, device_or_item_id: str) -> str:
    """
    Copy uploaded PDF to design_context/<id>_datasheet.pdf.
    Returns relative path from repo root for use as datasheet_file.
    """
    root = _repo_root()
    ctx_dir = _design_context_dir()
    device_or_item_id = (device_or_item_id or "").strip()
    if not device_or_item_id or not file_path or not os.path.isfile(file_path):
        return ""
    device_or_item_id = re.sub(r"[^a-z0-9_\-]", "_", device_or_item_id.lower()).strip("_") or "device"
    os.makedirs(ctx_dir, exist_ok=True)
    dest = os.path.join(ctx_dir, f"{device_or_item_id}_datasheet.pdf")
    try:
        import shutil
        shutil.copy2(file_path, dest)
        return os.path.relpath(dest, root).replace("\\", "/")
    except OSError:
        return ""
