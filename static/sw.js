// Service Worker for AI SDLC Pro PWA
const CACHE_VERSION = 'v3-shared-workspace';

self.addEventListener('install', (event) => {
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(keys.map((key) => caches.delete(key)));
    }).then(() => self.clients.claim())
  );
});

// Tuyệt đối không can thiệp vào các yêu cầu điều hướng trang (navigate) hoặc API
// Tránh lỗi "Không thể tải trang" khi máy chủ khởi động lại hoặc có chuyển hướng đăng nhập
self.addEventListener('fetch', (event) => {
  // Để trình duyệt xử lý tự nhiên qua mạng
  return;
});
