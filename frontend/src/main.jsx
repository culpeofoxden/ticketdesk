import React, { useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import { LogOut, MessageSquarePlus, Plus, RefreshCcw, Search, TicketCheck, Trash2, UserPlus, Users } from "lucide-react";
import "./styles.css";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";
const statuses = ["open", "pending", "solved", "closed"];
const priorities = ["low", "normal", "high", "urgent"];
const roles = ["admin", "agent", "customer"];
const queueOptions = [
  { value: "", label: "All tickets" },
  { value: "unassigned", label: "Unassigned" },
  { value: "my", label: "My tickets" },
  { value: "urgent", label: "Urgent" },
  { value: "overdue", label: "Overdue" },
  { value: "pending", label: "Pending" }
];

const statusOptionsByRole = {
  admin: statuses,
  agent: ["open", "pending", "solved"],
  customer: ["closed"]
};

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
    low: "bg-zinc-100 text-zinc-700",
    admin: "bg-indigo-50 text-indigo-700",
    agent: "bg-cyan-50 text-cyan-700",
    customer: "bg-stone-100 text-stone-700",
    active: "bg-emerald-50 text-emerald-700",
    inactive: "bg-rose-50 text-rose-700",
    info: "bg-sky-50 text-sky-700",
    warning: "bg-amber-50 text-amber-700",
    critical: "bg-red-50 text-red-700",
    ok: "bg-emerald-50 text-emerald-700",
    needs_review: "bg-amber-50 text-amber-700",
    needs_info: "bg-orange-50 text-orange-700"
  };
  return <span className={`rounded px-2 py-1 text-xs font-medium ${tones[tone] || tones.gray}`}>{children}</span>;
}

function formatDateTime(value) {
  return value ? new Date(value).toLocaleString() : "Not set";
}

function isTicketOverdue(ticket) {
  const now = Date.now();
  const firstResponseOverdue = !ticket.first_response_at && ticket.first_response_due_at && new Date(ticket.first_response_due_at).getTime() < now;
  const resolutionOverdue = !["solved", "closed"].includes(ticket.status) && ticket.resolution_due_at && new Date(ticket.resolution_due_at).getTime() < now;
  return firstResponseOverdue || resolutionOverdue;
}

function historyText(item) {
  if (item.event_type === "created") {
    return `created ticket via ${item.event_metadata?.source || item.new_value || "app"}`;
  }
  if (item.event_type === "status_changed") {
    return `changed status from ${item.old_value || "none"} to ${item.new_value}`;
  }
  if (item.event_type === "priority_changed") {
    return `changed priority from ${item.old_value || "none"} to ${item.new_value}`;
  }
  if (item.event_type === "assigned") {
    return item.new_value ? `assigned ticket to ${item.event_metadata?.assignee_name || `user #${item.new_value}`}` : "unassigned ticket";
  }
  if (item.event_type === "comment_added") {
    return item.event_metadata?.first_response ? "added first response comment" : "added comment";
  }
  if (item.event_type === "first_response_recorded") {
    return `recorded first response at ${formatDateTime(item.new_value)}`;
  }
  return `changed ${item.field} from ${item.old_value || "none"} to ${item.new_value || "none"}`;
}

