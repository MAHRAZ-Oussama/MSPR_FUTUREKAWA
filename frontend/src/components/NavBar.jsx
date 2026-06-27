import { NavLink } from "react-router-dom";
import { LayoutDashboard, MapPin, AlertCircle, Coffee } from "lucide-react";

const links = [
  { to: "/dashboard", label: "Tableau de bord", icon: LayoutDashboard },
  { to: "/pays/BR", label: "Brésil", icon: MapPin, flag: "🇧🇷" },
  { to: "/pays/EC", label: "Équateur", icon: MapPin, flag: "🇪🇨" },
  { to: "/pays/CO", label: "Colombie", icon: MapPin, flag: "🇨🇴" },
  { to: "/alertes", label: "Alertes", icon: AlertCircle },
];

export default function NavBar() {
  return (
    <nav className="bg-coffee-dark border-b border-coffee-espresso/80 px-6 flex items-center justify-between h-16 shadow-lg z-10">
      <div className="flex items-center gap-6">
        <a href="/" className="flex items-center gap-2 text-coffee-crema font-serif font-black text-xl tracking-wider select-none hover:opacity-90">
          <Coffee className="w-6 h-6 stroke-[1.5]" />
          <span>FUTUREKAWA</span>
        </a>
        <div className="hidden md:flex items-center gap-2">
          {links.slice(0, 1).map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                `flex items-center gap-2 px-3 py-1.5 rounded text-sm font-medium transition-all ${isActive
                  ? "text-coffee-crema bg-coffee-espresso/45 border border-coffee-espresso"
                  : "text-coffee-parchment/65 hover:text-coffee-parchment hover:bg-coffee-espresso/20"
                }`
              }
            >
              <Icon className="w-4 h-4" />
              <span>{label}</span>
            </NavLink>
          ))}

          <div className="h-6 w-px bg-coffee-espresso/50 mx-2" />

          {links.slice(1, 4).map(({ to, label, flag }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                `flex items-center gap-2 px-3 py-1.5 rounded text-sm font-medium transition-all ${isActive
                  ? "text-coffee-crema bg-coffee-espresso/45 border border-coffee-espresso"
                  : "text-coffee-parchment/65 hover:text-coffee-parchment hover:bg-coffee-espresso/20"
                }`
              }
            >
              <span className="text-xs select-none">{flag}</span>
              <span>{label}</span>
            </NavLink>
          ))}
        </div>
      </div>
      <div className="flex items-center gap-4">
        {links.slice(4).map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              `flex items-center gap-2 px-3.5 py-1.5 rounded-full text-xs font-semibold uppercase tracking-wider transition-all border ${isActive
                ? "bg-red-950/40 text-red-400 border-red-800"
                : "bg-coffee-espresso/20 text-coffee-parchment/60 border-coffee-espresso/40 hover:text-coffee-parchment"
              }`
            }
          >
            <Icon className="w-3.5 h-3.5" />
            <span>{label}</span>
          </NavLink>
        ))}
      </div>
    </nav>
  );
}
