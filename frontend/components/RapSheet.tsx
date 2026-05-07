"use client";

import { useState } from "react";

import type { Dossier, PriorToken } from "@/lib/api";
import { formatAddress, formatAge, formatNumber, getBandColor } from "@/lib/utils";

type RapSheetProps = {
  dossier: Dossier;
};

export function RapSheet({ dossier }: RapSheetProps) {
  const [copied, setCopied] = useState(false);
  const symbol = dossier.overview?.symbol || "UNKNOWN";
  const wallet = dossier.deployer?.wallet || "unknown";
  const bandColor = getBandColor(dossier.band);
  const priorTokens = dossier.deployer?.prior_tokens || [];
  const bundle = dossier.distribution?.bundle;
  const security = dossier.security;

  async function copyWallet() {
    if (!wallet || wallet === "unknown") {
      return;
    }
    await navigator.clipboard.writeText(wallet);
    setCopied(true);
    window.setTimeout(() => setCopied(false), 1200);
  }

  return (
    <article className="mx-auto max-w-5xl rounded border border-[#262626] bg-[#171717] text-[#f5f5f5]">
      <section className="grid gap-6 border-b border-[#262626] p-5 md:grid-cols-[1fr_auto] md:p-8">
        <div>
          <p className="font-mono text-sm text-[#737373]">RAP SHEET</p>
          <h1 className="mt-2 font-mono text-4xl font-bold tracking-normal md:text-6xl">
            ${symbol}
          </h1>
          <p className="mt-3 font-mono text-xs text-[#737373]">
            Generated {generatedAgo(dossier.generated_at)}
          </p>
        </div>
        <div className="flex items-end gap-4 md:items-center">
          <div className="font-mono text-6xl font-bold" style={{ color: bandColor }}>
            {dossier.score}
          </div>
          <span
            className="rounded px-3 py-1 font-mono text-sm font-bold text-[#f5f5f5]"
            style={{ backgroundColor: bandColor }}
          >
            {dossier.band}
          </span>
        </div>
      </section>

      <Section label="THE DEV">
        <button
          type="button"
          onClick={copyWallet}
          className="rounded border border-[#262626] bg-[#0a0a0a] px-3 py-2 text-left font-mono text-sm text-[#f5f5f5]"
        >
          {formatAddress(wallet)}
          <span className="ml-3 text-[#737373]">{copied ? "COPIED" : "COPY"}</span>
        </button>
        <div className="mt-5 space-y-2">
          {priorTokens.length ? (
            priorTokens.map((token) => <PriorRow key={token.ca} token={token} />)
          ) : (
            <p className="font-mono text-sm text-[#737373]">NO PRIOR TOKENS FOUND</p>
          )}
        </div>
      </Section>

      <Section label="SUPPLY">
        <div className="grid gap-3 md:grid-cols-3">
          <Metric
            label="BUNDLE"
            value={`${fixed(bundle?.bundle_pct)}%`}
            detail={bundle?.bundled ? "BUNDLED" : "CLEAN"}
            detailColor={bundle?.bundled ? "#ef4444" : "#22c55e"}
          />
          <Metric
            label="TOP 10"
            value={dossier.distribution?.top10_pct == null ? "N/A" : `${fixed(dossier.distribution.top10_pct)}%`}
          />
          <Metric
            label="SUSPECT WALLETS"
            value={String(bundle?.suspect_wallet_count ?? 0)}
          />
        </div>
      </Section>

      <Section label="SECURITY">
        {security?.mint_revoked == null && security?.freeze_revoked == null ? (
          <p className="font-mono text-sm text-[#737373]">SECURITY DATA UNAVAILABLE</p>
        ) : (
          <div className="grid gap-3 md:grid-cols-3">
            <SecurityStatus label="MINT" value={security?.mint_revoked} />
            <SecurityStatus label="FREEZE" value={security?.freeze_revoked} />
            <Metric
              label="LIQUIDITY"
              value={dossier.overview?.liquidity == null ? "N/A" : formatNumber(dossier.overview.liquidity)}
            />
          </div>
        )}
      </Section>

      <Section label="VERDICT">
        <blockquote
          className="border-l-2 pl-5 font-mono text-xl italic leading-8 text-[#f5f5f5]"
          style={{ borderColor: bandColor }}
        >
          {dossier.verdict}
        </blockquote>
      </Section>
    </article>
  );
}

function Section({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <section className="border-b border-[#262626] p-5 last:border-b-0 md:p-8">
      <p className="mb-4 font-mono text-xs font-bold text-[#737373]">{label}</p>
      {children}
    </section>
  );
}

function PriorRow({ token }: { token: PriorToken }) {
  return (
    <div className="grid gap-3 rounded border border-[#262626] bg-[#0a0a0a] p-3 font-mono text-sm md:grid-cols-[1fr_auto_auto]">
      <span>{token.symbol || formatAddress(token.ca)}</span>
      <span
        className="rounded px-2 py-0.5 text-xs text-[#f5f5f5]"
        style={{ backgroundColor: outcomeColor(token.outcome) }}
      >
        {token.outcome.toUpperCase()}
      </span>
      <span className="text-[#737373]">
        {token.age_days == null ? "AGE N/A" : formatAge(token.age_days)}
      </span>
    </div>
  );
}

function Metric({
  label,
  value,
  detail,
  detailColor,
}: {
  label: string;
  value: string;
  detail?: string;
  detailColor?: string;
}) {
  return (
    <div className="rounded border border-[#262626] bg-[#0a0a0a] p-4">
      <p className="font-mono text-xs text-[#737373]">{label}</p>
      <p className="mt-2 font-mono text-2xl font-bold">{value}</p>
      {detail ? (
        <p className="mt-2 font-mono text-xs font-bold" style={{ color: detailColor }}>
          {detail}
        </p>
      ) : null}
    </div>
  );
}

function SecurityStatus({ label, value }: { label: string; value: boolean | null | undefined }) {
  const text = value == null ? "UNKNOWN" : value ? "REVOKED" : "NOT REVOKED";
  const color = value == null ? "#737373" : value ? "#22c55e" : "#ef4444";
  return (
    <div className="rounded border border-[#262626] bg-[#0a0a0a] p-4">
      <p className="font-mono text-xs text-[#737373]">{label}</p>
      <p className="mt-2 font-mono text-sm font-bold" style={{ color }}>
        {text}
      </p>
    </div>
  );
}

function fixed(value: number | null | undefined) {
  if (value == null) {
    return "0";
  }
  return value.toFixed(1).replace(/\.0$/, "");
}

function generatedAgo(value: string) {
  const diff = Math.max(0, Date.now() - new Date(value).getTime());
  const minutes = Math.max(1, Math.round(diff / 60_000));
  return `${minutes} ${minutes === 1 ? "minute" : "minutes"} ago`;
}

function outcomeColor(outcome: string) {
  if (outcome === "rugged") {
    return "#ef4444";
  }
  if (outcome === "abandoned") {
    return "#eab308";
  }
  if (outcome === "alive") {
    return "#22c55e";
  }
  return "#737373";
}
