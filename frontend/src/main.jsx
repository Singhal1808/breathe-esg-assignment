import React from "react";
import { createRoot } from "react-dom/client";
import { AlertTriangle, Check, Database, FileUp, Lock, RefreshCw, UploadCloud, X } from "lucide-react";
import "./styles.css";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api";

function authHeader() {
  const token = localStorage.getItem("breatheAuth");
  return token ? { Authorization: `Basic ${token}` } : {};
}

async function api(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    credentials: "include",
    headers: {
      ...authHeader(),
      ...(options.headers || {}),
    },
    ...options,
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || response.statusText);
  }
  return response.json();
}

function Badge({ children, tone = "neutral" }) {
  return <span className={`badge ${tone}`}>{children}</span>;
}

function App() {
  const [summary, setSummary] = React.useState(null);
  const [sources, setSources] = React.useState([]);
  const [batches, setBatches] = React.useState([]);
  const [activities, setActivities] = React.useState([]);
  const [status, setStatus] = React.useState("");
  const [source, setSource] = React.useState("");
  const [message, setMessage] = React.useState("");
  const [busy, setBusy] = React.useState(false);
  const [loggedIn, setLoggedIn] = React.useState(Boolean(localStorage.getItem("breatheAuth")));

  async function load() {
    setBusy(true);
    try {
      const [summaryData, sourceData, batchData, activityData] = await Promise.all([
        api("/summary/"),
        api("/sources/"),
        api("/batches/"),
        api(`/activities/?${new URLSearchParams({ ...(status ? { status } : {}), ...(source ? { source_type: source } : {}) })}`),
      ]);
      setSummary(summaryData);
      setSources(sourceData);
      setBatches(batchData);
      setActivities(activityData);
      setMessage("");
    } catch (error) {
      setMessage("Sign in with the demo analyst credentials to load the review queue.");
    } finally {
      setBusy(false);
    }
  }

  React.useEffect(() => {
    load();
  }, [status, source]);

  async function handleUpload(event) {
    event.preventDefault();
    const form = event.currentTarget;
    const data = new FormData(form);
    await api("/upload/", { method: "POST", body: data });
    form.reset();
    load();
  }

  function handleLogin(event) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    localStorage.setItem("breatheAuth", btoa(`${data.get("email")}:${data.get("password")}`));
    setLoggedIn(true);
    load();
  }

  function logout() {
    localStorage.removeItem("breatheAuth");
    setLoggedIn(false);
    setSummary(null);
    setActivities([]);
  }

  async function action(id, name) {
    await api(`/activities/${id}/${name}/`, { method: "POST", headers: { "Content-Type": "application/json" }, body: "{}" });
    load();
  }

  const kpis = summary
    ? [
        ["Total", summary.total_records, "neutral"],
        ["Flagged", summary.flagged, "warn"],
        ["Failed rows", summary.failed_rows, "bad"],
        ["Locked", summary.locked, "good"],
      ]
    : [];

  return (
    <main>
      <header className="topbar">
        <div>
          <p className="eyebrow">Breathe ESG Prototype</p>
          <h1>Analyst Review Queue</h1>
        </div>
        <div className="topActions">
          {loggedIn && <button onClick={logout}>Logout</button>}
          <button onClick={load} className="iconButton" title="Refresh">
            <RefreshCw size={18} />
          </button>
        </div>
      </header>

      {message && <div className="notice">{message}</div>}

      {!loggedIn && (
        <section className="loginPanel">
          <form onSubmit={handleLogin}>
            <label>
              Email
              <input name="email" defaultValue="analyst@demo.com" autoComplete="username" />
            </label>
            <label>
              Password
              <input name="password" type="password" defaultValue="BreatheDemo123!" autoComplete="current-password" />
            </label>
            <button className="primary" type="submit">
              <Check size={17} />
              Sign in
            </button>
          </form>
        </section>
      )}

      <section className="kpiGrid">
        {kpis.map(([label, value, tone]) => (
          <div className="kpi" key={label}>
            <span>{label}</span>
            <strong>{value}</strong>
            <Badge tone={tone}>{summary?.tenant?.name || "Demo tenant"}</Badge>
          </div>
        ))}
      </section>

      <section className="workArea">
        <aside className="panel uploadPanel">
          <div className="panelTitle">
            <FileUp size={18} />
            <h2>Upload Source File</h2>
          </div>
          <form onSubmit={handleUpload}>
            <label>
              Source
              <select name="source_system" required>
                <option value="">Choose source</option>
                {sources.map((item) => (
                  <option value={item.id} key={item.id}>
                    {item.name}
                  </option>
                ))}
              </select>
            </label>
            <label>
              CSV file
              <input type="file" name="file" accept=".csv" required />
            </label>
            <button className="primary" type="submit">
              <UploadCloud size={17} />
              Upload and Normalize
            </button>
          </form>

          <div className="panelTitle compact">
            <Database size={18} />
            <h2>Recent Batches</h2>
          </div>
          <div className="batchList">
            {batches.map((batch) => (
              <div className="batch" key={batch.id}>
                <strong>{batch.filename}</strong>
                <span>{batch.source_system.name}</span>
                <small>{batch.notes}</small>
              </div>
            ))}
          </div>
        </aside>

        <section className="panel tablePanel">
          <div className="toolbar">
            <div>
              <h2>Normalized Records</h2>
              <p>Review suspicious rows, approve clean rows, then lock for audit.</p>
            </div>
            <div className="filters">
              <select value={source} onChange={(event) => setSource(event.target.value)}>
                <option value="">All sources</option>
                <option value="sap">SAP</option>
                <option value="utility">Utility</option>
                <option value="travel">Travel</option>
              </select>
              <select value={status} onChange={(event) => setStatus(event.target.value)}>
                <option value="">All statuses</option>
                <option value="pending">Pending</option>
                <option value="flagged">Flagged</option>
                <option value="approved">Approved</option>
                <option value="locked">Locked</option>
                <option value="rejected">Rejected</option>
              </select>
            </div>
          </div>

          <div className="tableWrap">
            <table>
              <thead>
                <tr>
                  <th>Source</th>
                  <th>Site</th>
                  <th>Scope</th>
                  <th>Category</th>
                  <th>Normalized</th>
                  <th>CO2e kg</th>
                  <th>Status</th>
                  <th>Flags</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {activities.map((item) => (
                  <tr key={item.id}>
                    <td>{item.source_type}</td>
                    <td>{item.site?.code || "Unmapped"}</td>
                    <td>{item.scope.replace("_", " ")}</td>
                    <td>{item.category}</td>
                    <td>
                      {Number(item.normalized_quantity).toLocaleString()} {item.normalized_unit}
                    </td>
                    <td>{item.co2e_kg ? Number(item.co2e_kg).toLocaleString(undefined, { maximumFractionDigits: 1 }) : "Review"}</td>
                    <td>
                      <Badge tone={item.status === "flagged" ? "warn" : item.status === "locked" ? "good" : "neutral"}>{item.status}</Badge>
                    </td>
                    <td className="flags">
                      {item.flags.length ? item.flags.map((flag) => <span key={flag}>{flag}</span>) : <span>clear</span>}
                    </td>
                    <td>
                      <div className="rowActions">
                        <button title="Approve" onClick={() => action(item.id, "approve")} disabled={item.status === "locked"}>
                          <Check size={15} />
                        </button>
                        <button title="Reject" onClick={() => action(item.id, "reject")} disabled={item.status === "locked"}>
                          <X size={15} />
                        </button>
                        <button title="Lock" onClick={() => action(item.id, "lock")} disabled={item.status !== "approved"}>
                          <Lock size={15} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {!activities.length && <div className="empty">{busy ? "Loading records..." : "No records match the selected filters."}</div>}
          </div>
        </section>
      </section>

      <footer>
        <AlertTriangle size={16} />
        Prototype factors are intentionally simple. The review flow and source traceability are the evaluated surface.
      </footer>
    </main>
  );
}

createRoot(document.getElementById("root")).render(<App />);
