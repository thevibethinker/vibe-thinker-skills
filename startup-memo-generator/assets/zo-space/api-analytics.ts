import { appendFile, mkdir } from "node:fs/promises";
import { timingSafeEqual } from "node:crypto";
import type { Context } from "hono";

const MEMO_ID = "{{MEMO_ID}}";
const DATA_ROOT = {{DATA_ROOT_JSON}};
const SESSION_TTL_MS = 24 * 60 * 60 * 1000;

function cookieName() {
  return `smg_${MEMO_ID.replace(/-/g, "")}`;
}

function readCookie(c: Context, name: string) {
  const cookie = c.req.header("cookie") || "";
  const part = cookie.split(";").map((item) => item.trim()).find((item) => item.startsWith(`${name}=`));
  return part ? decodeURIComponent(part.slice(name.length + 1)) : "";
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

async function authorizedEmail(c: Context): Promise<string | null> {
  const token = readCookie(c, cookieName());
  if (!token || !/^[a-f0-9-]{36}$/i.test(token)) return null;
  const sessionFile = Bun.file(`${DATA_ROOT}/sessions/${MEMO_ID}/${token}.json`);
  if (!(await sessionFile.exists())) return null;
  const session = await sessionFile.json();
  const ageMs = Date.now() - Date.parse(session.created_at);
  if (Number.isNaN(ageMs) || ageMs > SESSION_TTL_MS) return null;
  const memo = await readMemo();
  const stakeholder = memo.stakeholders?.find((item: any) => item.email === session.email);
  if (!stakeholder) return null;
  if (stakeholder.status === "blocked" || stakeholder.status === "revoked") return null;
  if (stakeholder.session_revoked_at && Date.parse(stakeholder.session_revoked_at) >= Date.parse(session.created_at)) return null;
  if ((memo.auth_mode === "whitelist-only" || memo.auth_mode === "email+pin") && stakeholder.status !== "approved") return null;
  return session.email;
}

function adminAuthorized(c: Context): boolean {
  const expected = process.env.MEMO_ADMIN_TOKEN || "";
  if (!expected) return false;
  const header = c.req.header("authorization") || "";
  const match = header.match(/^Bearer\s+(.+)$/i);
  if (!match) return false;
  return safeEqual(match[1].trim(), expected);
}

async function appendEvent(payload: Record<string, unknown>) {
  await mkdir(`${DATA_ROOT}/analytics`, { recursive: true });
  const path = `${DATA_ROOT}/analytics/${MEMO_ID}.jsonl`;
  await appendFile(path, JSON.stringify(payload) + "\n");
}

async function summary() {
  const file = Bun.file(`${DATA_ROOT}/analytics/${MEMO_ID}.jsonl`);
  if (!(await file.exists())) return {};
  const text = await file.text();
  const counts: Record<string, number> = {};
  for (const line of text.split(/\n/)) {
    if (!line.trim()) continue;
    try {
      const event = JSON.parse(line);
      const name = event.event || "unknown";
      counts[name] = (counts[name] || 0) + 1;
    } catch {
      // skip malformed line
    }
  }
  return counts;
}

export default async function analytics(c: Context) {
  const isSummary = c.req.method === "GET" || c.req.path.endsWith("/summary");

  if (isSummary) {
    if (!adminAuthorized(c)) return c.json({ error: "Unauthorized" }, 401);
    return c.json({ memo_id: MEMO_ID, event_counts: await summary() });
  }

  const email = await authorizedEmail(c);
  if (!email) return c.json({ error: "Unauthorized" }, 401);

  const body = await c.req.json().catch(() => ({}));
  await appendEvent({
    ts: new Date().toISOString(),
    memo_id: MEMO_ID,
    email,
    event: body.event || "unknown",
    details: body.details || {},
    user_agent: c.req.header("user-agent") || "",
  });
  return c.json({ ok: true });
}
