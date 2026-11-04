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
      .association-warning {
        border: 2px solid var(--warning-color, #e6a23c);
        border-radius: 8px;
        padding: 12px;
        margin: 16px 0;
        background: var(--card-background-color);
      }
      .association-warning strong {
        display: block;
        margin-bottom: 8px;
      }
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
      const raw = sites[utilityId] || "";
      let url;
      try {
        url = new URL(raw);
        if (!["http:", "https:"].includes(url.protocol) ||
            !url.hostname || url.username || url.password) {
          throw new Error("Invalid utility website URL");
        }
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
        const remembered = response.pending_resources || [];
        if (!Array.isArray(remembered)) {
          throw new Error("Invalid pending resource state");
        }
        for (const state of remembered) addResource(state);
        if (remembered.length) {
          status.textContent =
            `${response.pending_count || remembered.length}` +
            " imported resource(s) " +
            "await association review or Recorder verification. " +
            "Resume below; the XML files need not be uploaded again.";
          renderMappings();
          if (pendingResources.some(item => item.confirmed)) {
            void submitMappings(true);
          }
        }
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
    instructions.textContent = "Choose XML files or a folder, review " +
      "your selections, and import. Existing physical meter associations " +
      "are reused automatically. Select a physical meter only when " +
      "an association needs confirmation.";
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
    clear.textContent = "Clear files";
    controls.append(selectAll, clear);
    article.appendChild(controls);
    selectAll.disabled = true;
    clear.disabled = true;
    const list = document.createElement("ul");
    list.setAttribute("aria-label", "Discovered XML files");
    article.appendChild(list);
    const retry = document.createElement("button");
    retry.textContent = "Retry association and Recorder synchronization";
    retry.disabled = true;
    retry.hidden = true;
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
    const associationWarning = document.createElement("div");
    associationWarning.className = "association-warning";
    associationWarning.setAttribute("role", "alert");
    associationWarning.hidden = true;

    const warningTitle = document.createElement("strong");
    warningTitle.textContent =
      "Action required — Confirm physical meters";

    const warningMessage = document.createElement("p");
    warningMessage.textContent =
      "Your XML files were imported successfully, but some usage " +
      "readings have not yet been added to Home Assistant history. " +
      "Select the correct physical meter for each item below, then " +
      "click Confirm meters and finish.";

    associationWarning.append(warningTitle, warningMessage);
    article.appendChild(associationWarning);
    const mappingList = document.createElement("div");
    mappingList.style.maxHeight = "320px";
    mappingList.style.overflowY = "auto";
    article.appendChild(mappingList);
    const moreMappings = document.createElement("button");
    moreMappings.textContent = "Show more resources";
    moreMappings.hidden = true;
    article.appendChild(moreMappings);
    const confirm = document.createElement("button");
    confirm.textContent = "Confirm meters and finish";
    confirm.hidden = true;
    confirm.disabled = true;
    article.appendChild(confirm);
    const importDetails = document.createElement("pre");
    importDetails.setAttribute("aria-label", "XML import results");
    importDetails.hidden = true;
    article.appendChild(importDetails);
    const status = document.createElement("pre");
    status.setAttribute("role", "status");
    status.setAttribute("aria-live", "polite");
    status.textContent = "Select files or a folder to review XML documents.";
    article.appendChild(status);

    let candidates = [];
    let busy = false;
    let pendingResources = [];
    const autoAttempted = new Set();
    const verifiedMeters = new Map();
    let completedOutcomes = [];
    const configuredLimit = Number(this.config.resource_display_limit);
    const pageSize = Number.isSafeInteger(configuredLimit) &&
      configuredLimit >= 10 && configuredLimit <= 500 ?
      configuredLimit : 50;
    let visibleCount = pageSize;
    moreMappings.addEventListener("click", () => {
      visibleCount += pageSize;
      renderMappings();
    });
    const addResource = state => {
      if (!state || !Number.isSafeInteger(state.resource_id) ||
          state.resource_id <= 0) {
        throw new Error("Invalid imported resource identity");
      }
      const meter = state.physical_meter_id;
      const commodity = state.commodity;
      if (!Number.isSafeInteger(commodity) ||
          ![1, 7].includes(commodity)) {
        throw new Error("Resource commodity unavailable; update Energy " +
          "Ingest before confirming physical meters");
      }
      if (meter !== null && meter !== undefined &&
          (!Number.isSafeInteger(meter) || meter <= 0)) {
        throw new Error("Invalid confirmed physical meter");
      }
      if (meter && !availableMeters.some(item =>
        item.id === meter && Number(item.commodity) === commodity)) {
        throw new Error("Confirmed meter has incompatible commodity");
      }
      const found = pendingResources.find(
        item => item.resourceId === state.resource_id
      );
      if (found) {
        if (found.commodity !== commodity) {
          throw new Error("Conflicting resource commodity");
        }
        if (meter && found.meterId && found.meterId !== meter) {
          throw new Error("Conflicting physical meter association");
        }
        if (meter) found.meterId = meter;
        found.confirmed = Boolean(meter);
      } else {
        pendingResources.push({
          resourceId: state.resource_id,
          commodity,
          meterId: meter || null,
          confirmed: Boolean(meter),
        });
      }
    };
    const selected = () => candidates.filter(item => item.checked);
    const update = () => {
      button.disabled = busy || sourceSelect.disabled ||
        selected().length === 0;
      sourceSelect.disabled = busy || !sourceSelect.options.length;
      download.setAttribute("aria-disabled", String(busy));
      retry.disabled = busy || !retry.dataset.available ||
        !pendingResources.some(item => item.meterId);
      retry.hidden = !retry.dataset.available;
      const unresolved = pendingResources.filter(item => !item.confirmed);
      confirm.disabled = busy || !unresolved.length ||
        unresolved.some(item => !item.meterId);
      selectAll.disabled = busy || candidates.length === 0 ||
        selected().length === candidates.length;
      clear.disabled = busy || candidates.length === 0;
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
    clear.addEventListener("click", () => {
      candidates = [];
      completedOutcomes = [];
      list.replaceChildren();
      filesPicker.value = "";
      folderPicker.value = "";
      importDetails.replaceChildren();
      importDetails.hidden = true;
      status.textContent = "No XML files selected.";
      update();
    });

    const meterName = meter => {
      return meter.display_name || meter.name ||
        (Number(meter.commodity) === 1 ? "Electricity" : "Natural gas");
    };

    const renderMappings = () => {
      mappingList.replaceChildren();

      const needsConfirmation =
        pendingResources.some(item => !item.confirmed);

      mappingHeading.hidden = !needsConfirmation;
      associationWarning.hidden = !needsConfirmation;
      confirm.hidden = !needsConfirmation;

      moreMappings.hidden = pendingResources.length <= visibleCount;
      moreMappings.disabled = busy;
      for (const item of pendingResources.slice(0, visibleCount)) {
        const label = document.createElement("label");
        const commodityName = item.commodity === 1 ?
          "Electricity usage" : "Natural gas usage";
        label.textContent = `${commodityName} — ` +
          (item.confirmed ? "confirmed physical meter" :
            "select physical meter");
        label.title = `Reading resource ${item.resourceId}`;
        const select = document.createElement("select");
        select.setAttribute(
          "aria-label",
          `Physical meter for reading resource ${item.resourceId}`
        );
        const placeholder = document.createElement("option");
        placeholder.value = "";
        placeholder.textContent = "Select physical meter";
        select.appendChild(placeholder);
        const compatibleMeters = availableMeters.filter(
          meter => Number(meter.commodity) === item.commodity
        );
        for (const meter of compatibleMeters) {
          const option = document.createElement("option");
          option.value = String(meter.id);
          option.textContent = meterName(meter);
          select.appendChild(option);
        }
        select.value = item.meterId ? String(item.meterId) : "";
        select.addEventListener("change", () => {
          item.meterId = Number(select.value) || null;
          update();
        });
        select.disabled = busy || item.confirmed;
        label.appendChild(select);
        mappingList.appendChild(label);
      }
      update();
    };
    const submitMappings = async (automatic = false, retrying = false) => {
      if (!this._hass || busy) return;
      const eligible = pendingResources.filter(item =>
        item.meterId && (!automatic || item.confirmed &&
          !autoAttempted.has(item.resourceId))
      );
      if (!automatic && !retrying &&
          pendingResources.some(item => !item.meterId)) return;
      const batch = eligible.slice(0, 128);
      if (!batch.length) return;
      if (automatic) {
        for (const item of batch) autoAttempted.add(item.resourceId);
      }
      busy = true;
      status.textContent = "Synchronizing Home Assistant Recorder…";
      update();
      let success = false;
      try {
        const result = await this._hass.callApi(
          "POST", "energy-usage/utility-upload", {
            associations: batch.map(item => ({
              resource_id: item.resourceId, meter_id: item.meterId,
            })),
          }
        );
        if (!result.synchronized) {
          throw new Error(result.error || "Synchronization not confirmed");
        }
        if (!Array.isArray(result.meter_ids)) {
          throw new Error("Invalid Recorder verification response");
        }
        for (const id of result.meter_ids) {
          const meter = availableMeters.find(item => item.id === id);
          if (!meter) {
            throw new Error("Unknown verified physical meter");
          }
          verifiedMeters.set(id, meterName(meter));
        }
        const names = [...verifiedMeters.values()].join(", ");
        status.textContent = "Synchronization completed successfully. " +
          "Recorder verified for: " + names;
        if (completedOutcomes.length) {
          importDetails.textContent = formatImportSummary(
            completedOutcomes, true
          );
        }
        success = true;
        const completed = new Set(batch.map(item => item.resourceId));
        pendingResources = pendingResources.filter(
          item => !completed.has(item.resourceId)
        );
        delete retry.dataset.available;
        if (pendingResources.length) {
          status.textContent += "\nMore resources remain to synchronize.";
        }
      } catch (error) {
        status.textContent = "Association or Recorder verification " +
          "is incomplete. Review the physical meters and retry: " +
          utilityErrorMessage(error);
        retry.dataset.available = "1";
      } finally {
        busy = false;
        renderMappings();
        if (success && pendingResources.some(item =>
          item.confirmed && !autoAttempted.has(item.resourceId))) {
          void submitMappings(true);
        }
      }
    };
    confirm.addEventListener("click", () => void submitMappings(false));
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
      completedOutcomes = [];
      verifiedMeters.clear();
      importDetails.hidden = true;
      importDetails.replaceChildren();
      // Keep accepted resources pending when another file is imported.
      renderMappings();
      update();
      const outcomes = [];
      let startAuto = false;
      let activeFile = null;
      try {
        for (let i = 0; i < queue.length; i++) {
          const file = queue[i].file;
          activeFile = file.name;
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
          const associations = result.associations;
          if (!Array.isArray(associations) ||
              associations.length !== ids.length) {
            throw new Error("Association lookup is incomplete");
          }
          for (const state of associations) addResource(state);
        }
        activeFile = null;
        completedOutcomes = outcomes;
        importDetails.textContent = formatImportSummary(outcomes, false);
        importDetails.hidden = false;

        const requiresConfirmation =
          pendingResources.some(item => !item.confirmed);

        status.textContent = requiresConfirmation ?
          "Import accepted. Action required: confirm the physical " +
          "meters above to finish saving usage to Home Assistant." :
          "Import accepted. Synchronizing Home Assistant history.";

        renderMappings();
        if (pendingResources.some(item => item.confirmed)) {
          // The import batch is complete; synchronize confirmed meters.
          // Unresolved resources remain visible for explicit selection.
          startAuto = true;
        }

      } catch (error) {
          if (pendingResources.length) renderMappings();
          if (outcomes.length) {
            importDetails.textContent = formatImportSummary(outcomes, false);
            importDetails.hidden = false;
          }
          const context = activeFile ?
            `Could not finish importing ${activeFile}: ` :
            "Import processing failed: ";
          status.textContent = context + utilityErrorMessage(error);
      } finally {

        busy = false;
        renderMappings();
        if (startAuto) void submitMappings(true);
      }
    });
    retry.addEventListener("click", () => void submitMappings(false, true));
    // Fetch only after the card has Home Assistant's authenticated client.
    this.loadSources = loadSources;
    card.appendChild(article);
    root.appendChild(card);
  }
}

