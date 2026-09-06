# history

Append-only. **Nothing here is ever rewritten** — that is the whole point of the ref.

Every run of the engine writes one directory, `history/YYYY/MM/DD/HHMM/`, holding the
files that run produced. Git then stores exactly one blob per run, so the branch grows
with information rather than with the number of runs. The old design rewrote one file
per day in full, eleven times a day, which is how `data/` became 93.6% of the
repository's history while the archive itself was being overwritten several times a day
(#10).

This is the only store in the project that time cannot rebuild. Current state is a
cache and lives on the force-pushed `data` branch; the accumulated record lives here,
and both the anomaly detection and the deviation-based index read from it.

## `history/v1/`

The v1 archive, carried over as it was found: one file per day, from the pipeline that
predates the story engine. They are daily snapshots, not per-run records, so they are
kept under a separate prefix rather than renamed into the run layout — giving them a
run timestamp would mean inventing one.
