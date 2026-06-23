import { useState, useEffect, useRef } from "react";
import { useParams, Link } from "react-router-dom";
import { ArrowLeft, Upload, Check, AlertCircle, FileText, X } from "lucide-react";

const ALLOWED_TYPES = [".pdf", ".docx", ".doc", ".txt", ".md"];
const MAX_SIZE_MB = 10;

export default function ApplyPage() {
  const { jobId } = useParams();
  const [jobTitle, setJobTitle] = useState("");
  const [templateMode, setTemplateMode] = useState(true);
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [coverNote, setCoverNote] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [dragOver, setDragOver] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [success, setSuccess] = useState(false);
  const [errors, setErrors] = useState<string[]>([]);
  const fileRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    fetch(`/api/zoats/jobs/${jobId}`, { headers: { Accept: "application/json" } })
      .then((r) => r.ok ? r.json() : null)
      .then((data) => {
        if (data?.title) setJobTitle(data.title);
        if (typeof data?.site?.template_mode === "boolean") setTemplateMode(data.site.template_mode);
      });
  }, [jobId]);

  function validateFile(f: File): string | null {
    const ext = "." + f.name.split(".").pop()?.toLowerCase();
    if (!ALLOWED_TYPES.includes(ext)) return `File type ${ext} not allowed. Accepted: ${ALLOWED_TYPES.join(", ")}`;
    if (f.size > MAX_SIZE_MB * 1024 * 1024) return `File too large (${(f.size / 1024 / 1024).toFixed(1)}MB). Max: ${MAX_SIZE_MB}MB`;
    return null;
  }

  function handleFile(f: File) {
    const err = validateFile(f);
    if (err) { setErrors([err]); return; }
    setFile(f);
    setErrors([]);
  }

  function handleDrop(e: React.DragEvent) {
    e.preventDefault();
    setDragOver(false);
    if (e.dataTransfer.files[0]) handleFile(e.dataTransfer.files[0]);
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const errs: string[] = [];
    if (!name.trim()) errs.push("Name is required");
    if (!email.trim()) errs.push("Email is required");
    if (!file) errs.push("Resume is required");
    if (errs.length > 0) { setErrors(errs); return; }

    setSubmitting(true);
    setErrors([]);

    const fd = new FormData();
    fd.append("name", name.trim());
    fd.append("email", email.trim());
    fd.append("phone", phone.trim());
    fd.append("cover_note", coverNote.trim());
    fd.append("job_id", jobId || "unknown");
    fd.append("resume", file!);

    try {
      const res = await fetch("/api/zoats/apply", { method: "POST", body: fd });
      const data = await res.json();
      if (data.success) {
        setSuccess(true);
      } else {
        setErrors(data.errors || ["Something went wrong. Please try again."]);
      }
    } catch {
      setErrors(["Network error. Please check your connection and try again."]);
    } finally {
      setSubmitting(false);
    }
  }

  if (success) {
    return (
      <div className="min-h-screen bg-zinc-950 text-zinc-100 flex flex-col items-center justify-center px-6">
        <div className="w-16 h-16 bg-emerald-500/10 rounded-full flex items-center justify-center mb-6">
          <Check className="w-8 h-8 text-emerald-400" />
        </div>
        <h1 className="text-2xl font-bold mb-3">Application Received</h1>
        <p className="text-zinc-400 text-center max-w-md mb-8">
          Thanks for applying{jobTitle ? ` for ${jobTitle}` : ""}. We'll review your application and be in touch.
        </p>
        <Link to="/careers" className="text-zinc-400 hover:text-white flex items-center gap-2 transition-colors text-sm">
          <ArrowLeft className="w-4 h-4" /> Browse more positions
        </Link>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100">
      <div className="max-w-xl mx-auto px-6 py-12 sm:py-16">
        <Link to={`/careers/${jobId}`} className="inline-flex items-center gap-2 text-sm text-zinc-500 hover:text-zinc-300 transition-colors mb-8">
          <ArrowLeft className="w-4 h-4" /> Back to role details
        </Link>

        {templateMode && (
          <div className="mb-6 inline-flex rounded-full border border-amber-400/30 bg-amber-400/10 px-3 py-1 text-xs font-semibold uppercase tracking-[0.2em] text-amber-200">
            Template page
          </div>
        )}

        <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-white mb-2">Apply</h1>
        {jobTitle && <p className="text-zinc-400 mb-8">{jobTitle}</p>}
        {templateMode && (
          <p className="mb-8 max-w-lg text-sm text-zinc-500">
            Template application page. Replace this copy and confirm the local ZoATS runtime is configured before sending candidates here.
          </p>
        )}

        {errors.length > 0 && (
          <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-4 mb-6">
            {errors.map((err, i) => (
              <p key={i} className="text-red-400 text-sm flex items-start gap-2">
                <AlertCircle className="w-4 h-4 mt-0.5 shrink-0" /> {err}
              </p>
            ))}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Name */}
          <div>
            <label className="block text-sm font-medium text-zinc-300 mb-2">Full name *</label>
            <input type="text" value={name} onChange={(e) => setName(e.target.value)}
              className="w-full px-4 py-3 bg-zinc-900 border border-zinc-800 rounded-lg text-white placeholder-zinc-600
                         focus:outline-none focus:ring-2 focus:ring-zinc-600 focus:border-transparent transition-all"
              placeholder="Your full name" />
          </div>

          {/* Email */}
          <div>
            <label className="block text-sm font-medium text-zinc-300 mb-2">Email *</label>
            <input type="email" value={email} onChange={(e) => setEmail(e.target.value)}
              className="w-full px-4 py-3 bg-zinc-900 border border-zinc-800 rounded-lg text-white placeholder-zinc-600
                         focus:outline-none focus:ring-2 focus:ring-zinc-600 focus:border-transparent transition-all"
              placeholder="you@example.com" />
          </div>

          {/* Phone */}
          <div>
            <label className="block text-sm font-medium text-zinc-300 mb-2">Phone <span className="text-zinc-600">(optional)</span></label>
            <input type="tel" value={phone} onChange={(e) => setPhone(e.target.value)}
              className="w-full px-4 py-3 bg-zinc-900 border border-zinc-800 rounded-lg text-white placeholder-zinc-600
                         focus:outline-none focus:ring-2 focus:ring-zinc-600 focus:border-transparent transition-all"
              placeholder="+1 (555) 123-4567" />
          </div>

          {/* Resume Upload */}
          <div>
            <label className="block text-sm font-medium text-zinc-300 mb-2">Resume *</label>
            <div
              onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
              onDragLeave={() => setDragOver(false)}
              onDrop={handleDrop}
              onClick={() => fileRef.current?.click()}
              className={`relative border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all
                ${dragOver ? "border-zinc-500 bg-zinc-800/50" : file ? "border-zinc-700 bg-zinc-900/50" : "border-zinc-800 hover:border-zinc-700"}`}
            >
              <input ref={fileRef} type="file" accept=".pdf,.docx,.doc,.txt,.md" className="hidden"
                onChange={(e) => { if (e.target.files?.[0]) handleFile(e.target.files[0]); }} />

              {file ? (
                <div className="flex items-center justify-center gap-3">
                  <FileText className="w-5 h-5 text-zinc-400" />
                  <span className="text-zinc-300 text-sm">{file.name}</span>
                  <span className="text-zinc-600 text-xs">({(file.size / 1024).toFixed(0)} KB)</span>
                  <button type="button" onClick={(e) => { e.stopPropagation(); setFile(null); }}
                    className="ml-2 text-zinc-600 hover:text-zinc-400">
                    <X className="w-4 h-4" />
                  </button>
                </div>
              ) : (
                <>
                  <Upload className="w-8 h-8 text-zinc-600 mx-auto mb-3" />
                  <p className="text-zinc-400 text-sm">Drop your resume here or click to browse</p>
                  <p className="text-zinc-600 text-xs mt-2">PDF, DOCX, DOC, TXT, or MD — up to 10MB</p>
                </>
              )}
            </div>
          </div>

          {/* Cover Note */}
          <div>
            <label className="block text-sm font-medium text-zinc-300 mb-2">
              Cover note <span className="text-zinc-600">(optional)</span>
            </label>
            <textarea value={coverNote} onChange={(e) => setCoverNote(e.target.value)} rows={4}
              className="w-full px-4 py-3 bg-zinc-900 border border-zinc-800 rounded-lg text-white placeholder-zinc-600
                         focus:outline-none focus:ring-2 focus:ring-zinc-600 focus:border-transparent transition-all resize-none"
              placeholder="Anything you'd like us to know?" />
          </div>

          {/* Submit */}
          <button type="submit" disabled={submitting}
            className="w-full py-3 bg-white text-zinc-900 font-semibold rounded-lg hover:bg-zinc-200
                       disabled:opacity-50 disabled:cursor-not-allowed transition-all text-sm">
            {submitting ? "Submitting..." : "Submit Application"}
          </button>

          <p className="text-xs text-zinc-600 text-center">
            Your information will only be used for this application.
          </p>
        </form>
      </div>
    </div>
  );
}
