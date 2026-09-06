/**
 * How much of one country's coverage named an actor, run by run.
 *
 * The same shape as the division sparkline and drawn on the same fixed 0..1 axis, for
 * the same reason: auto-scaling would make a country that moved from 0.40 to 0.44 look
 * like one that moved from 0.10 to 0.90. The mark at one half is where the split is
 * widest, which is what every other figure on the site is ranked against.
 *
 * THIN RUNS ARE NOT DRAWN, AND THAT IS THE IMPORTANT DESIGN CONSTRAINT
 *
 * A rate over two sources is 0%, 50% or 100% and nothing else. Points below the floor
 * are kept in the count the caption states but excluded from the line, so a country with
 * three thin runs and one real one shows one dot and says why, rather than a zigzag that
 * reads as volatility.
 *
 * Inline SVG, rendered at build time, no JavaScript. Same as everything else that draws.
 */

export interface RatePoint {
  /** The day, "2026-09-06". */
  day: string;
  named: number;
  evaluable: number;
  /** Recomputed from banded stories only, before the engine kept this itself. */
  rebuilt?: boolean;
}

/** Below this many evaluable sources a rate is not a rate. Same floor the tables use. */
export const MIN_EVALUABLE_FOR_A_POINT = 3;

const W = 132;
const H = 30;
const PAD = 2;

export function RateLine({ points, label }: { points: RatePoint[]; label: string }) {
  const solid = points.filter((p) => p.evaluable >= MIN_EVALUABLE_FOR_A_POINT);
  const thin = points.length - solid.length;

  if (solid.length < 2) {
    return (
      <p className="line-none">
        {solid.length === 0
          ? `no day with ${MIN_EVALUABLE_FOR_A_POINT} or more sources yet`
          : `one day with enough sources to carry a rate`}
        {thin ? `, ${thin} too thin to draw` : ""}
      </p>
    );
  }

  const xs = solid.map((_, i) => PAD + (i * (W - 2 * PAD)) / (solid.length - 1));
  const rate = (p: RatePoint) => p.named / p.evaluable;
  const y = (r: number) => PAD + (1 - Math.min(1, Math.max(0, r))) * (H - 2 * PAD);
  const path = solid
    .map((p, i) => `${i ? "L" : "M"}${xs[i].toFixed(1)},${y(rate(p)).toFixed(1)}`)
    .join(" ");
  const first = rate(solid[0]);
  const last = rate(solid[solid.length - 1]);
  const rebuiltUpTo = solid.filter((p) => p.rebuilt).length;

  return (
    <div className="line">
      <svg
        className="line-svg line-svg-wide"
        viewBox={`0 0 ${W} ${H}`}
        role="img"
        aria-label={
          `${label}: share naming moved from ${Math.round(first * 100)}% to ` +
          `${Math.round(last * 100)}% across ${solid.length} days`
        }
      >
        <line x1={0} x2={W} y1={y(0.5)} y2={y(0.5)} className="line-mid" strokeDasharray="2 3" />
        {rebuiltUpTo > 0 && rebuiltUpTo < solid.length ? (
          // The boundary between what was recomputed and what the engine kept itself.
          <line
            x1={xs[rebuiltUpTo - 1]}
            x2={xs[rebuiltUpTo - 1]}
            y1={0}
            y2={H}
            className="line-rebuilt"
          />
        ) : null}
        <path d={path} className="line-path" fill="none" />
        <circle cx={xs[xs.length - 1]} cy={y(last)} r={2.4} className="line-now" />
      </svg>
      <p className="line-say">
        {solid.length} days ·{" "}
        <b>
          {Math.round(first * 100)}% → {Math.round(last * 100)}%
        </b>
        {thin ? <span className="line-move"> {thin} too thin to draw</span> : null}
      </p>
    </div>
  );
}
