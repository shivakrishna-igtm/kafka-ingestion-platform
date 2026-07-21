import type { Topic } from "../types";

export default function TopicList({ topics, selected, onSelect }: {
  topics: Topic[];
  selected: string | null;
  onSelect: (name: string) => void;
}) {
  if (!topics.length) {
    return <div className="empty">No topics registered yet.</div>;
  }
  return (
    <div>
      {topics.map((t) => (
        <button
          key={t.id}
          className={`topic-row${t.name === selected ? " active" : ""}`}
          onClick={() => onSelect(t.name)}
        >
          <span className="name">
            {t.name}
            <span className="vtag">v{t.latest_version}</span>
          </span>
          <div className="meta">
            {t.owner_team || "unowned"} · registered by {t.created_by}
          </div>
        </button>
      ))}
    </div>
  );
}
