#!/usr/bin/env python3
"""CLI utility to generate a formatted text or JSON report summary for an audit.

Usage:
  python scripts/generate_report.py --audit-id <AUDIT_ID> [--json]
"""

import argparse
import json
import sys

from app.core.config import get_settings
from app.services.analysis_service import AnalysisService
from app.services.audit_service import AuditService
from app.services.query_service import QueryService
from app.services.report_service import ReportService
from app.storage.json_store import JSONAuditStore


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Print or export an LLM Brand Visibility Audit Report."
    )
    parser.add_argument("--audit-id", required=True, help="Existing audit ID.")
    parser.add_argument(
        "--json", action="store_true", help="Output full JSON instead of text summary."
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    settings = get_settings()
    store = JSONAuditStore(settings)
    report_svc = ReportService(settings=settings)
    audit_svc = AuditService(
        store=store,
        query_service=QueryService(settings=settings),
        analysis_service=AnalysisService(settings=settings),
        report_service=report_svc,
    )

    try:
        report = audit_svc.get_report(args.audit_id)
        if args.json:
            print(json.dumps(report.model_dump(), indent=2, default=str))
            return

        summary = report.client_summary
        print("\n" + "=" * 60)
        print("         LLM BRAND VISIBILITY CLIENT SUMMARY")
        print("=" * 60)
        print(f"Brand:              {summary.brand}")
        print(f"Audit ID:           {summary.audit_id}")
        print(f"Providers Tested:   {', '.join(summary.providers_tested)}")
        print(f"Prompts Tested:     {summary.total_prompts_tested}")
        print("-" * 60)
        print("VISIBILITY SNAPSHOT:")
        print(f"  Composite Score:      {summary.visibility_score}/100")
        print(f"  Mention Rate:         {summary.mention_rate_percentage}%")
        print(f"  Recommendation Rate:  {summary.recommendation_rate_percentage}%")
        print(f"  Topic Coverage:       {summary.topic_coverage_percentage}%")
        print(f"  Citations Note:       {summary.citation_coverage_note}")
        print("-" * 60)
        print("TOP STRENGTHS:")
        for s in summary.top_strengths:
            print(f"  [+] {s}")
        print("\nCRITICAL VISIBILITY GAPS:")
        for g in summary.critical_visibility_gaps:
            print(f"  [!] {g}")
        print("\nCOMPETITOR HIGHLIGHTS:")
        for c in summary.competitor_highlights:
            print(f"  [*] {c}")
        print("\nSOURCE PATTERNS:")
        for sp in summary.source_attribution_patterns:
            print(f"  [>] {sp}")
        print("-" * 60)
        print(f"WHAT THIS MEANS:\n{summary.what_this_means}\n")
        print("RECOMMENDED INVESTIGATION AREAS:")
        for rec in summary.recommended_investigation_areas:
            print(f"  - {rec}")
        print("=" * 60 + "\n")

    except Exception as exc:
        print(f"[-] Error retrieving report for '{args.audit_id}': {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
