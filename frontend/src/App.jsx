import SeverityBadge from "./components/ui/SeverityBadge/SeverityBadge";

function App() {
  return (
    <div style={{ padding: 40, display: "flex", gap: 12 }}>
      <SeverityBadge level="CRITICAL" />
      <SeverityBadge level="HIGH" />
      <SeverityBadge level="MEDIUM" />
      <SeverityBadge level="LOW" />
    </div>
  );
}

export default App;