import { appendFile, mkdir, writeFile } from "node:fs/promises";
import { spawn } from "node:child_process";
import type { Context } from "hono";

const WORKSPACE = "/home/workspace";
const INTEGRATION_DIR = `${WORKSPACE}/Personal/Integrations/krisp-meeting-blocks`;
const INCOMING_DIR = `${INTEGRATION_DIR}/incoming`;
const LOG_PATH = `${INTEGRATION_DIR}/webhook.log`;
const IMPORT_LOG_PATH = `${INTEGRATION_DIR}/importer.log`;
const IMPORT_ERR_LOG_PATH = `${INTEGRATION_DIR}/importer.err.log`;
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
  await mkdir(INTEGRATION_DIR, { recursive: true });
  await appendFile(LOG_PATH, `${JSON.stringify({ ...event, at: new Date().toISOString() })}\n`, "utf8");
}

function calendarPolicyFromEnv(): "auto" | "on" | "off" {
  const value = String(process.env.KRISP_BLOCKS_CALENDAR || "auto").trim().toLowerCase();
  return value === "on" || value === "off" ? value : "auto";
}

function spawnImporter(payloadPath: string): { pid?: number; queued: boolean; logPath: string; errLogPath: string; calendar: string } {
  const calendar = calendarPolicyFromEnv();
  const escapedPayload = payloadPath.replace(/'/g, "'\\''");
  const escapedCalendar = calendar.replace(/'/g, "'\\''");
  const command = `python3 '${SCRIPT_PATH}' import '${escapedPayload}' --process --calendar '${escapedCalendar}' >> '${IMPORT_LOG_PATH}' 2>> '${IMPORT_ERR_LOG_PATH}'`;
  const child = spawn("bash", ["-lc", command], {
    cwd: WORKSPACE,
    detached: true,
    stdio: "ignore",
  });
  void logLine({ status: "import_spawned", payloadPath, pid: child.pid, calendar, logPath: IMPORT_LOG_PATH, errLogPath: IMPORT_ERR_LOG_PATH });
  child.on("error", (error) => {
    void logLine({ status: "import_spawn_error", payloadPath, error: String(error), logPath: IMPORT_LOG_PATH, errLogPath: IMPORT_ERR_LOG_PATH });
  });
  child.unref();
  return { pid: child.pid, queued: true, logPath: IMPORT_LOG_PATH, errLogPath: IMPORT_ERR_LOG_PATH, calendar };
}

export default async function krispWebhook(c: Context) {
  if (c.req.method === "GET") {
    return c.json({ ok: true, service: "krisp-meeting-blocks-webhook", incomingDir: INCOMING_DIR, logPath: LOG_PATH, importLogPath: IMPORT_LOG_PATH });
  }

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
