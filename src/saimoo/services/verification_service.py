from datetime import date
from typing import Any, Dict

from saimoo.data.storage.base import DataStorage
from saimoo.utils.types import AdjustType


class VerificationService:
    def __init__(self, storage: DataStorage):
        self.storage = storage

    def verify_data(
        self, symbol: str, start_date: date, end_date: date, adjust: AdjustType = AdjustType.QFQ
    ) -> Dict[str, Any]:
        """
        Verify AkShare data against Tushare data.
        Returns:
            Dict containing status ("pass"/"fail") and details.
        """
        # 1. Fetch data from local storage (assuming synced)
        bars_ak = self.storage.get_daily_bars(symbol, start_date, end_date, adjust, source="akshare")
        bars_ts = self.storage.get_daily_bars(symbol, start_date, end_date, adjust, source="tushare")

        if not bars_ak:
            return {"status": "fail", "details": "AkShare data missing"}
        if not bars_ts:
            # If secondary source missing, we can't verify.
            # Depending on policy, might return warning or skip.
            return {"status": "unknown", "details": "Tushare data missing"}

        # 2. Align data by date
        # Convert to dict for easier lookup
        dict_ak = {b.date: b for b in bars_ak}
        dict_ts = {b.date: b for b in bars_ts}

        common_dates = sorted(list(set(dict_ak.keys()) & set(dict_ts.keys())))
        if not common_dates:
            return {"status": "fail", "details": "No overlapping dates found"}

        diffs = []

        # 3. Compare fields
        # Tolerance: Price (0.02 or 1%), Volume (5%), Turnover (0.1 absolute percentage point or 5% relative)
        PRICE_TOLERANCE_ABS = 0.05
        PRICE_TOLERANCE_PCT = 0.01
        VOLUME_TOLERANCE_PCT = 0.05
        TURNOVER_TOLERANCE_ABS = 0.1  # e.g., 0.1% difference is acceptable

        for d in common_dates:
            bar_ak = dict_ak[d]
            bar_ts = dict_ts[d]

            # Compare OHLC
            for field in ["open", "high", "low", "close"]:
                val_ak = getattr(bar_ak, field)
                val_ts = getattr(bar_ts, field)

                diff = abs(val_ak - val_ts)
                # Check absolute difference or relative difference
                if diff > PRICE_TOLERANCE_ABS and (val_ts > 0 and diff / val_ts > PRICE_TOLERANCE_PCT):
                    diffs.append(f"{d}: {field} mismatch (Ak={val_ak}, Ts={val_ts})")

            # Compare Volume
            vol_ak = bar_ak.volume
            vol_ts = bar_ts.volume
            if vol_ts > 0:
                vol_diff_pct = abs(vol_ak - vol_ts) / vol_ts
                if vol_diff_pct > VOLUME_TOLERANCE_PCT:
                    diffs.append(f"{d}: volume mismatch (Ak={vol_ak}, Ts={vol_ts})")

            # Compare Turnover
            # Turnover might be None if data source doesn't provide it
            turn_ak = bar_ak.turnover
            turn_ts = bar_ts.turnover

            if turn_ak is not None and turn_ts is not None:
                turn_diff = abs(turn_ak - turn_ts)
                # Turnover is usually percentage (e.g., 1.5%), so we check absolute diff
                if turn_diff > TURNOVER_TOLERANCE_ABS:
                    diffs.append(f"{d}: turnover mismatch (Ak={turn_ak}, Ts={turn_ts})")
            elif (turn_ak is None) != (turn_ts is None):
                # One is None, the other isn't
                diffs.append(f"{d}: turnover presence mismatch (Ak={turn_ak}, Ts={turn_ts})")

        status = "pass" if not diffs else "fail"
        details = "; ".join(diffs[:5])
        if len(diffs) > 5:
            details += f"... (+{len(diffs) - 5} more)"

        # 4. Persist result
        # We verify usually for a range, but verification result is stored per symbol/adjust/date?
        # The table DataVerification has (symbol, date, adjust) as PK.
        # It implies we store verification result for *each day*.
        # But if we verify a batch, maybe we just store the overall result or the result for the latest date?
        # Given the user requirement "persistently prompt on UI", storing a single status for the symbol/adjust might be easier.
        # But my model has 'date' in PK.
        # Let's store the result for the *latest date* verified, or store for *every verified date*.
        # Storing for every date allows fine-grained checking.

        # For UI display, we probably care about "Is the dataset generally valid?".
        # Let's store the result for the end_date (or latest common date) to represent the latest check.
        # Or better: Save "fail" for the specific dates that failed?
        # The prompt says "In validation failure, persist prompt".
        # Let's save the result for the *latest date* of the sync.

        latest_date = common_dates[-1]
        self.storage.save_verification_result(
            symbol=symbol, date=latest_date, adjust=adjust, status=status, details=details if status == "fail" else None
        )

        return {"status": status, "details": details}
