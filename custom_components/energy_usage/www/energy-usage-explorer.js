/* SPDX-License-Identifier: MIT */
/* Copyright (c) 2026 Project Contributors */
/* Energy Usage Explorer: read-only Home Assistant Lovelace card. */

const NS = "http://www.w3.org/2000/svg";
// Initial locale catalog. Future locales may extend this mapping without
// changing chart calculations or the underlying usage observations.
const EXPLORER_LABELS = Object.freeze({
  "Energy Usage Explorer": "Energy Usage Explorer",
  "Start date": "Start date",
  "End date": "End date",
  "Group by": "Group by",
  "Graph": "Graph",
  "Calculation": "Calculation",
  "Apply": "Apply",
  "Use latest available": "Use latest available",
  "Jump to day (hourly)": "Jump to day (hourly)",
  "Show day": "Show day",
});
function explorerLabel(key) {
  return EXPLORER_LABELS[key] ?? key;
}

const SOURCES = [
  { id: "energy_usage:electricity_meter_1", name: "Electricity", unit: "kWh", granularity: "hour" },
  { id: "energy_usage:gas_meter_2", name: "Natural Gas", unit: "therm", granularity: "day" },
];
const css = `
:host { display:block; font-family:var(--primary-font-family, sans-serif); }
.wrapper { padding:18px; }
.controls { display:flex; flex-wrap:wrap; align-items:end; gap:12px; margin-bottom:16px; }
.field { display:flex; flex-direction:column; gap:4px; font-size:13px; }
.field input,.field select { font:inherit; padding:8px; border:1px solid var(--divider-color,#aaa);
  border-radius:7px; background:var(--card-background-color,#fff); color:var(--primary-text-color,#222); }
.action { padding:9px 16px; color:var(--primary-text-color,#222); background:var(--secondary-background-color,#eee);
  border:1px solid var(--divider-color,#aaa); border-radius:7px; cursor:pointer; }
.action:disabled { opacity:.5; cursor:default; }
.availability { font-size:13px; margin:6px 0; color:var(--secondary-text-color,#666); }
.pending { color:var(--warning-color,#a65f00); }
.status { min-height:1.4em; font-size:13px; color:var(--secondary-text-color,#666); }
.error { color:var(--error-color,#b22); }
.graph { margin-top:20px; }
.graph h3 { margin:5px 0 2px; font-size:18px; }
.graph .note { font-size:12px; color:var(--secondary-text-color,#666); margin-bottom:10px; }
.viewport { overflow-x:auto; max-width:100%; }
svg { display:block; color:var(--primary-text-color,#222); }
.axis { stroke:var(--primary-text-color,#333); stroke-width:1; }
.gridline { stroke:var(--divider-color,#bbb); stroke-opacity:.6; stroke-width:1; }
.tick { fill:var(--secondary-text-color,#666); font-size:11px; }
.plot { fill:var(--primary-color,#447adc); stroke:var(--primary-color,#447adc); }
.detail[hidden] { display:none; }
.detail { padding:12px; margin-top:10px; border:1px solid var(--divider-color,#bbb); border-radius:8px; background:var(--secondary-background-color,#f5f5f5); font-size:13px; }
.detail h4 {margin:0 0 8px;}
.detail dl {display:grid;grid-template-columns:max-content 1fr; gap:6px 14px;margin:0;}
.detail dt {font-weight:600;}
.detail dd {margin:0;}
.data-point { cursor:pointer; pointer-events:all; }
.data-point:hover { opacity:1; stroke-width:2; }
.data-point:focus {outline:2px solid var(--primary-color,#447adc);outline-offset:2px;}
.range-indicator {font-size:12px;color:var(--secondary-text-color,#666);margin-bottom:6px;}
.daylabel {fill:var(--primary-text-color,#222);font-size:12px;font-weight:600;}
.missing { color:var(--secondary-text-color,#666); font-size:13px; padding:30px 8px; }
`;

