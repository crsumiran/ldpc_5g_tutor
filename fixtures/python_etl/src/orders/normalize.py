import pandas as pd

ORDER_SCHEMA = ["order_id", "ts_utc", "amount"]


def normalize_orders(orders: pd.DataFrame) -> pd.DataFrame:
    """Return validated orders in the canonical order schema."""
    # Step 1: Create a copy so the input frame is not modified.
    normalized = orders.copy()

    # Step 2: Convert order timestamps to UTC.
    normalized["ts_utc"] = pd.to_datetime(normalized["order_date"], utc=True)

    # Step 3: Remove records that do not have a valid order identifier.
    normalized = normalized.dropna(subset=["order_id"])
    normalized = normalized[normalized["order_id"].astype(str).str.strip() != ""]

    # Step 4: Ensure amount is float
    normalized["amount"] = normalized["amount"].astype(float)

    # Step 5: Return columns in the order required by ORDER_SCHEMA.
    return normalized[ORDER_SCHEMA].reset_index(drop=True)
