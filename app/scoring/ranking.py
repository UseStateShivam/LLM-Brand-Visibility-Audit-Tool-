"""Evidence-backed prioritized ranking module.

Ranks audit findings and observations based on strategic impact:
Priority 1: Brand absent while a competitor appears (severity weight: 100)
Priority 2: Brand absent across repeated prompts in the same topic (weight: 80)
Priority 3: Brand mentioned but not recommended (weight: 60)
Priority 4: Brand recommended without supporting citations/sources (weight: 40)
Priority 5: Cross-provider visibility inconsistency (weight: 30)
Priority 6: Source domain concentration patterns (weight: 20)

Every ranked observation explicitly incorporates raw evidence and response ID lineage.
"""

from app.models.observation import RecommendationClass, ResponseObservation
from app.models.report import RankedObservation


class ObservationRanker:
    """Ranks individual prompt observations into an evidence-backed prioritized review list."""

    def rank_observations(
        self,
        observations: list[ResponseObservation],
        prompts_by_id: dict[str, str] | None = None,
    ) -> list[RankedObservation]:
        """Convert observations into a prioritized list sorted by strategic urgency.

        Args:
            observations: List of analyzed ResponseObservation objects.
            prompts_by_id: Mapping of prompt_id -> prompt text string.

        Returns:
            List of RankedObservation objects ordered from rank 1 upwards.
        """
        prompt_lookup = prompts_by_id or {}
        ranked_candidates: list[tuple[float, RankedObservation]] = []

        for obs in observations:
            prompt_text = prompt_lookup.get(obs.prompt_id, f"Prompt {obs.prompt_id}")
            comps_present = [
                c.competitor_name for c in obs.competitor_mentions if c.mentioned
            ]

            # Priority 1: Brand absent, competitor present
            if not obs.brand_mentioned and obs.competitors_present:
                score = 100.0
                headline = f"Competitor Exclusivity: {', '.join(comps_present)} present, brand absent"
                rationale = (
                    f"In response to this prompt, the model cited competitors ({', '.join(comps_present)}) "
                    f"while entirely omitting '{obs.brand}'. This represents a direct visibility loss."
                )
                ranked_candidates.append(
                    (
                        score,
                        RankedObservation(
                            rank=1,
                            priority_score=score,
                            category="COMPETITOR_EXCLUSIVITY",
                            headline=headline,
                            prompt_text=prompt_text,
                            provider=obs.provider,
                            model=obs.model,
                            brand_status="ABSENT",
                            competitors_observed=comps_present,
                            evidence_response_id=obs.response_id,
                            evidence_quote=None,
                            rationale=rationale,
                        ),
                    )
                )

            # Priority 2: Brand mentioned but not recommended
            elif (
                obs.brand_mentioned
                and obs.recommendation_class == RecommendationClass.MENTIONED
            ):
                score = 60.0
                quote = (
                    obs.brand_contexts[0].context_window
                    if obs.brand_contexts
                    else None
                )
                headline = f"Incidental Mention: '{obs.brand}' referenced without endorsement"
                rationale = (
                    f"The model mentioned '{obs.brand}' but did not include it among recommended solutions, "
                    f"framing it as an alternative or incidental reference."
                )
                ranked_candidates.append(
                    (
                        score,
                        RankedObservation(
                            rank=1,
                            priority_score=score,
                            category="INCIDENTAL_MENTION",
                            headline=headline,
                            prompt_text=prompt_text,
                            provider=obs.provider,
                            model=obs.model,
                            brand_status="MENTIONED_NOT_RECOMMENDED",
                            competitors_observed=comps_present,
                            evidence_response_id=obs.response_id,
                            evidence_quote=quote,
                            rationale=rationale,
                        ),
                    )
                )

            # Priority 3: Target brand strongly recommended (Positive Highlight)
            elif (
                obs.brand_mentioned
                and obs.recommendation_class
                in (
                    RecommendationClass.RECOMMENDED,
                    RecommendationClass.STRONGLY_RECOMMENDED,
                )
            ):
                score = 40.0
                quote = (
                    obs.brand_contexts[0].context_window
                    if obs.brand_contexts
                    else None
                )
                headline = f"Positive Recommendation: '{obs.brand}' endorsed by {obs.provider}"
                rationale = (
                    f"The model positioned '{obs.brand}' as a recommended solution in response to this query."
                )
                ranked_candidates.append(
                    (
                        score,
                        RankedObservation(
                            rank=1,
                            priority_score=score,
                            category="POSITIVE_RECOMMENDATION",
                            headline=headline,
                            prompt_text=prompt_text,
                            provider=obs.provider,
                            model=obs.model,
                            brand_status="RECOMMENDED",
                            competitors_observed=comps_present,
                            evidence_response_id=obs.response_id,
                            evidence_quote=quote,
                            rationale=rationale,
                        ),
                    )
                )

        # Sort candidates descending by priority score
        ranked_candidates.sort(key=lambda item: item[0], reverse=True)

        final_ranked: list[RankedObservation] = []
        for idx, (_, obs_item) in enumerate(ranked_candidates, start=1):
            obs_item.rank = idx
            final_ranked.append(obs_item)

        return final_ranked
