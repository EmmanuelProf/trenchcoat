import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.models.dossier import (
    BundleAnalysis,
    DeployerProfile,
    SupplyDistribution,
    TokenOverview,
    TokenSecurity,
)
from app.services.scorer import score_dossier


def make_case(
    *,
    mint_revoked=True,
    freeze_revoked=True,
    top10_pct=30,
    bundled=False,
    confidence="low",
    rugged_count=0,
    liquidity=50_000,
):
    security = TokenSecurity(
        mint_revoked=mint_revoked,
        freeze_revoked=freeze_revoked,
        top10_pct=top10_pct,
    )
    distribution = SupplyDistribution(
        top10_pct=top10_pct,
        bundle_pct=35 if bundled else 0,
        bundle=BundleAnalysis(
            bundled=bundled,
            bundle_pct=35 if bundled else 0,
            confidence=confidence,
        ),
    )
    deployer = DeployerProfile(
        wallet="deployer",
        prior_count=rugged_count,
        rugged_count=rugged_count,
    )
    overview = TokenOverview(symbol="TEST", liquidity=liquidity)
    return security, distribution, deployer, overview


def test_clean_token_scores_clear():
    score, band = score_dossier(*make_case())

    assert score > 70
    assert band == "CLEAR"


def test_bundled_new_launch_scores_avoid():
    score, band = score_dossier(
        *make_case(
            mint_revoked=False,
            freeze_revoked=True,
            top10_pct=75,
            bundled=True,
            confidence="high",
            rugged_count=0,
            liquidity=5_000,
        )
    )

    assert score < 30
    assert band == "AVOID"


def test_serial_rugger_scores_avoid():
    score, band = score_dossier(
        *make_case(
            mint_revoked=True,
            freeze_revoked=True,
            top10_pct=40,
            bundled=False,
            rugged_count=3,
            liquidity=20_000,
        )
    )

    assert score < 40
    assert band == "AVOID"


def test_borderline_scores_caution():
    score, band = score_dossier(
        *make_case(
            mint_revoked=True,
            freeze_revoked=False,
            top10_pct=55,
            bundled=True,
            confidence="medium",
            rugged_count=1,
            liquidity=30_000,
        )
    )

    assert 30 <= score <= 60
    assert band == "CAUTION"


def test_missing_security_and_unknown_deployer_does_not_crash():
    score, band = score_dossier(
        None,
        SupplyDistribution(top10_pct=None, bundle=None),
        None,
        TokenOverview(symbol="EDGE", liquidity=None),
    )

    assert 30 <= score <= 60
    assert band == "CAUTION"
