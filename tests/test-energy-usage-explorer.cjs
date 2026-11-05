// SPDX-License-Identifier: MIT
const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const path = require('node:path');
const source = fs.readFileSync(
  path.join(
    __dirname,
    '..',
    'custom_components',
    'energy_usage',
    'www',
    'energy-usage-explorer.js'
  ),
  'utf8'
);
const context = {
  HTMLElement: class {},
  customElements: { get: () => true },
  window: { customCards: [] },
  Intl, Date, Map, Set, Math, Number, String,
};
vm.createContext(context);
vm.runInContext(source, context);
const f = (expr) => vm.runInContext(expr, context);
assert.equal(f('dateValid("2026-02-30")'), false);
assert.equal(f('datePlusOne("2026-02-28")'), '2026-03-01');
const entries = [
  {start:Date.parse('2026-03-08T07:59:00Z'),change:2},
  {start:Date.parse('2026-03-09T06:59:00Z'),change:3},
  {start:Date.parse('2026-03-11T06:59:00Z'),change:5},
];
context.sample = entries;
const srcGas='SOURCE_TYPES[1]', srcElectric='SOURCE_TYPES[0]';
let result = f(`bucketize(sample,"America/Los_Angeles", "2026-03-07", "2026-03-11", "month", "average", ${srcGas})`);
assert.equal(result.length, 1);
assert.equal(result[0].value, 10/3);
assert.equal(result[0].count, 3);
result = f(`bucketize(sample,"America/Los_Angeles", "2026-03-07", "2026-03-11", "day", "total", ${srcGas})`);
assert.equal(result.length, 3); // Missing dates remain absent.
assert.equal(result[0].key, '2026-03-07');
assert.equal(result[1].key, '2026-03-08');
assert.equal(f(`bucketize(sample,"America/Los_Angeles", "2026-03-07", "2026-03-11", "hour", "total", ${srcGas})`), null);
context.sample = [
  {start:Date.parse('2026-11-01T08:00:00Z'),change:2},
  {start:Date.parse('2026-11-01T09:00:00Z'),change:3},
];
result = f(`bucketize(sample,"America/Los_Angeles", "2026-11-01", "2026-11-01", "hour", "total", ${srcElectric})`);
assert.equal(result.length,2); // DST repeated local hour remains distinct.
assert.notEqual(result[0].key,result[1].key);
assert.equal(f('niceStep(859.615)'), 250);
assert.equal(f('axisScale([{value:859.615}]).ceiling'), 1000);
assert.equal(f('consecutive("2026-02", "2026-03", "month")'), true);
assert.equal(f('consecutive("2026-12", "2027-01", "month")'), true);
assert.equal(f('consecutive("2026-03-07", "2026-03-09", "day")'), false);
assert.equal(f('consecutive("2026-03-07", "2026-03-08", "day")'), true);
console.log('Dashboard logic: 13 checks PASS');
assert.equal(f('calendarDays("2026-10-01", "2026-10-06")'), 6);
assert.equal(f('calendarDays("2026-10-01", "2026-11-01")'), 32);
assert.equal(f('calendarDays("2026-10-01", "2026-11-02")'), 33);
assert.equal(f('validSelection("2026-10-01", "2026-10-06", "hour")'), null);
assert.equal(f('validSelection("2026-10-01", "2026-11-01", "hour")'), null);
assert.match(f('validSelection("2026-10-01", "2026-11-02", "hour")'), /32/);
assert.equal(f('validSelection("2026-10-06", "2026-10-01", "day")') !== null,true);
assert.equal(f('validSelection("2026-02-30", "2026-03-01", "day")') !== null,true);
context.observations = {
  'energy_usage:electricity_meter_1': [
    {start:Date.parse('2026-10-08T12:00:00Z'), change: 0},
    {start:Date.parse('2026-10-09T12:00:00Z'), change: 1},
    {start:Date.parse('2026-10-10T12:00:00Z'), change: null},
  ],
  'energy_usage:gas_meter_2': [
    {start:Date.parse('2026-10-07T12:00:00Z'), change: 1},
  ],
};
assert.equal(f('newestObservation(observations, "America/Los_Angeles", [{id:"energy_usage:electricity_meter_1"},{id:"energy_usage:gas_meter_2"}])'), '2026-10-09');
assert.equal(f('newestObservation({}, "America/Los_Angeles", [])'), null);
console.log('Explorer update: 10 additional checks PASS');
assert.equal(f('shortTick("2026-10", "month")'), "Oct '26");
assert.equal(f('shortTick("2026-10-05", "day")'), 'Oct 05');
assert.equal(f('shortTick("2026-10-05 21:00 GMT-7", "hour")'), '21:00');
assert.equal(f('calculationLabel("total", "day", SOURCE_TYPES[0])'),
  'Total consumption per day');
