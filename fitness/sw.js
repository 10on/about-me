/* Service Worker — handles Web Push notifications */

self.addEventListener("install", () => self.skipWaiting());
self.addEventListener("activate", (e) => e.waitUntil(self.clients.claim()));

self.addEventListener("push", (event) => {
  let data = { title: "💪 Тренировка!", body: "Открой и жги.", url: "/" };

  if (event.data) {
    try {
      data = { ...data, ...JSON.parse(event.data.text()) };
    } catch {
      data.body = event.data.text();
    }
  }

  event.waitUntil(
    self.registration.showNotification(data.title, {
      body: data.body,
      icon: "/fitness/icon-192.png",
      badge: "/fitness/icon-192.png",
      data: { url: data.url },
      actions: [
        { action: "open", title: "Открыть" },
        { action: "dismiss", title: "Потом" },
      ],
      requireInteraction: true,
      vibrate: [200, 100, 200],
    })
  );
});

self.addEventListener("notificationclick", (event) => {
  event.notification.close();
  if (event.action === "dismiss") return;

  const url = event.notification.data?.url || "/fitness/";
  event.waitUntil(
    self.clients.matchAll({ type: "window" }).then((clients) => {
      const existing = clients.find((c) => c.url.includes("/fitness/"));
      if (existing) return existing.focus();
      return self.clients.openWindow(url);
    })
  );
});
