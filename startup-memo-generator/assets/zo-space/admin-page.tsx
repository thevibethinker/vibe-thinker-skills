import { useEffect, useState } from "react";
import { BarChart3, Clock, ShieldCheck } from "lucide-react";

const MEMO_ID = "{{MEMO_ID}}";
const MEMO_TITLE = {{MEMO_TITLE_JSON}};
const ORG_NAME = {{ORG_NAME_JSON}};

type EventCounts = Record<string, number>;

export default function MemoAdminPage() {
  const [counts, setCounts] = useState<EventCounts>({});
  const [adminToken, setAdminToken] = useState(() => window.localStorage.getItem(`smg-admin-${MEMO_ID}`) || "");
  const [error, setError] = useState("");

  useEffect(() => {
    if (!adminToken) return;
    window.localStorage.setItem(`smg-admin-${MEMO_ID}`, adminToken);
    fetch(`/api/startup-memo-generator/analytics/${MEMO_ID}/summary`, {
      headers: { Accept: "application/json", Authorization: `Bearer ${adminToken}` },
    })
      .then((response) => response.ok ? response.json() : Promise.reject(new Error(String(response.status))))
      .then((payload) => setCounts(payload.event_counts || {}))
      .catch(() => {
        setCounts({});
        setError("Admin analytics could not be loaded.");
      });
  }, [adminToken]);

  return (
    <main className="min-h-screen bg-neutral-950 px-6 py-10 text-neutral-50">
      <section className="mx-auto max-w-5xl">
        <p className="text-sm text-neutral-400">{ORG_NAME} memo admin</p>
        <h1 className="mt-2 text-4xl font-semibold tracking-normal">{MEMO_TITLE}</h1>
        <label className="mt-8 block max-w-xl text-sm text-neutral-300">
          Admin token
          <input
            className="mt-2 w-full rounded-md border border-neutral-700 bg-neutral-900 px-3 py-3 text-neutral-50"
            value={adminToken}
            onChange={(event) => setAdminToken(event.target.value)}
            type="password"
            placeholder="MEMO_ADMIN_TOKEN"
          />
        </label>
        {error && <p className="mt-3 text-sm text-red-300">{error}</p>}
        <div className="mt-10 grid gap-4 md:grid-cols-3">
          <Metric icon={<BarChart3 className="h-5 w-5" />} label="Views" value={counts.page_view || 0} />
          <Metric icon={<Clock className="h-5 w-5" />} label="Visible time events" value={counts.visible_time || 0} />
          <Metric icon={<ShieldCheck className="h-5 w-5" />} label="Auth attempts" value={counts.auth_attempt || 0} />
        </div>
        <section className="mt-8 rounded-md border border-neutral-800 bg-neutral-900 p-5">
          <h2 className="text-lg font-medium">Event Counts</h2>
          <pre className="mt-4 overflow-auto rounded bg-neutral-950 p-4 text-sm text-neutral-300">{JSON.stringify(counts, null, 2)}</pre>
        </section>
      </section>
    </main>
  );
}

function Metric({ icon, label, value }: { icon: React.ReactNode; label: string; value: number }) {
  return (
    <div className="rounded-md border border-neutral-800 bg-neutral-900 p-5">
      <div className="flex items-center justify-between text-neutral-400">{label}{icon}</div>
      <div className="mt-4 text-3xl font-semibold">{value}</div>
    </div>
  );
}
