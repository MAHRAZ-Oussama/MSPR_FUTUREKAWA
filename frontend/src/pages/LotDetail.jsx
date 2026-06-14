import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
  Chart as ChartJS,
  CategoryScale, LinearScale, PointElement, LineElement,
  Title, Tooltip, Legend,
} from "chart.js";
import { Line } from "react-chartjs-2";
import { getLotDetail } from "../api.js";
import StatusBadge from "../components/StatusBadge.jsx";
import Spinner from "../components/Spinner.jsx";

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend);

const COUNTRY_NAMES = { BR: "🇧🇷 Brésil", EC: "🇪🇨 Équateur", CO: "🇨🇴 Colombie" };

const s = {
  back:    { color: "#1a3a2a", cursor: "pointer", fontWeight: 600, marginBottom: 16, display: "inline-block" },
  title:   { fontSize: 22, fontWeight: 700, marginBottom: 20 },
  card:    { background: "#fff", borderRadius: 12, padding: 24, boxShadow: "0 2px 8px rgba(0,0,0,0.07)", marginBottom: 24 },
  infoGrid:{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(200px,1fr))", gap: 16 },
  infoItem:{ display: "flex", flexDirection: "column", gap: 4 },
  label:   { fontSize: 12, color: "#888", fontWeight: 600, textTransform: "uppercase" },
  value:   { fontSize: 15, fontWeight: 500 },
  statsRow:{ display: "flex", gap: 20, flexWrap: "wrap", marginTop: 16 },
  stat:    { background: "#f8f9fa", borderRadius: 8, padding: "12px 20px", textAlign: "center" },
};

function InfoItem({ label, value }) {
  return (
    <div style={s.infoItem}>
      <span style={s.label}>{label}</span>
      <span style={s.value}>{value ?? "—"}</span>
    </div>
  );
}

function StatsBar({ measurements }) {
  if (!measurements || measurements.length === 0) return null;
  const temps = measurements.map(m => parseFloat(m.temperature_c)).filter(Boolean);
  const hums  = measurements.map(m => parseFloat(m.humidity_pct)).filter(Boolean);
  const fmt   = v => v.toFixed(1);
  return (
    <div style={s.statsRow}>
      <div style={s.stat}>
        <div style={{ fontSize: 12, color: "#888" }}>Temp. min/moy/max (°C)</div>
        <div style={{ fontWeight: 700, color: "#dc3545" }}>
          {fmt(Math.min(...temps))} / {fmt(temps.reduce((a,b) => a+b,0)/temps.length)} / {fmt(Math.max(...temps))}
        </div>
      </div>
      <div style={s.stat}>
        <div style={{ fontSize: 12, color: "#888" }}>Hum. min/moy/max (%)</div>
        <div style={{ fontWeight: 700, color: "#0066cc" }}>
          {fmt(Math.min(...hums))} / {fmt(hums.reduce((a,b) => a+b,0)/hums.length)} / {fmt(Math.max(...hums))}
        </div>
      </div>
      <div style={s.stat}>
        <div style={{ fontSize: 12, color: "#888" }}>Mesures</div>
        <div style={{ fontWeight: 700 }}>{measurements.length}</div>
      </div>
    </div>
  );
}

export default function LotDetail() {
  const { country, lotId } = useParams();
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    getLotDetail(country, lotId)
      .then(setData)
      .catch(e => setError(e.message));
  }, [country, lotId]);

  if (!data && !error) return <Spinner />;
  if (error) return <div style={{ color: "#dc3545", padding: 24 }}>Erreur : {error}</div>;

  const { measurements = [], ...lot } = data;
  const days = Math.floor((Date.now() - new Date(lot.storage_date).getTime()) / 86400000);
  const showPoints = measurements.length <= 200;

  const labels = measurements.map(m =>
    new Date(m.measured_at).toLocaleTimeString("fr-FR", { hour: "2-digit", minute: "2-digit" })
  );
  const chartData = {
    labels,
    datasets: [
      {
        label: "Température (°C)",
        data: measurements.map(m => m.temperature_c),
        borderColor: "#dc3545",
        backgroundColor: "rgba(220,53,69,0.08)",
        yAxisID: "y",
        pointRadius: showPoints ? 2 : 0,
        tension: 0.3,
      },
      {
        label: "Humidité (%)",
        data: measurements.map(m => m.humidity_pct),
        borderColor: "#0066cc",
        backgroundColor: "rgba(0,102,204,0.08)",
        yAxisID: "y1",
        pointRadius: showPoints ? 2 : 0,
        tension: 0.3,
      },
    ],
  };
  const chartOptions = {
    responsive: true,
    interaction: { mode: "index", intersect: false },
    plugins: { legend: { position: "top" } },
    scales: {
      y:  { type: "linear", display: true, position: "left",  title: { display: true, text: "°C" } },
      y1: { type: "linear", display: true, position: "right", title: { display: true, text: "%" }, grid: { drawOnChartArea: false } },
    },
  };

  return (
    <div>
      <span style={s.back} onClick={() => navigate(`/pays/${country}`)}>← Retour</span>
      <h1 style={s.title}>
        Lot {lot.id} — {COUNTRY_NAMES[country] ?? country}
      </h1>

      <div style={s.card}>
        <h2 style={{ fontSize: 16, fontWeight: 600, marginBottom: 16 }}>Informations générales</h2>
        <div style={s.infoGrid}>
          <InfoItem label="ID Lot"         value={lot.id} />
          <InfoItem label="Entrepôt"       value={lot.warehouse_id} />
          <InfoItem label="Date stockage"  value={new Date(lot.storage_date).toLocaleDateString("fr-FR")} />
          <InfoItem label="Ancienneté"     value={`${days} jours`} />
          <InfoItem label="Variété"        value={lot.variete} />
          <InfoItem label="Poids"          value={lot.poids_kg ? `${lot.poids_kg} kg` : null} />
          <div style={s.infoItem}>
            <span style={s.label}>Statut</span>
            <StatusBadge value={lot.status} />
          </div>
        </div>
        <StatsBar measurements={measurements} />
      </div>

      <div style={s.card}>
        <h2 style={{ fontSize: 16, fontWeight: 600, marginBottom: 16 }}>
          Conditions de stockage — {measurements.length} mesure(s)
        </h2>
        {measurements.length === 0 ? (
          <p style={{ color: "#888" }}>Aucune mesure disponible pour ce lot.</p>
        ) : (
          <Line data={chartData} options={chartOptions} />
        )}
      </div>
    </div>
  );
}
