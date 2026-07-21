"""GTI scoring: regime scenarios and bounds."""

from tensionr.scoring import calculate_gti


def _articles(n: int, negative_ratio: float, manipulation: int) -> list[dict]:
    negatives = int(n * negative_ratio)
    return [
        {
            "narrative_emotion": "fear" if i < negatives else "neutral",
            "manipulation_score": manipulation,
        }
        for i in range(n)
    ]


def _market(vix_price: float, vix_change: float, sp_change: float = 0.5) -> list[dict]:
    return [
        {"symbol": "VIX (VOLATILITY)", "price": vix_price, "change": vix_change},
        {"symbol": "GOLD (XAU)", "price": 2000.0, "change": 0.2},
        {"symbol": "S&P 500", "price": 5000.0, "change": sp_change},
        {"symbol": "NASDAQ 100", "price": 18000.0, "change": sp_change},
    ]


def _flights(total: int, mil: int, high_severity: int) -> dict:
    assets = []
    for i in range(total):
        assets.append(
            {
                "is_mil": i < mil,
                "is_outlier": True,  # every tracked asset is an outlier by construction
                "anomaly_score": 0.9 if i < high_severity else 0.5,
            }
        )
    return {"status": "active", "assets": assets}


def test_empty_inputs_is_sane_low():
    gti, components = calculate_gti([], [], {})
    assert 1 <= gti <= 10
    assert components["narrative"] == 0.0
    assert components["market"] == 0.0
    assert components["telemetry"] == 0.0


def test_calm_scenario_reads_calm():
    gti, _ = calculate_gti(
        _articles(500, negative_ratio=0.05, manipulation=20),
        _market(vix_price=13.0, vix_change=-1.0),
        _flights(total=30, mil=3, high_severity=0),
    )
    assert gti < 45


def test_crisis_scenario_reads_crisis():
    gti, _ = calculate_gti(
        _articles(500, negative_ratio=0.6, manipulation=80),
        [
            {"symbol": "VIX (VOLATILITY)", "price": 45.0, "change": 15.0},
            {"symbol": "GOLD (XAU)", "price": 2400.0, "change": 3.0},
            {"symbol": "S&P 500", "price": 4500.0, "change": -4.0},
            {"symbol": "NASDAQ 100", "price": 15000.0, "change": -5.0},
        ],
        _flights(total=80, mil=30, high_severity=12),
    )
    assert gti > 75


def test_typical_day_no_longer_floors_high():
    """Regression: the old formula pinned a typical day at ~55+ (saturation bug)."""
    gti, _ = calculate_gti(
        _articles(500, negative_ratio=0.1, manipulation=40),
        _market(vix_price=18.0, vix_change=2.0),
        _flights(total=80, mil=10, high_severity=0),
    )
    assert gti < 50


def test_bounds_always_respected():
    gti_low, _ = calculate_gti([], [], {})
    assert 1 <= gti_low <= 100
    gti_high, _ = calculate_gti(
        _articles(500, 1.0, 100),
        [
            {"symbol": "VIX (VOLATILITY)", "price": 90.0, "change": 50.0},
            {"symbol": "GOLD (XAU)", "price": 3000.0, "change": 10.0},
            {"symbol": "S&P 500", "price": 3000.0, "change": -12.0},
            {"symbol": "NASDAQ 100", "price": 9000.0, "change": -15.0},
        ],
        _flights(total=200, mil=100, high_severity=50),
    )
    assert 1 <= gti_high <= 100


def test_falling_vix_subtracts():
    calm_market, _ = calculate_gti([], _market(vix_price=20.0, vix_change=-3.0), {})
    hot_market, _ = calculate_gti([], _market(vix_price=20.0, vix_change=3.0), {})
    assert calm_market < hot_market
