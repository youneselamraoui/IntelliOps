from collections import Counter

from collectors.github_collector import GitHubCollector
from normalizers.github_normalizer import GitHubNormalizer


def main():
    collector = GitHubCollector()
    normalizer = GitHubNormalizer()

    runs = collector.collect()
    print(f"Runs récupérés : {len(runs)}")

    events = []

    for run in runs:
        if run.get("status") != "completed":
            print(f"- run {run['id']} ignoré (statut : {run['status']})")
            continue

        run = collector.enrich_run(run)
        events.extend(normalizer.normalize(run))

    print(f"\nÉvénements générés : {len(events)}")
    print(dict(Counter(e.severity for e in events)))

    for e in events:
        print("\n----------------------------------------")
        print("ID       :", e.id)
        print("Type     :", e.event_type, "|", e.severity)
        print("Composant:", e.component)
        print("Message  :", e.message)
        if e.event_type == "PIPELINE_FAILURE":
            print("Étape    :", e.details.get("failed_step"))
            print("Erreur   :", e.details.get("error_type"), "-",
                  e.details.get("error_message"))
        print("URL      :", e.details.get("url"))


if __name__ == "__main__":
    main()