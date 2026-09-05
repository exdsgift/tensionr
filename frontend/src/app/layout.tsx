import type { Metadata } from "next";
import { Geist } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

/**
 * Anything published under `staging/` or `preview/` is not production and must not be
 * indexed. `robots.txt` already disallows crawling both, but a disallowed URL can still
 * be indexed without being fetched — a link from anywhere is enough — and a search
 * result pointing at a sandbox is worse than one pointing nowhere. This says it in the
 * document itself, where a crawler that has the page cannot miss it.
 */
const basePath = process.env.PAGES_BASE_PATH ?? "";
const isProduction = !/\/(staging|preview)(\/|$)/.test(basePath);

export const metadata: Metadata = {
  title: "tensionr — who is telling it differently",
  description:
    "tensionr does not measure the world's tension. It measures the disagreement " +
    "between those who narrate it.",
  robots: isProduction ? undefined : { index: false, follow: false },
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} h-full antialiased`}
    >
      {/*
        No `font-size` on the body, here or in globals.css: the reader's text size has
        to get through. See docs/adr/0001.
      */}
      <body className="min-h-full flex flex-col">
        {/*
          Applies a stored theme choice before the first paint. Without it a reader who
          has chosen light on a dark machine sees a dark frame first, and the flash is
          worst on the slowest devices. It runs ahead of React on purpose; the toggle
          component only handles clicks.

          Absent or unreadable storage means no class, which means the page follows
          `prefers-color-scheme` - the same thing it does with scripting off entirely.
        */}
        <script
          dangerouslySetInnerHTML={{
            __html:
              "try{var t=localStorage.getItem('tensionr-theme');" +
              "if(t==='light'||t==='dark')document.documentElement.classList.add(t)}catch(e){}",
          }}
        />
        {/*
          Without scripting, Base UI never removes the `hidden` attribute from a
          collapsed panel, so the five stories would be in the markup and invisible.
          `hiddenUntilFound` puts them in the HTML; this is what makes them readable.

          It must be inside `@layer base`. Tailwind's preflight ships
          `[hidden]:where(:not([hidden=until-found])){display:none!important}` in that
          layer, and because `!important` reverses layer order, an *unlayered*
          `!important` override ranks lowest and silently loses.
        */}
        <noscript>
          <style>{`
            @layer base {
              [data-slot="accordion-content"][hidden],
              [data-slot="collapsible-content"][hidden] {
                display: block !important;
                content-visibility: visible !important;
                height: auto !important;
              }
            }
          `}</style>
        </noscript>
        {children}
      </body>
    </html>
  );
}
