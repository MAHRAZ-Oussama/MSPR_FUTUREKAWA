import { useEffect, useState, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { getCountryLots, getCountryWarehouses } from "../api.js";
import StatusBadge from "../components/StatusBadge.jsx";
import Spinner from "../components/Spinner.jsx";
import {
  ArrowLeft,
  Filter,
  Warehouse as WarehouseIcon,
  Layers,
  Inbox,
  AlertTriangle,
  History
} from "lucide-react";

const COUNTRY_NAMES = { BR: "Brésil", EC: "Équateur", CO: "Colombie" };
const COUNTRY_FLAGS = { BR: "🇧🇷", EC: "🇪🇨", CO: "🇨🇴" };
const REFRESH_MS = 30_000;

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
      if (status) params.status = status;
      if (warehouseId) params.warehouse_id = warehouseId;
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

  if (loading && lots.length === 0) return <Spinner />;
  if (error) {
    return (
      <div className="bg-red-950/20 border border-red-800 text-red-400 p-6 rounded-lg font-mono">
        <div className="flex items-center gap-3">
          <AlertTriangle className="w-6 h-6 shrink-0" />
          <div>
            <h3 className="font-bold text-lg">Indisponibilité du Terminal {country}</h3>
            <p className="text-sm mt-1">{error}</p>
          </div>
        </div>
        <button
          onClick={load}
          className="mt-4 px-4 py-2 bg-red-900/40 border border-red-700 rounded text-red-300 text-xs font-semibold hover:bg-[#3B1F0E] transition-all"
        >
          Reconnexion
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Back to dashboard and Title */}
      <div className="space-y-3">
        <button
          onClick={() => navigate("/dashboard")}
          className="group inline-flex items-center gap-2 text-coffee-parchment/65 hover:text-coffee-crema text-xs font-bold uppercase tracking-wider transition-colors"
        >
          <ArrowLeft className="w-4 h-4 group-hover:-translate-x-1 transition-transform" />
          <span>Tableau de bord</span>
        </button>

        <div className="flex flex-col md:flex-row md:items-end justify-between gap-4 border-b border-coffee-espresso/40 pb-6">
          <div>
            <div className="flex items-center gap-2 text-coffee-crema text-xs font-bold uppercase tracking-widest mb-1">
              <span>Terminal Régional</span>
            </div>
            <h1 className="text-3xl font-serif font-black text-coffee-parchment tracking-tight flex items-center gap-3">
              <span className="select-none">{COUNTRY_FLAGS[country]}</span>
              <span>{COUNTRY_NAMES[country] ? COUNTRY_NAMES[country].toUpperCase() : country}</span>
            </h1>
          </div>
          <div className="text-xs text-coffee-parchment/40 font-mono flex items-center gap-1.5">
            <History className="w-3.5 h-3.5" />
            <span>{lots.length} Lot(s) Consolidé(s) (FIFO)</span>
          </div>
        </div>
      </div>

      {/* Select filters row */}
      <div className="bg-[#11130d] border border-coffee-espresso/60 rounded-lg p-4 flex flex-wrap items-center gap-4 shadow-md">
        <div className="flex items-center gap-2 text-coffee-crema text-xs font-bold uppercase tracking-wider pl-1 pr-3 border-r border-coffee-espresso/45">
          <Filter className="w-4 h-4" />
          <span>Filtres</span>
        </div>

        <div className="flex flex-wrap items-center gap-3 flex-1">
          {/* Status select */}
          <div className="flex flex-col gap-1 min-w-[150px]">
            <span className="text-[9px] uppercase text-coffee-parchment/45 font-bold tracking-wider">Statut du café</span>
            <select
              value={status}
              onChange={e => setStatus(e.target.value)}
              className="bg-[#0b0c08] border border-coffee-espresso/60 rounded text-xs text-coffee-parchment py-1.5 px-3 focus:outline-none focus:border-coffee-crema transition-all cursor-pointer font-semibold"
            >
              <option value="">Tous les statuts</option>
              <option value="CONFORME">Conforme</option>
              <option value="EN_ALERTE">En alerte</option>
              <option value="PERIME">Périmé</option>
            </select>
          </div>

          {/* Warehouse select */}
          <div className="flex flex-col gap-1 min-w-[200px]">
            <span className="text-[9px] uppercase text-coffee-parchment/45 font-bold tracking-wider">Entrepôt</span>
            <select
              value={warehouseId}
              onChange={e => setWarehouseId(e.target.value)}
              className="bg-[#0b0c08] border border-coffee-espresso/60 rounded text-xs text-coffee-parchment py-1.5 px-3 focus:outline-none focus:border-coffee-crema transition-all cursor-pointer font-semibold"
            >
              <option value="">Tous les entrepôts</option>
              {warehouses.map(wh => (
                <option key={wh.id} value={wh.id}>{wh.code} (H-ID: {wh.id})</option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Main inventory table */}
      <div className="bg-[#11130d] border border-coffee-espresso/60 rounded-lg shadow-md overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-coffee-espresso/50 text-xs text-coffee-crema font-bold uppercase tracking-wider bg-[#131610]/40">
                <th className="py-3.5 px-5">ID Lot</th>
                <th className="py-3.5 px-5">Date Stockage</th>
                <th className="py-3.5 px-5">Ancienneté</th>
                <th className="py-3.5 px-5">Variété</th>
                <th className="py-3.5 px-5">Poids</th>
                <th className="py-3.5 px-5">Statut de conformité</th>
                <th className="py-3.5 px-5 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-coffee-espresso/20 text-sm">
              {lots.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-12 text-center text-coffee-parchment/35">
                    <div className="flex flex-col items-center justify-center gap-3">
                      <Inbox className="w-8 h-8 text-coffee-espresso" />
                      <span>Aucun lot de café ne correspond aux filtres actifs.</span>
                    </div>
                  </td>
                </tr>
              ) : (
                lots.map(lot => {
                  const days = daysAgo(lot.storage_date);
                  const isOld = days > 365;

                  return (
                    <tr
                      key={lot.id}
                      onClick={() => navigate(`/pays/${country}/lots/${lot.id}`)}
                      className="hover:bg-coffee-espresso/15 transition-colors cursor-pointer group"
                    >
                      {/* ID Row */}
                      <td className="py-3 px-5 font-mono font-bold text-xs text-coffee-parchment group-hover:text-coffee-crema">
                        {lot.id}
                      </td>

                      {/* Storage Date */}
                      <td className="py-3 px-5 text-xs text-coffee-parchment/80 font-mono">
                        {new Date(lot.storage_date).toLocaleDateString("fr-FR")}
                      </td>

                      {/* Seniority */}
                      <td className={`py-3 px-5 text-xs font-mono font-bold ${isOld ? "text-red-400 font-extrabold" : "text-coffee-parchment/65"}`}>
                        {days} j {isOld && <span className="text-[10px] bg-red-950/60 px-1 py-0.5 rounded text-red-500 border border-red-900 ml-1.5 uppercase font-bold">Périmé</span>}
                      </td>

                      {/* Variety */}
                      <td className="py-3 px-5 text-xs font-semibold text-coffee-parchment/90">
                        {lot.variete || "—"}
                      </td>

                      {/* Weight */}
                      <td className="py-3 px-5 text-xs font-mono">
                        {lot.poids_kg ? `${lot.poids_kg.toLocaleString("fr-FR")} kg` : "—"}
                      </td>

                      {/* Status */}
                      <td className="py-3 px-5">
                        <StatusBadge value={lot.status} />
                      </td>

                      {/* Actions */}
                      <td className="py-3 px-5 text-right" onClick={e => e.stopPropagation()}>
                        <button
                          onClick={() => navigate(`/pays/${country}/lots/${lot.id}`)}
                          className="px-3 py-1 text-xs font-bold bg-coffee-espresso/45 border border-coffee-espresso hover:border-coffee-crema text-coffee-parchment hover:text-coffee-crema rounded transition-all"
                        >
                          Détails →
                        </button>
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
