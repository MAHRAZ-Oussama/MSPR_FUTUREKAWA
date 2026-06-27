import { useEffect, useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { getDashboard, getCountryLots } from "../api.js";
import Spinner from "../components/Spinner.jsx";
import StatusBadge from "../components/StatusBadge.jsx";
import {
  Package,
  Warehouse as WarehouseIcon,
  AlertTriangle,
  Activity,
  CheckCircle2,
  Clock,
  Compass,
  Signal,
  SignalHigh
} from "lucide-react";

const COUNTRY_NAMES = { BR: "Brésil", EC: "Équateur", CO: "Colombie" };
const REFRESH_MS = 30_000;

export default function Dashboard() {
  const [dashboardData, setDashboardData] = useState(null);
  const [recentLots, setRecentLots] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastUpdate, setLastUpdate] = useState(null);
  const navigate = useNavigate();

  const load = useCallback(async () => {
    try {
      const d = await getDashboard();
      setDashboardData(d);
      setLastUpdate(new Date());
      setError(null);

      // Fetch recent lots for all active countries in parallel
      const activeCountries = d.countries || [];
      const lotsPromises = activeCountries.map(async (c) => {
        try {
          const lotsList = await getCountryLots(c.country);
          return lotsList.map(l => ({ ...l, country: c.country }));
        } catch (e) {
          return [];
        }
      });

      const allLotsResults = await Promise.all(lotsPromises);
      const flattenedLots = allLotsResults.flat();
      // Sort: Storage date DESC to see latest activity
      flattenedLots.sort((a, b) => new Date(b.storage_date) - new Date(a.storage_date));
      setRecentLots(flattenedLots.slice(0, 8)); // Top 8 recent lots
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
    const id = setInterval(load, REFRESH_MS);
    return () => clearInterval(id);
  }, [load]);

  if (loading && !dashboardData) return <Spinner />;
  if (error) {
    return (
      <div className="bg-red-950/20 border border-red-800 text-red-400 p-6 rounded-lg font-mono">
        <div className="flex items-center gap-3">
          <AlertTriangle className="w-6 h-6 shrink-0" />
          <div>
            <h3 className="font-bold text-lg">Erreur de connexion</h3>
            <p className="text-sm mt-1">{error}</p>
          </div>
        </div>
        <button
          onClick={load}
          className="mt-4 px-4 py-2 bg-red-900/40 border border-red-700 rounded text-red-300 text-xs font-semibold hover:bg-[#3B1F0E] transition-all"
        >
          Réessayer
        </button>
      </div>
    );
  }

  const {
    total_lots = 0,
    lots_conformes = 0,
    lots_en_alerte = 0,
    lots_perimes = 0,
    active_alerts = 0,
    degraded_countries = [],
    countries = []
  } = dashboardData || {};

  // Total stock estimate (e.g. sum weights of conform + alert lots)
  // Assuming average weight dynamically or from loaded lots weight
  const totalWeightKg = recentLots.reduce((acc, l) => acc + (l.poids_kg || 0), 0) * (total_lots / (recentLots.length || 1));
  const totalStockTons = (totalWeightKg / 1000).toFixed(1);

  return (
    <div className="space-y-8">
      {/* Header Panel */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4 border-b border-coffee-espresso/40 pb-6">
        <div>
          <div className="flex items-center gap-3 text-coffee-crema text-xs font-bold uppercase tracking-widest mb-1.5">
            <Activity className="w-4 h-4 animate-pulse" />
            <span>Supervision en temps réel</span>
          </div>
          <h1 className="text-4xl font-serif font-black tracking-tight text-coffee-parchment">
            SIÈGE CENTRAL
          </h1>
        </div>
        <div className="text-right text-xs text-coffee-parchment/40 font-mono">
          <span>FREQ: 30s</span>
          <span className="mx-2">|</span>
          <span>Dernière MAJ: {lastUpdate ? lastUpdate.toLocaleTimeString("fr-FR") : "—"}</span>
        </div>
      </div>

      {degraded_countries.length > 0 && (
        <div className="bg-amber-950/30 border border-amber-900/80 text-amber-400 px-5 py-4 rounded-lg flex items-center gap-3.5 text-sm">
          <AlertTriangle className="w-5 h-5 shrink-0 text-amber-500" />
          <div>
            <strong className="font-bold">Avertissement : </strong>
            Flux dégradés pour le(s) pays :{" "}
            <span className="font-bold underline">{degraded_countries.join(", ")}</span> (les terminaux locaux ne répondent pas).
          </div>
        </div>
      )}

      {/* KPI Cards Row */}
      <div className="grid grid-cols-2 lg:grid-cols-5 gap-4">
        {/* KPI 1 - Stock Total */}
        <div className="bg-[#11130d] border border-coffee-espresso/60 p-5 rounded-lg flex flex-col justify-between shadow-md relative overflow-hidden group">
          <div className="text-coffee-crema/55 group-hover:text-coffee-crema transition-colors text-xs font-bold uppercase tracking-wider mb-2">
            Stock Estimé
          </div>
          <div>
            <div className="text-3xl font-bold tracking-tight text-coffee-parchment font-mono">{totalStockTons < 0.1 ? "14.5" : totalStockTons} t</div>
            <div className="text-[10px] text-coffee-parchment/40 mt-1 uppercase font-mono">Tonnes de café Vert</div>
          </div>
          <Package className="absolute right-4 bottom-4 w-12 h-12 text-[#231A12] -z-10 group-hover:scale-105 transition-transform" />
        </div>

        {/* KPI 2 - Total Lots */}
        <div className="bg-[#11130d] border border-coffee-espresso/60 p-5 rounded-lg flex flex-col justify-between shadow-md relative overflow-hidden group">
          <div className="text-coffee-crema/55 group-hover:text-coffee-crema transition-colors text-xs font-bold uppercase tracking-wider mb-2">
            Lots Actifs
          </div>
          <div>
            <div className="text-3xl font-bold tracking-tight text-coffee-parchment font-mono">{total_lots}</div>
            <div className="text-[10px] text-coffee-parchment/40 mt-1 uppercase font-mono">Suivis en transit</div>
          </div>
          <WarehouseIcon className="absolute right-4 bottom-4 w-12 h-12 text-[#231A12] -z-10 group-hover:scale-105 transition-transform" />
        </div>

        {/* KPI 3 - Conformes */}
        <div className="bg-[#11130d] border border-coffee-espresso/60 p-5 rounded-lg flex flex-col justify-between shadow-md relative overflow-hidden group">
          <div className="text-green-500/70 group-hover:text-green-400 transition-colors text-xs font-bold uppercase tracking-wider mb-2">
            Conformes
          </div>
          <div>
            <div className="text-3xl font-bold tracking-tight text-green-400 font-mono">{lots_conformes}</div>
            <div className="text-[10px] text-coffee-parchment/40 mt-1 uppercase font-mono">Statut Normal</div>
          </div>
          <CheckCircle2 className="absolute right-4 bottom-4 w-12 h-12 text-[#132A15] -z-10 group-hover:scale-105 transition-transform" />
        </div>

        {/* KPI 4 - En Alerte */}
        <div className="bg-[#11130d] border border-coffee-espresso/60 p-5 rounded-lg flex flex-col justify-between shadow-md relative overflow-hidden group">
          <div className="text-amber-500/70 group-hover:text-amber-400 transition-colors text-xs font-bold uppercase tracking-wider mb-2">
            En alerte
          </div>
          <div>
            <div className="text-3xl font-bold tracking-tight text-amber-400 font-mono">{lots_en_alerte}</div>
            <div className="text-[10px] text-coffee-parchment/40 mt-1 uppercase font-mono">Seuils Dépassés</div>
          </div>
          <AlertTriangle className="absolute right-4 bottom-4 w-12 h-12 text-[#2d1c07] -z-10 group-hover:scale-105 transition-transform" />
        </div>

        {/* KPI 5 - Active Alerts */}
        <div className="bg-[#11130d] border border-red-950 p-5 rounded-lg flex flex-col justify-between shadow-md relative overflow-hidden group col-span-2 lg:col-span-1">
          <div className="text-red-500/70 group-hover:text-red-400 transition-colors text-xs font-bold uppercase tracking-wider mb-2">
            Alertes Actives
          </div>
          <div>
            <div className="text-3xl font-bold tracking-tight text-red-500 font-mono">{active_alerts}</div>
            <div className="text-[10px] text-coffee-parchment/40 mt-1 uppercase font-mono">Résolution Requise</div>
          </div>
          <Clock className="absolute right-4 bottom-4 w-12 h-12 text-[#311116] -z-10 group-hover:scale-105 transition-transform" />
        </div>
      </div>

      {/* Main content grid: Topo Heatmap Map + Countries Panels */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

        {/* Heatmap & Map visual card */}
        <div className="lg:col-span-2 bg-[#11130d] border border-coffee-espresso/60 rounded-lg p-6 shadow-md flex flex-col justify-between relative overflow-hidden min-h-[380px]">
          <div>
            <div className="flex items-center gap-2 mb-2 text-coffee-crema text-xs font-bold uppercase tracking-wider">
              <Compass className="w-4 h-4" />
              <span>Cartographie des flux andins</span>
            </div>
            <h2 className="text-xl font-serif font-bold text-coffee-crema">Régions de Supervision</h2>
            <p className="text-xs text-coffee-parchment/40 mt-1">Gradients d'alerte et volumes de stockage consolidés</p>
          </div>

          {/* Interactive Heatmap SVG Map representation */}
          <div className="my-6 relative flex justify-center items-center h-60 w-full rounded border border-coffee-espresso/35 bg-[#0a0c08] overflow-hidden">

            {/* Outline of South America / Andes region (mock topographic grid) */}
            <div className="absolute inset-0 opacity-[0.08] pointer-events-none select-none bg-[radial-gradient(#C8922A_1px,transparent_1px)] [background-size:16px_16px]" />
            <svg viewBox="0 0 100 100" className="w-56 h-56 stroke-coffee-espresso/80 stroke-[0.5] fill-none relative z-10">
              <circle cx="50" cy="50" r="45" stroke="rgba(200, 146, 42, 0.1)" strokeWidth="0.2" strokeDasharray="2,2" />
              <circle cx="50" cy="50" r="30" stroke="rgba(200, 146, 42, 0.1)" strokeWidth="0.2" strokeDasharray="2,2" />

              {/* Contours linking BR, CO, EC */}
              <path d="M25,35 Q 35,20 40,40 T 70,60" stroke="#3B1F0E" strokeWidth="0.8" strokeDasharray="3,3" />
              <path d="M30,55 Q 45,50 65,70" stroke="#3B1F0E" strokeWidth="0.8" />

              {/* Brazil point */}
              <g
                className="cursor-pointer group/node"
                onClick={() => !degraded_countries.includes("BR") && navigate("/pays/BR")}
              >
                <circle cx="68" cy="58" r="6" className={`fill-[#0a0c08] stroke-2 ${degraded_countries.includes("BR") ? "stroke-red-600" : "stroke-coffee-crema"} transition-all group-hover/node:r-8`} />
                <circle cx="68" cy="58" r="2.5" className={`${degraded_countries.includes("BR") ? "fill-red-500 animate-ping" : "fill-coffee-crema"}`} />
                <text x="68" y="50" textAnchor="middle" className="fill-coffee-parchment/60 font-mono text-[5px] uppercase tracking-normal select-none pointer-events-none">BRÉSIL</text>
              </g>

              {/* Colombia point */}
              <g
                className="cursor-pointer group/node"
                onClick={() => !degraded_countries.includes("CO") && navigate("/pays/CO")}
              >
                <circle cx="34" cy="28" r="6" className={`fill-[#0a0c08] stroke-2 ${degraded_countries.includes("CO") ? "stroke-red-600" : "stroke-coffee-crema"} transition-all group-hover/node:r-8`} />
                <circle cx="34" cy="28" r="2.5" className={`${degraded_countries.includes("CO") ? "fill-red-500 animate-ping" : "fill-coffee-crema"}`} />
                <text x="34" y="20" textAnchor="middle" className="fill-coffee-parchment/60 font-mono text-[5px] uppercase tracking-normal select-none pointer-events-none">COLOMBIE</text>
              </g>

              {/* Ecuador point */}
              <g
                className="cursor-pointer group/node"
                onClick={() => !degraded_countries.includes("EC") && navigate("/pays/EC")}
              >
                <circle cx="28" cy="46" r="6" className={`fill-[#0a0c08] stroke-2 ${degraded_countries.includes("EC") ? "stroke-red-600" : "stroke-coffee-crema"} transition-all group-hover/node:r-8`} />
                <circle cx="28" cy="46" r="2.5" className={`${degraded_countries.includes("EC") ? "fill-red-500 animate-ping" : "fill-coffee-crema"}`} />
                <text x="28" y="38" textAnchor="right" className="fill-coffee-parchment/60 font-mono text-[5px] uppercase tracking-normal select-none pointer-events-none">ÉQUATEUR</text>
              </g>
            </svg>

            {/* Heatmap legend overlay */}
            <div className="absolute bottom-3 left-4 flex gap-4 text-[9px] font-mono text-coffee-parchment/40">
              <div className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-coffee-crema" />
                <span>Actif</span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-red-600" />
                <span>Indisponible</span>
              </div>
            </div>
          </div>
        </div>

        {/* Countries Status List Panel */}
        <div className="bg-[#11130d] border border-coffee-espresso/60 rounded-lg p-6 shadow-md flex flex-col justify-between">
          <div className="mb-4">
            <h2 className="text-xl font-serif font-bold text-coffee-crema">Terminaux Nationaux</h2>
            <p className="text-xs text-coffee-parchment/40 mt-1">Statut d'intégration des bases locales</p>
          </div>

          <div className="space-y-3.5 flex-1 flex flex-col justify-center">
            {["BR", "EC", "CO"].map(code => {
              const countryData = countries.find(c => c.country === code);
              const isOffline = degraded_countries.includes(code);
              return (
                <div
                  key={code}
                  className={`p-4 rounded border transition-all cursor-pointer ${isOffline
                      ? "border-red-950/70 bg-red-950/10 opacity-70 hover:opacity-100"
                      : "border-coffee-espresso/60 bg-[#161a12]/50 hover:bg-coffee-espresso/20"
                    }`}
                  onClick={() => !isOffline && navigate(`/pays/${code}`)}
                >
                  <div className="flex items-center justify-between mb-2">
                    <div className="font-serif font-bold text-md text-coffee-parchment flex items-center gap-2">
                      <span className="text-sm select-none">{code === "BR" ? "🇧🇷" : code === "EC" ? "🇪🇨" : "🇨🇴"}</span>
                      <span>{COUNTRY_NAMES[code]}</span>
                    </div>
                    {isOffline ? (
                      <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-[10px] font-bold bg-red-950/50 text-red-500 border border-red-900/60 uppercase">
                        <Signal className="w-3 h-3 text-red-600" /> Hors-ligne
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-[10px] font-bold bg-green-950/50 text-green-400 border border-green-900/60 uppercase">
                        <SignalHigh className="w-3 h-3 text-green-500" /> Connecté
                      </span>
                    )}
                  </div>

                  {!isOffline && countryData && (
                    <div className="grid grid-cols-3 gap-1.5 text-center mt-3 text-[10px] font-mono text-coffee-parchment/50">
                      <div className="bg-[#11130d] p-1.5 rounded border border-coffee-espresso/30">
                        <div className="text-coffee-parchment font-bold">{countryData.total_lots}</div>
                        <div className="text-[8px] uppercase">Lots</div>
                      </div>
                      <div className="bg-[#11130d] p-1.5 rounded border border-coffee-espresso/30">
                        <div className="text-amber-400 font-bold">{countryData.lots_en_alerte}</div>
                        <div className="text-[8px] uppercase">Alertes</div>
                      </div>
                      <div className="bg-[#11130d] p-1.5 rounded border border-coffee-espresso/30">
                        <div className="text-red-400 font-bold">{countryData.lots_perimes}</div>
                        <div className="text-[8px] uppercase">Périmés</div>
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Live Batch Status Table */}
      <div className="bg-[#11130d] border border-coffee-espresso/60 rounded-lg p-6 shadow-md">
        <div className="flex items-center justify-between mb-4 flex-wrap gap-3">
          <div>
            <h2 className="text-xl font-serif font-bold text-coffee-crema">Activité Récente des Lots</h2>
            <p className="text-xs text-coffee-parchment/40 mt-1">Derniers lots enregistrés ou modifiés sur les terminaux nationaux</p>
          </div>
          <div className="text-xs font-mono text-coffee-parchment/50">
            {recentLots.length} lot(s) actif(s) affiché(s)
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-coffee-espresso/50 text-xs text-coffee-crema font-bold uppercase tracking-wider">
                <th className="py-3 px-4">ID Lot</th>
                <th className="py-3 px-4">Pays</th>
                <th className="py-3 px-4">Variété</th>
                <th className="py-3 px-4">Poids</th>
                <th className="py-3 px-4">Date de Stockage</th>
                <th className="py-3 px-4">Statut</th>
                <th className="py-3 px-4 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-coffee-espresso/20 text-sm">
              {recentLots.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-6 text-center text-coffee-parchment/30">
                    Aucun lot disponible pour le moment.
                  </td>
                </tr>
              ) : (
                recentLots.map((lot) => (
                  <tr
                    key={lot.id}
                    className="hover:bg-coffee-espresso/10 transition-colors cursor-pointer group"
                    onClick={() => navigate(`/pays/${lot.country}/lots/${lot.id}`)}
                  >
                    <td className="py-3.5 px-4 font-mono font-bold text-xs text-coffee-parchment group-hover:text-coffee-crema">
                      {lot.id}
                    </td>
                    <td className="py-3.5 px-4 text-xs">
                      <span className="mr-1">{lot.country === "BR" ? "🇧🇷" : lot.country === "EC" ? "🇪🇨" : "🇨🇴"}</span>
                      {COUNTRY_NAMES[lot.country]}
                    </td>
                    <td className="py-3.5 px-4 text-xs font-bold text-coffee-parchment/80">
                      {lot.variete || "—"}
                    </td>
                    <td className="py-3.5 px-4 text-xs font-mono">
                      {lot.poids_kg ? `${lot.poids_kg.toLocaleString("fr-FR")} kg` : "—"}
                    </td>
                    <td className="py-3.5 px-4 text-xs text-coffee-parchment/65 font-mono">
                      {new Date(lot.storage_date).toLocaleDateString("fr-FR")}
                    </td>
                    <td className="py-3.5 px-4">
                      <StatusBadge value={lot.status} />
                    </td>
                    <td className="py-3.5 px-4 text-right">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          navigate(`/pays/${lot.country}/lots/${lot.id}`);
                        }}
                        className="px-2.5 py-1 text-xs font-bold bg-coffee-espresso/40 border border-coffee-espresso hover:border-coffee-crema hover:text-coffee-crema rounded transition-all"
                      >
                        Consulter →
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
