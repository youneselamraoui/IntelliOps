
from collectors.trivy_collector import TrivyCollector

# Initialiser le collecteur
collector = TrivyCollector()

# Récupérer le rapport depuis GitLab
report = collector.collect(
    source="gitlab",
    project_id=89112860,
    job_id=18206368947,
    artifact_path="trivy-report.json"
)

# Afficher quelques informations
print("\n===== RESULTAT DU TEST =====")

print("Type :", type(report))
print("Clés :", list(report.keys()))

print("Artifact :", report.get("ArtifactName"))
print("Type de scan :", report.get("ArtifactType"))

print("============================")
