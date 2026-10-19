const API_BASE = import.meta.env.VITE_API_BASE || "http://127.0.0.1:8000";

async function request(path, options = {}) {
  let response;
  try {
    response = await fetch(`${API_BASE}${path}`, options);
  } catch {
    throw new Error(`Cannot reach the API at ${API_BASE}. Start the backend first.`);
  }
  const body = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(body.detail || `Request failed (${response.status})`);
  return body;
}

export const checkHealth = async () => (await request("/health")).status === "ok";
export const getCandidates = (filters = {}) => {
  const params = new URLSearchParams();
  Object.entries(filters).forEach(([key, value]) => {
    if (value !== "" && value !== null && value !== undefined && value !== false) params.set(key, String(value));
  });
  return request(`/api/candidates?${params.toString()}`);
};
export const getCandidateFacets = () => request("/api/candidate-facets");
export const updateCandidate = (id, patch) => request(`/api/candidates/${encodeURIComponent(id)}`, {
  method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify(patch),
});
export const getFitSummary = (id, job_role = "") => request(`/api/candidates/${encodeURIComponent(id)}/fit-summary`, {
  method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ job_role }),
});
