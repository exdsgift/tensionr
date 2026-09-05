/**
 * Whether a story's split runs along the country of publication, and the table it
 * rests on.
 *
 * This is the answer to "the figures are banal". `division` says how evenly the sources
 * split; it peaks at one half, which is exactly what a coin gives, so it cannot tell a
 * story whose sources divide *by country* from one whose sources divide at random. On
 * the live run, the story at the top of the page scored 0.989 and tested at p = 0.62:
 * a coin flip, ranked first.
 *
 * The table is the point, not the p-value. "Outlets in these countries named it, those
 * did not" is a finding a reader can check row by row against the evidence below it. A
 * p-value is a statistic nobody can check.
 *
 * THIN CELLS ARE POOLED, NOT PRINTED
 *
 * Sorted by rate, the real tables open with `Australia 2/2` and close with
 * `Uruguay 0/1`. Those are noise wearing a percentage: with two sources every rate is
 * 0%, 50% or 100%. Countries with fewer than three evaluable sources are therefore
 * summed into one stated line rather than listed, because dropping them would hide part
 * of the sample and printing them would invite the reader to lean on them.
 *
 * AND A FAILED TEST IS NOT A FINDING
 *
 * Power is the binding limit: at twenty sources across six countries an 80/20 split is
 * detected 44% of the time. So "not distinguishable from chance" never means "the
 * sources agreed", it means "we could not tell", and where the test was underpowered
 * the component says that instead.
 */

import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

export interface Structure {
  sources: number;
  polities: number;
  p: number;
  floor: number;
  powered: boolean;
  by_polity: {
    polity: string;
    named: number;
    evaluable: number;
    thin: boolean;
  }[];
}

/** Below this a rate is not a rate. Matches the engine's own `thin` flag. */
const MIN_SOURCES = 3;

function verdict(s: Structure) {
  if (s.p <= 0.05) {
    return {
      label: "Splits by country",
      tone: "found" as const,
      say:
        `Which sources named it is not random: the split follows where they publish ` +
        `(p ${s.p <= s.floor ? `< ${s.floor}` : `= ${s.p}`}, ${s.sources} sources in ` +
        `${s.polities} countries).`,
    };
  }
  if (!s.powered) {
    return {
      label: "Too few to tell",
      tone: "unknown" as const,
      say:
        `${s.sources} sources across ${s.polities} countries is not enough to tell a ` +
        `country split from chance, so this says nothing either way. It is not a ` +
        `finding that the sources agreed.`,
    };
  }
  return {
    label: "No country pattern",
    tone: "none" as const,
    say:
      `The sources are divided, but not by where they publish: shuffling the countries ` +
      `reproduces this split about as often as not (p = ${s.p}, ${s.sources} sources ` +
      `in ${s.polities} countries).`,
  };
}

export function ByCountry({
  structure,
  actor,
}: {
  structure: Structure;
  actor: string;
}) {
  const v = verdict(structure);
  const shown = structure.by_polity.filter(
    (r) => r.evaluable >= MIN_SOURCES,
  );
  const thin = structure.by_polity.filter((r) => r.evaluable < MIN_SOURCES);
  const thinNamed = thin.reduce((n, r) => n + r.named, 0);
  const thinTotal = thin.reduce((n, r) => n + r.evaluable, 0);

  return (
    <section className="bycountry">
      <h3>
        Does it split by country?
        <Badge variant={v.tone === "found" ? "default" : "outline"}>{v.label}</Badge>
      </h3>
      <p className="bycountry-say">{v.say}</p>

      {shown.length ? (
        <Table
          className="bycountry-table"
          containerProps={{ className: "bycountry-scroll" }}
        >
          <caption className="vh">
            Countries with at least {MIN_SOURCES} sources, and how many named {actor}
          </caption>
          <TableHeader>
            <TableRow>
              <TableHead scope="col">Country</TableHead>
              <TableHead scope="col">Named {actor}</TableHead>
              <TableHead scope="col" className="bycountry-barhead">
                <span className="vh">share</span>
              </TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {shown.map((r) => {
              const rate = r.named / r.evaluable;
              return (
                <TableRow key={r.polity}>
                  <TableCell className="bycountry-name">{r.polity}</TableCell>
                  <TableCell className="bycountry-n">
                    <b>{r.named}</b> of {r.evaluable}
                  </TableCell>
                  <TableCell>
                    <span className="bycountry-bar" aria-hidden="true">
                      <i style={{ width: `${rate * 100}%` }} />
                    </span>
                    <span className="bycountry-pct">{Math.round(rate * 100)}%</span>
                  </TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      ) : null}

      {thin.length ? (
        <p className="bycountry-thin">
          {thin.length} further {thin.length === 1 ? "country" : "countries"} had fewer
          than {MIN_SOURCES} sources each and are summed rather than listed:{" "}
          <b>{thinNamed}</b> of <b>{thinTotal}</b> named {actor}. With one or two
          sources a rate is only ever 0, 50 or 100 per cent.
        </p>
      ) : null}
    </section>
  );
}
