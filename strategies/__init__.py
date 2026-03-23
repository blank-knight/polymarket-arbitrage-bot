"""
交易策略模块
提供多种交易策略实现
"""

from .base_strategy import BaseStrategy, TradingSignal, StrategyPerformance
from .arbitrage_strategy import ArbitrageStrategy
from .hedge_strategy import HedgeStrategy
from .trend_strategy import TrendStrategy
from .strategy_manager import StrategyManager, StrategyType
from .hedge_executor import HedgeExecutor, HedgePair, HedgeExecutionResult

__all__ = [
    "BaseStrategy",
    "TradingSignal",
    "StrategyPerformance",
    "ArbitrageStrategy",
    "HedgeStrategy",
    "TrendStrategy",
    "StrategyManager",
    "StrategyType",
    "HedgeExecutor",
    "HedgePair",
    "HedgeExecutionResult"
]
