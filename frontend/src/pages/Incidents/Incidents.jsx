import { Database, GitBranch, Bug, Server, Shield, FileText, Layers } from "lucide-react";
import SeverityBadge from "../../components/ui/SeverityBadge/SeverityBadge";
import { incidents } from "../../mocks/incidents";
import "./Incidents.css";

const ICONS = {
  database: Database,
  branch: GitBranch,
  bug: Bug,
  server: Server,
  shield: Shield,
  file: FileText,
  layers: Layers,
};

const STATUS_LABELS = {
  WAITING: "En attente de validation",
  NOTIFIED: "Notifié",
  ANALYZED: "Analysé",
  RESOLVED: "Résolu",
};

function Incidents() {
  return (
    <div className="incidents-page">
      <h1>Incidents</h1>
      <p className="page-subtitle">
        Tous les incidents analysés par IntelliOps, avec ou sans action à valider.
      </p>

      <div className="table-card">
        <table className="incidents-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Incident</th>
              <th>Sources</th>
              <th>Criticité</th>
              <th>Statut</th>
              <th>Détecté</th>
            </tr>
          </thead>

          <tbody>
            {incidents.map((incident) => {
              const Icon = ICONS[incident.icon];

              return (
                <tr key={incident.id}>
                  <td className="cell-id">{incident.id}</td>

                  <td>
                    <div className="incident-cell">
                      <span className="incident-icon">
                        <Icon size={18} />
                      </span>
                      <div>
                        <div className="incident-title">{incident.title}</div>
                        <div className="incident-sub">
                          {incident.component} · {incident.environment}
                        </div>
                      </div>
                    </div>
                  </td>

                  <td>
                    {incident.sources.map((source) => (
                      <span key={source} className="source-chip">{source}</span>
                    ))}
                  </td>

                  <td>
                    <SeverityBadge level={incident.severity} />
                  </td>

                  <td>
                    <span className={`status status-${incident.status.toLowerCase()}`}>
                      {STATUS_LABELS[incident.status]}
                    </span>
                  </td>

                  <td className="cell-muted">{incident.detectedAt}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default Incidents;