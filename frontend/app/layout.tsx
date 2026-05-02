import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-sans",
  display: "swap",
});

export const metadata: Metadata = {
  title: "VoteGuide — Your AI Election Assistant",
  description:
    "Get clear, unbiased answers about voting, elections, and civic processes. Powered by AI.",
  keywords: ["election", "voting", "civic", "democracy", "voter guide", "AI assistant"],
  openGraph: {
    title: "VoteGuide — AI Election Assistant",
    description: "Non-partisan AI guide for everything elections.",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={inter.variable}>
      <body className="min-h-screen flex flex-col">{children}</body>
    </html>
  );
}
