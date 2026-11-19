const API = 'http://127.0.0.1:8000/api';

async function request(path, opts = {}) {
  const token = localStorage.getItem('token');
  const headers = { ...(opts.headers || {}) };
  if (token) headers.Authorization = `Bearer ${token}`;
  let r;
  try {
    r = await fetch(API + path, { ...opts, headers });
  } catch {
    throw new Error('Cannot reach the server. Make sure the backend is running on http://127.0.0.1:8000');
  }
  let d = await r.json().catch(() => ({}));
  if (r.status === 401) { localStorage.clear(); window.location.href = '/login'; throw new Error('Session expired.'); }
  if (!r.ok) throw new Error(d.detail || `Request failed (${r.status})`);
  return d;
}

export const api = {
  login:    x => request('/auth/login',    { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(x) }),
  register: x => request('/auth/register', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(x) }),
  me:          () => request('/me'),
  jobs:        () => request('/jobs'),
  myJobs:      () => request('/jobs/mine'),
  createJob:    x => request('/jobs', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(x) }),
  applications: () => request('/candidate/applications'),
  application: id => request(`/applications/${id}`),
  upload: (id, file) => {
    const f = new FormData(); f.append('resume', file);
    return request(`/applications/${id}/resume`, { method: 'POST', body: f });
  },
  // AI Adaptive Interview
  startInterview:   id => request(`/applications/${id}/interview/start`, { method: 'POST' }),
  submitInterview: (id, answers) => request(`/applications/${id}/interview/submit`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ answers }),
  }),
  // Python Coding Test
  startCoding:   id => request(`/applications/${id}/coding/start`, { method: 'POST' }),
  submitCoding: (id, code) => request(`/applications/${id}/coding/submit`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ code }),
  }),
  // Project & Portfolio Verification
  verifyProjects: (id, payload) => request(`/applications/${id}/projects/verify`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload),
  }),
  getProjects: id => request(`/applications/${id}/projects`),
  // Role-Specific Skill Assessment
  startSkills: id => request(`/applications/${id}/skills/start`, { method: 'POST' }),
  submitSkills: (id, answers) => request(`/applications/${id}/skills/submit`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ answers }),
  }),
  getSkills: id => request(`/applications/${id}/skills`),
  // Communication & Situational Judgment
  startSituational: id => request(`/applications/${id}/situational/start`, { method: 'POST' }),
  submitSituational: (id, responses) => request(`/applications/${id}/situational/submit`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ responses }),
  }),
  getSituational: id => request(`/applications/${id}/situational`),
  // Explainable AI & Analysis
  explain: id => request(`/applications/${id}/explain`),
  jobAnalysis: jobId => request(`/recruiter/jobs/${jobId}/analysis`),
  // Test Scheduling
  scheduleTest: (aid, payload) => request(`/applications/${aid}/schedule`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload),
  }),
  deleteSchedule: sid => request(`/schedules/${sid}`, { method: 'DELETE' }),
  // Candidates & Status
  candidates: id => request(`/recruiter/jobs/${id}/candidates`),
  status: (id, status) => request(`/applications/${id}/status`, {
    method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ status }),
  }),
  uploadRecording: (id, blob) => {
    const f = new FormData(); f.append('recording', blob, 'interview.webm');
    return request(`/applications/${id}/recording`, { method: 'POST', body: f });
  },
  recordings: id => request(`/applications/${id}/recordings`),
  // ── Candidate Support Chatbot ──────────────────────────────────────────────
  chatMessage: (message, session_id) => request('/chatbot/message', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, session_id }),
  }),
  chatHistory: session_id => request(`/chatbot/history?session_id=${encodeURIComponent(session_id)}`),
  // ── Smart Candidate Pipeline ───────────────────────────────────────────────
  pipeline: jobId => request(`/recruiter/jobs/${jobId}/pipeline`),
  // ── Candidate 360° Profile ─────────────────────────────────────────────────
  profile360: aid => request(`/applications/${aid}/profile360`),
  // ── Multi-Job Matching ─────────────────────────────────────────────────────
  jobMatches: () => request('/candidate/job-matches'),
};

