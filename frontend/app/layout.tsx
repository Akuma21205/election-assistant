import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { TranslationProvider } from "@/lib/TranslationContext";
import ErrorBoundary from "./components/ErrorBoundary";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-sans",
  display: "swap",
});

export const metadata: Metadata = {
  title: "VoteGuide — Your AI Election Assistant",
  description:
    "Get clear, unbiased answers about voting, elections, and civic processes. Non-partisan AI assistant covering India, USA, and UK elections. Available in 9 languages with voice support.",
  keywords: [
    "election",
    "voting",
    "civic",
    "democracy",
    "voter guide",
    "AI assistant",
    "voter registration",
    "election timeline",
    "voting eligibility",
  ],
  openGraph: {
    title: "VoteGuide — AI Election Assistant",
    description:
      "Non-partisan AI guide for everything elections — registration, eligibility, timelines, and more. 9 languages, voice I/O, and real-time Gemini-powered answers.",
    type: "website",
    siteName: "VoteGuide",
  },
  twitter: {
    card: "summary_large_image",
    title: "VoteGuide — AI Election Assistant",
    description:
      "Non-partisan AI guide for everything elections. Multilingual, voice-enabled, and fully accessible.",
  },
  robots: {
    index: true,
    follow: true,
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={inter.variable}>
      <head>
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <meta name="theme-color" content="#09090f" />
        <link rel="icon" href="/favicon.ico" sizes="any" />
      </head>
      <body
        style={{
          minHeight: "100vh",
          display: "flex",
          flexDirection: "column",
          margin: 0,
        }}
      >
        <ErrorBoundary>
          <TranslationProvider>
            <a
              href="#main-content"
              style={{
                position: "absolute",
                left: "-9999px",
                top: "auto",
                width: "1px",
                height: "1px",
                overflow: "hidden",
              }}
              onFocus={(e) => {
                e.currentTarget.style.position = "fixed";
                e.currentTarget.style.top = "8px";
                e.currentTarget.style.left = "8px";
                e.currentTarget.style.width = "auto";
                e.currentTarget.style.height = "auto";
                e.currentTarget.style.padding = "8px 16px";
                e.currentTarget.style.background = "#6366f1";
                e.currentTarget.style.color = "white";
                e.currentTarget.style.borderRadius = "8px";
                e.currentTarget.style.zIndex = "9999";
                e.currentTarget.style.fontSize = "14px";
                e.currentTarget.style.textDecoration = "none";
                e.currentTarget.style.overflow = "visible";
              }}
              onBlur={(e) => {
                e.currentTarget.style.position = "absolute";
                e.currentTarget.style.left = "-9999px";
                e.currentTarget.style.width = "1px";
                e.currentTarget.style.height = "1px";
                e.currentTarget.style.overflow = "hidden";
              }}
            >
              Skip to main content
            </a>
            {children}
          </TranslationProvider>
        </ErrorBoundary>
      </body>
    </html>
  );
}
