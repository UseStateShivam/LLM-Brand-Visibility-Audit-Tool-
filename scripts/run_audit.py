#!/usr/bin/env python3
"""CLI utility to execute a full brand visibility audit from the command line.

Usage:
  python scripts/run_audit.py --brand "Acme AI" --competitors "Beta AI" "Gamma AI" --category "customer support"
"""

import argparse
import asyncio
import sys

from app.core.config import get_settings
from app.core.logging import setup_logging
from app.models.audit import Audit, ProviderSelection
from app.prompts.builder import PromptBuilder
from app.providers.factory import ProviderFactory
from app.services.analysis_service import AnalysisService
from app.services.audit_service import AuditService
from app.services.query_service import QueryService
from app.services.report_service import ReportService
from app.storage.json_store import JSONAuditStore


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run an end-to-end LLM Brand Visibility Audit."
    )
    parser.add_argument("--brand", required=True, help="Canonical brand name.")
    parser.add_argument(
        "--aliases", nargs="*", default=[], help="Optional brand aliases."
    )
    parser.add_argument(
        "--competitors", nargs="*", default=[], help="Competitor brand names."
    )
    parser.add_argument(
        "--category", default="technology", help="Industry / category."
    )
    parser.add_argument(
        "--prompts",
        nargs="*",
        default=[],
        help="Custom prompt texts. If omitted, default category prompts will be used.",
    )
    parser.add_argument(
        "--providers",
        nargs="*",
        default=["openai", "gemini"],
        help="LLM providers to audit (openai, gemini).",
    )
    return parser.parse_args()


async def main() -> None:
    args = parse_args()
    settings = get_settings()
    setup_logging(log_level=settings.log_level)

    store = JSONAuditStore(settings)
    factory = ProviderFactory(settings)
    query_svc = QueryService(factory=factory, settings=settings)
    analysis_svc = AnalysisService(settings=settings)
    report_svc = ReportService(settings=settings)
    audit_svc = AuditService(
        store=store,
        query_service=query_svc,
        analysis_service=analysis_svc,
        report_service=report_svc,
    )

    prompt_builder = PromptBuilder()
    prompt_texts = args.prompts or [
        f"What are the best tools for {args.category}?",
        f"Which top companies would you recommend for modern {args.category}?",
        f"Compare the leading platforms in {args.category}.",
    ]

    prompts = [
        prompt_builder.build_from_text(
            text=p,
            topic=args.category,
            order_index=idx,
        )
        for idx, p in enumerate(prompt_texts)
    ]

    providers = [ProviderSelection(provider=p) for p in args.providers]

    audit = Audit(
        brand=args.brand,
        aliases=args.aliases,
        competitors=args.competitors,
        industry=args.category,
        topics=[args.category],
        prompts=prompts,
        providers=providers,
    )

    created = audit_svc.create_audit(audit)
    print(f"\n[+] Created Audit: {created.audit_id} for Brand '{created.brand}'")
    print(f"[*] Running audit across {len(prompts)} prompts and {len(providers)} providers...")

    try:
        report, raw_responses, _ = await audit_svc.run_audit(created.audit_id)
        print("\n==================================================")
        print("       LLM BRAND VISIBILITY AUDIT COMPLETE        ")
        print("==================================================")
        print(f"Audit ID:           {report.audit_id}")
        print(f"Brand:              {report.brand}")
        print(f"Visibility Score:   {report.overall_metrics.composite_visibility_score}/100")
        print(f"Mention Rate:       {int(report.overall_metrics.mention_rate * 100)}%")
        print(f"Recommendation Rate:{int(report.overall_metrics.recommendation_rate * 100)}%")
        print(f"Topic Coverage:     {int(report.overall_metrics.topic_coverage * 100)}%")
        print(f"Identified Gaps:    {len(report.visibility_gaps)}")
        print(f"\nExecutive Summary:\n{report.executive_summary}\n")
        print(f"Report saved to data/reports/{report.audit_id}.json")
    except Exception as exc:
        print(f"[-] Audit run failed: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
