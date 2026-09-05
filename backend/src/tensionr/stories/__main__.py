"""Command line for one pass of the story engine: `python -m tensionr.stories`.

Kept separate from `run` so the pipeline stays importable and testable without argument
parsing, and so the scheduled job has one obvious surface to call.
"""

import argparse
import logging
from pathlib import Path

from tensionr.config import WINDOW_SLOTS
from tensionr.stories.run import STATE, run


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m tensionr.stories",
        description="Run the story engine once and write the run's four outputs.",
    )
    parser.add_argument(
        "--out", type=Path, default=Path("out"), help="directory to write outputs to"
    )
    parser.add_argument(
        "--slots",
        type=int,
        default=WINDOW_SLOTS,
        help="how many 15-minute heartbeats make up the window",
    )
    parser.add_argument(
        "--aliases", type=Path, default=Path("data/actors/aliases.json")
    )
    parser.add_argument(
        "--polities", type=Path, default=Path("data/polities/domains.json")
    )
    parser.add_argument(
        "--history",
        type=Path,
        default=None,
        help="directory of per-run index.json files from the last day, for the "
        "day-wide selection; absent means select over this window alone",
    )
    parser.add_argument(
        "--state",
        type=Path,
        default=None,
        help=f"previous run's {STATE}; absent on a first run, and that is not an error",
    )
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s"
    )
    args.out.mkdir(parents=True, exist_ok=True)

    report = run(
        args.out,
        slots=args.slots,
        aliases=args.aliases,
        polities=args.polities,
        state=args.state,
        history=args.history,
    )

    # A run that measured nothing is not a failure — GDELT can publish a thin window —
    # but it must not pass silently, or the site quietly serves an empty ledger.
    if not report["published"]["with_a_band"]:
        logging.getLogger(__name__).warning(
            "no story cleared both floors this window: %d stories, %.0f%% polity coverage",
            report["published"]["stories"],
            100 * report["polities"]["rate"],
        )
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
