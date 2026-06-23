import { appendFile, mkdir, writeFile } from "node:fs/promises";
import { spawn } from "node:child_process";
import type { Context } from "hono";

const WORKSPACE = "/home/workspace";
const INCOMING_DIR = `${WORKSPACE}/Personal/Integrations/krisp-meeting-blocks/incoming`;
const LOG_PATH = `${WORKSPACE}/Personal/Integrations/krisp-meeting-blocks/webhook.log`;
const SCRIPT_PATH = `${WORKSPACE}/Skills/krisp-meeting-blocks/scripts/krisp_blocks.py`;

function safePart(value: unknown, fallback: string): string {
  const raw = String(value || fallback).trim();
  return raw.replace(/[^a-zA-Z0-9._-]+/g, "-").replace(/^-+|-+$/g, "").slice(0, 96) || fallback;
}

function constantTimeEqual(a: string, b: string): boolean {
  const left = Buffer.from(a);
  const right = Buffer.from(b);
  if (left.length !== right.length) return false;
  let diff = 0;
  for (let i = 0; i < left.length; i += 1) diff |= left[i] ^ right[i];
  return diff === 0;
}

function authorized(c: Context): boolean {
  const secret = process.env.KRISP_WEBHOOK_SECRET;
  if (!secret) return false;
  const auth = c.req.header("authorization") || "";
  if (!auth.startsWith("Bearer ")) return false;
  return constantTimeEqual(auth.slice(7), secret);
}

async function logLine(event: Record<string, unknown>): Promise<void> {
  await mkdir(INCOMING_DIR, { recursive: true });
  await appendFile(LOG_PATH, `${JSON.stringify({ ...event, at: new Date().toISOString() })}\n`, "utf8");
}

function spawnImporter(payloadPath: string): { pid?: number; queued: boolean } {
  const child = spawn("python3", [SCRIPT_PATH, "import", payloadPath, "--process"], {
    cwd: WORKSPACE,
    detached: true,
    stdio: "ignore",
  });
  child.unref();
  return { pid: child.pid, queued: true };
}

export default async function krispWebhook(c: Context) {
  if (!authorized(c)) {
    await logLine({ status: "unauthorized", ip: c.req.header("x-forwarded-for") || null });
    return c.json({ error: "Unauthorized" }, 401);
  }

  let payload: any;
  try {
    payload = await c.req.json();
  } catch (error) {
    await logLine({ status: "bad_json", error: String(error) });
    return c.json({ error: "Invalid JSON" }, 400);
  }

  const eventType = payload?.event_type || payload?.type || payload?.event || "event";
  const data = payload?.data && typeof payload.data === "object" ? payload.data : {};
  const meeting = data?.meeting && typeof data.meeting === "object" ? data.meeting : {};
  const meetingId = safePart(meeting?.id || data?.meeting_id || payload?.meeting_id, "meeting");
  const eventId = safePart(payload?.event_id || payload?.id, crypto.randomUUID());
  const timestamp = new Date().toISOString().replace(/[:.]/g, "-");
  const payloadPath = `${INCOMING_DIR}/${timestamp}__${safePart(eventType, "event")}__${meetingId}__${eventId}.json`;

  await mkdir(INCOMING_DIR, { recursive: true });
  await writeFile(payloadPath, JSON.stringify(payload, null, 2), "utf8");

  const importRun = eventType === "transcript_created" ? spawnImporter(payloadPath) : { queued: false };
  await logLine({ status: "received", eventType, meetingId, eventId, payloadPath, importRun });

  return c.json({ ok: true, eventType, meetingId, eventId, payloadPath, importRun });
}
