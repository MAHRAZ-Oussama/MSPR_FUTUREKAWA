const BASE = "/api";

export async function fetchJSON(path) {
  const res = await fetch(BASE + path);
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return res.json();
}

export const getDashboard   = () => fetchJSON("/dashboard/summary");
export const getCountryLots = (country, params = {}) => {
  const qs = new URLSearchParams(params).toString();
  return fetchJSON(`/countries/${country}/lots${qs ? "?" + qs : ""}`);
};
export const getLotDetail      = (country, lotId) => fetchJSON(`/countries/${country}/lots/${lotId}`);
export const getCountryWarehouses = (country) => fetchJSON(`/countries/${country}/warehouses`);
export const getAlerts         = (params = {}) => {
  const qs = new URLSearchParams(params).toString();
  return fetchJSON(`/alerts${qs ? "?" + qs : ""}`);
};
export const resolveAlert = (country, alertId) =>
  fetch(`${BASE}/countries/${country}/alerts/${alertId}/resolve`, { method: "POST" }).then(r => r.json());
