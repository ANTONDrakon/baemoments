const CACHE_NAME = 'baemoments-v2';
const STATIC_ASSETS = [
  '/',
  '/index.html',
  '/landing.html'
];

// Pre-cache критических изображений для LCP
const CRITICAL_IMAGES = [
  '/images/dress-01-640.avif',
  '/images/dress-01-640.webp',
  '/images/dress-01-640.jpg'
];

// Google Sites CDN для кэширования
const GOOGLE_SITES_CACHE = 'google-sites-v1';
const GOOGLE_SITES_PATTERNS = [
  'sites.google.com',
  'www.google.com',
  'fonts.gstatic.com',
  'www.googletagmanager.com'
];

// Установка — кэшируем статику и критические изображения
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return Promise.all([
        cache.addAll(STATIC_ASSETS),
        cache.addAll(CRITICAL_IMAGES)
      ]);
    })
  );
  // Принудительная активация без ожидания закрытия страницы
  self.skipWaiting();
});

// Активация — очищаем старые кэши
self.addEventListener('activate', (event) => {
  event.waitUntil(
    Promise.all([
      caches.keys().then((keys) => {
        return Promise.all(
          keys.filter(key => key !== CACHE_NAME && key !== GOOGLE_SITES_CACHE).map(key => caches.delete(key))
        );
      }),
      // Немедленно захватываем все страницы
      self.clients.claim()
    ])
  );
});

// Проверка, относится ли URL к Google Sites
function isGoogleSitesUrl(url) {
  return GOOGLE_SITES_PATTERNS.some(pattern => url.hostname.includes(pattern));
}

// Стратегия: Cache First для изображений, Network First для HTML
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Кэшируем Google Sites ресурсы (Cache First)
  if (isGoogleSitesUrl(url)) {
    event.respondWith(
      caches.open(GOOGLE_SITES_CACHE).then((cache) => {
        return cache.match(request).then((cached) => {
          return cached || fetch(request).then((response) => {
            const clone = response.clone();
            cache.put(request, clone);
            return response;
          }).catch(() => cached);
        });
      })
    );
    return;
  }

  // Кэшируем изображения (Cache First)
  if (request.destination === 'image') {
    event.respondWith(
      caches.match(request).then((cached) => {
        return cached || fetch(request).then((response) => {
          const clone = response.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(request, clone));
          return response;
        });
      })
    );
    return;
  }

  // Для HTML — Network First с fallback на кэш
  if (request.mode === 'navigate') {
    event.respondWith(
      fetch(request).then((response) => {
        const clone = response.clone();
        caches.open(CACHE_NAME).then((cache) => cache.put(request, clone));
        return response;
      }).catch(() => caches.match(request))
    );
    return;
  }

  // Для всего остального — Cache First
  event.respondWith(
    caches.match(request).then((cached) => {
      return cached || fetch(request);
    })
  );
});