function el(tag, text, attrs = {}) {
  const node = document.createElement(tag);
  if (text !== null) node.textContent = text;
  for (const [key, value] of Object.entries(attrs)) node.setAttribute(key, value);
  return node;
}
function svg(tag, attrs = {}, text = null) {
  const node = document.createElementNS(NS, tag);
  for (const [key, value] of Object.entries(attrs)) node.setAttribute(key, String(value));
  if (text !== null) node.textContent = text;
  return node;
}
function parts(date, timeZone) {
  const p = Object.fromEntries(new Intl.DateTimeFormat("en-US", {
    timeZone, year:"numeric", month:"2-digit", day:"2-digit", hour:"2-digit",
    hourCycle:"h23", timeZoneName:"shortOffset"
  }).formatToParts(date).map(x => [x.type, x.value]));
  return { day:`${p.year}-${p.month}-${p.day}`, hour:p.hour, offset:p.timeZoneName || "" };
}
function dateValid(value) {
  return /^\d{4}-\d{2}-\d{2}$/.test(value) &&
    !Number.isNaN(Date.parse(value)) &&
    new Date(`${value}T00:00:00Z`).toISOString().slice(0,10) === value;
}
function datePlusOne(value) {
  const d = new Date(`${value}T00:00:00Z`);
  d.setUTCDate(d.getUTCDate() + 1);
  return d.toISOString().slice(0,10);
}
function calendarDays(start, end) {
  return Math.round((Date.parse(`${end}T00:00:00Z`) -
    Date.parse(`${start}T00:00:00Z`)) / 86400000) + 1;
}
function validSelection(start, end, period) {
  if (!dateValid(start) || !dateValid(end) || start > end)
    return "Enter valid start and end dates (start must not exceed end).";
  if (period === "hour" && calendarDays(start, end) > 32)
    return "For hourly charts, select at most 32 calendar days.";
  return null;
}
function newestObservation(response, timeZone) {
  let latest = null;
  for (const source of SOURCES) {
    for (const entry of response[source.id] || []) {
      if (!Number.isFinite(entry.start) ||
          !Number.isFinite(entry.change)) continue;
      const day = parts(new Date(entry.start), timeZone).day;
      if (latest === null || day > latest) latest = day;
    }
  }
  return latest;
}
function monthOf(day) { return day.slice(0,7); }
function bucketize(entries, timeZone, start, end, period, metric, source) {
  if (period === "hour" && source.granularity === "day") return null;
  const map = new Map();
  for (const reading of entries) {
    if (typeof reading.change !== "number" || !Number.isFinite(reading.change)) continue;
    if (!Number.isFinite(reading.start)) continue;
    const t = parts(new Date(reading.start), timeZone);
    if (t.day < start || t.day > end) continue;
    const groupKey = period === "month" ? monthOf(t.day) :
      period === "day" ? t.day : `${t.day} ${t.hour}:00 ${t.offset}`;
    if (!map.has(groupKey)) map.set(groupKey, {
      key:groupKey, total:0, count:0, observedDays:new Set(), hours:new Set()
    });
    const b = map.get(groupKey);
    b.total += reading.change;
    b.count += 1;
    b.observedDays.add(t.day);
    b.hours.add(`${t.day} ${t.hour} ${t.offset}`);
  }
  return [...map.values()].sort((a,b) => a.key.localeCompare(b.key)).map(b => {
    const denominator = metric === "total" ? 1 :
      period === "month" ? b.observedDays.size :
      period === "day" && source.granularity === "hour" ? b.hours.size : b.count;
    return { key:b.key, value:b.total / denominator, total:b.total,
      denominator, count:b.count,
      coverage:source.granularity === "hour" ? `${b.hours.size} observed hours` :
        `${b.observedDays.size} observed days` };
  });
}
function niceStep(maximum, divisions = 4) {
  if (maximum <= 0) return 1;
  const rough = maximum / divisions;
  const scale = 10 ** Math.floor(Math.log10(rough));
  const normalized = rough / scale;
  const step = [1, 2, 2.5, 5, 10].find(x => x >= normalized) || 10;
  return step * scale;
}
function axisScale(series) {
  const peak = Math.max(0, ...series.map(x => x.value));
  const step = niceStep(peak);
  return { step, ceiling: Math.max(step, Math.ceil(peak / step) * step) };
}
function consecutive(a, b, period) {
  if (period === "month") {
    const [y, m] = a.slice(0,7).split("-").map(Number);
    const next = new Date(Date.UTC(y,m,1));
    return next.toISOString().slice(0,7) === b.slice(0,7);
  }
  if (period === "day") return datePlusOne(a.slice(0,10)) === b.slice(0,10);
  // Local hour labels include their UTC offsets; do not connect across
  // ambiguous DST boundaries or unobserved hours.
  return false;
}
function shortTick(key, period) {
  if (period === "month") {
    const [year, month] = key.split("-").map(Number);
    return `${new Date(Date.UTC(year, month - 1, 1)).toLocaleString(
      "en-US", {month:"short", timeZone:"UTC"})} '${String(year).slice(-2)}`;
  }
  if (period === "day") {
    const [year, month, day] = key.split("-").map(Number);
    return new Date(Date.UTC(year, month - 1, day)).toLocaleString(
      "en-US", {month:"short", day:"2-digit", timeZone:"UTC"});
  }
  return key.slice(11,16); // Hour, without repeating the date or GMT offset.
}
function calculationLabel(metric, period, source) {
  if (period === "hour" && source.granularity === "day")
    return "No hourly gas consumption observations available";
  if (metric === "total") return `Total consumption per ${period}`;
  if (period === "month") return "Average consumption per observed day";
  if (period === "day" && source.granularity === "hour")
    return "Average consumption per observed hour";
  if (period === "hour") return "Average of actual records per hour";
  return "Observed daily consumption";
}
function formatPeriod(key, period) {
  if (period === "hour") {
    const [day, hour, offset] = key.split(" ");
    return `${day} ${hour} (${offset})`;
  }
  return period === "month" ? `${key} (local month)` : `${key} (local day)`;
}
function formatValue(value) {
  return Number(value.toPrecision(9)).toLocaleString(
    undefined, {maximumFractionDigits:6});
}
function showPointDetails(target, datum, source, period, metric) {
  const panel = target.parentElement.querySelector(".detail");
  if (!panel) return;
  panel.replaceChildren();
  panel.append(el("h4", `${source.name} — selected data point`));
  const definitions = el("dl", null);
  const fields = [
    ["Period", formatPeriod(datum.key, period)],
    [explorerLabel("Calculation"), calculationLabel(metric, period, source)],
    ["Displayed value", `${formatValue(datum.value)} ${source.unit}`],
    ["Recorded total", `${formatValue(datum.total)} ${source.unit}`],
    ["Average divisor", metric === "average" ?
      `${datum.denominator} observed periods` : "Not applicable"],
    ["Recorded observations", String(datum.count)],
    ["Observed coverage", datum.coverage],
    ["Source", "Home Assistant Recorder statistics"],
  ];
  fields.forEach(([name,value]) => {
    definitions.append(el("dt",name), el("dd",value));
  });
  panel.append(definitions);
  panel.hidden=false;
  panel.setAttribute("aria-live", "polite");
}
function visibleRange(target, series, left, right, width, period) {
  const indicator=target.parentElement.querySelector(".range-indicator");
  if (!indicator || !series?.length) return;
  const plotW=width-left-right;
  const scroll=target.scrollLeft;
  const view=Math.max(1,target.clientWidth);
  const begin=Math.min(series.length-1,Math.max(0,
    Math.floor((scroll-left)/plotW*series.length)));
  const finish=Math.min(series.length-1,
    Math.max(begin,Math.ceil((scroll+view-left)/plotW*series.length)-1));
  indicator.textContent=`Visible: ${formatPeriod(series[begin].key,period)}`+
    ` – ${formatPeriod(series[Math.max(begin,finish)].key,period)}`;
}
function graph(target, series, source, chart, period, metric) {
  target.replaceChildren();
  const unit=source.unit, title=source.name;
  const panel=target.parentElement.querySelector(".detail");
  const indicator=target.parentElement.querySelector(".range-indicator");
  if (panel && target._selectedIndex === undefined) {
    panel.replaceChildren();panel.hidden=true;
  }
  if (indicator) indicator.textContent="";
  if (!series || !series.length) {
    target.append(el("div", series === null ?
      "Hourly natural gas data is unavailable: only actual daily gas readings exist." :
      "No recorded observations in the selected range.", {class:"missing"}));
    return;
  }
  const left = 72, right = 24, top = period === "hour" ? 42 : 18;
  const plotH = 214, bottom = 62;
  const containerWidth = Math.max(300, Math.floor(target.clientWidth || 570));
  const preferredWidth = left + right + series.length *
    (chart === "bar" ? 14 : 10);
  // Fit short views to their container. Scroll only for crowded timelines.
  const width = Math.max(containerWidth, preferredWidth);
  const height = top + plotH + bottom;
  const plotW = width - left - right;
  const {step, ceiling} = axisScale(series);
  const ypos = value => top + (ceiling - value) / ceiling * plotH;
  const xcenter = i => left + (i + .5) * plotW / series.length;
  const chartSvg = svg("svg", {width, height,
    viewBox:`0 0 ${width} ${height}`,role:"img",
    "aria-label":`${title}, ${metric} ${unit} by ${period}`});
  const fmt = value => Number(value.toPrecision(9)).toLocaleString(
    undefined, {maximumFractionDigits:6});
  const ticks = Math.round(ceiling / step);
  for (let i = 0; i <= ticks; i++) {
    const value = step * i, y = ypos(value);
    chartSvg.append(svg("line", {x1:left,y1:y,x2:width-right,y2:y,
      class:"gridline"}));
    chartSvg.append(svg("text", {x:left-8,y:y+4,
      "text-anchor":"end",class:"tick"},fmt(value)));
  }
  chartSvg.append(svg("line", {x1:left,y1:top,x2:left,
    y2:top+plotH,class:"axis"}));
  chartSvg.append(svg("line", {x1:left,y1:top+plotH,
    x2:width-right,y2:top+plotH,class:"axis"}));
  chartSvg.append(svg("text", {x:17,y:top+plotH/2,
    transform:`rotate(-90 17 ${top+plotH/2})`,
    "text-anchor":"middle",class:"tick"},
    `${metric === "average" ? "Average" : "Total"} (${unit})`));
  // Space labels by plot width, not the full data count. No overlap at
  // narrow viewport widths and no duplicate end label.
  const tickCount = Math.max(2, Math.floor(plotW / 78));
  const labelEvery = Math.max(1, Math.ceil(series.length / tickCount));
  const barWidth = Math.max(2, plotW / series.length * .74);
  let segment = [];
  function drawSegment() {
    if (segment.length > 1) chartSvg.append(svg("polyline", {
      points:segment.join(" "),fill:"none",
      stroke:"var(--primary-color,#447adc)","stroke-width":2}));
    segment = [];
  }
  // One delegated handler works for every bar and line point. Prevent
  // dashboard-level handlers from stealing the selection event.
  const selectIndex = (index) => {
    if (!Number.isInteger(index) || index < 0 || index >= series.length)
      return;
    target._selectedIndex = index;
    showPointDetails(target,series[index],source,period,metric);
  };
  chartSvg.addEventListener("click",event => {
    const point = event.target.closest?.("[data-point-index]");
    if (!point) return;
    event.stopPropagation();
    selectIndex(Number(point.getAttribute("data-point-index")));
  });
  chartSvg.addEventListener("keydown",event => {
    if (event.key !== "Enter" && event.key !== " ") return;
    const point = event.target.closest?.("[data-point-index]");
    if (!point) return;
    event.preventDefault();
    event.stopPropagation();
    selectIndex(Number(point.getAttribute("data-point-index")));
  });
  series.forEach((datum,i) => {
    const x = xcenter(i), y = ypos(datum.value);
    const details = `${datum.key}\n${fmt(datum.value)} ${unit}\n`+
      `${datum.coverage}; ${datum.count} actual statistics records`;
    if (chart === "bar") {
      const rect = svg("rect", {x:x-barWidth/2,y,
        width:barWidth,height:Math.max(1,ypos(0)-y),class:"plot data-point",
        tabindex:0,role:"button","aria-label":details,
        "data-point-index":i,opacity:.82});
      rect.addEventListener("click", event => {
        event.stopPropagation();
        selectIndex(i);
      });
      rect.append(svg("title",{},details));
      chartSvg.append(rect);
    } else {
      if (i && !consecutive(series[i-1].key, datum.key, period))
        drawSegment();
      segment.push(`${x},${y}`);
      const dot = svg("circle",{cx:x,cy:y,r:5,
        class:"plot data-point",tabindex:0,role:"button",
        "data-point-index":i,"aria-label":details});
      dot.addEventListener("click", event => {
        event.stopPropagation();
        selectIndex(i);
      });
      dot.append(svg("title",{},details));
      chartSvg.append(dot);
    }
    if (period === "hour" && (i === 0 ||
        datum.key.slice(0,10) !== series[i-1].key.slice(0,10))) {
      chartSvg.append(svg("line",{x1:x-barWidth/2,y1:top,x2:x-barWidth/2,
        y2:top+plotH,"stroke-dasharray":"3 4",class:"gridline"}));
      chartSvg.append(svg("text",{x:x+3,y:top-10,class:"daylabel"},
        shortTick(datum.key.slice(0,10), "day")));
    }
    // A short, horizontal date label for every displayed tick.
    // The last observation remains available through the tooltip.
    if (i % labelEvery === 0) {
      chartSvg.append(svg("text", {x,y:top+plotH+20,
        "text-anchor":"middle",class:"tick"},
        shortTick(datum.key, period)));
    }
  });
  if (chart === "line") drawSegment();
  chartSvg.append(svg("text",{x:left+plotW/2,y:height-3,
    "text-anchor":"middle",class:"tick"},
    period === "hour" ? "Local hour (hover for date and UTC offset)" :
    period === "day" ? "Local date" : "Local month"));
  target.append(chartSvg);
  if (Number.isInteger(target._selectedIndex) &&
      target._selectedIndex < series.length) {
    selectIndex(target._selectedIndex);
  }
  target.onscroll=()=>visibleRange(target,series,left,right,width,period);
  visibleRange(target,series,left,right,width,period);
}

