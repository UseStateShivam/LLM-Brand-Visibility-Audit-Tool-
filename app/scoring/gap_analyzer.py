"""Visibility gap detector module.

Identifies observable mismatches between brand visibility and market expectations:
- Gap A: Competitor Presence Gap (target absent while competitor is recommended/mentioned)
- Gap B: Topic Invisibility Gap (target absent across an entire topic cluster)
- Gap C: Weak Recommendation Gap (target mentioned, but not recommended)
- Gap D: Provider Inconsistency Gap (brand appears in one LLM provider, absent in another)
Each gap links directly to evidence response IDs.
"""

from collections import defaultdict

from app.models.observation import RecommendationClass, ResponseObservation
from app.models.report import GapSeverity, VisibilityGap


class GapAnalyzer:
    """Detects and categorizes evidence-backed visibility gaps."""

    def analyze_gaps(
        self,
        observations: list[ResponseObservation],
    ) -> list[VisibilityGap]:
        """Examine observations and produce traceable VisibilityGap records."""
        gaps: list[VisibilityGap] = []
        if not observations:
            return gaps

        # 1. Competitor Presence Gaps: Target absent while competitor present
        competitor_gaps_by_comp: dict[str, list[str]] = defaultdict(list)
        for obs in observations:
            if not obs.brand_mentioned and obs.competitors_present:
                for comp in obs.competitor_mentions:
                    if comp.mentioned:
                        competitor_gaps_by_comp[comp.competitor_name].append(
                            obs.response_id
                        )

        for comp_name, resp_ids in competitor_gaps_by_comp.items():
            gaps.append(
                VisibilityGap(
                    gap_id=f"gap_comp_{comp_name.lower().replace(' ', '_')}",
                    gap_type="COMPETITOR_PRESENCE_GAP",
                    severity=GapSeverity.CRITICAL,
                    title=f"Competitor Advantage: '{comp_name}'",
                    description=(
                        f"Target brand was completely absent while competitor '{comp_name}' "
                        f"was present in {len(resp_ids)} LLM answer(s)."
                    ),
                    competitors_involved=[comp_name],
                    evidence_response_ids=resp_ids[:10],
                )
            )

        # 2. Topic Invisibility Gaps: Target absent across an entire topic
        topic_obs: dict[str, list[ResponseObservation]] = defaultdict(list)
        for obs in observations:
            topic_obs[obs.topic].append(obs)

        for topic, obs_list in topic_obs.items():
            mentions = sum(1 for o in obs_list if o.brand_mentioned)
            if mentions == 0 and len(obs_list) >= 2:
                resp_ids = [o.response_id for o in obs_list]
                gaps.append(
                    VisibilityGap(
                        gap_id=f"gap_topic_{topic.lower().replace(' ', '_')}",
                        gap_type="TOPIC_INVISIBILITY_GAP",
                        severity=GapSeverity.HIGH,
                        title=f"Zero Visibility in Topic: '{topic}'",
                        description=(
                            f"Target brand was not mentioned in any of the {len(obs_list)} "
                            f"prompts evaluated under topic '{topic}'."
                        ),
                        affected_topic=topic,
                        evidence_response_ids=resp_ids[:10],
                    )
                )

        # 3. Weak Recommendation Gaps: Mentioned but not recommended
        weak_rec_responses = [
            o.response_id
            for o in observations
            if o.brand_mentioned
            and o.recommendation_class == RecommendationClass.MENTIONED
        ]
        if weak_rec_responses:
            gaps.append(
                VisibilityGap(
                    gap_id="gap_weak_recommendation",
                    gap_type="WEAK_RECOMMENDATION_GAP",
                    severity=GapSeverity.MEDIUM,
                    title="Incidental Mention Without Endorsement",
                    description=(
                        f"Target brand was mentioned but not classified as recommended or top choice "
                        f"in {len(weak_rec_responses)} response(s)."
                    ),
                    evidence_response_ids=weak_rec_responses[:10],
                )
            )

        # 4. Provider Inconsistency Gaps: Prompt present in provider A, absent in provider B
        prompt_provider_map: dict[str, dict[str, ResponseObservation]] = defaultdict(
            dict
        )
        for obs in observations:
            prompt_provider_map[obs.prompt_id][obs.provider] = obs

        inconsistent_responses: list[str] = []
        for _prompt_id, prov_map in prompt_provider_map.items():
            if len(prov_map) > 1:
                statuses = {p: o.brand_mentioned for p, o in prov_map.items()}
                # Check if mixed presence (some True, some False)
                if True in statuses.values() and False in statuses.values():
                    for o in prov_map.values():
                        inconsistent_responses.append(o.response_id)

        if inconsistent_responses:
            # Deduplicate response IDs
            unique_inconsistents = list(dict.fromkeys(inconsistent_responses))
            gaps.append(
                VisibilityGap(
                    gap_id="gap_provider_discrepancy",
                    gap_type="PROVIDER_DISCREPANCY_GAP",
                    severity=GapSeverity.LOW,
                    title="Cross-Provider Visibility Discrepancy",
                    description=(
                        f"Target brand presence diverged between providers on identical prompts "
                        f"across {len(unique_inconsistents)} response pairs."
                    ),
                    evidence_response_ids=unique_inconsistents[:10],
                )
            )

        # Sort gaps by severity: CRITICAL -> HIGH -> MEDIUM -> LOW
        severity_order = {
            GapSeverity.CRITICAL: 0,
            GapSeverity.HIGH: 1,
            GapSeverity.MEDIUM: 2,
            GapSeverity.LOW: 3,
        }
        gaps.sort(key=lambda g: severity_order.get(g.severity, 99))
        return gaps
