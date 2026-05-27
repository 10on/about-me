/* ── Config ─────────────────────────────────────────────────────────────── */
// In production: your Worker URL, e.g. https://fitness-worker.yourname.workers.dev
// In local dev: leave as-is if using wrangler dev on port 8787
const API = window.WORKER_URL || "https://fitness-worker.REPLACE_ME.workers.dev";

const DAYS = ["Вс", "Пн", "Вт", "Ср", "Чт", "Пт", "Сб"];

/* ── State ──────────────────────────────────────────────────────────────── */
let exercises = [];
let editingId = null;
let selectedDays = [1, 2, 3, 4, 5];

/* ── Fetch wrapper ──────────────────────────────────────────────────────── */
async function api(path, opts = {}) {
  const res = await fetch(`${API}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...opts,
  });
  if (!res.ok) {
    const e = await res.json().catch(() => ({ error: res.statusText }));
    throw new Error(e.error || "API error");
  }
  return res.json();
}

/* ── Push notifications ─────────────────────────────────────────────────── */
let pushSub = null;

async function getPushPublicKey() {
  try {
    const { publicKey } = await api("/api/push/publickey");
    return publicKey;
  } catch {
    return null;
  }
}

function urlBase64ToUint8Array(base64String) {
  const padding = "=".repeat((4 - (base64String.length % 4)) % 4);
  const base64 = (base64String + padding).replace(/-/g, "+").replace(/_/g, "/");
  const raw = atob(base64);
  const arr = new Uint8Array(raw.length);
  for (let i = 0; i < raw.length; i++) arr[i] = raw.charCodeAt(i);
  return arr;
}

async function subscribeToPush() {
  if (!("serviceWorker" in navigator) || !("PushManager" in window)) {
    toast("Пуши не поддерживаются в этом браузере 😢", "error");
    return;
  }

  const perm = await Notification.requestPermission();
  if (perm !== "granted") {
    toast("Разрешение на пуши отклонено", "error");
    updatePushUI();
    return;
  }

  const publicKey = await getPushPublicKey();
  if (!publicKey) {
    toast("Не удалось получить VAPID ключ", "error");
    return;
  }

  const reg = await navigator.serviceWorker.ready;
  pushSub = await reg.pushManager.subscribe({
    userVisibleOnly: true,
    applicationServerKey: urlBase64ToUint8Array(publicKey),
  });

  await api("/api/push/subscribe", {
    method: "POST",
    body: JSON.stringify(pushSub.toJSON()),
  });

  toast("Пуши подключены 🔔", "success");
  updatePushUI();
}

async function unsubscribeFromPush() {
  if (!pushSub) return;
  const endpoint = pushSub.endpoint;
  await pushSub.unsubscribe();
  pushSub = null;

  await api("/api/push/subscribe", {
    method: "DELETE",
    body: JSON.stringify({ endpoint }),
  }).catch(() => {});

  toast("Пуши отключены", "success");
  updatePushUI();
}

async function initPush() {
  if (!("serviceWorker" in navigator)) return;

  const reg = await navigator.serviceWorker.register("/fitness/sw.js");
  await reg.update();

  const sub = await reg.pushManager.getSubscription();
  if (sub) pushSub = sub;
  updatePushUI();
}

function updatePushUI() {
  const banner = document.getElementById("push-banner");
  const dot = document.getElementById("push-dot");
  const dotLabel = document.getElementById("push-dot-label");
  const perm = Notification.permission;

  if (perm === "denied") {
    dot.className = "push-dot denied";
    dotLabel.textContent = "Пуши заблокированы";
    banner.classList.add("hidden");
    return;
  }

  if (pushSub) {
    dot.className = "push-dot active";
    dotLabel.textContent = "Пуши активны";
    banner.classList.add("hidden");
  } else {
    dot.className = "push-dot";
    dotLabel.textContent = "Пуши не подключены";
    if (perm !== "denied") banner.classList.remove("hidden");
  }
}

/* ── Exercises ──────────────────────────────────────────────────────────── */
async function loadExercises() {
  try {
    exercises = await api("/api/exercises");
    render();
  } catch (e) {
    console.error(e);
    // Show demo data if API not configured
    if (exercises.length === 0) {
      renderEmpty();
    }
  }
}

async function createExercise(data) {
  const ex = await api("/api/exercises", { method: "POST", body: JSON.stringify(data) });
  exercises.push(ex);
  render();
  toast(`«${ex.name}» добавлен 💪`, "success");
}

async function updateExercise(id, data) {
  const ex = await api(`/api/exercises/${id}`, { method: "PUT", body: JSON.stringify(data) });
  exercises = exercises.map((e) => (e.id === id ? ex : e));
  render();
  toast("Сохранено", "success");
}

async function deleteExercise(id) {
  await api(`/api/exercises/${id}`, { method: "DELETE" });
  exercises = exercises.filter((e) => e.id !== id);
  render();
  toast("Удалено", "success");
}

async function completeExercise(id) {
  const ex = await api(`/api/exercises/${id}/complete`, { method: "POST" });
  exercises = exercises.map((e) => (e.id === id ? ex : e));
  renderCard(id);
  toast("Зачёт! 🔥", "success");
}

async function toggleEnabled(id) {
  const ex = exercises.find((e) => e.id === id);
  if (!ex) return;
  await updateExercise(id, { enabled: !ex.enabled });
}

/* ── Render ─────────────────────────────────────────────────────────────── */
function isCompletedToday(ex) {
  if (!ex.lastCompleted) return false;
  const d = new Date(ex.lastCompleted);
  const now = new Date();
  return (
    d.getFullYear() === now.getFullYear() &&
    d.getMonth() === now.getMonth() &&
    d.getDate() === now.getDate()
  );
}

function fmtDays(days) {
  if (!days?.length) return "";
  if (days.length === 7) return "Каждый день";
  if (JSON.stringify([...days].sort()) === JSON.stringify([1, 2, 3, 4, 5])) return "Пн–Пт";
  if (JSON.stringify([...days].sort()) === JSON.stringify([0, 6])) return "Сб, Вс";
  return days.map((d) => DAYS[d]).join(", ");
}

function fmtDuration(sec) {
  if (!sec) return null;
  if (sec < 60) return `${sec}с`;
  return `${Math.floor(sec / 60)}мин`;
}

function cardHTML(ex) {
  const completedToday = isCompletedToday(ex);
  const classes = [
    "exercise-card",
    ex.enabled === false ? "disabled" : "",
    completedToday ? "completed-today" : "",
  ]
    .filter(Boolean)
    .join(" ");

  const metaTags = [];
  if (ex.sets && ex.reps) metaTags.push(`<span class="tag">${ex.sets}×${ex.reps}</span>`);
  else if (ex.reps) metaTags.push(`<span class="tag">${ex.reps} повт.</span>`);
  else if (ex.sets) metaTags.push(`<span class="tag">${ex.sets} подх.</span>`);
  if (ex.duration) metaTags.push(`<span class="tag">⏱ ${fmtDuration(ex.duration)}</span>`);
  if (ex.scheduleTime) metaTags.push(`<span class="tag tag-accent">🕐 ${ex.scheduleTime}</span>`);
  if (ex.scheduleDays?.length) metaTags.push(`<span class="tag">${fmtDays(ex.scheduleDays)}</span>`);
  if (completedToday) metaTags.push(`<span class="tag tag-green">✓ Сегодня выполнено</span>`);
  else if (ex.completions) metaTags.push(`<span class="tag">🏆 ${ex.completions} раз</span>`);

  return `
<div class="${classes}" data-id="${ex.id}">
  <div class="card-header">
    <div>
      <div class="card-title">${escHtml(ex.name)}</div>
      ${ex.description ? `<div class="card-desc">${escHtml(ex.description)}</div>` : ""}
    </div>
    <div class="card-menu">
      <button class="btn-icon card-menu-btn" onclick="toggleMenu('${ex.id}')" title="Ещё">⋮</button>
      <div class="dropdown" id="menu-${ex.id}">
        <button onclick="openEdit('${ex.id}')">✏️ Изменить</button>
        <button onclick="toggleEnabled('${ex.id}')">${ex.enabled === false ? "✅ Включить" : "⏸ Отключить"}</button>
        <button class="btn-danger" onclick="confirmDelete('${ex.id}')">🗑 Удалить</button>
      </div>
    </div>
  </div>
  ${metaTags.length ? `<div class="card-meta">${metaTags.join("")}</div>` : ""}
  <div class="card-actions">
    <button class="btn btn-done btn-sm ${completedToday ? "active" : ""}" onclick="completeExercise('${ex.id}')">
      ${completedToday ? "✓ Выполнено" : "Отметить"}
    </button>
  </div>
</div>`;
}

function render() {
  const list = document.getElementById("exercises-list");
  if (!exercises.length) {
    renderEmpty();
    return;
  }
  list.innerHTML = exercises.map(cardHTML).join("");
}

function renderCard(id) {
  const ex = exercises.find((e) => e.id === id);
  if (!ex) return;
  const el = document.querySelector(`[data-id="${id}"]`);
  if (!el) return;
  el.outerHTML = cardHTML(ex);
}

function renderEmpty() {
  document.getElementById("exercises-list").innerHTML = `
    <div class="empty-state">
      <div class="emoji">🏋️</div>
      <p>Пока нет упражнений.<br>Добавь первое и начни качать!</p>
      <button class="btn-primary btn" onclick="openCreate()">+ Добавить упражнение</button>
    </div>`;
}

/* ── Modal ──────────────────────────────────────────────────────────────── */
function openCreate() {
  editingId = null;
  selectedDays = [1, 2, 3, 4, 5];
  document.getElementById("modal-title").textContent = "Новое упражнение";
  document.getElementById("ex-form").reset();
  document.getElementById("ex-time").value = "09:00";
  renderDayPicker();
  document.getElementById("modal").classList.remove("hidden");
  document.getElementById("ex-name").focus();
}

function openEdit(id) {
  const ex = exercises.find((e) => e.id === id);
  if (!ex) return;
  editingId = id;
  selectedDays = ex.scheduleDays || [1, 2, 3, 4, 5];

  document.getElementById("modal-title").textContent = "Изменить упражнение";
  document.getElementById("ex-name").value = ex.name || "";
  document.getElementById("ex-desc").value = ex.description || "";
  document.getElementById("ex-sets").value = ex.sets || "";
  document.getElementById("ex-reps").value = ex.reps || "";
  document.getElementById("ex-duration").value = ex.duration ? Math.round(ex.duration / 60) : "";
  document.getElementById("ex-time").value = ex.scheduleTime || "09:00";

  renderDayPicker();
  document.getElementById("modal").classList.remove("hidden");
  closeMenu();
}

function closeModal() {
  document.getElementById("modal").classList.add("hidden");
  editingId = null;
}

function renderDayPicker() {
  const container = document.getElementById("day-picker");
  container.innerHTML = DAYS.map(
    (label, i) =>
      `<button type="button" class="day-btn ${selectedDays.includes(i) ? "selected" : ""}"
        onclick="toggleDay(${i})">${label}</button>`
  ).join("");
}

function toggleDay(i) {
  if (selectedDays.includes(i)) {
    selectedDays = selectedDays.filter((d) => d !== i);
  } else {
    selectedDays = [...selectedDays, i].sort((a, b) => a - b);
  }
  renderDayPicker();
}

function toggleMenu(id) {
  const menu = document.getElementById(`menu-${id}`);
  // Close all others
  document.querySelectorAll(".dropdown.open").forEach((m) => {
    if (m !== menu) m.classList.remove("open");
  });
  menu.classList.toggle("open");
}

function closeMenu() {
  document.querySelectorAll(".dropdown.open").forEach((m) => m.classList.remove("open"));
}

function confirmDelete(id) {
  const ex = exercises.find((e) => e.id === id);
  if (!ex) return;
  closeMenu();
  if (confirm(`Удалить «${ex.name}»?`)) deleteExercise(id);
}

/* ── Form submit ────────────────────────────────────────────────────────── */
document.addEventListener("DOMContentLoaded", () => {
  document.getElementById("ex-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const durationMin = parseFloat(document.getElementById("ex-duration").value);
    const data = {
      name: document.getElementById("ex-name").value.trim(),
      description: document.getElementById("ex-desc").value.trim(),
      sets: parseInt(document.getElementById("ex-sets").value) || null,
      reps: parseInt(document.getElementById("ex-reps").value) || null,
      duration: durationMin ? Math.round(durationMin * 60) : null,
      scheduleTime: document.getElementById("ex-time").value,
      scheduleDays: selectedDays,
    };

    try {
      if (editingId) {
        await updateExercise(editingId, data);
      } else {
        await createExercise(data);
      }
      closeModal();
    } catch (e) {
      toast(e.message, "error");
    }
  });

  // Close modal on backdrop click
  document.getElementById("modal").addEventListener("click", (e) => {
    if (e.target === e.currentTarget) closeModal();
  });

  // Close menus on outside click
  document.addEventListener("click", (e) => {
    if (!e.target.closest(".card-menu")) closeMenu();
  });

  // Init
  initPush();
  loadExercises();
});

/* ── Toast ──────────────────────────────────────────────────────────────── */
function toast(msg, type = "") {
  const c = document.getElementById("toast-container");
  const t = document.createElement("div");
  t.className = `toast ${type}`;
  t.textContent = msg;
  c.appendChild(t);
  setTimeout(() => t.remove(), 3000);
}

/* ── Utils ──────────────────────────────────────────────────────────────── */
function escHtml(str) {
  return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}

/* ── Expose globals ─────────────────────────────────────────────────────── */
window.openCreate = openCreate;
window.openEdit = openEdit;
window.closeModal = closeModal;
window.toggleDay = toggleDay;
window.toggleMenu = toggleMenu;
window.confirmDelete = confirmDelete;
window.completeExercise = completeExercise;
window.toggleEnabled = toggleEnabled;
window.subscribeToPush = subscribeToPush;
window.unsubscribeFromPush = unsubscribeFromPush;
window.testPush = async () => {
  try {
    await api("/api/push/test", { method: "POST" });
    toast("Тестовый пуш отправлен!", "success");
  } catch (e) {
    toast(e.message, "error");
  }
};
