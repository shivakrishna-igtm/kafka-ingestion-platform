import { useState } from "react";
import { api } from "../api/client";
import type { FieldDef, Session, Topic } from "../types";
import SchemaFieldsEditor from "./SchemaFieldsEditor";

export default function RegisterTopic({ session, onDone }: {
  session: Session;
  onDone: (t: Topic) => void;
}) {
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [team, setTeam] = useState("");
  const [fields, setFields] = useState<FieldDef[]>([
    { name: "", type: "string", required: true },
  ]);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const valid = /^[a-z0-9]([a-z0-9._-]*[a-z0-9])?$/.test(name)
    && name.length >= 3
    && fields.length > 0
    && fields.every((f) => f.name.trim());

  const submit = async () => {
    setBusy(true);
    setError("");
    try {
      const t = await api.registerTopic(session, {
        name, description, owner_team: team,
        schema_definition: { fields },
      });
      onDone(t);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="panel">
      <div className="panel-head"><h2>Register a topic</h2></div>
      <div className="panel-body">
        <label className="lbl" htmlFor="tn">Topic name (lowercase, dots/dashes ok)</label>
        <input id="tn" className="text" placeholder="orders.v1" value={name}
               onChange={(e) => setName(e.target.value)} />
        <label className="lbl" htmlFor="td">Description</label>
        <input id="td" className="text" placeholder="What events flow through this topic?"
               value={description} onChange={(e) => setDescription(e.target.value)} />
        <label className="lbl" htmlFor="tt">Owning team</label>
        <input id="tt" className="text" placeholder="commerce" value={team}
               onChange={(e) => setTeam(e.target.value)} />

        <label className="lbl">Schema — version 1</label>
        <SchemaFieldsEditor fields={fields} onChange={setFields} />

        {error && <div className="notice err">{error}</div>}
        <div style={{ marginTop: 16 }}>
          <button className="action" disabled={!valid || busy} onClick={() => void submit()}>
            {busy ? "Registering…" : "Register topic"}
          </button>
        </div>
      </div>
    </div>
  );
}
