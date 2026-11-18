
from collectors.gitlab_collector import GitLabCollector
from normalizers.gitlab_normalizer import GitLabNormalizer
from state.pipeline_state import PipelineState


class ExtractionService:

    def __init__(self):
        self.collector = GitLabCollector()
        self.normalizer = GitLabNormalizer()
        self.state = PipelineState()

    def extract(self):

        pipelines = self.collector.collect()

        events = []

        for pipeline in pipelines:

            project_id = self.collector.project_id
            pipeline_id = pipeline["id"]
            pipeline_status = pipeline["status"]

            if self.state.is_processed(
                project_id,
                pipeline_id,
                pipeline_status
            ):
                continue

            # Le normalizer retourne une liste d'événements
            normalized_events = self.normalizer.normalize(pipeline)

            # Ajouter tous les événements à la liste principale
            events.extend(normalized_events)

            self.state.mark_as_processed(
                project_id,
                pipeline_id,
                pipeline_status
            )

        return events
