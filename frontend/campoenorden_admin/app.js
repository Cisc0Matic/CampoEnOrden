/* CampoEnOrden · Panel de Administración (solo ADMIN_PRINCIPAL) */
"use strict";

const API_BASE = (new URLSearchParams(location.search).get("api"))
  ? new URLSearchParams(location.search).get("api").replace(/\/+$/, "")
  : "https://pam-prefix-effectively-macro.trycloudflare.com";

const ROLES = {
  "ADMIN_PRINCIPAL": { label: "Adm. Principal", cls: "badge-red" },
  "ADMIN_EMPRESA":   { label: "Adm. Empresa",   cls: "badge-amber" },
  "OPERARIO":        { label: "Operario",       cls: "badge-green" },
  "CONSULTA":        { label: "Consulta",       cls: "badge-blue" },
  "PRODUCTOR":       { label: "Productor",      cls: "badge-gray" },
};
const ESTADOS_PAGO = ["RECIBIDO", "PENDIENTE", "ANULADO"];
const CONCEPTOS_PAGO = ["MATRICULA", "MENSUALIDAD", "SERVICIO", "OTRO"];
const TIPOS_LABOR = ["SIEMBRA", "PULVERIZACION_TERRESTRE", "PULVERIZACION_DRONES", "PULVERIZACION_AEREA", "FERTILIZACION_TERRESTRE", "FERTILIZACION_DRONES", "COSECHA", "OTRA"];
const ESTADOS_LABOR = ["CARGADA", "PENDIENTE_REVISION", "REVISADA", "APROBADA", "PENDIENTE_FACTURA", "FACTURADA", "COBRADA"];
const ESTADOS_CONTRATO = ["ACTIVO", "VENCIDO", "PENDIENTE", "RENOVADO"];
const ROLES_PERSONA = ["PRODUCTOR", "DUENO", "ARRENDATARIO", "CONTRATISTA", "CHOFER", "ADMINISTRADOR", "RESPONSABLE_CARGA", "BENEFICIARIO"];

const $ = (id) => document.getElementById(id);

