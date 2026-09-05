/**
 * The world, drawn in braille, with a marker for every polity that carried the story.
 *
 * A server component: the coastline and the markers are computed at build time and
 * arrive as HTML. Both rasterisations are in the document and a media query picks
 * between them, so the choice survives with scripting off.
 *
 * The only JavaScript on this page lives at the bottom of this file, and it is
 * deliberately not React. It measures the DOM and positions elements in pixels —
 * imperative work React has an escape hatch for rather than an answer to — and it is
 * already debugged against real font behaviour. Shipping it as a plain <script> costs
 * about a kilobyte; making it an island would cost ~45 kB of React to move dots that
 * move today in 74 lines.
 *
 * It must run *after* hydration, which is why it goes through next/script rather than a
 * bare <script> tag. A bare tag executes at parse time, appends the markers, and React
 * then hydrates, finds children in `.layer` that were not in the server HTML, reports a
 * mismatch (#418) and re-renders the subtree — deleting every marker it just made. The
 * symptom is a map with no dots and no error anyone would connect to it. `.layer` also
 * carries suppressHydrationWarning, so React tolerates the markers arriving into a node
 * it rendered empty.
 */

import Script from "next/script";

import type { Marker } from "@/lib/map";
import type { Coastline } from "@/lib/stories";

interface MapData {
  w: number;
  h: number;
  panel: Marker[];
}

export interface BrailleMapProps {
  wide: Coastline;
  narrow: Coastline;
  wideMarkers: Marker[];
  narrowMarkers: Marker[];
  legend: { named: string; silent: string; plotted: string } | null;
}

export function BrailleMap({
  wide,
  narrow,
  wideMarkers,
  narrowMarkers,
  legend,
}: BrailleMapProps) {
  // Each map carries its own column count and its own markers, both derived from that
  // map's own projection fields. The page never restates a projection.
  const maps: Record<string, MapData> = {
    wide: { w: wide.width, h: wide.height, panel: wideMarkers },
    narrow: { w: narrow.width, h: narrow.height, panel: narrowMarkers },
  };

  return (
    <div className="globe">
      <div className="earth wide" data-map="wide" data-cap="11">
        {/* The coastline is decoration for a screen reader: it carries no information
            the legend and the markers do not state in words. */}
        <pre aria-hidden="true">{wide.rows.join("\n")}</pre>
        <div className="layer" suppressHydrationWarning />
      </div>
      <div className="earth narrow" data-map="narrow" data-cap="14">
        <pre aria-hidden="true">{narrow.rows.join("\n")}</pre>
        <div className="layer" suppressHydrationWarning />
      </div>

      {legend ? (
        <div className="cap">
          <span>
            <span className="mark-on">●</span> {legend.named}
          </span>
          <span>
            <span className="mark-off">○</span> {legend.silent}
          </span>
          <span className="dim">pulse = signal received</span>
          <span className="dim">{legend.plotted}</span>
          <span className="dim">tap or hover a point</span>
        </div>
      ) : (
        <div className="cap">
          <span className="dim">no polities plotted, no story carries a figure</span>
        </div>
      )}

      {/* Clipped, not merely hidden. The probe carries 100 characters at 100px, so left
          in the flow it is ~6,836px wide and, absolutely positioned with no clipping
          ancestor, it made the whole document scroll sideways by that much at every
          viewport width. `visibility: hidden` does not remove a box from layout. */}
      <div id="probebox" aria-hidden="true">
        <span id="probe" />
      </div>

      <Script
        id="braille-markers"
        strategy="afterInteractive"
        dangerouslySetInnerHTML={{
          __html: PLACEMENT.replace("__MAPS__", JSON.stringify(maps)),
        }}
      />
    </div>
  );
}

/**
 * Marker placement. Plain DOM, no framework.
 *
 * The map is drawn in braille (U+28xx), and no monospace face on any platform tested
 * covers that block, so the glyphs always come from a fallback whose advance is NOT the
 * width of "0" — measured at 1.11x it in Safari and 1.14x in Chrome. `ch` is therefore
 * the wrong unit for both sizing and placement. Probe with the real characters, then
 * place every marker in pixels measured off the rendered block.
 */
const PLACEMENT = /* js */ `(function(){
  var MAPS = __MAPS__;
  var probe = document.getElementById('probe');
  if (!probe) return;
  probe.textContent = '\\u283F'.repeat(100);
  probe.style.fontSize = '100px';

  var maps = [].slice.call(document.querySelectorAll('.earth')).map(function(earth){
    var m = MAPS[earth.dataset.map], layer = earth.querySelector('.layer');
    var blips = m.panel.map(function(p, i){
      var d = document.createElement('span');
      d.className = 'blip' + (p.on ? '' : ' off');
      d.dataset.n = p.n;
      d.tabIndex = 0;
      d.setAttribute('aria-label', p.n + (p.on ? ', reporting' : ', silent'));
      d.innerHTML = '<span class="dot"></span><span class="r"></span><span class="r"></span>';
      [].forEach.call(d.querySelectorAll('.r'), function(r, k){
        r.style.animationDelay = (i * 0.31 + k * 1.5) + 's';
      });
      layer.appendChild(d);
      return d;
    });
    return { earth: earth, layer: layer, blips: blips,
             pre: earth.querySelector('pre'), cap: +earth.dataset.cap,
             w: m.w, h: m.h, panel: m.panel };
  });

  function layout(){
    // braille advance per 1px of font-size, in the face the page will actually use
    var per = probe.getBoundingClientRect().width / 100 / 100;
    if (!per) return;
    maps.forEach(function(m){
      if (!m.earth.clientWidth) return;             // the one the media query hid
      // Each map declares its own ceiling. The narrow one is allowed 14px rather than
      // 11 because it can fill a phone column at that size. The ceilings are also what
      // makes the map respond to page zoom, so do not remove them: a size derived from
      // the container's width in CSS pixels is zoom-resistant the way vw is, and it is
      // the ceiling governing over most of the range that makes the dot grow instead.
      m.pre.style.fontSize =
        Math.max(4, Math.min(m.cap, m.earth.clientWidth / (m.w * per))) + 'px';
      var g = m.pre.getBoundingClientRect(), e = m.layer.getBoundingClientRect();
      var cw = g.width / m.w, rh = g.height / m.h;  // measured, not assumed
      var dx = g.left - e.left, dy = g.top - e.top; // the block's offset in its box
      m.blips.forEach(function(d, i){
        var p = m.panel[i];
        d.style.left = (dx + p.c * cw) + 'px';
        d.style.top = (dy + p.r * rh) + 'px';
        d.style.width = Math.max(4, cw * 1.6) + 'px';
        d.style.height = Math.max(4, rh) + 'px';
        d.classList.toggle('flip', p.c > m.w / 2); // label inward, never off the map
      });
      m.layer.style.setProperty('--cw', cw + 'px');
    });
  }

  layout();
  if (window.ResizeObserver) {
    var ro = new ResizeObserver(layout);
    maps.forEach(function(m){ ro.observe(m.earth); });
  }
  addEventListener('load', layout);
  if (document.fonts) document.fonts.ready.then(layout);
})();`;
