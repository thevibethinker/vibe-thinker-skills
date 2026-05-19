import { mkdir, writeFile } from "node:fs/promises";
import { randomUUID, timingSafeEqual } from "node:crypto";
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

async function selectVersionId(memo: any, email: string): Promise<string> {
  const stakeholder = memo.stakeholders?.find((item: any) => item.email === email);
  return (stakeholder && stakeholder.version_id) || memo.default_version_id;
}

async function loadSourceText(memo: any, versionId: string): Promise<string> {
  const version = memo.versions?.find((item: any) => item.id === versionId) || memo.versions?.[0];
  if (!version || !version.source_snapshot_id) return "";
  const file = Bun.file(`${DATA_ROOT}/sources/${version.source_snapshot_id}/source.txt`);
  if (!(await file.exists())) return "";
  return await file.text();
}

function toSections(text: string) {
  return text
    .split(/\n{2,}/)
    .map((body, index) => ({ id: `section-${index + 1}`, body: body.trim() }))
    .filter((section) => section.body.length > 0);
}

export default async function content(c: Context) {
  const email = await authorizedEmail(c);
  if (!email) {
    return c.json({ error: "Unauthorized" }, 401);
  }
  const memo = await readMemo();
  const versionId = await selectVersionId(memo, email);
  const sourceText = await loadSourceText(memo, versionId);
  return c.json({
    memo_id: memo.id,
    title: memo.title,
    version_id: versionId,
    sections: toSections(sourceText),
  });
}
