"use client";

import Link from "next/link";

import PasteHero from "@/components/PasteHero";

const COLORS = {
  black: "#080808",
  card: "#111111",
  border: "#1e1e1e",
  text: "#f0f0f0",
  muted: "#666666",
  red: "#ef4444",
  yellow: "#eab308",
  green: "#22c55e",
};

const fonts = {
  mono: "var(--font-geist-mono), monospace",
  display: "var(--font-bebas), sans-serif",
  body: "var(--font-dm-sans), sans-serif",
};

const links = {
  live: "https://frontend-one-wheat-14.vercel.app",
  github: "https://github.com/EmmanuelProf/trenchcoat",
  telegram: "https://t.me/Trench_coat_bot",
  api: "https://trenchcoat.onrender.com",
};

export default function Home() {
  function scrollToPaste() {
    document.getElementById("try")?.scrollIntoView({ behavior: "smooth", block: "center" });
  }

  return (
    <main style={{ background: COLORS.black, color: COLORS.text, fontFamily: fonts.body, overflowX: "hidden" }}>
      <div style={noiseStyle} />
      <Nav onTry={scrollToPaste} />
      <Hero onTry={scrollToPaste} />
      <ProblemSection />
      <SolutionSection />
      <HowSection />
      <StackSection />
      <EndpointsSection />
      <DemoSection />
      <TelegramSection />
      <Footer />
      <style dangerouslySetInnerHTML={{ __html: `
        html { scroll-behavior: smooth; }
        body { background: ${COLORS.black}; }
        @keyframes fadeUp {
          from { opacity: 0; transform: translateY(24px); }
          to { opacity: 1; transform: translateY(0); }
        }
        @keyframes fadeLeft {
          from { opacity: 0; transform: translateX(24px) translateY(-50%); }
          to { opacity: 1; transform: translateX(0) translateY(-50%); }
        }
        @media (max-width: 1024px) {
          .hero-card { display: none; }
          .two-col { grid-template-columns: 1fr !important; }
          .three-grid { grid-template-columns: 1fr !important; }
          .metrics-row { grid-template-columns: repeat(2, 1fr) !important; }
          .endpoints-list { grid-template-columns: 1fr !important; }
        }
        @media (max-width: 768px) {
          .nav-links { display: none !important; }
          .hero { padding: 100px 24px 60px !important; }
          .section { padding: 80px 24px !important; }
          .footer { padding: 40px 24px !important; flex-direction: column; gap: 32px; text-align: center; }
          .step { grid-template-columns: 1fr !important; gap: 12px !important; }
          .paste-shell { margin-top: 48px !important; }
        }
      ` }} />
    </main>
  );
}

function Nav({ onTry }: { onTry: () => void }) {
  return (
    <nav
      style={{
        position: "fixed",
        top: 0,
        left: 0,
        right: 0,
        zIndex: 100,
        padding: "20px 48px",
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        borderBottom: `1px solid ${COLORS.border}`,
        background: "rgba(8,8,8,0.95)",
      }}
    >
      <Link href="#" style={{ fontFamily: fonts.display, fontSize: 28, letterSpacing: 4, color: COLORS.text, textDecoration: "none" }}>
        TRENCHCOAT
      </Link>
      <div className="nav-links" style={{ display: "flex", alignItems: "center", gap: 32 }}>
        {[
          ["Problem", "#problem"],
          ["Solution", "#solution"],
          ["How It Works", "#how"],
          ["Stack", "#stack"],
          ["Telegram", "#telegram"],
        ].map(([label, href]) => (
          <a key={label} href={href} style={navLinkStyle}>
            {label}
          </a>
        ))}
        <a href={links.telegram} target="_blank" rel="noreferrer" style={navLinkStyle}>
          TG BOT ↗
        </a>
      </div>
      <button onClick={onTry} style={navCtaStyle}>
        TRY IT LIVE ↗
      </button>
    </nav>
  );
}

