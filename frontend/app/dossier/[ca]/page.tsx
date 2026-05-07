import type { Metadata } from "next";

import { RapSheet } from "@/components/RapSheet";
import { getDossier } from "@/lib/api";

type DossierPageProps = {
  params: {
    ca: string;
  };
  searchParams: {
    chain?: string;
  };
};

export async function generateMetadata({
  params,
  searchParams,
}: DossierPageProps): Promise<Metadata> {
  try {
    const dossier = await getDossier(params.ca, searchParams.chain || "solana");
    const symbol = dossier.overview?.symbol || params.ca;
    return {
      title: `${symbol} — TRENCHCOAT Rap Sheet`,
      openGraph: {
        title: `${symbol} — TRENCHCOAT Rap Sheet`,
        images: [`/api/og/${params.ca}`],
      },
    };
  } catch {
    return {
      title: "TRENCHCOAT Rap Sheet",
      openGraph: {
        title: "TRENCHCOAT Rap Sheet",
        images: [`/api/og/${params.ca}`],
      },
    };
  }
}

export default async function DossierPage({
  params,
  searchParams,
}: DossierPageProps) {
  const dossier = await getDossier(params.ca, searchParams.chain || "solana");

  return (
    <main className="min-h-screen bg-[#0a0a0a] px-5 py-8 text-[#f5f5f5]">
      <div className="mx-auto mb-6 flex max-w-5xl items-center justify-between border-b border-[#262626] pb-5 font-mono">
        <a href="/" className="text-sm font-bold">
          TRENCHCOAT
        </a>
        <span className="text-xs text-[#737373]">{dossier.chain.toUpperCase()}</span>
      </div>
      <RapSheet dossier={dossier} />
    </main>
  );
}