assert.equal(f('calculationLabel("average", "month", SOURCE_TYPES[1])'),
  'Average consumption per observed day');
assert.equal(f('calculationLabel("average", "day", SOURCE_TYPES[0])'),
  'Average consumption per observed hour');
assert.equal(f('calculationLabel("average", "day", SOURCE_TYPES[1])'),
  'Observed daily consumption');
console.log('Axis labels and calculation explanations: 7 checks PASS');

// V5/V6: inspectable points, date navigation and coverage provenance.
assert.equal(f('formatPeriod("2026-10-01 21:00 GMT-7", "hour")'),
  '2026-10-01 21:00 (GMT-7)');
context.sample = [
  {start:Date.parse('2026-10-01T07:00:00Z'),change:1.25},
  {start:Date.parse('2026-10-01T08:00:00Z'),change:0.75},
];
result = f(`bucketize(sample,"America/Los_Angeles",
  "2026-10-01", "2026-10-01", "day", "average", ${srcElectric})`);
assert.equal(result[0].total,2);
assert.equal(result[0].denominator,2);
assert.equal(result[0].value,1);
assert.equal(result[0].count,2);
assert.equal(result[0].coverage,'2 observed hours');
assert.match(f('calculationLabel("total", "hour", SOURCE_TYPES[1])'),
  /No hourly gas/);
assert.match(source, /chartSvg.addEventListener\("click",event =>/);
assert.match(source, /chartSvg.addEventListener\("keydown",event =>/);
assert.match(source, /Jump to day \(hourly\)/);
assert.match(source, /Visible:/);
assert.match(source, /shortTick\(datum.key.slice\(0,10\), "day"\)/);
console.log('Clickable details and hourly navigation: 10 checks PASS');

// V7: click selection survives charts, details remain visible above scroll.
assert.match(source, /"data-point-index":i/);
assert.match(source, /selectIndex\(Number\(point.getAttribute/);
assert.match(source, /event.stopPropagation\(\)/);
assert.match(source, /section.append\(detail\);\s*const view=/);
assert.match(source, /\.detail\[hidden\] \{ display:none; \}/);
console.log('Delegated selection and visible details: 5 checks PASS');

// V8: selected point must remain after an SVG redraw caused by resize.
assert.match(source, /target\._selectedIndex = index/);
assert.match(source, /selectIndex\(target\._selectedIndex\)/);
assert.match(source, /width !== this\._lastChartWidth/);
assert.match(source, /delete view\._selectedIndex/);
assert.match(source, /rect\.addEventListener\("click"/);
assert.match(source, /dot\.addEventListener\("click"/);
console.log('Persistent selection and direct SVG clicks: 6 checks PASS');

// Reviewer regression: arbitrary meter IDs, missing commodities, and dates.
assert.equal(f('discoveredSources([{statistic_id:"energy_usage:electricity_meter_37"}]).length'),1);
assert.equal(f('discoveredSources([{statistic_id:"energy_usage:gas_meter_8"}])[0].id'),"energy_usage:gas_meter_8");
assert.equal(f('discoveredSources([{statistic_id:"other:gas_meter_2"}]).length'),0);
assert.equal(f('discoveredSources([{statistic_id:"energy_usage:gas_meter_8"},{statistic_id:"energy_usage:gas_meter_9"}]).length'),2);
assert.equal(f('configuredSources({gas_statistic:"energy_usage:gas_meter_9"}).length'),1);
assert.equal(f('initialDates(new Date("2026-11-04T12:00:00Z"),"UTC").end'),"2026-11-04");
assert.equal(f('initialDates(new Date("2026-11-04T12:00:00Z"),"UTC").start'),"2026-10-06");
console.log('HACS Explorer portability: 7 checks PASS');

// Recorder expects the measurement type, not the statistics source.
assert.match(source, /type:"recorder\/list_statistic_ids", statistic_type:"sum"/);
assert.doesNotMatch(source, /statistic_type:"external"/);
console.log("Recorder statistic discovery contract: 2 checks PASS");

// Latest actual observation updates both navigation controls.
const latestMethod = source.slice(source.indexOf('  async _useLatest() {'),
  source.indexOf('  async _resolveSources() {'));
assert.match(latestMethod, /this\._endInput\.value=latest;/);
assert.match(latestMethod, /this\._dayInput\.value=latest;/);
assert.match(latestMethod, /End date and hourly jump date updated/);
console.log('Latest-date navigation consistency: 3 checks PASS');
