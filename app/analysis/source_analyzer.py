"""Source and domain analyzer.

Aggregates source domains across multiple observations to identify:
- High-frequency influence domains observed alongside answers
- Presence of brand-owned domains vs 3rd party comparison sites
- Domain concentration patterns across providers and topics
Strictly adheres to descriptive phrasing: "Sources observed alongside the model's answer",
not claiming unproven causal influence.
"""

from collections import Counter

from app.models.citation import CitationRecord, CitationStatus
from app.models.metrics import DomainFrequency, SourceAnalysisSummary
from app.models.observation import ResponseObservation


class SourceAnalyzer:
    """Aggregates and analyzes domain patterns from audit observations."""

    def analyze_sources(
        self,
        observations: list[ResponseObservation],
        brand_domain: str | None = None,
    ) -> SourceAnalysisSummary:
        """Calculate domain frequencies and source distributions across observations."""
        all_citations: list[CitationRecord] = []
        supported_responses_count = 0

        for obs in observations:
            if obs.citation_status in (CitationStatus.AVAILABLE, CitationStatus.NONE_FOUND):
                supported_responses_count += 1
            all_citations.extend(obs.citations)

        total_citations = len(all_citations)
        if total_citations == 0:
            return SourceAnalysisSummary(
                total_citations=0,
                unique_domains_count=0,
                brand_owned_citations=0,
                third_party_citations=0,
                top_domains=[],
                citations_available_rate=(
                    supported_responses_count / len(observations)
                    if observations
                    else 0.0
                ),
            )

        domain_counter: Counter[str] = Counter()
        brand_owned_count = 0
        domain_owned_map: dict[str, bool] = {}

        for cit in all_citations:
            domain = cit.domain
            if domain:
                domain_counter[domain] += 1
                if cit.is_brand_owned:
                    brand_owned_count += 1
                    domain_owned_map[domain] = True
                elif domain not in domain_owned_map:
                    domain_owned_map[domain] = False

        unique_domains = len(domain_counter)
        third_party_count = total_citations - brand_owned_count

        # Build sorted list of top domains
        top_domains: list[DomainFrequency] = []
        for domain, count in domain_counter.most_common(15):
            share = round(count / total_citations, 4)
            top_domains.append(
                DomainFrequency(
                    domain=domain,
                    citation_count=count,
                    is_brand_owned=domain_owned_map.get(domain, False),
                    percentage_of_all_citations=share,
                )
            )

        avail_rate = (
            supported_responses_count / len(observations) if observations else 0.0
        )

        return SourceAnalysisSummary(
            total_citations=total_citations,
            unique_domains_count=unique_domains,
            brand_owned_citations=brand_owned_count,
            third_party_citations=third_party_count,
            top_domains=top_domains,
            citations_available_rate=round(avail_rate, 4),
        )