function Hero({ onTry }: { onTry: () => void }) {
  return (
    <section className="hero" style={{ minHeight: "100vh", display: "flex", flexDirection: "column", justifyContent: "center", padding: "120px 48px 80px", position: "relative", overflow: "hidden" }}>
      <div style={heroGridStyle} />
      <p style={{ ...eyebrowStyle, animation: "fadeUp 0.6s ease forwards 0.2s" }}>→ Birdeye BIP Sprint 3 Submission</p>
      <h1 style={{ fontFamily: fonts.display, fontSize: "clamp(80px, 14vw, 200px)", lineHeight: 0.9, letterSpacing: 8, color: COLORS.text, marginBottom: 32, opacity: 0, animation: "fadeUp 0.6s ease forwards 0.4s" }}>
        TRENCH<span style={{ color: COLORS.red }}>COAT</span>
      </h1>
      <p style={{ fontFamily: fonts.mono, fontSize: 15, color: COLORS.muted, lineHeight: 1.8, maxWidth: 520, marginBottom: 48, opacity: 0, animation: "fadeUp 0.6s ease forwards 0.6s" }}>
        Every degen has a rug story. The dev&apos;s history was on-chain the whole time. Nobody was looking.
        <br />
        <br />
        TRENCHCOAT looks.
      </p>
      <div style={{ display: "flex", gap: 16, flexWrap: "wrap", opacity: 0, animation: "fadeUp 0.6s ease forwards 0.8s" }}>
        <button onClick={onTry} style={primaryButtonStyle}>TRY IT NOW →</button>
        <a href={links.github} target="_blank" rel="noreferrer" style={secondaryButtonStyle}>View on GitHub ↗</a>
        <a href={links.telegram} target="_blank" rel="noreferrer" style={secondaryButtonStyle}>Telegram Bot ↗</a>
      </div>
      <div id="try" className="paste-shell" style={{ marginTop: 80, opacity: 0, animation: "fadeUp 0.6s ease forwards 1s" }}>
        <p style={{ fontFamily: fonts.mono, fontSize: 10, color: COLORS.green, letterSpacing: 3, marginBottom: 14 }}>LIVE SCANNER</p>
        <PasteHero />
      </div>
      <div style={{ position: "absolute", bottom: 40, left: 48, fontFamily: fonts.mono, fontSize: 10, color: COLORS.muted, letterSpacing: 3 }}>
        SCROLL TO EXPLORE
      </div>
      <HeroCard />
    </section>
  );
}

function HeroCard() {
  return (
    <div className="hero-card" style={{ position: "absolute", right: 48, top: "50%", transform: "translateY(-50%)", width: 340, background: COLORS.card, border: `1px solid ${COLORS.border}`, padding: 24, opacity: 0, animation: "fadeLeft 0.8s ease forwards 1s" }}>
      <div style={cardLabelStyle}>RAP SHEET — LIVE EXAMPLE</div>
      <div style={{ fontFamily: fonts.mono, fontSize: 20, color: COLORS.text, marginBottom: 4 }}>$SCAMTOKEN</div>
      <div style={{ fontFamily: fonts.display, fontSize: 72, color: COLORS.red, lineHeight: 1, marginBottom: 8 }}>18</div>
      <div style={{ display: "inline-block", fontFamily: fonts.mono, fontSize: 10, background: COLORS.red, color: "white", padding: "4px 12px", letterSpacing: 2, marginBottom: 16 }}>AVOID</div>
      <div style={{ fontFamily: fonts.display, fontSize: 48, color: COLORS.red, letterSpacing: 4, marginBottom: 16 }}>DUMP</div>
      <Divider />
      {[
        ["BUNDLE %", "49.6% BUNDLED"],
        ["TOP 10 HOLDERS", "72%"],
        ["PRIOR RUGS", "4 OF 4"],
      ].map(([label, value]) => (
        <div key={label} style={{ display: "flex", justifyContent: "space-between", marginBottom: 8 }}>
          <span style={tinyMutedStyle}>{label}</span>
          <span style={{ ...tinyMutedStyle, color: COLORS.red }}>{value}</span>
        </div>
      ))}
      <div style={{ fontFamily: fonts.mono, fontSize: 11, color: COLORS.text, fontStyle: "italic", lineHeight: 1.6, borderLeft: `2px solid ${COLORS.red}`, paddingLeft: 12, marginTop: 16 }}>
        &quot;Same wallet shipped four tokens. All four zeros. This makes five.&quot;
      </div>
    </div>
  );
}

