import { useEffect, useState, useCallback } from "react";
import { getAlerts, resolveAlert } from "../api.js";
import StatusBadge from "../components/StatusBadge.jsx";
import Spinner from "../components/Spinner.jsx";

const REFRESH_MS = 30_000;
const COUNTRY_NAMES = { BR: "🇧🇷 Brésil", EC: "🇪🇨 Équateur", CO: "🇨🇴 Colombie" };

const ALERT_ICONS = {
  TEMP_OUT_OF_RANGE:     "🌡️",
  HUMIDITY_OUT_OF_RANGE: "💧",
  LOT_EXPIRED:           "⏰",
};

const s = {
  title:   { fontSize: 24, fontWeight: 700, marginBottom: 20 },
  filters: { display: "flex", gap: 12, marginBottom: 20, flexWrap: "wrap", alignItems: "center" },
  select:  { padding: "6px 12px", borderRadius: 6, border: "1px solid #ccc", fontSize: 14 },
  table:   { width: "100%", borderCollapse: "collapse", background: "#fff", borderRadius: 12,
              overflow: "hidden", boxShadow: "0 2px 8px rgba(0,0,0,0.07)" },
  th:      { background: "#1a3a2a", color: "#fff", padding: "12px 16px", textAlign: "left", fontWeight: 600 },
  td:      { padding: "11px 16px", borderBottom: "1px solid #f0f0f0", fontSize: 14 },
  btnResolve: {
    background: "#1a3a2a", color: "#fff", border: "none", borderRadius: 6,
    padding: "4px 10px", cursor: "pointer", fontSize: 12,
  },
  degraded: {
    background: "#fff3cd", border: "1px solid #ffc107",
    borderRadius: 8, padding: "10px 16px", marginBottom: 16, color: "#856404",
  },
};

export default function AlertsPage() {
  const [data, setData] = useState({ alerts: [], degraded_countries: [] });
  const [loading, setLoading] = useState(true);
  const [severity, setSeverity] = useState("");
  const [alertType, setAlertType] = useState("");
  const [countryFilter, setCountryFilter] = useState("");
  const [activeOnly, setActiveOnly] = useState(false);

  const load = useCallback(async () => {
    try {
      const params = {};
      if (severity)   params.severity   = severity;
      if (alertType)  params.alert_type = alertType;
      if (activeOnly) params.active_only = "true";
      const d = await getAlerts(params);
      setData(d);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }, [severity, alertType, activeOnly]);

  useEffect(() => {
    setLoading(true);
    load();
    const id = setInterval(load, REFRESH_MS);
    return () => clearInterval(id);
  }, [load]);

  const handleResolve = async (country, alertId) => {
    await resolveAlert(country, alertId);
    load();
  };

  if (loading) return <Spinner />;

  const displayed = countryFilter
    ? data.alerts.filter(a => a.country === countryFilter)
    : data.alerts;

  return (
    <div>
      <h1 style={s.title}>🔔 Alertes</h1>

      {data.degraded_countries?.length > 0 && (
        <div style={s.degraded}>
          ⚠️ Données partielles — pays indisponibles : {data.degraded_countries.join(", ")}
        </div>
      )}

      <div style={s.filters}>
        <select style={s.select} value={severity} onChange={e => setSeverity(e.target.value)}>
          <option value="">Toutes sévérités</option>
          <option value="CRITICAL">CRITICAL</option>
          <option value="WARNING">WARNING</option>
        </select>
        <select style={s.select} value={alertType} onChange={e => setAlertType(e.target.value)}>
          <option value="">Tous types</option>
          <option value="TEMP_OUT_OF_RANGE">Température</option>
          <option value="HUMIDITY_OUT_OF_RANGE">Humidité</option>
          <option value="LOT_EXPIRED">Lot périmé</option>
        </select>
        <select style={s.select} value={countryFilter} onChange={e => setCountryFilter(e.target.value)}>
          <option value="">Tous les pays</option>
          <option value="BR">🇧🇷 Brésil</option>
          <option value="EC">🇪🇨 Équateur</option>
          <option value="CO">🇨🇴 Colombie</option>
        </select>
        <label style={{ fontSize: 14, display: "flex", gap: 6, alignItems: "center" }}>
          <input type="checkbox" checked={activeOnly} onChange={e => setActiveOnly(e.target.checked)} />
          Actives uniquement
        </label>
        <span style={{ color: "#555", fontSize: 14, marginLeft: "auto" }}>
          {displayed.length} alerte(s)
        </span>
      </div>

      <table style={s.table}>
        <thead>
          <tr>
            {["Type", "Sévérité", "Pays", "Entrepôt", "Message", "Créée le", "Résolue", ""].map(h => (
              <th key={h} style={s.th}>{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {displayed.length === 0 ? (
            <tr>
              <td colSpan={8} style={{ ...s.td, textAlign: "center", color: "#888" }}>
                Aucune alerte
              </td>
            </tr>
          ) : displayed.map(alert => (
            <tr key={`${alert.country}-${alert.id}`}>
              <td style={s.td}>
                {ALERT_ICONS[alert.alert_type] ?? "📋"} {alert.alert_type.replace(/_/g, " ")}
              </td>
              <td style={s.td}><StatusBadge value={alert.severity} /></td>
              <td style={s.td}>{COUNTRY_NAMES[alert.country] ?? alert.country}</td>
              <td style={s.td}>{alert.warehouse_id}</td>
              <td style={{ ...s.td, maxWidth: 280, fontSize: 13 }}>{alert.message ?? "—"}</td>
              <td style={s.td}>
                {new Date(alert.created_at).toLocaleString("fr-FR")}
              </td>
              <td style={s.td}>
                {alert.resolved_at
                  ? new Date(alert.resolved_at).toLocaleString("fr-FR")
                  : <span style={{ color: "#dc3545" }}>Active</span>
                }
              </td>
              <td style={s.td}>
                {!alert.resolved_at && (
                  <button
                    style={s.btnResolve}
                    onClick={() => handleResolve(alert.country, alert.id)}
                  >
                    Résoudre
                  </button>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
