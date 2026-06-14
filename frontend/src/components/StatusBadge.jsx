const CONFIG = {
  CONFORME:  { bg: "#d4edda", color: "#155724", label: "Conforme" },
  EN_ALERTE: { bg: "#fff3cd", color: "#856404", label: "En alerte" },
  PERIME:    { bg: "#f8d7da", color: "#721c24", label: "Périmé" },
  WARNING:   { bg: "#fff3cd", color: "#856404", label: "WARNING" },
  CRITICAL:  { bg: "#f8d7da", color: "#721c24", label: "CRITICAL" },
};

export default function StatusBadge({ value }) {
  const cfg = CONFIG[value] ?? { bg: "#e2e3e5", color: "#383d41", label: value };
  return (
    <span style={{
      background: cfg.bg,
      color: cfg.color,
      padding: "2px 10px",
      borderRadius: 12,
      fontWeight: 600,
      fontSize: 13,
      whiteSpace: "nowrap",
    }}>
      {cfg.label}
    </span>
  );
}
