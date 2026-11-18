
from service.extraction_service import ExtractionService


def main():

    service = ExtractionService()

    events = service.extract()

    print(f"Nombre de nouveaux événements : {len(events)}")

    for event in events:

        print("\n================================")
        print("ID :", event.id)
        print("Source :", event.source)
        print("Component :", event.component)
        print("Type :", event.event_type)
        print("Severity :", event.severity)
        print("Message :", event.message)
        print("Status :", event.status)

        print("\n--- Détails techniques ---")

        for key, value in event.details.items():
            print(f"{key} : {value}")


if __name__ == "__main__":
    main()
