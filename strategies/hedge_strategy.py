"""
对冲策略
查找并执行对冲交易以降低风险
"""

from typing import Dict, Any, Optional, List
from .base_strategy import BaseStrategy, TradingSignal


class HedgeStrategy(BaseStrategy):
    """对冲策略 - 降低风险的组合交易"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__("hedge", config)

        # 对冲参数
        self.min_coverage_ratio = config.get("min_coverage_ratio", 0.90)  # 90%覆盖度
        self.max_correlation_cost = config.get("max_correlation_cost", 0.05)  # 5%对冲成本
        self.min_hedge_profit = config.get("min_hedge_profit", 0.01)  # 1%最小利润

    def generate_signal(self, market_data: Dict[str, Any],
                       context: Optional[Dict[str, Any]] = None) -> Optional[TradingSignal]:
        """
        生成对冲信号（单市场分析，不生成信号）
        对冲需要至少两个市场，此方法返回None

        Args:
            market_data: 市场数据
            context: 额外上下文

        Returns:
            None（对冲需要多市场分析）
        """
        # 对冲策略不直接从单个市场生成信号
        # 需要使用 find_hedge_pairs 方法查找对冲对
        return None

    def validate_signal(self, signal: TradingSignal) -> bool:
        """验证对冲信号"""
        # 对冲信号需要额外的验证
        return True

    def find_hedge_pairs(self, markets: List[Dict[str, Any]],
                        llm_analysis: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        查找对冲对

        Args:
            markets: 市场列表
            llm_analysis: LLM分析结果（包含相关性判断）

        Returns:
            对冲对列表
        """
        hedge_pairs = []

        # 如果有LLM分析，使用LLM提供的对冲对
        if llm_analysis and "hedge_pairs" in llm_analysis:
            for pair_data in llm_analysis["hedge_pairs"]:
                if pair_data.get("is_valid", False):
                    hedge_pair = self._build_hedge_pair(
                        markets,
                        pair_data["market1_id"],
                        pair_data["market2_id"],
                        pair_data
                    )
                    if hedge_pair:
                        hedge_pairs.append(hedge_pair)
            return hedge_pairs

        # 如果没有LLM分析，使用简单的相似度匹配
        for i, market1 in enumerate(markets):
            for j, market2 in enumerate(markets[i+1:], i+1):
                pair = self._check_hedge_opportunity(market1, market2)
                if pair:
                    hedge_pairs.append(pair)

        # 按利润排序
        hedge_pairs.sort(key=lambda x: x.get("profit_potential", 0), reverse=True)

        return hedge_pairs

    def _check_hedge_opportunity(self, market1: Dict[str, Any],
                               market2: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        检查两个市场是否有对冲机会

        Args:
            market1: 市场1
            market2: 市场2

        Returns:
            对冲对信息或None
        """
        # 检查问题相似度
        question1 = market1.get("question", "").lower()
        question2 = market2.get("question", "").lower()

        # 简单的相似度检查（实际应该使用LLM）
        similarity = self._calculate_similarity(question1, question2)

        if similarity < 0.6:  # 相似度阈值
            return None

        # 提取价格
        prices1 = market1.get("outcomePrices", [])
        prices2 = market2.get("outcomePrices", [])

        if len(prices1) < 2 or len(prices2) < 2:
            return None

        # 检查价格差异
        yes_diff = abs(prices1[0].get("price", 0) - prices2[0].get("price", 0))
        no_diff = abs(prices1[1].get("price", 0) - prices2[1].get("price", 0))

        # 如果价格差异足够大，可能存在套利机会
        avg_diff = (yes_diff + no_diff) / 2

        if avg_diff < self.min_hedge_profit:
            return None

        # 计算对冲成本
        hedge_cost = avg_diff

        # 计算利润潜力
        profit_potential = avg_diff - self.fee_rate * 2  # 两个市场的费用

        if profit_potential < self.min_hedge_profit:
            return None

        # 检查流动性
        liquidity1 = market1.get("liquidity_score", 0)
        liquidity2 = market2.get("liquidity_score", 0)

        if liquidity1 < self.min_liquidity_score or liquidity2 < self.min_liquidity_score:
            return None

        # 确定交易方向
        trade1_direction = "buy" if prices1[0].get("price", 0) < prices2[0].get("price", 0) else "sell"
        trade2_direction = "sell" if trade1_direction == "buy" else "buy"

        return {
            "market1_id": market1.get("marketId"),
            "market2_id": market2.get("marketId"),
            "market1_question": market1.get("question"),
            "market2_question": market2.get("question"),
            "similarity": similarity,
            "trade1_direction": trade1_direction,
            "trade2_direction": trade2_direction,
            "hedge_cost": hedge_cost,
            "profit_potential": profit_potential,
            "liquidity_score": (liquidity1 + liquidity2) / 2,
            "confidence": min(similarity, 0.9)
        }

    def _build_hedge_pair(self, markets: List[Dict[str, Any]],
                         market1_id: str, market2_id: str,
                         llm_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        基于LLM分析构建对冲对

        Args:
            markets: 市场列表
            market1_id: 市场1 ID
            market2_id: 市场2 ID
            llm_data: LLM分析数据

        Returns:
            对冲对信息或None
        """
        # 查找市场
        market1 = next((m for m in markets if m.get("marketId") == market1_id), None)
        market2 = next((m for m in markets if m.get("marketId") == market2_id), None)

        if not market1 or not market2:
            return None

        # 使用LLM提供的覆盖度和风险信息
        coverage = llm_data.get("coverage_percentage", 0) / 100

        if coverage < self.min_coverage_ratio:
            return None

        # 计算对冲参数
        prices1 = market1.get("outcomePrices", [])
        prices2 = market2.get("outcomePrices", [])

        if len(prices1) < 1 or len(prices2) < 1:
            return None

        # 确定交易方向（根据LLM推荐）
        direction = llm_data.get("recommended_direction", "neutral")

        if direction == "neutral":
            return None

        # 计算利润
        profit = llm_data.get("profit_potential", 0)

        if profit < self.min_hedge_profit:
            return None

        # 计算仓位大小
        position_size = self._calculate_hedge_position_size(market1, market2, profit)

        return {
            "market1_id": market1_id,
            "market2_id": market2_id,
            "market1_question": market1.get("question"),
            "market2_question": market2.get("question"),
            "direction": direction,
            "position_size": position_size,
            "coverage_ratio": coverage,
            "hedge_cost": llm_data.get("hedge_cost", 0),
            "profit_potential": profit,
            "risk_level": llm_data.get("risk_level", "medium"),
            "confidence": llm_data.get("confidence", 0.5),
            "llm_reasoning": llm_data.get("reasoning", "")
        }

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """
        计算文本相似度（简化版本）

        Args:
            text1: 文本1
            text2: 文本2

        Returns:
            相似度（0-1）
        """
        words1 = set(text1.split())
        words2 = set(text2.split())

        if not words1 or not words2:
            return 0.0

        # Jaccard相似度
        intersection = len(words1 & words2)
        union = len(words1 | words2)

        return intersection / union if union > 0 else 0.0

    def _calculate_hedge_position_size(self, market1: Dict[str, Any],
                                       market2: Dict[str, Any],
                                       profit_potential: float) -> float:
        """
        计算对冲仓位大小

        Args:
            market1: 市场1
            market2: 市场2
            profit_potential: 利润潜力

        Returns:
            仓位大小（USDC）
        """
        # 基础仓位
        base_position = self.max_position_size * 0.4  # 对冲使用40%仓位

        # 根据利润调整
        profit_multiplier = min(profit_potential / 0.03, 1.2)  # 最多1.2倍
        adjusted_position = base_position * profit_multiplier

        # 根据流动性调整
        liquidity1 = market1.get("liquidity_score", 0.5)
        liquidity2 = market2.get("liquidity_score", 0.5)
        avg_liquidity = (liquidity1 + liquidity2) / 2

        final_position = adjusted_position * avg_liquidity

        return min(final_position, self.max_position_size)

    def analyze_hedge_quality(self, hedge_pair: Dict[str, Any]) -> Dict[str, Any]:
        """
        分析对冲质量

        Args:
            hedge_pair: 对冲对数据

        Returns:
            质量分析
        """
        coverage = hedge_pair.get("coverage_ratio", 0)
        profit = hedge_pair.get("profit_potential", 0)
        confidence = hedge_pair.get("confidence", 0)

        # 质量评分
        quality_score = (coverage * 0.4 + confidence * 0.3 + min(profit / 0.05, 1) * 0.3)

        # 风险等级
        if quality_score >= 0.8:
            risk_level = "low"
        elif quality_score >= 0.6:
            risk_level = "medium"
        else:
            risk_level = "high"

        return {
            "quality_score": quality_score,
            "risk_level": risk_level,
            "recommendation": "execute" if quality_score >= 0.6 and risk_level != "high" else "skip",
            "reasoning": f"质量评分{quality_score:.2f}，风险等级{risk_level}"
        }

    def execute_hedge_trade(self, hedge_pair: Dict[str, Any]) -> List[TradingSignal]:
        """
        执行对冲交易

        Args:
            hedge_pair: 对冲对数据

        Returns:
            交易信号列表
        """
        signals = []

        # 市场1的交易信号
        signal1 = TradingSignal(
            signal_type=hedge_pair.get("trade1_direction", "buy"),
            market_id=hedge_pair["market1_id"],
            outcome="YES",  # 简化，实际应该根据分析确定
            price=0.5,  # 需要从市场数据获取
            amount=hedge_pair.get("position_size", 10),
            confidence=hedge_pair.get("confidence", 0.7),
            reasoning=f"对冲交易 - 市场1: {hedge_pair.get('market1_question', '')}",
            risk_level=hedge_pair.get("risk_level", "medium"),
            timestamp=datetime.now(),
            metadata={"hedge_pair_id": f"{hedge_pair['market1_id']}-{hedge_pair['market2_id']}"}
        )

        # 市场2的交易信号
        signal2 = TradingSignal(
            signal_type=hedge_pair.get("trade2_direction", "buy"),
            market_id=hedge_pair["market2_id"],
            outcome="NO",  # 简化
            price=0.5,
            amount=hedge_pair.get("position_size", 10),
            confidence=hedge_pair.get("confidence", 0.7),
            reasoning=f"对冲交易 - 市场2: {hedge_pair.get('market2_question', '')}",
            risk_level=hedge_pair.get("risk_level", "medium"),
            timestamp=datetime.now(),
            metadata={"hedge_pair_id": f"{hedge_pair['market1_id']}-{hedge_pair['market2_id']}"}
        )

        signals.extend([signal1, signal2])

        return signals
