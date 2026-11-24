import SeverityBadge from "./components/ui/SeverityBadge/SeverityBadge";
import Button from "./components/ui/Button/Button";
import StatCard from "./components/ui/StatCard/StatCard";

function App() {
  return (
    <div style={{ padding: 40, display: "flex", flexDirection: "column", gap: 32 }}>

      {/* Les cartes */}
      <div style={{ display: "flex", gap: 20 }}>
        <StatCard value={2} label="À valider" icon="✓" color="purple" />
        <StatCard value={3} label="Notifications non lues" icon="!" color="teal" />
        <StatCard value={18} label="Décisions ce mois" icon="◷" color="grey" />
      </div>

      {/* Les boutons */}
      <div style={{ display: "flex", gap: 12 }}>
        <Button>Examiner</Button>
        <Button variant="secondary">Examiner</Button>
      </div>

      {/* Les badges */}
      <div style={{ display: "flex", gap: 12 }}>
        <SeverityBadge level="CRITICAL" />
        <SeverityBadge level="HIGH" />
        <SeverityBadge level="MEDIUM" />
        <SeverityBadge level="LOW" />
      </div>

    </div>
  );
}

export default App;