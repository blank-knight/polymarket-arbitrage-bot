"""
趋势跟踪策略
基于市场趋势进行投机交易
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from collections import deque
import numpy as np
from .base_strategy import BaseStrategy, TradingSignal


class TrendStrategy(BaseStrategy):
    """趋势跟踪策略 - 识别并跟踪市场趋势"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__("trend", config)

        # 趋势参数
        self.trend_window = config.get("trend_window", 12)  # 12小时窗口
        self.min_trend_strength = config.get("min_trend_strength", 0.1)  # 10%最小趋势强度
        self.volume_threshold = config.get("volume_threshold", 1000)  # 最小成交量

        # 价格历史缓存
        self.price_history: Dict[str, deque] = {}
        self.max_history_length = self.trend_window * 6  # 保存2倍窗口的历史

    def generate_signal(self, market_data: Dict[str, Any],
                       context: Optional[Dict[str, Any]] = None) -> Optional[TradingSignal]:
        """
        生成趋势信号

        Args:
            market_data: 市场数据
            context: 额外上下文（历史价格等）

        Returns:
            趋势信号或None
        """
        market_id = market_data.get("marketId", "")

        # 提取价格
        outcome_prices = market_data.get("outcomePrices", [])
        if len(outcome_prices) < 1:
            return None

        current_yes_price = outcome_prices[0].get("price", 0)

        # 更新价格历史
        self._update_price_history(market_id, current_yes_price)

        # 检查是否有足够的历史数据
        history = self.price_history.get(market_id, deque())
        if len(history) < self.trend_window:
            return None

        # 检查成交量
        volume_24h = market_data.get("volume_24h", 0)
        if volume_24h < self.volume_threshold:
            return None

        # 检查流动性
        liquidity_score = market_data.get("liquidity_score", 0)
        if liquidity_score < self.min_liquidity_score:
            return None

        # 分析趋势
        trend_analysis = self._analyze_trend(history)

        if not trend_analysis["has_trend"]:
            return None

        # 计算仓位大小
        position_size = self._calculate_position_size(
            market_data,
            trend_analysis["trend_strength"]
        )

        # 确定交易方向
        if trend_analysis["direction"] == "up":
            signal_type = "buy"
            outcome = "YES"
            reasoning = (f"上升趋势，价格从{trend_analysis['start_price']:.3f}"
                        f"涨至{current_yes_price:.3f}"
                        f"(+{trend_analysis['trend_strength']:.1%})")
        else:
            signal_type = "sell"  # 买NO
            outcome = "NO"
            reasoning = (f"下降趋势，价格从{trend_analysis['start_price']:.3f}"
                        f"跌至{current_yes_price:.3f}"
                        f"({trend_analysis['trend_strength']:.1%})")

        # 信心度（基于趋势强度和成交量）
        confidence = self._calculate_confidence(
            trend_analysis["trend_strength"],
            volume_24h,
            liquidity_score
        )

        # 风险等级
        risk_level = self._assess_risk_level(trend_analysis, liquidity_score)

        return TradingSignal(
            signal_type=signal_type,
            market_id=market_id,
            outcome=outcome,
            price=current_yes_price,
            amount=position_size,
            confidence=confidence,
            reasoning=reasoning,
            risk_level=risk_level,
            timestamp=datetime.now(),
            metadata={
                "trend_direction": trend_analysis["direction"],
                "trend_strength": trend_analysis["trend_strength"],
                "start_price": trend_analysis["start_price"],
                "end_price": current_yes_price,
                "volume_24h": volume_24h,
                "liquidity_score": liquidity_score
            }
        )

    def validate_signal(self, signal: TradingSignal) -> bool:
        """验证趋势信号"""
        # 基本验证
        if not signal.market_id:
            return False

        if signal.price <= 0 or signal.price >= 1:
            return False

        if signal.amount <= 0 or signal.amount > self.max_position_size:
            return False

        # 趋势策略需要更高的信心度
        if signal.confidence < 0.6:
            return False

        # 检查趋势强度
        trend_strength = signal.metadata.get("trend_strength", 0)
        if trend_strength < self.min_trend_strength:
            return False

        return True

    def _update_price_history(self, market_id: str, price: float):
        """
        更新价格历史

        Args:
            market_id: 市场ID
            price: 当前价格
        """
        if market_id not in self.price_history:
            self.price_history[market_id] = deque(maxlen=self.max_history_length)

        self.price_history[market_id].append({
            "price": price,
            "timestamp": datetime.now()
        })

    def _analyze_trend(self, history: deque) -> Dict[str, Any]:
        """
        分析趋势

        Args:
            history: 价格历史

        Returns:
            趋势分析
        """
        # 提取价格
        prices = [item["price"] for item in history]

        # 线性回归计算趋势
        x = np.arange(len(prices))
        y = np.array(prices)

        # 简单线性回归
        coefficients = np.polyfit(x, y, 1)
        slope = coefficients[0]

        # 计算价格变化
        start_price = prices[0]
        end_price = prices[-1]
        price_change = (end_price - start_price) / start_price if start_price > 0 else 0

        # 判断趋势方向
        if price_change > 0.02:  # 至少2%的上涨
            direction = "up"
            has_trend = True
        elif price_change < -0.02:  # 至少2%的下跌
            direction = "down"
            has_trend = True
        else:
            direction = "neutral"
            has_trend = False

        # 趋势强度（绝对值）
        trend_strength = abs(price_change)

        # 计算波动性（标准差）
        volatility = np.std(prices) if len(prices) > 1 else 0

        return {
            "direction": direction,
            "has_trend": has_trend,
            "trend_strength": trend_strength,
            "start_price": start_price,
            "end_price": end_price,
            "slope": slope,
            "volatility": volatility,
            "price_change": price_change
        }

    def _calculate_position_size(self, market_data: Dict[str, Any],
                                trend_strength: float) -> float:
        """
        计算仓位大小

        Args:
            market_data: 市场数据
            trend_strength: 趋势强度

        Returns:
            仓位大小（USDC）
        """
        # 基础仓位
        base_position = self.max_position_size * 0.25  # 趋势策略使用25%仓位

        # 根据趋势强度调整
        strength_multiplier = min(trend_strength / 0.15, 1.5)  # 最多1.5倍
        adjusted_position = base_position * strength_multiplier

        # 根据流动性调整
        liquidity_score = market_data.get("liquidity_score", 0.5)
        liquidity_multiplier = liquidity_score

        final_position = adjusted_position * liquidity_multiplier

        return min(final_position, self.max_position_size)

    def _calculate_confidence(self, trend_strength: float,
                             volume: float,
                             liquidity_score: float) -> float:
        """
        计算信心度

        Args:
            trend_strength: 趋势强度
            volume: 成交量
            liquidity_score: 流动性分数

        Returns:
            信心度（0-1）
        """
        # 趋势强度分数（0.02-0.20范围映射到0-1）
        strength_score = min(max((trend_strength - 0.02) / 0.18, 0), 1)

        # 成交量分数
        volume_score = min(volume / 10000, 1)

        # 综合评分
        confidence = (strength_score * 0.5 +
                     volume_score * 0.3 +
                     liquidity_score * 0.2)

        return min(confidence, 1.0)

    def _assess_risk_level(self, trend_analysis: Dict[str, Any],
                          liquidity_score: float) -> str:
        """
        评估风险等级

        Args:
            trend_analysis: 趋势分析
            liquidity_score: 流动性分数

        Returns:
            风险等级
        """
        volatility = trend_analysis.get("volatility", 0)
        trend_strength = trend_analysis.get("trend_strength", 0)

        # 高波动性 = 高风险
        if volatility > 0.1:  # 10%波动性
            return "high"

        # 低流动性 = 高风险
        if liquidity_score < 0.5:
            return "high"

        # 趋势强度适中 + 流动性良好 = 低风险
        if trend_strength > 0.05 and trend_strength < 0.15 and liquidity_score >= 0.8:
            return "low"

        # 其他情况 = 中等风险
        return "medium"

    def get_market_trend(self, market_id: str) -> Optional[Dict[str, Any]]:
        """
        获取指定市场的趋势

        Args:
            market_id: 市场ID

        Returns:
            趋势信息或None
        """
        history = self.price_history.get(market_id)

        if not history or len(history) < self.trend_window:
            return None

        return self._analyze_trend(history)

    def scan_trending_markets(self, markets: List[Dict[str, Any]],
                            limit: int = 10) -> List[Dict[str, Any]]:
        """
        扫描有趋势的市场

        Args:
            markets: 市场列表
            limit: 返回数量限制

        Returns:
            有趋势的市场列表
        """
        trending_markets = []

        for market in markets:
            analysis = self.analyze(market)

            if analysis.get("action") in ["buy", "sell"]:
                trending_markets.append({
                    "market_id": market.get("marketId"),
                    "question": market.get("question"),
                    "signal": analysis["signal"],
                    "strategy": "trend"
                })

        # 按趋势强度排序
        trending_markets.sort(
            key=lambda x: x["signal"].metadata.get("trend_strength", 0),
            reverse=True
        )

        return trending_markets[:limit]
