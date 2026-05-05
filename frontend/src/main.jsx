import React, { useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import { LogOut, MessageSquarePlus, Plus, RefreshCcw, Search, TicketCheck } from "lucide-react";
import "./styles.css";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";
const statuses = ["open", "pending", "solved", "closed"];
const priorities = ["low", "normal", "high", "urgent"];

function authHeaders(token) {
  return {
    "Content-Type": "application/json",
    Authorization: `Bearer ${token}`
  };
}

async function request(path, options = {}) {
  const response = await fetch(`${API_URL}${path}`, options);
  const data = await response.json().catch(() => null);
  if (!response.ok) {
    throw new Error(data?.detail || "Request failed");
  }
  return data;
}

function Badge({ children, tone = "gray" }) {
  const tones = {
    gray: "bg-slate-100 text-slate-700",
    open: "bg-emerald-50 text-emerald-700",
    pending: "bg-amber-50 text-amber-700",
    solved: "bg-sky-50 text-sky-700",
    closed: "bg-slate-200 text-slate-700",
    urgent: "bg-red-50 text-red-700",
    high: "bg-orange-50 text-orange-700",
    normal: "bg-blue-50 text-blue-700",
    low: "bg-zinc-100 text-zinc-700"
  };
  return <span className={`rounded px-2 py-1 text-xs font-medium ${tones[tone] || tones.gray}`}>{children}</span>;
}

function AuthView({ onAuth }) {
  const [mode, setMode] = useState("login");
  const [form, setForm] = useState({ email: "admin@example.com", password: "password", full_name: "New Customer", role: "customer" });
  const [error, setError] = useState("");

  async function submit(event) {
    event.preventDefault();
    setError("");
    try {
      const path = mode === "login" ? "/auth/login" : "/auth/register";
      const payload = mode === "login" ? { email: form.email, password: form.password } : form;
      const data = await request(path, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      onAuth(data);
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <main className="min-h-screen bg-slate-100 px-4 py-10">
      <section className="mx-auto max-w-md rounded bg-white p-6 shadow-sm">
        <div className="mb-6 flex items-center gap-3">
          <TicketCheck className="h-8 w-8 text-teal-600" />
          <div>
            <h1 className="text-2xl font-semibold text-slate-900">TicketDesk</h1>
            <p className="text-sm text-slate-500">Support tickets MVP</p>
          </div>
        </div>
        <div className="mb-4 grid grid-cols-2 rounded bg-slate-100 p-1">
          <button className={`rounded px-3 py-2 text-sm ${mode === "login" ? "bg-white shadow-sm" : ""}`} onClick={() => setMode("login")}>Login</button>
          <button className={`rounded px-3 py-2 text-sm ${mode === "register" ? "bg-white shadow-sm" : ""}`} onClick={() => setMode("register")}>Register</button>
        </div>
        <form className="space-y-3" onSubmit={submit}>
          {mode === "register" && (
            <input className="input" placeholder="Full name" value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })} />
          )}
          <input className="input" placeholder="Email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
          <input className="input" type="password" placeholder="Password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} />
          {mode === "register" && (
            <select className="input" value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value })}>
              <option value="customer">customer</option>
              <option value="agent">agent</option>
            </select>
          )}
          {error && <p className="rounded bg-red-50 p-3 text-sm text-red-700">{error}</p>}
          <button className="btn-primary w-full" type="submit">{mode === "login" ? "Login" : "Create account"}</button>
        </form>
      </section>
    </main>
  );
}

