// Never cache API/member data or uploaded media: stale responses can resurrect removed data.
self.addEventListener('install',()=>self.skipWaiting());
self.addEventListener('activate',event=>event.waitUntil(
  caches.keys().then(keys=>Promise.all(keys.filter(k=>k.startsWith('resonance-shell-')).map(k=>caches.delete(k)))).then(()=>self.clients.claim())
));