function esc(v) {
  return String(v ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

function fmtFecha(iso) {
  if (!iso) return "—";
  const d = new Date(iso);
  if (isNaN(d)) return esc(iso);
  return d.toLocaleDateString("es-AR", { day: "2-digit", month: "2-digit", year: "numeric" });
}
function fmtHora(iso) {
  if (!iso) return "—";
  const d = new Date(iso);
  if (isNaN(d)) return esc(iso);
  return d.toLocaleString("es-AR", { day: "2-digit", month: "2-digit", year: "numeric", hour: "2-digit", minute: "2-digit" });
}
function fmtMonto(pago) {
  return `${Number(pago.monto).toLocaleString("es-AR", { minimumFractionDigits: 2 })} ${pago.moneda || "USD"}`;
}
function roleBadge(role) {
  const r = ROLES[role] || { label: role, cls: "badge-gray" };
  return `<span class="badge ${r.cls}">${esc(r.label)}</span>`;
}
function activeDot(u) {
  return `<span class="dot ${u.is_active ? "dot-on" : "dot-off"}"></span>`;
}

/* ── API ─────────────────────────────────────────────────────────────── */
async function api(path, opts = {}) {
  const headers = { "Content-Type": "application/json" };
  if (state.token) headers["Authorization"] = "Bearer " + state.token;
  const res = await fetch(API_BASE + path, { ...opts, headers });
  let data = null;
  const ct = res.headers.get("content-type") || "";
  if (ct.includes("application/json")) data = await res.json();
  if (res.status === 401) { logout(); throw new Error("Sesión expirada."); }
  if (!res.ok) {
    const msg = data && data.detail
      ? data.detail
      : data && typeof data === "object"
        ? Object.values(data).map((v) => Array.isArray(v) ? v.join(" ") : v).filter(Boolean).join(" · ")
        : `Error ${res.status}`;
    throw new Error(msg);
  }
  return data;
}

/* ── Estado / sesión ─────────────────────────────────────────────────── */
const state = { token: null, user: null, empresas: [], roles: {} };

function store() {
  if (state.token) localStorage.setItem("ceo_admin_token", state.token);
  else localStorage.removeItem("ceo_admin_token");
}
function logout() {
  state.token = null; state.user = null; store();
  location.hash = "#/login";
}

async function login(username, password) {
  const r = await fetch(API_BASE + "/api/token/", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });
  let data = null;
  if (r.headers.get("content-type")?.includes("application/json")) data = await r.json();
  if (!r.ok) throw new Error(data?.detail || `No se pudo iniciar sesión (${r.status}).`);
  state.token = data.access;
  const me = await api("/api/users/auth/me/");
  if (me.role !== "ADMIN_PRINCIPAL") {
    state.token = null; store();
    throw new Error("Este panel es solo para el ADMIN_PRINCIPAL de CampoEnOrden.");
  }
  state.user = me; store();
  location.hash = "#/resumen";
}

async function loadEmpresas() {
  try { state.empresas = await api("/api/users/empresas/") || []; }
  catch { state.empresas = []; }
}

/* ── Router ──────────────────────────────────────────────────────────── */
const routes = {
  "#/login": renderLogin,
  "#/resumen": renderResumen,
  "#/usuarios": renderUsuarios,
  "#/empresas": renderEmpresas,
  "#/invitaciones": renderInvitaciones,
  "#/pagos": renderPagos,
  "#/registros": renderRegistros,
};

function router() {
  const hash = location.hash || "#/login";
  if (!state.token && hash !== "#/login") { location.hash = "#/login"; return; }
  const mEmp = hash.match(/^#\/empresa\/(\d+)(?:\/tab\/(\w+))?$/);
  const fn = routes[hash] || (mEmp ? () => renderEmpresaDetalle(Number(mEmp[1]), mEmp[2] || "resumen") : renderNotFound);
  fn();
  document.querySelectorAll(".nav a").forEach((a) => a.classList.toggle("active", a.getAttribute("href") === hash));
}

async function loadAll() {
  await Promise.all([loadEmpresas(), api("/api/users/list/").then((u) => { state.users = u; }).catch(() => { state.users = []; })]);
}

/* ── Modal genérico ──────────────────────────────────────────────────── */
function openModal(title, fields, initial = {}, onSubmit) {
  $("modal-title").textContent = title;
  const form = $("modal-form");
  form.innerHTML = "";
  const grid = document.createElement("div");
  grid.className = "form-grid";

  fields.forEach((f) => {
    const wrap = document.createElement("div");
    wrap.className = "field";
    const lbl = document.createElement("label");
    lbl.textContent = f.label;
    const val = f.value !== undefined ? f.value : initial[f.key];
    let input;
    if (f.type === "select") {
      input = document.createElement("select");
      if (!f.required) {
        input.add(new Option(f.placeholder || "— Sin asignar —", ""));
      }
      (f.options || []).forEach((o) => input.add(new Option(o.label, o.value)));
      input.value = val ?? "";
    } else {
      input = document.createElement(f.type === "textarea" ? "textarea" : "input");
      input.type = f.type === "textarea" ? undefined : (f.type || "text");
      input.value = val ?? "";
      if (f.type === "checkbox") input.checked = !!val;
    }
    input.dataset.field = f.key;
    if (f.required) input.required = true;
    if (f.accept) input.accept = f.accept;
    if (f.type === "number") input.step = "0.01";
    wrap.appendChild(lbl);
    wrap.appendChild(input);
    if (f.hint) { const h = document.createElement("div"); h.className = "hint"; h.textContent = f.hint; wrap.appendChild(h); }
    grid.appendChild(wrap);
  });
  form.appendChild(grid);

  const submitBtn = $("modal-submit");
  submitBtn.onclick = async () => {
    const out = {};
    let valid = true;
    form.querySelectorAll("[data-field]").forEach((el) => {
      const v = el.type === "checkbox" ? el.checked : el.value;
      if (el.required && !String(v).trim()) valid = false;
      out[el.dataset.field] = v === "" ? null : v;
    });
    if (!valid) { toast("Completá los campos obligatorios.", "err"); return; }
    submitBtn.disabled = true;
    try { await onSubmit(out); hideModal(); }
    catch (e) { toast(e.message, "err"); }
    finally { submitBtn.disabled = false; }
  };
  $("modal-backdrop").classList.remove("hidden");
}
function hideModal() { $("modal-backdrop").classList.add("hidden"); $("modal-form").innerHTML = ""; }

function toast(msg, kind = "ok") {
  const t = document.createElement("div");
  t.className = "toast" + (kind === "err" ? " err" : kind === "warn" ? " warn" : "");
  t.textContent = msg;
  $("toast-wrap").appendChild(t);
  setTimeout(() => t.remove(), 4200);
}

function confirmar(msg) { return window.confirm(msg); }

/* ── Login ───────────────────────────────────────────────────────────── */
function renderLogin() {
  $("app").innerHTML = `
    <div class="login-wrap">
      <div class="login-card">
        <div class="login-brand"><div class="brand-badge">C</div><h1 class="login-title">CampoEnOrden</h1></div>
        <p class="login-sub">Panel de administración · acceso restringido</p>
        <div class="field">
          <label>Usuario</label>
          <input id="login-user" type="text" autocomplete="username" placeholder="usuario">
        </div>
        <div class="field">
          <label>Contraseña</label>
          <input id="login-pass" type="password" autocomplete="current-password" placeholder="••••••••">
        </div>
        <button class="btn btn-primary" id="login-btn" style="width:100%">Ingresar</button>
        <p style="color:var(--muted);font-size:12px;margin-top:14px">Con API: <span class="code">${esc(API_BASE)}</span></p>
      </div>
    </div>`;
  const doLogin = async () => {
    const b = $("login-btn"); b.disabled = true;
    try { await login($("login-user").value.trim(), $("login-pass").value); }
    catch (e) { toast(e.message, "err"); b.disabled = false; }
  };
  $("login-btn").onclick = doLogin;
  $("login-pass").addEventListener("keydown", (e) => { if (e.key === "Enter") doLogin(); });
  $("login-user").focus();
}

/* ── Shell ───────────────────────────────────────────────────────────── */
function shell(content) {
  const nav = [
    ["#/resumen", "◧", "Resumen"],
    ["#/usuarios", "👥", "Usuarios"],
    ["#/empresas", "🏢", "Empresas"],
    ["#/invitaciones", "✉", "Invitaciones"],
    ["#/pagos", "💳", "Pagos"],
    ["#/registros", "🕒", "Registros"],
  ];
  $("app").innerHTML = `
    <div class="shell">
      <aside class="sidebar">
        <div class="sidebar-brand"><div class="brand-badge">C</div><span>CampoEnOrden</span></div>
        <nav class="nav">
          ${nav.map(([h, ico, txt]) => `<a href="${h}"><span>${ico}</span><span>${txt}</span></a>`).join("")}
        </nav>
        <div class="sidebar-foot">
          <span class="user">${esc(state.user?.first_name || state.user?.username || "")}</span>
          <button class="icon-btn" id="logout-btn" title="Cerrar sesión">⎋</button>
        </div>
      </aside>
      <main class="main">${content}</main>
    </div>`;
  $("logout-btn").onclick = logout;
}

/* ── Resumen ─────────────────────────────────────────────────────────── */
async function renderResumen() {
  shell(`<div class="page-head"><div><h1 class="page-title">Resumen</h1><p class="page-sub">Estado general de la plataforma</p></div><div class="toolbar"><button class="btn btn-ghost" id="btn-refresh">Refrescar</button></div></div><div id="kpis"><div class="kpi"><div class="kpi-label">Cargando…</div></div></div><div id="roadmap"></div>`);
  $("btn-refresh").onclick = () => { location.hash = "#/resumen"; location.reload(); };
  renderResumenData();
}

async function renderResumenData() {
  let users, empresas, invites, pagos, audit;
  try {
    [users, empresas, invites, pagos, audit] = await Promise.all([
      api("/api/users/list/"), api("/api/users/empresas/"), api("/api/users/invites/"),
      api("/api/users/pagos/"), api("/api/users/audit/?limit=5"),
    ]);
  } catch (e) { $("kpis").innerHTML = `<div class="empty">${esc(e.message)}</div>`; return; }

  const activos = users.filter((u) => u.is_active).length;
  const porRol = {};
  users.forEach((u) => { porRol[u.role] = (porRol[u.role] || 0) + 1; });
  const cobrado = pagos.filter((p) => p.estado === "RECIBIDO").reduce((s, p) => s + Number(p.monto), 0);
  const pendientes = pagos.filter((p) => p.estado === "PENDIENTE");
  const pendTotal = pendientes.reduce((s, p) => s + Number(p.monto), 0);

  const kpi = (label, value, note) => `<div class="kpi"><div class="kpi-label">${label}</div><div class="kpi-value">${value}</div><div class="kpi-note">${note || ""}</div></div>`;
  $("kpis").innerHTML = [
    kpi("Usuarios", users.length, `${activos} activos · ${users.length - activos} inactivos`),
    kpi("Empresas", empresas.length, "compañías registradas"),
    kpi("Invitaciones", invites.length, "pendientes de aceptar"),
    kpi("Cobrado", "💵 " + cobrado.toLocaleString("es-AR"),
      `${pendientes.length} pendiente${pendientes.length === 1 ? "" : "s"} · ${pendTotal.toLocaleString("es-AR")} en concepto`),
  ].join("");

  const rolesList = Object.keys(ROLES).map((r) => [ROLES[r].label, porRol[r] || 0]);
  const empleadosPorEmp = empresas.map((e) => `• <b>${esc(e.nombre)}</b>: ${e.usuarios_count ?? 0} empleados`).join("<br>");

  $("roadmap").innerHTML = `
    <div class="panel"><div class="panel-head"><h2 class="panel-title">Usuarios por rol</h2></div>
      <div class="panel-body">
        <div style="display:flex;flex-wrap:wrap;gap:8px">
          ${rolesList.map(([l, n]) => `<span class="badge badge-green">${esc(l)}: ${n}</span>`).join(" ")}
        </div>
      </div></div>
    <div class="panel"><div class="panel-head"><h2 class="panel-title">Empleados por empresa</h2></div>
      <div class="panel-body">${empleadosPorEmp || '<div class="empty">No hay empresas.</div>'}</div></div>
    <div class="panel"><div class="panel-head"><h2 class="panel-title">Últimas acciones</h2></div>
      <div class="panel-body">${audit.length ? audit.map((a) => `<div>${fmtHora(a.created_at)} · <b>${esc(a.actor_username || "—")}</b> · ${esc(a.action)} · ${esc(a.target_desc || a.target_type || "")}</div>`).join("") : '<div class="empty">Sin actividad todavía.</div>'}</div></div>
    <div class="panel"><div class="panel-head"><h2 class="panel-title">Próximas implementaciones</h2></div>
      <div class="panel-body"><ul class="roadmap">
        <li><b>Página «Empleados» en la app móvil</b> para Administradores de Empresa (crear / invitar / reset / activar cuentas de sus colaboradores con los roles Operario, Consulta y Productor).</li>
        <li><b>Pago online / pasarela de cobro</b>: hoy la cobranza es manual desde este panel; se integrará pago electrónico para las empresas.</li>
        <li><b>Aislamiento de datos por empresa</b> (tenancy): que cada empresa solo vea sus labores, campos, insumos y personas en la app.</li>
        <li><b>Productores</b> como rol con campos asociados y reportes propios.</li>
        <li>Backend en <b>dominio fijo</b> para producción estable (hoy corre detrás de un túnel Cloudflare temporal).</li>
      </ul></div></div>`;
}

/* ── Usuarios ────────────────────────────────────────────────────────── */
let userFilter = "";
async function renderUsuarios() {
  shell(`
    <div class="page-head">
      <div><h1 class="page-title">Usuarios</h1><p class="page-sub">Cuentas, roles y empresas de toda la plataforma</p></div>
      <div class="toolbar">
        <input id="user-filter" type="search" placeholder="Buscar…" style="padding:7px 10px;border:1px solid var(--border);border-radius:8px">
        <button class="btn btn-ghost" id="btn-invite">Invitar</button>
        <button class="btn btn-primary" id="btn-create">+ Crear usuario</button>
      </div>
    </div>
    <div class="panel"><div class="panel-body" id="user-table"><div class="empty">Cargando…</div></div></div>`);
  $("user-filter").addEventListener("input", (e) => { userFilter = e.target.value.toLowerCase(); drawUsers(); });
  $("btn-create").onclick = modalCrearUsuario;
  $("btn-invite").onclick = modalInvitar;
  await loadAll();
  drawUsers();
}

function drawUsers() {
  const q = userFilter;
  const rows = state.users
    .filter((u) => !q || [u.username, u.email, u.first_name, u.last_name, u.empresa_nombre].join(" ").toLowerCase().includes(q))
    .map((u) => `
      <tr>
        <td>${activeDot(u)}<b>${esc(u.username)}</b><br><span style="color:var(--muted);font-size:12px">${esc(u.email || "")}</span></td>
        <td>${esc(u.first_name || "")} ${esc(u.last_name || "")}</td>
        <td>${roleBadge(u.role)}</td>
        <td>${esc(u.empresa_nombre || "—")}</td>
        <td>${fmtFecha(u.fecha_alta)}</td>
        <td style="white-space:nowrap">
          <button class="btn btn-ghost btn-sm" data-act="edit" data-id="${u.id}">Editar</button>
          <button class="btn btn-ghost btn-sm" data-act="reset" data-id="${u.id}">Reset clave</button>
        </td>
      </tr>`).join("");
  $("user-table").innerHTML = rows
    ? `<table><thead><tr><th>Cuenta</th><th>Nombre</th><th>Rol</th><th>Empresa</th><th>Alta</th><th></th></tr></thead><tbody>${rows}</tbody></table>`
    : '<div class="empty">No hay usuarios.</div>';

  $("user-table").querySelectorAll("button[data-act]").forEach((b) => {
    b.onclick = () => {
      const u = state.users.find((x) => x.id === Number(b.dataset.id));
      if (!u) return;
      if (b.dataset.act === "edit") modalEditarUsuario(u);
      else modalResetClave(u);
    };
  });
}

function modalCrearUsuario(empresaId) {
  if (!state.empresas.length) { toast("Primero creá al menos una empresa.", "warn"); location.hash = "#/empresas"; return; }
  const fields = [
    { key: "username", label: "Usuario", required: true },
    { key: "email", label: "Email", type: "email", required: true },
    { key: "password", label: "Contraseña inicial", type: "password", required: true },
    { key: "first_name", label: "Nombre", required: true },
    { key: "last_name", label: "Apellido" },
    { key: "role", label: "Rol", type: "select", required: true,
      options: ["ADMIN_EMPRESA", "OPERARIO", "CONSULTA", "PRODUCTOR"].map((r) => ({ value: r, label: ROLES[r].label })) },
  ];
  if (!empresaId) {
    fields.push({ key: "empresa_id", label: "Empresa", type: "select", required: true,
      options: state.empresas.map((e) => ({ value: e.id, label: e.nombre })) });
  }
  openModal("Crear usuario", fields, {}, async (d) => {
    if (empresaId) d.empresa_id = empresaId;
    const created = await api("/api/users/create/", { method: "POST", body: JSON.stringify(d) });
    toast("Usuario " + created.username + " creado.");
    if (empresaId) renderEmpresaDetalle(empresaId, "usuarios");
    else { await loadAll(); drawUsers(); }
  });
}

function modalInvitar() {
  if (!state.empresas.length) { toast("Primero creá al menos una empresa.", "warn"); location.hash = "#/empresas"; return; }
  openModal("Invitar al equipo", [
    { key: "email", label: "Email del invitado", type: "email", required: true },
    { key: "role", label: "Rol", type: "select", required: true,
      options: ["ADMIN_EMPRESA", "OPERARIO", "CONSULTA", "PRODUCTOR"].map((r) => ({ value: r, label: ROLES[r].label })) },
    { key: "empresa_id", label: "Empresa", type: "select", required: true,
      options: state.empresas.map((e) => ({ value: e.id, label: e.nombre })) },
  ], {}, async (d) => {
    api("/api/users/invite/", { method: "POST", body: JSON.stringify(d) }).then(() => {
      toast("Invitación enviada a " + d.email + ".");
    }).catch((e) => toast(e.message, "err"));
  });
}

function modalEditarUsuario(u, after) {
  const esOtroPrincipal = u.role === "ADMIN_PRINCIPAL" && u.id !== state.user.id;
  if (esOtroPrincipal) { toast("No podés modificar a otro ADMIN_PRINCIPAL.", "err"); return; }
  const rolesEditable = u.role === "ADMIN_PRINCIPAL" ? [u.role] : ["OPERARIO", "CONSULTA", "PRODUCTOR", "ADMIN_EMPRESA"];
  openModal("Editar " + u.username, [
    { key: "first_name", label: "Nombre" },
    { key: "last_name", label: "Apellido" },
    { key: "email", label: "Email", type: "email" },
    { key: "role", label: "Rol", type: "select",
      options: rolesEditable.map((r) => ({ value: r, label: ROLES[r].label })), value: u.role },
    { key: "empresa", label: "Empresa", type: "select",
      options: state.empresas.map((e) => ({ value: e.id, label: e.nombre })), value: u.empresa },
    { key: "is_active", label: "Cuenta activa", type: "checkbox", value: u.is_active },
  ], {}, async (d) => {
    const body = {};
    if (d.first_name !== null) body.first_name = d.first_name;
    if (d.last_name !== null) body.last_name = d.last_name;
    if (d.email !== null) body.email = d.email;
    body.role = d.role; body.empresa = d.empresa; body.is_active = !!d.is_active;
    await api(`/api/users/${u.id}/`, { method: "PATCH", body: JSON.stringify(body) });
    toast(u.username + " actualizado.");
    if (after) await after(); else { await loadAll(); drawUsers(); }
  });
}

function modalResetClave(u) {
  openModal("Resetear contraseña de " + u.username, [
    { key: "new_password", label: "Nueva contraseña", type: "password", required: true, hint: "Se la enviará al usuario por email." },
  ], {}, async (d) => {
    await api(`/api/users/${u.id}/reset-password/`, { method: "POST", body: JSON.stringify(d) });
    toast("Contraseña de " + u.username + " actualizada.");
  });
}

/* ── Empresas ────────────────────────────────────────────────────────── */
async function renderEmpresas() {
  shell(`
    <div class="page-head">
      <div><h1 class="page-title">Empresas</h1><p class="page-sub">Compañías cliente de la plataforma</p></div>
      <button class="btn btn-primary" id="btn-nueva-empresa">+ Nueva empresa</button>
    </div>
    <div class="panel"><div class="panel-body" id="emp-table"><div class="empty">Cargando…</div></div></div>`);
  $("btn-nueva-empresa").onclick = modalNuevaEmpresa;
  await loadEmpresas(); drawEmpresas();
}
function drawEmpresas() {
  $("emp-table").innerHTML = state.empresas.length
    ? `<table><thead><tr><th>Nombre</th><th>Empleados</th><th>Contacto</th><th>Email</th><th>Estado</th><th></th></tr></thead><tbody>
        ${state.empresas.map((e) => `
          <tr data-id="${e.id}" style="cursor:pointer">
            <td><b>${esc(e.nombre)}</b></td>
            <td>${e.usuarios_count ?? 0}</td>
            <td>${esc(e.telefono || "—")}</td>
            <td>${esc(e.email || "—")}</td>
            <td><span class="badge ${e.activo ? "badge-green" : "badge-gray"}">${e.activo ? "Activa" : "Inactiva"}</span></td>
            <td style="white-space:nowrap">
              <button class="btn btn-primary btn-sm" data-go="${e.id}">Ingresar</button>
            </td>
          </tr>`).join("")}
      </tbody></table>`
    : '<div class="empty">No hay empresas registradas.</div>';
  $("emp-table").querySelectorAll("tr[data-id]").forEach((tr) => {
    tr.addEventListener("click", (ev) => {
      if (ev.target.closest("button")) return;
      location.hash = "#/empresa/" + tr.dataset.id;
    });
  });
  $("emp-table").querySelectorAll("button[data-go]").forEach((b) => {
    b.onclick = () => { location.hash = "#/empresa/" + b.dataset.go; };
  });
}
function modalNuevaEmpresa() {
  openModal("Nueva empresa", [
    { key: "nombre", label: "Nombre de la empresa", required: true },
    { key: "email", label: "Email de contacto", type: "email" },
    { key: "telefono", label: "Teléfono" },
  ], {}, async (d) => {
    const created = await api("/api/users/empresas/", { method: "POST", body: JSON.stringify(d) });
    toast("Empresa " + created.nombre + " creada.");
    await loadEmpresas(); drawEmpresas(); await loadAll();
  });
}

/* ── Detalle de empresa (dashboard / empleados / productores / campos / labores) ── */
const EMP_TABS = [
  ["resumen", "Resumen"],
  ["usuarios", "Empleados"],
  ["productores", "Productores"],
  ["campos", "Campos"],
  ["labores", "Labores"],
];

async function renderEmpresaDetalle(id, tab) {
  let emp;
  try { emp = await api("/api/users/empresas/" + id + "/"); }
  catch (e) { shell(`<div class="page-head"><h1 class="page-title">Empresa</h1></div><div class="empty">${esc(e.message)}</div>`); return; }
  if (!EMP_TABS.some(([k]) => k === tab)) tab = "resumen";
  shell(`
    <div class="page-head" style="align-items:flex-start">
      <div>
        <a href="#/empresas" style="color:var(--muted);font-size:13px;text-decoration:none">&larr; Empresas</a>
        <h1 class="page-title">${esc(emp.nombre)}</h1>
        <p class="page-sub">
          ${esc(emp.direccion || "")}${emp.direccion && (emp.email || emp.telefono) ? " · " : ""}
          ${esc(emp.email || "")}${emp.email && emp.telefono ? " · " : ""}
          ${esc(emp.telefono || "")}
          <span class="badge ${emp.activo ? "badge-green" : "badge-gray"}" style="margin-left:6px">${emp.activo ? "Activa" : "Inactiva"}</span>
        </p>
      </div>
      <div class="toolbar"><button class="btn btn-ghost" id="btn-edit-emp">Datos de la empresa</button></div>
    </div>
    <div class="tabs" style="display:flex;gap:4px;border-bottom:1px solid var(--border);margin-bottom:16px">
      ${EMP_TABS.map(([k, l]) => `<button class="tab-btn ${k === tab ? "tab-active" : ""}" data-t="${k}" style="padding:9px 14px;border:0;cursor:pointer;border-radius:8px 8px 0 0;background:${k === tab ? "var(--accent)" : "transparent"};color:${k === tab ? "#fff" : "var(--muted)"};font-weight:600">${l}</button>`).join("")}
    </div>
    <div id="emp-tab" data-emp="${id}" data-tab="${tab}"><div class="empty">Cargando…</div></div>`);
  $("btn-edit-emp").onclick = () => modalEditarEmpresa(emp);
  document.querySelectorAll(".tab-btn").forEach((b) => {
    b.onclick = () => { location.hash = `#/empresa/${id}/tab/${b.dataset.t}`; };
  });
  await empTabContent(id, tab);
}

async function empTabContent(id, tab) {
  const host = $("emp-tab");
  if (!host) return;
  try {
    if (tab === "resumen") await empTabResumen(host, id);
    else if (tab === "usuarios") await empTabUsuarios(host, id);
    else if (tab === "productores") await empTabProductores(host, id);
    else if (tab === "campos") await empTabCampos(host, id);
    else if (tab === "labores") await empTabLabores(host, id);
  } catch (e) { host.innerHTML = `<div class="empty">${esc(e.message)}</div>`; }
}

/* Resumen: KPIs del dashboard acotado a la empresa */
async function empTabResumen(host, id) {
  const d = await api(`/api/core/dashboard/?empresa=${id}`);
  const kpi = (label, value, note) => `<div class="kpi"><div class="kpi-label">${label}</div><div class="kpi-value">${value}</div><div class="kpi-note">${note || ""}</div></div>`;
  const fmtCosto = (v) => "$" + Number(v || 0).toLocaleString("es-AR", { maximumFractionDigits: 2 });
  host.innerHTML = `
    <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:12px">
      ${kpi("Campos activos", d.campos_activos, "con contrato ACTIVO")}
      ${kpi("Hectáreas totales", Number(d.hectareas_totales || 0).toLocaleString("es-AR"), "cargadas al sistema")}
      ${kpi("Hectáreas trabajadas", Number(d.hectareas_trabajadas || 0).toLocaleString("es-AR"), "superficie trabajada")}
      ${kpi("Labores cargadas", d.labores_cargadas, "total de labores")}
      ${kpi("Costos totales", fmtCosto(d.costos_totales), "labores + fletes")}
      ${kpi("Costo por ha", fmtCosto(d.costos_por_ha), "costo por hectárea trabajada")}
      ${kpi("Documentos pendientes", d.documentos_pendientes, "en estado PENDIENTE")}
    </div>
    ${d.alertas && d.alertas.length ? `<div class="panel" style="margin-top:16px"><div class="panel-head"><h2 class="panel-title">Alertas</h2></div><div class="panel-body">${d.alertas.map((a) => `<div>⚠️ ${esc(a)}</div>`).join("")}</div></div>` : ""}`;
}

/* Empleados: usuarios de la empresa */
async function empTabUsuarios(host, id) {
  const users = await api(`/api/users/list/?empresa=${id}`) || [];
  host.innerHTML = `
    <div class="page-head" style="padding:0 0 12px">
      <p class="page-sub">${users.length} cuenta${users.length === 1 ? "" : "s"} en esta empresa</p>
      <button class="btn btn-primary" id="btn-emp-user">+ Crear usuario</button>
    </div>
    <div class="panel"><div class="panel-body">${users.length ? `<table><thead><tr><th>Cuenta</th><th>Nombre</th><th>Rol</th><th>Estado</th><th></th></tr></thead><tbody>
      ${users.map((u) => `<tr>
        <td>${activeDot(u)}<b>${esc(u.username)}</b><br><span style="color:var(--muted);font-size:12px">${esc(u.email || "")}</span></td>
        <td>${esc(u.first_name || "")} ${esc(u.last_name || "")}</td>
        <td>${roleBadge(u.role)}</td>
        <td><span class="badge ${u.is_active ? "badge-green" : "badge-gray"}">${u.is_active ? "Activo" : "Inactivo"}</span></td>
        <td style="white-space:nowrap">
          <button class="btn btn-ghost btn-sm" data-u="${u.id}" data-cmd="edit">Editar</button>
          <button class="btn btn-ghost btn-sm" data-u="${u.id}" data-cmd="reset">Reset clave</button>
        </td>
      </tr>`).join("")}
    </tbody></table>` : '<div class="empty">No hay usuarios en esta empresa todavía.</div>'}</div></div>`;
  $("btn-emp-user").onclick = () => modalCrearUsuario(id);
  host.querySelectorAll("button[data-cmd]").forEach((b) => {
    b.onclick = () => {
      const u = users.find((x) => x.id === Number(b.dataset.u));
      if (!u) return;
      if (b.dataset.cmd === "edit") modalEditarUsuario(u, () => renderEmpresaDetalle(id, "usuarios"));
      else modalResetClave(u);
    };
  });
}

/* Productores / Personas de la empresa */
async function empTabProductores(host, id) {
  const personas = await api(`/api/core/personas/?empresa=${id}`) || [];
  const orden = ROLES_PERSONA;
  personas.sort((a, b) => (orden.indexOf(a.rol) - orden.indexOf(b.rol)) || a.nombre.localeCompare(b.nombre));
  host.innerHTML = `
    <div class="page-head" style="padding:0 0 12px">
      <p class="page-sub">${personas.length} persona${personas.length === 1 ? "" : "s"} vinculadas (productores, contratistas, choferes…)</p>
      <button class="btn btn-primary" id="btn-emp-persona">+ Nueva persona</button>
    </div>
    <div class="panel"><div class="panel-body">${personas.length ? `<table><thead><tr><th>Nombre</th><th>Rol</th><th>Documento</th><th>Teléfono</th><th>Email</th><th></th></tr></thead><tbody>
      ${personas.map((p) => `<tr>
        <td><b>${esc(p.nombre)}</b></td>
        <td><span class="badge badge-green">${esc(p.nombre_rol || p.rol || "—")}</span></td>
        <td>${esc(p.documento || "—")}</td>
        <td>${esc(p.telefono || "—")}</td>
        <td>${esc(p.email || "—")}</td>
        <td style="white-space:nowrap">
          <button class="btn btn-ghost btn-sm" data-p="${p.id}" data-cmd="edit">Editar</button>
          <button class="btn btn-danger btn-sm" data-p="${p.id}" data-cmd="del">Eliminar</button>
        </td>
      </tr>`).join("")}
    </tbody></table>` : '<div class="empty">No hay personas vinculadas a esta empresa. Creá un productor para empezar.</div>'}</div></div>`;
  $("btn-emp-persona").onclick = () => modalNuevaPersonaEmpresa(id, null, personas);
  host.querySelectorAll("button[data-cmd]").forEach((b) => {
    b.onclick = () => {
      const p = personas.find((x) => x.id === Number(b.dataset.p));
      if (!p) return;
      if (b.dataset.cmd === "edit") modalNuevaPersonaEmpresa(id, p, personas);
      else if (confirmar("Eliminar a " + p.nombre + "?")) {
        api(`/api/core/personas/${p.id}/`, { method: "DELETE" }).then(() => {
          toast("Persona eliminada."); renderEmpresaDetalle(id, "productores");
        }).catch((e) => toast(e.message, "err"));
      }
    };
  });
}

function modalNuevaPersonaEmpresa(id, persona, personas) {
  const camposPersona = [
    { key: "nombre", label: "Nombre", required: true, value: persona?.nombre },
    { key: "rol", label: "Rol", type: "select", required: true,
      options: ROLES_PERSONA.map((r) => ({ value: r, label: r })),
      value: persona?.rol || "PRODUCTOR" },
    { key: "documento", label: "DNI / documento", value: persona?.documento },
    { key: "cuil", label: "CUIL", value: persona?.cuil },
    { key: "telefono", label: "Teléfono", value: persona?.telefono },
    { key: "email", label: "Email", type: "email", value: persona?.email },
    { key: "direccion", label: "Dirección", value: persona?.direccion },
    { key: "observaciones", label: "Observaciones", type: "textarea", value: persona?.observaciones },
    { key: "activo", label: "Activo", type: "checkbox", value: persona ? !!persona.activo : true },
  ];
  openModal(persona ? "Editar " + persona.nombre : "Nueva persona", camposPersona, {}, async (d) => {
    const body = { ...d, tipo: "PERSONA", empresa: id };
    if (!persona) body.activo = d.activo;
    if (persona) {
      await api(`/api/core/personas/${persona.id}/`, { method: "PATCH", body });
    } else {
      await api("/api/core/personas/", { method: "POST", body });
    }
    toast(persona ? "Persona actualizada." : "Persona creada.");
    renderEmpresaDetalle(id, "productores");
  });
}

/* Campos de la empresa */
async function empTabCampos(host, id) {
  const [campos, personas] = await Promise.all([
    api(`/api/core/campos/?empresa=${id}`) || [],
    api(`/api/core/personas/?empresa=${id}`) || [],
  ]);
  const productores = personas.filter((p) => p.rol === "PRODUCTOR");
  host.innerHTML = `
    <div class="page-head" style="padding:0 0 12px">
      <p class="page-sub">${campos.length} campo${campos.length === 1 ? "" : "s"} de esta empresa</p>
      <button class="btn btn-primary" id="btn-emp-campo">+ Nuevo campo</button>
    </div>
    <div class="panel"><div class="panel-body">${campos.length ? `<table><thead><tr><th>Nombre</th><th>Productor</th><th>Ubicación</th><th>Superficie</th><th>Estado</th><th></th></tr></thead><tbody>
      ${campos.map((c) => `<tr>
        <td><b>${esc(c.nombre)}</b></td>
        <td>${esc(c.productor_nombre || "—")}</td>
        <td>${esc(c.localidad || c.ubicacion || "—")}</td>
        <td>${Number(c.superficie_total || 0).toLocaleString("es-AR")} ha</td>
        <td><span class="badge badge-green">${esc(c.estado_contrato_display || c.estado_contrato)}</span></td>
        <td style="white-space:nowrap">
          <button class="btn btn-ghost btn-sm" data-c="${c.id}" data-cmd="edit">Editar</button>
          <button class="btn btn-danger btn-sm" data-c="${c.id}" data-cmd="del">Eliminar</button>
        </td>
      </tr>`).join("")}
    </tbody></table>` : '<div class="empty">Esta empresa todavía no tiene campos. Asignale un productor y creá el primer campo.</div>'}</div></div>`;
  $("btn-emp-campo").onclick = () => modalCampoEmpresa(id, null, productores);
  host.querySelectorAll("button[data-cmd]").forEach((b) => {
    b.onclick = () => {
      const c = campos.find((x) => x.id === Number(b.dataset.c));
      if (!c) return;
      if (b.dataset.cmd === "edit") modalCampoEmpresa(id, c, productores);
      else if (confirmar("Eliminar el campo " + c.nombre + "?")) {
        api(`/api/core/campos/${c.id}/`, { method: "DELETE" }).then(() => {
          toast("Campo eliminado."); renderEmpresaDetalle(id, "campos");
        }).catch((e) => toast(e.message, "err"));
      }
    };
  });
}

function modalCampoEmpresa(id, campo, productores) {
  if (!campo && !productores.length) {
    toast("Creá primero un productor para esta empresa (el campo necesita uno).", "warn");
    return;
  }
  const prodOptions = productores.map((p) => ({ value: p.id, label: p.nombre }));
  openModal(campo ? "Editar " + campo.nombre : "Nuevo campo", [
    { key: "nombre", label: "Nombre", required: true, value: campo?.nombre },
    { key: "productor", label: "Productor", type: "select",
      options: prodOptions, value: campo?.productor },
    { key: "ubicacion", label: "Ubicación", value: campo?.ubicacion },
    { key: "localidad", label: "Localidad", value: campo?.localidad },
    { key: "provincia", label: "Provincia", value: campo?.provincia },
    { key: "superficie_total", label: "Superficie total (ha)", type: "number", value: campo?.superficie_total },
    { key: "superficie_trabajada", label: "Superficie trabajada (ha)", type: "number", value: campo?.superficie_trabajada },
    { key: "estado_contrato", label: "Estado de contrato", type: "select", required: true,
      options: ESTADOS_CONTRATO.map((e) => ({ value: e, label: e })), value: campo?.estado_contrato || "ACTIVO" },
    { key: "observaciones", label: "Observaciones", type: "textarea", value: campo?.observaciones },
  ], {}, async (d) => {
    d.productor = d.productor || null;
    if (campo) await api(`/api/core/campos/${campo.id}/`, { method: "PATCH", body: JSON.stringify(d) });
    else await api("/api/core/campos/", { method: "POST", body: JSON.stringify(d) });
    toast(campo ? "Campo actualizado." : "Campo creado.");
    renderEmpresaDetalle(id, "campos");
  });
}

/* Labores de la empresa */
async function empTabLabores(host, id) {
  const labores = await api(`/api/core/labores/?empresa=${id}`) || [];
  host.innerHTML = `
    <div class="page-head" style="padding:0 0 12px">
      <p class="page-sub">${labores.length} labor${labores.length === 1 ? "" : "es"} de la empresa</p>
    </div>
    <div class="panel"><div class="panel-body">${labores.length ? `<table><thead><tr><th>Fecha</th><th>Tipo</th><th>Campo / Lote</th><th>Estado</th><th>Ha</th><th>Costo</th><th></th></tr></thead><tbody>
      ${labores.map((l) => `<tr>
        <td class="mono">${fmtFecha(l.fecha)}</td>
        <td>${esc(l.tipo_display || l.tipo)}</td>
        <td><b>${esc(l.campo_nombre || "—")}</b> · ${esc(l.lote_nombre || "")}</td>
        <td><span class="badge badge-amber">${esc(l.estado_display || l.estado)}</span></td>
        <td>${Number(l.hectareas || 0).toLocaleString("es-AR")}</td>
        <td class="mono">$${Number(l.costo_total || 0).toLocaleString("es-AR", { maximumFractionDigits: 2 })}</td>
        <td style="white-space:nowrap">
          <button class="btn btn-ghost btn-sm" data-l="${l.id}" data-cmd="edit">Editar</button>
          <button class="btn btn-danger btn-sm" data-l="${l.id}" data-cmd="del">Eliminar</button>
        </td>
      </tr>`).join("")}
    </tbody></table>` : '<div class="empty">No hay labores para esta empresa todavía.</div>'}</div></div>`;
  host.querySelectorAll("button[data-cmd]").forEach((b) => {
    b.onclick = () => {
      const l = labores.find((x) => x.id === Number(b.dataset.l));
      if (!l) return;
      if (b.dataset.cmd === "edit") modalLaborEmpresa(id, l);
      else if (confirmar("Eliminar la labor del " + fmtFecha(l.fecha) + "?")) {
        api(`/api/core/labores/${l.id}/`, { method: "DELETE" }).then(() => {
          toast("Labor eliminada."); renderEmpresaDetalle(id, "labores");
        }).catch((e) => toast(e.message, "err"));
      }
    };
  });
}

function modalLaborEmpresa(id, l) {
  openModal("Editar labor " + l.lote_nombre + " (" + (l.tipo_display || l.tipo) + ")", [
    { key: "fecha", label: "Fecha", type: "date", value: l.fecha },
    { key: "tipo", label: "Tipo", type: "select", required: true,
      options: TIPOS_LABOR.map((t) => ({ value: t, label: t })), value: l.tipo },
    { key: "estado", label: "Estado", type: "select", required: true,
      options: ESTADOS_LABOR.map((e) => ({ value: e, label: e.replace("_", " ") })), value: l.estado },
    { key: "hectareas", label: "Hectáreas", type: "number", value: l.hectareas },
    { key: "precio_por_ha", label: "Precio por ha", type: "number", value: l.precio_por_ha },
    { key: "moneda", label: "Moneda", value: l.moneda || "USD" },
    { key: "qq_ha", label: "Rendimiento (qq/ha)", type: "number", value: l.qq_ha },
    { key: "observaciones", label: "Observaciones", type: "textarea", value: l.observaciones },
  ], {}, async (d) => {
    await api(`/api/core/labores/${l.id}/`, { method: "PATCH", body: JSON.stringify(d) });
    toast("Labor actualizada.");
    renderEmpresaDetalle(id, "labores");
  });
}

function modalEditarEmpresa(emp) {
  openModal("Datos de " + emp.nombre, [
    { key: "nombre", label: "Nombre de la empresa", required: true, value: emp.nombre },
    { key: "documento", label: "Documento / CUIT", value: emp.documento },
    { key: "direccion", label: "Dirección", value: emp.direccion },
    { key: "telefono", label: "Teléfono", value: emp.telefono },
    { key: "email", label: "Email", type: "email", value: emp.email },
    { key: "observaciones", label: "Observaciones", type: "textarea", value: emp.observaciones },
    { key: "activo", label: "Empresa activa", type: "checkbox", value: !!emp.activo },
  ], {}, async (d) => {
    await api(`/api/users/empresas/${emp.id}/`, { method: "PATCH", body: JSON.stringify(d) });
    toast("Empresa actualizada.");
    renderEmpresaDetalle(emp.id, "resumen");
  });
}

/* ── Invitaciones ────────────────────────────────────────────────────── */
async function renderInvitaciones() {
  shell(`
    <div class="page-head"><div><h1 class="page-title">Invitaciones</h1><p class="page-sub">Invitaciones enviadas sin aceptar</p></div></div>
    <div class="panel"><div class="panel-body" id="inv-table"><div class="empty">Cargando…</div></div></div>`);
  let invites;
  try { invites = await api("/api/users/invites/") || []; }
  catch (e) { $("inv-table").innerHTML = `<div class="empty">${esc(e.message)}</div>`; return; }
  drawInvitaciones(invites);
}
function drawInvitaciones(invites) {
  $("inv-table").innerHTML = invites.length
    ? `<table><thead><tr><th>Email</th><th>Rol</th><th>Empresa</th><th>Enviada</th><th>Vence</th><th></th></tr></thead><tbody>
        ${invites.map((i) => `
          <tr>
            <td><b>${esc(i.email)}</b></td>
            <td>${roleBadge(i.role)}</td>
            <td>${esc(i.empresa_nombre || "—")}</td>
            <td>${fmtFecha(i.created_at)}</td>
            <td>${fmtFecha(i.expires_at)}</td>
            <td><button class="btn btn-danger btn-sm" data-id="${i.id}" data-email="${esc(i.email)}">Eliminar</button></td>
          </tr>`).join("")}
      </tbody></table>`
    : '<div class="empty">No hay invitaciones pendientes.</div>';
  $("inv-table").querySelectorAll("button[data-id]").forEach((b) => {
    b.onclick = async () => {
      if (!confirmar("Eliminar la invitación de " + b.dataset.email + "?")) return;
      try { await api(`/api/users/invites/${b.dataset.id}/`, { method: "DELETE" }); toast("Invitación eliminada."); renderInvitaciones(); }
      catch (e) { toast(e.message, "err"); }
    };
  });
}

/* ── Pagos ───────────────────────────────────────────────────────────── */
let pagoFilterEmpresa = "";
async function renderPagos() {
  shell(`
    <div class="page-head">
      <div><h1 class="page-title">Pagos</h1><p class="page-sub">Cobranzas de las empresas por el servicio</p></div>
      <div class="toolbar">
        <select id="pago-filtro" style="padding:7px 10px;border:1px solid var(--border);border-radius:8px">
          <option value="">Todas las empresas</option>
        </select>
        <button class="btn btn-primary" id="btn-nuevo-pago">+ Registrar pago</button>
      </div>
    </div>
    <div class="panel"><div class="panel-body" id="pago-table"><div class="empty">Cargando…</div></div></div>`);
  if (!state.empresas.length) await loadEmpresas();
  $("pago-filtro").innerHTML += state.empresas.map((e) => `<option value="${e.id}">${esc(e.nombre)}</option>`).join("");
  $("pago-filtro").onchange = renderPagosData;
  $("btn-nuevo-pago").onclick = modalNuevoPago;
  await renderPagosData();
}
async function renderPagosData() {
  let pagos;
  try {
    const q = pagoFilterEmpresa ? `?empresa=${encodeURIComponent(pagoFilterEmpresa)}` : "";
    pagos = await api("/api/users/pagos/" + q) || [];
  } catch (e) { $("pago-table").innerHTML = `<div class="empty">${esc(e.message)}</div>`; return; }
  const badge = { RECIBIDO: "badge-green", PENDIENTE: "badge-amber", ANULADO: "badge-gray" };
  $("pago-table").innerHTML = pagos.length
    ? `<table><thead><tr><th>Fecha</th><th>Empresa</th><th>Concepto</th><th>Monto</th><th>Método</th><th>Estado</th><th></th></tr></thead><tbody>
        ${pagos.map((p) => `
          <tr>
            <td class="mono">${fmtFecha(p.fecha)}</td>
            <td><b>${esc(p.empresa_nombre || "—")}</b></td>
            <td>${esc(p.concepto_display || p.concepto)}</td>
            <td class="mono"><b>${fmtMonto(p)}</b></td>
            <td>${esc(p.metodo || "—")}</td>
            <td><span class="badge ${badge[p.estado] || "badge-gray"}">${esc(p.estado_display || p.estado)}</span></td>
            <td style="white-space:nowrap">
              <button class="btn btn-ghost btn-sm" data-o="edit" data-id="${p.id}">Editar</button>
              <button class="btn btn-danger btn-sm" data-o="del" data-id="${p.id}">Eliminar</button>
            </td>
          </tr>`).join("")}
      </tbody></table>`
    : '<div class="empty">No hay pagos registrados.</div>';
  $("pago-table").querySelectorAll("button[data-id]").forEach((b) => {
    b.onclick = () => {
      const p = pagos.find((x) => x.id === Number(b.dataset.id));
      if (b.dataset.o === "edit" && p) modalEditarPago(p);
      else if (p) modalEliminarPago(p);
    };
  });
}
function modalNuevoPago() {
  openModal("Registrar pago", [
    { key: "empresa", label: "Empresa", type: "select", required: true, options: state.empresas.map((e) => ({ value: e.id, label: e.nombre })) },
    { key: "concepto", label: "Concepto", type: "select", required: true, options: CONCEPTOS_PAGO.map((c) => ({ value: c, label: c })) },
    { key: "monto", label: "Monto", type: "number", required: true },
    { key: "moneda", label: "Moneda", required: true, value: "USD" },
    { key: "fecha", label: "Fecha", type: "date", required: true, value: new Date().toISOString().slice(0, 10) },
    { key: "metodo", label: "Método de pago", hint: "Transferencia, efectivo, etc." },
    { key: "estado", label: "Estado", type: "select", required: true, options: ESTADOS_PAGO.map((e) => ({ value: e, label: e })), value: "RECIBIDO" },
    { key: "referencia", label: "Referencia / comprobante" },
  ], {}, async (d) => {
    const created = await api("/api/users/pagos/", { method: "POST", body: JSON.stringify(d) });
    toast("Pago registrado (" + fmtMonto(created) + ").");
    renderPagosData();
  });
}
function modalEditarPago(p) {
  openModal("Editar pago de " + p.empresa_nombre, [
    { key: "concepto", label: "Concepto", type: "select", required: true, options: CONCEPTOS_PAGO.map((c) => ({ value: c, label: c })), value: p.concepto },
    { key: "monto", label: "Monto", type: "number", required: true, value: p.monto },
    { key: "moneda", label: "Moneda", required: true, value: p.moneda },
    { key: "fecha", label: "Fecha", type: "date", required: true, value: p.fecha },
    { key: "metodo", label: "Método", value: p.metodo },
    { key: "estado", label: "Estado", type: "select", required: true, options: ESTADOS_PAGO.map((e) => ({ value: e, label: e })), value: p.estado },
    { key: "referencia", label: "Referencia", value: p.referencia },
    { key: "observaciones", label: "Observaciones", type: "textarea" },
  ], {}, async (d) => {
    await api(`/api/users/pagos/${p.id}/`, { method: "PATCH", body: JSON.stringify(d) });
    toast("Pago actualizado.");
    renderPagosData();
  });
}
function modalEliminarPago(p) {
  if (!confirmar("Eliminar el pago de " + p.empresa_nombre + " por " + fmtMonto(p) + "?")) return;
  api(`/api/users/pagos/${p.id}/`, { method: "DELETE" }).then(() => { toast("Pago eliminado."); });
  renderPagosData();
}

/* ── Registros / Auditoría ───────────────────────────────────────────── */
async function renderRegistros() {
  shell(`
    <div class="page-head"><div><h1 class="page-title">Registros</h1><p class="page-sub">Bitácora de acciones administrativas</p></div>
      <div><button class="btn btn-ghost" id="btn-ver-empleados">Ver registros de datos</button></div></div>
    <div class="panel"><div class="panel-body" id="audit-table"><div class="empty">Cargando…</div></div></div>`);
  let audit;
  try { audit = await api("/api/users/audit/") || []; }
  catch (e) { $("audit-table").innerHTML = `<div class="empty">${esc(e.message)}</div>`; return; }
  $("audit-table").innerHTML = audit.length
    ? `<table><thead><tr><th>Cuándo</th><th>Quién</th><th>Acción</th><th>Objetivo</th><th>Detalle</th></tr></thead><tbody>
        ${audit.map((a) => `
          <tr>
            <td class="mono" nowrap>${fmtHora(a.created_at)}</td>
            <td><b>${esc(a.actor_username || "—")}</b></td>
            <td><span class="badge badge-green">${esc(a.action)}</span></td>
            <td>${esc(a.target_desc || (a.target_type + (a.target_id ? " #" + a.target_id : "")) || "—")}</td>
            <td class="code" style="font-size:11px">${esc(JSON.stringify(a.payload || {}))}</td>
          </tr>`).join("")}
      </tbody></table>`
    : '<div class="empty">Sin acciones registradas todavía.</div>';
  $("btn-ver-empleados").onclick = () => {
    const nota = "Los registros de datos (quién cargó/qué cambió en labores, campos, insumos) se exponen en el detalle de cada Labor de la app (cargada_por / revisada_por). La bitácora completa del panel se centraliza en esta sección y crecerá con cada registro de datos.";
    toast(nota, "warn");
  };
}

function renderNotFound() {
  shell(`<div class="page-head"><h1 class="page-title">404</h1></div><div class="empty">Sección no encontrada.</div>`);
}

/* ── Init ────────────────────────────────────────────────────────────── */
function init() {
  state.token = localStorage.getItem("ceo_admin_token") || null;
  if (state.token) {
    api("/api/users/auth/me/").then((me) => {
      if (me.role !== "ADMIN_PRINCIPAL") { logout(); return; }
      state.user = me;
      if (!location.hash || location.hash === "#/login") location.hash = "#/resumen";
      router();
    }).catch(() => { /* api() already logs out on 401 */ });
  } else {
    location.hash = "#/login";
    router();
  }
  window.addEventListener("hashchange", router);
  $("modal-close").onclick = hideModal;
  $("modal-cancel").onclick = hideModal;
  $("modal-backdrop").addEventListener("click", (e) => { if (e.target === $("modal-backdrop")) hideModal(); });
}

init();