function ProblemSection() {
  const tweets = [
    ["Original $Kitty team ran a Pump → Bonk migration scam, lied about allocations, and rugged on Bonk", "Real X post — dev cross-history problem"],
    ["Before I even placed a trade I already felt like I had lost my money because everything is bundled", "Real X post — bundle detection problem"],
    ["i literally lost everything in 3 days... tried to learn for 7 days straight everything they did, i did, still lost everything", "Real X post — information asymmetry"],
    ["This guy launched again under a new ticker and people still aped because nobody checked the wallet.", "Real X post — repeat deployer problem"],
  ];
  return (
    <Section id="problem" label="01 — The Problem" title={<>WE SCRAPED X.<br />HERE&apos;S WHAT<br />DEGENS SAID.</>}>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))", gap: 16, marginBottom: 80 }}>
        {tweets.map(([text, meta]) => (
          <article key={text} style={{ background: COLORS.card, border: `1px solid ${COLORS.border}`, padding: 24, position: "relative" }}>
            <p style={{ fontFamily: fonts.mono, fontSize: 12, color: COLORS.text, lineHeight: 1.8, marginBottom: 16 }}>{text}</p>
            <div style={{ fontFamily: fonts.mono, fontSize: 10, color: COLORS.muted, display: "flex", alignItems: "center", gap: 8 }}>
              <span style={{ width: 4, height: 4, borderRadius: "50%", background: COLORS.muted }} />
              <span>{meta}</span>
            </div>
          </article>
        ))}
      </div>
      <Metrics />
    </Section>
  );
}

function Metrics() {
  return (
    <div className="metrics-row" style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 1, background: COLORS.border, border: `1px solid ${COLORS.border}`, marginBottom: 80 }}>
      {[
        ["7", "Birdeye endpoints"],
        ["50+", "API calls required"],
        ["3", "Verdict bands"],
        ["1", "Rap sheet"],
      ].map(([value, label]) => (
        <div key={label} style={{ background: COLORS.black, padding: "40px 32px", textAlign: "center" }}>
          <div style={{ fontFamily: fonts.display, fontSize: 56, letterSpacing: 2, marginBottom: 8 }}>{value}</div>
          <div style={tinyMutedStyle}>{label}</div>
        </div>
      ))}
    </div>
  );
}

function SolutionSection() {
  return (
    <Section id="solution" label="02 — The Solution" title={<>A DEV RAP SHEET<br />BEFORE THE BUY.</>}>
      <div className="three-grid" style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 1, background: COLORS.border, border: `1px solid ${COLORS.border}`, marginBottom: 80 }}>
        {[
          ["01", "DEV BACKGROUND CHECK", "Known deployer history, prior tokens, and outcomes get pulled into one file."],
          ["02", "BUNDLE DETECTION", "Launch-window buyers are grouped and measured against supply."],
          ["03", "AI VERDICT", "Signals are compressed into one hard sentence. No perfume."],
        ].map(([num, title, desc]) => (
          <article key={title} style={{ background: COLORS.black, padding: "40px 32px", position: "relative", overflow: "hidden" }}>
            <div style={{ fontFamily: fonts.display, fontSize: 64, color: COLORS.border, lineHeight: 1, marginBottom: 24 }}>{num}</div>
            <h3 style={{ fontFamily: fonts.mono, fontSize: 11, color: COLORS.green, letterSpacing: 3, textTransform: "uppercase", marginBottom: 12 }}>{title}</h3>
            <p style={{ fontFamily: fonts.body, fontSize: 14, color: COLORS.muted, lineHeight: 1.7 }}>{desc}</p>
          </article>
        ))}
      </div>
    </Section>
  );
}

