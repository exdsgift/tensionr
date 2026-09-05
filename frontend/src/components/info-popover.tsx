/**
 * A definition, behind an `i` next to the thing it defines.
 *
 * The browser's own popover, not shadcn's. A React popover renders into a portal, and
 * portals only attach client-side, so its text is never in the exported HTML — which
 * would put four definitions of the page's core vocabulary out of reach of a crawler,
 * a reader-mode extraction and anyone with scripting off. The native attribute is a
 * server component: zero JavaScript, text in the markup, and the top layer, focus
 * trapping and light-dismiss all come from the browser.
 *
 * The cost is CSS anchor positioning, which Firefox still only partly supports. Where
 * it is missing the popover centres in the viewport instead of sitting under its
 * button — degraded, still readable, still dismissible.
 */

import type { ReactNode } from "react";

export function InfoPopover({
  id,
  label,
  title,
  children,
}: {
  id: string;
  /** What the button means, for a screen reader. The visible glyph is just "i". */
  label: string;
  title: string;
  children: ReactNode;
}) {
  return (
    <>
      <button
        className="i"
        popoverTarget={id}
        aria-label={label}
        style={{ anchorName: `--${id}` } as React.CSSProperties}
      >
        i
      </button>
      <div
        popover=""
        id={id}
        className="info-pop"
        style={{ positionAnchor: `--${id}` } as React.CSSProperties}
      >
        <h3>{title}</h3>
        {children}
        <button className="close" popoverTarget={id} popoverTargetAction="hide">
          Close
        </button>
      </div>
    </>
  );
}
