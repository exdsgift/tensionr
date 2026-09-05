/**
 * A story's division over the runs that carried it.
 *
 * The third pillar of the v2 map was "the anomalies: deviations over time in the same
 * measure". It was designed, never built, and the data has been accumulating since
 * 2026-08-04. The engine keeps a story's identity between runs by sharing article URLs,
 * and every run publishes its own index, so the line was there all along and nothing
 * read it.
 *
 * Inline SVG, rendered at build time, no JavaScript and no charting library. A line of
 * at most sixty points does not need Recharts, and Recharts would cost more than every
 * line on the page put together.
 *
 * MOST STORIES HAVE NO LINE, and that is the important design constraint. Measured over
 * 163 runs and 1,743 banded story identities: 57% appear in exactly one run, the median
 * lifetime is one run, and only 1% reach ten. A component that drew a chart regardless
 * would draw 1,001 single dots and imply a history none of them have. So fewer than
 * three points draws nothing and says how many runs there were, which is a fact rather
 * than a picture.
 *
 * A run that did not carry the story contributes no point at all; the engine already
 * omits it rather than writing a zero. Absence and agreement are different claims, and
 * a line dipping to the floor because nobody covered a story would show a fall that
 * never happened. The consequence is that the horizontal axis is *runs that carried it*,
 * not time, and the caption has to say so.
 */

export interface Point {
  run: string;
  division: number;
  sources?: number | null;
}

const W = 132;
const H = 30;
const PAD = 2;

export function DivisionLine({
  points,
  label,
}: {
  points: Point[];
  /** Named for a screen reader, which gets the numbers rather than the picture. */
  label: string;
}) {
  if (points.length < 3) {
    return (
      <p className="line-none">
        {points.length < 2
          ? "first seen in this run"
          : `carried by ${points.length} runs so far`}
      </p>
    );
  }

  const xs = points.map((_, i) => PAD + (i * (W - 2 * PAD)) / (points.length - 1));
  // Division is a bit of entropy: 0 is unanimity, 1 is an even split. The axis is
  // therefore fixed at 0..1, never scaled to the data. Auto-scaling would make every
  // story's wobble look like the same drama.
  const y = (d: number) => PAD + (1 - Math.min(1, Math.max(0, d))) * (H - 2 * PAD);
  const path = points
    .map((p, i) => `${i ? "L" : "M"}${xs[i].toFixed(1)},${y(p.division).toFixed(1)}`)
    .join(" ");

  const first = points[0].division;
  const last = points[points.length - 1].division;
  const move = last - first;

  return (
    <div className="line">
      <svg
        className="line-svg"
        viewBox={`0 0 ${W} ${H}`}
        role="img"
        aria-label={`${label}: division moved from ${first.toFixed(2)} to ${last.toFixed(
          2,
        )} across ${points.length} runs`}
      >
        {/* Where an even split sits, so a line can be read against the same mark the
            bars use rather than against an invisible zero. */}
        <line
          x1={0}
          x2={W}
          y1={y(0.5)}
          y2={y(0.5)}
          className="line-mid"
          strokeDasharray="2 3"
        />
        <path d={path} className="line-path" fill="none" />
        <circle cx={xs[xs.length - 1]} cy={y(last)} r={2.4} className="line-now" />
      </svg>
      <p className="line-say">
        {points.length} runs ·{" "}
        <b>
          {first.toFixed(2)} → {last.toFixed(2)}
        </b>
        {Math.abs(move) >= 0.15 ? (
          <span className="line-move">
            {" "}
            {move > 0 ? "more divided as it ran" : "more agreed as it ran"}
          </span>
        ) : null}
      </p>
    </div>
  );
}
