import { Routes, Route, Navigate } from "react-router-dom";
import NavBar from "./components/NavBar.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import CountryPage from "./pages/CountryPage.jsx";
import LotDetail from "./pages/LotDetail.jsx";
import AlertsPage from "./pages/AlertsPage.jsx";

const styles = {
  layout: { minHeight: "100vh", display: "flex", flexDirection: "column" },
  main: { flex: 1, padding: "24px", maxWidth: 1200, margin: "0 auto", width: "100%" },
};

export default function App() {
  return (
    <div style={styles.layout}>
      <NavBar />
      <main style={styles.main}>
        <Routes>
          <Route path="/"              element={<Navigate to="/dashboard" replace />} />
          <Route path="/dashboard"     element={<Dashboard />} />
          <Route path="/pays/:country" element={<CountryPage />} />
          <Route path="/pays/:country/lots/:lotId" element={<LotDetail />} />
          <Route path="/alertes"       element={<AlertsPage />} />
        </Routes>
      </main>
    </div>
  );
}
