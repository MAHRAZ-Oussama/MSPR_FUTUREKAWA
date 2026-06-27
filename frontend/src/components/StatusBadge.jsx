const CONFIG = {
  CONFORME: { className: "bg-green-950/45 text-green-400 border border-green-800/80", label: "Conforme" },
  EN_ALERTE: { className: "bg-amber-950/45 text-amber-400 border border-amber-800/80", label: "En alerte" },
  PERIME: { className: "bg-red-950/45 text-red-400 border border-red-800/80", label: "Périmé" },
  WARNING: { className: "bg-amber-950/45 text-amber-400 border border-amber-800/80", label: "Avertissement" },
  CRITICAL: { className: "bg-red-950/45 text-red-400 border border-red-800/80", label: "Critique" },
};

export default function StatusBadge({ value }) {
  const cfg = CONFIG[value] ?? { className: "bg-zinc-900 text-zinc-400 border border-zinc-800", label: value };
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold uppercase tracking-wider whitespace-nowrap ${cfg.className}`}>
      {cfg.label}
    </span>
  );
}
