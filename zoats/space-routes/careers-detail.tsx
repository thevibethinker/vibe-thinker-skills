import { useState, useEffect } from "react";
import { useParams, Link } from "react-router-dom";
import { ArrowLeft, MapPin, Briefcase, Clock, ExternalLink } from "lucide-react";

interface JobDetail {
  id: string;
  title: string;
  company: string;
  location: string;
  type: string;
  posted_date: string;
  description: string;
  description_summary: string;
  site?: {
    company_name: string;
    company_tagline: string;
    careers_intro: string;
    template_mode: boolean;
  };
}

function formatDate(dateStr: string): string {
  if (!dateStr) return "";
  try {
    return new Date(dateStr + "T00:00:00").toLocaleDateString("en-US", {
      month: "long", day: "numeric", year: "numeric",
    });
  } catch { return dateStr; }
}

function typeLabel(t: string): string {
  const map: Record<string, string> = {
    "full-time": "Full-time", "part-time": "Part-time",
    contract: "Contract", internship: "Internship",
  };
  return map[t] || t;
}

function renderMarkdown(md: string): string {
  return md
    .replace(/^### (.*$)/gm, '<h3 class="text-lg font-semibold text-white mt-8 mb-3">$1</h3>')
    .replace(/^## (.*$)/gm, '<h2 class="text-xl font-semibold text-white mt-10 mb-4">$1</h2>')
    .replace(/^# (.*$)/gm, '<h1 class="text-2xl font-bold text-white mt-10 mb-4">$1</h1>')
    .replace(/^\- (.*$)/gm, '<li class="ml-4 text-zinc-300 leading-relaxed">$1</li>')
    .replace(/\*\*(.*?)\*\*/g, '<strong class="text-white font-medium">$1</strong>')
    .replace(/\n\n/g, '</p><p class="text-zinc-400 leading-relaxed mb-4">')
    .replace(/^(?!<[hl])/gm, (m) => m);
}

export default function RoleDetailPage() {
  const { jobId } = useParams();
  const [job, setJob] = useState<JobDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [notFound, setNotFound] = useState(false);

  useEffect(() => {
    fetch(`/api/zoats/jobs/${jobId}`, { headers: { Accept: "application/json" } })
      .then((r) => {
        if (!r.ok) throw new Error("Not found");
        return r.json();
      })
      .then((data) => { setJob(data); setLoading(false); })
      .catch(() => { setNotFound(true); setLoading(false); });
  }, [jobId]);

  if (loading) {
    return (
      <div className="min-h-screen bg-zinc-950 flex items-center justify-center">
        <div className="w-6 h-6 border-2 border-zinc-700 border-t-zinc-400 rounded-full animate-spin" />
      </div>
    );
  }

  if (notFound || !job) {
    return (
      <div className="min-h-screen bg-zinc-950 text-zinc-100 flex flex-col items-center justify-center px-6">
        <h1 className="text-2xl font-bold mb-3">Position Not Found</h1>
        <p className="text-zinc-500 mb-6">This position may have been filled or removed.</p>
        <Link to="/careers" className="text-zinc-400 hover:text-white flex items-center gap-2 transition-colors">
          <ArrowLeft className="w-4 h-4" /> Back to all positions
        </Link>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100">
      <div className="max-w-3xl mx-auto px-6 py-12 sm:py-16">
        {/* Back link */}
        <Link to="/careers" className="inline-flex items-center gap-2 text-sm text-zinc-500 hover:text-zinc-300 transition-colors mb-10">
          <ArrowLeft className="w-4 h-4" /> All positions
        </Link>

        {/* Header */}
        <header className="mb-10">
          {job.site?.template_mode && (
            <div className="mb-5 inline-flex rounded-full border border-amber-400/30 bg-amber-400/10 px-3 py-1 text-xs font-semibold uppercase tracking-[0.2em] text-amber-200">
              Template page
            </div>
          )}
          <h1 className="text-3xl sm:text-4xl font-bold tracking-tight text-white">{job.title}</h1>
          {job.company && <p className="text-lg text-zinc-400 mt-2">{job.company}</p>}
          {job.site?.template_mode && (
            <p className="mt-3 max-w-2xl text-sm text-zinc-500">
              Template role page. Replace the company branding, intro copy, and job content before sharing this publicly.
            </p>
          )}

          <div className="flex flex-wrap items-center gap-x-5 gap-y-2 mt-5">
            {job.location && (
              <span className="flex items-center gap-1.5 text-sm text-zinc-400">
                <MapPin className="w-4 h-4 text-zinc-600" /> {job.location}
              </span>
            )}
            <span className="flex items-center gap-1.5 text-sm text-zinc-400">
              <Briefcase className="w-4 h-4 text-zinc-600" /> {typeLabel(job.type)}
            </span>
            {job.posted_date && (
              <span className="flex items-center gap-1.5 text-sm text-zinc-500">
                <Clock className="w-4 h-4 text-zinc-600" /> Posted {formatDate(job.posted_date)}
              </span>
            )}
          </div>
        </header>

        {/* Apply CTA */}
        <div className="bg-zinc-900/60 border border-zinc-800/60 rounded-xl p-6 mb-10 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <p className="text-white font-medium">Interested in this role?</p>
            <p className="text-sm text-zinc-500 mt-1">Submit your resume and we'll be in touch.</p>
          </div>
          <Link
            to={`/careers/${jobId}/apply`}
            className="inline-flex items-center justify-center gap-2 px-6 py-3 bg-white text-zinc-900 font-semibold rounded-lg
                       hover:bg-zinc-200 transition-colors text-sm shrink-0"
          >
            Apply Now <ExternalLink className="w-4 h-4" />
          </Link>
        </div>

        {/* Job Description */}
        {job.description && (
          <article className="prose-invert">
            <div
              className="text-zinc-400 leading-relaxed space-y-1 [&_h1]:text-2xl [&_h1]:font-bold [&_h1]:text-white [&_h1]:mt-10 [&_h1]:mb-4
                [&_h2]:text-xl [&_h2]:font-semibold [&_h2]:text-white [&_h2]:mt-10 [&_h2]:mb-4
                [&_h3]:text-lg [&_h3]:font-semibold [&_h3]:text-white [&_h3]:mt-8 [&_h3]:mb-3
                [&_li]:ml-4 [&_li]:text-zinc-300 [&_li]:leading-relaxed
                [&_strong]:text-white [&_strong]:font-medium"
              dangerouslySetInnerHTML={{ __html: renderMarkdown(job.description) }}
            />
          </article>
        )}

        {/* Bottom Apply CTA */}
        <div className="mt-12 pt-8 border-t border-zinc-800/40 text-center">
          <Link
            to={`/careers/${jobId}/apply`}
            className="inline-flex items-center gap-2 px-8 py-3 bg-white text-zinc-900 font-semibold rounded-lg
                       hover:bg-zinc-200 transition-all text-sm"
          >
            Apply for this position <ExternalLink className="w-4 h-4" />
          </Link>
        </div>
      </div>

      <footer className="border-t border-zinc-800/40 mt-8">
        <div className="max-w-3xl mx-auto px-6 py-8">
          <p className="text-sm text-zinc-700 text-center">ZoATS template role page.</p>
        </div>
      </footer>
    </div>
  );
}
