import type { Context } from "hono";
import { access, mkdir, writeFile } from "node:fs/promises";
import { join } from "node:path";
import { spawn } from "node:child_process";

const ZOATS_HOME = process.env.ZOATS_HOME || "/home/workspace/ZoATS";
const JOBS_DIR = join(ZOATS_HOME, "jobs");
const INBOX_DIR = join(ZOATS_HOME, "inbox_drop");
const INTAKE_SCRIPT = join(ZOATS_HOME, "scripts", "intake_trigger.py");
const ALLOWED_EXTS = new Set([".pdf", ".docx", ".doc", ".txt", ".md"]);
const MAX_SIZE = 10 * 1024 * 1024;

export default async (c: Context) => {
  try {
    const contentType = c.req.header("content-type") || "";
    let name: string | null = null;
    let email: string | null = null;
    let phone = "";
    let coverNote = "";
    let jobId = "unknown";
    let file: File | null = null;
    let resumeText: string | null = null;

    if (contentType.includes("multipart/form-data")) {
      const formData = await c.req.formData();
      name = formData.get("name") as string | null;
      email = formData.get("email") as string | null;
      phone = (formData.get("phone") as string) || "";
      coverNote = (formData.get("cover_note") as string) || "";
      jobId = (formData.get("job_id") as string) || "unknown";
      file = formData.get("resume") as File | null;
    } else if (contentType.includes("application/json")) {
      const body = await c.req.json();
      name = body.name || null;
      email = body.email || null;
      phone = body.phone || "";
      coverNote = body.cover_note || "";
      jobId = body.job_id || body.jobId || "unknown";
      resumeText = body.resume || null;
    } else {
      return c.json({ success: false, errors: ["Content-Type must be multipart/form-data or application/json"] }, 400);
    }

    try {
      await access(join(JOBS_DIR, jobId, "metadata.json"));
      await access(INTAKE_SCRIPT);
    } catch {
      return c.json({ success: false, errors: ["ZoATS is not fully configured for applications yet. Finish the local install and deploy the template pages again."] }, 503);
    }

    const errors: string[] = [];
    if (!name?.trim()) errors.push("Name is required");
    if (!email?.trim()) errors.push("Email is required");
    if (!file && !resumeText) errors.push("Resume is required (file upload or text)");

    if (file) {
      const ext = "." + file.name.split(".").pop()?.toLowerCase();
      if (!ALLOWED_EXTS.has(ext)) {
        errors.push(`File type not allowed: ${ext}. Accepted: .pdf, .docx, .doc, .txt, .md`);
      }
      if (file.size > MAX_SIZE) {
        errors.push(`File too large (${(file.size / 1024 / 1024).toFixed(1)}MB). Max: 10MB`);
      }
    }

    if (errors.length > 0) {
      return c.json({ success: false, errors }, 400);
    }

    const ts = new Date().toISOString().replace(/[:.]/g, "-").slice(0, 19);
    const safeName = name!.trim().toLowerCase().replace(/[^a-z0-9]+/g, "-").slice(0, 30);
    const folderName = `${ts}--${safeName}`;
    const submissionDir = join(INBOX_DIR, folderName);
    const rawDir = join(submissionDir, "raw");
    await mkdir(rawDir, { recursive: true });

    if (file) {
      const ext = file.name.split(".").pop()?.toLowerCase() || "pdf";
      const resumePath = join(rawDir, `resume.${ext}`);
      const buffer = Buffer.from(await file.arrayBuffer());
      await writeFile(resumePath, buffer);
    } else if (resumeText) {
      await writeFile(join(rawDir, "resume.txt"), resumeText);
    }

    const submission = {
      name: name!.trim(),
      email: email!.trim(),
      phone: phone.trim(),
      cover_note: coverNote.trim(),
      job_id: jobId,
      submitted_at: new Date().toISOString(),
      resume_filename: file ? file.name : "resume.txt",
      resume_size: file ? file.size : (resumeText?.length || 0),
    };
    await writeFile(join(submissionDir, "submission.json"), JSON.stringify(submission, null, 2));

    console.log(`[zoats/apply] New application: ${name} for ${jobId} → ${folderName}`);

    try {
      const child = spawn("python3", [INTAKE_SCRIPT, "--once"], {
        stdio: "ignore",
        detached: true,
        env: { ...process.env, ZOATS_HOME },
      });
      child.unref();
      console.log(`[zoats/apply] Intake trigger fired (pid ${child.pid})`);
    } catch (triggerErr) {
      console.warn("[zoats/apply] Intake trigger failed (non-fatal):", triggerErr);
    }

    return c.json({ success: true, message: "Application received successfully", submission_id: folderName });
  } catch (err) {
    console.error("[zoats/apply] Error processing application:", err);
    return c.json({ success: false, errors: ["Internal error processing your application"] }, 500);
  }
};
