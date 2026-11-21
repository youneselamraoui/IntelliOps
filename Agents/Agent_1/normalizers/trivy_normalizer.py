
from datetime import datetime, timezone
import hashlib

from models.event import Event


class TrivyNormalizer:

    def normalize(self, report, environment="unknown"):

        # 1. Vérifier le rapport reçu
        if not isinstance(report, dict):
            raise ValueError("Invalid Trivy report: expected a dictionary")

        events = []

        # 2. Définir une date commune pour les événements du rapport
        timestamp = datetime.now(timezone.utc)

        # 3. Récupérer le nom de l'image scannée
        artifact_name = report.get("ArtifactName") or "unknown"

        # 4. Récupérer les résultats du scan
        results = report.get("Results") or []

        # 5. Parcourir chaque résultat
        for result in results:

            if not isinstance(result, dict):
                continue

            target = result.get("Target") or artifact_name

            # 6. Récupérer les vulnérabilités
            vulnerabilities = result.get("Vulnerabilities") or []

            # 7. Parcourir chaque vulnérabilité
            for vulnerability in vulnerabilities:

                if not isinstance(vulnerability, dict):
                    continue

                cve_id = vulnerability.get("VulnerabilityID") or "UNKNOWN"
                package = vulnerability.get("PkgName") or "unknown"
                installed_version = vulnerability.get("InstalledVersion") or "unknown"
                severity = (
                    vulnerability.get("Severity") or "UNKNOWN"
                ).upper()

                # 8. Construire un identifiant stable et unique
                unique_value = (
                    f"{artifact_name}|{target}|{cve_id}|"
                    f"{package}|{installed_version}"
                )

                event_id = "TRIVY-" + hashlib.sha256(
                    unique_value.encode("utf-8")
                ).hexdigest()[:16]

                # 9. Construire le message
                message = (
                    f"Vulnerability {cve_id} detected "
                    f"in package {package} "
                    f"(severity: {severity})"
                )

                # 10. Construire l'événement IntelliOps
                event = Event(
                    id=event_id,
                    timestamp=timestamp,
                    source="TRIVY",
                    component=artifact_name,
                    environment=environment,
                    event_type="VULNERABILITY",
                    severity=severity,
                    message=message,
                    status="NEW",

                    details={
                        "target": target,
                        "vulnerability_id": cve_id,
                        "package": package,
                        "installed_version": installed_version,
                        "fixed_version": vulnerability.get("FixedVersion"),
                        "title": vulnerability.get("Title"),
                        "description": vulnerability.get("Description"),
                        "primary_url": vulnerability.get("PrimaryURL"),
                        "class": result.get("Class"),
                        "type": result.get("Type")
                    }
                )

                # 11. Ajouter l'événement à la liste
                events.append(event)

        return events