function AuthView({ onAuth }) {
  const [mode, setMode] = useState("login");
  const [form, setForm] = useState({ email: "admin@example.com", password: "password", full_name: "New Customer", role: "customer" });
  const [supportForm, setSupportForm] = useState({ email: "", company: "", store: "", subject: "", description: "" });
  const [submittedTicket, setSubmittedTicket] = useState(null);
  const [error, setError] = useState("");

  async function submit(event) {
    event.preventDefault();
    setError("");
    try {
      if (mode === "support") {
        const data = await request("/support-submissions", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(supportForm)
        });
        setSubmittedTicket(data);
        setSupportForm({ email: "", company: "", store: "", subject: "", description: "" });
        return;
      }
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
        <div className="mb-4 grid grid-cols-3 rounded bg-slate-100 p-1">
          <button className={`rounded px-3 py-2 text-sm ${mode === "login" ? "bg-white shadow-sm" : ""}`} onClick={() => { setMode("login"); setSubmittedTicket(null); }}>Login</button>
          <button className={`rounded px-3 py-2 text-sm ${mode === "register" ? "bg-white shadow-sm" : ""}`} onClick={() => { setMode("register"); setSubmittedTicket(null); }}>Register</button>
          <button className={`rounded px-3 py-2 text-sm ${mode === "support" ? "bg-white shadow-sm" : ""}`} onClick={() => { setMode("support"); setSubmittedTicket(null); }}>Support</button>
        </div>
        <form className="space-y-3" onSubmit={submit}>
          {mode === "support" ? (
            <>
              <input className="input" placeholder="Email" value={supportForm.email} onChange={(e) => setSupportForm({ ...supportForm, email: e.target.value })} />
              <input className="input" placeholder="Company" value={supportForm.company} onChange={(e) => setSupportForm({ ...supportForm, company: e.target.value })} />
              <input className="input" placeholder="Store" value={supportForm.store} onChange={(e) => setSupportForm({ ...supportForm, store: e.target.value })} />
              <input className="input" placeholder="Subject" value={supportForm.subject} onChange={(e) => setSupportForm({ ...supportForm, subject: e.target.value })} />
              <textarea className="input min-h-28" placeholder="Description" value={supportForm.description} onChange={(e) => setSupportForm({ ...supportForm, description: e.target.value })} />
            </>
          ) : (
          <>
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
          </>
          )}
          {error && <p className="rounded bg-red-50 p-3 text-sm text-red-700">{error}</p>}
          {submittedTicket && <p className="rounded bg-emerald-50 p-3 text-sm text-emerald-700">Request submitted. Ticket #{submittedTicket.ticket_id}</p>}
          <button className="btn-primary w-full" type="submit">{mode === "login" ? "Login" : mode === "register" ? "Create account" : "Submit request"}</button>
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
              <p className="mt-1 text-sm text-slate-500">Customer: {ticket.customer?.full_name || ticket.requester_email || "Guest requester"}</p>
            </div>
            <div className="flex shrink-0 gap-2">
              <Badge tone={ticket.status}>{ticket.status}</Badge>
              <Badge tone={ticket.priority}>{ticket.priority}</Badge>
            </div>
          </div>
          <p className="mt-2 text-sm text-slate-600">Agent: {ticket.assignee?.full_name || "Unassigned"}</p>
          <div className="mt-2 flex flex-wrap gap-2">
            {isTicketOverdue(ticket) && <Badge tone="urgent">overdue</Badge>}
            {ticket.first_response_due_at && <span className="text-xs text-slate-500">First response: {formatDateTime(ticket.first_response_due_at)}</span>}
          </div>
        </button>
      ))}
    </div>
  );
}

