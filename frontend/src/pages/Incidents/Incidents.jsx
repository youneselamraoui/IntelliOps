import { useState } from "react";
import { Database, GitBranch, Bug, Server, Shield, FileText, Layers, Search } from "lucide-react";
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

const FILTERS = [
  { value: "ALL", label: "Toutes" },
  { value: "CRITICAL", label: "Critique" },
  { value: "HIGH", label: "Élevé" },
  { value: "MEDIUM", label: "Moyen" },
  { value: "LOW", label: "Faible" },
];

function Incidents() {
  const [severityFilter, setSeverityFilter] = useState("ALL");
  const [search, setSearch] = useState("");

  const filteredIncidents = incidents.filter((incident) => {
    const matchesSeverity =
      severityFilter === "ALL" || incident.severity === severityFilter;

    const text = `${incident.id} ${incident.title} ${incident.component}`.toLowerCase();
    const matchesSearch = text.includes(search.toLowerCase());

    return matchesSeverity && matchesSearch;
  });

  function countFor(value) {
    if (value === "ALL") return incidents.length;
    return incidents.filter((incident) => incident.severity === value).length;
  }

  return (
    <div className="incidents-page">
      <h1>Incidents</h1>
      <p className="page-subtitle">
        Tous les incidents analysés par IntelliOps, avec ou sans action à valider.
      </p>

      <div className="toolbar">
        <div className="filter-pills">
          {FILTERS.map((filter) => (
            <button
              key={filter.value}
              className={severityFilter === filter.value ? "pill pill-active" : "pill"}
              onClick={() => setSeverityFilter(filter.value)}
            >
              {filter.label} · {countFor(filter.value)}
            </button>
          ))}
        </div>

        <label className="search-box">
          <Search size={18} />
          <input
            type="text"
            placeholder="Rechercher un incident"
            aria-label="Rechercher un incident"
            value={search}
            onChange={(event) => setSearch(event.target.value)}
          />
        </label>
      </div>

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
            {filteredIncidents.map((incident) => {
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

        {filteredIncidents.length === 0 && (
          <p className="empty">Aucun incident ne correspond à votre recherche.</p>
        )}
      </div>
    </div>
  );
}

export default Incidents;