import Link from "next/link";

import { PasteHero } from "@/components/PasteHero";

export default function Home() {
  return (
    <main className="min-h-screen bg-[#0a0a0a] text-[#f5f5f5]">
      <nav className="mx-auto flex max-w-6xl items-center justify-between border-b border-[#262626] px-5 py-5 font-mono">
        <Link href="/" className="text-sm font-bold tracking-normal">
          TRENCHCOAT
        </Link>
        <Link href="/trending" className="text-sm text-[#737373]">
          TRENDING
        </Link>
      </nav>

      <section className="mx-auto flex min-h-[calc(100vh-73px)] max-w-6xl flex-col justify-center px-5 py-20">
        <div className="max-w-5xl">
          <h1 className="font-mono text-5xl font-bold leading-none tracking-normal text-[#f5f5f5] sm:text-7xl lg:text-8xl">
            TRENCHCOAT
          </h1>
          <p className="mt-6 max-w-2xl font-mono text-lg leading-7 text-[#737373] sm:text-xl">
            Paste a token. Know who&apos;s behind it before you lose your money.
          </p>
          <div className="mt-10">
            <PasteHero />
          </div>
        </div>
      </section>

      <section className="border-t border-[#262626] px-5 py-16">
        <div className="mx-auto max-w-6xl">
          <h2 className="font-mono text-sm font-bold text-[#737373]">
            HOW IT WORKS
          </h2>
          <div className="mt-6 grid gap-4 md:grid-cols-3">
            {[
              [
                "DEV BACKGROUND CHECK",
                "Known deployer history, prior tokens, and outcomes get pulled into one file.",
              ],
              [
                "BUNDLE DETECTION",
                "Launch-window buyers are grouped and measured against supply.",
              ],
              [
                "AI VERDICT",
                "Signals are compressed into one hard sentence. No perfume.",
              ],
            ].map(([title, copy]) => (
              <article
                key={title}
                className="rounded border border-[#262626] bg-[#171717] p-5"
              >
                <h3 className="font-mono text-base font-bold text-[#f5f5f5]">
                  {title}
                </h3>
                <p className="mt-4 font-mono text-sm leading-6 text-[#737373]">
                  {copy}
                </p>
              </article>
            ))}
          </div>
        </div>
      </section>

      <footer className="border-t border-[#262626] px-5 py-6">
        <div className="mx-auto max-w-6xl font-mono text-sm text-[#737373]">
          Built with Birdeye Data. Not financial advice.
        </div>
      </footer>
    </main>
  );
}
