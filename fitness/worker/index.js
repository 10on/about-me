/**
 * Fitness App — Cloudflare Worker
 *
 * Routes:
 *   GET    /api/exercises
 *   POST   /api/exercises
 *   PUT    /api/exercises/:id
 *   DELETE /api/exercises/:id
 *   POST   /api/exercises/:id/complete
 *
 *   GET    /api/push/publickey
 *   POST   /api/push/subscribe
 *   DELETE /api/push/subscribe
 *   POST   /api/push/test
 *
 * Cron:  scheduled() — sends push reminders per schedule
 */

// ─── CORS helpers ────────────────────────────────────────────────────────────

function corsHeaders(env) {
  return {
    "Access-Control-Allow-Origin": env.FRONTEND_URL || "*",
    "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
  };
}

function json(data, status = 200, env = {}) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { "Content-Type": "application/json", ...corsHeaders(env) },
  });
}

function err(msg, status = 400, env = {}) {
  return json({ error: msg }, status, env);
}

// ─── KV helpers ──────────────────────────────────────────────────────────────

async function kvGet(kv, key, fallback = null) {
  const val = await kv.get(key, "json");
  return val ?? fallback;
}

async function kvSet(kv, key, value) {
  await kv.put(key, JSON.stringify(value));
}

// ─── UUID ─────────────────────────────────────────────────────────────────────

function uuid() {
  return crypto.randomUUID();
}

// ─── base64url helpers ───────────────────────────────────────────────────────

function base64urlFromBuffer(buf) {
  const bytes = new Uint8Array(buf);
  let str = "";
  for (const b of bytes) str += String.fromCharCode(b);
  return btoa(str).replace(/\+/g, "-").replace(/\//g, "_").replace(/=/g, "");
}

function bufferFromBase64url(b64) {
  const b64std = b64.replace(/-/g, "+").replace(/_/g, "/");
  const pad = b64std.length % 4 === 0 ? "" : "=".repeat(4 - (b64std.length % 4));
  const binary = atob(b64std + pad);
  const buf = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) buf[i] = binary.charCodeAt(i);
  return buf.buffer;
}

// ─── VAPID JWT signing ────────────────────────────────────────────────────────

async function buildVapidJwt(audience, subject, privateKeyJwk) {
  const header = base64urlFromBuffer(new TextEncoder().encode(JSON.stringify({ typ: "JWT", alg: "ES256" })));
  const payload = base64urlFromBuffer(
    new TextEncoder().encode(
      JSON.stringify({
        aud: audience,
        exp: Math.floor(Date.now() / 1000) + 43200, // 12h
        sub: subject,
      })
    )
  );

  const signingInput = `${header}.${payload}`;

  const key = await crypto.subtle.importKey(
    "jwk",
    privateKeyJwk,
    { name: "ECDSA", namedCurve: "P-256" },
    false,
    ["sign"]
  );

  const sig = await crypto.subtle.sign(
    { name: "ECDSA", hash: "SHA-256" },
    key,
    new TextEncoder().encode(signingInput)
  );

  return `${signingInput}.${base64urlFromBuffer(sig)}`;
}

// ─── Web Push encryption (RFC 8291 / RFC 8188) ───────────────────────────────
// Sends an encrypted push notification payload.
// subscription: { endpoint, keys: { p256dh, auth } }

async function encryptPushPayload(subscription, plaintext) {
  const { p256dh, auth } = subscription.keys;

  // Receiver public key
  const receiverPublicKeyBuf = bufferFromBase64url(p256dh);
  const authSecretBuf = bufferFromBase64url(auth);

  // Generate ephemeral ECDH key pair
  const senderKeyPair = await crypto.subtle.generateKey(
    { name: "ECDH", namedCurve: "P-256" },
    true,
    ["deriveKey", "deriveBits"]
  );

  const senderPublicKeyRaw = await crypto.subtle.exportKey("raw", senderKeyPair.publicKey);

  // Import receiver public key
  const receiverKey = await crypto.subtle.importKey(
    "raw",
    receiverPublicKeyBuf,
    { name: "ECDH", namedCurve: "P-256" },
    false,
    []
  );

  // ECDH shared secret
  const sharedBits = await crypto.subtle.deriveBits(
    { name: "ECDH", public: receiverKey },
    senderKeyPair.privateKey,
    256
  );

  // salt (16 random bytes)
  const salt = crypto.getRandomValues(new Uint8Array(16));

  // HKDF to derive content encryption key & nonce (RFC 8291 §3.3)
  const encoder = new TextEncoder();

  async function hkdf(ikm, saltBuf, info, length) {
    const ikmKey = await crypto.subtle.importKey("raw", ikm, "HKDF", false, ["deriveBits"]);
    return crypto.subtle.deriveBits({ name: "HKDF", hash: "SHA-256", salt: saltBuf, info }, ikmKey, length * 8);
  }

  // PRK (pseudo-random key)
  const prkInfo = concat(encoder.encode("WebPush: info\0"), receiverPublicKeyBuf, senderPublicKeyRaw);
  const prk = await hkdf(sharedBits, authSecretBuf, prkInfo, 32);

  const cekInfo = encoder.encode("Content-Encoding: aes128gcm\0");
  const nonceInfo = encoder.encode("Content-Encoding: nonce\0");

  const cek = await hkdf(prk, salt, cekInfo, 16);
  const nonce = await hkdf(prk, salt, nonceInfo, 12);

  // Import CEK
  const aesKey = await crypto.subtle.importKey("raw", cek, "AES-GCM", false, ["encrypt"]);

  // Pad and encrypt (RFC 8188 record)
  const plaintextBuf = encoder.encode(plaintext);
  const padded = new Uint8Array(plaintextBuf.length + 1 + 1); // +1 for delimiter, at least 1 byte pad
  padded.set(plaintextBuf);
  padded[plaintextBuf.length] = 2; // record delimiter

  const ciphertext = await crypto.subtle.encrypt(
    { name: "AES-GCM", iv: nonce },
    aesKey,
    padded
  );

  // RFC 8188 header: salt(16) + rs(4) + idlen(1) + sender_pub(65)
  const rs = new Uint8Array(4);
  new DataView(rs.buffer).setUint32(0, 4096, false); // record size = 4096
  const idlen = new Uint8Array([65]);

  const header = concat(salt, rs, idlen, new Uint8Array(senderPublicKeyRaw));
  const body = concat(header, new Uint8Array(ciphertext));

  return { body, salt };
}

