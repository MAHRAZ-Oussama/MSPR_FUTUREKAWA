import { Routes, Route, Navigate } from "react-router-dom";
import NavBar from "./components/NavBar.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import CountryPage from "./pages/CountryPage.jsx";
import LotDetail from "./pages/LotDetail.jsx";
import AlertsPage from "./pages/AlertsPage.jsx";

export default function App() {
  return (
    <div className="min-h-screen bg-coffee-dark text-coffee-parchment font-mono flex flex-col relative overflow-x-hidden">
      {/* Topographic Andean Terrain contours (vector background) */}
      <div className="absolute top-0 right-0 w-[500px] h-[500px] pointer-events-none opacity-[0.04] select-none z-0">
        <svg viewBox="0 0 100 100" className="w-full h-full stroke-coffee-crema stroke-[0.4] fill-none">
          <path d="M-10,35 C20,30 30,5 60,15 C90,25 95,5 110,20" />
          <path d="M-10,45 C20,40 35,15 65,25 C95,35 90,15 110,30" />
          <path d="M-10,55 C15,50 40,25 70,35 C100,45 85,25 110,40" />
          <path d="M-10,65 C10,60 45,35 75,45 C105,55 80,35 110,50" />
          <path d="M-10,75 C20,70 50,45 80,55 C110,65 85,45 110,60" />
        </svg>
      </div>

      <div className="absolute bottom-0 left-0 w-[400px] h-[400px] pointer-events-none opacity-[0.03] select-none z-0">
        <svg viewBox="0 0 100 100" className="w-full h-full stroke-coffee-crema stroke-[0.4] fill-none">
          <path d="M-10,85 C20,80 30,55 60,65 C90,75 95,55 110,70" />
          <path d="M-10,95 C20,90 35,65 65,75 C95,85 90,65 110,80" />
          <path d="M-10,105 C15,100 40,75 70,85 C100,95 85,75 110,90" />
        </svg>
      </div>

      {/* Radial overlay for premium dark gradient */}
      <div className="absolute inset-0 bg-radial-at-t from-coffee-espresso/15 via-transparent to-transparent pointer-events-none z-0" />

      <NavBar />
      <main className="flex-1 py-8 px-4 md:px-8 max-w-7xl mx-auto w-full z-10 relative">
        <Routes>
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/pays/:country" element={<CountryPage />} />
          <Route path="/pays/:country/lots/:lotId" element={<LotDetail />} />
          <Route path="/alertes" element={<AlertsPage />} />
        </Routes>
      </main>
    </div>
  );
}
