"""Citation and source normalization extractor.

Extracts citations and source links from provider responses.
Rules:
- Missing citations != zero citations (explicit CitationStatus enum).
- Never fabricate domain names or URLs.
- Extracts inline markdown links and provider metadata sources.
"""

import re
from urllib.parse import urlparse

from app.models.citation import CitationRecord, CitationStatus
from app.models.response import RawLLMResponse


class CitationExtractor:
    """Extracts, verifies, and normalizes citation and source URLs from responses."""

    # Matches inline markdown links: [text](http...)
    MARKDOWN_URL_PATTERN = re.compile(
        r"\[([^\]]+)\]\((https?://[^\s\)]+)\)", re.IGNORECASE
    )
    # Matches plain URLs in text: https://...
    PLAIN_URL_PATTERN = re.compile(
        r"(?<!\()(https?://[a-zA-Z0-9\-\.]+\.[a-zA-Z]{2,}(?:/[^\s\)\"\'>]*)?)",
        re.IGNORECASE,
    )

    @staticmethod
    def _clean_domain(url: str) -> str:
        """Extract clean domain name without www, port, or schema."""
        if not url:
            return ""
        clean_input = url.strip().lower()
        if not clean_input.startswith(("http://", "https://")):
            clean_input = f"https://{clean_input}"
        try:
            parsed = urlparse(clean_input)
            netloc = parsed.netloc or ""
            if ":" in netloc:
                netloc = netloc.split(":")[0]
            netloc = netloc.removeprefix("www.")
            return netloc
        except Exception:
            return ""

    def extract_from_raw_response(
        self,
        raw_response: RawLLMResponse,
        brand_domain: str | None = None,
    ) -> tuple[CitationStatus, list[CitationRecord]]:
        """Extract citations from provider metadata or in-text source links.

        Returns:
            Tuple of (CitationStatus, list[CitationRecord]).
        """
        # 1. Check if provider adapter already extracted structured citations in metadata
        provider_meta = raw_response.provider_metadata or {}
        structured_citations_data = provider_meta.get("structured_citations")

        citations: list[CitationRecord] = []
        clean_brand_domain = self._clean_domain(brand_domain) if brand_domain else None

        if structured_citations_data and isinstance(structured_citations_data, list):
            for idx, item in enumerate(structured_citations_data):
                if isinstance(item, dict) and "url" in item:
                    url = item["url"]
                    domain = self._clean_domain(url)
                    is_owned = bool(clean_brand_domain and domain == clean_brand_domain)
                    citations.append(
                        CitationRecord(
                            url=url,
                            domain=domain,
                            title=item.get("title"),
                            citation_marker=item.get("citation_marker"),
                            order_index=idx,
                            is_brand_owned=is_owned,
                        )
                    )

            if citations:
                return CitationStatus.AVAILABLE, citations

        # 2. Check for inline markdown citations in response_text
        text = raw_response.response_text or ""
        seen_urls: set[str] = set()
        inline_citations: list[CitationRecord] = []

        # Parse markdown links: [title](url)
        for match in self.MARKDOWN_URL_PATTERN.finditer(text):
            title, url = match.group(1), match.group(2)
            url_clean = url.rstrip(".,;!?:")
            if url_clean not in seen_urls:
                seen_urls.add(url_clean)
                domain = self._clean_domain(url_clean)
                is_owned = bool(clean_brand_domain and domain == clean_brand_domain)
                inline_citations.append(
                    CitationRecord(
                        url=url_clean,
                        domain=domain,
                        title=title.strip(),
                        order_index=len(inline_citations),
                        is_brand_owned=is_owned,
                    )
                )

        # Parse plain URLs if no markdown links found
        if not inline_citations:
            for match in self.PLAIN_URL_PATTERN.finditer(text):
                url = match.group(1).rstrip(".,;!?:")
                if url not in seen_urls:
                    seen_urls.add(url)
                    domain = self._clean_domain(url)
                    is_owned = bool(clean_brand_domain and domain == clean_brand_domain)
                    inline_citations.append(
                        CitationRecord(
                            url=url,
                            domain=domain,
                            title=None,
                            order_index=len(inline_citations),
                            is_brand_owned=is_owned,
                        )
                    )

        if inline_citations:
            return CitationStatus.AVAILABLE, inline_citations

        # 3. If no citations found, evaluate whether the provider supports them
        # OpenAI without search grounding does not support citations natively
        provider = raw_response.provider.lower()
        if provider == "openai":
            # If no tool calls or search enabled, mark as NOT_SUPPORTED_BY_PROVIDER
            return CitationStatus.NOT_SUPPORTED_BY_PROVIDER, []

        return CitationStatus.NONE_FOUND, []
