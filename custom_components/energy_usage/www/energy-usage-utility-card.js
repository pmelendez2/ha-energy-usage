// SPDX-License-Identifier: MIT
// Copyright (c) 2026 Project Contributors
// Green Button XML remains in browser memory until the user imports it.
class EnergyUsageUtilityCard extends HTMLElement {
  setConfig(config) {
    if (!config || config.type !== "custom:energy-usage-utility-card") {
      throw new Error("Invalid Energy Usage utility card configuration");
    }
    this.config = {...config};
    this.render();
  }

  set hass(value) {
    const first = !this._hass;
    this._hass = value;
    if (first && this.loadSources) this.loadSources();
  }
  getCardSize() { return 6; }
  static getConfigElement() {
    return document.createElement("energy-usage-utility-card-editor");
  }
  static getStubConfig() {
    return {type: "custom:energy-usage-utility-card"};
  }


  render() {
    if (this.shadowRoot) return;
    const root = this.attachShadow({mode: "open"});
    const style = document.createElement("style");
    style.textContent = `
      article { padding: 16px; color: var(--primary-text-color); }
      label { display: block; margin: 12px 0; }
      [hidden] { display: none !important; }
      input[type=file] { display: block; margin-top: 6px; max-width: 100%; }
      button, a { margin: 8px 8px 8px 0; }
      ul { list-style: none; padding: 0; }
      li { margin: 6px 0; overflow-wrap: anywhere; }
      li label { display: inline; margin: 0; }
      pre { white-space: pre-wrap; overflow-wrap: anywhere; }
    `;
    root.appendChild(style);
    const card = document.createElement("ha-card");
    const article = document.createElement("article");
    const heading = document.createElement("h2");
    heading.textContent = "Update utility data";
    article.appendChild(heading);
    const download = document.createElement("a");
    download.target = "_blank";
    download.rel = "noopener noreferrer";
    download.hidden = true;
    article.appendChild(download);
    const sourceLabel = document.createElement("label");
    sourceLabel.textContent = "Utility Company";
    const sourceSelect = document.createElement("select");
    sourceSelect.setAttribute("aria-label", "Utility Company");
    sourceSelect.disabled = true;
    sourceLabel.appendChild(sourceSelect);
    sourceLabel.hidden = true;
    article.appendChild(sourceLabel);
    const sites = this.config.utility_websites || {};
    const setDownload = () => {
      const selected = sourceSelect.selectedOptions[0];
      const utilityId = selected && selected.dataset.utilityId;
      const utilityName = selected && selected.textContent;
      const raw = sites[utilityId] ||
        (sourceSelect.options.length === 1 ? this.config.utility_url : "");
      let url;
      try {
        url = new URL(raw);
        if (url.protocol !== "https:") throw new Error();
      } catch (_) {
        download.hidden = true;
        return;
      }
      download.href = url.href;
      download.textContent = `Download data from ${utilityName}`;
      download.hidden = false;
    };
    sourceSelect.addEventListener("change", setDownload);
    let availableMeters = [];
    const loadSources = async () => {
      if (!this._hass) return;
      try {
        const response = await this._hass.callApi(
          "GET", "energy-usage/utility-upload"
        );
        availableMeters = (response.meters || []).filter(meter =>
          Number.isSafeInteger(meter.id) && meter.id > 0 &&
          [1, 7].includes(Number(meter.commodity))
        );
        sourceSelect.replaceChildren();
        const utilities = new Map();
        for (const source of response.sources || []) {
          if (typeof source.utility_company !== "string" ||
              !source.utility_company.trim()) {
            throw new Error("Energy Ingest must return utility_company");
          }
          const key = String(source.data_custodian_id);
          if (!utilities.has(key)) utilities.set(key, []);
          utilities.get(key).push(source);
        }
        for (const [utilityId, sources] of utilities) {
          // A utility with multiple sources requires explicit configuration.
          if (sources.length !== 1) {
            throw new Error(`Utility ${sources[0].utility_company} has ` +
              "multiple acquisition sources; configure a single source " +
              "before importing.");
          }
          const option = document.createElement("option");
          option.value = String(sources[0].id);
          option.dataset.utilityId = utilityId;
          option.textContent = sources[0].utility_company;
          sourceSelect.appendChild(option);
        }
        sourceLabel.hidden = sourceSelect.options.length <= 1;
        sourceSelect.disabled = !sourceSelect.options.length;
        const preferred = String(this.config.source_id || "");
        if ([...sourceSelect.options].some(o => o.value === preferred)) {
          sourceSelect.value = preferred;
        }
        setDownload();
        update();
      } catch (error) {
        sourceSelect.replaceChildren();
        sourceSelect.disabled = true;
        download.hidden = true;
        status.textContent = "Cannot retrieve utility companies: " +
          utilityErrorMessage(error);
        update();
      }
    };
    const instructions = document.createElement("p");
    instructions.textContent = "Add XML files, a folder, or both. " +
      "Review the checked files, import, then confirm each physical meter.";
    article.appendChild(instructions);
    const picker = (text, folder) => {
      const input = document.createElement("input");
      input.type = "file";
      input.accept = ".xml,application/xml,text/xml";
      input.multiple = true;
      input.hidden = true;
      input.style.display = "none";
      if (folder) {
        input.setAttribute("webkitdirectory", "");
        input.setAttribute("directory", "");
      }
      const button = document.createElement("button");
      button.type = "button";
      button.textContent = text;
      button.addEventListener("click", () => input.click());
      article.append(button, input);
      return {input, button};
    };
    const filesControl = picker("Choose Files", false);
    const folderControl = picker("Choose Folder", true);
    const filesPicker = filesControl.input;
    const folderPicker = folderControl.input;
    const count = document.createElement("p");
    count.setAttribute("aria-live", "polite");
    count.textContent = "No XML files selected.";
    article.appendChild(count);
    const controls = document.createElement("div");
    const selectAll = document.createElement("button");
    selectAll.textContent = "Select all";
    const clear = document.createElement("button");
    clear.textContent = "Clear selection";
    controls.append(selectAll, clear);
    article.appendChild(controls);
    selectAll.disabled = true;
    clear.disabled = true;
    const list = document.createElement("ul");
    list.setAttribute("aria-label", "Discovered XML files");
    article.appendChild(list);
    const retry = document.createElement("button");
    retry.textContent = "Retry Recorder synchronization";
    retry.disabled = true;
    article.appendChild(retry);
    const button = document.createElement("button");
    button.textContent = "Import XML files";
    button.dataset.upload = "1";
    button.disabled = true;
    article.appendChild(button);
    const mappingHeading = document.createElement("h3");
    mappingHeading.textContent = "Confirm physical meters";
    mappingHeading.hidden = true;
    article.appendChild(mappingHeading);
    const mappingList = document.createElement("div");
    mappingList.style.maxHeight = "320px";
    mappingList.style.overflowY = "auto";
    article.appendChild(mappingList);
    const confirm = document.createElement("button");
    confirm.textContent = "Confirm associations and synchronize";
    confirm.hidden = true;
    confirm.disabled = true;
    article.appendChild(confirm);
    const status = document.createElement("pre");
    status.setAttribute("role", "status");
    status.textContent = "Select files or a folder to review XML documents.";
    article.appendChild(status);

    let candidates = [];
    let busy = false;
    let pendingResources = [];
    const selected = () => candidates.filter(item => item.checked);
    const update = () => {
      button.disabled = busy || sourceSelect.disabled ||
        selected().length === 0;
      sourceSelect.disabled = busy || !sourceSelect.options.length;
      download.setAttribute("aria-disabled", String(busy));
      retry.disabled = busy || !retry.dataset.available ||
        pendingResources.some(item => !item.meterId);
      confirm.disabled = busy || !pendingResources.length ||
        pendingResources.some(item => !item.meterId);
      selectAll.disabled = busy || candidates.length === 0 ||
        selected().length === candidates.length;
      clear.disabled = busy || selected().length === 0;
      filesPicker.disabled = busy;
      folderPicker.disabled = busy;
      filesControl.button.disabled = busy;
      folderControl.button.disabled = busy;
      count.textContent = `${selected().length} of ` +
        `${candidates.length} XML file(s) selected.`;
    };
    const show = (files) => {
      // File and folder selections are additive. Never discard a previous
      // selection when the other picker is used.
      const incoming = Array.from(files).filter(file =>
        file.name.toLowerCase().endsWith(".xml")
      );
      const key = file => [file.webkitRelativePath || file.name,
        file.size, file.lastModified].join("\u0000");
      const existing = new Set(candidates.map(item => key(item.file)));
      for (const file of incoming) {
        if (!existing.has(key(file))) {
          candidates.push({file, checked: true});
          existing.add(key(file));
        }
      }
      candidates.sort((a, b) =>
        (a.file.webkitRelativePath || a.file.name).localeCompare(
          b.file.webkitRelativePath || b.file.name
        )
      );
      list.replaceChildren();
      for (const item of candidates) {
        const li = document.createElement("li");
        const label = document.createElement("label");
        const checkbox = document.createElement("input");
        checkbox.type = "checkbox";
        checkbox.checked = item.checked;
        checkbox.addEventListener("change", () => {
          item.checked = checkbox.checked;
          update();
        });
        const name = item.file.webkitRelativePath || item.file.name;
        label.append(checkbox, document.createTextNode(
          ` ${name} (${item.file.size} bytes)`
        ));
        li.appendChild(label);
        list.appendChild(li);
      }
      status.textContent = candidates.length ?
        `${candidates.length} XML file(s) discovered. ` +
          "Review the selection before importing." :
        "No XML files found. Select XML files or another folder.";
      update();
    };
    filesPicker.addEventListener("change", () => {
      show(filesPicker.files);
      filesPicker.value = "";
    });
    folderPicker.addEventListener("change", () => {
      show(folderPicker.files);
      folderPicker.value = "";
    });
    const toggle = (checked) => {
      for (const item of candidates) item.checked = checked;
      for (const checkbox of list.querySelectorAll("input[type=checkbox]")) {
        checkbox.checked = checked;
      }
      update();
    };
    selectAll.addEventListener("click", () => toggle(true));
    clear.addEventListener("click", () => toggle(false));

    const renderMappings = () => {
      mappingList.replaceChildren();
      mappingHeading.hidden = !pendingResources.length;
      confirm.hidden = !pendingResources.length;
      for (const item of pendingResources) {
        const label = document.createElement("label");
        label.textContent = `Reading resource ${item.resourceId} — physical meter`;
        const select = document.createElement("select");
        select.setAttribute("aria-label", `Meter for resource ${item.resourceId}`);
        const placeholder = document.createElement("option");
        placeholder.value = "";
        placeholder.textContent = "Select physical meter";
        select.appendChild(placeholder);
        for (const meter of availableMeters) {
          const option = document.createElement("option");
          option.value = String(meter.id);
          option.textContent = `${meter.display_name || meter.name ||
            `Meter ${meter.id}`} (ID ${meter.id}, ` +
            `${Number(meter.commodity) === 1 ? "Electricity" : "Gas"})`;
          select.appendChild(option);
        }
        select.value = item.meterId ? String(item.meterId) : "";
        select.addEventListener("change", () => {
          item.meterId = Number(select.value) || null;
          update();
        });
        select.disabled = busy;
        label.appendChild(select);
        mappingList.appendChild(label);
      }
      update();
    };
    const submitMappings = async () => {
      if (!this._hass || busy || !pendingResources.length ||
          pendingResources.some(item => !item.meterId)) return;
      busy = true;
      update();
      try {
        const result = await this._hass.callApi(
          "POST", "energy-usage/utility-upload", {
            associations: pendingResources.map(item => ({
              resource_id: item.resourceId, meter_id: item.meterId,
            })),
          }
        );
        if (!result.synchronized) {
          throw new Error(result.error || "Synchronization not confirmed");
        }
        status.textContent = "Meter associations confirmed. " +
          "Recorder synchronization verified for meters: " +
          (result.meter_ids || []).join(", ");
        pendingResources = [];
        delete retry.dataset.available;
      } catch (error) {
        status.textContent = "Association or Recorder retry needed: " +
          utilityErrorMessage(error);
        retry.dataset.available = "1";
      } finally {
        busy = false;
        renderMappings();
      }
    };
    confirm.addEventListener("click", submitMappings);
    button.addEventListener("click", async () => {
      if (!this._hass) {
        status.textContent = "Home Assistant unavailable";
        return;
      }
      const queue = selected();
      if (!queue.length) return;
      // Source selection is explicit; never guess commodity from filenames.
      const sourceId = Number(sourceSelect.value);
      if (!Number.isSafeInteger(sourceId) || sourceId <= 0) {
        status.textContent = "Select a utility company.";
        return;
      }
      busy = true;
      delete retry.dataset.available;
      pendingResources = [];
      renderMappings();
      update();
      const outcomes = [];
      try {
        for (let i = 0; i < queue.length; i++) {
          const file = queue[i].file;
          if (file.size === 0 || file.size > 8 * 1024 * 1024) {
            throw new Error(`${file.name}: XML must be 1 byte to 8 MiB`);
          }
          status.textContent = `Importing ${i + 1}/${queue.length}: ` +
            file.name;
          const bytes = new Uint8Array(await file.arrayBuffer());
          let binary = "";
          for (let j = 0; j < bytes.length; j += 32768) {
            binary += String.fromCharCode(...bytes.subarray(j, j + 32768));
          }
          const result = await this._hass.callApi(
            "POST", "energy-usage/utility-upload", {
              source_id: sourceId,
              xml_base64: btoa(binary),
              // Meter association must be confirmed after all imports.
            }
          );
          outcomes.push({file: file.name, result});
          const ids = result.import && result.import.resource_ids;
          if (!Array.isArray(ids) || ids.some(id =>
            !Number.isSafeInteger(id) || id <= 0)) {
            throw new Error("Invalid imported resource identities");
          }
          for (const resourceId of ids) {
            if (!pendingResources.some(item => item.resourceId === resourceId)) {
              pendingResources.push({resourceId, meterId: null});
            }
          }
        }
        status.textContent = formatImportSummary(outcomes, false) +
          "\nConfirm the physical meter for each imported resource.";
        renderMappings();
      } catch (error) {
        if (pendingResources.length) renderMappings();
        status.textContent = "Stopped: " + utilityErrorMessage(error) +
          (outcomes.length ? "\n" + formatImportSummary(outcomes, false) : "");
      } finally {
        busy = false;
        update();
      }
    });
    retry.addEventListener("click", submitMappings);
    // Fetch only after the card has Home Assistant's authenticated client.
    this.loadSources = loadSources;
    card.appendChild(article);
    root.appendChild(card);
  }
}
// Summarize accepted utility observations without exposing raw API JSON.
// meter_ids refer to Recorder synchronization, not necessarily XML contents.
function formatImportSummary(outcomes, synchronized) {
  const lines = [synchronized ?
    "Import and synchronization completed." :
    "Import completed; meter association pending."];
  let checked = 0;
  let unchanged = 0;
  let accepted = 0;
  for (const outcome of outcomes) {
    const result = outcome.result || {};
    const imported = result.import || {};
    for (const key of ["observations", "unchanged", "accepted"]) {
      if (!Number.isSafeInteger(imported[key]) || imported[key] < 0) {
        throw new Error("Invalid import statistics from Energy Ingest");
      }
    }
    checked += imported.observations;
    unchanged += imported.unchanged;
    accepted += imported.accepted;
    lines.push(`File: ${outcome.file}`);
  }
  lines.push(`XML files processed: ${outcomes.length}`);
  lines.push(`Observations checked: ${checked}`);
  lines.push(`Already recorded: ${unchanged}`);
  lines.push(`New observations accepted: ${accepted}`);
  lines.push("Recorder synchronization: " +
    (synchronized ? "Completed" : "Not confirmed"));
  const last = outcomes[outcomes.length - 1];
  const meters = last && last.result && last.result.meter_ids;
  if (Array.isArray(meters) && meters.length) {
    lines.push("Recorder meters synchronized: " + meters.join(", "));
    lines.push("These meter IDs do not identify the XML file's commodity.");
  }
  return lines.join("\n");
}

