const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { test } = require('node:test');
const vm = require('node:vm');

const files = ['wrench_demo.html', 'wrench_deploy/index.html'];
const nhtsa = /href="https:\/\/www\.nhtsa\.gov\/recalls"/;
const falseClear = /no open recalls|your recall status|rcl-head ok/i;
const vinA = '1'.repeat(17), vinB = '2'.repeat(17);
const settle = () => new Promise(resolve => setImmediate(resolve));
const dec = (model = 'Sentra') => ({ year: '2020', make: 'Nissan', model });
const response = (status, data) => ({ ok: status >= 200 && status < 300, json: async () => data });

function segment(html, start, end) {
  const first = html.indexOf(start), last = html.indexOf(end, first + start.length);
  assert.ok(first >= 0 && last > first, 'renderer boundaries found');
  return html.slice(first, last);
}

function boot(html, fetch, vehicles = []) {
  const vin = {};
  const out = {
    panel: null,
    set innerHTML(text) { this.panel = null; this.text = text; },
    get innerHTML() { return this.text; },
    set textContent(text) { this.innerHTML = text; },
    appendChild(panel) { this.panel = panel; },
  };
  const opened = [];
  const env = vm.createContext({
    document: {
      createElement: () => ({}),
      getElementById: id => id === 'vin-input' ? vin : out,
    },
    DB: { v: vehicles },
    openModal: id => opened.push(id),
    fetch,
  });
  vm.runInContext(
    segment(html, '/*WRENCH_VIN*/', '/*WRENCH_PARTTIERS*/') +
    segment(html, '/*WRENCH_RECALL*/', 'function switchTab') +
    segment(html, 'function plRow(', 'function kyrPlSlot(') +
    segment(html, 'function renderWarranty(v)', '// 4-tab consolidation') +
    html.split('\n').find(line => line.startsWith('function htmlEsc(')),
    env,
  );
  return { env, out, opened, decode(value = vinA) { vin.value = value; env.decodeVIN(); } };
}

