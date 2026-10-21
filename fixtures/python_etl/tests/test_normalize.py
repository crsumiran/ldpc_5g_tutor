import pandas as pd
from src.orders.normalize import ORDER_SCHEMA, normalize_orders


def test_normalize_orders_basic():
    df = pd.DataFrame({
        "order_id": ["O1", "O2", None, " "],
        "order_date": ["2026-01-01 10:00:00", "2026-01-02 12:00:00", "2026-01-03", "2026-01-04"],
        "amount": [100.5, 200.0, 50.0, 75.0],
    })
    res = normalize_orders(df)
    assert list(res.columns) == ORDER_SCHEMA
    assert len(res) == 2
    assert res.iloc[0]["order_id"] == "O1"
    assert str(res.iloc[0]["ts_utc"]).startswith("2026-01-01")
