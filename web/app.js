"use strict";

const $ = (id) => document.getElementById(id);

async function api(url, method, body) {
  const opts = { method: method || "GET", headers: {} };
  if (body !== undefined && body !== null) {
    opts.headers["Content-Type"] = "application/json";
    opts.body = JSON.stringify(body);
  }
  const r = await fetch(url, opts);
  const data = await r.json().catch(() => ({}));
  if (!r.ok) {
    throw new Error(data.detail || r.statusText);
  }
  return data;
}

function log(obj) {
  const out = $("out");
  if (out) out.textContent = JSON.stringify(obj, null, 2);
}

// ---------- Mentor helpers ----------
async function importLocal() {
  const path = $("localPath").value.trim();
  try { log(await api("/api/projects/local", "POST", { path })); }
  catch (e) { log({ error: String(e) }); }
}
async function importGit() {
  const url = $("gitUrl").value.trim();
  try { log(await api("/api/projects/git", "POST", { url })); }
  catch (e) { log({ error: String(e) }); }
}
async function importZip() {
  const file = $("zipFile").files[0];
  if (!file) { log({ error: "choose a zip file" }); return; }
  const form = new FormData();
  form.append("file", file);
  try {
    const r = await fetch("/api/projects/upload", { method: "POST", body: form });
    log(await r.json());
  } catch (e) { log({ error: String(e) }); }
}
function projectId() { return $("projectId").value.trim(); }
async function analyzeProject() {
  try { log(await api(`/api/projects/${projectId()}/analyze`, "POST", {})); }
  catch (e) { log({ error: String(e) }); }
}
async function generatePlan() {
  try { log(await api(`/api/projects/${projectId()}/plans/generate`, "POST", {})); }
  catch (e) { log({ error: String(e) }); }
}
async function approvePlan() {
  const pid = $("planId").value.trim();
  try { log(await api(`/api/plans/${pid}/approve`, "POST")); }
  catch (e) { log({ error: String(e) }); }
}
async function generateAssignments() {
  const pid = $("planId").value.trim();
  try { log(await api(`/api/plans/${pid}/assignments/generate`, "POST", {})); }
  catch (e) { log({ error: String(e) }); }
}
async function savePlan() {
  const pid = $("planId").value.trim();
  const plan = JSON.parse($("planJson").value);
  try { log(await api(`/api/plans/${pid}`, "PATCH", plan)); }
  catch (e) { log({ error: String(e) }); }
}
async function loadAssignment() {
  const aid = $("assignmentId").value.trim();
  try { const d = await api(`/api/assignments/${aid}?view=mentor`); $("assignmentPreview").textContent = JSON.stringify(d, null, 2); }
  catch (e) { log({ error: String(e) }); }
}
async function publishAssignment() {
  const aid = $("assignmentId").value.trim();
  try { log(await api(`/api/assignments/${aid}/publish`, "POST")); }
  catch (e) { log({ error: String(e) }); }
}
async function createWorkspace() {
  const aid = $("assignmentId").value.trim();
  try { log(await api(`/api/assignments/${aid}/workspace`, "POST")); }
  catch (e) { log({ error: String(e) }); }
}

// ---------- Learner helpers ----------
let currentAssignment = null;
let history = [];

async function loadLearnerAssignment() {
  const aid = $("assignmentId").value.trim();
  if (!aid) return;
  currentAssignment = await api(`/api/assignments/${aid}?view=learner`);
  const a = currentAssignment;
  $("title").textContent = `${a.id} — ${a.title}`;
  $("context").textContent = a.business_context;
  $("task").textContent = a.task;
  $("approach").textContent = (a.approach || []).join("\n");
  if (a.starter_files && a.starter_files.length) {
    $("code").value = a.starter_files[0].content;
  }
  $("specCard").style.display = "block";
  $("codeCard").style.display = "block";
}

async function submit() {
  const aid = currentAssignment.id;
  const code = $("code").value;
  const message = $("msg").value;

  // Evaluate through submission endpoint
  await api(`/api/assignments/${aid}/submissions`, "POST", { message, code });

  // Then chat for pedagogical feedback
  const res = await api(`/api/assignments/${aid}/chat`, "POST", {
    message,
    code,
    history,
  });
  history.push({ role: "user", content: message });
  history.push({ role: "assistant", content: res.reply });

  $("resultCard").style.display = "block";
  const status = $("status");
  status.textContent = res.passed ? "PASSED" : "NOT PASSED";
  status.className = "status " + (res.passed ? "pass" : "fail");
  $("reply").textContent = res.reply;
  $("execOut").textContent = res.executor_output || (res.evaluation ? JSON.stringify(res.evaluation, null, 2) : "");
}

async function hint() {
  const aid = currentAssignment.id;
  const res = await api(`/api/assignments/${aid}/chat`, "POST", {
    message: "Please give me the next hint.",
    history,
  });
  history.push({ role: "user", content: "Please give me the next hint." });
  history.push({ role: "assistant", content: res.reply });
  $("resultCard").style.display = "block";
  $("reply").textContent = res.reply;
}

// Wire up buttons
window.importLocal = importLocal;
window.importGit = importGit;
window.importZip = importZip;
window.analyzeProject = analyzeProject;
window.generatePlan = generatePlan;
window.approvePlan = approvePlan;
window.generateAssignments = generateAssignments;
window.savePlan = savePlan;
window.loadAssignment = loadAssignment;
window.publishAssignment = publishAssignment;
window.createWorkspace = createWorkspace;
window.loadLearnerAssignment = loadLearnerAssignment;
window.submit = submit;
window.hint = hint;

// Learner page: auto-load assignment from query string
const urlParams = new URLSearchParams(window.location.search);
const aidFromUrl = urlParams.get("id");
if (aidFromUrl && $("assignmentId")) {
  $("assignmentId").value = aidFromUrl;
  loadLearnerAssignment();
}