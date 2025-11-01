"""Command line entry-point for the LinkedIn Easy Apply bot."""
from __future__ import annotations

import argparse
import logging
import os
import sys

from bot import JobSearchQuery, LinkedInCredentials, LinkedInEasyApplyBot


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("keywords", help="Keywords used in the LinkedIn job search")
    parser.add_argument("--location", default="", help="Job location filter")
    parser.add_argument(
        "--experience",
        nargs="*",
        default=None,
        help="LinkedIn experience level codes (e.g. 2 for Entry level).",
    )
    parser.add_argument(
        "--max-applications",
        type=int,
        default=10,
        help="Maximum number of applications to submit in a single run.",
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run the browser in headless mode (no visible UI).",
    )
    parser.add_argument(
        "--username",
        default=os.getenv("LINKEDIN_USERNAME"),
        help="LinkedIn username or email. Defaults to LINKEDIN_USERNAME env variable.",
    )
    parser.add_argument(
        "--password",
        default=os.getenv("LINKEDIN_PASSWORD"),
        help="LinkedIn password. Defaults to LINKEDIN_PASSWORD env variable.",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging verbosity.",
    )
    return parser.parse_args(argv)


def configure_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if not args.username or not args.password:
        raise SystemExit("LinkedIn username and password must be provided via arguments or env vars")

    configure_logging(args.log_level)

    credentials = LinkedInCredentials(username=args.username, password=args.password)
    query = JobSearchQuery(
        keywords=args.keywords,
        location=args.location,
        experience_levels=args.experience,
        max_applications=args.max_applications,
    )

    bot = LinkedInEasyApplyBot(
        credentials=credentials,
        query=query,
        headless=args.headless,
    )

    applications = bot.run()
    logging.info("Submitted %s application(s)", applications)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