class EnergyUsageExplorer extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({mode:"open"});
    this._cfg={}; this._cache=null; this._hass=null; this._generation=0;
    this._start="2025-09-07"; this._end="2026-10-06";
    this._period="month"; this._chart="bar"; this._metric="total";
    this._renderShell();
    this._lastChartWidth = 0;
    if (typeof ResizeObserver !== "undefined") {
      this._resize = new ResizeObserver(entries => {
        const width = Math.floor(entries[0]?.contentRect?.width || 0);
        if (width && width !== this._lastChartWidth) {
          this._lastChartWidth = width;
          if (this._series) this._redraw();
        }
      });
      this._resize.observe(this);
    }
  }
  disconnectedCallback() {
    if (this._resize) this._resize.disconnect();
  }
  _redraw() {
    if (!this._series) return;
    for (let i=0;i<SOURCES.length;i++) {
      const src=SOURCES[i];
      graph(this._graphs[i],this._series[i],src,
        this._chart,this._period,this._metric);
    }
  }
  setConfig(config) {
    this._cfg=config;
    this._start=config.start_date || this._start;
    this._end=config.end_date || this._end;
    this._renderShell();
    if (this._hass) this._load();
  }
  set hass(hass) {
    const changed = this._hass && this._hass.connection !== hass.connection;
    this._hass=hass;
    if ((changed || !this._cache) && !this._loading) this._load();
  }
  getCardSize() { return 10; }
  static getStubConfig() { return {type:"custom:energy-usage-explorer"}; }
  _renderShell() {
    this.shadowRoot.innerHTML="";
    this.shadowRoot.append(el("style",css));
    const card=el("ha-card",null);
    const root=el("div",null,{class:"wrapper"});
    root.append(el("h2",explorerLabel("Energy Usage Explorer")));
    const controls=el("div",null,{class:"controls"});
    const field=(name,value,type,options) => {
      const holder=el("label",null,{class:"field"});
      holder.append(el("span",name));
      const input=el(options?"select":"input",null,options?{}:{type,value});
      if (options) options.forEach(([v,label]) => {
        const opt=el("option",label,{value:v});
        if (v===value) opt.selected=true;
        input.append(opt);
      });
      holder.append(input); controls.append(holder);
      return input;
    };
    this._startInput=field(explorerLabel("Start date"),this._start,"date");
    this._endInput=field(explorerLabel("End date"),this._end,"date");
    this._periodInput=field(explorerLabel("Group by"),this._period,null,
      [["month","Month"],["day","Day"],["hour","Hour"]]);
    this._chartInput=field(explorerLabel("Graph"),this._chart,null,
      [["bar","Bar"],["line","Line"]]);
    this._metricInput=field(explorerLabel("Calculation"),this._metric,null,
      [["total","Total"],["average","Average"]]);
    const apply=el("button",explorerLabel("Apply"),{class:"action"});
    const latest=el("button",explorerLabel("Use latest available"),{class:"action"});
    const dayLabel=el("label",null,{class:"field"});
    dayLabel.append(el("span",explorerLabel("Jump to day (hourly)")));
    this._dayInput=el("input",null,{type:"date",value:this._end});
    dayLabel.append(this._dayInput);
    const jump=el("button",explorerLabel("Show day"),{class:"action"});
    jump.addEventListener("click",()=>{
      const day=this._dayInput.value;
      if(!dateValid(day)) {
        this._status.textContent="Select a valid day.";
        this._status.classList.add("error");return;
      }
      this._startInput.value=day;
      this._endInput.value=day;
      this._periodInput.value="hour";
      this._start=day;this._end=day;this._period="hour";
      this._chart=this._chartInput.value;
      this._metric=this._metricInput.value;
      this._load();
    });
    latest.addEventListener("click",() => this._useLatest());
    const inputs=[this._startInput,this._endInput,this._periodInput,
      this._chartInput,this._metricInput];
    for (const input of inputs) input.addEventListener("change",() => {
      this._status.textContent="Selection changed — click Apply to update the graphs.";
      this._status.classList.add("pending");
      this._status.classList.remove("error");
    });
    apply.addEventListener("click",() => {
      this._start=this._startInput.value;
      this._end=this._endInput.value;
      this._period=this._periodInput.value;
      this._chart=this._chartInput.value;
      this._metric=this._metricInput.value;
      this._load();
    });
    controls.append(apply); controls.append(latest);
    controls.append(dayLabel); controls.append(jump); root.append(controls);
    this._definition=el("div", "", {class:"availability"});
    root.append(this._definition);
    this._availability=el("div","Available history: checking…",
      {class:"availability"}); root.append(this._availability);
    this._status=el("div","",{class:"status"}); root.append(this._status);
    this._graphs=[];
    for (const source of SOURCES) {
      const section=el("section",null,{class:"graph"});
      section.append(el("h3",`${source.name} (${source.unit})`));
      const note=el("div",source.granularity === "day" ?
        "Daily observations only; no hourly gas values are inferred." :
        "Hourly source observations; incomplete periods reflect only available data.",
        {class:"note"});
      section.append(note);
      const visible=el("div","",{class:"range-indicator"});
      section.append(visible);
      const detail=el("div",null,{class:"detail"});
      detail.hidden=true; section.append(detail);
      const view=el("div",null,{class:"viewport"}); section.append(view);
      this._graphs.push(view); root.append(section);
    }
    card.append(root); this.shadowRoot.append(card);
  }
  _clearGraphs() {
    this._series=null;
    for (const view of this._graphs) {
      view.replaceChildren();
      delete view._selectedIndex;
      const panel=view.parentElement.querySelector(".detail");
      if(panel) {panel.replaceChildren();panel.hidden=true;}
      const indicator=view.parentElement.querySelector(".range-indicator");
      if(indicator) indicator.textContent="";
    }
  }
  _query(start, end) {
    const startMs=Date.parse(`${start}T00:00:00Z`)-86400000;
    const endMs=Date.parse(`${datePlusOne(end)}T00:00:00Z`)+86400000;
    return this._hass.callWS({type:"recorder/statistics_during_period",
      start_time:new Date(startMs).toISOString(),
      end_time:new Date(endMs).toISOString(),
      statistic_ids:SOURCES.map(s=>s.id),period:"hour",types:["change"]});
  }
  async _useLatest() {
    if (!this._hass) return;
    const generation=++this._generation;
    this._clearGraphs();
    this._status.classList.remove("pending", "error");
    this._status.textContent="Looking up the latest actual observation…";
    this._loading=true;
    try {
      const zone=this._hass.config?.time_zone || "UTC";
      const today=parts(new Date(),zone).day;
      // Query only real Recorder observations, never infer freshness
      // from the wall clock or assume a last-import date.
      const start=dateValid(this._startInput.value) &&
        this._startInput.value <= today ? this._startInput.value :
        "2025-01-01";
      const response=await this._query(start,today);
      if (generation!==this._generation) return;
      const latest=newestObservation(response,zone);
      if (!latest) throw new Error("No recorded usage found in the search range");
      this._endInput.value=latest;
      this._availability.textContent=`Latest recorded date: ${latest} (${zone})`;
      this._status.textContent="End date updated. Click Apply to refresh graphs.";
      this._status.classList.add("pending");
    } catch (err) {
      if (generation===this._generation) {
        this._status.textContent=`Latest date lookup failed: ${err.message || err}`;
        this._status.classList.add("error");
      }
    } finally {
      if (generation===this._generation) this._loading=false;
    }
  }
  async _load() {
    if (!this._hass) return;
    const generation=++this._generation;
    this._clearGraphs();
    this._status.classList.remove("error", "pending");
    const error=validSelection(this._start,this._end,this._period);
    if (error) {
      this._status.textContent=error;
      this._status.classList.add("error");
      return;
    }
    this._status.textContent="Loading existing Recorder statistics…";
    this._loading=true;
    try {
      const zone=this._hass.config?.time_zone || "UTC";
      const response=await this._query(this._start,this._end);
      if (generation!==this._generation) return;
      this._cache=true;
      this._series=SOURCES.map(s => bucketize(response[s.id] || [],
        zone,this._start,this._end,this._period,this._metric,s));
      this._redraw();
      this._definition.textContent = SOURCES.map(source =>
        `${source.name}: ${calculationLabel(this._metric, this._period, source)}`
      ).join(" · ") + ". Values reflect observed readings only.";
      const latest=newestObservation(response,zone);
      this._availability.textContent=latest ?
        `Latest observation in selected range: ${latest} (${zone})` :
        "No actual observations in the selected range.";
      this._status.textContent=`Showing ${this._start} to ${this._end} · `+
        `${this._period} · ${this._chart} · ${this._metric} · ${zone}. `+
        "Missing readings are never filled.";
    } catch (err) {
      if (generation===this._generation) {
        this._clearGraphs();
        this._status.textContent=`Statistics query failed: ${err.message || err}`;
        this._status.classList.add("error");
      }
    } finally {
      if (generation===this._generation) this._loading=false;
    }
  }
}
if (!customElements.get("energy-usage-explorer")) {
  customElements.define("energy-usage-explorer",EnergyUsageExplorer);
}
window.customCards=window.customCards || [];
window.customCards.push({type:"energy-usage-explorer",name:explorerLabel("Energy Usage Explorer"),
  description:"Read-only electricity and gas history charts with date and aggregation controls."});
