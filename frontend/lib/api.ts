const API_URL = process.env.NEXT_PUBLIC_API_URL;

export type Band = "AVOID" | "CAUTION" | "CLEAR";
export type BundleConfidence = "high" | "medium" | "low";
export type TokenOutcome = "rugged" | "abandoned" | "alive" | "unknown";

export interface TokenOverview {
  symbol: string | null;
  name: string | null;
  price: number | null;
  mc: number | null;
  liquidity: number | null;
  supply: number | null;
  age_days: number | null;
}

export interface TokenSecurity {
  mint_revoked: boolean | null;
  freeze_revoked: boolean | null;
  top10_pct: number | null;
  mutable_metadata: boolean | null;
  transfer_fee_enabled: boolean | null;
}

export interface PriorToken {
  ca: string;
  symbol: string | null;
  outcome: TokenOutcome;
  age_days: number | null;
  pct_from_ath: number | null;
}

export interface DeployerProfile {
  wallet: string | null;
  prior_tokens: PriorToken[];
  prior_count: number;
  rugged_count: number;
  abandoned_count: number;
  alive_count: number;
  unknown_count: number;
}

export interface BundleAnalysis {
  bundled: boolean;
  bundle_pct: number;
  suspect_wallet_count: number;
  earliest_block: number | null;
  confidence: BundleConfidence;
}

export interface SupplyDistribution {
  bundle_pct: number | null;
  top10_pct: number | null;
  suspect_wallets: string[];
  bundle: BundleAnalysis | null;
}

export interface Dossier {
  ca: string;
  chain: string;
  generated_at: string;
  score: number;
  band: Band;
  overview: TokenOverview | null;
  security: TokenSecurity | null;
  deployer: DeployerProfile | null;
  distribution: SupplyDistribution | null;
  verdict: string;
  raw_signals: Record<string, unknown>;
}

export interface TrendingToken {
  address: string;
  symbol: string | null;
  name: string | null;
  price: number | null;
  mc: number | null;
  liquidity: number | null;
  volume24hUSD: number | null;
  rank?: number | null;
}

export async function getDossier(
  ca: string,
  chain: string = "solana"
): Promise<Dossier> {
  return fetchJson<Dossier>(`/dossier/${encodeURIComponent(ca)}?chain=${encodeURIComponent(chain)}`);
}

export async function getTrending(
  chain: string = "solana"
): Promise<TrendingToken[]> {
  return fetchJson<TrendingToken[]>(`/trending?chain=${encodeURIComponent(chain)}`);
}

async function fetchJson<T>(path: string): Promise<T> {
  if (!API_URL) {
    throw new Error("NEXT_PUBLIC_API_URL is not configured");
  }

  const response = await fetch(`${API_URL}${path}`, {
    headers: {
      accept: "application/json",
    },
    next: {
      revalidate: 60,
    },
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(`Backend request failed (${response.status}): ${text || response.statusText}`);
  }

  return response.json() as Promise<T>;
}