function concat(...arrays) {
  const total = arrays.reduce((n, a) => n + a.byteLength, 0);
  const out = new Uint8Array(total);
  let offset = 0;
  for (const a of arrays) {
    out.set(new Uint8Array(a instanceof ArrayBuffer ? a : a.buffer ?? a), offset);
    offset += a.byteLength ?? a.length;
  }
  return out;
}

// ─── Send one push notification ───────────────────────────────────────────────

async function sendPush(subscription, payload, env) {
  if (!env.VAPID_PRIVATE_KEY_JWK || !env.VAPID_PUBLIC_KEY || !env.VAPID_SUBJECT) {
    console.error("VAPID env vars not set");
    return false;
  }

  let privateKeyJwk;
  try {
    privateKeyJwk = JSON.parse(env.VAPID_PRIVATE_KEY_JWK);
  } catch {
    console.error("Invalid VAPID_PRIVATE_KEY_JWK");
    return false;
  }

  const url = new URL(subscription.endpoint);
  const audience = `${url.protocol}//${url.host}`;

  const jwt = await buildVapidJwt(audience, env.VAPID_SUBJECT, privateKeyJwk);
  const vapidHeader = `vapid t=${jwt},k=${env.VAPID_PUBLIC_KEY}`;

  let body, contentEncoding;

  if (payload && subscription.keys) {
    try {
      const { body: enc } = await encryptPushPayload(subscription, payload);
      body = enc;
      contentEncoding = "aes128gcm";
    } catch (e) {
      console.error("Encryption failed:", e);
      // fallback: send without payload
      body = null;
    }
  }

  const headers = {
    Authorization: vapidHeader,
    TTL: "86400",
  };

  if (body) {
    headers["Content-Type"] = "application/octet-stream";
    headers["Content-Encoding"] = contentEncoding;
  }

  try {
    const res = await fetch(subscription.endpoint, {
      method: "POST",
      headers,
      body: body ?? null,
    });

    if (res.status === 410 || res.status === 404) {
      // Subscription expired — caller should remove it
      return "expired";
    }

    return res.ok;
  } catch (e) {
    console.error("Push send error:", e);
    return false;
  }
}

// ─── Send push to all subscribers ────────────────────────────────────────────

async function broadcastPush(payload, env) {
  const subscriptions = await kvGet(env.FITNESS_KV, "subscriptions", []);
  const alive = [];

  for (const sub of subscriptions) {
    const result = await sendPush(sub, payload, env);
    if (result !== "expired") alive.push(sub);
  }

  if (alive.length !== subscriptions.length) {
    await kvSet(env.FITNESS_KV, "subscriptions", alive);
  }
}

// ─── Cron: send daily reminders ───────────────────────────────────────────────

async function handleCron(env) {
  const exercises = await kvGet(env.FITNESS_KV, "exercises", []);
  const enabled = exercises.filter((e) => e.enabled !== false);

  if (!enabled.length) return;

  const names = enabled
    .slice(0, 3)
    .map((e) => e.name)
    .join(", ");
  const more = enabled.length > 3 ? ` (+${enabled.length - 3} ещё)` : "";

  const payload = JSON.stringify({
    title: "💪 Время тренироваться!",
    body: `${names}${more}`,
    url: env.FRONTEND_URL || "/",
  });

  await broadcastPush(payload, env);
}