function DiagnosticsPanel({ diagnostics, loading, error, onRun }) {
  const latest = diagnostics[0];
  const intent = latest?.intent || "not_classified";
  const playbook = latest?.playbook || "not_run";

  return (
    <div className="rounded bg-white p-5 shadow-sm">
      <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h3 className="font-semibold text-slate-900">Diagnostics</h3>
          <p className="mt-1 text-sm text-slate-500">Intent: {intent} - Playbook: {playbook}</p>
        </div>
        <button className="btn-secondary inline-flex items-center gap-2" onClick={onRun} disabled={loading}>
          <RefreshCcw className="h-4 w-4" /> Run checks
        </button>
      </div>
      {error && <p className="mb-3 rounded bg-red-50 p-3 text-sm text-red-700">{error}</p>}
      {loading ? (
        <div className="rounded border border-slate-200 bg-slate-50 p-3 text-sm text-slate-500">Running diagnostics...</div>
      ) : diagnostics.length ? (
        <div className="space-y-2">
          {diagnostics.map((item) => (
            <div key={item.id} className="rounded border border-slate-200 p-3">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <p className="font-medium text-slate-900">{item.check_name}</p>
                  <p className="mt-1 text-sm text-slate-600">{item.summary}</p>
                </div>
                <div className="flex shrink-0 gap-2">
                  <Badge tone={item.status}>{item.status}</Badge>
                  <Badge tone={item.severity}>{item.severity}</Badge>
                </div>
              </div>
              <div className="mt-2 flex flex-wrap gap-3 text-xs text-slate-500">
                <span>Service: {item.service}</span>
                <span>Checked: {formatDateTime(item.checked_at)}</span>
                {item.details?.next_connector && <span>Next: {item.details.next_connector}</span>}
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="rounded border border-dashed border-slate-300 p-6 text-center text-sm text-slate-500">No diagnostics available for this ticket.</div>
      )}
    </div>
  );
}

function TicketDetail({ token, user, ticket, agents, diagnostics, diagnosticsLoading, diagnosticsError, onRunDiagnostics, onRefresh }) {
  const [comment, setComment] = useState("");
  const canManage = user.role === "admin" || user.role === "agent";
  const visibleStatuses = statusOptionsByRole[user.role] || [];

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
            {(ticket.requester_email || ticket.company || ticket.store) && (
              <div className="mt-4 grid gap-3 rounded border border-slate-200 bg-slate-50 p-3 text-sm md:grid-cols-3">
                <div>
                  <p className="text-xs font-medium uppercase text-slate-500">Requester email</p>
                  <p className="mt-1 text-slate-800">{ticket.requester_email || "Not provided"}</p>
                </div>
                <div>
                  <p className="text-xs font-medium uppercase text-slate-500">Company</p>
                  <p className="mt-1 text-slate-800">{ticket.company || "Not provided"}</p>
                </div>
                <div>
                  <p className="text-xs font-medium uppercase text-slate-500">Store</p>
                  <p className="mt-1 text-slate-800">{ticket.store || "Not provided"}</p>
                </div>
              </div>
            )}
            <div className="mt-4 grid gap-3 rounded border border-slate-200 bg-white p-3 text-sm md:grid-cols-4">
              <div>
                <p className="text-xs font-medium uppercase text-slate-500">First response due</p>
                <p className="mt-1 text-slate-800">{formatDateTime(ticket.first_response_due_at)}</p>
              </div>
              <div>
                <p className="text-xs font-medium uppercase text-slate-500">First response at</p>
                <p className="mt-1 text-slate-800">{formatDateTime(ticket.first_response_at)}</p>
              </div>
              <div>
                <p className="text-xs font-medium uppercase text-slate-500">Resolution due</p>
                <p className="mt-1 text-slate-800">{formatDateTime(ticket.resolution_due_at)}</p>
              </div>
              <div>
                <p className="text-xs font-medium uppercase text-slate-500">Solved at</p>
                <p className="mt-1 text-slate-800">{formatDateTime(ticket.solved_at)}</p>
              </div>
            </div>
          </div>
          <div className="flex gap-2">
            <Badge tone={ticket.status}>{ticket.status}</Badge>
            <Badge tone={ticket.priority}>{ticket.priority}</Badge>
          </div>
        </div>
        <div className="mt-4 grid gap-3 md:grid-cols-3">
          <label className="field">
            <span>Status</span>
            <select className="input" value={ticket.status} disabled={!visibleStatuses.length} onChange={(e) => patchTicket({ status: e.target.value })}>
              {visibleStatuses.includes(ticket.status) ? null : <option value={ticket.status}>{ticket.status}</option>}
              {visibleStatuses.map((status) => <option key={status}>{status}</option>)}
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

      {canManage && (
        <DiagnosticsPanel
          diagnostics={diagnostics}
          loading={diagnosticsLoading}
          error={diagnosticsError}
          onRun={() => onRunDiagnostics(ticket.id)}
        />
      )}

      <div className="rounded bg-white p-5 shadow-sm">
        <h3 className="mb-3 font-semibold text-slate-900">Comments</h3>
        <div className="space-y-3">
          {ticket.comments.map((item) => (
            <div key={item.id} className="rounded border border-slate-200 p-3">
              <p className="text-sm text-slate-800">{item.body}</p>
              <p className="mt-2 text-xs text-slate-500">{item.author.full_name} - {new Date(item.created_at).toLocaleString()}</p>
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
              <span className="font-medium text-slate-800">{item.actor?.full_name || "System"}</span> {historyText(item)}
              <span className="text-slate-400"> - {new Date(item.created_at).toLocaleString()}</span>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function UsersView({ auth }) {
  const [users, setUsers] = useState([]);
  const [error, setError] = useState("");
  const [filters, setFilters] = useState({ search: "", role: "", active: "" });
  const [form, setForm] = useState({ email: "", full_name: "", password: "", role: "customer" });

  const filteredUsers = useMemo(() => {
    const search = filters.search.trim().toLowerCase();
    return users.filter((user) => {
      const matchesSearch = !search || user.email.toLowerCase().includes(search) || user.full_name.toLowerCase().includes(search);
      const matchesRole = !filters.role || user.role === filters.role;
      const matchesActive = filters.active === "" || String(user.is_active) === filters.active;
      return matchesSearch && matchesRole && matchesActive;
    });
  }, [users, filters]);

  async function loadUsers() {
    setError("");
    try {
      const data = await request("/users", { headers: authHeaders(auth.access_token) });
      setUsers(data);
    } catch (err) {
      setError(err.message);
    }
  }

  async function createUser(event) {
    event.preventDefault();
    setError("");
    try {
      await request("/users", {
        method: "POST",
        headers: authHeaders(auth.access_token),
        body: JSON.stringify({
          email: form.email,
          password: form.password,
          role: form.role,
          full_name: form.full_name || undefined
        })
      });
      setForm({ email: "", full_name: "", password: "", role: "customer" });
      await loadUsers();
    } catch (err) {
      setError(err.message);
    }
  }

  async function patchUser(userId, changes) {
    setError("");
    try {
      await request(`/users/${userId}`, {
        method: "PATCH",
        headers: authHeaders(auth.access_token),
        body: JSON.stringify(changes)
      });
      await loadUsers();
    } catch (err) {
      setError(err.message);
    }
  }

  async function deactivateUser(userId) {
    setError("");
    try {
      await request(`/users/${userId}`, {
        method: "DELETE",
        headers: authHeaders(auth.access_token)
      });
      await loadUsers();
    } catch (err) {
      setError(err.message);
    }
  }

  useEffect(() => {
    loadUsers();
  }, [auth.access_token]);

  return (
    <div className="mx-auto grid max-w-7xl gap-6 px-4 py-6 lg:grid-cols-[380px_1fr]">
      <aside className="space-y-5">
        <div className="rounded bg-white p-5 shadow-sm">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="font-semibold text-slate-900">Users</h2>
            <button className="icon-btn" title="Refresh" onClick={loadUsers}><RefreshCcw className="h-4 w-4" /></button>
          </div>
          <div className="grid gap-2">
            <div className="relative">
              <Search className="pointer-events-none absolute left-3 top-3 h-4 w-4 text-slate-400" />
              <input className="input pl-9" placeholder="Search users" value={filters.search} onChange={(e) => setFilters({ ...filters, search: e.target.value })} />
            </div>
            <select className="input" value={filters.role} onChange={(e) => setFilters({ ...filters, role: e.target.value })}>
              <option value="">All roles</option>
              {roles.map((role) => <option key={role}>{role}</option>)}
            </select>
            <select className="input" value={filters.active} onChange={(e) => setFilters({ ...filters, active: e.target.value })}>
              <option value="">All statuses</option>
              <option value="true">active</option>
              <option value="false">inactive</option>
            </select>
          </div>
          {error && <p className="mt-3 rounded bg-red-50 p-3 text-sm text-red-700">{error}</p>}
        </div>

        <div className="rounded bg-white p-5 shadow-sm">
          <h2 className="mb-4 font-semibold text-slate-900">Create user</h2>
          <form className="space-y-3" onSubmit={createUser}>
            <input className="input" placeholder="Email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
            <input className="input" placeholder="Full name" value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })} />
            <input className="input" type="password" placeholder="Password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} />
            <select className="input" value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value })}>
              {roles.map((role) => <option key={role}>{role}</option>)}
            </select>
            <button className="btn-primary inline-flex items-center gap-2" type="submit"><UserPlus className="h-4 w-4" /> Create user</button>
          </form>
        </div>
      </aside>

      <section className="rounded bg-white p-5 shadow-sm">
        <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
          <h2 className="font-semibold text-slate-900">Team directory</h2>
          <p className="text-sm text-slate-500">{filteredUsers.length} of {users.length} users</p>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full min-w-[760px] text-left text-sm">
            <thead className="border-b border-slate-200 text-xs uppercase text-slate-500">
              <tr>
                <th className="py-3 pr-4 font-medium">User</th>
                <th className="py-3 pr-4 font-medium">Role</th>
                <th className="py-3 pr-4 font-medium">Status</th>
                <th className="py-3 pr-4 font-medium">Created</th>
                <th className="py-3 text-right font-medium">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {filteredUsers.map((user) => {
                const isSelf = user.id === auth.user.id;
                return (
                  <tr key={user.id}>
                    <td className="py-3 pr-4">
                      <input
                        className="input mb-2 max-w-xs"
                        value={user.full_name}
                        onChange={(e) => setUsers(users.map((item) => item.id === user.id ? { ...item, full_name: e.target.value } : item))}
                        onBlur={(e) => patchUser(user.id, { full_name: e.target.value })}
                      />
                      <p className="text-xs text-slate-500">{user.email}</p>
                    </td>
                    <td className="py-3 pr-4">
                      <select className="input max-w-40" value={user.role} disabled={isSelf} onChange={(e) => patchUser(user.id, { role: e.target.value })}>
                        {roles.map((role) => <option key={role}>{role}</option>)}
                      </select>
                    </td>
                    <td className="py-3 pr-4">
                      <div className="flex items-center gap-3">
                        <Badge tone={user.is_active ? "active" : "inactive"}>{user.is_active ? "active" : "inactive"}</Badge>
                        <label className="inline-flex items-center gap-2 text-xs text-slate-600">
                          <input type="checkbox" checked={user.is_active} disabled={isSelf} onChange={(e) => patchUser(user.id, { is_active: e.target.checked })} />
                          enabled
                        </label>
                      </div>
                    </td>
                    <td className="py-3 pr-4 text-slate-500">{new Date(user.created_at).toLocaleDateString()}</td>
                    <td className="py-3 text-right">
                      <button className="btn-secondary inline-flex items-center gap-2" disabled={isSelf || !user.is_active} onClick={() => deactivateUser(user.id)}>
                        <Trash2 className="h-4 w-4" /> Deactivate
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
        {!filteredUsers.length && <div className="rounded border border-dashed border-slate-300 p-6 text-center text-sm text-slate-500">No users match the current filters.</div>}
      </section>
    </div>
  );
}

function AppView({ auth, onLogout }) {
  const [activeView, setActiveView] = useState("tickets");
  const [tickets, setTickets] = useState([]);
  const [agents, setAgents] = useState([]);
  const [selectedId, setSelectedId] = useState(null);
  const [detail, setDetail] = useState(null);
  const [diagnostics, setDiagnostics] = useState([]);
  const [diagnosticsLoading, setDiagnosticsLoading] = useState(false);
  const [diagnosticsError, setDiagnosticsError] = useState("");
  const [filters, setFilters] = useState({ queue: "", status: "", priority: "", assignee_id: "" });
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
        setDiagnostics([]);
      }
    } catch (err) {
      setError(err.message);
    }
  }

  async function loadDetail(id) {
    setDiagnostics([]);
    const data = await request(`/tickets/${id}`, { headers: authHeaders(auth.access_token) });
    setDetail(data);
    if (auth.user.role !== "customer") {
      await loadDiagnostics(id);
    }
  }

  async function loadDiagnostics(id) {
    setDiagnosticsLoading(true);
    setDiagnosticsError("");
    try {
      const data = await request(`/tickets/${id}/diagnostics`, { headers: authHeaders(auth.access_token) });
      setDiagnostics(data);
    } catch (err) {
      setDiagnosticsError(err.message);
    } finally {
      setDiagnosticsLoading(false);
    }
  }

  async function runDiagnostics(id) {
    setDiagnosticsLoading(true);
    setDiagnosticsError("");
    try {
      const data = await request(`/tickets/${id}/diagnostics/run`, {
        method: "POST",
        headers: authHeaders(auth.access_token)
      });
      setDiagnostics(data);
      await loadTickets(id);
    } catch (err) {
      setDiagnosticsError(err.message);
    } finally {
      setDiagnosticsLoading(false);
    }
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
        <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-4 px-4 py-4">
          <div className="flex items-center gap-6">
            <div className="flex items-center gap-3">
              <TicketCheck className="h-7 w-7 text-teal-600" />
              <div>
                <h1 className="font-semibold text-slate-900">TicketDesk</h1>
                <p className="text-xs text-slate-500">{auth.user.full_name} - {auth.user.role}</p>
              </div>
            </div>
            <nav className="flex rounded border border-slate-200 bg-slate-50 p-1">
              <button className={`inline-flex items-center gap-2 rounded px-3 py-2 text-sm ${activeView === "tickets" ? "bg-white text-slate-900 shadow-sm" : "text-slate-600"}`} onClick={() => setActiveView("tickets")}>
                <TicketCheck className="h-4 w-4" /> Tickets
              </button>
              {auth.user.role === "admin" && (
                <button className={`inline-flex items-center gap-2 rounded px-3 py-2 text-sm ${activeView === "users" ? "bg-white text-slate-900 shadow-sm" : "text-slate-600"}`} onClick={() => setActiveView("users")}>
                  <Users className="h-4 w-4" /> Users
                </button>
              )}
            </nav>
          </div>
          <button className="btn-secondary inline-flex items-center gap-2" onClick={onLogout}><LogOut className="h-4 w-4" /> Logout</button>
        </div>
      </header>

      {activeView === "users" && auth.user.role === "admin" ? (
        <UsersView auth={auth} />
      ) : (
      <div className="mx-auto grid max-w-7xl gap-6 px-4 py-6 lg:grid-cols-[380px_1fr]">
        <aside className="space-y-5">
          <div className="rounded bg-white p-5 shadow-sm">
            <div className="mb-4 flex items-center justify-between">
              <h2 className="font-semibold text-slate-900">Tickets</h2>
              <button className="icon-btn" title="Refresh" onClick={() => loadTickets()}><RefreshCcw className="h-4 w-4" /></button>
            </div>
            <div className="mb-4 grid gap-2">
              <select className="input" value={filters.queue} onChange={(e) => setFilters({ ...filters, queue: e.target.value })}>
                {queueOptions.map((queue) => <option key={queue.value} value={queue.value}>{queue.label}</option>)}
              </select>
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
            <TicketList tickets={tickets} selectedId={selectedId} onSelect={(id) => { setSelectedId(id); setDiagnostics([]); loadDetail(id); }} />
          </div>

          <div className="rounded bg-white p-5 shadow-sm">
            <h2 className="mb-4 font-semibold text-slate-900">New ticket</h2>
            <TicketForm token={auth.access_token} onCreated={() => loadTickets()} />
          </div>
        </aside>

        {detail ? (
          <TicketDetail
            token={auth.access_token}
            user={auth.user}
            ticket={detail}
            agents={agents}
            diagnostics={diagnostics}
            diagnosticsLoading={diagnosticsLoading}
            diagnosticsError={diagnosticsError}
            onRunDiagnostics={runDiagnostics}
            onRefresh={(id) => loadTickets(id)}
          />
        ) : (
          <section className="rounded bg-white p-10 text-center text-slate-500 shadow-sm">Select or create a ticket.</section>
        )}
      </div>
      )}
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