function HowSection() {
  const steps = [
    ["Paste a CA", "User pastes any Solana token address into web or Telegram.", ["Next.js", "Telegram"]],
    ["Pull Birdeye data", "Overview, holders, transactions, security where available, and listings feed power the dossier.", ["Birdeye", "FastAPI"]],
    ["Detect bundles", "First launch-window transactions are grouped to estimate bundled supply.", ["txs/token", "Python"]],
    ["Check the dev", "We derive deployer wallet from earliest transactions and compare against our Supabase history index.", ["Supabase", "Redis"]],
    ["Generate verdict", "Signals become a score, APE/CAUTION/DUMP band, and a tight AI verdict.", ["OpenRouter", "Claude"]],
  ];
  return (
    <Section id="how" label="03 — How It Works" title={<>FROM CONTRACT<br />TO CONFIDENCE.</>}>
      <div style={{ maxWidth: 800 }}>
        {steps.map(([title, desc, badges], index) => (
          <div key={String(title)} className="step" style={{ display: "grid", gridTemplateColumns: "80px 1fr", gap: 32, padding: "40px 0", borderBottom: `1px solid ${COLORS.border}`, opacity: 0, animation: `fadeUp 0.5s ease forwards ${0.1 + index * 0.1}s` }}>
            <div style={{ fontFamily: fonts.display, fontSize: 48, color: COLORS.border, lineHeight: 1, paddingTop: 4 }}>{String(index + 1).padStart(2, "0")}</div>
            <div>
              <h3 style={{ fontFamily: fonts.mono, fontSize: 13, letterSpacing: 2, color: COLORS.text, textTransform: "uppercase", marginBottom: 8 }}>{title}</h3>
              <p style={{ fontFamily: fonts.body, fontSize: 14, color: COLORS.muted, lineHeight: 1.7 }}>{desc}</p>
              <div style={{ marginTop: 8 }}>
                {(badges as string[]).map((badge) => <span key={badge} style={badgeStyle}>{badge}</span>)}
              </div>
            </div>
          </div>
        ))}
      </div>
    </Section>
  );
}

function StackSection() {
  const stack = [
    ["FRONTEND", "Next.js 14", "App Router, TypeScript, Vercel"],
    ["BACKEND", "FastAPI", "Python API, Render deploy"],
    ["DATA", "Birdeye Data", "Real-time onchain token intel"],
    ["CACHE", "Upstash Redis", "Dossier and verdict cache"],
    ["DATABASE", "Supabase", "Deployer history and outcomes"],
    ["AI", "OpenRouter", "Claude Haiku verdict layer"],
    ["BOT", "Telegram Bot API", "Webhook mode inside FastAPI"],
    ["LINKS", "Solscan / RugCheck", "External verification paths"],
  ];
  return (
    <Section id="stack" label="04 — Stack" title={<>BUILT LIKE<br />A REAL PRODUCT.</>}>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: 1, background: COLORS.border, border: `1px solid ${COLORS.border}` }}>
        {stack.map(([layer, name, note]) => (
          <div key={name} style={{ background: COLORS.black, padding: "32px 24px" }}>
            <div style={tinyMutedStyle}>{layer}</div>
            <div style={{ fontFamily: fonts.mono, fontSize: 14, color: COLORS.text, marginBottom: 4 }}>{name}</div>
            <div style={{ fontFamily: fonts.body, fontSize: 12, color: COLORS.muted }}>{note}</div>
          </div>
        ))}
      </div>
    </Section>
  );
}

