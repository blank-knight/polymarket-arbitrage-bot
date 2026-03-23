"""
套利策略
检测并执行价格套利机会
"""

from typing import Dict, Any, Optional
from .base_strategy import BaseStrategy, TradingSignal


class ArbitrageStrategy(BaseStrategy):
    """套利策略 - 检测价格偏差并执行套利"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__("arbitrage", config)

        # 套利参数
        self.min_arbitrage_space = config.get("min_arbitrage_space", 0.03)  # 3%
        self.max_arbitrage_space = config.get("max_arbitrage_space", 0.20)  # 20%
        self.fee_rate = config.get("fee_rate", 0.0315)  # 3.15% Polymarket费用
        self.min_liquidity_score = config.get("min_liquidity_score", 0.5)  # 最小流动性

    def generate_signal(self, market_data: Dict[str, Any],
                       context: Optional[Dict[str, Any]] = None) -> Optional[TradingSignal]:
        """
        生成套利信号

        Args:
            market_data: 市场数据，包含价格信息
            context: 额外上下文

        Returns:
            套利信号或None
        """
        # 提取价格
        outcome_prices = market_data.get("outcomePrices", [])
        if len(outcome_prices) < 2:
            return None

        yes_price = outcome_prices[0].get("price", 0)
        no_price = outcome_prices[1].get("price", 0)

        # 计算价格总和
        price_sum = yes_price + no_price

        # 计算套利空间
        arbitrage_space = 1.0 - price_sum

        # 计算利润（扣除费用）
        profit_after_fees = arbitrage_space - self.fee_rate

        # 检查套利空间是否在目标范围内
        if profit_after_fees < self.min_arbitrage_space:
            return None

        if profit_after_fees > self.max_arbitrage_space:
            # 套利空间过大，可能是数据错误或异常情况
            self.logger.warning(f"套利空间过大: {profit_after_fees:.2%}")
            return None

        # 检查流动性
        liquidity_score = market_data.get("liquidity_score", 0)
        if liquidity_score < self.min_liquidity_score:
            self.logger.warning(f"流动性不足: {liquidity_score}")
            return None

        # 检查成交量
        volume_24h = market_data.get("volume_24h", 0)
        if volume_24h < 100:  # 最小24h成交量
            self.logger.warning(f"成交量过低: {volume_24h}")
            return None

        # 计算仓位大小（基于可用资金和风险控制）
        position_size = self._calculate_position_size(market_data, profit_after_fees)

        # 信心评分（基于套利空间和流动性）
        confidence = self._calculate_confidence(arbitrage_space, liquidity_score)

        # 确定方向（哪个价格更低）
        if yes_price < no_price:
            # 买YES更便宜
            outcome = "YES"
            price = yes_price
            reasoning = f"YES价格偏低({yes_price:.3f})，套利空间{arbitrage_space:.2%}，预期利润{profit_after_fees:.2%}"
        else:
            # 买NO更便宜
            outcome = "NO"
            price = no_price
            reasoning = f"NO价格偏低({no_price:.3f})，套利空间{arbitrage_space:.2%}，预期利润{profit_after_fees:.2%}"

        # 创建套利信号
        return TradingSignal(
            signal_type="buy",
            market_id=market_data.get("marketId", ""),
            outcome=outcome,
            price=price,
            amount=position_size,
            confidence=confidence,
            reasoning=reasoning,
            risk_level="low",
            timestamp=datetime.now(),
            metadata={
                "arbitrage_space": arbitrage_space,
                "profit_after_fees": profit_after_fees,
                "liquidity_score": liquidity_score,
                "volume_24h": volume_24h
            }
        )

    def validate_signal(self, signal: TradingSignal) -> bool:
        """验证套利信号"""
        # 检查市场ID
        if not signal.market_id:
            return False

        # 检查价格有效性
        if signal.price <= 0 or signal.price >= 1:
            return False

        # 检查金额
        if signal.amount <= 0 or signal.amount > self.max_position_size:
            return False

        # 检查信心度
        if signal.confidence < 0.5:
            return False

        return True

    def _calculate_position_size(self, market_data: Dict[str, Any],
                                 profit_margin: float) -> float:
        """
        计算仓位大小

        Args:
            market_data: 市场数据
            profit_margin: 利润空间

        Returns:
            仓位大小（USDC）
        """
        # 基础仓位
        base_position = self.max_position_size * 0.3  # 最多使用30%的仓位

        # 根据利润空间调整
        profit_multiplier = min(profit_margin / 0.05, 1.5)  # 最多1.5倍
        adjusted_position = base_position * profit_multiplier

        # 根据流动性调整
        liquidity_score = market_data.get("liquidity_score", 0.5)
        liquidity_multiplier = liquidity_score

        final_position = adjusted_position * liquidity_multiplier

        # 限制在最大仓位内
        return min(final_position, self.max_position_size)

    def _calculate_confidence(self, arbitrage_space: float,
                             liquidity_score: float) -> float:
        """
        计算信心度

        Args:
            arbitrage_space: 套利空间
            liquidity_score: 流动性分数

        Returns:
            信心度（0-1）
        """
        # 套利空间分数（0.03-0.20范围映射到0-1）
        space_score = min(max((arbitrage_space - 0.03) / 0.17, 0), 1)

        # 综合评分
        confidence = (space_score * 0.7 + liquidity_score * 0.3)

        return min(confidence, 1.0)

    def analyze_cross_market_arbitrage(self, markets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        分析跨市场套利机会

        Args:
            markets: 多个市场数据

        Returns:
            套利机会列表
        """
        opportunities = []

        for market in markets:
            signal = self.generate_signal(market)

            if signal:
                opportunities.append({
                    "market_id": market.get("marketId"),
                    "question": market.get("question"),
                    "signal": signal
                })

        # 按利润排序
        opportunities.sort(
            key=lambda x: x["signal"].metadata.get("profit_after_fees", 0),
            reverse=True
        )

        return opportunities

    def scan_opportunities(self, market_data_list: List[Dict[str, Any]],
                          limit: int = 10) -> List[Dict[str, Any]]:
        """
        扫描套利机会

        Args:
            market_data_list: 市场数据列表
            limit: 返回数量限制

        Returns:
            套利机会列表
        """
        all_opportunities = []

        for market_data in market_data_list:
            analysis = self.analyze(market_data)

            if analysis.get("action") == "buy":
                all_opportunities.append({
                    "market_id": market_data.get("marketId"),
                    "question": market_data.get("question"),
                    "signal": analysis["signal"],
                    "strategy": "arbitrage"
                })

        # 按利润排序
        all_opportunities.sort(
            key=lambda x: x["signal"].metadata.get("profit_after_fees", 0),
            reverse=True
        )

        return all_opportunities[:limit]
