import { useEffect, useState, useCallback } from "react";
import { getAlerts, resolveAlert } from "../api.js";
import StatusBadge from "../components/StatusBadge.jsx";
import Spinner from "../components/Spinner.jsx";
import {
  AlertTriangle,
  BellRing,
  Check,
  Filter,
  MapPin,
  Layers,
  Calendar,
  AlertOctagon,
  ShieldAlert,
  ShieldCheck,
  Info
} from "lucide-react";

const REFRESH_MS = 30_000;
const COUNTRY_NAMES = { BR: "Brésil", EC: "Équateur", CO: "Colombie" };
const COUNTRY_FLAGS = { BR: "🇧🇷", EC: "🇪🇨", CO: "🇨🇴" };

const ALERT_ICONS = {
  TEMP_OUT_OF_RANGE: "🌡️",
  HUMIDITY_OUT_OF_RANGE: "💧",
  LOT_EXPIRED: "⏰",
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
      if (severity) params.severity = severity;
      if (alertType) params.alert_type = alertType;
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
    try {
      await resolveAlert(country, alertId);
      load();
    } catch (e) {
      console.error(e);
    }
  };

  if (loading && data.alerts.length === 0) return <Spinner />;

  const displayed = countryFilter
    ? data.alerts.filter(a => a.country === countryFilter)
    : data.alerts;

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4 border-b border-coffee-espresso/40 pb-6">
        <div>
          <div className="flex items-center gap-2 text-red-500 text-xs font-bold uppercase tracking-widest mb-1.5 animate-pulse">
            <BellRing className="w-4 h-4" />
            <span>Incidents & Alertes systèmes</span>
          </div>
          <h1 className="text-3xl font-serif font-black text-coffee-parchment tracking-tight">
            CENTRE D'ALERTES
          </h1>
        </div>
        <div className="text-xs text-coffee-parchment/40 font-mono">
          <span>{displayed.length} incident(s) répertorié(s)</span>
        </div>
      </div>

      {data.degraded_countries?.length > 0 && (
        <div className="bg-[#311116]/30 border border-red-950 text-red-400 px-5 py-4 rounded-lg flex items-center gap-3.5 text-sm">
          <AlertOctagon className="w-5 h-5 shrink-0 text-red-500" />
          <div>
            <strong className="font-bold font-mono">Flux Interrompus : </strong>
            Impossible d'agréger les alertes pour les terminaux :{" "}
            <span className="font-bold underline">{data.degraded_countries.join(", ")}</span>.
          </div>
        </div>
      )}

      {/* Filter Toolbar */}
      <div className="bg-[#11130d] border border-coffee-espresso/60 rounded-lg p-4 flex flex-wrap items-center gap-6 shadow-md">
        <div className="flex items-center gap-2 text-coffee-crema text-xs font-bold uppercase tracking-wider pl-1 pr-3 border-r border-coffee-espresso/45">
          <Filter className="w-4 h-4" />
          <span>Filtres</span>
        </div>

        <div className="flex flex-wrap items-center gap-4 flex-1">
          {/* Severity filter */}
          <div className="flex flex-col gap-1 min-w-[130px]">
            <span className="text-[9px] uppercase text-coffee-parchment/45 font-bold tracking-wider">Sévérité</span>
            <select
              value={severity}
              onChange={e => setSeverity(e.target.value)}
              className="bg-[#0b0c08] border border-coffee-espresso/60 rounded text-xs text-coffee-parchment py-1.5 px-3 focus:outline-none focus:border-coffee-crema transition-all cursor-pointer font-semibold"
            >
              <option value="">Toutes sévérités</option>
              <option value="CRITICAL">Critique</option>
              <option value="WARNING">Avertissement</option>
            </select>
          </div>

          {/* Alert Type filter */}
          <div className="flex flex-col gap-1 min-w-[150px]">
            <span className="text-[9px] uppercase text-coffee-parchment/45 font-bold tracking-wider">Nature</span>
            <select
              value={alertType}
              onChange={e => setAlertType(e.target.value)}
              className="bg-[#0b0c08] border border-coffee-espresso/60 rounded text-xs text-coffee-parchment py-1.5 px-3 focus:outline-none focus:border-coffee-crema transition-all cursor-pointer font-semibold"
            >
              <option value="">Tous types</option>
              <option value="TEMP_OUT_OF_RANGE">Température</option>
              <option value="HUMIDITY_OUT_OF_RANGE">Humidité</option>
              <option value="LOT_EXPIRED">Lot périmé</option>
            </select>
          </div>

          {/* Country filter */}
          <div className="flex flex-col gap-1 min-w-[130px]">
            <span className="text-[9px] uppercase text-coffee-parchment/45 font-bold tracking-wider">Pays</span>
            <select
              value={countryFilter}
              onChange={e => setCountryFilter(e.target.value)}
              className="bg-[#0b0c08] border border-coffee-espresso/60 rounded text-xs text-coffee-parchment py-1.5 px-3 focus:outline-none focus:border-coffee-crema transition-all cursor-pointer font-semibold"
            >
              <option value="">Tous les pays</option>
              <option value="BR">Brésil</option>
              <option value="EC">Équateur</option>
              <option value="CO">Colombie</option>
            </select>
          </div>

          {/* Active only checkbox wrapper */}
          <div className="flex items-center h-full pt-4">
            <label className="flex items-center gap-2 text-xs text-coffee-parchment/70 font-semibold cursor-pointer select-none hover:text-coffee-parchment transition-colors">
              <input
                type="checkbox"
                checked={activeOnly}
                onChange={e => setActiveOnly(e.target.checked)}
                className="w-3.5 h-3.5 accent-coffee-crema bg-coffee-dark border-coffee-espresso rounded cursor-pointer"
              />
              <span>Actives uniquement</span>
            </label>
          </div>
        </div>
      </div>

      {/* Alerts list/table container */}
      <div className="bg-[#11130d] border border-coffee-espresso/60 rounded-lg shadow-md overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-coffee-espresso/50 text-xs text-coffee-crema font-bold uppercase tracking-wider bg-[#131610]/40">
                <th className="py-3.5 px-5">Type / Code</th>
                <th className="py-3.5 px-5">Sévérité</th>
                <th className="py-3.5 px-5">Origine</th>
                <th className="py-3.5 px-5">Détail du message</th>
                <th className="py-3.5 px-5">Déclenchement</th>
                <th className="py-3.5 px-5">Résolution</th>
                <th className="py-3.5 px-5 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-coffee-espresso/20 text-sm font-mono">
              {displayed.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-16 text-center text-coffee-parchment/35 font-mono">
                    <div className="flex flex-col items-center justify-center gap-3">
                      <ShieldCheck className="w-10 h-10 text-green-700/80" />
                      <span>Aucune alerte active sur le réseau de supervision.</span>
                    </div>
                  </td>
                </tr>
              ) : (
                displayed.map(alert => {
                  const isResolved = !!alert.resolved_at;
                  const isCritical = alert.severity === "CRITICAL";

                  return (
                    <tr
                      key={`${alert.country}-${alert.id}`}
                      className={`transition-colors ${isResolved
                          ? "opacity-60 hover:opacity-100 hover:bg-coffee-espresso/5"
                          : isCritical
                            ? "bg-red-950/5 hover:bg-red-950/10 border-l-2 border-l-red-500"
                            : "bg-[#11130d] hover:bg-coffee-espresso/10 border-l-2 border-l-amber-500"
                        }`}
                    >
                      {/* Alert type representation */}
                      <td className="py-3.5 px-5">
                        <div className="flex items-center gap-2">
                          <span className="text-sm select-none">{ALERT_ICONS[alert.alert_type] || "📋"}</span>
                          <span className="font-bold text-xs uppercase tracking-tight text-coffee-parchment">
                            {alert.alert_type.replace(/_/g, " ")}
                          </span>
                        </div>
                      </td>

                      {/* Severity badge */}
                      <td className="py-3.5 px-5">
                        <StatusBadge value={alert.severity} />
                      </td>

                      {/* Origin country & warehouse */}
                      <td className="py-3.5 px-5 text-xs text-coffee-parchment/80">
                        <div className="flex items-center gap-1.5">
                          <span className="select-none">{COUNTRY_FLAGS[alert.country] || "🗺️"}</span>
                          <span className="font-bold">{COUNTRY_NAMES[alert.country]}</span>
                          <span className="text-coffee-parchment/40 font-normal">/</span>
                          <span className="bg-coffee-espresso/35 px-1.5 py-0.5 rounded text-[10px] uppercase font-bold text-coffee-parchment/70">W-{alert.warehouse_id}</span>
                        </div>
                      </td>

                      {/* Message details */}
                      <td className="py-3.5 px-5 text-xs max-w-xs font-sans text-coffee-parchment/75 leading-relaxed">
                        {alert.message || "Aucune description fournie par le capteur."}
                      </td>

                      {/* Timestamp trigger */}
                      <td className="py-3.5 px-5 text-xs text-coffee-parchment/65 font-bold">
                        <div className="flex items-center gap-1">
                          <Calendar className="w-3.5 h-3.5 text-coffee-crema/70" />
                          <span>{new Date(alert.created_at).toLocaleString("fr-FR", { hour: "2-digit", minute: "2-digit", second: "2-digit", day: "2-digit", month: "2-digit" })}</span>
                        </div>
                      </td>

                      {/* Resolution Timestamp */}
                      <td className="py-3.5 px-5 text-xs">
                        {isResolved ? (
                          <div className="flex items-center gap-1.5 text-green-400 font-bold">
                            <ShieldCheck className="w-3.5 h-3.5" />
                            <span>{new Date(alert.resolved_at).toLocaleString("fr-FR", { hour: "2-digit", minute: "2-digit" })}</span>
                          </div>
                        ) : (
                          <div className="flex items-center gap-1.5 text-red-500 font-bold animate-pulse">
                            <ShieldAlert className="w-3.5 h-3.5" />
                            <span>Active</span>
                          </div>
                        )}
                      </td>

                      {/* Resolve CTA */}
                      <td className="py-3.5 px-5 text-right">
                        {!isResolved ? (
                          <button
                            onClick={() => handleResolve(alert.country, alert.id)}
                            className="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-bold bg-green-950/60 border border-green-800 hover:border-green-500 text-green-400 hover:text-green-300 rounded transition-all shadow-sm"
                          >
                            <Check className="w-3 h-3" />
                            <span>Acquitter</span>
                          </button>
                        ) : (
                          <span className="text-[10px] text-coffee-parchment/30 uppercase tracking-widest font-bold">Résolue</span>
                        )}
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