function EndpointsSection() {
  const endpoints = [
    ["/defi/token_overview", "Symbol, price, market cap, liquidity"],
    ["/defi/token_security", "Mint authority, freeze, top holders where available"],
    ["/defi/v3/token/holder", "Top 20 holders, concentration calc"],
    ["/defi/txs/token", "Transaction history, bundle detection"],
    ["/defi/token_trending", "Live trending feed, mini dossiers"],
    ["/defi/v2/tokens/new_listing", "30-day backfill for dev history index"],
    ["/defi/token_creation_info", "Planned deployer wallet source, fallback is tx-derived"],
  ];
  return (
    <Section id="endpoints" label="04.2 — Birdeye Data" title={<>THE BIRDEYE<br />ENDPOINTS USED.</>}>
      <div className="endpoints-list" style={{ display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: 1, background: COLORS.border, border: `1px solid ${COLORS.border}` }}>
        {endpoints.map(([path, desc]) => (
          <div key={path} style={{ background: COLORS.black, padding: "24px 28px", display: "flex", gap: 16, alignItems: "flex-start" }}>
            <span style={{ fontFamily: fonts.mono, fontSize: 9, color: COLORS.green, background: "rgba(34,197,94,0.1)", padding: "3px 8px", letterSpacing: 1, whiteSpace: "nowrap", marginTop: 2 }}>GET</span>
            <div>
              <div style={{ fontFamily: fonts.mono, fontSize: 12, color: COLORS.text, marginBottom: 4 }}>{path}</div>
              <div style={{ fontFamily: fonts.body, fontSize: 12, color: COLORS.muted }}>{desc}</div>
            </div>
          </div>
        ))}
      </div>
    </Section>
  );
}

function DemoSection() {
  const demos = [
    ["01", "PASTE CA", "Drop any Solana contract address. Hit RUN. Button shows RUNNING... immediately so you know it's working."],
    ["02", "CLEAN TOKEN", "Score 80. APE in green. Token overview, dev wallet, supply stats all visible."],
    ["03", "RISKY TOKEN", "Score 40. CAUTION in yellow. Brand new token, thin liquidity, too early to call."],
    ["04", "ON TELEGRAM", "Same data, straight in Telegram. DM @Trench_coat_bot any CA."],
  ];
  return (
    <Section id="demo" label="04.5 — See It In Action" title={<>PASTE TO<br />VERDICT IN<br />SECONDS.</>}>
      <div style={{ display: "flex", flexDirection: "column", gap: 80, maxWidth: 1000 }}>
        {demos.map(([num, title, desc]) => (
          <div key={num} className="step" style={{ display: "grid", gridTemplateColumns: "120px 1fr", gap: 40, alignItems: "start" }}>
            <div>
              <div style={{ fontFamily: fonts.display, fontSize: 80, color: COLORS.border, lineHeight: 1 }}>{num}</div>
              <div style={{ fontFamily: fonts.mono, fontSize: 10, color: title === "RISKY TOKEN" ? COLORS.yellow : COLORS.green, letterSpacing: 2, marginTop: 8 }}>{title}</div>
            </div>
            <DemoPanel title={title as string} desc={desc as string} />
          </div>
        ))}
      </div>
    </Section>
  );
}

function DemoPanel({ title, desc }: { title: string; desc: string }) {
  return (
    <div>
      <p style={{ fontFamily: fonts.mono, fontSize: 12, color: COLORS.muted, lineHeight: 1.8, marginBottom: 20, letterSpacing: 1 }}>{desc}</p>
      <div style={{ border: `1px solid ${COLORS.border}`, overflow: "hidden" }}>
        <div style={{ background: COLORS.card, padding: "8px 16px", borderBottom: `1px solid ${COLORS.border}` }}>
          <span style={{ fontFamily: fonts.mono, fontSize: 10, color: title === "RISKY TOKEN" ? COLORS.yellow : COLORS.green, letterSpacing: 2 }}>{title} — LIVE FLOW</span>
        </div>
        <div style={{ background: "#0a0a0a", padding: 32 }}>
          {title === "PASTE CA" ? <PasteHero /> : <MiniRapSheet caution={title === "RISKY TOKEN"} telegram={title === "ON TELEGRAM"} />}
        </div>
      </div>
    </div>
  );
}

