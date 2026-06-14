import { NavLink } from "react-router-dom";

const s = {
  nav: {
    background: "#1a3a2a",
    padding: "0 24px",
    display: "flex",
    alignItems: "center",
    gap: 8,
    height: 56,
    boxShadow: "0 2px 8px rgba(0,0,0,0.25)",
  },
  brand: { color: "#fff", fontWeight: 700, fontSize: 18, marginRight: 24, textDecoration: "none" },
  link: ({ isActive }) => ({
    color: isActive ? "#7fff9a" : "#c8e6c9",
    textDecoration: "none",
    padding: "6px 14px",
    borderRadius: 6,
    fontWeight: 500,
    background: isActive ? "rgba(127,255,154,0.12)" : "transparent",
    transition: "background 0.15s",
  }),
};

const links = [
  { to: "/dashboard",    label: "Tableau de bord" },
  { to: "/pays/BR",      label: "🇧🇷 Brésil" },
  { to: "/pays/EC",      label: "🇪🇨 Équateur" },
  { to: "/pays/CO",      label: "🇨🇴 Colombie" },
  { to: "/alertes",      label: "🔔 Alertes" },
];

export default function NavBar() {
  return (
    <nav style={s.nav}>
      <a href="/" style={s.brand}>☕ FutureKawa</a>
      {links.map(({ to, label }) => (
        <NavLink key={to} to={to} style={s.link}>{label}</NavLink>
      ))}
    </nav>
  );
}