// Give the user one plain-English result for each selected XML file.
function formatImportSummary(outcomes, synchronized) {
  const lines = ["Results for each XML file:"];
  let previouslyImported = 0;
  let changed = 0;
  let unchanged = 0;
  let empty = 0;

  for (const outcome of outcomes) {
    const imported = (outcome.result || {}).import || {};

    for (const key of ["observations", "unchanged", "accepted"]) {
      if (!Number.isSafeInteger(imported[key]) || imported[key] < 0) {
        throw new Error("Invalid import statistics from Energy Ingest");
      }
    }

    if (!Array.isArray(imported.resource_ids) ||
        imported.resource_ids.some(id =>
          !Number.isSafeInteger(id) || id <= 0)) {
      throw new Error("Invalid imported resource identities");
    }

    if (typeof imported.already_imported !== "boolean") {
      throw new Error(
        "Energy Ingest does not report file import status; " +
        "update the backend before importing XML"
      );
    }

    if (imported.already_imported && imported.accepted !== 0) {
      throw new Error("Conflicting import status from Energy Ingest");
    }

    let message;

    if (imported.already_imported) {
      previouslyImported += 1;
      message = "Already imported — no changes needed.";
    } else if (imported.accepted > 0) {
      changed += 1;
      message = `${imported.accepted} usage reading(s) added or updated.`;
    } else if (imported.observations > 0) {
      unchanged += 1;
      message = "No changes needed — usage data is up to date.";
    } else {
      empty += 1;
      message = "No usage readings were processed from this file.";
    }

    lines.push(`File: ${outcome.file}`);
    lines.push(`Result: ${message}`);
    lines.push("");
  }

  lines.push(`XML files processed: ${outcomes.length}`);
  lines.push(`Already imported: ${previouslyImported}`);
  lines.push(`Files with added or updated data: ${changed}`);
  lines.push(`Files already up to date: ${unchanged}`);
  lines.push(`Files with no readings processed: ${empty}`);
  lines.push(
    "Home Assistant history: " +
    (synchronized ? "Synchronized" : "Not yet verified")
  );

  return lines.join("\n").trimEnd();
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
        input.setCustomValidity("");
        if (key === "source_id" && value &&
            (!Number.isSafeInteger(Number(value)) || Number(value) <= 0)) {
          input.setCustomValidity("Enter a positive source ID");
          input.reportValidity();
          return;
        }
        if (key === "resource_display_limit" && value &&
            (!Number.isSafeInteger(Number(value)) ||
              Number(value) < 10 || Number(value) > 500)) {
          input.setCustomValidity("Enter a number from 10 to 500");
          input.reportValidity();
          return;
        }
        if (value) next[key] = ["source_id", "resource_display_limit"]
          .includes(key) ? Number(value) : value;
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
    field("Resources shown per page (10–500)",
      "resource_display_limit", "50", "number");
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
          label.textContent = `${name} download website (HTTP or HTTPS)`;
          const input = document.createElement("input");
          input.type = "url";
          input.placeholder = "http://utility.example/";
          input.value = (this._config.utility_websites || {})[id] || "";
          input.addEventListener("change", () => {
            const value = input.value.trim();
            if (value) {
              try {
                const url = new URL(value);
                if (!["http:", "https:"].includes(url.protocol) ||
                    !url.hostname ||
                    url.username || url.password) throw new Error();
              } catch (_) {
                input.setCustomValidity(
                  "Enter a valid HTTP or HTTPS website URL"
                );
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
