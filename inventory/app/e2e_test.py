#!/usr/bin/env python3
"""
E2E tests for inventory web app: all endpoints and basic UI flows.
Usage: python inventory/app/e2e_test.py [BASE_URL]
Default BASE_URL: http://127.0.0.1:5050
"""
import json
import sys
import urllib.error
import urllib.request
from urllib.parse import urljoin

BASE_URL = (sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:5050").rstrip("/")


def request(method, path, data=None, expect_status=None):
    url = urljoin(BASE_URL + "/", path.lstrip("/"))
    req = urllib.request.Request(url, method=method)
    if data is not None:
        req.add_header("Content-Type", "application/json")
        req.data = json.dumps(data).encode("utf-8")
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            body = r.read().decode("utf-8")
            try:
                body = json.loads(body) if body.strip() else None
            except json.JSONDecodeError:
                pass
            return r.status, body
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        try:
            body = json.loads(body) if body.strip() else None
        except json.JSONDecodeError:
            pass
        return e.code, body
    except urllib.error.URLError as e:
        return None, str(e.reason)
    except Exception as e:
        return None, str(e)


def get(path, expect_status=200):
    status, body = request("GET", path)
    ok = status == expect_status
    return ok, status, body


def post(path, data, expect_status=(200, 201)):
    status, body = request("POST", path, data=data)
    ok = status in (expect_status,) if isinstance(expect_status, int) else status in expect_status
    return ok, status, body


def put(path, data, expect_status=200):
    status, body = request("PUT", path, data=data)
    return status == expect_status, status, body


def main():
    failed = []
    print(f"E2E base URL: {BASE_URL}\n")

    # --- HTML ---
    ok, status, _ = get("/")
    print(f"GET /                    -> {status} {'OK' if ok else 'FAIL'}")
    if not ok:
        failed.append(("GET /", status))

    # --- Settings ---
    ok, status, _ = get("/api/settings/ai")
    print(f"GET /api/settings/ai     -> {status} {'OK' if ok else 'FAIL'}")
    if not ok:
        failed.append(("GET /api/settings/ai", status))

    ok, status, _ = get("/api/settings/paths")
    print(f"GET /api/settings/paths  -> {status} {'OK' if ok else 'FAIL'}")
    if not ok:
        failed.append(("GET /api/settings/paths", status))

    # --- Categories (from DB) ---
    ok, status, body = get("/api/categories")
    print(f"GET /api/categories      -> {status} {'OK' if ok else 'FAIL'}")
    if not ok:
        failed.append(("GET /api/categories", status))
    categories = body.get("categories", []) if isinstance(body, dict) else []

    # --- Items (from DB) ---
    ok, status, body = get("/api/items")
    print(f"GET /api/items           -> {status} {'OK' if ok else 'FAIL'}")
    if not ok:
        failed.append(("GET /api/items", status))
    items = body.get("items", []) if isinstance(body, dict) else []
    first_id = items[0].get("id") if items else None

    if first_id:
        ok, status, _ = get(f"/api/items/{first_id}")
        print(f"GET /api/items/<id>       -> {status} {'OK' if ok else 'FAIL'}")
        if not ok:
            failed.append((f"GET /api/items/{first_id}", status))
    else:
        ok, status, _ = get("/api/items/nonexistent")
        print(f"GET /api/items/<id>       -> {status} (expect 404) {'OK' if status == 404 else 'FAIL'}")

    # --- Docker ---
    ok, status, _ = get("/api/docker/status")
    print(f"GET /api/docker/status   -> {status} {'OK' if ok else 'FAIL'}")
    if not ok and status != 503:
        failed.append(("GET /api/docker/status", status))

    ok, status, _ = get("/api/docker/containers")
    print(f"GET /api/docker/containers -> {status} {'OK' if ok or status == 503 else 'FAIL'}")

    ok, status, _ = get("/api/docker/tools")
    print(f"GET /api/docker/tools    -> {status} {'OK' if ok else 'FAIL'}")
    if not ok:
        failed.append(("GET /api/docker/tools", status))

    # --- Updates ---
    ok, status, _ = get("/api/updates")
    print(f"GET /api/updates         -> {status} {'OK' if ok else 'FAIL'}")
    if not ok:
        failed.append(("GET /api/updates", status))

    # --- Flash ---
    ok, status, _ = get("/api/flash/ports")
    print(f"GET /api/flash/ports     -> {status} {'OK' if ok else 'FAIL'}")
    if not ok:
        failed.append(("GET /api/flash/ports", status))

    ok, status, _ = get("/api/flash/devices")
    print(f"GET /api/flash/devices   -> {status} {'OK' if ok else 'FAIL'}")
    if not ok:
        failed.append(("GET /api/flash/devices", status))

    ok, status, _ = get("/api/flash/artifacts")
    print(f"GET /api/flash/artifacts -> {status} {'OK' if ok else 'FAIL'}")
    if not ok:
        failed.append(("GET /api/flash/artifacts", status))

    # --- Projects ---
    ok, status, body = get("/api/projects")
    print(f"GET /api/projects        -> {status} {'OK' if ok else 'FAIL'}")
    if not ok:
        failed.append(("GET /api/projects", status))

    # Create a project for project-scoped endpoints
    ok, status, body = post("/api/projects", {"title": "E2E test project", "description": "E2E", "parts_bom": [], "conversation": []})
    print(f"POST /api/projects       -> {status} {'OK' if ok else 'FAIL'}")
    if not ok:
        failed.append(("POST /api/projects", status))

    proposal_id = body.get("id") if isinstance(body, dict) else None
    if proposal_id:
        ok, status, _ = get(f"/api/projects/{proposal_id}")
        print(f"GET /api/projects/<id>    -> {status} {'OK' if ok else 'FAIL'}")
        if not ok:
            failed.append((f"GET /api/projects/{proposal_id}", status))

        ok, status, _ = put(f"/api/projects/{proposal_id}", {"title": "E2E updated", "description": "", "parts_bom": [], "conversation": []})
        print(f"PUT /api/projects/<id>   -> {status} {'OK' if ok else 'FAIL'}")
        if not ok:
            failed.append((f"PUT /api/projects/{proposal_id}", status))

        ok, status, _ = get(f"/api/projects/{proposal_id}/check-inventory")
        print(f"GET .../check-inventory   -> {status} {'OK' if ok else 'FAIL'}")
        if not ok:
            failed.append((f"GET .../check-inventory", status))

        ok, status, _ = get(f"/api/projects/{proposal_id}/bom/digikey")
        print(f"GET .../bom/digikey      -> {status} {'OK' if ok else 'FAIL'} (csv)")

        ok, status, _ = get(f"/api/projects/{proposal_id}/bom/mouser")
        print(f"GET .../bom/mouser      -> {status} {'OK' if ok else 'FAIL'} (csv)")

        ok, status, _ = get(f"/api/projects/{proposal_id}/export/pinout")
        print(f"GET .../export/pinout    -> {status} {'OK' if ok else 'FAIL'}")

        ok, status, _ = get(f"/api/projects/{proposal_id}/export/wiring")
        print(f"GET .../export/wiring    -> {status} {'OK' if ok else 'FAIL'}")

        ok, status, _ = get(f"/api/projects/{proposal_id}/export/schematic")
        print(f"GET .../export/schematic -> {status} {'OK' if ok else 'FAIL'}")

        ok, status, _ = get(f"/api/projects/{proposal_id}/export/enclosure")
        print(f"GET .../export/enclosure -> {status} {'OK' if ok else 'FAIL'}")

    # --- Frontend: endpoints the UI calls on load ---
    print("\n--- Frontend load (same endpoints the UI calls) ---")
    ok, status, body = get("/api/items")
    n_items = len(body.get("items", [])) if isinstance(body, dict) else 0
    print(f"  /api/items -> {n_items} items")
    ok, status, body = get("/api/categories")
    n_cat = len(body.get("categories", [])) if isinstance(body, dict) else 0
    print(f"  /api/categories -> {n_cat} categories")
    ok, status, body = get("/api/settings/ai")
    print(f"  /api/settings/ai -> api_key_set={body.get('api_key_set') if isinstance(body, dict) else '?'}")
    ok, status, body = get("/api/settings/paths")
    print(f"  /api/settings/paths -> database_path set={bool((body or {}).get('database_path'))}")

    print()
    if failed:
        print(f"FAILED: {len(failed)}")
        for name, status in failed:
            print(f"  {name} -> {status}")
        sys.exit(1)
    print("All E2E checks passed.")
    sys.exit(0)


if __name__ == "__main__":
    main()
