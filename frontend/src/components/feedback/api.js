const API = "http://localhost:8000/api";

export async function listProjects() {
  const r = await fetch(`${API}/projects`);
  return r.json();
}

export async function listPeople() {
  const r = await fetch(`${API}/people`);
  return r.json();
}

export async function createFeedback(data) {
  const r = await fetch(`${API}/feedback`, {
    method: "POST",
    headers: {"Content-Type":"application/json"},
    body: JSON.stringify(data)
  });
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

export async function listFeedback(params = {}) {
  const qs = new URLSearchParams(params).toString();
  const r = await fetch(`${API}/feedback?${qs}`);
  return r.json();
}

export async function getFeedback(id) {
  const r = await fetch(`${API}/feedback/${id}`);
  return r.json();
}

export async function patchFeedback(id, data) {
  const r = await fetch(`${API}/feedback/${id}`, {
    method: "PATCH",
    headers: {"Content-Type":"application/json"},
    body: JSON.stringify(data)
  });
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

export async function addComment(id, data) {
  const r = await fetch(`${API}/feedback/${id}/comments`, {
    method: "POST",
    headers: {"Content-Type":"application/json"},
    body: JSON.stringify(data)
  });
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

export async function listComments(id) {
  const r = await fetch(`${API}/feedback/${id}/comments`);
  return r.json();
}
