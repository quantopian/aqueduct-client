import numpy as np
import pandas as pd

from quantopian.pipeline import Pipeline
from quantopian.pipeline.domain import US_EQUITIES
from quantopian.pipeline.data import EquityPricing
from quantopian.pipeline.data.factset import Fundamentals, EquityMetadata, RBICSFocus
from quantopian.pipeline.factors import (
    CustomFactor,
    AnnualizedVolatility,
    SimpleBeta,
    Returns,
    SimpleMovingAverage,
    AverageDollarVolume,
)


# import groupings
# ----------------
rbics_economy_number = RBICSFocus.l1_id.latest
rbics_economy = RBICSFocus.l1_name.latest

# Defining universe criteria
# --------------------------
avg_day_dv_200 = AverageDollarVolume(window_length=200)
mcap = Fundamentals.mkt_val.latest
price = EquityPricing.close.latest
volume = EquityPricing.volume.latest

# Set Universe
# ------------
universe = (
    avg_day_dv_200.percentile_between(5, 100)
    & (price > 5.0)
    & (mcap > 100e6)
    & EquityMetadata.security_type.latest.eq("SHARE")
    & EquityMetadata.is_primary.latest
    & volume.notnull()
)

universe_top500 = mcap.top(500, mask=universe)

# Creating custom factors
# -----------------------
class lt_mom(CustomFactor):
    inputs = [EquityPricing.close]
    window_length = 252

    def compute(self, today, assets, out, price):
        out[:] = (price[-21] - price[-252]) / price[-252]


# Size
# ----
mcap = Fundamentals.mkt_val.latest
log_mcap = (
    mcap.log()
    .winsorize(min_percentile=0.05, max_percentile=0.95, mask=universe_top500)
    .zscore()
)

# Value
# -----
fcfy = Fundamentals.free_cf_fcfe_ltm.latest / mcap
fcfy = fcfy.winsorize(
    min_percentile=0.05, max_percentile=0.95, mask=universe_top500
).zscore()

ey = Fundamentals.oper_inc_bef_dep_ltm.latest / mcap
ey = ey.winsorize(
    min_percentile=0.05, max_percentile=0.95, mask=universe_top500
).zscore()

# Momentum
# --------
lt_momentum = lt_mom(mask=universe_top500).zscore()

# Volatility
# ----------
ann_vol = AnnualizedVolatility(
    inputs=[Returns(window_length=2)], window_length=66, mask=universe_top500
).zscore()

# Quality
# -------
gpa = Fundamentals.gross_inc_ltm.latest / Fundamentals.assets.latest
gpa = gpa.zscore(mask=universe_top500)

factors = {
    "fcfy": fcfy,
    "ey": ey,
    "log_mcap": log_mcap,
    "lt_mom": lt_momentum,
    "ann_vol": ann_vol,
    "gpa": gpa,
}


def make_pipeline():

    return Pipeline(
        columns=factors,
        screen=universe_top500.downsample("month_start"),
        domain=US_EQUITIES,
    )