function MiniRapSheet({ caution, telegram }: { caution?: boolean; telegram?: boolean }) {
  const color = caution ? COLORS.yellow : COLORS.green;
  const band = caution ? "CAUTION" : "CLEAR";
  const score = caution ? "40" : "80";
  const symbol = caution ? "WOJALIEN" : "ALIEN";
  if (telegram) {
    return (
      <div style={{ background: "#1a1a2e", padding: 24, fontFamily: fonts.mono, fontSize: 12 }}>
        <div style={{ display: "flex", justifyContent: "flex-end", marginBottom: 12 }}>
          <div style={{ background: "#1e3a5f", padding: "10px 14px", maxWidth: "80%", color: COLORS.text, fontSize: 11, lineHeight: 1.4, wordBreak: "break-all" }}>6sk8py73jnmwzkrXZ7pHb5bpjHDo1ideFqrfrRAtGbph</div>
        </div>
        <div style={{ background: COLORS.border, padding: 14, maxWidth: "90%", color: COLORS.text, fontSize: 11, lineHeight: 2 }}>
          <span style={{ color: COLORS.green }}>🟢 TRENCHCOAT RAP SHEET</span><br />
          $ALIEN · ALIEN<br /><br />APE · CLEAR<br />████████░░ 80/100<br /><br />
          <span style={{ color: COLORS.muted }}>VERDICT</span><br />
          <em>Mint still live. Top ten own 42%. Bundled launch with 18% concentrated.</em>
        </div>
      </div>
    );
  }
  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 24, paddingBottom: 24, borderBottom: `1px solid ${COLORS.border}` }}>
        <div>
          <div style={tinyMutedStyle}>RAP SHEET</div>
          <div style={{ fontFamily: fonts.mono, fontSize: 28, color: COLORS.text, fontWeight: "bold" }}>${symbol}</div>
          <div style={{ fontFamily: fonts.mono, fontSize: 10, color: COLORS.muted, marginTop: 4 }}>Generated 1 minute ago</div>
        </div>
        <div style={{ textAlign: "right" }}>
          <div style={{ fontFamily: fonts.display, fontSize: 56, color, lineHeight: 1 }}>{score}</div>
          <div style={{ display: "inline-block", background: color, color: "black", fontFamily: fonts.mono, fontSize: 9, padding: "3px 10px", letterSpacing: 2, marginBottom: 6 }}>{band}</div>
          <div style={{ fontFamily: fonts.display, fontSize: 36, color, letterSpacing: 3 }}>{caution ? "CAUTION" : "APE"}</div>
        </div>
      </div>
      <div style={{ fontFamily: fonts.mono, fontSize: 11, color: COLORS.text, fontStyle: "italic", borderLeft: `2px solid ${color}`, paddingLeft: 12, lineHeight: 1.8 }}>
        {caution ? "Brand new. Under a day old. Liquidity thin. Size tiny or skip." : "Clean deployer history. Bundle low. Still memecoin — DYOR."}
      </div>
    </div>
  );
}

