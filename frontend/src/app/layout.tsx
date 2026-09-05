import type { Metadata } from "next";
import { Geist } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "tensionr — who is telling it differently",
  description:
    "tensionr does not measure the world's tension. It measures the disagreement " +
    "between those who narrate it.",
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
