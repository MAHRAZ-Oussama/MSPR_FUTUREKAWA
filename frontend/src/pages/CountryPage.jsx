import { useEffect, useState, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { getCountryLots, getCountryWarehouses } from "../api.js";
import StatusBadge from "../components/StatusBadge.jsx";
import Spinner from "../components/Spinner.jsx";

const COUNTRY_NAMES = { BR: "🇧🇷 Brésil", EC: "🇪🇨 Équateur", CO: "🇨🇴 Colombie" };
const REFRESH_MS = 30_000;

const s = {
  header:   { display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 20 },
  title:    { fontSize: 24, fontWeight: 700 },
  filters:  { display: "flex", gap: 12, marginBottom: 20, flexWrap: "wrap" },
  select:   { padding: "6px 12px", borderRadius: 6, border: "1px solid #ccc", fontSize: 14 },
  table:    { width: "100%", borderCollapse: "collapse", background: "#fff", borderRadius: 12,
               overflow: "hidden", boxShadow: "0 2px 8px rgba(0,0,0,0.07)" },
  th:       { background: "#1a3a2a", color: "#fff", padding: "12px 16px", textAlign: "left", fontWeight: 600 },
  td:       { padding: "11px 16px", borderBottom: "1px solid #f0f0f0", fontSize: 14 },
  trHover:  { cursor: "pointer" },
  btnLink:  {
    background: "#1a3a2a", color: "#fff", border: "none", borderRadius: 6,
    padding: "5px 12px", cursor: "pointer", fontSize: 13,
  },
  expired:  { color: "#dc3545", fontWeight: 600 },
};

function daysAgo(dateStr) {
  const diff = Math.floor((Date.now() - new Date(dateStr).getTime()) / 86400000);
  return diff;
}

export default function CountryPage() {
  const { country } = useParams();
  const navigate = useNavigate();
  const [lots, setLots] = useState([]);
  const [warehouses, setWarehouses] = useState([]);
  const [status, setStatus] = useState("");
  const [warehouseId, setWarehouseId] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const load = useCallback(async () => {
    try {
      const params = {};
      if (status)      params.status       = status;
      if (warehouseId) params.warehouse_id  = warehouseId;
      const [lotsData, whData] = await Promise.all([
        getCountryLots(country, params),
        getCountryWarehouses(country),
      ]);
      setLots(lotsData);
      setWarehouses(whData);
      setError(null);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, [country, status, warehouseId]);

  useEffect(() => {
    setLoading(true);
    load();
    const id = setInterval(load, REFRESH_MS);
    return () => clearInterval(id);
  }, [load]);

  if (loading) return <Spinner />;
  if (error)   return <div style={{ color: "#dc3545", padding: 24 }}>Backend indisponible : {error}</div>;

  return (
    <div>
      <div style={s.header}>
        <h1 style={s.title}>{COUNTRY_NAMES[country] ?? country} — Lots de café</h1>
        <span style={{ color: "#555", fontSize: 14 }}>{lots.length} lot(s) — ordre FIFO</span>
      </div>

      <div style={s.filters}>
        <select style={s.select} value={status} onChange={e => setStatus(e.target.value)}>
          <option value="">Tous les statuts</option>
          <option value="CONFORME">Conforme</option>
          <option value="EN_ALERTE">En alerte</option>
          <option value="PERIME">Périmé</option>
        </select>
        <select style={s.select} value={warehouseId} onChange={e => setWarehouseId(e.target.value)}>
          <option value="">Tous les entrepôts</option>
          {warehouses.map(wh => (
            <option key={wh.id} value={wh.id}>{wh.code}</option>
          ))}
        </select>
      </div>

      <table style={s.table}>
        <thead>
          <tr>
            {["ID Lot", "Date stockage ↑", "Ancienneté", "Variété", "Poids (kg)", "Statut", ""].map(h => (
              <th key={h} style={s.th}>{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {lots.length === 0 ? (
            <tr><td colSpan={7} style={{ ...s.td, textAlign: "center", color: "#888" }}>Aucun lot trouvé</td></tr>
          ) : lots.map(lot => {
            const days = daysAgo(lot.storage_date);
            return (
              <tr
                key={lot.id}
                style={s.trHover}
                onClick={() => navigate(`/pays/${country}/lots/${lot.id}`)}
                onMouseEnter={e => e.currentTarget.style.background = "#f8f9fa"}
                onMouseLeave={e => e.currentTarget.style.background = ""}
              >
                <td style={s.td}><code style={{ fontSize: 13 }}>{lot.id}</code></td>
                <td style={s.td}>{new Date(lot.storage_date).toLocaleDateString("fr-FR")}</td>
                <td style={{ ...s.td, ...(days > 365 ? s.expired : {}) }}>{days} j</td>
                <td style={s.td}>{lot.variete ?? "—"}</td>
                <td style={s.td}>{lot.poids_kg ? `${lot.poids_kg} kg` : "—"}</td>
                <td style={s.td}><StatusBadge value={lot.status} /></td>
                <td style={s.td}>
                  <button
                    style={s.btnLink}
                    onClick={e => { e.stopPropagation(); navigate(`/pays/${country}/lots/${lot.id}`); }}
                  >Voir →</button>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
