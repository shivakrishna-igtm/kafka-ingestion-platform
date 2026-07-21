import { useCallback, useEffect, useState } from "react";
import { api } from "../api/client";
import type {
  CompatibilityResult, FieldDef, Session, Topic,
} from "../types";
import SchemaFieldsEditor from "./SchemaFieldsEditor";
import PreviewPane from "./PreviewPane";

type Tab = "preview" | "schemas" | "evolve";

export default function TopicDetail({ session, topicName, canWrite, onChanged }: {
  session: Session;
  topicName: string;
  canWrite: boolean;
  onChanged: () => void;
}) {
  const [topic, setTopic] = useState<Topic | null>(null);
  const [tab, setTab] = useState<Tab>("preview");
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    try {
      setTopic(await api.getTopic(session, topicName));
      setError("");
    } catch (e) {
      setError((e as Error).message);
    }
  }, [session, topicName]);

  useEffect(() => { void load(); }, [load]);

  if (error) return <div className="notice err">{error}</div>;
  if (!topic) return <div className="panel"><div className="empty">Loading…</div></div>;

  const latest = topic.schemas[topic.schemas.length - 1];

  return (
    <div className="panel">
      <div className="panel-head">
        <h2>
          <span style={{ fontFamily: "var(--mono)", textTransform: "none", letterSpacing: 0 }}>
            {topic.name}
          </span>{" "}
          · v{topic.latest_version}
        </h2>
        <span style={{ fontSize: 12.5, color: "var(--ink-soft)" }}>
          {topic.owner_team || "unowned"}
        </span>
      </div>
      <div className="tabs" role="tablist">
        <button role="tab" className={tab === "preview" ? "on" : ""}
                onClick={() => setTab("preview")}>Snowflake preview</button>
        <button role="tab" className={tab === "schemas" ? "on" : ""}
                onClick={() => setTab("schemas")}>Schema history</button>
        {canWrite && (
          <button role="tab" className={tab === "evolve" ? "on" : ""}
                  onClick={() => setTab("evolve")}>Evolve schema</button>
        )}
      </div>
      <div className="panel-body">
        {tab === "preview" && (
          <PreviewPane session={session} topic={topic} />
        )}
        {tab === "schemas" && (
          <div className="schema-ledger">
            {topic.schemas.map((s) => (
              <div key={s.version}>
                <div className="v">v{s.version} — {s.created_by}, {new Date(s.created_at).toLocaleString()}</div>
                {s.definition.fields.map((f) => (
                  <div className="f" key={f.name}>
                    <span>{f.name}</span>
                    <span className="ty">{f.type}</span>
                    {f.required && <span className="rq">REQUIRED</span>}
                  </div>
                ))}
              </div>
            ))}
          </div>
        )}
        {tab === "evolve" && canWrite && (
          <Evolve
            session={session}
            topic={topic}
            baseFields={latest.definition.fields}
            onEvolved={() => { void load(); onChanged(); setTab("schemas"); }}
          />
        )}
      </div>
    </div>
  );
}

function Evolve({ session, topic, baseFields, onEvolved }: {
  session: Session;
  topic: Topic;
  baseFields: FieldDef[];
  onEvolved: () => void;
}) {
  const [fields, setFields] = useState<FieldDef[]>(
    baseFields.map((f) => ({ ...f })));
  const [check, setCheck] = useState<CompatibilityResult | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const runCheck = async () => {
    setBusy(true);
    setError("");
    try {
      setCheck(await api.checkSchema(session, topic.name, fields));
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };

  const publish = async () => {
    setBusy(true);
    setError("");
    try {
      await api.evolveSchema(session, topic.name, fields);
      onEvolved();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div>
      <p style={{ marginTop: 0, color: "var(--ink-soft)", fontSize: 13.5 }}>
        Propose the next version. The registry enforces BACKWARD compatibility:
        the new schema must still read every record already on the topic.
      </p>
      <SchemaFieldsEditor fields={fields} onChange={(f) => { setFields(f); setCheck(null); }} />

      {check && check.compatible && (
        <div className="notice ok">
          Compatible — safe to publish as v{topic.latest_version + 1}.
          {check.safe_changes.length > 0 && (
            <ul>{check.safe_changes.map((m) => <li key={m}>{m}</li>)}</ul>
          )}
        </div>
      )}
      {check && !check.compatible && (
        <div className="notice err">
          Not backward-compatible:
          <ul>{check.breaking_changes.map((m) => <li key={m}>{m}</li>)}</ul>
        </div>
      )}
      {error && <div className="notice err">{error}</div>}

      <div style={{ marginTop: 16, display: "flex", gap: 10 }}>
        <button className="ghost" disabled={busy} onClick={() => void runCheck()}>
          Check compatibility
        </button>
        <button className="action" disabled={busy || !check?.compatible}
                onClick={() => void publish()}>
          Publish v{topic.latest_version + 1}
        </button>
      </div>
    </div>
  );
}
