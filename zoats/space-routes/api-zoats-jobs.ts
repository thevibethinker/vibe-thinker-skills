import type { Context } from "hono";
import { readdir, readFile } from "node:fs/promises";
import { join } from "node:path";

const ZOATS_HOME = process.env.ZOATS_HOME || "/home/workspace/ZoATS";
const JOBS_DIR = join(ZOATS_HOME, "jobs");
const SETTINGS_PATH = join(ZOATS_HOME, "config", "settings.json");

interface JobListing {
  id: string;
  title: string;
  company: string;
  location: string;
  type: string;
  posted_date: string;
  status: string;
  description_summary: string;
}

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

function shouldList(status: unknown): boolean {
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
  const site = await loadSiteConfig();
  try {
    const entries = await readdir(JOBS_DIR, { withFileTypes: true });
    const jobs: JobListing[] = [];

    for (const entry of entries) {
      if (!entry.isDirectory()) continue;
      const jobId = entry.name;
      const metaPath = join(JOBS_DIR, jobId, "metadata.json");

      try {
        const raw = await readFile(metaPath, "utf-8");
        const meta = JSON.parse(raw);

        if (!shouldList(meta.status)) continue;

        let summary = meta.description_summary || "";
        if (!summary) {
          try {
            const jd = await readFile(join(JOBS_DIR, jobId, "job-description.md"), "utf-8");
            summary = jd.slice(0, 200).replace(/[#*\n]/g, " ").trim();
          } catch {}
        }

        jobs.push({
          id: jobId,
          title: meta.title || "Untitled Position",
          company: meta.company || "",
          location: meta.location || "Not specified",
          type: meta.type || "full-time",
          posted_date: meta.posted_date || "",
          status: normalizeStatus(meta.status),
          description_summary: summary,
        });
      } catch {
        console.warn(`[zoats/jobs] Skipping ${jobId}: missing or invalid metadata.json`);
      }
    }

    jobs.sort((a, b) => (b.posted_date || "").localeCompare(a.posted_date || ""));

    return c.json({ jobs, total: jobs.length, site });
  } catch (err) {
    console.error("[zoats/jobs] Error reading jobs directory:", err);
    return c.json({ jobs: [], total: 0, site, error: "Jobs directory not found" });
  }
};
