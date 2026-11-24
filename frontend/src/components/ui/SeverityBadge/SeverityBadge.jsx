import "./SeverityBadge.css";

const LABELS = {
  CRITICAL: "Critique",
  HIGH: "Élevé",
  MEDIUM: "Moyen",
  LOW: "Faible",
};

function SeverityBadge({ level }) {
  return (
    <span className={`badge badge-${level.toLowerCase()}`}>
      {LABELS[level]}
    </span>
  );
}

export default SeverityBadge;