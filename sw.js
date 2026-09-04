const CACHE = "lingtai-v11";
const ASSETS = [
  "/",
  "/index.html",
  "/manifest.webmanifest",
  "/assets/ip-waiting.jpg",
  "/assets/ip-rejoice.jpg",
  "/assets/ip-complete.jpg",
  "/assets/ip-comfort.jpg",
  "/assets/logo-seal.jpg",
  "/assets/muyu-body.jpg",
  "/assets/icon-192.png",
  "/assets/apple-touch-icon.png",
  "/assets/app-icon-512.png"
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE).then(async (cache) => {
      await Promise.all(
        ASSETS.map((url) => cache.add(url).catch(() => null))
      );
    }).then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((key) => key !== CACHE).map((key) => caches.delete(key)))
    ).then(() => self.clients.claim())
  );
});

function isNavigate(request) {
  return request.mode === "navigate" ||
    (request.method === "GET" && request.headers.get("accept") || "").includes("text/html");
}

function sameOrigin(url) {
  return url.origin === self.location.origin;
}

self.addEventListener("fetch", (event) => {
  if (event.request.method !== "GET") return;
  const url = new URL(event.request.url);
  if (!sameOrigin(url)) return;

  // /index.html 会被 Pages 308 到 /，导航统一走首页，避免独立 App 里跟跳失败
  if (isNavigate(event.request) || url.pathname === "/index.html") {
    event.respondWith(
      fetch("/")
        .then((response) => {
          if (response.ok) {
            const copy = response.clone();
            caches.open(CACHE).then((cache) => {
              cache.put("/", copy);
              cache.put("/index.html", copy.clone());
            });
          }
          return response;
        })
        .catch(async () => {
          return (await caches.match("/")) ||
            (await caches.match("/index.html")) ||
            Response.error();
        })
    );
    return;
  }

  event.respondWith(
    caches.match(event.request).then((cached) => {
      if (cached) return cached;
      return fetch(event.request)
        .then((response) => {
          if (response.ok) {
            const copy = response.clone();
            caches.open(CACHE).then((cache) => cache.put(event.request, copy));
          }
          return response;
        })
        .catch(() => caches.match("/"));
    })
  );
});
