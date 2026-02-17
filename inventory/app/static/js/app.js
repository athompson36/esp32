(function () {
  const searchEl = document.getElementById("search");
  const categoryEl = document.getElementById("category");
  const btnSearch = document.getElementById("btn-search");
  const tbody = document.getElementById("tbody");
  const resultsCount = document.getElementById("results-count");
  const aiQueryEl = document.getElementById("ai-query");
  const btnAi = document.getElementById("btn-ai");
  const aiAnswerEl = document.getElementById("ai-answer");
  const detailPanel = document.getElementById("detail-panel");
  const detailContent = document.getElementById("detail-content");
  const closeDetail = document.getElementById("close-detail");

  const TAB_STORAGE_KEY = "inventory-app-tab";

  function switchTab(tabId) {
    const panels = document.querySelectorAll(".tab-panels .tab-panel");
    const buttons = document.querySelectorAll(".tabs .tab-btn");
    const targetPanel = document.getElementById("panel-" + tabId);
    const targetBtn = document.getElementById("tab-btn-" + tabId);
    if (!targetPanel || !targetBtn) return;
    panels.forEach((p) => {
      p.classList.remove("active");
      p.setAttribute("hidden", "");
      p.setAttribute("aria-hidden", "true");
    });
    buttons.forEach((b) => {
      b.classList.remove("active");
      b.setAttribute("aria-selected", "false");
    });
    targetPanel.classList.add("active");
    targetPanel.removeAttribute("hidden");
    targetPanel.setAttribute("aria-hidden", "false");
    targetBtn.classList.add("active");
    targetBtn.setAttribute("aria-selected", "true");
    try { sessionStorage.setItem(TAB_STORAGE_KEY, tabId); } catch (e) {}
  }

  function initTabs() {
    const btns = document.querySelectorAll(".tabs .tab-btn");
    btns.forEach((btn) => {
      btn.addEventListener("click", () => {
        const tabId = btn.getAttribute("data-tab");
        if (tabId) switchTab(tabId);
      });
    });
    const savedTab = (function () {
      try { return sessionStorage.getItem(TAB_STORAGE_KEY); } catch (e) { return null; }
    })();
    if (savedTab && document.getElementById("panel-" + savedTab)) {
      switchTab(savedTab);
    } else {
      switchTab("search");
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initTabs);
  } else {
    initTabs();
  }

  function loadCategories() {
    fetch("/api/categories")
      .then((r) => r.json())
      .then((data) => {
        categoryEl.innerHTML = '<option value="">All categories</option>';
        (data.categories || []).forEach((cat) => {
          const opt = document.createElement("option");
          opt.value = cat;
          opt.textContent = cat;
          categoryEl.appendChild(opt);
        });
      })
      .catch((err) => console.error(err));
  }

  function buildQueryParams() {
    const params = new URLSearchParams();
    const q = searchEl.value.trim();
    const cat = categoryEl.value.trim();
    if (q) params.set("q", q);
    if (cat) params.set("category", cat);
    params.set("limit", "500");
    return params.toString();
  }

  function renderTable(items) {
    resultsCount.textContent = items.total != null ? items.total : items.length;
    const list = items.items || items;
    tbody.innerHTML = list
      .map(
        (it) => `
      <tr data-id="${escapeHtml(it.id)}">
        <td class="name">${escapeHtml(it.name)}</td>
        <td class="category">${escapeHtml(it.category)}</td>
        <td class="qty">${it.quantity != null ? it.quantity : ""}</td>
        <td>${escapeHtml(it.part_number || "")}</td>
        <td>${escapeHtml(it.location || "")}</td>
        <td>${it.datasheet_url ? '<a href="' + escapeHtml(it.datasheet_url) + '" target="_blank" rel="noopener">Link</a>' : ""}</td>
      </tr>
    `
      )
      .join("");

    tbody.querySelectorAll("tr").forEach((row) => {
      row.addEventListener("click", () => openDetail(row.dataset.id));
    });
  }

  function fetchItems(queryString) {
    const url = queryString ? "/api/items?" + queryString : "/api/items";
    fetch(url)
      .then((r) => {
        if (!r.ok) throw new Error(r.statusText);
        return r.json();
      })
      .then(renderTable)
      .catch((err) => {
        resultsCount.textContent = "—";
        tbody.innerHTML = "<tr><td colspan=\"6\">Error: " + escapeHtml(err.message) + "</td></tr>";
      });
  }

  function runSearch() {
    fetchItems(buildQueryParams());
  }

  function runAiQuery() {
    const query = aiQueryEl.value.trim();
    if (!query) return;
    aiAnswerEl.textContent = "";
    aiAnswerEl.classList.add("has-content");
    fetch("/api/ai/query/stream", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query }),
    })
      .then((r) => {
        if (!r.ok) return r.json().then((j) => { throw new Error(j.error || r.statusText); });
        return r.body.getReader();
      })
      .then((reader) => {
        const decoder = new TextDecoder();
        let buffer = "";
        let items = [];
        function pump() {
          return reader.read().then(({ done, value }) => {
            if (value) {
              buffer += decoder.decode(value, { stream: true });
              const lines = buffer.split("\n");
              buffer = lines.pop() || "";
              for (const line of lines) {
                if (line.startsWith("data: ")) {
                  try {
                    const data = JSON.parse(line.slice(6));
                    if (data.delta) aiAnswerEl.appendChild(document.createTextNode(data.delta));
                    if (data.done && data.items) {
                      items = data.items || [];
                      renderTable({ items, total: items.length });
                    }
                  } catch (e) { /* skip */ }
                }
              }
            }
            if (!done) return pump();
            if (buffer.startsWith("data: ")) {
              try {
                const data = JSON.parse(buffer.slice(6));
                if (data.delta) aiAnswerEl.appendChild(document.createTextNode(data.delta));
                if (data.done && data.items) {
                  items = data.items || [];
                  renderTable({ items, total: items.length });
                }
              } catch (e) { /* skip */ }
            }
          });
        }
        return pump();
      })
      .catch((err) => {
        aiAnswerEl.textContent = "Error: " + err.message;
      });
  }

  function setupVoiceInput(inputEl, btnEl) {
    if (!inputEl || !btnEl) return;
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      btnEl.title = "Voice not supported in this browser";
      btnEl.disabled = true;
      return;
    }
    let listening = false;
    let recognition = null;
    btnEl.addEventListener("click", () => {
      if (listening && recognition) {
        recognition.stop();
        return;
      }
      recognition = new SpeechRecognition();
      recognition.continuous = true;
      recognition.interimResults = true;
      recognition.lang = "en-US";
      recognition.onresult = (e) => {
        for (let i = e.resultIndex; i < e.results.length; i++) {
          if (e.results[i].isFinal) {
            const transcript = e.results[i][0].transcript;
            inputEl.value = (inputEl.value + " " + transcript).trim();
          }
        }
      };
      recognition.onend = () => {
        listening = false;
        btnEl.classList.remove("voice-active");
      };
      recognition.onerror = () => {
        listening = false;
        btnEl.classList.remove("voice-active");
      };
      recognition.start();
      listening = true;
      btnEl.classList.add("voice-active");
    });
  }
  setupVoiceInput(aiQueryEl, document.getElementById("btn-ai-voice"));
  setupVoiceInput(document.getElementById("project-message"), document.getElementById("btn-project-voice"));

  function openDetail(id) {
    fetch("/api/items/" + encodeURIComponent(id))
      .then((r) => {
        if (!r.ok) throw new Error("Not found");
        return r.json();
      })
      .then((item) => {
        const specStr =
          item.specs && Object.keys(item.specs).length
            ? JSON.stringify(item.specs, null, 2)
            : "—";
        const tagsStr = item.tags && item.tags.length ? item.tags.join(", ") : "—";
        const usedInStr = item.used_in && item.used_in.length ? item.used_in.join(", ") : "—";
        detailContent.innerHTML = `
          <h2>${escapeHtml(item.name)}</h2>
          <dl>
            <dt>ID</dt><dd><code>${escapeHtml(item.id)}</code></dd>
            <dt>Category</dt><dd>${escapeHtml(item.category)}</dd>
            <dt>Quantity</dt><dd>${item.quantity != null ? item.quantity : "—"}</dd>
            <dt>Manufacturer</dt><dd>${escapeHtml(item.manufacturer || "—")}</dd>
            <dt>Part #</dt><dd>${escapeHtml(item.part_number || "—")}</dd>
            <dt>Model</dt><dd>${escapeHtml(item.model || "—")}</dd>
            <dt>Location</dt><dd>${escapeHtml(item.location || "—")}</dd>
            <dt>Used in</dt><dd>${escapeHtml(usedInStr)}</dd>
            <dt>Tags</dt><dd class="tags-list">${escapeHtml(tagsStr)}</dd>
            <dt>Specs</dt><dd><pre class="specs-json">${escapeHtml(specStr)}</pre></dd>
            <dt>Notes</dt><dd>${escapeHtml(item.notes || "—")}</dd>
            ${item.datasheet_url ? "<dt>Datasheet</dt><dd><a href=\"" + escapeHtml(item.datasheet_url) + "\" target=\"_blank\" rel=\"noopener\">Open</a></dd>" : ""}
          </dl>
        `;
        detailPanel.hidden = false;
      })
      .catch(() => {
        detailContent.innerHTML = "<p>Item not found.</p>";
        detailPanel.hidden = false;
      });
  }

  function escapeHtml(s) {
    if (s == null) return "";
    const div = document.createElement("div");
    div.textContent = s;
    return div.innerHTML;
  }

  function loadAiSettings() {
    fetch("/api/settings/ai")
      .then((r) => r.json())
      .then((data) => {
        const statusEl = document.getElementById("settings-api-key-status");
        const modelEl = document.getElementById("settings-model");
        const baseUrlEl = document.getElementById("settings-base-url");
        if (statusEl) statusEl.textContent = data.api_key_set ? "Set" : "Not set";
        if (modelEl) modelEl.value = data.model || "gpt-4o-mini";
        if (baseUrlEl) baseUrlEl.value = data.base_url || "";
      })
      .catch(() => {});
  }

  function saveAiSettings() {
    const apiKeyEl = document.getElementById("settings-api-key");
    const modelEl = document.getElementById("settings-model");
    const baseUrlEl = document.getElementById("settings-base-url");
    const statusEl = document.getElementById("settings-save-status");
    const payload = {
      model: (modelEl?.value || "").trim() || "gpt-4o-mini",
      base_url: (baseUrlEl?.value || "").trim(),
    };
    if (apiKeyEl && (apiKeyEl.value || "").trim() !== "") payload.api_key = apiKeyEl.value;
    fetch("/api/settings/ai", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    })
      .then((r) => r.json())
      .then((data) => {
        if (data.error) throw new Error(data.error);
        if (statusEl) { statusEl.textContent = "Saved."; statusEl.className = "flash-status flash-ok"; }
        if (document.getElementById("settings-api-key-status")) document.getElementById("settings-api-key-status").textContent = data.api_key_set ? "Set" : "Not set";
        if (apiKeyEl) apiKeyEl.value = "";
      })
      .catch((err) => {
        if (statusEl) { statusEl.textContent = "Error: " + err.message; statusEl.className = "flash-status flash-error"; }
      });
  }

  document.getElementById("btn-settings-save")?.addEventListener("click", saveAiSettings);

  function loadPathSettings() {
    fetch("/api/settings/paths")
      .then((r) => r.json())
      .then((data) => {
        if (data.error) throw new Error(data.error);
        const set = (id, v) => {
          const el = document.getElementById(id);
          if (el) el.value = v ?? "";
        };
        set("settings-docker-container", data.docker_container);
        set("settings-frontend-path", data.frontend_path);
        set("settings-backend-path", data.backend_path);
        set("settings-database-path", data.database_path);
        set("settings-mcp-server-path", data.mcp_server_path);
      })
      .catch(() => {});
  }

  function savePathSettings() {
    const statusEl = document.getElementById("settings-paths-save-status");
    const payload = {
      docker_container: (document.getElementById("settings-docker-container")?.value ?? "").trim(),
      frontend_path: (document.getElementById("settings-frontend-path")?.value ?? "").trim(),
      backend_path: (document.getElementById("settings-backend-path")?.value ?? "").trim(),
      database_path: (document.getElementById("settings-database-path")?.value ?? "").trim(),
      mcp_server_path: (document.getElementById("settings-mcp-server-path")?.value ?? "").trim(),
    };
    fetch("/api/settings/paths", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    })
      .then((r) => r.json())
      .then((data) => {
        if (data.error) throw new Error(data.error);
        if (statusEl) { statusEl.textContent = "Saved."; statusEl.className = "flash-status flash-ok"; }
      })
      .catch((err) => {
        if (statusEl) { statusEl.textContent = "Error: " + err.message; statusEl.className = "flash-status flash-error"; }
      });
  }

  document.getElementById("btn-settings-paths-save")?.addEventListener("click", savePathSettings);

  closeDetail.addEventListener("click", () => (detailPanel.hidden = true));
  btnSearch.addEventListener("click", runSearch);
  searchEl.addEventListener("keydown", (e) => e.key === "Enter" && runSearch());
  btnAi.addEventListener("click", runAiQuery);
  aiQueryEl.addEventListener("keydown", (e) => e.key === "Enter" && runAiQuery());

  function loadDockerStatus() {
    const statusEl = document.getElementById("docker-status");
    const toolsEl = document.getElementById("docker-tools");
    if (!statusEl || !toolsEl) return;

    Promise.all([fetch("/api/docker/status").then((r) => r.json()), fetch("/api/docker/tools").then((r) => r.json())])
      .then(([status, toolsData]) => {
        const ok = status.docker_available;
        statusEl.innerHTML =
          "<span class=\"docker-badge " +
          (ok ? "docker-ok" : "docker-off") +
          "\">Docker: " +
          (ok ? "running (" + escapeHtml(status.docker_message || "") + ")" : escapeHtml(status.docker_message || "not available")) +
          "</span>" +
          (status.images && status.images.length
            ? " <span class=\"docker-images\">Images: " + escapeHtml(status.images.join(", ")) + "</span>"
            : "");

        const tools = toolsData.tools || [];
        toolsEl.innerHTML =
          "<ul class=\"tools-list\">" +
          tools
            .map(
              (t) =>
                "<li class=\"tool-item\">" +
                "<span class=\"tool-name\">" +
                escapeHtml(t.name) +
                "</span> " +
                (t.available ? "<span class=\"tool-avail tool-yes\">available</span>" : "<span class=\"tool-avail tool-no\">build required</span>") +
                "<p class=\"tool-desc\">" +
                escapeHtml(t.description) +
                "</p>" +
                (t.command ? "<code class=\"tool-cmd\">" + escapeHtml(t.command) + "</code>" : "") +
                (t.build ? " <code class=\"tool-build\">Build: " + escapeHtml(t.build) + "</code>" : "") +
                "</li>"
            )
            .join("") +
          "</ul>";
      })
      .catch((err) => {
        statusEl.textContent = "Docker status: error — " + err.message;
        toolsEl.innerHTML = "";
      });
  }

  function loadDockerContainers() {
    const tbody = document.getElementById("docker-containers-tbody");
    const msgEl = document.getElementById("docker-containers-message");
    if (!tbody) return;
    if (msgEl) { msgEl.textContent = ""; msgEl.className = "flash-status"; }
    fetch("/api/docker/containers")
      .then((r) => r.json())
      .then((data) => {
        if (data.error) {
          tbody.innerHTML = "<tr><td colspan=\"5\">" + escapeHtml(data.error) + "</td></tr>";
          return;
        }
        const list = data.containers || [];
        if (list.length === 0) {
          tbody.innerHTML = "<tr><td colspan=\"5\">No lab-related containers found.</td></tr>";
          return;
        }
        tbody.innerHTML = list
          .map(
            (c) =>
              "<tr data-id=\"" +
              escapeHtml(c.id) +
              "\">" +
              "<td>" + escapeHtml(c.name) + "</td>" +
              "<td>" + escapeHtml(c.image) + "</td>" +
              "<td>" + escapeHtml(c.state) + "</td>" +
              "<td>" + escapeHtml(c.status || "") + "</td>" +
              "<td class=\"docker-actions-cell\">" +
              (c.state === "running"
                ? "<button type=\"button\" class=\"docker-btn docker-btn-stop\" data-action=\"stop\">Stop</button> <button type=\"button\" class=\"docker-btn docker-btn-restart\" data-action=\"restart\">Restart</button>"
                : "<button type=\"button\" class=\"docker-btn docker-btn-start\" data-action=\"start\">Start</button>") +
              "</td></tr>"
          )
          .join("");
        tbody.querySelectorAll(".docker-btn").forEach((btn) => {
          btn.addEventListener("click", function () {
            const row = this.closest("tr");
            const id = row?.dataset?.id;
            const action = this.dataset?.action;
            if (!id || !action) return;
            const msgEl2 = document.getElementById("docker-containers-message");
            if (msgEl2) { msgEl2.textContent = action + "ing…"; msgEl2.className = "flash-status"; }
            fetch("/api/docker/containers/" + encodeURIComponent(id) + "/" + action, { method: "POST" })
              .then((res) => res.json())
              .then((data2) => {
                if (msgEl2) {
                  msgEl2.textContent = data2.success ? data2.message || "Done." : (data2.error || "Failed.");
                  msgEl2.className = "flash-status " + (data2.success ? "flash-ok" : "flash-error");
                }
                loadDockerContainers();
              })
              .catch((err) => {
                if (msgEl2) { msgEl2.textContent = "Error: " + err.message; msgEl2.className = "flash-status flash-error"; }
              });
          });
        });
      })
      .catch((err) => {
        tbody.innerHTML = "<tr><td colspan=\"5\">Error: " + escapeHtml(err.message) + "</td></tr>";
      });
  }

  const btnDockerRefresh = document.getElementById("btn-docker-refresh");
  if (btnDockerRefresh) {
    btnDockerRefresh.addEventListener("click", () => {
      loadDockerStatus();
      loadDockerContainers();
    });
  }
  const btnDockerContainersRefresh = document.getElementById("btn-docker-containers-refresh");
  if (btnDockerContainersRefresh) btnDockerContainersRefresh.addEventListener("click", loadDockerContainers);

  function loadFlashPorts(detect) {
    const sel = document.getElementById("flash-port");
    const deviceSel = document.getElementById("flash-device");
    const statusEl = document.getElementById("flash-detect-status");
    if (!sel) return;
    const url = "/api/flash/ports" + (detect ? "?detect=1" : "");
    if (detect && statusEl) { statusEl.textContent = "Detecting…"; statusEl.className = "flash-status"; }
    fetch(url)
      .then((r) => r.json())
      .then((data) => {
        const ports = data.ports || [];
        const portValue = (p) => (typeof p === "string" ? p : (p && p.port)) || "";
        const portLabel = (p) => {
          if (typeof p === "string") return p;
          if (!p) return "";
          let label = p.description || p.port || "";
          if (p.chip) label += " — " + p.chip.toUpperCase();
          if (p.suggested_device_ids && p.suggested_device_ids.length) label += " (" + p.suggested_device_ids[0] + ")";
          return label;
        };
        sel.innerHTML = '<option value="">— Select port —</option>' + ports.map((p) => '<option value="' + escapeHtml(portValue(p)) + '">' + escapeHtml(portLabel(p)) + "</option>").join("");
        if (detect && deviceSel && ports.length) {
          const detected = ports.find((p) => p.suggested_device_ids && p.suggested_device_ids.length);
          if (detected && detected.suggested_device_ids) {
            sel.value = portValue(detected);
            loadFlashDevices().then(() => {
              if (deviceSel && detected.suggested_device_ids[0]) deviceSel.value = detected.suggested_device_ids[0];
            });
          }
        }
        if (statusEl) { statusEl.textContent = ""; }
      })
      .catch(() => { sel.innerHTML = '<option value="">— Select port —</option>'; if (statusEl) statusEl.textContent = ""; });
  }

  function loadFlashDevices() {
    const sel = document.getElementById("flash-device");
    if (!sel) return Promise.resolve();
    return fetch("/api/flash/devices")
      .then((r) => r.json())
      .then((data) => {
        const devices = Array.isArray(data.devices) ? data.devices : Object.entries(data.devices || {}).map(([id, d]) => ({ id, ...d }));
        sel.innerHTML = '<option value="">— Select device —</option>' + devices.map((d) => '<option value="' + escapeHtml(d.id) + '">' + escapeHtml((d.id || "") + " — " + (d.description || d.chip || "")) + "</option>").join("");
      })
      .catch(() => { sel.innerHTML = '<option value="">— Select device —</option>'; return Promise.resolve(); });
  }

  function loadFlashArtifacts() {
    const restoreSel = document.getElementById("flash-restore-file");
    const flashSel = document.getElementById("flash-flash-file");
    if (!restoreSel || !flashSel) return;
    fetch("/api/flash/artifacts")
      .then((r) => r.json())
      .then((data) => {
        const list = data.files || data.artifacts || [];
        const opts = '<option value="">— Select file or upload —</option>' + list.map((a) => '<option value="' + escapeHtml(a.path) + '">' + escapeHtml(a.name + (a.type ? " (" + a.type + ")" : "")) + "</option>").join("");
        restoreSel.innerHTML = opts;
        flashSel.innerHTML = opts;
      })
      .catch(() => {
        restoreSel.innerHTML = flashSel.innerHTML = '<option value="">— Select file or upload —</option>';
      });
  }

  function setFlashStatus(idSuffix, message, isError) {
    const el = document.getElementById("flash-" + idSuffix);
    if (!el) return;
    el.textContent = message || "";
    el.className = "flash-status " + (isError ? "flash-error" : "flash-ok");
  }

  function doBackup() {
    const port = document.getElementById("flash-port")?.value?.trim();
    const deviceId = document.getElementById("flash-device")?.value?.trim();
    const backupType = document.getElementById("flash-backup-type")?.value || "full";
    const statusEl = document.getElementById("flash-backup-status");
    if (!port || !deviceId) {
      setFlashStatus("backup-status", "Select port and device.", true);
      return;
    }
    if (statusEl) statusEl.textContent = "Backing up…";
    fetch("/api/flash/backup", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ port, device_id: deviceId, backup_type: backupType }),
    })
      .then((r) => {
        if (!r.ok) return r.json().then((j) => { throw new Error(j.error || r.statusText); });
        return r.blob();
      })
      .then((blob) => {
        const name = "backup-" + deviceId + "-" + backupType + "-" + new Date().toISOString().slice(0, 19).replace(/[:-]/g, "") + ".bin";
        const a = document.createElement("a");
        a.href = URL.createObjectURL(blob);
        a.download = name;
        a.click();
        URL.revokeObjectURL(a.href);
        setFlashStatus("backup-status", "Download started.", false);
      })
      .catch((err) => setFlashStatus("backup-status", "Error: " + err.message, true));
  }

  let restoreUploadFile = null;
  let flashUploadFile = null;

  document.getElementById("flash-restore-upload")?.addEventListener("change", (e) => {
    restoreUploadFile = e.target.files?.[0] || null;
    const sel = document.getElementById("flash-restore-file");
    if (sel) { sel.value = ""; sel.selectedIndex = 0; }
  });
  document.getElementById("flash-flash-upload")?.addEventListener("change", (e) => {
    flashUploadFile = e.target.files?.[0] || null;
    const sel = document.getElementById("flash-flash-file");
    if (sel) { sel.value = ""; sel.selectedIndex = 0; }
  });

  document.getElementById("btn-flash-restore-choose")?.addEventListener("click", () => document.getElementById("flash-restore-upload")?.click());
  document.getElementById("btn-flash-flash-choose")?.addEventListener("click", () => document.getElementById("flash-flash-upload")?.click());

  function doRestore() {
    const port = document.getElementById("flash-port")?.value?.trim();
    const deviceId = document.getElementById("flash-device")?.value?.trim();
    const pathOpt = document.getElementById("flash-restore-file")?.value?.trim();
    if (!port || !deviceId) {
      setFlashStatus("restore-status", "Select port and device.", true);
      return;
    }
    const fd = new FormData();
    fd.set("port", port);
    fd.set("device_id", deviceId);
    if (restoreUploadFile) {
      fd.set("file", restoreUploadFile);
    } else if (pathOpt) {
      fd.set("path", pathOpt);
    } else {
      setFlashStatus("restore-status", "Select a file or upload one.", true);
      return;
    }
    setFlashStatus("restore-status", "Restoring…", false);
    fetch("/api/flash/restore", { method: "POST", body: fd })
      .then((r) => r.json())
      .then((data) => {
        if (data.success) {
          setFlashStatus("restore-status", data.message || "Restore complete.", false);
        } else {
          setFlashStatus("restore-status", data.error || "Restore failed.", true);
        }
      })
      .catch((err) => setFlashStatus("restore-status", "Error: " + err.message, true));
  }

  function doFlash() {
    const port = document.getElementById("flash-port")?.value?.trim();
    const deviceId = document.getElementById("flash-device")?.value?.trim();
    const pathOpt = document.getElementById("flash-flash-file")?.value?.trim();
    if (!port || !deviceId) {
      setFlashStatus("flash-status", "Select port and device.", true);
      return;
    }
    const fd = new FormData();
    fd.set("port", port);
    fd.set("device_id", deviceId);
    if (flashUploadFile) {
      fd.set("file", flashUploadFile);
    } else if (pathOpt) {
      fd.set("path", pathOpt);
    } else {
      setFlashStatus("flash-status", "Select a file or upload one.", true);
      return;
    }
    setFlashStatus("flash-status", "Flashing…", false);
    fetch("/api/flash/flash", { method: "POST", body: fd })
      .then((r) => r.json())
      .then((data) => {
        if (data.success) {
          setFlashStatus("flash-status", data.message || "Flash complete.", false);
        } else {
          setFlashStatus("flash-status", data.error || "Flash failed.", true);
        }
      })
      .catch((err) => setFlashStatus("flash-status", "Error: " + err.message, true));
  }

  document.getElementById("btn-flash-backup")?.addEventListener("click", doBackup);
  document.getElementById("btn-flash-restore")?.addEventListener("click", doRestore);
  document.getElementById("btn-flash-flash")?.addEventListener("click", doFlash);

  const btnFlashRefresh = document.getElementById("btn-flash-refresh");
  if (btnFlashRefresh) {
    btnFlashRefresh.addEventListener("click", () => {
      loadFlashPorts(true);
      loadFlashArtifacts();
    });
  }

  // --- Project planning ---
  let currentProjectId = "";
  let currentBom = [];
  let currentMessages = [];
  let currentDesign = { pin_outs: [], wiring: [], schematic: "", enclosure: "" };

  function loadProjectsList() {
    const sel = document.getElementById("project-select");
    if (!sel) return;
    fetch("/api/projects")
      .then((r) => r.json())
      .then((data) => {
        const list = data.projects || [];
        const cur = sel.value;
        sel.innerHTML = '<option value="">— New or select —</option>' + list.map((p) => '<option value="' + escapeHtml(p.id) + '">' + escapeHtml(p.title || p.id) + "</option>").join("");
        if (cur) sel.value = cur;
      })
      .catch(() => {});
  }

  function renderBom(bom) {
    const tbody = document.getElementById("project-bom-tbody");
    if (!tbody) return;
    const rows = bom || [];
    tbody.innerHTML = rows
      .map(
        (r) =>
          "<tr><td>" +
          escapeHtml(r.name || "—") +
          "</td><td>" +
          escapeHtml(r.part_number || "—") +
          "</td><td>" +
          (r.quantity ?? "—") +
          "</td><td>" +
          (r.qty_on_hand != null ? r.qty_on_hand : "—") +
          "</td><td>" +
          (r.shortfall != null && r.shortfall > 0 ? r.shortfall : "—") +
          "</td></tr>"
      )
      .join("");
  }

  function renderProjectMessages(msgs) {
    const el = document.getElementById("project-messages");
    if (!el) return;
    const list = msgs || [];
    el.innerHTML = list
      .map((m) => '<div class="project-msg project-msg-' + escapeHtml(m.role || "user") + '">' + escapeHtml(m.content || "").slice(0, 2000) + "</div>")
      .join("");
    el.scrollTop = el.scrollHeight;
  }

  function renderDesign(design) {
    const d = design || currentDesign;
    const pinoutTbody = document.getElementById("project-pinout-tbody");
    if (pinoutTbody) {
      const rows = d.pin_outs || [];
      pinoutTbody.innerHTML = rows
        .map((r) => "<tr><td>" + escapeHtml(r.pin || "—") + "</td><td>" + escapeHtml(r.function || "—") + "</td><td>" + escapeHtml(r.notes || "—") + "</td></tr>")
        .join("");
    }
    const wiringTbody = document.getElementById("project-wiring-tbody");
    if (wiringTbody) {
      const rows = d.wiring || [];
      wiringTbody.innerHTML = rows
        .map((r) => "<tr><td>" + escapeHtml(r.from || "—") + "</td><td>" + escapeHtml(r.to || "—") + "</td><td>" + escapeHtml(r.net || "—") + "</td></tr>")
        .join("");
    }
    const schematicEl = document.getElementById("project-schematic-text");
    if (schematicEl) schematicEl.textContent = d.schematic || "";
    const enclosureEl = document.getElementById("project-enclosure-text");
    if (enclosureEl) enclosureEl.textContent = d.enclosure || "";
  }

  function setProjectExportLinks(projectId) {
    if (!projectId) {
      ["btn-export-pinout", "btn-export-wiring", "btn-export-schematic", "btn-export-enclosure"].forEach((id) => {
        const a = document.getElementById(id);
        if (a) a.href = "#";
      });
      return;
    }
    const base = "/api/projects/" + encodeURIComponent(projectId) + "/export/";
    const pinout = document.getElementById("btn-export-pinout");
    if (pinout) pinout.href = base + "pinout";
    const wiring = document.getElementById("btn-export-wiring");
    if (wiring) wiring.href = base + "wiring";
    const schematic = document.getElementById("btn-export-schematic");
    if (schematic) schematic.href = base + "schematic";
    const enclosure = document.getElementById("btn-export-enclosure");
    if (enclosure) enclosure.href = base + "enclosure";
  }

  function openProject(projectId) {
    currentProjectId = projectId || "";
    const titleEl = document.getElementById("project-title");
    const descEl = document.getElementById("project-description");
    const digiLink = document.getElementById("btn-bom-digikey");
    const mouserLink = document.getElementById("btn-bom-mouser");
    if (!projectId) {
      if (titleEl) titleEl.value = "";
      if (descEl) descEl.value = "";
      currentMessages = [];
      currentBom = [];
      currentDesign = { pin_outs: [], wiring: [], schematic: "", enclosure: "" };
      renderProjectMessages([]);
      renderBom([]);
      renderDesign(currentDesign);
      if (digiLink) digiLink.href = "#";
      if (mouserLink) mouserLink.href = "#";
      setProjectExportLinks("");
      return;
    }
    fetch("/api/projects/" + encodeURIComponent(projectId))
      .then((r) => {
        if (!r.ok) throw new Error("Not found");
        return r.json();
      })
      .then((proj) => {
        if (titleEl) titleEl.value = proj.title || "";
        if (descEl) descEl.value = proj.description || "";
        currentMessages = proj.conversation || [];
        currentBom = proj.parts_bom || [];
        currentDesign = {
          pin_outs: proj.pin_outs || [],
          wiring: proj.wiring || [],
          schematic: proj.schematic || "",
          enclosure: proj.enclosure || "",
        };
        renderProjectMessages(currentMessages);
        renderBom(currentBom);
        renderDesign(currentDesign);
        if (digiLink) digiLink.href = "/api/projects/" + encodeURIComponent(projectId) + "/bom/digikey";
        if (mouserLink) mouserLink.href = "/api/projects/" + encodeURIComponent(projectId) + "/bom/mouser";
        setProjectExportLinks(projectId);
      })
      .catch(() => {
        currentMessages = [];
        currentBom = [];
        currentDesign = { pin_outs: [], wiring: [], schematic: "", enclosure: "" };
        renderProjectMessages([]);
        renderBom([]);
        renderDesign(currentDesign);
      });
  }

  document.getElementById("project-select")?.addEventListener("change", (e) => openProject((e.target.value || "").trim()));
  document.getElementById("btn-project-new")?.addEventListener("click", () => {
    const sel = document.getElementById("project-select");
    if (sel) sel.value = "";
    openProject("");
  });

  document.getElementById("btn-project-send")?.addEventListener("click", () => {
    const input = document.getElementById("project-message");
    const msg = (input?.value || "").trim();
    if (!msg) return;
    if (input) input.value = "";
    currentMessages.push({ role: "user", content: msg });
    renderProjectMessages(currentMessages);
    currentMessages.push({ role: "assistant", content: "" });
    renderProjectMessages(currentMessages);
    const messagesEl = document.getElementById("project-messages");
    const streamDiv = messagesEl?.lastElementChild;
    if (streamDiv) streamDiv.textContent = "";
    fetch("/api/projects/ai/stream", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: msg, project_id: currentProjectId || undefined }),
    })
      .then((r) => {
        if (!r.ok) return r.json().then((j) => { throw new Error(j.error || r.statusText); });
        return r.body.getReader();
      })
      .then((reader) => {
        const decoder = new TextDecoder();
        let buffer = "";
        let fullReply = "";
        let suggestedBom = [];
        let suggestedDesign = null;
        function pump() {
          return reader.read().then(({ done, value }) => {
            if (value) {
              buffer += decoder.decode(value, { stream: true });
              const lines = buffer.split("\n");
              buffer = lines.pop() || "";
              for (const line of lines) {
                if (line.startsWith("data: ")) {
                  try {
                    const data = JSON.parse(line.slice(6));
                    if (data.delta) {
                      fullReply += data.delta;
                      if (streamDiv) streamDiv.appendChild(document.createTextNode(data.delta));
                      if (messagesEl) messagesEl.scrollTop = messagesEl.scrollHeight;
                    }
                    if (data.done && data.suggested_bom) suggestedBom = data.suggested_bom;
                    if (data.done && data.suggested_design) suggestedDesign = data.suggested_design;
                  } catch (e) { /* skip */ }
                }
              }
            }
            if (!done) return pump();
            if (buffer.startsWith("data: ")) {
              try {
                const data = JSON.parse(buffer.slice(6));
                if (data.delta) {
                  fullReply += data.delta;
                  if (streamDiv) streamDiv.appendChild(document.createTextNode(data.delta));
                }
                if (data.done && data.suggested_bom) suggestedBom = data.suggested_bom || [];
                if (data.done && data.suggested_design) suggestedDesign = data.suggested_design;
              } catch (e) { /* skip */ }
            }
            currentMessages[currentMessages.length - 1].content = fullReply;
            if (suggestedBom.length) {
              currentBom = suggestedBom;
              renderBom(currentBom);
            }
            if (suggestedDesign && (suggestedDesign.pin_outs?.length || suggestedDesign.wiring?.length || suggestedDesign.schematic || suggestedDesign.enclosure)) {
              currentDesign = {
                pin_outs: suggestedDesign.pin_outs || [],
                wiring: suggestedDesign.wiring || [],
                schematic: suggestedDesign.schematic || "",
                enclosure: suggestedDesign.enclosure || "",
              };
              renderDesign(currentDesign);
            }
          });
        }
        return pump();
      })
      .catch((err) => {
        const errMsg = "Error: " + err.message;
        if (streamDiv) streamDiv.textContent = errMsg;
        currentMessages[currentMessages.length - 1].content = errMsg;
        renderProjectMessages(currentMessages);
      });
  });
  document.getElementById("project-message")?.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      document.getElementById("btn-project-send")?.click();
    }
  });

  document.getElementById("btn-project-check-inv")?.addEventListener("click", () => {
    if (!currentProjectId) {
      const st = document.getElementById("project-save-status");
      if (st) { st.textContent = "Save the project first, or get a BOM from the AI."; st.className = "flash-status flash-error"; }
      return;
    }
    fetch("/api/projects/" + encodeURIComponent(currentProjectId) + "/check-inventory")
      .then((r) => r.json())
      .then((data) => {
        if (data.bom) {
          currentBom = data.bom;
          renderBom(currentBom);
        }
      })
      .catch(() => {});
  });

  document.getElementById("btn-project-save")?.addEventListener("click", () => {
    const title = (document.getElementById("project-title")?.value || "").trim();
    const description = (document.getElementById("project-description")?.value || "").trim();
    const statusEl = document.getElementById("project-save-status");
    const parts_bom = currentBom.map((r) => ({ name: r.name, part_number: r.part_number || "", quantity: r.quantity ?? 0 }));
    const payload = {
      title: title || "Untitled project",
      description,
      parts_bom,
      conversation: currentMessages,
      pin_outs: currentDesign.pin_outs,
      wiring: currentDesign.wiring,
      schematic: currentDesign.schematic,
      enclosure: currentDesign.enclosure,
    };
    if (currentProjectId) {
      fetch("/api/projects/" + encodeURIComponent(currentProjectId), {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      })
        .then((r) => r.json())
        .then((data) => {
          if (data.error) throw new Error(data.error);
          if (statusEl) { statusEl.textContent = "Saved."; statusEl.className = "flash-status flash-ok"; }
        })
        .catch((err) => {
          if (statusEl) { statusEl.textContent = "Error: " + err.message; statusEl.className = "flash-status flash-error"; }
        });
    } else {
      fetch("/api/projects", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      })
        .then((r) => r.json())
        .then((data) => {
          if (data.error) throw new Error(data.error);
          currentProjectId = data.id;
          if (statusEl) { statusEl.textContent = "Saved as " + data.id + "."; statusEl.className = "flash-status flash-ok"; }
          loadProjectsList();
          const sel = document.getElementById("project-select");
          if (sel) sel.value = currentProjectId;
          const digiLink = document.getElementById("btn-bom-digikey");
          const mouserLink = document.getElementById("btn-bom-mouser");
          if (digiLink) digiLink.href = "/api/projects/" + encodeURIComponent(currentProjectId) + "/bom/digikey";
          if (mouserLink) mouserLink.href = "/api/projects/" + encodeURIComponent(currentProjectId) + "/bom/mouser";
          setProjectExportLinks(currentProjectId);
        })
        .catch((err) => {
          if (statusEl) { statusEl.textContent = "Error: " + err.message; statusEl.className = "flash-status flash-error"; }
        });
    }
  });

  loadCategories();
  fetchItems();
  loadAiSettings();
  loadPathSettings();
  loadDockerStatus();
  loadDockerContainers();
  loadFlashPorts(false);
  loadFlashDevices();
  loadFlashArtifacts();
  loadProjectsList();
})();
