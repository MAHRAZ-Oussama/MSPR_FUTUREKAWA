import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
  Chart as ChartJS,
  CategoryScale, LinearScale, PointElement, LineElement,
  Title, Tooltip, Legend
} from "chart.js";
import { Line } from "react-chartjs-2";
import { getLotDetail } from "../api.js";
import StatusBadge from "../components/StatusBadge.jsx";
import Spinner from "../components/Spinner.jsx";
import {
  ArrowLeft,
  Calendar,
  Layers,
  Thermometer,
  Droplet,
  HardDrive,
  Scale,
  Activity,
  History,
  ShieldCheck,
  AlertTriangle
} from "lucide-react";

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend);

const COUNTRY_NAMES = { BR: "Brésil", EC: "Équateur", CO: "Colombie" };
const COUNTRY_FLAGS = { BR: "🇧🇷", EC: "🇪🇨", CO: "🇨🇴" };

function StatsBar({ measurements }) {
  if (!measurements || measurements.length === 0) return null;
  const temps = measurements.map(m => parseFloat(m.temperature_c)).filter(m => !isNaN(m));
  const hums = measurements.map(m => parseFloat(m.humidity_pct)).filter(m => !isNaN(m));
  const fmt = v => v.toFixed(1);

  const avgTemp = temps.reduce((a, b) => a + b, 0) / temps.length;
  const avgHum = hums.reduce((a, b) => a + b, 0) / hums.length;

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-4 border-t border-coffee-espresso/30 mt-6">
      {/* Temp Card */}
      <div className="bg-[#0b0c08] border border-coffee-espresso/40 p-4 rounded flex items-center gap-3">
        <Thermometer className="w-8 h-8 text-coffee-crema shrink-0" />
        <div className="flex-1 font-mono">
          <div className="text-[10px] text-coffee-parchment/40 uppercase font-bold tracking-wider">Température Min/Moy/Max</div>
          <div className="text-sm font-bold text-coffee-parchment mt-0.5">
            {fmt(Math.min(...temps))} <span className="text-coffee-parchment/35">/</span> {fmt(avgTemp)} <span className="text-coffee-parchment/35">/</span> {fmt(Math.max(...temps))} <span className="text-xs text-coffee-crema">°C</span>
          </div>
        </div>
      </div>

      {/* Hum Card */}
      <div className="bg-[#0b0c08] border border-coffee-espresso/40 p-4 rounded flex items-center gap-3">
        <Droplet className="w-8 h-8 text-blue-400 shrink-0" />
        <div className="flex-1 font-mono">
          <div className="text-[10px] text-coffee-parchment/40 uppercase font-bold tracking-wider">Humidité Min/Moy/Max</div>
          <div className="text-sm font-bold text-coffee-parchment mt-0.5">
            {fmt(Math.min(...hums))} <span className="text-coffee-parchment/35">/</span> {fmt(avgHum)} <span className="text-coffee-parchment/35">/</span> {fmt(Math.max(...hums))} <span className="text-xs text-blue-400">%</span>
          </div>
        </div>
      </div>

      {/* Measures Card */}
      <div className="bg-[#0b0c08] border border-coffee-espresso/40 p-4 rounded flex items-center gap-3">
        <HardDrive className="w-8 h-8 text-coffee-parchment/50 shrink-0" />
        <div className="flex-1 font-mono">
          <div className="text-[10px] text-coffee-parchment/40 uppercase font-bold tracking-wider">Index des Capteurs</div>
          <div className="text-sm font-bold text-coffee-parchment mt-0.5">
            {measurements.length} <span className="text-xs text-coffee-parchment/40 font-normal">points enregistrés</span>
          </div>
        </div>
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
  if (error) {
    return (
      <div className="bg-red-950/20 border border-red-800 text-red-400 p-6 rounded-lg font-mono">
        <div className="flex items-center gap-3">
          <AlertTriangle className="w-6 h-6 shrink-0" />
          <div>
            <h3 className="font-bold text-lg">Erreur de chargement du lot</h3>
            <p className="text-sm mt-1">{error}</p>
          </div>
        </div>
        <button
          onClick={() => navigate(`/pays/${country}`)}
          className="mt-4 px-4 py-2 bg-[#3B1F0E] border border-coffee-espresso rounded text-coffee-parchment text-xs font-semibold hover:border-coffee-crema transition-all"
        >
          Retourner au terminal {country}
        </button>
      </div>
    );
  }

  const { measurements = [], ...lot } = data;
  const days = Math.floor((Date.now() - new Date(lot.storage_date).getTime()) / 86400000);
  const showPoints = measurements.length <= 200;

  // Sorting measurements cronologically for correct chart representation
  const sortedMeasurements = [...measurements].sort((a, b) => new Date(a.measured_at) - new Date(b.measured_at));

  const labels = sortedMeasurements.map(m =>
    new Date(m.measured_at).toLocaleTimeString("fr-FR", { hour: "2-digit", minute: "2-digit" })
  );

  const chartData = {
    labels,
    datasets: [
      {
        label: "Température (°C)",
        data: sortedMeasurements.map(m => m.temperature_c),
        borderColor: "#C8922A", // Crema
        backgroundColor: "rgba(200, 146, 42, 0.05)",
        yAxisID: "y",
        pointRadius: showPoints ? 1.5 : 0,
        borderWidth: 1.5,
        tension: 0.25,
      },
      {
        label: "Humidité (%)",
        data: sortedMeasurements.map(m => m.humidity_pct),
        borderColor: "#3B82F6", // Blue
        backgroundColor: "rgba(59, 130, 246, 0.05)",
        yAxisID: "y1",
        pointRadius: showPoints ? 1.5 : 0,
        borderWidth: 1.5,
        tension: 0.25,
      },
    ],
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    interaction: { mode: "index", intersect: false },
    plugins: {
      legend: {
        position: "top",
        labels: {
          color: "#EDE8DC",
          font: { family: "'JetBrains Mono', monospace", size: 10 }
        }
      },
      tooltip: {
        backgroundColor: "#0D0F0A",
        titleColor: "#C8922A",
        bodyColor: "#EDE8DC",
        borderColor: "#3B1F0E",
        borderWidth: 1,
        titleFont: { family: "'JetBrains Mono', monospace" },
        bodyFont: { family: "'JetBrains Mono', monospace" }
      }
    },
    scales: {
      y: {
        type: "linear",
        display: true,
        position: "left",
        title: { display: true, text: "Température (°C)", color: "#C8922A", font: { family: "'JetBrains Mono', monospace" } },
        grid: { color: "rgba(59, 31, 14, 0.3)" },
        ticks: { color: "#EDE8DC", font: { family: "'JetBrains Mono', monospace", size: 10 } }
      },
      y1: {
        type: "linear",
        display: true,
        position: "right",
        title: { display: true, text: "Humidité (%)", color: "#3B82F6", font: { family: "'JetBrains Mono', monospace" } },
        grid: { drawOnChartArea: false },
        ticks: { color: "#EDE8DC", font: { family: "'JetBrains Mono', monospace", size: 10 } }
      },
      x: {
        grid: { color: "rgba(59, 31, 14, 0.3)" },
        ticks: { color: "#EDE8DC", font: { family: "'JetBrains Mono', monospace", size: 9 } }
      }
    },
  };

  return (
    <div className="space-y-6">
      {/* Navigation and title header */}
      <div className="space-y-3">
        <button
          onClick={() => navigate(`/pays/${country}`)}
          className="group inline-flex items-center gap-2 text-coffee-parchment/65 hover:text-coffee-crema text-xs font-bold uppercase tracking-wider transition-colors"
        >
          <ArrowLeft className="w-4 h-4 group-hover:-translate-x-1 transition-transform" />
          <span>Fiche Terminal {country}</span>
        </button>

        <div className="flex flex-col md:flex-row md:items-end justify-between gap-4 border-b border-coffee-espresso/40 pb-6">
          <div>
            <div className="flex items-center gap-2 text-coffee-crema text-xs font-bold uppercase tracking-widest mb-1">
              <span>Rapport de Lot</span>
            </div>
            <h1 className="text-3xl font-serif font-black text-coffee-parchment tracking-tight flex items-center gap-2.5">
              <span>LOT {lot.id}</span>
              <span className="text-xl font-mono text-coffee-parchment/40">[{COUNTRY_FLAGS[country]} {COUNTRY_NAMES[country]}]</span>
            </h1>
          </div>
          <div className="text-xs">
            <StatusBadge value={lot.status} />
          </div>
        </div>
      </div>

      {/* Info details grid card */}
      <div className="bg-[#11130d] border border-coffee-espresso/60 rounded-lg p-6 shadow-md">
        <h2 className="text-lg font-serif font-bold text-coffee-crema mb-4 flex items-center gap-2">
          <Layers className="w-5 h-5 text-coffee-crema/70" />
          <span>Fiche d'identification technique</span>
        </h2>

        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-x-4 gap-y-5 font-mono text-xs">

          <div className="space-y-1">
            <div className="text-[10px] text-coffee-parchment/40 uppercase font-bold tracking-wider">Référence Lot</div>
            <div className="font-bold text-coffee-parchment">{lot.id}</div>
          </div>

          <div className="space-y-1">
            <div className="text-[10px] text-coffee-parchment/40 uppercase font-bold tracking-wider">Entrepôt ID</div>
            <div className="font-bold text-coffee-parchment">W-{lot.warehouse_id || "Non spécifié"}</div>
          </div>

          <div className="space-y-1">
            <div className="text-[10px] text-coffee-parchment/40 uppercase font-bold tracking-wider">Stockage Enregistré</div>
            <div className="font-bold text-coffee-parchment flex items-center gap-1.5">
              <Calendar className="w-3.5 h-3.5 text-coffee-crema/70" />
              <span>{new Date(lot.storage_date).toLocaleDateString("fr-FR")}</span>
            </div>
          </div>

          <div className="space-y-1">
            <div className="text-[10px] text-coffee-parchment/40 uppercase font-bold tracking-wider">Ancienneté Stock</div>
            <div className={`font-bold ${days > 365 ? "text-red-400" : "text-coffee-parchment"}`}>{days} jours</div>
          </div>

          <div className="space-y-1">
            <div className="text-[10px] text-coffee-parchment/40 uppercase font-bold tracking-wider">Variété Green Coffee</div>
            <div className="font-bold text-coffee-crema">{lot.variete || "—"}</div>
          </div>

          <div className="space-y-1">
            <div className="text-[10px] text-coffee-parchment/40 uppercase font-bold tracking-wider">Masse du Lot</div>
            <div className="font-bold text-coffee-parchment flex items-center gap-1">
              <Scale className="w-3.5 h-3.5 text-coffee-parchment/50" />
              <span>{lot.poids_kg ? `${lot.poids_kg.toLocaleString("fr-FR")} kg` : "—"}</span>
            </div>
          </div>

        </div>

        <StatsBar measurements={sortedMeasurements} />
      </div>

      {/* Storage conditions evolution chart */}
      <div className="bg-[#11130d] border border-coffee-espresso/60 rounded-lg p-6 shadow-md">
        <h2 className="text-lg font-serif font-bold text-coffee-crema mb-2 flex items-center gap-2">
          <Activity className="w-5 h-5 text-coffee-crema/70" />
          <span>Télémétrie des capteurs environnementaux</span>
        </h2>
        <p className="text-xs text-coffee-parchment/40 mb-6">Évolution des relevés de température et d'humidité du lot en temps réel</p>

        {sortedMeasurements.length === 0 ? (
          <div className="py-16 text-center text-coffee-parchment/30 text-xs font-mono">
            <HardDrive className="w-10 h-10 mx-auto text-coffee-espresso mb-3" />
            <span>Aucune mesure disponible pour ce lot de café vert.</span>
          </div>
        ) : (
          <div className="h-80 w-full relative">
            <Line data={chartData} options={chartOptions} />
          </div>
        )}
      </div>
    </div>
  );
}
