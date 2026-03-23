"""
交易策略基类
定义所有策略的通用接口
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime
import logging


@dataclass
class TradingSignal:
    """交易信号"""
    signal_type: str  # 'buy', 'sell', 'hold'
    market_id: str
    outcome: str  # 'YES', 'NO'
    price: float
    amount: float
    confidence: float  # 0-1
    reasoning: str
    risk_level: str  # 'low', 'medium', 'high'
    timestamp: datetime
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class StrategyPerformance:
    """策略表现"""
    total_trades: int = 0
    profitable_trades: int = 0
    total_profit: float = 0.0
    total_loss: float = 0.0
    win_rate: float = 0.0
    max_drawdown: float = 0.0
    sharpe_ratio: float = 0.0

    def calculate_metrics(self):
        """计算指标"""
        if self.total_trades > 0:
            self.win_rate = self.profitable_trades / self.total_trades

        # 简化的夏普比率计算
        total_return = self.total_profit + self.total_loss
        if self.total_trades > 0:
            avg_return = total_return / self.total_trades
            self.sharpe_ratio = avg_return  # 简化版本


class BaseStrategy(ABC):
    """交易策略基类"""

    def __init__(self, name: str, config: Dict[str, Any]):
        self.name = name
        self.config = config
        self.enabled = config.get("enabled", True)

        # 策略参数
        self.max_position_size = config.get("max_position_size", 100)  # USDC
        self.min_profit_threshold = config.get("min_profit_threshold", 0.02)  # 2%
        self.max_risk_per_trade = config.get("max_risk_per_trade", 0.05)  # 5%

        # 性能追踪
        self.performance = StrategyPerformance()
        self.signals_history: List[TradingSignal] = []

        # 日志
        self.logger = logging.getLogger(f"strategy.{name}")

    @abstractmethod
    def generate_signal(self, market_data: Dict[str, Any],
                       context: Optional[Dict[str, Any]] = None) -> Optional[TradingSignal]:
        """
        生成交易信号

        Args:
            market_data: 市场数据
            context: 额外上下文（历史数据、其他市场信息等）

        Returns:
            交易信号，如果不交易则返回None
        """
        pass

    @abstractmethod
    def validate_signal(self, signal: TradingSignal) -> bool:
        """
        验证信号有效性

        Args:
            signal: 交易信号

        Returns:
            是否有效
        """
        pass

    def analyze(self, market_data: Dict[str, Any],
               context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        分析市场并返回决策

        Args:
            market_data: 市场数据
            context: 额外上下文

        Returns:
            分析结果
        """
        if not self.enabled:
            return {
                "action": "hold",
                "reason": "策略未启用"
            }

        # 生成信号
        signal = self.generate_signal(market_data, context)

        if signal is None:
            return {
                "action": "hold",
                "reason": "无交易信号"
            }

        # 验证信号
        if not self.validate_signal(signal):
            return {
                "action": "hold",
                "reason": "信号未通过验证"
            }

        # 记录信号
        self.signals_history.append(signal)

        return {
            "action": signal.signal_type,
            "signal": signal,
            "reason": signal.reasoning,
            "confidence": signal.confidence
        }

    def update_performance(self, trade_result: Dict[str, Any]):
        """
        更新策略表现

        Args:
            trade_result: 交易结果
        """
        self.performance.total_trades += 1

        profit = trade_result.get("profit", 0.0)

        if profit > 0:
            self.performance.profitable_trades += 1
            self.performance.total_profit += profit
        else:
            self.performance.total_loss += profit

        # 重新计算指标
        self.performance.calculate_metrics()

    def get_performance(self) -> StrategyPerformance:
        """获取策略表现"""
        return self.performance

    def reset(self):
        """重置策略状态"""
        self.performance = StrategyPerformance()
        self.signals_history = []

    def get_config_summary(self) -> Dict[str, Any]:
        """获取配置摘要"""
        return {
            "name": self.name,
            "enabled": self.enabled,
            "max_position_size": self.max_position_size,
            "min_profit_threshold": self.min_profit_threshold,
            "max_risk_per_trade": self.max_risk_per_trade
        }
