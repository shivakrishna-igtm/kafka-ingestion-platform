import { useCallback, useEffect, useState } from "react";
import { api } from "./api/client";
import type { Session, Topic } from "./types";
import Login from "./components/Login";
import TopicList from "./components/TopicList";
import TopicDetail from "./components/TopicDetail";
import RegisterTopic from "./components/RegisterTopic";

export default function App() {
  const [session, setSession] = useState<Session | null>(null);
  const [topics, setTopics] = useState<Topic[]>([]);
  const [selected, setSelected] = useState<string | null>(null);
  const [registering, setRegistering] = useState(false);
  const [error, setError] = useState("");

  const refresh = useCallback(async (s: Session) => {
    try {
      setTopics(await api.listTopics(s));
      setError("");
    } catch (e) {
      setError((e as Error).message);
    }
  }, []);

  useEffect(() => {
    if (session) void refresh(session);
  }, [session, refresh]);

  if (!session) return <Login onLogin={setSession} />;

  const canWrite = session.role !== "viewer";

  return (
    <>
      <header className="topbar">
        <div className="brand">
          Ingestion Portal <span className="tick">▮</span>
          <small>Kafka topics → Snowflake, without the ticket queue</small>
        </div>
        <div className="session">
          {session.username}
          <span className="role">{session.role}</span>
          <button className="ghost" onClick={() => setSession(null)}>Sign out</button>
        </div>
      </header>

      <main className="layout">
        {error && <div className="notice err">{error}</div>}
        <div className="split">
          <section className="panel">
            <div className="panel-head">
              <h2>Topics</h2>
              {canWrite && (
                <button className="ghost" onClick={() => { setRegistering(true); setSelected(null); }}>
                  Register topic
                </button>
              )}
            </div>
            <TopicList
              topics={topics}
              selected={selected}
              onSelect={(name) => { setSelected(name); setRegistering(false); }}
            />
          </section>

          <section>
            {registering && canWrite ? (
              <RegisterTopic
                session={session}
                onDone={(t) => {
                  setRegistering(false);
                  setSelected(t.name);
                  void refresh(session);
                }}
              />
            ) : selected ? (
              <TopicDetail
                key={selected}
                session={session}
                topicName={selected}
                canWrite={canWrite}
                onChanged={() => void refresh(session)}
              />
            ) : (
              <div className="panel">
                <div className="empty">
                  Select a topic to inspect its schema history and preview how
                  payloads will land in Snowflake — or register a new one.
                </div>
              </div>
            )}
          </section>
        </div>
      </main>
    </>
  );
}
