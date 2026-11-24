import "./StatCard.css";

function StatCard({ value, label, icon, color = "teal" }) {
  return (
    <div className="stat-card">
      <span className={`stat-icon stat-icon-${color}`}>{icon}</span>
      <div>
        <div className="stat-value">{value}</div>
        <div className="stat-label">{label}</div>
      </div>
    </div>
  );
}

export default StatCard;