import { useEffect, useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { getDashboard } from "../api.js";
import Spinner from "../components/Spinner.jsx";

const COUNTRY_NAMES = { BR: "🇧🇷 Brésil", EC: "🇪🇨 Équateur", CO: "🇨🇴 Colombie" };
const REFRESH_MS = 30_000;

const s = {
  title: { fontSize: 24, fontWeight: 700, marginBottom: 8 },
  sub:   { color: "#555", marginBottom: 24 },
  degraded: {
    background: "#fff3cd", border: "1px solid #ffc107",
    borderRadius: 8, padding: "10px 16px", marginBottom: 20, color: "#856404",
  },
  statsRow: { display: "flex", gap: 16, flexWrap: "wrap", marginBottom: 32 },
  statCard: {
    background: "#fff", borderRadius: 12, padding: "20px 28px",
    boxShadow: "0 2px 8px rgba(0,0,0,0.07)", flex: "1 1 140px", minWidth: 120,
  },
  statNum:   { fontSize: 36, fontWeight: 800, lineHeight: 1 },
  statLabel: { color: "#666", fontSize: 14, marginTop: 4 },
  grid: { display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(280px,1fr))", gap: 20 },
  card: {
    background: "#fff", borderRadius: 12, padding: 24,
    boxShadow: "0 2px 8px rgba(0,0,0,0.07)", cursor: "pointer",
    transition: "box-shadow 0.15s", border: "2px solid transparent",
  },
  cardOffline: { border: "2px solid #dc3545", opacity: 0.6 },
  cardTitle: { fontWeight: 700, fontSize: 18, marginBottom: 12 },
  row: { display: "flex", justifyContent: "space-between", fontSize: 14, marginBottom: 6 },
};

function StatCard({ num, label, color = "#1a3a2a" }) {
  return (
    <div style={s.statCard}>
      <div style={{ ...s.statNum, color }}>{num}</div>
      <div style={s.statLabel}>{label}</div>
    </div>
  );
}

function CountryCard({ data, isOffline, onClick }) {
  return (
    <div
      style={{ ...s.card, ...(isOffline ? s.cardOffline : {}) }}
      onClick={onClick}
      onMouseEnter={e => e.currentTarget.style.boxShadow = "0 4px 16px rgba(0,0,0,0.13)"}
      onMouseLeave={e => e.currentTarget.style.boxShadow = "0 2px 8px rgba(0,0,0,0.07)"}
    >
      <div style={s.cardTitle}>{COUNTRY_NAMES[data?.country] ?? data?.country}</div>
      {isOffline ? (
        <div style={{ color: "#dc3545", fontWeight: 600 }}>Hors ligne</div>
      ) : (
        <>
          <div style={s.row}><span>Lots totaux</span><strong>{data.total_lots}</strong></div>
          <div style={s.row}><span style={{color:"#155724"}}>✅ Conformes</span><strong>{data.lots_conformes}</strong></div>
          <div style={s.row}><span style={{color:"#856404"}}>⚠️ En alerte</span><strong>{data.lots_en_alerte}</strong></div>
          <div style={s.row}><span style={{color:"#721c24"}}>🔴 Périmés</span><strong>{data.lots_perimes}</strong></div>
          <div style={s.row}><span>Alertes actives</span><strong style={{color:"#dc3545"}}>{data.active_alerts}</strong></div>
        </>
      )}
    </div>
  );
}

export default function Dashboard() {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [lastUpdate, setLastUpdate] = useState(null);
  const navigate = useNavigate();

  const load = useCallback(async () => {
    try {
      const d = await getDashboard();
      setData(d);
      setLastUpdate(new Date());
      setError(null);
    } catch (e) {
      setError(e.message);
    }
  }, []);

  useEffect(() => {
    load();
    const id = setInterval(load, REFRESH_MS);
    return () => clearInterval(id);
  }, [load]);

  if (!data && !error) return <Spinner />;
  if (error) return <div style={{ color: "#dc3545", padding: 24 }}>Erreur : {error}</div>;

  const { total_lots, lots_conformes, lots_en_alerte, lots_perimes, active_alerts,
          degraded_countries = [], countries = [] } = data;

  const allCountries = ["BR", "EC", "CO"];

  return (
    <div>
      <h1 style={s.title}>Tableau de bord global</h1>
      <p style={s.sub}>
        Rafraîchissement automatique toutes les 30s
        {lastUpdate && ` — Dernière MAJ : ${lastUpdate.toLocaleTimeString("fr-FR")}`}
      </p>

      {degraded_countries.length > 0 && (
        <div style={s.degraded}>
          ⚠️ Pays en mode dégradé (backend indisponible) : {degraded_countries.join(", ")}
        </div>
      )}

      <div style={s.statsRow}>
        <StatCard num={total_lots}     label="Lots totaux" />
        <StatCard num={lots_conformes} label="Conformes"   color="#155724" />
        <StatCard num={lots_en_alerte} label="En alerte"   color="#856404" />
        <StatCard num={lots_perimes}   label="Périmés"     color="#721c24" />
        <StatCard num={active_alerts}  label="Alertes actives" color="#dc3545" />
      </div>

      <h2 style={{ marginBottom: 16, fontSize: 18, fontWeight: 600 }}>Par pays</h2>
      <div style={s.grid}>
        {allCountries.map(code => {
          const countryData = countries.find(c => c.country === code);
          const isOffline = degraded_countries.includes(code);
          return (
            <CountryCard
              key={code}
              data={countryData ?? { country: code }}
              isOffline={isOffline}
              onClick={() => !isOffline && navigate(`/pays/${code}`)}
            />
          );
        })}
      </div>
    </div>
  );
}
