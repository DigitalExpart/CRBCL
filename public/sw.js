/**
 * CRBCL Family Wellness Platform — Conservative Static Asset Service Worker
 *
 * SAFETY RESTRICTIONS:
 * - NEVER intercepts or caches API traffic (/api/*).
 * - NEVER intercepts non-GET requests (POST, PUT, DELETE).
 * - NEVER caches protected client records, narratives, or tokens.
 * - Only caches static application shell assets (CSS, JS, logos) for offline page loading.
 */

const CACHE_NAME = 'crbcl-app-shell-v1';
const PRECACHE_ASSETS = [
  '/',
  '/index.html',
  '/crbcl-emblem.png',
  '/crbcl-logo.png',
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(PRECACHE_ASSETS).catch((err) => {
        console.warn('CRBCL SW: Precache assets warning:', err);
      });
    })
  );
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k))
      );
    })
  );
  self.clients.claim();
});

self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);

  // STRICT SAFETY RULE: Never intercept API calls, auth routes, or non-GET requests
  if (url.pathname.startsWith('/api/') || event.request.method !== 'GET') {
    return;
  }

  // Network-first strategy with cache fallback for static app shell
  event.respondWith(
    fetch(event.request)
      .then((networkResponse) => {
        // Cache successful responses for static assets only
        if (networkResponse && networkResponse.status === 200 && networkResponse.type === 'basic') {
          const responseToCache = networkResponse.clone();
          caches.open(CACHE_NAME).then((cache) => {
            cache.put(event.request, responseToCache);
          });
        }
        return networkResponse;
      })
      .catch(async () => {
        // Offline fallback to cache
        const cachedResponse = await caches.match(event.request);
        if (cachedResponse) {
          return cachedResponse;
        }
        // Fallback for HTML navigation requests
        if (event.request.mode === 'navigate') {
          return caches.match('/index.html');
        }
        return new Response('Network error (offline)', { status: 503, statusText: 'Service Unavailable' });
      })
  );
});
