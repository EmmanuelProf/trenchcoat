from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


Band = Literal["AVOID", "CAUTION", "CLEAR"]
BundleConfidence = Literal["high", "medium", "low"]
TokenOutcome = Literal["rugged", "abandoned", "alive", "unknown"]


class TokenOverview(BaseModel):
    symbol: str | None = None
    name: str | None = None
    price: float | None = None
    mc: float | None = None
    liquidity: float | None = None
    supply: float | None = None
    age_days: float | None = None


class TokenSecurity(BaseModel):
    mint_revoked: bool | None = None
    freeze_revoked: bool | None = None
    top10_pct: float | None = None
    mutable_metadata: bool | None = None
    transfer_fee_enabled: bool | None = None


class PriorToken(BaseModel):
    ca: str
    symbol: str | None = None
    outcome: TokenOutcome = "unknown"
    age_days: float | None = None
    pct_from_ath: float | None = None


class DeployerProfile(BaseModel):
    wallet: str | None = None
    prior_tokens: list[PriorToken] = Field(default_factory=list)
    prior_count: int = 0
    rugged_count: int = 0
    abandoned_count: int = 0
    alive_count: int = 0
    unknown_count: int = 0


class BundleAnalysis(BaseModel):
    bundled: bool = False
    bundle_pct: float = 0
    suspect_wallet_count: int = 0
    earliest_block: int | None = None
    confidence: BundleConfidence = "low"


class SupplyDistribution(BaseModel):
    bundle_pct: float | None = None
    top10_pct: float | None = None
    suspect_wallets: list[str] = Field(default_factory=list)
    bundle: BundleAnalysis | None = None


class Dossier(BaseModel):
    ca: str
    chain: str
    generated_at: datetime
    score: int
    band: Band
    overview: TokenOverview | None = None
    security: TokenSecurity | None = None
    deployer: DeployerProfile | None = None
    distribution: SupplyDistribution | None = None
    verdict: str
    raw_signals: dict[str, Any] = Field(default_factory=dict)
