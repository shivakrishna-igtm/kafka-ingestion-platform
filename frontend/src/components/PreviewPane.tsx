import { useState } from "react";
import { api } from "../api/client";
import type { PreviewResult, Session, Topic } from "../types";

const SAMPLE = `[
  {"order_id": "A-1001", "amount": 42.5, "created_at": "2026-07-21T09:30:00Z"},
  {"order_id": "A-1002", "amount": "oops", "metadata": {"channel": "web"}}
]`;

export default function PreviewPane({ session, topic }: {
  session: Session;
  topic: Topic;
}) {
  const [raw, setRaw] = useState(SAMPLE);
  const [result, setResult] = useState<PreviewResult | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const run = async () => {
    setError("");
    let payloads: unknown;
    try {
      payloads = JSON.parse(raw);
    } catch {
      setError("Sample payloads must be valid JSON — an array of objects.");
      return;
    }
    const list = Array.isArray(payloads) ? payloads : [payloads];
    setBusy(true);
    try {
      setResult(await api.preview(session, topic.name, list));
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div>
      <p style={{ marginTop: 0, color: "var(--ink-soft)", fontSize: 13.5 }}>
        Paste sample payloads to see exactly how they'd land in
        RAW.{topic.name.replace(/[^A-Za-z0-9_]/g, "_").toUpperCase()} after the
        staged COPY INTO — types coerced, drift from the registered contract flagged.
      </p>
      <textarea
        className="code"
        aria-label="sample payloads"
        value={raw}
        onChange={(e) => setRaw(e.target.value)}
      />
      {error && <div className="notice err">{error}</div>}
      <div style={{ marginTop: 12 }}>
        <button className="action" disabled={busy} onClick={() => void run()}>
          {busy ? "Previewing…" : "Preview landing"}
        </button>
      </div>

      {result && (
        <div style={{ marginTop: 20 }}>
          {result.warnings.length > 0 && (
            <div className="notice warn">
              {result.warnings.length} thing{result.warnings.length > 1 ? "s" : ""} to
              fix before go-live:
              <ul>{result.warnings.map((w, i) => <li key={i}>{w}</li>)}</ul>
            </div>
          )}
          {result.warnings.length === 0 && (
            <div className="notice ok">Clean landing — every payload matches the contract.</div>
          )}

          <div className="scroll-x" style={{ marginTop: 12 }}>
            <table className="preview">
              <thead>
                <tr>
                  {result.columns.map((c) => (
                    <th key={c.name}>
                      {c.name}
                      <span className="t">
                        {c.snowflake_type}{c.nullable ? "" : " NOT NULL"}
                      </span>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {result.rows.map((r, i) => (
                  <tr key={i}>
                    {result.columns.map((c) => (
                      <td key={c.name} className={r[c.name] === "NULL" ? "null" : ""}>
                        {r[c.name]}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <label className="lbl">Generated DDL</label>
          <pre className="sql">{result.create_table_ddl}</pre>
          <label className="lbl">Staged load</label>
          <pre className="sql">{result.copy_into_sql}</pre>
        </div>
      )}
    </div>
  );
}
