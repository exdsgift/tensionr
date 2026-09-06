/**
 * Where the five featured stories sit relative to one another in the space that
 * grouped them.
 *
 * The engine groups articles by the cosine distance between 512-dimensional document
 * embeddings. Every figure on this page is downstream of that space and nothing on the
 * page has ever shown it. This does, on a plane, which is a lossy thing to do, so the
 * two numbers that say how lossy are printed under the figure rather than left out.
 *
 * WHY FIVE AND NOT ALL OF THEM
 *
 * Measured on a real window, the first two principal components of the whole 26,015
 * article window carry 7.4% of its variance and 42 are needed for half. That picture is
 * a cloud, and a reader would take the absence of structure in it for a finding about
 * the news. Fitted to the five featured stories alone the same procedure carries 32.3%,
 * and 90.5% of the plotted points have their nearest neighbour on the plane inside the
 * story they actually belong to. At twenty stories that falls to 74.8%: a quarter of
 * the adjacencies a reader would see would be artefacts of the flattening. So the cut
 * is measured, not aesthetic, and the engine refuses to publish a projection whose
 * agreement falls below its floor rather than drawing it anyway.
 *
 * WHY THE GROUPS ARE NUMBERED IN PLACE
 *
 * shadcn's stock palette here is neutral: five greys at zero chroma. Five series told
 * apart only by grey would be unreadable at this size, and colour alone would fail
 * WCAG 1.4.1 regardless of the palette. Each group therefore carries its own number
 * where it sits, matching the story's position on the page, so nothing has to be
 * matched against a legend and nothing depends on telling two greys apart.
 *
 * Inline SVG, rendered at build time, no JavaScript and no charting library. shadcn's
 * own Chart is Recharts, about 100 KB gzipped, against a content budget of 160 KB that
 * a heavy run already fills to 147 (ADR 0002). This costs about 2 KB.
 */

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export interface LatentStory {
  /** Position on the page, 1-based, which is what the figure labels. */
  rank: number;
  headline: string;
  actor: string;
  points: [number, number][];
  shown: number;
  articles: number;
}

export interface LatentFacts {
  grid: number;
  retained: number;
  agreement: number;
  plotted: number;
  articles: number;
}

/** Drawing box. Square, because neither axis means anything the other does not. */
const SIZE = 320;
const PAD = 14;

/** Dot radius, and the tone each group is drawn at, darkest first.
 *
 * Not shadcn's `--chart-1..5`: that ramp is identical in both themes here, and
 * measured against the plot background it gives 1.36:1 for chart-1 in light and
 * 1.00:1 for chart-5 in dark, where it is exactly the background colour. These are
 * `--foreground` at five opacities, which inverts with the theme by construction and
 * clears 3:1 in both. See the note in globals.css for the measurements. */
const DOT = 2.1;
const RAMP = ["lm-t1", "lm-t2", "lm-t3", "lm-t4", "lm-t5"] as const;

function place(v: number, grid: number): number {
  return PAD + (v / grid) * (SIZE - 2 * PAD);
}

export function LatentMap({
  stories,
  facts,
}: {
  stories: LatentStory[];
  facts: LatentFacts;
}) {
  if (stories.length < 2) return null;

  const centres = stories.map((s) => {
    const n = s.points.length || 1;
    const x = s.points.reduce((t, p) => t + p[0], 0) / n;
    const y = s.points.reduce((t, p) => t + p[1], 0) / n;
    return { x: place(x, facts.grid), y: place(y, facts.grid) };
  });

  return (
    <Card className="lm-card">
      <CardHeader>
        <CardTitle>Where the five sit, in the space that grouped them</CardTitle>
        <p className="lm-sub">
          Each dot is one article, placed by the meaning of its headline rather than by
          where or when it was published. Distance is similarity: articles telling the
          same story fall together, and that is exactly what the engine grouped on.
        </p>
      </CardHeader>
      <CardContent>
        <figure className="lm-figure">
          <svg
            className="lm-svg"
            viewBox={`0 0 ${SIZE} ${SIZE}`}
            role="img"
            aria-label={
              `The ${stories.length} featured stories projected onto a plane. ` +
              stories
                .map((s) => `Group ${s.rank}, ${s.actor}, ${s.articles} articles`)
                .join(". ") +
              `. ${Math.round(facts.agreement * 100)} per cent of plotted points have ` +
              `their nearest neighbour inside their own story.`
            }
          >
            {stories.map((story, i) => (
              <path
                key={story.rank}
                className={`lm-dots ${RAMP[i % RAMP.length]}`}
                strokeLinecap="round"
                strokeWidth={DOT * 2}
                fill="none"
                d={story.points
                  .map(
                    ([x, y]) =>
                      `M${place(x, facts.grid).toFixed(1)} ${place(
                        y,
                        facts.grid,
                      ).toFixed(1)}h0`,
                  )
                  .join("")}
              />
            ))}
            {stories.map((story, i) => (
              <g key={`n${story.rank}`} className="lm-tag" aria-hidden="true">
                <circle cx={centres[i].x} cy={centres[i].y} r={9} />
                <text x={centres[i].x} y={centres[i].y} dy="0.34em">
                  {story.rank}
                </text>
              </g>
            ))}
          </svg>
          <figcaption className="lm-caption">
            The plane carries <b>{Math.round(facts.retained * 100)}%</b> of what
            separates these five in the full space, and{" "}
            <b>{Math.round(facts.agreement * 100)}%</b> of the dots have their nearest
            neighbour inside their own group. So most of what looks close here is close,
            and the axes themselves mean nothing: only the grouping does.
          </figcaption>
        </figure>

        <ol className="lm-key">
          {stories.map((story, i) => (
            <li key={story.rank}>
              <span className={`lm-swatch ${RAMP[i % RAMP.length]}`} aria-hidden="true">
                {story.rank}
              </span>
              <span className="lm-name">{story.headline}</span>
              <span className="lm-n">
                {story.shown < story.articles ? (
                  <>
                    {story.shown} of {story.articles.toLocaleString("en-US")} drawn
                  </>
                ) : (
                  <>{story.articles.toLocaleString("en-US")} articles</>
                )}
              </span>
            </li>
          ))}
        </ol>

        {facts.plotted < facts.articles ? (
          <p className="lm-note">
            {facts.plotted.toLocaleString("en-US")} of{" "}
            {facts.articles.toLocaleString("en-US")} articles are drawn. A long story is
            sampled evenly through its own order rather than truncated, so the shape is
            the story&rsquo;s and not its first hundred sources.
          </p>
        ) : null}
      </CardContent>
    </Card>
  );
}