for (const file of files) {
  const html = fs.readFileSync(path.join(__dirname, '..', file), 'utf8');
  test(file + ': recall lookup distinguishes campaigns, empty and failures', async () => {
    const campaign = { NHTSACampaignNumber: '20V001', Summary: '<affected>', Remedy: 'Replace seat', ParkIt: true, ParkOutSide: false, status: 'Completed' };
    const other = { NHTSACampaignNumber: '20V002', ParkIt: 'No', ParkOutSide: 'Yes' };
    const cases = [
      [() => response(200, { recalls: [campaign, other], count: 2 }), /2 model-year campaigns found/],
      [() => response(200, { recalls: [], count: 0 }), /No campaigns returned/],
      [() => response(400, { recalls: [] }), /Recall lookup unavailable/],
      [() => response(502, { recalls: [] }), /Recall lookup unavailable/],
      [() => response(200, { error: '', recalls: [] }), /Recall lookup unavailable/],
      [() => response(200, { count: 1, recalls: [] }), /Recall lookup unavailable/],
      [() => response(200, { results: [] }), /Recall lookup unavailable/],
      [() => response(200, { recalls: [{}] }), /Recall lookup unavailable/],
      [() => ({ ok: true, json: () => Promise.reject(Error('invalid JSON')) }), /Recall lookup unavailable/],
      [() => Promise.reject(Error('network offline')), /Recall lookup unavailable/],
    ];
    for (const [makeResponse, expected] of cases) {
      const setup = boot(html, async url => {
        if (url.startsWith('/api/vin/')) return response(200, dec());
        assert.equal(url, '/api/recalls?make=Nissan&model=Sentra&year=2020');
        return makeResponse();
      });
      setup.decode();
      await settle();
      assert.match(setup.out.panel.innerHTML, expected);
      assert.match(setup.out.panel.innerHTML, nhtsa);
      assert.doesNotMatch(setup.out.panel.innerHTML, falseClear);
      if (expected.source.includes('2 model-year')) {
        assert.equal(setup.out.panel.innerHTML.match(/DO NOT DRIVE AFFECTED VEHICLES/g).length, 1);
        assert.equal(setup.out.panel.innerHTML.match(/PARK AFFECTED VEHICLES OUTSIDE/g).length, 1);
        assert.match(setup.out.panel.innerHTML, /&lt;affected&gt;/);
        assert.match(setup.out.panel.innerHTML, /Replace seat/);
        assert.ok(setup.out.panel.innerHTML.indexOf('Check VIN at NHTSA.gov') < setup.out.panel.innerHTML.indexOf('CAMPAIGN 20V001'));
        assert.doesNotMatch(setup.out.panel.innerHTML, /Completed/);
      }
    }
  });

  test(file + ': incomplete VIN metadata and decode failure still offer official VIN check', async () => {
    const incomplete = boot(html, async url => {
      assert.ok(url.startsWith('/api/vin/'));
      return response(200, dec(''));
    });
    incomplete.decode();
    await settle();
    assert.match(incomplete.out.panel.innerHTML, /Recall lookup unavailable/);
    assert.match(incomplete.out.panel.innerHTML, nhtsa);
    const failed = boot(html, async () => response(502, {}));
    failed.decode();
    await settle();
    assert.match(failed.out.innerHTML, /Could not reach the VIN decode service/);
    assert.match(failed.out.innerHTML, nhtsa);
  });

  test(file + ': stale decode and recall responses cannot overwrite newer results', async () => {
    let finishOldDecode;
    const first = boot(html, url => url.endsWith(vinA)
      ? new Promise(resolve => { finishOldDecode = resolve; })
      : Promise.resolve(response(200, url.endsWith(vinB) ? dec('Altima') : { recalls: [] })));
    first.decode();
    first.decode(vinB);
    await settle();
    finishOldDecode(response(200, dec()));
    await settle();
    assert.match(first.out.innerHTML, /Altima/);

    let finishOldRecall;
    const next = boot(html, url => {
      if (url.includes('model=Sentra')) return new Promise(resolve => { finishOldRecall = resolve; });
      return Promise.resolve(response(200, url.endsWith(vinA) ? dec() : url.endsWith(vinB) ? dec('Altima') : { recalls: [] }));
    });
    next.decode();
    await settle();
    const oldPanel = next.out.panel;
    assert.match(oldPanel.innerHTML, /Checking model-year campaigns/);
    next.decode(vinB);
    await settle();
    finishOldRecall(response(200, { recalls: [{ NHTSACampaignNumber: 'OLD' }] }));
    await settle();
    assert.match(next.out.innerHTML, /Altima/);
    assert.match(next.out.panel.innerHTML, /No campaigns returned/);
    assert.doesNotMatch(oldPanel.innerHTML, /OLD/);
  });


  test(file + ': VIN identification does not choose specs for different or ambiguous configurations', async () => {
    const mustang = { year: 2021, make: 'FORD', model: 'Mustang', trim: 'GT', engine: 'V8', displacement_liters: '5.0', cylinders: 8 };
    const eco = { ...mustang, trim: 'EcoBoost Premium', engine: 'I4', displacement_liters: 2.3, cylinders: 4 };
    const fastback = { id: 1, year: '2021', make: 'Ford', model: 'Mustang', trim: 'Fastback', engine: '2.3L EcoBoost' };
    const convertible = { ...fastback, id: 2, trim: 'Convertible' };
    const elantra = { year: '2020', make: 'HYUNDAI', model: 'Elantra', trim: 'Eco', engine: 'G4LD', displacement_liters: 1.4, cylinders: 4 };
    const cases = [
      [mustang, [fastback], /2021 FORD Mustang GT/, /5\.0L \/ V8 \/ 8 cylinders/],
      [elantra, [{ ...elantra, id: 3, engine: '1.4L / 1.6L / 2.0L', oil: { verified: true } }], /2020 HYUNDAI Elantra Eco/, /1\.4L \/ G4LD/],
      [eco, [fastback, convertible], /2021 FORD Mustang EcoBoost Premium/, /2\.3L \/ I4/],
      [eco, [convertible, fastback], /2021 FORD Mustang EcoBoost Premium/, /2\.3L \/ I4/],
      [eco, [convertible], /2021 FORD Mustang EcoBoost Premium/, /2\.3L \/ I4/],
    ];
    for (const [decoded, vehicles, identity, engine] of cases) {
      const app = boot(html, async url => {
        if (url.startsWith('/api/vin/')) return response(200, decoded);
        assert.equal(url, '/api/recalls?make='+decoded.make+'&model='+decoded.model+'&year='+decoded.year);
        return response(200, { recalls: [], count: 0 });
      }, vehicles);
      app.decode();
      await settle();
      assert.deepEqual(app.opened, []);
      assert.match(app.out.innerHTML, identity);
      assert.match(app.out.innerHTML, engine);
      assert.match(app.out.innerHTML, /has not verified which specs apply to this VIN/);
      assert.match(app.out.innerHTML, /vehicle search below to browse available specs/);
      assert.doesNotMatch(app.out.innerHTML, /Opening available vehicle details|not in our specs database/);
      assert.match(app.out.panel.innerHTML, /No campaigns returned/);
      assert.match(app.out.panel.innerHTML, nhtsa);
    }
  });

  test(file + ': partial, malformed and truncated decode fail closed', async () => {
    const partial = boot(html, async url => {
      assert.ok(url.startsWith('/api/vin/'));
      return response(200, { make: ' FORD ', model: { name: 'Mustang' }, year: 'broken',
        trim: '<unknown>', engine: '<strong>V8</strong>', displacement_liters: { value: 5 },
        fuel_type: ['Gasoline'], cylinders: 'eight' });
    });
    partial.decode();
    assert.equal(partial.out.innerHTML, 'Decoding VIN...');
    await settle();
    assert.match(partial.out.innerHTML, /FORD &lt;unknown&gt;/);
    assert.match(partial.out.innerHTML, /&lt;strong&gt;V8&lt;\/strong&gt;/);
    assert.match(partial.out.innerHTML, /Some vehicle details could not be decoded/);
    assert.doesNotMatch(partial.out.innerHTML, /undefined|\[object Object\]|broken|Gasoline|eight/);
    assert.match(partial.out.panel.innerHTML, /Recall lookup unavailable/);
    assert.match(partial.out.panel.innerHTML, nhtsa);
    assert.deepEqual(partial.opened, []);

    for (const decoded of [null, [], 'invalid', { make: {} }, { make: '   ' }, { error: 'No result', ...dec() }]) {
      let count = 0;
      const app = boot(html, async () => { count++; return response(200, decoded); });
      app.decode();
      await settle();
      assert.equal(count, 1);
      assert.match(app.out.innerHTML, /No decode result for that VIN/);
      assert.match(app.out.innerHTML, nhtsa);
      assert.deepEqual(app.opened, []);
    }

    let finish;
    const truncated = boot(html, () => new Promise(resolve => { finish = resolve; }));
    truncated.decode();
    truncated.decode('1'.repeat(16));
    finish(response(200, dec()));
    await settle();
    assert.match(truncated.out.innerHTML, /VIN must be exactly 17 characters/);
    assert.equal(truncated.out.panel, null);
    assert.deepEqual(truncated.opened, []);
  });

  test(file + ': sample, selected vehicle, decoded VIN, and Safety retain official link', async () => {
    const vehicle = { ...dec(), id: 467, recalls: [{ camp: '20V001', park: true }] };
    const app = boot(html, async url => response(200, url.startsWith('/api/vin/') ? dec() : { recalls: [] }), [vehicle]);
    const sample = html.split('\n').find(line => line.includes('  <div id="kyr-sample"'));
    assert.match(sample, nhtsa);
    assert.match(sample, /4 Model-Year Recall Campaigns/);
    assert.doesNotMatch(sample, falseClear);
    for (const item of [vehicle, { ...vehicle, recalls: undefined }]) {
      const placard = app.env.renderPlacard(item);
      const safety = app.env.renderWarranty(item);
      assert.match(placard, /MODEL-YEAR RECALLS/);
      assert.match(placard, nhtsa);
      assert.match(safety, /NHTSA Model-Year Recall Campaigns/);
      assert.match(safety, nhtsa);
      assert.doesNotMatch(placard + safety, falseClear);
      if (item.recalls) assert.match(safety, /DO NOT DRIVE AFFECTED VEHICLES/);
      else assert.match(safety, /No campaigns for this model year in our data/);
    }
    assert.match(html, /renderWarrantyKbb\(v\)[\s\S]*?renderWarranty\(v\)/);
    assert.match(html, /function renderSafetyTab\(v\)\{[^}]*renderWarrantyKbb\(v\)/);
    assert.match(html, /safety:\s*renderSafetyTab/);
    app.decode();
    await settle();
    assert.deepEqual(app.opened, []);
    assert.match(app.out.panel.innerHTML, nhtsa);
  });
}
