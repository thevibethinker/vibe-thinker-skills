import { useState, useEffect } from "react";
import { MapPin, Clock, Briefcase, ArrowRight, Building2 } from "lucide-react";

interface Job {
  id: string;
  title: string;
  company: string;
  location: string;
  type: string;
  posted_date: string;
  description_summary: string;
}

interface SiteConfig {
  company_name: string;
  company_tagline: string;
  careers_intro: string;
  template_mode: boolean;
}

function formatDate(dateStr: string): string {
  if (!dateStr) return "";
  try {
    const d = new Date(dateStr + "T00:00:00");
    return d.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
  } catch {
    return dateStr;
  }
}

function typeLabel(t: string): string {
  const map: Record<string, string> = {
    "full-time": "Full-time",
    "part-time": "Part-time",
    contract: "Contract",
    internship: "Internship",
  };
  return map[t] || t;
}

export default function CareersPage() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [site, setSite] = useState<SiteConfig>({
    company_name: "Template Company",
    company_tagline: "Hiring template for ZoATS installs",
    careers_intro: "Template page. Replace this copy, branding, and job data before sending candidates here.",
    template_mode: true,
  });
  const [apiError, setApiError] = useState("");

  useEffect(() => {
    fetch("/api/zoats/jobs", { headers: { Accept: "application/json" } })
      .then((r) => r.json())
      .then((data) => {
        setJobs(data.jobs || []);
        if (data.site) setSite(data.site);
        setApiError(data.error || "");
        setLoading(false);
      })
      .catch(() => {
        setError(true);
        setLoading(false);
      });
  }, []);

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100">
      <header className="border-b border-zinc-800/60">
        <div className="max-w-4xl mx-auto px-6 py-16 sm:py-24">
          {site.template_mode && (
            <div className="mb-6 inline-flex rounded-full border border-amber-400/30 bg-amber-400/10 px-3 py-1 text-xs font-semibold uppercase tracking-[0.2em] text-amber-200">
              Template page
            </div>
          )}
          <div className="flex items-center gap-3 mb-6">
            <Building2 className="w-5 h-5 text-zinc-500" />
            <span className="text-sm font-medium tracking-wide text-zinc-500 uppercase">Careers</span>
          </div>
          <h1 className="text-4xl sm:text-5xl font-bold tracking-tight text-white leading-tight">{site.company_name}</h1>
          <p className="mt-3 text-sm font-semibold uppercase tracking-[0.2em] text-zinc-500">{site.company_tagline}</p>
          <p className="mt-4 text-lg text-zinc-400 max-w-2xl leading-relaxed">
            {site.careers_intro}
          </p>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-6 py-12 sm:py-16">
        {loading && (
          <div className="flex items-center justify-center py-24">
            <div className="w-6 h-6 border-2 border-zinc-700 border-t-zinc-400 rounded-full animate-spin" />
          </div>
        )}
        {error && (
          <div className="text-center py-24">
            <p className="text-zinc-500">Something went wrong loading positions. Try refreshing.</p>
          </div>
        )}
        {!loading && !error && jobs.length === 0 && (
          <div className="text-center py-24">
            <Briefcase className="w-10 h-10 text-zinc-700 mx-auto mb-4" />
            <p className="text-zinc-400 text-lg">No open positions right now.</p>
            <p className="text-zinc-600 mt-2">
              {apiError || "Check back soon after you publish real roles to this template."}
            </p>
          </div>
        )}
        {!loading && !error && jobs.length > 0 && (
          <div className="space-y-4">
            {jobs.map((job) => (
              <a key={job.id} href={`/careers/${job.id}`}
                className="group block bg-zinc-900/50 border border-zinc-800/60 rounded-xl p-6 sm:p-7 hover:bg-zinc-900 hover:border-zinc-700/60 transition-all duration-200">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1 min-w-0">
                    <h2 className="text-xl font-semibold text-white group-hover:text-zinc-50 transition-colors">{job.title}</h2>
                    <div className="flex flex-wrap items-center gap-x-4 gap-y-2 mt-3">
                      {job.location && (<span className="flex items-center gap-1.5 text-sm text-zinc-400"><MapPin className="w-3.5 h-3.5 text-zinc-600" />{job.location}</span>)}
                      <span className="flex items-center gap-1.5 text-sm text-zinc-400"><Briefcase className="w-3.5 h-3.5 text-zinc-600" />{typeLabel(job.type)}</span>
                      {job.posted_date && (<span className="flex items-center gap-1.5 text-sm text-zinc-500"><Clock className="w-3.5 h-3.5 text-zinc-600" />{formatDate(job.posted_date)}</span>)}
                    </div>
                    {job.description_summary && (<p className="mt-3 text-sm text-zinc-500 leading-relaxed line-clamp-2">{job.description_summary}</p>)}
                  </div>
                  <div className="flex-shrink-0 mt-1">
                    <ArrowRight className="w-5 h-5 text-zinc-700 group-hover:text-zinc-400 group-hover:translate-x-0.5 transition-all duration-200" />
                  </div>
                </div>
              </a>
            ))}
          </div>
        )}
        {!loading && !error && jobs.length > 0 && (
          <p className="text-center text-sm text-zinc-600 mt-12">{jobs.length} open {jobs.length === 1 ? "position" : "positions"}</p>
        )}
      </main>

      <footer className="border-t border-zinc-800/40 mt-8">
        <div className="max-w-4xl mx-auto px-6 py-8">
          <p className="text-sm text-zinc-700 text-center">
            ZoATS template careers page. Replace branding and copy before using it live.
          </p>
        </div>
      </footer>
    </div>
  );
}