// Home Assistant callApi may reject with a response object rather than Error.
// Do not print credentials or raw response bodies into the dashboard.
function utilityErrorMessage(error) {
  if (typeof error === "string") return error.slice(0, 300);
  if (!error || typeof error !== "object") return "Unknown error";
  const status = Number(error.status || error.statusCode);
  const code = Number.isInteger(status) && status >= 100 && status <= 599 ?
    `HTTP ${status}: ` : "";
  const detail = [error.message, error.error, error.code].find(
    value => typeof value === "string" && value.trim()
  );
  return code + (detail ? detail.slice(0, 300) :
    "Request failed (see Home Assistant logs)");
}

class EnergyUsageUtilityCardEditor extends HTMLElement {
  setConfig(config) {
    this._config = {...config};
    this.render();
  }
  set hass(value) {
    const firstConnection = !this._hass && !!value;
    this._hass = value;
    if (firstConnection && this._config) this.render();
  }
  render() {
    if (!this._config) return;
    if (!this.shadowRoot) this.attachShadow({mode: "open"});
    const root = this.shadowRoot;
    root.replaceChildren();
    const style = document.createElement("style");
    style.textContent = `
      label { display: block; margin: 12px 0; }
      input { display: block; box-sizing: border-box; width: 100%;
        padding: 10px; margin-top: 5px; border-radius: 4px;
        color: var(--primary-text-color);
        background: var(--card-background-color);
        border: 1px solid var(--divider-color); }
      p { color: var(--secondary-text-color); }
    `;
    root.appendChild(style);
    const help = document.createElement("p");
    help.textContent = "Energy Ingest connection and credentials are " +
      "configured in the Energy Usage integration, not in this card.";
    root.appendChild(help);
    const field = (name, key, placeholder, kind) => {
      const label = document.createElement("label");
      label.textContent = name;
      const input = document.createElement("input");
      input.type = kind;
      input.placeholder = placeholder;
      input.value = this._config[key] || "";
      input.addEventListener("change", () => {
        const next = {...this._config};
        const value = input.value.trim();
        if (key === "utility_url" && value) {
          try {
            const url = new URL(value);
            if (url.protocol !== "https:") throw new Error();
          } catch (_) {
            input.setCustomValidity("Enter an HTTPS website URL");
            input.reportValidity();
            return;
          }
        }
        input.setCustomValidity("");
        if (key === "source_id" && value &&
            (!Number.isSafeInteger(Number(value)) || Number(value) <= 0)) {
          input.setCustomValidity("Enter a positive source ID");
          input.reportValidity();
          return;
        }
        if (value) next[key] = key === "source_id" ? Number(value) : value;
        else delete next[key];
        this._config = next;
        this.dispatchEvent(new CustomEvent("config-changed", {
          detail: {config: {...next}}, bubbles: true, composed: true
        }));
      });
      label.appendChild(input);
      root.appendChild(label);
    };
    const heading = document.createElement("p");
    heading.textContent = "Download websites for registered utilities";
    root.appendChild(heading);
    const websites = document.createElement("div");
    root.appendChild(websites);
    const note = document.createElement("p");
    note.textContent = "Loading registered utility companies...";
    root.appendChild(note);
    const loadUtilities = async () => {
      if (!this._hass) {
        note.textContent = "Connect to Home Assistant to configure " +
          "utility download websites.";
        return;
      }
      try {
        const response = await this._hass.callApi(
          "GET", "energy-usage/utility-upload"
        );
        const utilities = new Map();
        for (const source of response.sources || []) {
          const id = Number(source.data_custodian_id);
          const name = source.utility_company;
          if (!Number.isSafeInteger(id) || id <= 0 ||
              typeof name !== "string" || !name.trim()) {
            throw new Error("Invalid registered utility company");
          }
          if (utilities.has(id) && utilities.get(id) !== name) {
            throw new Error("Conflicting utility company names");
          }
          utilities.set(id, name);
        }
        websites.replaceChildren();
        for (const [id, name] of utilities) {
          const label = document.createElement("label");
          label.textContent = `${name} download website (HTTPS)`;
          const input = document.createElement("input");
          input.type = "url";
          input.placeholder = "https://utility.example/";
          input.value = (this._config.utility_websites || {})[id] ||
            (utilities.size === 1 ? this._config.utility_url || "" : "");
          input.addEventListener("change", () => {
            const value = input.value.trim();
            if (value) {
              try {
                const url = new URL(value);
                if (url.protocol !== "https:" || !url.hostname ||
                    url.username || url.password) throw new Error();
              } catch (_) {
                input.setCustomValidity("Enter a valid HTTPS website URL");
                input.reportValidity();
                return;
              }
            }
            input.setCustomValidity("");
            const next = {...this._config};
            const updated = {...(next.utility_websites || {})};
            if (value) updated[id] = value;
            else delete updated[id];
            next.utility_websites = updated;
            // Migrate the legacy single-utility setting automatically.
            delete next.utility_url;
            this._config = next;
            this.dispatchEvent(new CustomEvent("config-changed", {
              detail: {config: {...next}}, bubbles: true, composed: true
            }));
          });
          label.appendChild(input);
          websites.appendChild(label);
        }
        note.textContent = utilities.size ?
          "Save each utility's website here. Only administrators " +
          "can import XML files." :
          "No registered utility companies found in Energy Ingest.";
      } catch (_) {
        note.textContent = "Cannot load utility companies. Check the " +
          "Energy Usage connection and administrator permissions.";
      }
    };
    void loadUtilities();
  }
}

customElements.define("energy-usage-utility-card-editor",
  EnergyUsageUtilityCardEditor);
customElements.define("energy-usage-utility-card", EnergyUsageUtilityCard);
