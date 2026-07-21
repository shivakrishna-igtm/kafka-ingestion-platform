import { useState } from "react";
import { api } from "../api/client";
import type { Session } from "../types";

export default function Login({ onLogin }: { onLogin: (s: Session) => void }) {
  const [username, setUsername] = useState("producer");
  const [password, setPassword] = useState("producer123");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const submit = async () => {
    setBusy(true);
    setError("");
    try {
      const r = await api.login(username, password);
      onLogin({ token: r.access_token, username: r.username, role: r.role });
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="login-wrap">
      <div className="panel">
        <div className="panel-head"><h2>Sign in</h2></div>
        <div className="panel-body">
          <label className="lbl" htmlFor="u">Username</label>
          <input id="u" className="text" value={username}
                 onChange={(e) => setUsername(e.target.value)} />
          <label className="lbl" htmlFor="p">Password</label>
          <input id="p" className="text" type="password" value={password}
                 onKeyDown={(e) => e.key === "Enter" && void submit()}
                 onChange={(e) => setPassword(e.target.value)} />
          {error && <div className="notice err">{error}</div>}
          <div style={{ marginTop: 16 }}>
            <button className="action" disabled={busy} onClick={() => void submit()}>
              {busy ? "Signing in…" : "Sign in"}
            </button>
          </div>
          <p className="hint">
            demo: producer/producer123 · viewer/viewer123 · admin/admin123
          </p>
        </div>
      </div>
    </div>
  );
}
