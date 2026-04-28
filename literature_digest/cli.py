from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
from typing import Any

from .config import load_config
from .dedupe import deduplicate_entries
from .digest import write_digests
from .email_filter import classify_email
from .env import load_dotenv_file
from .gmail_client import GmailClient
from .interests import analyze_research_interests, fallback_interest_profile, read_research_interests
from .llm import build_llm_client
from .models import DigestRun, RunStats, SkippedEmail
from .parsers import parse_emails
from .ranking import count_relevance, rank_papers
from .sample_data import sample_emails


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)
    base_dir = Path.cwd()
    load_dotenv_file(base_dir / ".env")
    config = load_config(args.config)

    dry_run = _resolve_dry_run(args, config)
    if args.max_emails is not None:
        config["gmail"]["max_emails_per_run"] = args.max_emails

    sample_mode, warnings = _should_use_sample(args, config, dry_run, base_dir)
    llm = build_llm_client(config, sample_mode=sample_mode)

    if sample_mode:
        emails = sample_emails()
    else:
        gmail = GmailClient(config, base_dir=base_dir)
        emails = gmail.fetch_unread_emails(max_results=config["gmail"]["max_emails_per_run"])

    skipped: list[SkippedEmail] = []
    accepted = []
    for email in emails:
        decision = classify_email(email, config)
        if decision.skip:
            skipped.append(
                SkippedEmail(
                    email_id=email.id,
                    subject=email.subject,
                    sender=email.sender,
                    reason=decision.reason,
                )
            )
        else:
            accepted.append(email)

    entries = parse_emails(accepted)
    deduped = deduplicate_entries(
        entries,
        fuzzy_title_threshold=int(config["parsing"].get("fuzzy_title_threshold", 92)),
    )
    interests_path = _resolve_path(config["research_interests"]["path"], base_dir)
    interest_text = read_research_interests(interests_path)
    if deduped.unique_entries:
        interest_profile = analyze_research_interests(interest_text, llm)
        ranked = rank_papers(deduped.unique_entries, interest_profile, llm)
    else:
        warnings.append("没有找到可处理的未读论文条目，本次生成空 digest。")
        interest_profile = fallback_interest_profile(interest_text)
        ranked = []

    if not config["digest"].get("include_low_relevance", True):
        ranked = [paper for paper in ranked if paper.relevance != "low"]

    stats = RunStats(
        emails_read=len(emails),
        skipped_emails=len(skipped),
        paper_entries_extracted=len(entries),
        duplicates_removed=deduped.duplicates_removed,
        high_relevance=count_relevance(ranked, "high"),
        medium_relevance=count_relevance(ranked, "medium"),
        low_relevance=count_relevance(ranked, "low"),
        sample_mode=sample_mode,
    )
    date_label = args.date or datetime.now().strftime("%Y-%m-%d")
    run = DigestRun(
        date_label=date_label,
        stats=stats,
        interest_profile=interest_profile,
        papers=_apply_digest_limits(ranked, config),
        skipped=skipped if config["filtering"].get("audit_skipped_emails", True) else [],
        warnings=warnings,
    )
    output_paths = write_digests(
        run,
        _resolve_path(config["digest"]["output_dir"], base_dir),
        formats=list(config["digest"].get("output_formats", ["md", "html"])),
    )

    if not dry_run and not sample_mode and config["gmail"].get("mark_as_read", False):
        gmail = GmailClient(config, base_dir=base_dir)
        gmail.mark_as_read([email.id for email in accepted])

    print("Digest written:")
    for output_path in output_paths:
        print(f"  - {output_path}")
    print(
        "Stats: "
        f"emails={stats.emails_read}, entries={stats.paper_entries_extracted}, "
        f"duplicates={stats.duplicates_removed}, high={stats.high_relevance}, "
        f"medium={stats.medium_relevance}, low={stats.low_relevance}, skipped={stats.skipped_emails}"
    )
    if dry_run:
        print("Dry-run mode: no email state was modified and no emails were sent.")
    return 0


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate a daily academic literature digest.")
    parser.add_argument("--config", help="Path to config YAML. Defaults to config.local.yaml if present.")
    parser.add_argument("--dry-run", action="store_true", help="Do not modify Gmail state.")
    parser.add_argument("--no-dry-run", action="store_true", help="Allow configured non-dry-run actions.")
    parser.add_argument("--max-emails", type=int, help="Override gmail.max_emails_per_run.")
    parser.add_argument("--sample", action="store_true", help="Use built-in sample emails.")
    parser.add_argument("--date", help="Override output date label, e.g. 2026-04-28.")
    return parser


def _resolve_dry_run(args: argparse.Namespace, config: dict[str, Any]) -> bool:
    if args.no_dry_run:
        return False
    if args.dry_run:
        return True
    return bool(config["safety"].get("dry_run_default", True))


def _should_use_sample(
    args: argparse.Namespace,
    config: dict[str, Any],
    dry_run: bool,
    base_dir: Path,
) -> tuple[bool, list[str]]:
    warnings: list[str] = []
    if args.sample:
        warnings.append("使用内置样例邮件进行 dry-run；未读取真实 Gmail。")
        return True, warnings
    credentials_path = _resolve_path(config["gmail"].get("credentials_path", "credentials.json"), base_dir)
    if (
        dry_run
        and config["safety"].get("allow_sample_without_credentials", True)
        and not credentials_path.exists()
    ):
        warnings.append(
            f"未找到 Gmail OAuth 凭据 {credentials_path}，本次 dry-run 使用内置样例邮件。"
        )
        return True, warnings
    return False, warnings


def _apply_digest_limits(ranked, config: dict[str, Any]):
    high_limit = int(config["digest"].get("max_high_relevance", 20))
    medium_limit = int(config["digest"].get("max_medium_relevance", 30))
    high_count = medium_count = 0
    result = []
    for paper in ranked:
        if paper.relevance == "high":
            if high_count >= high_limit:
                continue
            high_count += 1
        elif paper.relevance == "medium":
            if medium_count >= medium_limit:
                continue
            medium_count += 1
        result.append(paper)
    return result


def _resolve_path(value: str | Path, base_dir: Path) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return base_dir / path
