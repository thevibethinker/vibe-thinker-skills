import { useEffect, useRef, useState } from "react";
import { Eye, Lock, Mail, MousePointerClick } from "lucide-react";

const MEMO_ID = "{{MEMO_ID}}";
const MEMO_TITLE = {{MEMO_TITLE_JSON}};
const MEMO_ROUTE = {{MEMO_ROUTE_JSON}};
const DISCLOSURE = {{ANALYTICS_DISCLOSURE_JSON}};
const DEFAULT_LOCALE = {{DEFAULT_LOCALE_JSON}};

type AuthState = "checking" | "locked" | "authorized";
type Section = { id: string; body: string };

export default function MemoPage() {
  const [authState, setAuthState] = useState<AuthState>("checking");
  const [email, setEmail] = useState("");
  const [pin, setPin] = useState("");
  const [error, setError] = useState("");
  const [sections, setSections] = useState<Section[]>([]);
  const [contentError, setContentError] = useState("");
  const startedAt = useRef(Date.now());

  useEffect(() => {
    fetch(`/api/startup-memo-generator/auth/${MEMO_ID}/session`, { headers: { Accept: "application/json" } })
      .then((response) => response.ok ? response.json() : Promise.reject())
      .then((payload) => setAuthState(payload.authorized ? "authorized" : "locked"))
      .catch(() => setAuthState("locked"));
  }, []);

  useEffect(() => {
    if (authState !== "authorized") return;
    let cancelled = false;
    fetch(`/api/startup-memo-generator/content/${MEMO_ID}`, { headers: { Accept: "application/json" } })
      .then((response) => response.ok ? response.json() : Promise.reject(new Error(String(response.status))))
      .then((payload) => {
        if (cancelled) return;
        setSections(Array.isArray(payload.sections) ? payload.sections : []);
      })
      .catch(() => {
        if (cancelled) return;
        setContentError("Unable to load memo content.");
      });
    return () => { cancelled = true; };
  }, [authState]);

  useEffect(() => {
    if (authState !== "authorized") return;
    track("page_view", { route: MEMO_ROUTE });
    const timer = window.setInterval(() => {
      track("visible_time", { seconds: Math.round((Date.now() - startedAt.current) / 1000) });
    }, 15000);
    return () => window.clearInterval(timer);
  }, [authState]);

  function track(event: string, details: Record<string, unknown>) {
    fetch(`/api/startup-memo-generator/analytics/${MEMO_ID}/event`, {
      method: "POST",
      headers: { "Accept": "application/json", "Content-Type": "application/json" },
      body: JSON.stringify({ event, details, ts: new Date().toISOString() }),
    }).catch(() => undefined);
  }

  async function submitAccess(event: React.FormEvent) {
    event.preventDefault();
    setError("");
    const response = await fetch(`/api/startup-memo-generator/auth/${MEMO_ID}/login`, {
      method: "POST",
      headers: { "Accept": "application/json", "Content-Type": "application/json" },
      body: JSON.stringify({ email, pin }),
    });
    if (!response.ok) {
      setError("Access could not be verified.");
      return;
    }
    setAuthState("authorized");
  }

  if (authState !== "authorized") {
    return (
      <main className="min-h-screen bg-neutral-950 px-6 py-12 text-neutral-50">
        <section className="mx-auto flex min-h-[70vh] max-w-md flex-col justify-center">
          <Lock className="mb-6 h-9 w-9 text-amber-300" />
          <h1 className="text-3xl font-semibold tracking-normal">{MEMO_TITLE}</h1>
          <form className="mt-8 space-y-4" onSubmit={submitAccess}>
            <label className="block text-sm text-neutral-300">
              Email
              <input className="mt-2 w-full rounded-md border border-neutral-700 bg-neutral-900 px-3 py-3 text-neutral-50" value={email} onChange={(event) => setEmail(event.target.value)} type="email" required />
            </label>
            <label className="block text-sm text-neutral-300">
              PIN
              <input className="mt-2 w-full rounded-md border border-neutral-700 bg-neutral-900 px-3 py-3 text-neutral-50" value={pin} onChange={(event) => setPin(event.target.value)} inputMode="numeric" maxLength={4} required />
            </label>
            {error && <p className="text-sm text-red-300">{error}</p>}
            <button className="inline-flex w-full items-center justify-center gap-2 rounded-md bg-amber-300 px-4 py-3 font-medium text-neutral-950" type="submit">
              <Mail className="h-4 w-4" /> Continue
            </button>
          </form>
          {DISCLOSURE && <p className="mt-6 text-xs leading-5 text-neutral-500">{DISCLOSURE}</p>}
        </section>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-[#f5f2ea] text-neutral-950">
      <article className="mx-auto max-w-4xl px-6 py-12 md:py-20">
        <header className="mb-12 border-b border-neutral-300 pb-8">
          <p className="mb-3 inline-flex items-center gap-2 text-sm text-neutral-600"><Eye className="h-4 w-4" /> Confidential memo</p>
          <h1 className="text-4xl font-semibold tracking-normal md:text-6xl">{MEMO_TITLE}</h1>
        </header>
        <div className="space-y-8">
          {contentError && <p className="text-sm text-red-700">{contentError}</p>}
          {!contentError && sections.length === 0 && <p className="text-sm text-neutral-500">Loading…</p>}
          {sections.map((section, index) => (
            <section key={section.id} id={section.id} className="border-b border-neutral-200 pb-8" onMouseEnter={() => track("section_dwell", { section: section.id })}>
              <p className="mb-3 text-xs font-medium uppercase tracking-[0.18em] text-neutral-500">{new Intl.NumberFormat(DEFAULT_LOCALE).format(index + 1)}</p>
              <p className="whitespace-pre-wrap text-lg leading-8 text-neutral-800">{section.body}</p>
            </section>
          ))}
        </div>
        {DISCLOSURE && <footer className="mt-12 flex items-start gap-2 border-t border-neutral-300 pt-6 text-xs leading-5 text-neutral-500"><MousePointerClick className="mt-0.5 h-4 w-4 shrink-0" /> {DISCLOSURE}</footer>}
      </article>
    </main>
  );
}
