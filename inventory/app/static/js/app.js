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
    if (tabId === "inventory") {
      loadManufacturers();
      fetchItems(buildInventoryQueryParams());
    }
    if (tabId === "flash") {
      loadFlashPorts(false);
      loadFlashDevices();
      loadFlashBuildConfig();
    }
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
        const cats = data.categories || [];
        categoryEl.innerHTML = '<option value="">All categories</option>';
        cats.forEach((cat) => {
          const opt = document.createElement("option");
          opt.value = cat;
          opt.textContent = cat;
          categoryEl.appendChild(opt);
        });
        const invCat = document.getElementById("inventory-category");
        if (invCat) {
          invCat.innerHTML = '<option value="">All categories</option>';
          cats.forEach((cat) => {
            const opt = document.createElement("option");
            opt.value = cat;
            opt.textContent = cat;
            invCat.appendChild(opt);
          });
        }
      })
      .catch((err) => console.error(err));
  }

  function loadManufacturers() {
    const el = document.getElementById("inventory-manufacturer");
    if (!el) return;
    fetch("/api/items/manufacturers")
      .then((r) => r.json())
      .then((data) => {
        const list = data.manufacturers || [];
        el.innerHTML = '<option value="">All manufacturers</option>';
        list.forEach((m) => {
          const opt = document.createElement("option");
          opt.value = m;
          opt.textContent = m;
          el.appendChild(opt);
        });
      })
      .catch(() => {});
  }

  let inventorySortColumn = "category";
  let inventorySortOrder = "asc";

  function buildQueryParams() {
    const params = new URLSearchParams();
    const q = searchEl.value.trim();
    const cat = categoryEl.value.trim();
    if (q) params.set("q", q);
    if (cat) params.set("category", cat);
    params.set("limit", "500");
    return params.toString();
  }

  function buildInventoryQueryParams() {
    const params = new URLSearchParams();
    const invSearch = document.getElementById("inventory-search");
    const invCat = document.getElementById("inventory-category");
    const invMfr = document.getElementById("inventory-manufacturer");
    const q = (invSearch && invSearch.value || "").trim();
    const cat = (invCat && invCat.value || "").trim();
    const mfr = (invMfr && invMfr.value || "").trim();
    if (q) params.set("q", q);
    if (cat) params.set("category", cat);
    if (mfr) params.set("manufacturer", mfr);
    params.set("sort", inventorySortColumn);
    params.set("order", inventorySortOrder);
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
        <td>${escapeHtml(it.manufacturer || "")}</td>
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

  function showDetailEditForm(item) {
    const id = item.id;
    const catOpts = (window._detailCategories || []).map((c) => '<option value="' + escapeHtml(c) + '">' + escapeHtml(c) + "</option>").join("");
    detailContent.innerHTML = `
      <div class="detail-head-row">
        <h2>Edit item</h2>
      </div>
      <form id="detail-edit-form" class="detail-edit-form">
        <input type="hidden" name="id" value="${escapeHtml(id)}">
        <div class="detail-edit-field">
          <label for="detail-edit-name">Name</label>
          <input type="text" id="detail-edit-name" name="name" value="${escapeHtml(item.name || "")}" required>
        </div>
        <div class="detail-edit-field">
          <label for="detail-edit-category">Category</label>
          <input type="text" id="detail-edit-category" name="category" list="detail-edit-category-list" value="${escapeHtml(item.category || "")}" required>
          <datalist id="detail-edit-category-list">${catOpts}</datalist>
        </div>
        <div class="detail-edit-field">
          <label for="detail-edit-quantity">Quantity</label>
          <input type="number" id="detail-edit-quantity" name="quantity" min="0" value="${item.quantity != null ? item.quantity : 1}">
        </div>
        <div class="detail-edit-field">
          <label for="detail-edit-manufacturer">Manufacturer</label>
          <input type="text" id="detail-edit-manufacturer" name="manufacturer" value="${escapeHtml(item.manufacturer || "")}">
        </div>
        <div class="detail-edit-field">
          <label for="detail-edit-part_number">Part #</label>
          <input type="text" id="detail-edit-part_number" name="part_number" value="${escapeHtml(item.part_number || "")}">
        </div>
        <div class="detail-edit-field">
          <label for="detail-edit-model">Model</label>
          <input type="text" id="detail-edit-model" name="model" value="${escapeHtml(item.model || "")}">
        </div>
        <div class="detail-edit-field">
          <label for="detail-edit-location">Location</label>
          <input type="text" id="detail-edit-location" name="location" value="${escapeHtml(item.location || "")}">
        </div>
        <div class="detail-edit-field">
          <label for="detail-edit-datasheet_url">Datasheet URL</label>
          <input type="url" id="detail-edit-datasheet_url" name="datasheet_url" value="${escapeHtml(item.datasheet_url || "")}">
        </div>
        <div class="detail-edit-field">
          <label for="detail-edit-notes">Notes</label>
          <textarea id="detail-edit-notes" name="notes" rows="3">${escapeHtml(item.notes || "")}</textarea>
        </div>
        <div class="detail-edit-actions">
          <button type="submit" class="detail-save-btn">Save</button>
          <button type="button" class="detail-cancel-btn" id="detail-edit-cancel">Cancel</button>
          <span id="detail-edit-status" class="flash-status"></span>
        </div>
      </form>
    `;
    document.getElementById("detail-edit-form").addEventListener("submit", (e) => {
      e.preventDefault();
      const statusEl = document.getElementById("detail-edit-status");
      const payload = {
        name: document.getElementById("detail-edit-name").value.trim(),
        category: (document.getElementById("detail-edit-category").value || "").trim(),
        quantity: parseInt(document.getElementById("detail-edit-quantity").value, 10) || 0,
        manufacturer: (document.getElementById("detail-edit-manufacturer").value || "").trim(),
        part_number: (document.getElementById("detail-edit-part_number").value || "").trim(),
        model: (document.getElementById("detail-edit-model").value || "").trim(),
        location: (document.getElementById("detail-edit-location").value || "").trim(),
        datasheet_url: (document.getElementById("detail-edit-datasheet_url").value || "").trim(),
        notes: (document.getElementById("detail-edit-notes").value || "").trim(),
      };
      if (!payload.name || !payload.category) {
        if (statusEl) { statusEl.textContent = "Name and category required."; statusEl.className = "flash-status flash-error"; }
        return;
      }
      if (statusEl) { statusEl.textContent = "Saving…"; statusEl.className = "flash-status"; }
      fetch("/api/items/" + encodeURIComponent(id), {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      })
        .then((r) => r.json())
        .then((data) => {
          if (data.error) throw new Error(data.error);
          if (statusEl) { statusEl.textContent = "Saved."; statusEl.className = "flash-status flash-ok"; }
          openDetail(id);
          fetchItems(buildInventoryQueryParams());
        })
        .catch((err) => {
          if (statusEl) { statusEl.textContent = "Error: " + err.message; statusEl.className = "flash-status flash-error"; }
        });
    });
    document.getElementById("detail-edit-cancel").addEventListener("click", () => openDetail(id));
  }

  function openDetail(id) {
    fetch("/api/categories")
      .then((r) => r.json())
      .then((data) => { window._detailCategories = data.categories || []; })
      .catch(() => { window._detailCategories = []; });
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
        const qty = item.quantity != null ? item.quantity : 1;
        detailContent.innerHTML = `
          <div class="detail-head-row">
            <h2>${escapeHtml(item.name)}</h2>
            <button type="button" class="detail-edit-btn" id="detail-edit-btn" data-item-id="${escapeHtml(item.id)}">Edit</button>
          </div>
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
          <div class="detail-add-to-project" id="detail-add-to-project">
            <h3>Add to project</h3>
            <p class="detail-add-hint">Add this item to a project&rsquo;s BOM.</p>
            <div class="detail-add-to-project-row">
              <select id="detail-add-to-project-select"><option value="">Select project…</option></select>
              <label for="detail-add-to-project-qty">Qty</label>
              <input type="number" id="detail-add-to-project-qty" min="1" value="${qty}">
              <button type="button" id="detail-add-to-project-btn">Add to project</button>
              <button type="button" id="detail-add-to-new-project-btn">Add to new project</button>
            </div>
            <span id="detail-add-to-project-status" class="flash-status"></span>
          </div>
        `;
        const sel = document.getElementById("detail-add-to-project-select");
        const statusEl = document.getElementById("detail-add-to-project-status");
        fetch("/api/projects")
          .then((r) => r.json())
          .then((data) => {
            (data.projects || []).forEach((p) => {
              const opt = document.createElement("option");
              opt.value = p.id;
              opt.textContent = p.title || p.id;
              sel.appendChild(opt);
            });
          })
          .catch(() => {});
        document.getElementById("detail-add-to-project-btn").addEventListener("click", () => {
          const projectId = (sel.value || "").trim();
          if (!projectId) {
            if (statusEl) { statusEl.textContent = "Select a project."; statusEl.className = "flash-status flash-error"; }
            return;
          }
          const qtyInput = document.getElementById("detail-add-to-project-qty");
          const quantity = Math.max(1, parseInt(qtyInput.value, 10) || 1);
          statusEl.textContent = "";
          fetch("/api/projects/" + encodeURIComponent(projectId) + "/bom/items", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ item_id: item.id, quantity }),
          })
            .then((r) => r.json())
            .then((data) => {
              if (data.error) throw new Error(data.error);
              if (statusEl) { statusEl.textContent = "Added to BOM."; statusEl.className = "flash-status flash-ok"; }
            })
            .catch((err) => {
              if (statusEl) { statusEl.textContent = "Error: " + err.message; statusEl.className = "flash-status flash-error"; }
            });
        });
        document.getElementById("detail-add-to-new-project-btn").addEventListener("click", () => {
          const qtyInput = document.getElementById("detail-add-to-project-qty");
          const quantity = Math.max(1, parseInt(qtyInput.value, 10) || 1);
          const newTitle = (item.name && item.name.trim()) ? item.name.trim() + " project" : "New project";
          statusEl.textContent = "Creating project…";
          statusEl.className = "flash-status";
          fetch("/api/projects", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ title: newTitle, description: "", parts_bom: [], conversation: [] }),
          })
            .then((r) => r.json())
            .then((data) => {
              if (data.error) throw new Error(data.error);
              const newId = data.id;
              const projectTitle = (data.project && data.project.title) ? data.project.title : newTitle;
              return fetch("/api/projects/" + encodeURIComponent(newId) + "/bom/items", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ item_id: item.id, quantity }),
              }).then((r) => r.json()).then((bomData) => {
                if (bomData.error) throw new Error(bomData.error);
                return { newId, projectTitle };
              });
            })
            .then(({ newId, projectTitle }) => {
              const opt = document.createElement("option");
              opt.value = newId;
              opt.textContent = projectTitle;
              opt.selected = true;
              sel.appendChild(opt);
              if (statusEl) { statusEl.textContent = "Created project and added item."; statusEl.className = "flash-status flash-ok"; }
            })
            .catch((err) => {
              if (statusEl) { statusEl.textContent = "Error: " + err.message; statusEl.className = "flash-status flash-error"; }
            });
        });
        document.getElementById("detail-edit-btn")?.addEventListener("click", () => showDetailEditForm(item));
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
        const noticeEl = document.getElementById("flash-docker-notice");
        if (noticeEl) {
          noticeEl.hidden = !data.in_container_no_usb;
        }
        if (statusEl) {
          if (data.in_container_no_usb && ports.length === 0) {
            statusEl.textContent = "Serial/USB not available (app is in Docker). Run on host for backup/flash.";
            statusEl.className = "flash-status flash-error";
          } else if (detect && ports.length === 0) {
            statusEl.textContent = "No ports found. Connect T-Beam via USB; put in bootloader (hold BOOT, press RESET) then Refresh again.";
            statusEl.className = "flash-status";
          } else {
            statusEl.textContent = "";
          }
        }
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
    const firmwareTargetSel = document.getElementById("flash-firmware-target");
    if (!restoreSel || !flashSel) return;
    const firmware = (firmwareTargetSel?.value || "").trim();
    const url = "/api/flash/artifacts" + (firmware ? "?firmware=" + encodeURIComponent(firmware) : "");
    fetch(url)
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

  let flashBuildConfig = [];
  (function initFlashBuildDropdowns() {
    const deviceSel = document.getElementById("flash-build-device");
    const firmwareSel = document.getElementById("flash-build-firmware");
    const envSel = document.getElementById("flash-build-env");
    if (!deviceSel || !firmwareSel || !envSel) return;
    deviceSel.addEventListener("change", () => {
      const did = deviceSel.value;
      const builds = flashBuildConfig.filter((b) => b.device_id === did);
      firmwareSel.innerHTML = '<option value="">— Select —</option>' + builds.map((b) => '<option value="' + escapeHtml(b.firmware_id) + '">' + escapeHtml(b.firmware_id) + "</option>").join("");
      envSel.innerHTML = "<option value=\"\">— Select —</option>";
      if (builds[0] && builds[0].envs && builds[0].envs.length) {
        envSel.innerHTML += builds[0].envs.map((e) => '<option value="' + escapeHtml(e) + '">' + escapeHtml(e) + "</option>").join("");
      }
    });
    firmwareSel.addEventListener("change", () => {
      const did = deviceSel.value;
      const fid = firmwareSel.value;
      const b = flashBuildConfig.find((x) => x.device_id === did && x.firmware_id === fid);
      envSel.innerHTML = "<option value=\"\">— Select —</option>";
      if (b && b.envs && b.envs.length) {
        envSel.innerHTML += b.envs.map((e) => '<option value="' + escapeHtml(e) + '">' + escapeHtml(e) + "</option>").join("");
      }
      loadFlashPatches(did, fid);
    });
    deviceSel.addEventListener("change", () => {
      const did = deviceSel.value;
      const fid = firmwareSel.value;
      if (did && fid) loadFlashPatches(did, fid);
    });
  })();

  function loadFlashPatches(deviceId, firmwareId) {
    const container = document.getElementById("flash-build-patches");
    if (!container) return;
    if (!deviceId || !firmwareId) {
      container.innerHTML = "—";
      container.replaceChildren();
      return;
    }
    container.innerHTML = "Loading…";
    fetch("/api/flash/patches?device_id=" + encodeURIComponent(deviceId) + "&firmware_id=" + encodeURIComponent(firmwareId))
      .then((r) => r.json())
      .then((data) => {
        const patches = data.patches || [];
        container.innerHTML = "";
        if (patches.length === 0) {
          container.appendChild(document.createTextNode("None"));
          return;
        }
        patches.forEach((p) => {
          const label = document.createElement("label");
          label.className = "flash-patch-check";
          const cb = document.createElement("input");
          cb.type = "checkbox";
          cb.name = "flash-patch";
          cb.value = p.path;
          cb.setAttribute("data-patch-path", p.path);
          label.appendChild(cb);
          label.appendChild(document.createTextNode(" " + (p.name || p.path)));
          container.appendChild(label);
        });
      })
      .catch(() => {
        container.innerHTML = "";
        container.appendChild(document.createTextNode("Error loading patches"));
      });
  }
  function loadFlashBuildConfig() {
    return fetch("/api/flash/build-config")
      .then((r) => r.json())
      .then((data) => {
        flashBuildConfig = data.builds || [];
        const deviceSel = document.getElementById("flash-build-device");
        const firmwareSel = document.getElementById("flash-build-firmware");
        const envSel = document.getElementById("flash-build-env");
        if (!deviceSel || !firmwareSel || !envSel) return;
        const devices = [...new Set(flashBuildConfig.map((b) => b.device_id))];
        deviceSel.innerHTML = '<option value="">— Select —</option>' + devices.map((d) => '<option value="' + escapeHtml(d) + '">' + escapeHtml(d) + "</option>").join("");
        if (devices.length) { deviceSel.value = devices[0]; deviceSel.dispatchEvent(new Event("change")); }
        if (deviceSel.value && firmwareSel.value) loadFlashPatches(deviceSel.value, firmwareSel.value);
      })
      .catch(() => { flashBuildConfig = []; });
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
    const dialog = document.getElementById("backup-progress-dialog");
    const msgEl = document.getElementById("backup-progress-message");
    if (!port || !deviceId) {
      setFlashStatus("backup-status", "Select port and device.", true);
      return;
    }
    function closeBackupDialog() {
      if (dialog) dialog.hidden = true;
    }
    if (msgEl) {
      const typeLabel = backupType === "full" ? "Full flash (several minutes)" : backupType === "app" ? "App partition" : "NVS";
      msgEl.textContent = "Reading " + typeLabel + ". Please wait…";
    }
    if (dialog) dialog.hidden = false;
    if (statusEl) statusEl.textContent = "";
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
        closeBackupDialog();
        const name = "backup-" + deviceId + "-" + backupType + "-" + new Date().toISOString().slice(0, 19).replace(/[:-]/g, "") + ".bin";
        const a = document.createElement("a");
        a.href = URL.createObjectURL(blob);
        a.download = name;
        a.click();
        URL.revokeObjectURL(a.href);
        setFlashStatus("backup-status", "Download started.", false);
      })
      .catch((err) => {
        closeBackupDialog();
        setFlashStatus("backup-status", "Error: " + err.message, true);
      });
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

  document.getElementById("btn-flash-build")?.addEventListener("click", () => {
    const deviceId = document.getElementById("flash-build-device")?.value?.trim();
    const firmwareId = document.getElementById("flash-build-firmware")?.value?.trim();
    const envName = document.getElementById("flash-build-env")?.value?.trim();
    const statusEl = document.getElementById("flash-build-status");
    if (!deviceId || !firmwareId || !envName) {
      setFlashStatus("build-status", "Select device, firmware, and env.", true);
      return;
    }
    const patchPaths = [];
    document.querySelectorAll('#flash-build-patches input[name="flash-patch"]:checked').forEach((cb) => {
      const v = cb.getAttribute("data-patch-path") || cb.value;
      if (v) patchPaths.push(v);
    });
    const clean = document.getElementById("flash-build-clean")?.checked || false;
    const verbose = document.getElementById("flash-build-verbose")?.checked || false;
    const flashAfter = document.getElementById("flash-build-flash-after")?.checked || false;
    let timeout = parseInt(document.getElementById("flash-build-timeout")?.value, 10);
    if (!timeout || timeout < 60) timeout = 300;
    if (timeout > 3600) timeout = 3600;
    const port = document.getElementById("flash-port")?.value?.trim() || "";
    const flashDeviceId = document.getElementById("flash-device")?.value?.trim() || "";
    if (flashAfter && (!port || !flashDeviceId)) {
      setFlashStatus("build-status", "Select port and device above for Flash after build.", true);
      return;
    }
    if (statusEl) statusEl.textContent = "Building…";
    const body = {
      device_id: deviceId,
      firmware_id: firmwareId,
      env_name: envName,
      patch_paths: patchPaths,
      clean,
      verbose,
      timeout,
      flash_after: flashAfter,
    };
    if (flashAfter) {
      body.port = port;
      body.flash_device_id = flashDeviceId;
    }
    fetch("/api/flash/build", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    })
      .then((r) => r.json())
      .then((data) => {
        if (data.success) {
          let msg = "Built: " + (data.path || "");
          if (data.flashed) msg = "Built and flashed: " + (data.path || "");
          else if (data.flash_error) msg = "Built: " + (data.path || "") + ". Flash failed: " + data.flash_error;
          setFlashStatus("build-status", msg, !!data.flash_error);
          loadFlashArtifacts();
        } else {
          setFlashStatus("build-status", data.error || "Build failed", true);
        }
      })
      .catch((err) => setFlashStatus("build-status", "Error: " + err.message, true));
  });

  document.getElementById("btn-flash-download")?.addEventListener("click", () => {
    const repoVal = document.getElementById("flash-download-repo")?.value?.trim();
    const tag = document.getElementById("flash-download-tag")?.value?.trim() || null;
    const assetFilter = document.getElementById("flash-download-filter")?.value?.trim() || null;
    const deviceId = document.getElementById("flash-device")?.value?.trim() || null;
    const statusEl = document.getElementById("flash-download-status");
    if (!repoVal || repoVal.indexOf("/") === -1) {
      setFlashStatus("download-status", "Select a repo (owner/repo).", true);
      return;
    }
    const [owner, repo] = repoVal.split("/").map((s) => s.trim());
    if (!owner || !repo) {
      setFlashStatus("download-status", "Invalid repo.", true);
      return;
    }
    if (statusEl) statusEl.textContent = "Downloading…";
    fetch("/api/flash/download-release", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ owner, repo, tag, device_id: deviceId, firmware_id: repo, asset_filter: assetFilter }),
    })
      .then((r) => r.json())
      .then((data) => {
        if (data.success) {
          setFlashStatus("download-status", "Saved: " + (data.path || ""), false);
          loadFlashArtifacts();
        } else {
          setFlashStatus("download-status", data.error || "Download failed", true);
        }
      })
      .catch((err) => setFlashStatus("download-status", "Error: " + err.message, true));
  });

  const btnFlashRefresh = document.getElementById("btn-flash-refresh");
  if (btnFlashRefresh) {
    btnFlashRefresh.addEventListener("click", () => {
      loadFlashPorts(true);
      loadFlashArtifacts();
    });
  }
  const flashFirmwareTargetSel = document.getElementById("flash-firmware-target");
  if (flashFirmwareTargetSel) {
    flashFirmwareTargetSel.addEventListener("change", loadFlashArtifacts);
  }

  // --- Device configuration wizard (pre/post flash, internal or Launcher) ---
  (function initDeviceConfigWizard() {
    const panel = document.getElementById("panel-device-config");
    const stepIndicator = document.getElementById("config-wizard-step-indicator");
    const deviceSel = document.getElementById("config-wizard-device");
    const firmwareSel = document.getElementById("config-wizard-firmware");
    const regionSel = document.getElementById("config-wizard-region");
    const deviceNameInp = document.getElementById("config-wizard-device-name");
    const presetNameInp = document.getElementById("config-wizard-preset-name");
    const reviewEl = document.getElementById("config-wizard-review");
    const resultEl = document.getElementById("config-wizard-result");
    const btnSavePreset = document.getElementById("config-wizard-save-preset");
    const btnGotoFlash = document.getElementById("config-wizard-goto-flash");
    const btnPrev = document.getElementById("config-wizard-prev");
    const btnNext = document.getElementById("config-wizard-next");
    const aiMessages = document.getElementById("config-wizard-ai-messages");
    const aiInput = document.getElementById("config-wizard-ai-input");
    const btnAiSend = document.getElementById("config-wizard-ai-send");

    let wizardContext = { devices: [], firmware_targets: [], rf_presets: [] };
    let currentStep = 1;
    const totalSteps = 5;

    function getStepEl(n) { return document.querySelector(".config-wizard-step[data-step=\"" + n + "\"]"); }
    function getOptions() {
      const when = document.querySelector("input[name=\"config-when\"]:checked");
      return {
        when: when ? when.value : "pre",
        device_id: deviceSel?.value?.trim() || "",
        firmware: firmwareSel?.value?.trim() || "",
        region: regionSel?.value?.trim() || "",
        device_name: deviceNameInp?.value?.trim() || "",
        preset_name: presetNameInp?.value?.trim() || "",
      };
    }

    function renderSteps() {
      for (let i = 1; i <= totalSteps; i++) {
        const el = getStepEl(i);
        if (el) el.style.display = currentStep === i ? "block" : "none";
      }
      if (stepIndicator) stepIndicator.textContent = "Step " + currentStep + " of " + totalSteps;
      if (btnPrev) btnPrev.style.visibility = currentStep > 1 ? "visible" : "hidden";
      if (btnNext) {
        btnNext.textContent = currentStep < totalSteps ? "Next" : "Finish";
        btnNext.style.visibility = "visible";
      }
      if (currentStep === 5 && reviewEl) {
        const o = getOptions();
        reviewEl.textContent = "When: " + (o.when === "pre" ? "Pre-flash" : "Post-flash") + "\nDevice: " + (o.device_id || "—") + "\nFirmware: " + (o.firmware || "—") + "\nRegion: " + (o.region || "—") + "\nDevice name: " + (o.device_name || "—") + "\nPreset name: " + (o.preset_name || "—");
      }
    }

    function loadContext() {
      fetch("/api/config-wizard/context")
        .then((r) => r.json())
        .then((data) => {
          wizardContext = data;
          if (deviceSel) {
            deviceSel.innerHTML = "<option value=\"\">— Select device —</option>" + (data.devices || []).map((d) => "<option value=\"" + escapeHtml(d.id) + "\">" + escapeHtml(d.name || d.id) + "</option>").join("");
          }
          if (regionSel) {
            regionSel.innerHTML = "<option value=\"\">— Select region —</option>" + (data.rf_presets || []).map((p) => "<option value=\"" + escapeHtml(p.id) + "\">" + escapeHtml(p.name || p.id) + " " + (p.legal_warning ? "(" + p.legal_warning.substring(0, 40) + "…)" : "") + "</option>").join("");
          }
          renderSteps();
        })
        .catch(() => {});
    }

    deviceSel?.addEventListener("change", () => {
      const id = deviceSel.value;
      const dev = (wizardContext.devices || []).find((d) => d.id === id);
      if (!firmwareSel) return;
      const compat = dev ? (dev.compatible_firmware || []) : [];
      firmwareSel.innerHTML = "<option value=\"\">— Select firmware —</option>" + (wizardContext.firmware_targets || []).filter((f) => compat.indexOf(f.id) >= 0).map((f) => "<option value=\"" + escapeHtml(f.id) + "\">" + escapeHtml(f.name) + (f.internal ? " (internal)" : " (Launcher)") + "</option>").join("");
    });

    btnPrev?.addEventListener("click", () => { if (currentStep > 1) { currentStep--; renderSteps(); } });
    btnNext?.addEventListener("click", () => {
      if (currentStep < totalSteps) { currentStep++; renderSteps(); } else { currentStep = 5; renderSteps(); }
    });

    btnSavePreset?.addEventListener("click", () => {
      const o = getOptions();
      if (!o.device_id || !o.firmware) {
        if (resultEl) { resultEl.textContent = "Select device and firmware first."; resultEl.className = "flash-status flash-error"; }
        return;
      }
      const presetName = o.preset_name || "preset_" + Date.now();
      if (resultEl) resultEl.textContent = "Saving…";
      fetch("/api/config-wizard/presets", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          device_id: o.device_id,
          firmware: o.firmware,
          preset_name: presetName,
          options: { region: o.region, device_name: o.device_name },
        }),
      })
        .then((r) => r.json())
        .then((data) => {
          if (data.success) {
            if (resultEl) { resultEl.textContent = "Saved: " + (data.path || ""); resultEl.className = "flash-status flash-ok"; }
          } else {
            if (resultEl) { resultEl.textContent = data.error || "Failed"; resultEl.className = "flash-status flash-error"; }
          }
        })
        .catch((err) => { if (resultEl) { resultEl.textContent = "Error: " + err.message; resultEl.className = "flash-status flash-error"; } });
    });

    btnGotoFlash?.addEventListener("click", () => {
      const tab = document.getElementById("tab-btn-flash");
      if (tab) tab.click();
    });

    btnAiSend?.addEventListener("click", () => {
      const msg = (aiInput?.value || "").trim();
      if (!msg || !aiMessages) return;
      const o = getOptions();
      const userDiv = document.createElement("div");
      userDiv.className = "msg";
      userDiv.textContent = "You: " + msg;
      aiMessages.appendChild(userDiv);
      aiMessages.scrollTop = aiMessages.scrollHeight;
      if (aiInput) aiInput.value = "";
      fetch("/api/config-wizard/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: msg,
          step: "step_" + currentStep,
          device_id: o.device_id,
          firmware: o.firmware,
          options: { region: o.region, device_name: o.device_name },
        }),
      })
        .then((r) => r.json())
        .then((data) => {
          const replyDiv = document.createElement("div");
          replyDiv.className = "msg";
          replyDiv.textContent = "AI: " + (data.reply || "(No reply)");
          aiMessages.appendChild(replyDiv);
          aiMessages.scrollTop = aiMessages.scrollHeight;
        })
        .catch((err) => {
          const errDiv = document.createElement("div");
          errDiv.className = "msg";
          errDiv.textContent = "Error: " + err.message;
          aiMessages.appendChild(errDiv);
        });
    });
    aiInput?.addEventListener("keydown", (e) => { if (e.key === "Enter") btnAiSend?.click(); });

    const obs = new MutationObserver((mutations) => {
      mutations.forEach((m) => { if (m.attributeName === "hidden" && panel && !panel.hidden) loadContext(); });
    });
    if (panel) obs.observe(panel, { attributes: true });
  })();

  // --- Debug tab: live serial monitor + maintenance tools ---
  (function initDebugTab() {
    const serialPortSel = document.getElementById("debug-serial-port");
    const serialStartBtn = document.getElementById("debug-serial-start");
    const serialStopBtn = document.getElementById("debug-serial-stop");
    const serialStatusEl = document.getElementById("debug-serial-status");
    const serialLogEl = document.getElementById("debug-serial-log");
    const toolPortsBtn = document.getElementById("debug-tool-ports");
    const toolEsptoolBtn = document.getElementById("debug-tool-esptool");
    const toolHealthBtn = document.getElementById("debug-tool-health");
    const toolsOutputEl = document.getElementById("debug-tools-output");
    const panelDebug = document.getElementById("panel-debug");

    let serialPollTimer = null;

    function loadDebugPorts() {
      if (!serialPortSel) return;
      fetch("/api/flash/ports")
        .then((r) => r.json())
        .then((data) => {
          const ports = data.ports || [];
          const portValue = (p) => (typeof p === "string" ? p : (p && p.port)) || "";
          const portLabel = (p) => {
            if (typeof p === "string") return p;
            if (!p) return "";
            return p.description || p.port || "";
          };
          serialPortSel.innerHTML = '<option value="">— Select port —</option>' + ports.map((p) => '<option value="' + escapeHtml(portValue(p)) + '">' + escapeHtml(portLabel(p)) + "</option>").join("");
        })
        .catch(() => { serialPortSel.innerHTML = '<option value="">— Select port —</option>'; });
    }

    function pollSerialBuffer() {
      if (!serialLogEl) return;
      fetch("/api/debug/serial")
        .then((r) => r.json())
        .then((data) => {
          const lines = data.lines || [];
          serialLogEl.textContent = lines.length ? lines.join("\n") : "(no output yet)";
          serialLogEl.scrollTop = serialLogEl.scrollHeight;
          if (data.active && serialPollTimer === null) {
            serialPollTimer = setInterval(pollSerialBuffer, 1500);
          } else if (!data.active && serialPollTimer !== null) {
            clearInterval(serialPollTimer);
            serialPollTimer = null;
          }
        })
        .catch(() => {});
    }

    serialStartBtn?.addEventListener("click", () => {
      const port = serialPortSel?.value?.trim();
      if (!port) {
        if (serialStatusEl) serialStatusEl.textContent = "Select a port first.";
        return;
      }
      if (serialStatusEl) serialStatusEl.textContent = "Starting…";
      const baudEl = document.getElementById("debug-serial-baud");
      const baud = baudEl ? parseInt(baudEl.value, 10) : 115200;
      fetch("/api/debug/serial/start", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ port: port, baud: baud }),
      })
        .then((r) => r.json())
        .then((data) => {
          if (data.success) {
            if (serialStatusEl) serialStatusEl.textContent = data.message || "Listening.";
            serialPollTimer = setInterval(pollSerialBuffer, 1500);
            pollSerialBuffer();
          } else {
            if (serialStatusEl) serialStatusEl.textContent = data.error || "Failed.";
          }
        })
        .catch((err) => { if (serialStatusEl) serialStatusEl.textContent = "Error: " + err.message; });
    });

    serialStopBtn?.addEventListener("click", () => {
      fetch("/api/debug/serial/stop", { method: "POST" })
        .then(() => {
          if (serialPollTimer) { clearInterval(serialPollTimer); serialPollTimer = null; }
          if (serialStatusEl) serialStatusEl.textContent = "Stopped.";
          if (serialLogEl) serialLogEl.textContent = "";
        })
        .catch(() => {});
    });

    const serialClearBtn = document.getElementById("debug-serial-clear");
    serialClearBtn?.addEventListener("click", () => {
      fetch("/api/debug/serial/clear", { method: "POST" })
        .then(() => {
          if (serialLogEl) serialLogEl.textContent = "";
        })
        .catch(() => {});
    });

    function setToolsOutput(text) {
      if (toolsOutputEl) toolsOutputEl.textContent = text || "";
    }

    toolPortsBtn?.addEventListener("click", () => {
      setToolsOutput("Loading…");
      fetch("/api/flash/ports")
        .then((r) => r.json())
        .then((data) => {
          const ports = data.ports || [];
          setToolsOutput(ports.length ? JSON.stringify(ports, null, 2) : "No ports found.");
        })
        .catch((err) => setToolsOutput("Error: " + err.message));
    });

    toolEsptoolBtn?.addEventListener("click", () => {
      setToolsOutput("Checking…");
      fetch("/api/debug/tools/esptool-version")
        .then((r) => r.json())
        .then((data) => setToolsOutput(data.message || (data.ok ? "OK" : "Not found")))
        .catch((err) => setToolsOutput("Error: " + err.message));
    });

    toolHealthBtn?.addEventListener("click", () => {
      setToolsOutput("Running health check…");
      fetch("/api/debug/tools/health")
        .then((r) => r.json())
        .then((data) => {
          let out = "";
          (data.checks || []).forEach((c) => { out += (c.ok ? "[OK] " : "[FAIL] ") + c.name + ": " + (c.message || "") + "\n"; });
          if ((data.problems || []).length) {
            out += "\nProblems: " + data.problems.join("; ") + "\n";
            if (data.suggestions && data.suggestions.length) out += "Suggestions: " + data.suggestions.join("; ") + "\n";
          }
          setToolsOutput(out || "No checks returned.");
        })
        .catch((err) => setToolsOutput("Error: " + err.message));
    });

    const debugPanelObserver = new MutationObserver((mutations) => {
      mutations.forEach((m) => {
        if (m.attributeName === "hidden" && panelDebug && !panelDebug.hidden) loadDebugPorts();
      });
    });
    if (panelDebug) debugPanelObserver.observe(panelDebug, { attributes: true });
  })();

  // --- Project planning ---
  let currentProjectId = "";
  let currentBom = [];
  let currentMessages = [];
  let currentDesign = { pin_outs: [], wiring: [], schematic: "", enclosure: "" };
  let projectTemplatesData = { controllers: [], templates_by_controller: {} };

  function loadProjectTemplates() {
    fetch("/api/projects/templates")
      .then((r) => r.json())
      .then((data) => {
        projectTemplatesData.controllers = data.controllers || [];
        projectTemplatesData.templates_by_controller = data.templates_by_controller || {};
        projectTemplatesData.inventory_controller_ids = data.inventory_controller_ids || [];
        const sel = document.getElementById("project-controller");
        if (!sel) return;
        const cur = sel.value;
        const inInv = projectTemplatesData.inventory_controller_ids || [];
        const controllers = projectTemplatesData.controllers || [];
        const ordered = inInv.length
          ? inInv.map((id) => controllers.find((c) => c.id === id)).filter(Boolean).concat(controllers.filter((c) => !inInv.includes(c.id)))
          : controllers;
        sel.innerHTML = '<option value="">— Select —</option>' + ordered.map((c) => '<option value="' + escapeHtml(c.id) + '">' + escapeHtml(c.name || c.id) + (inInv.includes(c.id) ? " ✓" : "") + "</option>").join("");
        if (cur) sel.value = cur;
        else if (inInv.length) sel.value = inInv[0];
        onProjectControllerChange();
      })
      .catch(() => {});
  }

  function onProjectControllerChange() {
    const controllerId = document.getElementById("project-controller")?.value?.trim() || "";
    const wrap = document.getElementById("project-templates-wrap");
    const listEl = document.getElementById("project-templates-list");
    if (!wrap || !listEl) return;
    if (!controllerId) {
      wrap.hidden = true;
      listEl.innerHTML = "";
      return;
    }
    const templates = projectTemplatesData.templates_by_controller[controllerId] || [];
    if (templates.length === 0) {
      wrap.hidden = true;
      listEl.innerHTML = "";
      return;
    }
    wrap.hidden = false;
    listEl.innerHTML = templates
      .map(
        (t) =>
          '<button type="button" class="project-template-card" data-controller="' + escapeHtml(controllerId) + '" data-template-id="' + escapeHtml(t.id) + '">' +
          "<strong>" + escapeHtml(t.name || t.id) + "</strong>" +
          (t.description ? "<span class=\"project-template-desc\">" + escapeHtml(t.description) + "</span>" : "") +
          "</button>"
      )
      .join("");
    listEl.querySelectorAll(".project-template-card").forEach((btn) => {
      btn.addEventListener("click", () => {
        const cid = btn.getAttribute("data-controller") || "";
        const tid = btn.getAttribute("data-template-id") || "";
        const templatesForController = projectTemplatesData.templates_by_controller[cid] || [];
        const t = templatesForController.find((x) => x.id === tid);
        if (!t) return;
        const titleEl = document.getElementById("project-title");
        const descEl = document.getElementById("project-description");
        const msgEl = document.getElementById("project-message");
        if (titleEl) titleEl.value = t.name || t.id || "";
        if (descEl) descEl.value = t.description || "";
        if (msgEl) msgEl.value = t.prompt || "";
      });
    });
  }

  document.getElementById("project-controller")?.addEventListener("change", onProjectControllerChange);

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

  const BOM_ADD_CATEGORIES = ["component", "board", "module", "tool", "other"];

  function formatCurrency(n) {
    if (n == null || isNaN(n) || n === "") return "—";
    const num = Number(n);
    if (num === 0) return "$0.00";
    return "$" + num.toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, ",");
  }

  function computeBomTotal(bom) {
    const rows = bom || [];
    let total = 0;
    for (let i = 0; i < rows.length; i++) {
      const qty = Number(rows[i].quantity) || 0;
      const up = Number(rows[i].unit_price);
      if (!isNaN(up) && up >= 0) total += qty * up;
    }
    return total;
  }

  function updateProjectCost() {
    const el = document.getElementById("project-cost-summary");
    if (!el) return;
    const total = computeBomTotal(currentBom);
    const hasAnyPrice = (currentBom || []).some((r) => r.unit_price != null && r.unit_price !== "" && !isNaN(Number(r.unit_price)));
    if (!hasAnyPrice && total === 0) {
      el.textContent = "";
      el.className = "project-cost-summary";
      return;
    }
    el.textContent = "Project cost: " + formatCurrency(total);
    el.className = "project-cost-summary project-cost-summary-visible";
  }

  function renderBom(bom) {
    const tbody = document.getElementById("project-bom-tbody");
    if (!tbody) return;
    const rows = bom || [];
    const projectId = currentProjectId;
    tbody.innerHTML = rows
      .map(
        (r, idx) => {
          const catOpts = BOM_ADD_CATEGORIES.map((c) => '<option value="' + escapeHtml(c) + '">' + escapeHtml(c) + "</option>").join("");
          const qty = Number(r.quantity) || 0;
          const up = r.unit_price != null && r.unit_price !== "" ? Number(r.unit_price) : NaN;
          const lineTotal = !isNaN(up) && up >= 0 ? qty * up : null;
          const upVal = (r.unit_price != null && r.unit_price !== "") ? String(r.unit_price) : "";
          return (
            "<tr data-bom-index=\"" + idx + "\">" +
            "<td>" + escapeHtml(r.name || "—") + "</td>" +
            "<td>" + escapeHtml(r.part_number || "—") + "</td>" +
            "<td>" + (r.quantity ?? "—") + "</td>" +
            "<td><input type=\"number\" step=\"0.01\" min=\"0\" placeholder=\"0\" class=\"bom-unit-price\" data-index=\"" + idx + "\" value=\"" + escapeHtml(upVal) + "\" aria-label=\"Unit price for row " + (idx + 1) + "\"></td>" +
            "<td class=\"bom-line-total\">" + (lineTotal != null ? formatCurrency(lineTotal) : "—") + "</td>" +
            "<td>" + (r.qty_on_hand != null ? r.qty_on_hand : "—") + "</td>" +
            "<td>" + (r.shortfall != null && r.shortfall > 0 ? r.shortfall : "—") + "</td>" +
            "<td class=\"bom-actions\">" +
            "<button type=\"button\" class=\"bom-remove-btn\" data-index=\"" + idx + "\">Remove from BOM</button> " +
            "<select class=\"bom-add-category\" data-index=\"" + idx + "\"><option value=\"\">Category</option>" + catOpts + "</select> " +
            "<button type=\"button\" class=\"bom-add-to-inv-btn\" data-index=\"" + idx + "\">Add to inventory</button>" +
            "</td></tr>"
          );
        }
      )
      .join("");
    tbody.querySelectorAll(".bom-unit-price").forEach((input) => {
      const idx = parseInt(input.getAttribute("data-index"), 10);
      input.addEventListener("input", () => {
        const val = input.value.trim();
        if (!currentBom[idx]) return;
        currentBom[idx].unit_price = val === "" ? undefined : (parseFloat(val) || 0);
        const qty = Number(currentBom[idx].quantity) || 0;
        const up = Number(currentBom[idx].unit_price);
        const lineEl = input.closest("tr")?.querySelector(".bom-line-total");
        if (lineEl) lineEl.textContent = (!isNaN(up) && up >= 0) ? formatCurrency(qty * up) : "—";
        updateProjectCost();
      });
      input.addEventListener("change", () => {
        const val = input.value.trim();
        if (!currentBom[idx]) return;
        currentBom[idx].unit_price = val === "" ? undefined : (parseFloat(val) || 0);
        updateProjectCost();
      });
    });
    tbody.querySelectorAll(".bom-remove-btn").forEach((btn) => {
      btn.addEventListener("click", (e) => {
        e.stopPropagation();
        const index = parseInt(btn.getAttribute("data-index"), 10);
        if (!projectId) return;
        fetch("/api/projects/" + encodeURIComponent(projectId) + "/bom/items/" + index, { method: "DELETE" })
          .then((r) => r.json())
          .then((data) => {
            if (data.error) throw new Error(data.error);
            currentBom = data.parts_bom || [];
            renderBom(currentBom);
            updateProjectCost();
          })
          .catch((err) => alert(err.message));
      });
    });
    tbody.querySelectorAll(".bom-add-to-inv-btn").forEach((btn) => {
      btn.addEventListener("click", (e) => {
        e.stopPropagation();
        const index = parseInt(btn.getAttribute("data-index"), 10);
        const row = btn.closest("tr");
        const select = row ? row.querySelector(".bom-add-category") : null;
        const category = (select && select.value || "component").trim();
        if (!projectId) return;
        fetch("/api/inventory/from-bom", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ project_id: projectId, bom_index: index, category }),
        })
          .then((r) => r.json())
          .then((data) => {
            if (data.error) throw new Error(data.error);
            alert(data.message || "Added to inventory. Run scripts/build_db.py to refresh the database.");
          })
          .catch((err) => alert(err.message));
      });
    });
    updateProjectCost();
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
        const controllerSel = document.getElementById("project-controller");
        if (controllerSel) {
          const preferred = (proj.controller || "").trim() || (projectTemplatesData.inventory_controller_ids || [])[0];
          if (preferred && Array.from(controllerSel.options).some((o) => o.value === preferred)) controllerSel.value = preferred;
          onProjectControllerChange();
        }
        renderProjectMessages(currentMessages);
        renderBom(currentBom);
        renderDesign(currentDesign);
        updateProjectCost();
        if (digiLink) digiLink.href = "/api/projects/" + encodeURIComponent(projectId) + "/bom/digikey";
        if (mouserLink) mouserLink.href = "/api/projects/" + encodeURIComponent(projectId) + "/bom/mouser";
        setProjectExportLinks(projectId);
      })
      .catch(() => {
        currentMessages = [];
        currentBom = [];
        currentDesign = { pin_outs: [], wiring: [], schematic: "", enclosure: "" };
        const controllerSel = document.getElementById("project-controller");
        if (controllerSel && (projectTemplatesData.inventory_controller_ids || []).length) {
          const def = projectTemplatesData.inventory_controller_ids[0];
          if (Array.from(controllerSel.options).some((o) => o.value === def)) controllerSel.value = def;
          onProjectControllerChange();
        }
        renderProjectMessages([]);
        renderBom([]);
        renderDesign(currentDesign);
        updateProjectCost();
      });
  }

  document.getElementById("project-select")?.addEventListener("change", (e) => openProject((e.target.value || "").trim()));
  document.getElementById("btn-project-new")?.addEventListener("click", () => {
    const sel = document.getElementById("project-select");
    if (sel) sel.value = "";
    openProject("");
  });

  const panelProjects = document.getElementById("panel-projects");
  if (panelProjects) {
    const obsProjects = new MutationObserver((mutations) => {
      mutations.forEach((m) => {
        if (m.attributeName === "hidden" && !panelProjects.hidden && currentProjectId) {
          openProject(currentProjectId);
        }
      });
    });
    obsProjects.observe(panelProjects, { attributes: true });
  }

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
              updateProjectCost();
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

  (function setupHelpChat() {
    const messagesEl = document.getElementById("setup-help-messages");
    const inputEl = document.getElementById("setup-help-message");
    const btnSend = document.getElementById("btn-setup-help-send");
    const problemsBanner = document.getElementById("setup-help-problems-banner");
    const problemsText = document.getElementById("setup-help-problems-text");
    const btnAskFixes = document.getElementById("setup-help-ask-fixes");
    const panelSetupHelp = document.getElementById("panel-setup-help");
    if (!messagesEl || !inputEl || !btnSend) return;
    let setupHelpHistory = [];

    function renderSetupHelpMessages(msgs) {
      const list = msgs || [];
      messagesEl.innerHTML = list
        .map((m) => '<div class="project-msg project-msg-' + escapeHtml(m.role || "user") + '">' + escapeHtml(m.content || "").slice(0, 4000) + "</div>")
        .join("");
      messagesEl.scrollTop = messagesEl.scrollHeight;
    }

    function updateProblemsBanner(problems, suggestions) {
      if (!problemsBanner || !problemsText) return;
      if (!problems || !problems.length) {
        problemsBanner.hidden = true;
        return;
      }
      problemsText.textContent = problems.join(". ");
      if (suggestions && suggestions.length) problemsText.textContent += " Ask the AI for step-by-step fixes.";
      problemsBanner.hidden = false;
    }

    function fetchDebugContextAndShowProblems() {
      fetch("/api/debug/context")
        .then((r) => r.json())
        .then((data) => {
          if (data.health_problems && data.health_problems.length) {
            updateProblemsBanner(data.health_problems, data.health_suggestions);
          } else {
            if (problemsBanner) problemsBanner.hidden = true;
          }
        })
        .catch(() => {});
    }

    function sendSetupHelp() {
      const msg = (inputEl.value || "").trim();
      if (!msg) return;
      inputEl.value = "";
      setupHelpHistory.push({ role: "user", content: msg });
      renderSetupHelpMessages(setupHelpHistory);
      setupHelpHistory.push({ role: "assistant", content: "…" });
      renderSetupHelpMessages(setupHelpHistory);

      fetch("/api/setup/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: msg, history: setupHelpHistory.slice(0, -1) }),
      })
        .then((r) => {
          if (!r.ok) return r.json().then((j) => { throw new Error(j.error || r.statusText); });
          return r.json();
        })
        .then((data) => {
          setupHelpHistory[setupHelpHistory.length - 1].content = data.reply || "(No reply)";
          renderSetupHelpMessages(setupHelpHistory);
          if (data.problems && data.problems.length) {
            updateProblemsBanner(data.problems, data.suggestions);
          }
        })
        .catch((err) => {
          setupHelpHistory[setupHelpHistory.length - 1].content = "Error: " + err.message;
          renderSetupHelpMessages(setupHelpHistory);
        });
    }

    btnSend.addEventListener("click", sendSetupHelp);
    inputEl.addEventListener("keydown", (e) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        sendSetupHelp();
      }
    });

    btnAskFixes?.addEventListener("click", () => {
      fetch("/api/debug/context")
        .then((r) => r.json())
        .then((data) => {
          const problems = data.health_problems || [];
          if (problems.length && inputEl) {
            inputEl.value = "I see these issues: " + problems.join("; ") + ". What should I do?";
            inputEl.focus();
          }
        })
        .catch(() => {});
    });

    const setupHelpPanelObserver = new MutationObserver((mutations) => {
      mutations.forEach((m) => {
        if (m.attributeName === "hidden" && panelSetupHelp && !panelSetupHelp.hidden) fetchDebugContextAndShowProblems();
      });
    });
    if (panelSetupHelp) setupHelpPanelObserver.observe(panelSetupHelp, { attributes: true });
  })();

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
          const prev = currentBom;
          currentBom = (data.bom || []).map((row, i) => ({
            ...row,
            unit_price: (prev[i] && (prev[i].unit_price != null && prev[i].unit_price !== "")) ? prev[i].unit_price : row.unit_price,
          }));
          renderBom(currentBom);
          updateProjectCost();
        }
      })
      .catch(() => {});
  });

  document.getElementById("btn-project-save")?.addEventListener("click", () => {
    const title = (document.getElementById("project-title")?.value || "").trim();
    const description = (document.getElementById("project-description")?.value || "").trim();
    const statusEl = document.getElementById("project-save-status");
    const parts_bom = currentBom.map((r) => {
      const out = { name: r.name, part_number: r.part_number || "", quantity: r.quantity ?? 0 };
      if (r.unit_price != null && r.unit_price !== "" && !isNaN(Number(r.unit_price))) out.unit_price = Number(r.unit_price);
      return out;
    });
    const controllerVal = document.getElementById("project-controller")?.value?.trim() || undefined;
    const payload = {
      title: title || "Untitled project",
      description,
      parts_bom,
      conversation: currentMessages,
      pin_outs: currentDesign.pin_outs,
      wiring: currentDesign.wiring,
      schematic: currentDesign.schematic,
      enclosure: currentDesign.enclosure,
      controller: controllerVal,
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
  loadProjectTemplates();

  document.getElementById("inventory-btn-apply")?.addEventListener("click", () => fetchItems(buildInventoryQueryParams()));
  document.querySelectorAll("#inventory-table .sortable").forEach((th) => {
    th.addEventListener("click", () => {
      const col = (th.getAttribute("data-sort") || "category").toLowerCase();
      if (inventorySortColumn === col) inventorySortOrder = inventorySortOrder === "asc" ? "desc" : "asc";
      else { inventorySortColumn = col; inventorySortOrder = "asc"; }
      fetchItems(buildInventoryQueryParams());
    });
  });

  (function initAddDeviceWizard() {
    const vendorSelect = document.getElementById("device-wizard-vendor");
    const searchInput = document.getElementById("device-wizard-search");
    const listEl = document.getElementById("device-wizard-list");
    const formWrap = document.getElementById("device-wizard-form-wrap");
    const formId = document.getElementById("device-form-id");
    const formName = document.getElementById("device-form-name");
    const formMcu = document.getElementById("device-form-mcu");
    const formDatasheet = document.getElementById("device-form-datasheet");
    const formSchematic = document.getElementById("device-form-schematic");
    const formReposContainer = document.getElementById("device-form-firmware-repos");
    const btnAddRepo = document.getElementById("device-form-add-repo");
    const btnSubmit = document.getElementById("device-form-submit");
    const btnCancel = document.getElementById("device-form-cancel");
    const resultEl = document.getElementById("device-wizard-result");
    const panelAddDevice = document.getElementById("panel-add-device");
    const checkAddToInventory = document.getElementById("device-form-add-to-inventory");
    const inventoryCategoryWrap = document.getElementById("device-form-inventory-category-wrap");
    const inventoryCategorySelect = document.getElementById("device-form-inventory-category");
    const sdkRow = document.getElementById("device-form-sdk-row");
    const checkInstallSdk = document.getElementById("device-form-install-sdk");
    const sdkHint = document.getElementById("device-form-sdk-hint");
    const showImagesCheckbox = document.getElementById("device-wizard-show-images");
    const previewEl = document.getElementById("device-wizard-preview");
    const previewImg = document.getElementById("device-wizard-preview-img");
    const previewNameEl = document.getElementById("device-wizard-preview-name");

    const FLASHER_IMG_BASE = "https://flasher.meshtastic.org/img/devices";

    if (!listEl || !formWrap) return;

    const dropZone = document.getElementById("datasheet-drop-zone");
    const fileInput = document.getElementById("datasheet-file-input");
    const dropText = document.getElementById("datasheet-drop-text");
    const analyzingEl = document.getElementById("datasheet-analyzing");
    const resultElDs = document.getElementById("datasheet-result");
    if (dropZone && fileInput) {
      dropZone.addEventListener("click", (e) => {
        if (e.target === fileInput) return;
        fileInput.click();
      });
      fileInput.addEventListener("change", () => {
        const file = fileInput.files?.[0];
        if (file && file.type === "application/pdf") doDatasheetUpload(file);
        fileInput.value = "";
      });
      dropZone.addEventListener("dragover", (e) => { e.preventDefault(); dropZone.classList.add("dragover"); });
      dropZone.addEventListener("dragleave", () => dropZone.classList.remove("dragover"));
      dropZone.addEventListener("drop", (e) => {
        e.preventDefault();
        dropZone.classList.remove("dragover");
        const file = e.dataTransfer?.files?.[0];
        if (file && file.type === "application/pdf") doDatasheetUpload(file);
      });
    }
    function doDatasheetUpload(file) {
      if (!resultElDs || !analyzingEl || !dropText) return;
      resultElDs.hidden = true;
      resultElDs.className = "datasheet-result";
      dropText.hidden = true;
      analyzingEl.hidden = false;
      const fd = new FormData();
      fd.append("file", file);
      fetch("/api/devices/analyze-datasheet", { method: "POST", body: fd })
        .then((r) => r.json().then((j) => ({ ok: r.ok, ...j })))
        .then((data) => {
          dropText.hidden = false;
          analyzingEl.hidden = true;
          resultElDs.hidden = false;
          if (data.error) {
            resultElDs.className = "datasheet-result error";
            resultElDs.innerHTML = "<strong>Error</strong>: " + escapeHtml(data.error);
            return;
          }
          if (data.action === "assign") {
            resultElDs.className = "datasheet-result assign";
            resultElDs.innerHTML = "<strong>Matched</strong>: " + escapeHtml(data.message || "") +
              (data.design_context_path ? " <span class=\"datasheet-result-path\">Context: " + escapeHtml(data.design_context_path) + "</span>" : "") +
              (data.item_id ? " <a href=\"#\" data-tab=\"inventory\" data-open-item=\"" + escapeHtml(data.item_id) + "\">View in inventory</a>" : "");
            resultElDs.querySelector("[data-open-item]")?.addEventListener("click", (e) => {
              e.preventDefault();
              switchTab("inventory");
              openDetail(data.item_id);
            });
          } else {
            resultElDs.className = "datasheet-result create";
            const ex = data.extracted || {};
            let html = "<strong>New device suggested</strong>: " + escapeHtml(ex.name || data.suggested_id || "device") +
              (data.design_context_path ? " <span class=\"datasheet-result-path\">Context: " + escapeHtml(data.design_context_path) + "</span>" : "") +
              "<div class=\"datasheet-result-actions\"><button type=\"button\" class=\"btn-refresh datasheet-create-device-btn\">Create device structure</button></div>";
            resultElDs.innerHTML = html;
            resultElDs.querySelector(".datasheet-create-device-btn")?.addEventListener("click", () => {
              if (formId) formId.value = data.suggested_id || "";
              if (formName) formName.value = (ex.name || data.suggested_id || "").trim();
              if (formMcu) formMcu.value = (ex.mcu || "").trim();
              if (inventoryCategorySelect) inventoryCategorySelect.value = (ex.category || "controller").trim();
              if (checkAddToInventory) checkAddToInventory.checked = true;
              if (inventoryCategoryWrap) inventoryCategoryWrap.hidden = false;
              formWrap.hidden = false;
              resultElDs.scrollIntoView({ behavior: "smooth", block: "nearest" });
            });
          }
        })
        .catch((err) => {
          dropText.hidden = false;
          analyzingEl.hidden = true;
          resultElDs.hidden = true;
          resultElDs.className = "datasheet-result error";
          resultElDs.innerHTML = "<strong>Error</strong>: " + escapeHtml(err.message || "Upload failed");
          resultElDs.hidden = false;
        });
    }

    checkAddToInventory?.addEventListener("change", () => {
      if (inventoryCategoryWrap) inventoryCategoryWrap.hidden = !checkAddToInventory.checked;
    });

    showImagesCheckbox?.addEventListener("change", () => {
      if (!previewEl) return;
      if (showImagesCheckbox.checked) {
        previewEl.hidden = false;
        previewEl.setAttribute("aria-hidden", "false");
        updatePreview(selectedDevice);
      } else {
        previewEl.hidden = true;
        previewEl.setAttribute("aria-hidden", "true");
        selectedDevice = null;
        updatePreview(null);
      }
    });

    let catalogData = { vendors: [], devices: [] };
    let selectedVendor = "";
    let selectedDevice = null;
    let flasherImageBase = FLASHER_IMG_BASE;

    function updatePreview(device) {
      if (!previewEl || !previewImg || !previewNameEl) return;
      if (showImagesCheckbox && !showImagesCheckbox.checked) return;
      if (device && device.flasher_image) {
        previewImg.src = (flasherImageBase || FLASHER_IMG_BASE).replace(/\/$/, "") + "/" + device.flasher_image;
        previewImg.alt = device.name || "";
        previewNameEl.textContent = device.name || "";
        previewImg.hidden = false;
      } else {
        previewImg.removeAttribute("src");
        previewImg.alt = "";
        previewNameEl.textContent = "Select a device";
        previewImg.hidden = true;
      }
    }

    function buildCatalogQuery() {
      const params = new URLSearchParams();
      const v = (vendorSelect?.value || "").trim();
      const q = (searchInput?.value || "").trim();
      if (v) params.set("vendor", v);
      if (q) params.set("q", q);
      return params.toString();
    }

    function renderDeviceList(devices, vendors) {
      const byVendor = {};
      vendors.forEach((vr) => { byVendor[vr.id] = vr.name; });
      devices.forEach((d) => {
        const v = d.vendor || "other";
        if (!byVendor[v]) byVendor[v] = v;
        if (!byVendor[v + "_list"]) byVendor[v + "_list"] = [];
        byVendor[v + "_list"].push(d);
      });
      const vendorOrder = vendors.length ? vendors.map((v) => v.id) : Object.keys(byVendor).filter((k) => !k.endsWith("_list"));
      let html = "";
      vendorOrder.forEach((vid) => {
        const list = byVendor[vid + "_list"] || devices.filter((d) => (d.vendor || "") === vid);
        const label = byVendor[vid] || vid;
        if (!list.length) return;
        html += '<div class="add-device-vendor-group">';
        html += '<button type="button" class="add-device-vendor-toggle" aria-expanded="true" data-vendor="' + escapeHtml(vid) + '">' + escapeHtml(label) + ' <span class="add-device-vendor-count">' + list.length + '</span></button>';
        html += '<div class="add-device-vendor-devices">';
        list.forEach((d) => {
          const inLab = d.already_in_lab;
          const flasherImg = d.flasher_image ? escapeHtml(d.flasher_image) : "";
          html += '<div class="add-device-row" data-id="' + escapeHtml(d.id) + '" data-name="' + escapeHtml(d.name || d.id) + '" data-mcu="' + escapeHtml(d.mcu || "") + '" data-vendor="' + escapeHtml(byVendor[d.vendor] || d.vendor || "") + '" data-vendor-id="' + escapeHtml(d.vendor || "") + '"' + (flasherImg ? ' data-flasher-image="' + flasherImg + '"' : "") + '>';
          html += '<span class="add-device-row-name">' + escapeHtml(d.name || d.id) + '</span>';
          html += ' <span class="add-device-row-mcu">' + escapeHtml(d.mcu || "") + '</span>';
          if (inLab) html += ' <span class="add-device-badge">Already in lab</span>';
          else html += ' <button type="button" class="add-device-row-add btn-refresh">Add</button>';
          html += '</div>';
        });
        html += "</div></div>";
      });
      listEl.innerHTML = html || "<p class=\"add-device-empty\">No devices match. Try another vendor or search.</p>";

      listEl.querySelectorAll(".add-device-vendor-toggle").forEach((btn) => {
        btn.addEventListener("click", () => {
          const expanded = btn.getAttribute("aria-expanded") !== "false";
          btn.setAttribute("aria-expanded", expanded ? "false" : "true");
          btn.nextElementSibling.classList.toggle("add-device-vendor-collapsed", expanded);
        });
      });
      listEl.querySelectorAll(".add-device-row-add").forEach((btn) => {
        btn.addEventListener("click", () => {
          const row = btn.closest(".add-device-row");
          if (!row) return;
          const id = row.getAttribute("data-id");
          const name = row.getAttribute("data-name");
          const mcu = row.getAttribute("data-mcu") || "";
          const vendor = row.getAttribute("data-vendor") || "";
          const vendorId = row.getAttribute("data-vendor-id") || "";
          const flasherImage = row.getAttribute("data-flasher-image") || "";
          if (formId) formId.value = id || "";
          if (formName) formName.value = name || "";
          if (formMcu) formMcu.value = mcu || "";
          if (formDatasheet) formDatasheet.value = "";
          if (formSchematic) formSchematic.value = "";
          if (formReposContainer) {
            formReposContainer.innerHTML = '<input type="url" class="device-form-repo" placeholder="https://github.com/…" autocomplete="off">';
          }
          if (checkAddToInventory) checkAddToInventory.checked = false;
          if (inventoryCategoryWrap) inventoryCategoryWrap.hidden = true;
          if (inventoryCategorySelect) {
            inventoryCategorySelect.value = (vendorId === "raspberry_pi" || vendorId === "pine64") ? "sbc" : "controller";
          }
          const catalogDevice = (catalogData.devices || []).find((d) => (d.id || "") === (id || ""));
          const hasSdk = catalogDevice && catalogDevice.sdk && catalogDevice.sdk.available;
          if (sdkRow) sdkRow.hidden = !hasSdk;
          if (checkInstallSdk) checkInstallSdk.checked = hasSdk && (catalogDevice.sdk.default_install !== false);
          if (sdkHint && hasSdk && catalogDevice.sdk.platform_id) {
            sdkHint.textContent = "PlatformIO platform \"" + (catalogDevice.sdk.platform_id || "") + "\" will be installed so builds work for this device.";
          }
          if (resultEl) resultEl.textContent = "";
          selectedVendor = vendor || "";
          selectedDevice = flasherImage ? { flasher_image: flasherImage, name: name || "" } : null;
          if (showImagesCheckbox && showImagesCheckbox.checked && previewEl) {
            previewEl.hidden = false;
            previewEl.setAttribute("aria-hidden", "false");
            updatePreview(selectedDevice);
          }
          formWrap.hidden = false;
        });
      });
      listEl.querySelectorAll(".add-device-row").forEach((row) => {
        if (row.querySelector(".add-device-row-add")) return;
        row.addEventListener("click", () => {
          const addBtn = row.querySelector(".add-device-row-add");
          if (addBtn) addBtn.click();
        });
      });
      if (showImagesCheckbox && previewEl) {
        listEl.querySelectorAll(".add-device-row[data-flasher-image]").forEach((row) => {
          row.addEventListener("mouseenter", () => {
            if (!showImagesCheckbox.checked) return;
            const img = row.getAttribute("data-flasher-image");
            const name = row.getAttribute("data-name") || "";
            if (img) updatePreview({ flasher_image: img, name: name });
          });
          row.addEventListener("mouseleave", () => {
            if (!showImagesCheckbox.checked) return;
            updatePreview(selectedDevice);
          });
        });
        if (showImagesCheckbox.checked) {
          previewEl.hidden = false;
          previewEl.setAttribute("aria-hidden", "false");
          updatePreview(selectedDevice);
        }
      }
    }

    function loadDeviceCatalog() {
      const query = buildCatalogQuery();
      fetch("/api/devices/catalog" + (query ? "?" + query : ""))
        .then((r) => r.json())
        .then((data) => {
          catalogData = data;
          flasherImageBase = data.flasher_image_base || FLASHER_IMG_BASE;
          const vendors = data.vendors || [];
          const devices = data.devices || [];
          if (vendorSelect) {
            vendorSelect.innerHTML = '<option value="">All vendors</option>' + vendors.map((v) => '<option value="' + escapeHtml(v.id) + '">' + escapeHtml(v.name) + '</option>').join("");
          }
          renderDeviceList(devices, vendors);
        })
        .catch((err) => {
          listEl.innerHTML = "<p class=\"add-device-empty\">Failed to load catalog: " + escapeHtml(err.message) + "</p>";
        });
    }

    function onAddDeviceTabVisible() {
      if (catalogData.vendors.length === 0) loadDeviceCatalog();
    }

    const observer = new MutationObserver((mutations) => {
      mutations.forEach((m) => {
        if (m.attributeName === "hidden") {
          if (panelAddDevice && !panelAddDevice.hidden) onAddDeviceTabVisible();
        }
      });
    });
    if (panelAddDevice) observer.observe(panelAddDevice, { attributes: true });

    vendorSelect?.addEventListener("change", loadDeviceCatalog);
    searchInput?.addEventListener("input", () => { if (searchInput.value.trim().length >= 2 || searchInput.value.trim() === "") loadDeviceCatalog(); });
    searchInput?.addEventListener("keydown", (e) => { if (e.key === "Enter") loadDeviceCatalog(); });

    btnAddRepo?.addEventListener("click", () => {
      const input = document.createElement("input");
      input.type = "url";
      input.className = "device-form-repo";
      input.placeholder = "https://github.com/…";
      input.setAttribute("autocomplete", "off");
      formReposContainer?.appendChild(input);
    });

    btnCancel?.addEventListener("click", () => {
      formWrap.hidden = true;
    });

    btnSubmit?.addEventListener("click", () => {
      const device_id = (formId?.value || "").trim();
      const name = (formName?.value || "").trim();
      const mcu = (formMcu?.value || "").trim();
      const vendor = selectedVendor.trim();
      if (!device_id && !name) {
        if (resultEl) { resultEl.textContent = "Enter device ID or name."; resultEl.className = "flash-status flash-error"; }
        return;
      }
      const repoInputs = formReposContainer?.querySelectorAll(".device-form-repo") || [];
      const firmware_repos = [];
      repoInputs.forEach((inp) => { const v = (inp.value || "").trim(); if (v) firmware_repos.push(v); });
      const doc_links = {
        datasheet: (formDatasheet?.value || "").trim() || undefined,
        schematic: (formSchematic?.value || "").trim() || undefined,
        firmware_repos: firmware_repos.length ? firmware_repos : undefined,
      };
      if (resultEl) { resultEl.textContent = "Creating…"; resultEl.className = "flash-status"; }
      const add_to_inventory = !!(checkAddToInventory?.checked);
      const inventory_category = (inventoryCategorySelect?.value || "controller").trim();
      const install_sdk = sdkRow && !sdkRow.hidden ? !!(checkInstallSdk?.checked) : false;
      fetch("/api/devices/scaffold", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          device_id: device_id || name,
          name: name || device_id,
          vendor,
          mcu,
          doc_links,
          add_to_inventory,
          inventory_category: add_to_inventory ? inventory_category : undefined,
          install_sdk,
        }),
      })
        .then((r) => r.json().then((data) => ({ ok: r.ok, data })))
        .then(({ ok, data }) => {
          if (ok && data.success) {
            let msg = "Created: " + (data.paths?.device_dir || "") + ".";
            if (data.sdk_message) msg += " SDK: " + data.sdk_message + ".";
            if (data.paths?.sdk_install_error) msg += " (SDK install failed: " + data.paths.sdk_install_error + ")";
            if (data.paths?.inventory_file) msg += " Added to " + data.paths.inventory_file + ". Run build_db to update the DB.";
            msg += " Add more or refresh the list.";
            if (resultEl) { resultEl.textContent = msg; resultEl.className = "flash-status flash-ok"; }
            formWrap.hidden = true;
            loadDeviceCatalog();
          } else {
            if (resultEl) { resultEl.textContent = data.error || "Failed"; resultEl.className = "flash-status flash-error"; }
          }
        })
        .catch((err) => {
          if (resultEl) { resultEl.textContent = "Error: " + err.message; resultEl.className = "flash-status flash-error"; }
        });
    });
  })();
})();