function TelegramSection() {
  return (
    <section id="telegram" className="section two-col" style={{ padding: "120px 48px", borderTop: `1px solid ${COLORS.border}`, display: "grid", gridTemplateColumns: "1fr 1fr", gap: 80, alignItems: "center" }}>
      <div>
        <p style={sectionLabelStyle}>05 — Telegram Bot</p>
        <h2 style={{ fontFamily: fonts.display, fontSize: "clamp(40px, 5vw, 72px)", letterSpacing: 4, lineHeight: 1, marginBottom: 24 }}>TRADE FROM<br />TELEGRAM.<br />CHECK FROM<br />TELEGRAM.</h2>
        <p style={{ fontFamily: fonts.body, fontSize: 15, color: COLORS.muted, lineHeight: 1.8, marginBottom: 32 }}>Degens live in Telegram. We built @Trench_coat_bot so you can get a full rap sheet without leaving your trading group. Paste a CA, get the verdict in seconds.</p>
        <a href={links.telegram} target="_blank" rel="noreferrer" style={primaryButtonStyle}>Open @Trench_coat_bot ↗</a>
      </div>
      <div style={{ background: COLORS.card, border: `1px solid ${COLORS.border}`, padding: 24 }}>
        <div style={{ fontFamily: fonts.mono, fontSize: 10, color: COLORS.muted, letterSpacing: 2, marginBottom: 20, paddingBottom: 16, borderBottom: `1px solid ${COLORS.border}` }}>@Trench_coat_bot — LIVE DEMO</div>
        <ChatUser>DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263</ChatUser>
        <ChatBot color={COLORS.green}>🟢 <b>TRENCHCOAT RAP SHEET</b><br />$Bonk · BONK<br /><br />APE · CLEAR<br />██████████ 100/100<br /><br /><span style={{ color: COLORS.muted }}>VERDICT</span><br /><em>Four years old. Deep liquidity. This one&apos;s actually clean.</em></ChatBot>
        <ChatUser>E8syR4zsgQG2zo9YyiyfX4ujubByR4z6qj9stJASpump</ChatUser>
        <ChatBot color={COLORS.red}>🔴 <b>TRENCHCOAT RAP SHEET</b><br />$SCAM · SCAMTOKEN<br /><br />DUMP · AVOID<br />██░░░░░░░░ 18/100<br /><br /><span style={{ color: COLORS.muted }}>CHECKS</span><br />Solscan | RugCheck</ChatBot>
      </div>
    </section>
  );
}

function ChatUser({ children }: { children: React.ReactNode }) {
  return <div style={{ display: "flex", justifyContent: "flex-end", marginBottom: 12 }}><div style={{ background: "#1e3a5f", fontFamily: fonts.mono, fontSize: 11, color: COLORS.text, padding: "10px 14px", maxWidth: "80%", lineHeight: 1.5, wordBreak: "break-all" }}>{children}</div></div>;
}

function ChatBot({ children, color }: { children: React.ReactNode; color: string }) {
  return <div style={{ marginBottom: 12 }}><div style={{ background: COLORS.border, fontFamily: fonts.mono, fontSize: 11, color, padding: "10px 14px", maxWidth: "90%", lineHeight: 1.6 }}>{children}</div></div>;
}

