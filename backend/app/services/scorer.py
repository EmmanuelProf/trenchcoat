from app.models.dossier import (
    DeployerProfile,
    SupplyDistribution,
    TokenOverview,
    TokenSecurity,
)


def _band(score: int) -> str:
    if score <= 30:
        return "AVOID"
    if score <= 60:
        return "CAUTION"
    return "CLEAR"


def score_dossier(
    security: TokenSecurity | None,
    distribution: SupplyDistribution | None,
    deployer: DeployerProfile | None,
    overview: TokenOverview | None,
) -> tuple[int, str]:
    score = 100

    if security is not None:
        if security.mint_revoked is False:
            score -= 25
        if security.freeze_revoked is False:
            score -= 10

        top10_pct = security.top10_pct
        if top10_pct is None and distribution is not None:
            top10_pct = distribution.top10_pct

        if top10_pct is not None:
            if top10_pct > 80:
                score -= 20
            elif top10_pct >= 50:
                score -= 10

    bundle = distribution.bundle if distribution is not None else None
    if bundle is not None and bundle.bundled:
        if bundle.confidence == "high":
            score -= 25
        elif bundle.confidence == "medium":
            score -= 15
        elif bundle.confidence == "low":
            score -= 5

    prior_rugs = deployer.rugged_count if deployer is not None else 0
    if prior_rugs >= 3:
        score -= 35
        score = min(score, 30)
    elif prior_rugs == 2:
        score -= 25
    elif prior_rugs == 1:
        score -= 15

    liquidity = overview.liquidity if overview is not None else None
    if liquidity is not None:
        if liquidity <= 5_000:
            score -= 15
        elif liquidity < 20_000:
            score -= 5

    score = max(0, min(100, score))
    return score, _band(score)
