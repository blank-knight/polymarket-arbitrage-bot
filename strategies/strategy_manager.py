"""
策略管理器
管理多个交易策略，选择最优策略执行
"""

from typing import Dict, Any, List, Optional, Type
from enum import Enum
import logging
from .base_strategy import BaseStrategy, TradingSignal, StrategyPerformance
from .arbitrage_strategy import ArbitrageStrategy
from .hedge_strategy import HedgeStrategy
from .trend_strategy import TrendStrategy


class StrategyType(Enum):
    """策略类型"""
    ARBITRAGE = "arbitrage"
    HEDGE = "hedge"
    TREND = "trend"


class StrategyManager:
    """策略管理器"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.strategies: Dict[str, BaseStrategy] = {}

        # 初始化日志
        self.logger = logging.getLogger("strategy_manager")

        # 加载策略
        self._load_strategies()

    def _load_strategies(self):
        """加载策略配置"""
        strategies_config = self.config.get("strategies", {})

        # 加载套利策略
        if strategies_config.get("arbitrage", {}).get("enabled", True):
            self.strategies["arbitrage"] = ArbitrageStrategy(
                strategies_config.get("arbitrage", {})
            )
            self.logger.info("套利策略已加载")

        # 加载对冲策略
        if strategies_config.get("hedge", {}).get("enabled", True):
            self.strategies["hedge"] = HedgeStrategy(
                strategies_config.get("hedge", {})
            )
            self.logger.info("对冲策略已加载")

        # 加载趋势策略
        if strategies_config.get("trend", {}).get("enabled", True):
            self.strategies["trend"] = TrendStrategy(
                strategies_config.get("trend", {})
            )
            self.logger.info("趋势策略已加载")

        self.logger.info(f"共加载 {len(self.strategies)} 个策略")

    def analyze_market(self, market_data: Dict[str, Any],
                      strategy_name: Optional[str] = None,
                      context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        分析市场（使用指定策略或所有策略）

        Args:
            market_data: 市场数据
            strategy_name: 策略名称，如果为None则使用所有策略
            context: 额外上下文

        Returns:
            分析结果
        """
        if strategy_name:
            # 使用指定策略
            if strategy_name not in self.strategies:
                return {
                    "error": f"策略 '{strategy_name}' 未找到"
                }

            return self.strategies[strategy_name].analyze(market_data, context)
        else:
            # 使用所有策略
            results = {}
            best_signal = None
            best_confidence = 0.0

            for name, strategy in self.strategies.items():
                result = strategy.analyze(market_data, context)
                results[name] = result

                # 选择最佳信号
                if result.get("action") in ["buy", "sell"]:
                    signal = result.get("signal")
                    if signal and signal.confidence > best_confidence:
                        best_signal = signal
                        best_confidence = signal.confidence

            return {
                "all_results": results,
                "best_signal": best_signal,
                "recommended_strategy": best_signal.metadata.get("strategy") if best_signal else None
            }

    def scan_markets(self, markets: List[Dict[str, Any]],
                    limit_per_strategy: int = 5) -> Dict[str, Any]:
        """
        扫描多个市场，寻找机会

        Args:
            markets: 市场列表
            limit_per_strategy: 每个策略返回的最大机会数

        Returns:
            所有策略的机会
        """
        all_opportunities = {}

        # 套利策略
        if "arbitrage" in self.strategies:
            arb_opportunities = self.strategies["arbitrage"].scan_opportunities(
                markets,
                limit=limit_per_strategy
            )
            all_opportunities["arbitrage"] = arb_opportunities

        # 趋势策略
        if "trend" in self.strategies:
            trend_opportunities = self.strategies["trend"].scan_trending_markets(
                markets,
                limit=limit_per_strategy
            )
            all_opportunities["trend"] = trend_opportunities

        # 对冲策略需要LLM分析，这里跳过
        if "hedge" in self.strategies:
            # 对冲策略需要单独调用 find_hedge_pairs
            all_opportunities["hedge"] = []

        return all_opportunities

    def find_hedges(self, markets: List[Dict[str, Any],
                  llm_analysis: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        查找对冲机会

        Args:
            markets: 市场列表
            llm_analysis: LLM分析结果

        Returns:
            对冲对列表
        """
        if "hedge" not in self.strategies:
            return []

        hedge_strategy = self.strategies["hedge"]
        return hedge_strategy.find_hedge_pairs(markets, llm_analysis)

    def select_best_opportunity(self, opportunities: Dict[str, Any],
                               max_risk: str = "medium") -> Optional[TradingSignal]:
        """
        从多个机会中选择最佳机会

        Args:
            opportunities: 所有策略的机会
            max_risk: 最大风险等级（low, medium, high）

        Returns:
            最佳交易信号或None
        """
        all_signals = []

        # 收集所有信号
        for strategy_name, strategy_opportunities in opportunities.items():
            for opp in strategy_opportunities:
                signal = opp.get("signal")
                if signal:
                    signal.metadata["strategy"] = strategy_name
                    all_signals.append(signal)

        if not all_signals:
            return None

        # 过滤风险等级
        risk_order = {"low": 0, "medium": 1, "high": 2}
        max_risk_level = risk_order.get(max_risk, 1)

        filtered_signals = [
            s for s in all_signals
            if risk_order.get(s.risk_level, 2) <= max_risk_level
        ]

        if not filtered_signals:
            return None

        # 按信心度排序
        filtered_signals.sort(key=lambda x: x.confidence, reverse=True)

        return filtered_signals[0]

    def update_strategy_performance(self, strategy_name: str,
                                   trade_result: Dict[str, Any]):
        """
        更新策略表现

        Args:
            strategy_name: 策略名称
            trade_result: 交易结果
        """
        if strategy_name in self.strategies:
            self.strategies[strategy_name].update_performance(trade_result)

    def get_strategy_performance(self, strategy_name: Optional[str] = None) -> Dict[str, StrategyPerformance]:
        """
        获取策略表现

        Args:
            strategy_name: 策略名称，如果为None则返回所有策略

        Returns:
            策略表现
        """
        if strategy_name:
            if strategy_name not in self.strategies:
                return {}

            return {strategy_name: self.strategies[strategy_name].get_performance()}
        else:
            return {
                name: strategy.get_performance()
                for name, strategy in self.strategies.items()
            }

    def get_strategy_config(self, strategy_name: Optional[str] = None) -> Dict[str, Any]:
        """
        获取策略配置

        Args:
            strategy_name: 策略名称，如果为None则返回所有策略

        Returns:
            策略配置
        """
        if strategy_name:
            if strategy_name not in self.strategies:
                return {}

            return {strategy_name: self.strategies[strategy_name].get_config_summary()}
        else:
            return {
                name: strategy.get_config_summary()
                for name, strategy in self.strategies.items()
            }

    def enable_strategy(self, strategy_name: str):
        """启用策略"""
        if strategy_name in self.strategies:
            self.strategies[strategy_name].enabled = True
            self.logger.info(f"策略 '{strategy_name}' 已启用")

    def disable_strategy(self, strategy_name: str):
        """禁用策略"""
        if strategy_name in self.strategies:
            self.strategies[strategy_name].enabled = False
            self.logger.info(f"策略 '{strategy_name}' 已禁用")

    def reset_strategies(self):
        """重置所有策略"""
        for strategy in self.strategies.values():
            strategy.reset()

        self.logger.info("所有策略已重置")

    def get_summary(self) -> Dict[str, Any]:
        """
        获取策略管理器摘要

        Returns:
            摘要信息
        """
        return {
            "total_strategies": len(self.strategies),
            "enabled_strategies": sum(1 for s in self.strategies.values() if s.enabled),
            "strategies": list(self.strategies.keys()),
            "performance": self.get_strategy_performance()
        }
