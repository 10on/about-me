#!/usr/bin/env node
/**
 * Generates VAPID key pair for Web Push.
 * Run once: node scripts/generate-vapid.js
 *
 * Then set as Cloudflare Worker Secrets:
 *   wrangler secret put VAPID_PRIVATE_KEY_JWK
 *   wrangler secret put VAPID_PUBLIC_KEY
 *   wrangler secret put VAPID_SUBJECT
 */

const { webcrypto } = require("crypto");
const crypto = webcrypto;

function base64url(buf) {
  const bytes = Buffer.from(buf);
  return bytes.toString("base64").replace(/\+/g, "-").replace(/\//g, "_").replace(/=/g, "");
}

(async () => {
  const keyPair = await crypto.subtle.generateKey(
    { name: "ECDSA", namedCurve: "P-256" },
    true,
    ["sign", "verify"]
  );

  const privateJwk = await crypto.subtle.exportKey("jwk", keyPair.privateKey);
  const publicRaw = await crypto.subtle.exportKey("raw", keyPair.publicKey);

  const publicKeyBase64 = base64url(publicRaw);

  console.log("\n=== VAPID Keys ===\n");
  console.log("VAPID_PUBLIC_KEY (для wrangler.toml [vars] или CF dashboard):");
  console.log(publicKeyBase64);
  console.log("\nVAPID_PRIVATE_KEY_JWK (добавить как CF Secret):");
  console.log(JSON.stringify(privateJwk));
  console.log("\nVAPID_SUBJECT (твой email или URL):");
  console.log("mailto:your@email.com");
  console.log("\n=== Как применить ===");
  console.log("wrangler secret put VAPID_PRIVATE_KEY_JWK");
  console.log("wrangler secret put VAPID_PUBLIC_KEY");
  console.log("wrangler secret put VAPID_SUBJECT");
  console.log("\n(или через Cloudflare Dashboard → Workers → Settings → Variables)\n");
})();
