
from collections import Counter

from service.extraction_service import ExtractionService


def main():
    service = ExtractionService()

    events = service.extract()

    print("\n========== INTELLIOPS - AGENT 1 ==========")
    print(f"Nombre de nouveaux événements : {len(events)}")

    if not events:
        print("\nAucun nouvel événement détecté.")
        return

    # Répartition des événements par sévérité
    severity_counts = Counter(event.severity for event in events)

    print("\n--- Répartition par sévérité ---")
    for severity, count in sorted(severity_counts.items()):
        print(f"{severity} : {count}")

    # Affichage des événements
    for event in events:
        print("\n========================================")
        print("ID         :", event.id)
        print("Source     :", event.source)
        print("Composant  :", event.component)
        print("Type       :", event.event_type)
        print("Sévérité   :", event.severity)
        print("Message    :", event.message)
        print("Statut     :", event.status)

        if event.details:
            print("\n--- Informations techniques ---")

            # Informations utiles pour les vulnérabilités Trivy
            important_fields = [
                "target",
                "vulnerability_id",
                "package",
                "installed_version",
                "fixed_version",
            ]

            for key in important_fields:
                if key in event.details:
                    print(f"{key} : {event.details[key]}")


if __name__ == "__main__":
    main()
