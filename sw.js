const CACHE = "lingtai-v8";
const ASSETS = [
  "./",
  "./index.html",
  "./manifest.webmanifest",
  "./assets/ip-waiting.jpg",
  "./assets/ip-rejoice.jpg",
  "./assets/ip-complete.jpg",
  "./assets/ip-comfort.jpg",
  "./assets/logo-seal.jpg",
  "./assets/muyu-body.jpg",
  "./assets/icon-192.png",
  "./assets/apple-touch-icon.png",
  "./assets/app-icon-512.png"
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE).then((cache) => cache.addAll(ASSETS)).then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((key) => key !== CACHE).map((key) => caches.delete(key)))
    ).then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (event) => {
  if (event.request.method !== "GET") return;
  event.respondWith(
    caches.match(event.request).then((cached) => {
      if (cached) return cached;
      return fetch(event.request)
        .then((response) => {
          const copy = response.clone();
          if (response.ok) {
            caches.open(CACHE).then((cache) => cache.put(event.request, copy));
          }
          return response;
        })
        .catch(() => caches.match("./index.html"));
    })
  );
});