function TicketForm({ token, onCreated }) {
  const [form, setForm] = useState({ subject: "", description: "", priority: "normal" });
  const [error, setError] = useState("");

  async function submit(event) {
    event.preventDefault();
    setError("");
    try {
      await request("/tickets", {
        method: "POST",
        headers: authHeaders(token),
        body: JSON.stringify(form)
      });
      setForm({ subject: "", description: "", priority: "normal" });
      onCreated();
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <form className="space-y-3" onSubmit={submit}>
      <input className="input" placeholder="Subject" value={form.subject} onChange={(e) => setForm({ ...form, subject: e.target.value })} />
      <textarea className="input min-h-24" placeholder="Description" value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
      <select className="input" value={form.priority} onChange={(e) => setForm({ ...form, priority: e.target.value })}>
        {priorities.map((priority) => <option key={priority}>{priority}</option>)}
      </select>
      {error && <p className="rounded bg-red-50 p-3 text-sm text-red-700">{error}</p>}
      <button className="btn-primary inline-flex items-center gap-2" type="submit"><Plus className="h-4 w-4" /> Create ticket</button>
    </form>
  );
}

function TicketList({ tickets, selectedId, onSelect }) {
  if (!tickets.length) {
    return <div className="rounded border border-dashed border-slate-300 p-6 text-center text-sm text-slate-500">No tickets match the current filters.</div>;
  }
  return (
    <div className="space-y-2">
      {tickets.map((ticket) => (
        <button key={ticket.id} onClick={() => onSelect(ticket.id)} className={`w-full rounded border p-4 text-left transition ${selectedId === ticket.id ? "border-teal-500 bg-teal-50" : "border-slate-200 bg-white hover:border-slate-300"}`}>
          <div className="flex items-start justify-between gap-3">
            <div>
              <p className="font-medium text-slate-900">#{ticket.id} {ticket.subject}</p>
              <p className="mt-1 text-sm text-slate-500">Customer: {ticket.customer.full_name}</p>
            </div>
            <div className="flex shrink-0 gap-2">
              <Badge tone={ticket.status}>{ticket.status}</Badge>
              <Badge tone={ticket.priority}>{ticket.priority}</Badge>
            </div>
          </div>
          <p className="mt-2 text-sm text-slate-600">Agent: {ticket.assignee?.full_name || "Unassigned"}</p>
        </button>
      ))}
    </div>
  );
}

function TicketDetail({ token, user, ticket, agents, onRefresh }) {
  const [comment, setComment] = useState("");
  const canManage = user.role === "admin" || user.role === "agent";

  async function patchTicket(changes) {
    await request(`/tickets/${ticket.id}`, {
      method: "PATCH",
      headers: authHeaders(token),
      body: JSON.stringify(changes)
    });
    onRefresh(ticket.id);
  }

  async function addComment(event) {
    event.preventDefault();
    if (!comment.trim()) return;
    await request(`/tickets/${ticket.id}/comments`, {
      method: "POST",
      headers: authHeaders(token),
      body: JSON.stringify({ body: comment })
    });
    setComment("");
    onRefresh(ticket.id);
  }

  return (
    <section className="space-y-5">
      <div className="rounded bg-white p-5 shadow-sm">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h2 className="text-xl font-semibold text-slate-900">#{ticket.id} {ticket.subject}</h2>
            <p className="mt-2 whitespace-pre-wrap text-sm text-slate-600">{ticket.description}</p>
          </div>
          <div className="flex gap-2">
            <Badge tone={ticket.status}>{ticket.status}</Badge>
            <Badge tone={ticket.priority}>{ticket.priority}</Badge>
          </div>
        </div>
        <div className="mt-4 grid gap-3 md:grid-cols-3">
          <label className="field">
            <span>Status</span>
            <select className="input" value={ticket.status} disabled={!canManage} onChange={(e) => patchTicket({ status: e.target.value })}>
              {statuses.map((status) => <option key={status}>{status}</option>)}
            </select>
          </label>
          <label className="field">
            <span>Priority</span>
            <select className="input" value={ticket.priority} onChange={(e) => patchTicket({ priority: e.target.value })}>
              {priorities.map((priority) => <option key={priority}>{priority}</option>)}
            </select>
          </label>
          <label className="field">
            <span>Assigned agent</span>
            <select className="input" value={ticket.assignee?.id || ""} disabled={!canManage} onChange={(e) => patchTicket({ assignee_id: e.target.value ? Number(e.target.value) : null })}>
              <option value="">Unassigned</option>
              {agents.map((agent) => <option key={agent.id} value={agent.id}>{agent.full_name}</option>)}
            </select>
          </label>
        </div>
      </div>

      <div className="rounded bg-white p-5 shadow-sm">
        <h3 className="mb-3 font-semibold text-slate-900">Comments</h3>
        <div className="space-y-3">
          {ticket.comments.map((item) => (
            <div key={item.id} className="rounded border border-slate-200 p-3">
              <p className="text-sm text-slate-800">{item.body}</p>
              <p className="mt-2 text-xs text-slate-500">{item.author.full_name} · {new Date(item.created_at).toLocaleString()}</p>
            </div>
          ))}
        </div>
        <form className="mt-4 flex gap-2" onSubmit={addComment}>
          <input className="input" placeholder="Add comment" value={comment} onChange={(e) => setComment(e.target.value)} />
          <button className="btn-primary inline-flex items-center gap-2" type="submit"><MessageSquarePlus className="h-4 w-4" /> Add</button>
        </form>
      </div>

      <div className="rounded bg-white p-5 shadow-sm">
        <h3 className="mb-3 font-semibold text-slate-900">History</h3>
        <div className="space-y-2">
          {ticket.history.map((item) => (
            <div key={item.id} className="text-sm text-slate-600">
              <span className="font-medium text-slate-800">{item.actor?.full_name || "System"}</span> changed <span className="font-medium">{item.field}</span>
              {item.old_value !== null && <> from <span className="font-medium">{item.old_value}</span></>} to <span className="font-medium">{item.new_value}</span>
              <span className="text-slate-400"> · {new Date(item.created_at).toLocaleString()}</span>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function AppView({ auth, onLogout }) {
  const [tickets, setTickets] = useState([]);
  const [agents, setAgents] = useState([]);
  const [selectedId, setSelectedId] = useState(null);
  const [detail, setDetail] = useState(null);
  const [filters, setFilters] = useState({ status: "", priority: "", assignee_id: "" });
  const [error, setError] = useState("");

  const query = useMemo(() => {
    const params = new URLSearchParams();
    Object.entries(filters).forEach(([key, value]) => value && params.set(key, value));
    return params.toString();
  }, [filters]);

  async function loadTickets(nextSelectedId = selectedId) {
    setError("");
    try {
      const data = await request(`/tickets${query ? `?${query}` : ""}`, { headers: authHeaders(auth.access_token) });
      setTickets(data);
      const id = nextSelectedId || data[0]?.id || null;
      setSelectedId(id);
      if (id) {
        await loadDetail(id);
      } else {
        setDetail(null);
      }
    } catch (err) {
      setError(err.message);
    }
  }

  async function loadDetail(id) {
    const data = await request(`/tickets/${id}`, { headers: authHeaders(auth.access_token) });
    setDetail(data);
  }

  useEffect(() => {
    request("/users/agents", { headers: authHeaders(auth.access_token) }).then(setAgents).catch((err) => setError(err.message));
  }, [auth.access_token]);

  useEffect(() => {
    loadTickets();
  }, [query]);

  return (
    <main className="min-h-screen bg-slate-100">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-4">
          <div className="flex items-center gap-3">
            <TicketCheck className="h-7 w-7 text-teal-600" />
            <div>
              <h1 className="font-semibold text-slate-900">TicketDesk</h1>
              <p className="text-xs text-slate-500">{auth.user.full_name} · {auth.user.role}</p>
            </div>
          </div>
          <button className="btn-secondary inline-flex items-center gap-2" onClick={onLogout}><LogOut className="h-4 w-4" /> Logout</button>
        </div>
      </header>

      <div className="mx-auto grid max-w-7xl gap-6 px-4 py-6 lg:grid-cols-[380px_1fr]">
        <aside className="space-y-5">
          <div className="rounded bg-white p-5 shadow-sm">
            <div className="mb-4 flex items-center justify-between">
              <h2 className="font-semibold text-slate-900">Tickets</h2>
              <button className="icon-btn" title="Refresh" onClick={() => loadTickets()}><RefreshCcw className="h-4 w-4" /></button>
            </div>
            <div className="mb-4 grid gap-2">
              <div className="relative">
                <Search className="pointer-events-none absolute left-3 top-3 h-4 w-4 text-slate-400" />
                <select className="input pl-9" value={filters.status} onChange={(e) => setFilters({ ...filters, status: e.target.value })}>
                  <option value="">All statuses</option>
                  {statuses.map((status) => <option key={status}>{status}</option>)}
                </select>
              </div>
              <select className="input" value={filters.priority} onChange={(e) => setFilters({ ...filters, priority: e.target.value })}>
                <option value="">All priorities</option>
                {priorities.map((priority) => <option key={priority}>{priority}</option>)}
              </select>
              <select className="input" value={filters.assignee_id} onChange={(e) => setFilters({ ...filters, assignee_id: e.target.value })}>
                <option value="">All agents</option>
                {agents.map((agent) => <option key={agent.id} value={agent.id}>{agent.full_name}</option>)}
              </select>
            </div>
            {error && <p className="mb-3 rounded bg-red-50 p-3 text-sm text-red-700">{error}</p>}
            <TicketList tickets={tickets} selectedId={selectedId} onSelect={(id) => { setSelectedId(id); loadDetail(id); }} />
          </div>

          <div className="rounded bg-white p-5 shadow-sm">
            <h2 className="mb-4 font-semibold text-slate-900">New ticket</h2>
            <TicketForm token={auth.access_token} onCreated={() => loadTickets()} />
          </div>
        </aside>

        {detail ? (
          <TicketDetail token={auth.access_token} user={auth.user} ticket={detail} agents={agents} onRefresh={(id) => loadTickets(id)} />
        ) : (
          <section className="rounded bg-white p-10 text-center text-slate-500 shadow-sm">Select or create a ticket.</section>
        )}
      </div>
    </main>
  );
}

function Root() {
  const [auth, setAuth] = useState(() => {
    const saved = localStorage.getItem("ticketdesk_auth");
    return saved ? JSON.parse(saved) : null;
  });

  function handleAuth(data) {
    localStorage.setItem("ticketdesk_auth", JSON.stringify(data));
    setAuth(data);
  }

  function logout() {
    localStorage.removeItem("ticketdesk_auth");
    setAuth(null);
  }

  return auth ? <AppView auth={auth} onLogout={logout} /> : <AuthView onAuth={handleAuth} />;
}

createRoot(document.getElementById("root")).render(<Root />);

