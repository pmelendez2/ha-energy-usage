// SPDX-License-Identifier: MIT
// Copyright (c) 2026 Project Contributors
// Exercise actual dashboard summary logic without a Home Assistant browser.
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

const file = path.join(__dirname, "../custom_components/energy_usage/www",
  "energy-usage-utility-card.js");
const source = fs.readFileSync(file, "utf8");
const context = vm.createContext({
  HTMLElement: class {},
  customElements: {define() {}},
});
vm.runInContext(source, context, {filename: file});
const summary = vm.runInContext("formatImportSummary", context);

const result = (
  ids,
  observations,
  unchanged,
  accepted,
  alreadyImported = false
) => ({
  import: {
    resource_ids: ids,
    observations,
    unchanged,
    accepted,
    already_imported: alreadyImported,
  },
});

const files = [
  {
    file: "new-electric.xml",
    result: result([5], 20, 8, 12),
  },
  {
    file: "existing-gas.xml",
    result: result([6], 0, 0, 0, true),
  },
  {
    file: "unchanged-electric.xml",
    result: result([7], 20, 20, 0),
  },
  {
    file: "empty.xml",
    result: result([8], 0, 0, 0),
  },
];

const text = summary(files, true);

assert.match(text, /File: new-electric.xml/);
assert.match(text, /12 usage reading\(s\) added or updated/);

assert.match(text, /File: existing-gas.xml/);
assert.match(text, /Already imported — no changes needed/);

assert.match(text, /File: unchanged-electric.xml/);
assert.match(text, /usage data is up to date/);

assert.match(text, /File: empty.xml/);
assert.match(text, /No usage readings were processed/);

assert.match(text, /XML files processed: 4/);
assert.match(text, /Already imported: 1/);
assert.match(text, /Files with added or updated data: 1/);
assert.match(text, /Files already up to date: 1/);
assert.match(text, /Files with no readings processed: 1/);
assert.match(text, /Home Assistant history: Synchronized/);

assert.match(
  summary(files, false),
  /Home Assistant history: Not yet verified/
);

assert.throws(
  () => summary([
    {
      file: "invalid.xml",
      result: result([0], 0, 0, 0),
    },
  ], false),
  /Invalid imported resource identities/
);

assert.throws(
  () => summary([
    {
      file: "old-backend.xml",
      result: {
        import: {
          resource_ids: [5],
          observations: 0,
          unchanged: 0,
          accepted: 0,
        },
      },
    },
  ], false),
  /does not report file import status/
);

assert.throws(
  () => summary([
    {
      file: "conflicting.xml",
      result: result([5], 1, 0, 1, true),
    },
  ], false),
  /Conflicting import status/
);

console.log("Utility import summary: PASS");
