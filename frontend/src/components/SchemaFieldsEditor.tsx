import type { FieldDef } from "../types";

const TYPES = ["string", "int", "long", "float", "double",
               "boolean", "timestamp", "object", "array"];

export default function SchemaFieldsEditor({ fields, onChange }: {
  fields: FieldDef[];
  onChange: (f: FieldDef[]) => void;
}) {
  const update = (i: number, patch: Partial<FieldDef>) =>
    onChange(fields.map((f, j) => (j === i ? { ...f, ...patch } : f)));

  return (
    <div className="field-grid">
      {fields.map((f, i) => (
        <div className="field-line" key={i}>
          <input
            type="text"
            placeholder="field_name"
            aria-label={`field ${i + 1} name`}
            value={f.name}
            onChange={(e) => update(i, { name: e.target.value })}
          />
          <select
            aria-label={`field ${i + 1} type`}
            value={f.type}
            onChange={(e) => update(i, { type: e.target.value })}
          >
            {TYPES.map((t) => <option key={t}>{t}</option>)}
          </select>
          <label className="req">
            <input
              type="checkbox"
              checked={f.required}
              onChange={(e) => update(i, { required: e.target.checked })}
            />
            required
          </label>
          <button
            className="icon"
            aria-label={`remove field ${i + 1}`}
            onClick={() => onChange(fields.filter((_, j) => j !== i))}
          >×</button>
        </div>
      ))}
      <div>
        <button
          className="ghost"
          onClick={() => onChange([...fields, { name: "", type: "string", required: false }])}
        >
          + Add field
        </button>
      </div>
    </div>
  );
}
