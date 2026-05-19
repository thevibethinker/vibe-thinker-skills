import { createHash, randomUUID, timingSafeEqual } from "node:crypto";
import { appendFile, mkdir, writeFile, unlink } from "node:fs/promises";
import type { Context } from "hono";

const MEMO_ID = "{{MEMO_ID}}";
const DATA_ROOT = {{DATA_ROOT_JSON}};
const SESSION_TTL_MS = 24 * 60 * 60 * 1000;

function hashStakeholderPin(email: string, pin: string) {
  return createHash("sha256").update(`${email.toLowerCase()}:${pin}`).digest("hex");
}

function hashSharedPin(memoId: string, pin: string) {
  return createHash("sha256").update(`memo:${memoId}:${pin}`).digest("hex");
}

function safeEqual(a: string, b: string) {
  if (!a || !b) return false;
  const left = Buffer.from(a);
  const right = Buffer.from(b);
  return left.length === right.length && timingSafeEqual(left, right);
}

async function readMemo() {
  const file = Bun.file(`${DATA_ROOT}/memos/${MEMO_ID}/memo.json`);
  return await file.json();
}

async function writeMemo(memo: any) {
  await writeFile(`${DATA_ROOT}/memos/${MEMO_ID}/memo.json`, JSON.stringify(memo, null, 2) + "\n");
}

export function cookieName() {
  return `smg_${MEMO_ID.replace(/-/g, "")}`;
}

export function readCookie(c: Context, name: string) {
  const cookie = c.req.header("cookie") || "";
  const part = cookie.split(";").map((item) => item.trim()).find((item) => item.startsWith(`${name}=`));
  return part ? decodeURIComponent(part.slice(name.length + 1)) : "";
}

export async function loadSession(token: string): Promise<{ email: string; created_at: string } | null> {
  if (!token || !/^[a-f0-9-]{36}$/i.test(token)) return null;
  const file = Bun.file(`${DATA_ROOT}/sessions/${MEMO_ID}/${token}.json`);
  if (!(await file.exists())) return null;
  return await file.json();
}

export async function authorizedEmail(c: Context): Promise<string | null> {
  const token = readCookie(c, cookieName());
  const session = await loadSession(token);
  if (!session) return null;
  const ageMs = Date.now() - Date.parse(session.created_at);
  if (Number.isNaN(ageMs) || ageMs > SESSION_TTL_MS) return null;
  const memo = await readMemo();
  const stakeholder = memo.stakeholders?.find((item: any) => item.email === session.email);
  if (!stakeholder) return null;
  if (stakeholder.status === "blocked" || stakeholder.status === "revoked") return null;
  if (stakeholder.session_revoked_at && Date.parse(stakeholder.session_revoked_at) >= Date.parse(session.created_at)) {
    return null;
  }
  if (memo.auth_mode === "whitelist-only" || memo.auth_mode === "email+pin") {
    if (stakeholder.status !== "approved") return null;
  }
  return session.email;
}

async function createSession(email: string) {
  const token = randomUUID();
  const dir = `${DATA_ROOT}/sessions/${MEMO_ID}`;
  await mkdir(dir, { recursive: true });
  await writeFile(`${dir}/${token}.json`, JSON.stringify({ email, created_at: new Date().toISOString() }, null, 2) + "\n");
  return token;
}

async function captureCandidate(memo: any, email: string) {
  const existing = memo.stakeholders?.find((item: any) => item.email === email);
  if (existing) {
    if (existing.status === "blocked" || existing.status === "revoked") return existing.status;
    return existing.status;
  }
  memo.stakeholders = memo.stakeholders || [];
  memo.stakeholders.push({
    email,
    name: "",
    org: "",
    role: "",
    status: "candidate",
    locale: "en-US",
    version_id: memo.default_version_id,
    pin_hash: "",
    pin_updated_at: null,
    session_revoked_at: null,
    custom_fields: {},
  });
  memo.updated_at = new Date().toISOString();
  await writeMemo(memo);
  return "candidate";
}

async function appendAuthEvent(event: string, email: string, ok: boolean) {
  try {
    await mkdir(`${DATA_ROOT}/analytics`, { recursive: true });
    const path = `${DATA_ROOT}/analytics/${MEMO_ID}.jsonl`;
    const payload = { ts: new Date().toISOString(), memo_id: MEMO_ID, event, details: { email, ok } };
    await appendFile(path, JSON.stringify(payload) + "\n");
  } catch {
    // analytics best-effort
  }
}

function isLogout(path: string) {
  return path.endsWith("/logout");
}

function isSession(path: string) {
  return path.endsWith("/session");
}

export default async function auth(c: Context) {
  const path = c.req.path;
  const memo = await readMemo();

  if (isSession(path)) {
    const email = await authorizedEmail(c);
    return c.json({ authorized: Boolean(email), email });
  }

  if (isLogout(path)) {
    const token = readCookie(c, cookieName());
    if (token && /^[a-f0-9-]{36}$/i.test(token)) {
      try { await unlink(`${DATA_ROOT}/sessions/${MEMO_ID}/${token}.json`); } catch { /* noop */ }
    }
    const headers = new Headers();
    headers.append("Set-Cookie", `${cookieName()}=; HttpOnly; Secure; SameSite=Lax; Path=/; Max-Age=0`);
    return c.json({ ok: true }, 200, headers);
  }

  // login
  const body = await c.req.json().catch(() => ({}));
  const email = String(body.email || "").trim().toLowerCase();
  const pin = String(body.pin || "").trim();

  if (!email || !/^.+@.+\..+$/.test(email) || !/^\d{4}$/.test(pin)) {
    await appendAuthEvent("auth_attempt", email, false);
    return c.json({ error: "Email and 4-digit PIN required." }, 400);
  }

  const stakeholder = memo.stakeholders?.find((item: any) => item.email === email);

  if (stakeholder && (stakeholder.status === "blocked" || stakeholder.status === "revoked")) {
    await appendAuthEvent("auth_attempt", email, false);
    return c.json({ error: "Access has been revoked." }, 401);
  }

  let approved = false;
  let candidateCaptured = false;

  if (memo.auth_mode === "whitelist-only") {
    approved = !!(stakeholder && stakeholder.status === "approved" && safeEqual(stakeholder.pin_hash, hashStakeholderPin(email, pin)));
  } else if (memo.auth_mode === "email+pin") {
    approved = !!(stakeholder && stakeholder.status === "approved" && safeEqual(stakeholder.pin_hash, hashStakeholderPin(email, pin)));
  } else if (memo.auth_mode === "pin-only-with-email-capture") {
    if (memo.shared_pin_hash && safeEqual(memo.shared_pin_hash, hashSharedPin(MEMO_ID, pin))) {
      approved = true;
      const status = await captureCandidate(memo, email);
      candidateCaptured = status === "candidate";
    } else if (stakeholder && stakeholder.status === "approved" && safeEqual(stakeholder.pin_hash, hashStakeholderPin(email, pin))) {
      approved = true;
    }
  }

  if (!approved) {
    await appendAuthEvent("auth_attempt", email, false);
    return c.json({ error: "Unauthorized" }, 401);
  }

  const token = await createSession(email);
  const headers = new Headers();
  headers.append("Set-Cookie", `${cookieName()}=${encodeURIComponent(token)}; HttpOnly; Secure; SameSite=Lax; Path=/; Max-Age=${SESSION_TTL_MS / 1000}`);
  await appendAuthEvent("auth_attempt", email, true);
  if (candidateCaptured) await appendAuthEvent("candidate_capture", email, true);
  return c.json({ authorized: true, email }, 200, headers);
}
