"""Mathematical metrics calculator for brand visibility.

Implements transparent, documented, deterministic formulas:
- mention_rate = prompts_where_brand_mentioned / total_successful_responses
- recommendation_rate = prompts_where_brand_recommended / total_successful_responses
- citation_rate = responses_with_brand_citations / responses_with_available_citations
- topic_coverage = topics_with_brand_mention / total_topics_audited
- competitor_presence_rate = responses_with_any_competitor / total_successful_responses
- average_mention_position = mean normalized position of first brand mention
"""

from collections import defaultdict

from app.models.citation import CitationStatus
from app.models.metrics import (
    CompetitorSummaryMetric,
    ProviderMetric,
    TopicMetric,
)
from app.models.observation import RecommendationClass, ResponseObservation
from app.models.response import RawLLMResponse


class MetricsCalculator:
    """Calculates granular and aggregate visibility metrics from observations."""

    @staticmethod
    def calculate_topic_metrics(
        observations: list[ResponseObservation],
    ) -> list[TopicMetric]:
        """Aggregate visibility metrics grouped by topic."""
        topic_groups: dict[str, list[ResponseObservation]] = defaultdict(list)
        for obs in observations:
            topic_groups[obs.topic].append(obs)

        results: list[TopicMetric] = []
        for topic, obs_list in topic_groups.items():
            total = len(obs_list)
            mentions = sum(1 for o in obs_list if o.brand_mentioned)
            recs = sum(
                1
                for o in obs_list
                if o.recommendation_class
                in (
                    RecommendationClass.RECOMMENDED,
                    RecommendationClass.STRONGLY_RECOMMENDED,
                )
            )
            comps = sum(1 for o in obs_list if o.competitors_present)

            results.append(
                TopicMetric(
                    topic=topic,
                    total_prompts=total,
                    successful_responses=total,
                    brand_mentions=mentions,
                    mention_rate=round(mentions / total, 4) if total > 0 else 0.0,
                    recommendation_rate=round(recs / total, 4) if total > 0 else 0.0,
                    competitor_presence_rate=(
                        round(comps / total, 4) if total > 0 else 0.0
                    ),
                )
            )

        results.sort(key=lambda x: x.topic)
        return results

    @staticmethod
    def calculate_provider_metrics(
        raw_responses: list[RawLLMResponse],
        observations: list[ResponseObservation],
    ) -> list[ProviderMetric]:
        """Aggregate operational and visibility metrics by LLM provider."""
        # Map observations by response_id
        obs_by_resp = {o.response_id: o for o in observations}

        provider_responses: dict[str, list[RawLLMResponse]] = defaultdict(list)
        for r in raw_responses:
            provider_responses[r.provider].append(r)

        results: list[ProviderMetric] = []
        for provider, resp_list in provider_responses.items():
            total_req = len(resp_list)
            successes = [r for r in resp_list if r.success]
            failures = total_req - len(successes)

            model_name = resp_list[0].model if resp_list else "unknown"
            latencies = [r.latency_ms for r in successes]
            avg_latency = round(sum(latencies) / len(latencies), 2) if latencies else 0.0

            # Compute mention & recommendation rates across successful responses
            brand_mentions = 0
            recommendations = 0
            citations_supported = False

            for r in successes:
                obs = obs_by_resp.get(r.response_id)
                if obs:
                    if obs.brand_mentioned:
                        brand_mentions += 1
                    if obs.recommendation_class in (
                        RecommendationClass.RECOMMENDED,
                        RecommendationClass.STRONGLY_RECOMMENDED,
                    ):
                        recommendations += 1
                    if obs.citation_status in (
                        CitationStatus.AVAILABLE,
                        CitationStatus.NONE_FOUND,
                    ):
                        citations_supported = True

            succ_count = len(successes)
            mention_rate = round(brand_mentions / succ_count, 4) if succ_count > 0 else 0.0
            rec_rate = round(recommendations / succ_count, 4) if succ_count > 0 else 0.0

            results.append(
                ProviderMetric(
                    provider=provider,
                    model=model_name,
                    total_requests=total_req,
                    successful_requests=succ_count,
                    failed_requests=failures,
                    brand_mention_count=brand_mentions,
                    mention_rate=mention_rate,
                    recommendation_rate=rec_rate,
                    average_latency_ms=avg_latency,
                    citations_supported=citations_supported,
                )
            )

        results.sort(key=lambda x: x.provider)
        return results

    @staticmethod
    def calculate_competitor_metrics(
        observations: list[ResponseObservation],
        configured_competitors: list[str],
    ) -> list[CompetitorSummaryMetric]:
        """Aggregate head-to-head visibility performance per competitor."""
        total_obs = len(observations)
        results: list[CompetitorSummaryMetric] = []

        for competitor in configured_competitors:
            comp_clean = competitor.strip()
            if not comp_clean:
                continue

            mentions = 0
            wins = 0      # competitor mentioned, brand absent
            losses = 0    # brand mentioned, competitor absent
            co_occurs = 0 # both mentioned

            for obs in observations:
                # Find mention record for this competitor
                comp_match = next(
                    (c for c in obs.competitor_mentions if c.competitor_name.lower() == comp_clean.lower()),
                    None,
                )
                comp_is_present = bool(comp_match and comp_match.mentioned)
                brand_is_present = obs.brand_mentioned

                if comp_is_present:
                    mentions += 1

                if comp_is_present and not brand_is_present:
                    wins += 1
                elif brand_is_present and not comp_is_present:
                    losses += 1
                elif comp_is_present and brand_is_present:
                    co_occurs += 1

            mention_rate = round(mentions / total_obs, 4) if total_obs > 0 else 0.0

            results.append(
                CompetitorSummaryMetric(
                    competitor_name=comp_clean,
                    total_responses=total_obs,
                    mentions_count=mentions,
                    mention_rate=mention_rate,
                    head_to_head_wins=wins,
                    head_to_head_losses=losses,
                    co_occurrences=co_occurs,
                )
            )

        # Sort competitors by mention frequency descending
        results.sort(key=lambda c: c.mentions_count, reverse=True)
        return results

    @staticmethod
    def calculate_overall_metrics(
        total_prompts: int,
        raw_responses: list[RawLLMResponse],
        observations: list[ResponseObservation],
        total_topics_count: int,
    ) -> tuple[
        int, int, int, int, float, float, float | None, float, float, float | None
    ]:
        """Calculate master aggregate audit rates and positions."""
        total_requests = len(raw_responses)
        successful = sum(1 for r in raw_responses if r.success)
        failed = total_requests - successful

        if not observations:
            return (
                total_prompts,
                total_requests,
                successful,
                failed,
                0.0,
                0.0,
                None,
                0.0,
                0.0,
                None,
            )

        obs_count = len(observations)
        brand_mentions = sum(1 for o in observations if o.brand_mentioned)
        mention_rate = round(brand_mentions / obs_count, 4)

        recommendations = sum(
            1
            for o in observations
            if o.recommendation_class
            in (
                RecommendationClass.RECOMMENDED,
                RecommendationClass.STRONGLY_RECOMMENDED,
            )
        )
        rec_rate = round(recommendations / obs_count, 4)

        # Citations rate: only compute across observations where citations are supported
        supported_citation_obs = [
            o
            for o in observations
            if o.citation_status
            in (CitationStatus.AVAILABLE, CitationStatus.NONE_FOUND)
        ]
        citation_rate: float | None = None
        if supported_citation_obs:
            brand_cited = sum(
                1
                for o in supported_citation_obs
                if any(c.is_brand_owned for c in o.citations)
            )
            citation_rate = round(brand_cited / len(supported_citation_obs), 4)

        # Topic coverage: topics with at least one brand mention / total topics
        topics_with_mention = {
            o.topic for o in observations if o.brand_mentioned and o.topic
        }
        effective_total_topics = max(1, total_topics_count)
        topic_coverage = round(
            min(1.0, len(topics_with_mention) / effective_total_topics), 4
        )

        # Competitor presence rate
        competitor_obs = sum(1 for o in observations if o.competitors_present)
        comp_presence_rate = round(competitor_obs / obs_count, 4)

        # Average mention position
        positions = [
            o.first_brand_position
            for o in observations
            if o.brand_mentioned and o.first_brand_position is not None
        ]
        avg_pos = round(sum(positions) / len(positions), 4) if positions else None

        return (
            total_prompts,
            total_requests,
            successful,
            failed,
            mention_rate,
            rec_rate,
            citation_rate,
            topic_coverage,
            comp_presence_rate,
            avg_pos,
        )
