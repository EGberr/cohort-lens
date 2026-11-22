import type { Metadata } from "next";
import { Geist, Geist_Mono, Instrument_Serif } from "next/font/google";
import { Suspense } from "react";
import { Footer, TopNav } from "@/components/topnav";
import { LangProvider } from "@/lib/i18n";
import "./globals.css";

const geistSans = Geist({ variable: "--font-geist-sans", subsets: ["latin"] });
const geistMono = Geist_Mono({ variable: "--font-geist-mono", subsets: ["latin"] });
const serif = Instrument_Serif({ variable: "--font-serif", subsets: ["latin"], weight: "400", style: ["normal", "italic"] });

export const metadata: Metadata = {
  title: "Zentrend — Gen Z consumer intelligence",
  description: "Browse what Gen Z buys across 52 categories and ask the studies: an agentic RAG analyst grounded in research reports and a survey panel.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" className={`${geistSans.variable} ${geistMono.variable} ${serif.variable} h-full antialiased`}>
      <body className="flex min-h-full flex-col bg-bg text-ink">
        <LangProvider>
          <Suspense fallback={<div className="h-16 border-b hairline" />}>
            <TopNav />
          </Suspense>
          <main className="min-w-0 flex-1">{children}</main>
          <Footer />
        </LangProvider>
      </body>
    </html>
  );
}
