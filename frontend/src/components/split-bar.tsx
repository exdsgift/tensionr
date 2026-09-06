/**
 * How the sources split on naming one actor, drawn.
 *
 * The page's ranking key is `division`, the binary Shannon entropy of the naming rate:
 * 1 bit when the sources are exactly half and half, 0 when they all agree in either
 * direction. It was printed as `division 0.998` in grey, six words into a line of small
 * type, and nobody could read it. Making that number bigger would not have helped: a
 * reader has no way to know that 0.998 is the maximum and 0.1 is near-unanimity, and a
 * prominent uninterpretable number is worse than a buried one.
 *
 * So the bar shows the thing the number measures. Filled to the naming rate, with the
 * halfway point marked, because halfway *is* the maximum. A bar that stops near the
 * mark is a divided story; a bar at either extreme is an agreed one. That reading needs
 * no scale and no legend.
 *
 * Not a `Progress`: this is not progress toward anything, and the shadcn component
 * carries `role="progressbar"` with its ARIA value semantics, which would tell a screen
 * reader that 28 of 53 sources is 53% of a task. The figure is stated in text beside
 * the bar instead, and the bar itself is decoration for a screen reader.
 */

export function SplitBar({
  named,
  evaluable,
  actor,
  division,
  evenSplit,
  restate = true,
  className,
}: {
  named: number;
  evaluable: number;
  actor: string;
  /** The ranking key, in bits. Shown beside its own picture so it can be read. */
  division?: number;
  /** Restate the midpoint in sources. Used where there is room to teach the reading. */
  evenSplit?: boolean;
  /**
   * Whether the caption opens by naming the fraction again.
   *
   * True in a story row, where the bar arrives with no figure above it. False in the
   * hero, where the page has just printed `14/32` at four rems and `SOURCES NAMED
   * SPAIN` under it: repeating "14 of 32 sources named Spain" two lines later is the
   * same fact three times in one glance, and it was the first thing a reader noticed.
   */
  restate?: boolean;
  className?: string;
}) {
  if (!evaluable) return null;
  const rate = named / evaluable;
  // Below this a reader should notice: most sources covering the story did not use the
  // name at all. The same threshold marks the counts elsewhere on the page.
  const sparse = rate < 0.4;

  return (
    <div className={`split ${className ?? ""}`}>
      <div className="split-bar" aria-hidden="true">
        <i style={{ width: `${rate * 100}%` }} data-sparse={sparse || undefined} />
        {/* Where division peaks. Everything on this page is ranked by distance from it. */}
        <span className="split-mid" />
      </div>
      <p className="split-say">
        {restate ? (
          <>
            <b>{named}</b> of <b>{evaluable}</b> sources named{" "}
            <b className="split-actor">{actor}</b>
            <span className="split-rest">, {evaluable - named} did not</span>
          </>
        ) : (
          // The complement, which the figure above does not give and a reader would
          // otherwise have to subtract.
          <span className="split-rest">
            <b>{evaluable - named}</b> of them did not
          </span>
        )}
        {evenSplit ? (
          // The mark on the bar, restated in the units the reader is already holding.
          // "Halfway is the maximum" is the one thing that makes the picture readable,
          // and saying it in bits does not carry it.
          <span className="split-even">
            an even split ({Math.round(evaluable / 2)} of {evaluable}) is the most
            divided a story can be
          </span>
        ) : null}
        {division !== undefined ? (
          // The number the page ranks on, kept but given its ceiling. On its own,
          // "0.998" tells a reader nothing; "0.998 of a possible 1" at least says
          // which end is which, and the bar above says what it means.
          <span className="split-div">
            division <b>{division.toFixed(3)}</b>
            <span className="split-max"> of 1</span>
          </span>
        ) : null}
      </p>
    </div>
  );
}