// ─── Request router ───────────────────────────────────────────────────────────

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const path = url.pathname;
    const method = request.method;

    // Preflight
    if (method === "OPTIONS") {
      return new Response(null, { status: 204, headers: corsHeaders(env) });
    }

    // ── Exercises ──────────────────────────────────────────────────────────

    if (path === "/api/exercises" && method === "GET") {
      const exercises = await kvGet(env.FITNESS_KV, "exercises", []);
      return json(exercises, 200, env);
    }

    if (path === "/api/exercises" && method === "POST") {
      let body;
      try {
        body = await request.json();
      } catch {
        return err("Invalid JSON", 400, env);
      }
      if (!body.name?.trim()) return err("name is required", 400, env);

      const exercise = {
        id: uuid(),
        name: body.name.trim(),
        description: body.description || "",
        sets: body.sets || null,
        reps: body.reps || null,
        duration: body.duration || null,        // seconds
        scheduleDays: body.scheduleDays || [1, 2, 3, 4, 5], // 0=Sun…6=Sat
        scheduleTime: body.scheduleTime || "09:00",
        enabled: true,
        createdAt: new Date().toISOString(),
        lastCompleted: null,
        completions: 0,
      };

      const exercises = await kvGet(env.FITNESS_KV, "exercises", []);
      exercises.push(exercise);
      await kvSet(env.FITNESS_KV, "exercises", exercises);
      return json(exercise, 201, env);
    }

    const exerciseMatch = path.match(/^\/api\/exercises\/([^/]+)$/);
    if (exerciseMatch) {
      const id = exerciseMatch[1];

      if (method === "PUT") {
        let body;
        try {
          body = await request.json();
        } catch {
          return err("Invalid JSON", 400, env);
        }
        const exercises = await kvGet(env.FITNESS_KV, "exercises", []);
        const idx = exercises.findIndex((e) => e.id === id);
        if (idx === -1) return err("Not found", 404, env);

        exercises[idx] = { ...exercises[idx], ...body, id };
        await kvSet(env.FITNESS_KV, "exercises", exercises);
        return json(exercises[idx], 200, env);
      }

      if (method === "DELETE") {
        const exercises = await kvGet(env.FITNESS_KV, "exercises", []);
        const filtered = exercises.filter((e) => e.id !== id);
        if (filtered.length === exercises.length) return err("Not found", 404, env);
        await kvSet(env.FITNESS_KV, "exercises", filtered);
        return json({ ok: true }, 200, env);
      }
    }

    const completeMatch = path.match(/^\/api\/exercises\/([^/]+)\/complete$/);
    if (completeMatch && method === "POST") {
      const id = completeMatch[1];
      const exercises = await kvGet(env.FITNESS_KV, "exercises", []);
      const idx = exercises.findIndex((e) => e.id === id);
      if (idx === -1) return err("Not found", 404, env);

      exercises[idx].lastCompleted = new Date().toISOString();
      exercises[idx].completions = (exercises[idx].completions || 0) + 1;
      await kvSet(env.FITNESS_KV, "exercises", exercises);
      return json(exercises[idx], 200, env);
    }

    // ── Push subscriptions ─────────────────────────────────────────────────

    if (path === "/api/push/publickey" && method === "GET") {
      const key = env.VAPID_PUBLIC_KEY;
      if (!key) return err("VAPID not configured", 503, env);
      return json({ publicKey: key }, 200, env);
    }

    if (path === "/api/push/subscribe" && method === "POST") {
      let sub;
      try {
        sub = await request.json();
      } catch {
        return err("Invalid JSON", 400, env);
      }
      if (!sub.endpoint) return err("endpoint required", 400, env);

      const subscriptions = await kvGet(env.FITNESS_KV, "subscriptions", []);
      const exists = subscriptions.find((s) => s.endpoint === sub.endpoint);
      if (!exists) {
        subscriptions.push(sub);
        await kvSet(env.FITNESS_KV, "subscriptions", subscriptions);
      }
      return json({ ok: true }, 201, env);
    }

    if (path === "/api/push/subscribe" && method === "DELETE") {
      let body;
      try {
        body = await request.json();
      } catch {
        return err("Invalid JSON", 400, env);
      }
      const subscriptions = await kvGet(env.FITNESS_KV, "subscriptions", []);
      const filtered = subscriptions.filter((s) => s.endpoint !== body.endpoint);
      await kvSet(env.FITNESS_KV, "subscriptions", filtered);
      return json({ ok: true }, 200, env);
    }

    if (path === "/api/push/test" && method === "POST") {
      const payload = JSON.stringify({
        title: "💪 Тест работает!",
        body: "Пуши настроены правильно. Пора качать яйца.",
        url: env.FRONTEND_URL || "/",
      });
      await broadcastPush(payload, env);
      return json({ ok: true }, 200, env);
    }

    return json({ error: "Not found" }, 404, env);
  },

  async scheduled(event, env) {
    await handleCron(env);
  },
};
