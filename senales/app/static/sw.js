const CACHE = 'senales-v1';
const SHELL = ['/', '/static/style.css', '/static/app.js', '/static/icon-192.png'];

self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(SHELL)).then(() => self.skipWaiting()));
});
self.addEventListener('activate', e => {
  e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== CACHE).map(k => caches.delete(k)))).then(() => self.clients.claim()));
});
// La interfaz se sirve primero desde la red; la caché solo cubre cuando no hay conexión. La API nunca se cachea.
self.addEventListener('fetch', e => {
  const u = new URL(e.request.url);
  if (e.request.method !== 'GET' || u.pathname.startsWith('/api/') || u.pathname === '/hook') return;
  e.respondWith(fetch(e.request).then(r => {
    const copy = r.clone();
    caches.open(CACHE).then(c => c.put(e.request, copy));
    return r;
  }).catch(() => caches.match(e.request)));
});

self.addEventListener('push', e => {
  let d = {};
  try { d = e.data.json(); } catch (_) { d = {title: 'Señales', body: e.data ? e.data.text() : ''}; }
  e.waitUntil(self.registration.showNotification(d.title || 'Señales', {
    body: d.body || '', tag: d.tag, data: {url: d.url || '/'},
    icon: '/static/icon-192.png', badge: '/static/icon-192.png'
  }));
});
self.addEventListener('notificationclick', e => {
  e.notification.close();
  const url = e.notification.data?.url || '/';
  e.waitUntil(self.clients.matchAll({type: 'window', includeUncontrolled: true}).then(cs => {
    for (const c of cs) { c.navigate(url); return c.focus(); }
    return self.clients.openWindow(url);
  }));
});
