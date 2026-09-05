import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
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
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      {/*
        No `font-size` on the body, here or in globals.css: the reader's text size has
        to get through. See docs/adr/0001.
      */}
      <body className="min-h-full flex flex-col">{children}</body>
    </html>
  );
}