function Footer() {
  return (
    <footer className="footer" style={{ padding: "60px 48px", borderTop: `1px solid ${COLORS.border}`, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
      <div>
        <div style={{ fontFamily: fonts.display, fontSize: 32, letterSpacing: 4, color: COLORS.text }}>TRENCHCOAT</div>
        <div style={{ fontFamily: fonts.mono, fontSize: 11, color: COLORS.muted, letterSpacing: 2, marginTop: 4 }}>Everyone checks the chart. We check the dev.</div>
        <div style={{ fontFamily: fonts.mono, fontSize: 10, color: COLORS.muted, letterSpacing: 1, marginTop: 8 }}>Built with Birdeye Data · Birdeye BIP Sprint 3 · May 2026</div>
      </div>
      <div style={{ display: "flex", gap: 24, flexWrap: "wrap" }}>
        <a href={links.live} target="_blank" rel="noreferrer" style={footerLinkStyle}>Live App ↗</a>
        <a href={links.github} target="_blank" rel="noreferrer" style={footerLinkStyle}>GitHub ↗</a>
        <a href={links.telegram} target="_blank" rel="noreferrer" style={footerLinkStyle}>Telegram ↗</a>
        <a href={links.api} target="_blank" rel="noreferrer" style={footerLinkStyle}>API ↗</a>
      </div>
    </footer>
  );
}

function Section({ id, label, title, children }: { id: string; label: string; title: React.ReactNode; children: React.ReactNode }) {
  return (
    <section id={id} className="section" style={{ padding: "120px 48px", borderTop: `1px solid ${COLORS.border}` }}>
      <p style={sectionLabelStyle}>{label}</p>
      <h2 style={{ fontFamily: fonts.display, fontSize: "clamp(40px, 6vw, 80px)", letterSpacing: 4, lineHeight: 1, marginBottom: 64 }}>{title}</h2>
      {children}
    </section>
  );
}

function Divider() {
  return <div style={{ height: 1, background: COLORS.border, margin: "16px 0" }} />;
}

const noiseStyle: React.CSSProperties = {
  position: "fixed",
  inset: 0,
  backgroundImage: "url(\"data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)' opacity='0.03'/%3E%3C/svg%3E\")",
  pointerEvents: "none",
  zIndex: 9999,
  opacity: 0.4,
};

const heroGridStyle: React.CSSProperties = {
  position: "absolute",
  inset: 0,
  backgroundImage: "linear-gradient(rgba(255,255,255,0.02) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.02) 1px, transparent 1px)",
  backgroundSize: "60px 60px",
  pointerEvents: "none",
};

const navLinkStyle: React.CSSProperties = { fontFamily: fonts.mono, fontSize: 11, color: COLORS.muted, textDecoration: "none", letterSpacing: 2, textTransform: "uppercase" };
const navCtaStyle: React.CSSProperties = { fontFamily: fonts.mono, fontSize: 11, color: COLORS.black, background: COLORS.text, padding: "8px 20px", letterSpacing: 2, border: "none", cursor: "pointer" };
const primaryButtonStyle: React.CSSProperties = { fontFamily: fonts.mono, fontSize: 12, letterSpacing: 2, textTransform: "uppercase", background: COLORS.text, color: COLORS.black, padding: "14px 32px", textDecoration: "none", fontWeight: 700, border: "none", cursor: "pointer", display: "inline-block" };
const secondaryButtonStyle: React.CSSProperties = { fontFamily: fonts.mono, fontSize: 12, letterSpacing: 2, textTransform: "uppercase", background: "transparent", color: COLORS.text, padding: "14px 32px", textDecoration: "none", border: `1px solid ${COLORS.border}`, display: "inline-block" };
const eyebrowStyle: React.CSSProperties = { fontFamily: fonts.mono, fontSize: 11, color: COLORS.green, letterSpacing: 4, textTransform: "uppercase", marginBottom: 24, opacity: 0 };
const sectionLabelStyle: React.CSSProperties = { fontFamily: fonts.mono, fontSize: 10, color: COLORS.muted, letterSpacing: 4, textTransform: "uppercase", marginBottom: 16 };
const cardLabelStyle: React.CSSProperties = { fontFamily: fonts.mono, fontSize: 9, color: COLORS.muted, letterSpacing: 3, marginBottom: 16 };
const tinyMutedStyle: React.CSSProperties = { fontFamily: fonts.mono, fontSize: 10, color: COLORS.muted, letterSpacing: 3, textTransform: "uppercase" };
const badgeStyle: React.CSSProperties = { display: "inline-block", fontFamily: fonts.mono, fontSize: 9, background: COLORS.border, color: COLORS.muted, padding: "3px 8px", letterSpacing: 1, marginTop: 8, marginRight: 4 };
const footerLinkStyle: React.CSSProperties = { fontFamily: fonts.mono, fontSize: 11, color: COLORS.muted, textDecoration: "none", letterSpacing: 2 };
