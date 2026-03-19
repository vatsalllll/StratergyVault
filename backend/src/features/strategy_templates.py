"""
StrategyVault — Strategy Templates Library
Curated strategy templates from Harvard Algorithmic Trading course.

Each template is a string of clean, backtesting.py-compatible Python code
that the AI generator can use as a base or reference.

Sources:
  - Harvard-Algorithmic-Trading-with-AI/backtest/bb_squeeze_adx.py
  - Harvard-Algorithmic-Trading-with-AI/backtest/template.py
"""

STRATEGY_TEMPLATES = {
    "bb_squeeze_adx": {
        "name": "Bollinger Band Squeeze + ADX",
        "description": (
            "Detects Bollinger Band squeeze inside Keltner Channels, "
            "enters on breakout confirmed by ADX trend strength. "
            "Uses SL/TP for risk management."
        ),
        "tags": ["mean-reversion", "volatility", "trend-filter", "crypto", "stocks"],
        "source": "Harvard Algorithmic Trading with AI",
        "code": '''import pandas as pd
import numpy as np
from backtesting import Backtest, Strategy

class BBSqueezeADX(Strategy):
    bb_window = 20
    bb_std    = 2.0
    kc_window = 20
    kc_atr    = 1.5
    adx_period = 14
    adx_thresh = 25
    take_profit = 0.05
    stop_loss   = 0.03

    def init(self):
        close = self.data.Close
        high  = self.data.High
        low   = self.data.Low

        # Bollinger Bands
        self.sma = self.I(lambda c: pd.Series(c).rolling(self.bb_window).mean().values, close)
        std_vals = self.I(lambda c: pd.Series(c).rolling(self.bb_window).std().values,  close)
        self.upper_bb = self.I(lambda s,d: s + self.bb_std * d, self.sma, std_vals)
        self.lower_bb = self.I(lambda s,d: s - self.bb_std * d, self.sma, std_vals)

        # ATR for Keltner
        def _atr(h, l, c, n=14):
            tr = pd.DataFrame({
                'hl': pd.Series(h) - pd.Series(l),
                'hc': (pd.Series(h) - pd.Series(c).shift(1)).abs(),
                'lc': (pd.Series(l) - pd.Series(c).shift(1)).abs(),
            }).max(axis=1)
            return tr.rolling(n).mean().values

        self.atr = self.I(_atr, high, low, close, self.kc_window)
        kc_mid = self.I(lambda c: pd.Series(c).rolling(self.kc_window).mean().values, close)
        self.upper_kc = self.I(lambda m,a: m + self.kc_atr * a, kc_mid, self.atr)
        self.lower_kc = self.I(lambda m,a: m - self.kc_atr * a, kc_mid, self.atr)

        # Squeeze: BB inside KC
        self.in_squeeze = self.I(
            lambda ub, uk, lb, lk: ((pd.Series(ub) < pd.Series(uk)) & (pd.Series(lb) > pd.Series(lk))).astype(float).values,
            self.upper_bb, self.upper_kc, self.lower_bb, self.lower_kc
        )

        # ADX
        def _adx(h, l, c, n=14):
            hi, lo, cl = pd.Series(h), pd.Series(l), pd.Series(c)
            plus_dm  = hi.diff().clip(lower=0)
            minus_dm = (-lo.diff()).clip(lower=0)
            tr = pd.DataFrame({'hl': hi-lo, 'hc': (hi-cl.shift()).abs(), 'lc': (lo-cl.shift()).abs()}).max(axis=1)
            atr  = tr.rolling(n).mean()
            plus_di  = 100 * plus_dm.rolling(n).mean()  / atr
            minus_di = 100 * minus_dm.rolling(n).mean() / atr
            dx = (100 * (plus_di - minus_di).abs() / (plus_di + minus_di + 1e-9))
            return dx.rolling(n).mean().values

        self.adx = self.I(_adx, high, low, close, self.adx_period)
        self._released = False

    def next(self):
        sq_now  = bool(self.in_squeeze[-1])
        sq_prev = bool(self.in_squeeze[-2]) if len(self.data) > 1 else True
        if sq_prev and not sq_now:
            self._released = True

        if self._released and self.adx[-1] > self.adx_thresh:
            price = self.data.Close[-1]
            if price > self.upper_bb[-1] and not self.position:
                self.buy(sl=price * (1 - self.stop_loss), tp=price * (1 + self.take_profit))
                self._released = False
            elif price < self.lower_bb[-1] and not self.position:
                self.sell(sl=price * (1 + self.stop_loss), tp=price * (1 - self.take_profit))
                self._released = False

DATA_PATH = "path/to/your/data.csv"
data = pd.read_csv(DATA_PATH, index_col=0, parse_dates=True)
data.columns = [c.strip().capitalize() for c in data.columns]
bt = Backtest(data, BBSqueezeADX, cash=100_000, commission=0.001)
stats = bt.run()
print(stats)
''',
    },

    "simple_sma_crossover": {
        "name": "Simple SMA Crossover",
        "description": "Classic dual-SMA crossover. Buys when fast SMA crosses above slow SMA.",
        "tags": ["trend-following", "simple", "crypto", "stocks"],
        "source": "Harvard Algorithmic Trading with AI",
        "code": '''import pandas as pd
import numpy as np
from backtesting import Backtest, Strategy

class SMACrossover(Strategy):
    fast = 21
    slow = 63

    def init(self):
        close = self.data.Close
        self.fast_ma = self.I(lambda c: pd.Series(c).rolling(self.fast).mean().values, close)
        self.slow_ma = self.I(lambda c: pd.Series(c).rolling(self.slow).mean().values, close)

    def next(self):
        if self.fast_ma[-1] > self.slow_ma[-1] and self.fast_ma[-2] <= self.slow_ma[-2]:
            if not self.position:
                self.buy(size=0.95)
        elif self.fast_ma[-1] < self.slow_ma[-1] and self.fast_ma[-2] >= self.slow_ma[-2]:
            if self.position:
                self.position.close()

DATA_PATH = "path/to/your/data.csv"
data = pd.read_csv(DATA_PATH, index_col=0, parse_dates=True)
data.columns = [c.strip().capitalize() for c in data.columns]
bt = Backtest(data, SMACrossover, cash=100_000, commission=0.001)
stats = bt.run()
print(stats)
''',
    },

    "rsi_mean_reversion": {
        "name": "RSI Mean Reversion",
        "description": "Buys oversold (RSI < 30) and sells overbought (RSI > 70) conditions.",
        "tags": ["mean-reversion", "oscillator", "crypto", "stocks"],
        "source": "StrategyVault template",
        "code": '''import pandas as pd
import numpy as np
from backtesting import Backtest, Strategy

class RSIMeanReversion(Strategy):
    rsi_period = 14
    oversold   = 30
    overbought = 70

    def init(self):
        close = self.data.Close
        def _rsi(c, n=14):
            s = pd.Series(c)
            delta = s.diff()
            gain = delta.clip(lower=0).rolling(n).mean()
            loss = (-delta.clip(upper=0)).rolling(n).mean()
            rs = gain / (loss + 1e-9)
            return (100 - 100 / (1 + rs)).values
        self.rsi = self.I(_rsi, close, self.rsi_period)

    def next(self):
        if self.rsi[-1] < self.oversold and not self.position:
            self.buy(size=0.95)
        elif self.rsi[-1] > self.overbought and self.position:
            self.position.close()

DATA_PATH = "path/to/your/data.csv"
data = pd.read_csv(DATA_PATH, index_col=0, parse_dates=True)
data.columns = [c.strip().capitalize() for c in data.columns]
bt = Backtest(data, RSIMeanReversion, cash=100_000, commission=0.001)
stats = bt.run()
print(stats)
''',
    },
}


def get_template(name: str) -> dict:
    """Get a strategy template by name."""
    return STRATEGY_TEMPLATES.get(name, {})


def list_templates() -> list:
    """List all available templates with metadata."""
    return [
        {
            "id": k,
            "name": v["name"],
            "description": v["description"],
            "tags": v["tags"],
            "source": v["source"],
        }
        for k, v in STRATEGY_TEMPLATES.items()
    ]
