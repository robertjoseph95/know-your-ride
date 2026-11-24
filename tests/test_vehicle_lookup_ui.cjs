const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { test } = require('node:test');
const vm = require('node:vm');

const root = path.join(__dirname, '..');
const files = ['wrench_demo.html', 'wrench_deploy/index.html'];

function segment(html, start, end) {
  const first = html.indexOf(start), last = html.indexOf(end, first + start.length);
  assert.ok(first >= 0 && last > first, 'renderer boundaries found');
  return html.slice(first, last);
}

function boot(html, pro) {
  const env = vm.createContext({
    kyrPro: () => pro,
    fmt: value => value || '&mdash;',
    specRow: (label, value) => '<div>' + label + ': ' + value + '</div>',
    specNote: () => '',
    renderEV: () => 'EV details',
    renderPartsTieredYTG: () => '',
    affShopParts: () => '<div>Shop parts</div>',
    affMaintBtn: () => '',
    affRow: () => '',
    renderFluids: () => '',
    renderPerf: () => '',
    window: {},
  });
  vm.runInContext(
    segment(html, 'function proUnlock(', 'function restorePro(') +
    segment(html, 'function renderMaintGated(', 'function kyrInitPaywall(') +
    segment(html, 'function valU(', 'function renderParts(') +
    segment(html, 'function renderMaint(v)', '// Service-cost table REMOVED') +
    segment(html, 'function remainingScheduleIntervals(', 'function renderHistory('),
    env,
  );
  return env;
}

const deployHtml = fs.readFileSync(path.join(root, files[1]), 'utf8');
const asset = deployHtml.match(/<script src="\/(data\.[\da-f]+\.js)"/)[1];
const data = fs.readFileSync(path.join(root, 'wrench_deploy', asset), 'utf8');
const vehicles = vm.runInNewContext(data + '\n__D__.v');
const sample = id => vehicles.find(v => v.id === id);

for (const file of files) {
  const html = fs.readFileSync(path.join(root, file), 'utf8');
  test(file + ': free specs arrive before vehicle-relevant paid benefit', () => {
    const free = boot(html, false), vehicle = sample(669);
    const page = free.renderOverview(vehicle);
    assert.match(page, /Oil Specifications/);
    assert.match(page, /Preview 3 verified service intervals for free\. Pro includes the full 10-interval schedule\./);
    assert.match(page, /onclick="switchMTab\('maint',669\)"/);
    assert.ok(page.indexOf('Oil Specifications') < page.indexOf('Preview schedule'));
    assert.ok(page.indexOf('Oil Specifications') < page.indexOf('Shop parts'));
    const preview = free.renderMaintGated(vehicle);
    assert.match(preview, /Free preview: 3 of 10 verified service intervals/);
    assert.match(preview, /onclick="openPricing\(\)"/);
    assert.ok(preview.indexOf('Maintenance Schedule') < preview.indexOf('Unlock with Pro'));
    const pro = boot(html, true);
    assert.doesNotMatch(pro.renderOverview(vehicle), /Preview schedule|Pro includes/);
    assert.doesNotMatch(pro.renderMaintGated(vehicle), /Free preview|Unlock with Pro/);
    assert.equal(free.remainingScheduleIntervals(vehicle).total, 10);
  });

  test(file + ': fully free or unverified data does not get an upsell', () => {
    const free = boot(html, false), short = sample(467), missing = sample(12939);
    assert.match(free.renderOverview(short), /Oil Specifications/);
    assert.match(free.renderMaintGated(short), /Maintenance Schedule/);
    assert.doesNotMatch(free.renderOverview(short) + free.renderMaintGated(short), /Unlock with Pro|Preview schedule/);
    assert.match(free.renderOverview(missing), /Verified oil specifications are unavailable/);
    assert.match(free.renderMaintGated(missing), /No verified maintenance schedule is available/);
    assert.doesNotMatch(free.renderOverview(missing) + free.renderMaintGated(missing), /Unlock with Pro|Preview schedule/);
    assert.doesNotMatch(free.renderMaintGated({...short, maint: Array.from({length: 5},()=>({ver:0}))}), /Unlock with Pro/);
  });

  test(file + ': free lookup copy is explicit and avoids promising missing specs', () => {
    assert.match(html, /Free VIN lookup/);
    assert.match(html, /see available specs for free/);
    assert.match(html, /has not verified which specs apply to this VIN/);
    assert.doesNotMatch(html, /opening full specs|full specs coming soon/);
  });
}
