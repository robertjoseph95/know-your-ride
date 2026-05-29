// Know Your Ride service worker — offline app shell caching.
// CACHE name is bumped on every deploy that changes HTML behavior. The activate
// handler deletes any cache that isn't the current name, so users get a clean
// slate on the next browser-controlled SW activation.
const CACHE = 'kyr-v2';
const CORE = ['/manifest.json', '/icon-192.png', '/icon-512.png'];

self.addEventListener('install', function (e) {
  e.waitUntil(
    caches.open(CACHE)
      .then(function (c) { return Promise.all(CORE.map(function (u) { return c.add(u).catch(function () {}); })); })
      .then(function () { return self.skipWaiting(); })
  );
});

self.addEventListener('activate', function (e) {
  e.waitUntil(
    caches.keys()
      .then(function (keys) { return Promise.all(keys.filter(function (k) { return k !== CACHE; }).map(function (k) { return caches.delete(k); })); })
      .then(function () { return self.clients.claim(); })
  );
});

// Heuristic: any top-level navigation OR an explicit Accept: text/html is the
// app shell — these MUST use network-first so deploys land on the very next
// load. Everything else (icons, manifest, etc.) stays on stale-while-revalidate
// for offline resilience.
function isAppShell(req) {
  if (req.mode === 'navigate') return true;
  var accept = req.headers.get('accept') || '';
  if (accept.indexOf('text/html') >= 0) return true;
  var p = new URL(req.url).pathname;
  if (p === '/' || p.endsWith('.html')) return true;
  return false;
}

self.addEventListener('fetch', function (e) {
  var req = e.request;
  if (req.method !== 'GET') return;
  var url = new URL(req.url);
  // Never touch API calls or cross-origin requests.
  if (url.origin !== self.location.origin || url.pathname.indexOf('/api/') === 0) return;

  if (isAppShell(req)) {
    // Network-first: a successful fetch updates the cache AND is returned. If
    // the network fails (offline), fall back to whatever's in cache so the
    // PWA still launches.
    e.respondWith(
      fetch(req).then(function (res) {
        if (res && res.status === 200 && res.type === 'basic') {
          var copy = res.clone();
          caches.open(CACHE).then(function (c) { c.put(req, copy); });
        }
        return res;
      }).catch(function () { return caches.match(req); })
    );
    return;
  }

  // Stale-while-revalidate for non-HTML assets.
  e.respondWith(
    caches.match(req).then(function (cached) {
      var net = fetch(req).then(function (res) {
        if (res && res.status === 200 && res.type === 'basic') {
          var copy = res.clone();
          caches.open(CACHE).then(function (c) { c.put(req, copy); });
        }
        return res;
      }).catch(function () { return cached; });
      return cached || net;
    })
  );
});
