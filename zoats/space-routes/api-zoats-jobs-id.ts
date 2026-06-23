import type { Context } from "hono";
import { readFile } from "node:fs/promises";
import { join } from "node:path";

const ZOATS_HOME = process.env.ZOATS_HOME || "/home/workspace/ZoATS";
const JOBS_DIR = join(ZOATS_HOME, "jobs");
const SETTINGS_PATH = join(ZOATS_HOME, "config", "settings.json");

interface SiteConfig {
  company_name: string;
  company_tagline: string;
  careers_intro: string;
  template_mode: boolean;
}

function normalizeStatus(status: unknown): string {
  if (status === "active") return "open";
  if (status === "paused") return "on_hold";
  return typeof status === "string" ? status : "draft";
}

function isPublicJob(status: unknown): boolean {
  return normalizeStatus(status) === "open";
}

async function loadSiteConfig(): Promise<SiteConfig> {
  try {
    const raw = await readFile(SETTINGS_PATH, "utf-8");
    const data = JSON.parse(raw);
    return {
      company_name: data.company_name || "Template Company",
      company_tagline: data.company_tagline || "Hiring template for ZoATS installs",
      careers_intro:
        data.careers_intro ||
        "Template page. Replace this copy, branding, and job data before sending candidates here.",
      template_mode: data.template_mode !== false,
    };
  } catch {
    return {
      company_name: "Template Company",
      company_tagline: "Hiring template for ZoATS installs",
      careers_intro:
        "Template page. Replace this copy, branding, and job data before sending candidates here.",
      template_mode: true,
    };
  }
}

export default async (c: Context) => {
  const id = c.req.param("id");
  if (!id) return c.json({ error: "Job ID required" }, 400);
  const site = await loadSiteConfig();

  const jobDir = join(JOBS_DIR, id);
  const metaPath = join(jobDir, "metadata.json");

  try {
    const raw = await readFile(metaPath, "utf-8");
    const meta = JSON.parse(raw);

    if (!isPublicJob(meta.status)) {
      return c.json({ error: "Position not found" }, 404);
    }

    let description = "";
    try {
      description = await readFile(join(jobDir, "job-description.md"), "utf-8");
    } catch {}

    return c.json({
      id,
      title: meta.title || "Untitled Position",
      company: meta.company || "",
      location: meta.location || "Not specified",
      type: meta.type || "full-time",
      posted_date: meta.posted_date || "",
      status: normalizeStatus(meta.status),
      description_summary: meta.description_summary || "",
      description,
      site,
    });
  } catch {
    return c.json({ error: "Position not found" }, 404);
  }
};
