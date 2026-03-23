"""
对冲执行器
负责对冲交易的完整执行流程
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import logging
from dataclasses import dataclass
from .hedge_strategy import HedgeStrategy
from .base_strategy import TradingSignal
from core.llm_client import LLMAnalyst
from core.state_manager import StateManager


@dataclass
class HedgePair:
    """对冲对"""
    market1_id: str
    market2_id: str
    market1_question: str
    market2_question: str
    correlation: float  # 相关性 0-1
    coverage_ratio: float  # 覆盖度 0-1
    direction: str  # 'long', 'short', 'neutral'
    position_size: float  # USDC
    expected_profit: float
    hedge_cost: float
    risk_level: str
    confidence: float
    reasoning: str

    def is_valid(self) -> bool:
        """检查对冲对是否有效"""
        return (
            self.correlation > 0.7 and
            self.coverage_ratio > 0.8 and
            self.direction != "neutral" and
            self.confidence > 0.6
        )


@dataclass
class HedgeExecutionResult:
    """对冲执行结果"""
    success: bool
    hedge_pair: HedgePair
    trades: List[Dict[str, Any]]
    total_cost: float
    expected_profit: float
    error: Optional[str] = None
    execution_time: float = 0.0


class HedgeExecutor:
    """对冲执行器"""

    def __init__(self, state_manager: StateManager, config: Dict[str, Any]):
        self.state_manager = state_manager
        self.config = config
        self.logger = logging.getLogger("hedge_executor")

        # LLM 分析客户端
        llm_config = config.get("llm", {})
        self.llm_client = LLMAnalyst(
            api_key=llm_config.get("api_key", ""),
            model=llm_config.get("model", "nvidia/nemotron-nano-9b-v2:free")
        )

        # 对冲策略
        self.hedge_strategy = HedgeStrategy(config.get("hedge_strategy", {}))

        # 执行参数
        self.auto_execute = config.get("auto_execute", False)
        self.max_hedge_cost = config.get("max_hedge_cost", 0.05)  # 5%最大对冲成本
        self.min_hedge_profit = config.get("min_hedge_profit", 0.01)  # 1%最小利润

        # 交易记录
        self.hedge_history: List[HedgeExecutionResult] = []

    def discover_hedge_pairs(self, markets: List[Dict[str, Any]]) -> List[HedgePair]:
        """
        发现对冲对

        Args:
            markets: 市场列表

        Returns:
            对冲对列表
        """
        hedge_pairs = []

        self.logger.info(f"分析 {len(markets)} 个市场，寻找对冲对...")

        # 使用 LLM 进行深度分析
        llm_analysis = self._analyze_market_correlations(markets)

        if not llm_analysis or "hedge_pairs" not in llm_analysis:
            self.logger.warning("LLM 未能提供对冲对分析")
            return []

        # 构建 HedgePair 对象
        for pair_data in llm_analysis["hedge_pairs"]:
            try:
                hedge_pair = self._build_hedge_pair_from_llm(markets, pair_data)
                if hedge_pair and hedge_pair.is_valid():
                    hedge_pairs.append(hedge_pair)
            except Exception as e:
                self.logger.error(f"构建对冲对失败: {e}")

        # 按利润排序
        hedge_pairs.sort(key=lambda x: x.expected_profit, reverse=True)

        self.logger.info(f"发现 {len(hedge_pairs)} 个有效对冲对")

        return hedge_pairs

    def _analyze_market_correlations(self, markets: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        使用 LLM 分析市场相关性

        Args:
            markets: 市场列表

        Returns:
            LLM 分析结果
        """
        # 准备市场数据摘要
        market_summaries = []

        for market in markets:
            summary = {
                "market_id": market.get("marketId"),
                "question": market.get("question"),
                "end_time": market.get("endTimestamp"),
                "volume_24h": market.get("volume24h", 0),
                "yes_price": 0,
                "no_price": 0
            }

            # 提取价格
            outcome_prices = market.get("outcomePrices", [])
            if len(outcome_prices) >= 2:
                summary["yes_price"] = outcome_prices[0].get("price", 0)
                summary["no_price"] = outcome_prices[1].get("price", 0)

            market_summaries.append(summary)

        # 构建 LLM 提示
        prompt = self._build_hedge_analysis_prompt(market_summaries)

        try:
            # 调用 LLM
            analysis = self.llm_client.analyze_hedge_opportunities(
                markets=market_summaries,
                prompt=prompt
            )

            return analysis

        except Exception as e:
            self.logger.error(f"LLM 分析失败: {e}")
            return None

    def _build_hedge_analysis_prompt(self, market_summaries: List[Dict[str, Any]]) -> str:
        """
        构建对冲分析提示

        Args:
            market_summaries: 市场摘要列表

        Returns:
            提示文本
        """
        prompt = """分析以下预测市场，找出可以用于对冲的交易对。

任务目标：
1. 找出相关问题（相同主题、相关事件）
2. 计算市场对的相关性（0-1，越高越好）
3. 计算对冲覆盖度（如果市场1 YES，市场2 NO，总覆盖度 = YES价格 + NO价格）
4. 评估风险和利润潜力
5. 推荐交易方向（long做多, short做空, neutral中性）

市场数据：
"""

        for i, market in enumerate(market_summaries[:20]):  # 限制数量
            prompt += f"""
{i+1}. ID: {market['market_id']}
   问题: {market['question']}
   YES价格: {market['yes_price']:.3f}
   NO价格: {market['no_price']:.3f}
   成交量: {market['volume_24h']}
"""

        prompt += """
请以JSON格式返回结果，格式如下：
{
    "hedge_pairs": [
        {
            "market1_id": "市场1 ID",
            "market2_id": "市场2 ID",
            "correlation": 0.95,
            "coverage_ratio": 0.92,
            "direction": "long",
            "expected_profit": 0.025,
            "hedge_cost": 0.02,
            "risk_level": "low",
            "confidence": 0.85,
            "reasoning": "分析理由"
        }
    ]
}

只返回前10个最佳对冲对。
"""
        return prompt

    def _build_hedge_pair_from_llm(self, markets: List[Dict[str, Any]],
                                   llm_pair: Dict[str, Any]) -> Optional[HedgePair]:
        """
        从 LLM 分析结果构建 HedgePair

        Args:
            markets: 市场列表
            llm_pair: LLM 提供的对冲对数据

        Returns:
            HedgePair 对象
        """
        # 查找市场
        market1 = next((m for m in markets if m.get("marketId") == llm_pair.get("market1_id")), None)
        market2 = next((m for m in markets if m.get("marketId") == llm_pair.get("market2_id")), None)

        if not market1 or not market2:
            return None

        # 提取价格
        prices1 = market1.get("outcomePrices", [])
        prices2 = market2.get("outcomePrices", [])

        if len(prices1) < 1 or len(prices2) < 1:
            return None

        # 计算仓位大小
        position_size = self._calculate_hedge_position_size(market1, market2, llm_pair)

        return HedgePair(
            market1_id=llm_pair.get("market1_id"),
            market2_id=llm_pair.get("market2_id"),
            market1_question=market1.get("question", ""),
            market2_question=market2.get("question", ""),
            correlation=llm_pair.get("correlation", 0.7),
            coverage_ratio=llm_pair.get("coverage_ratio", 0.8),
            direction=llm_pair.get("direction", "neutral"),
            position_size=position_size,
            expected_profit=llm_pair.get("expected_profit", 0),
            hedge_cost=llm_pair.get("hedge_cost", 0),
            risk_level=llm_pair.get("risk_level", "medium"),
            confidence=llm_pair.get("confidence", 0.5),
            reasoning=llm_pair.get("reasoning", "")
        )

    def _calculate_hedge_position_size(self, market1: Dict[str, Any],
                                      market2: Dict[str, Any],
                                      llm_pair: Dict[str, Any]) -> float:
        """
        计算对冲仓位大小

        Args:
            market1: 市场1
            market2: 市场2
            llm_pair: LLM 分析结果

        Returns:
            仓位大小（USDC）
        """
        # 基础仓位
        base_position = self.hedge_strategy.max_position_size * 0.4

        # 根据利润调整
        profit = llm_pair.get("expected_profit", 0)
        profit_multiplier = min(profit / 0.03, 1.2)
        adjusted_position = base_position * profit_multiplier

        # 根据流动性调整
        liquidity1 = market1.get("liquidity_score", 0.5)
        liquidity2 = market2.get("liquidity_score", 0.5)
        avg_liquidity = (liquidity1 + liquidity2) / 2

        final_position = adjusted_position * avg_liquidity

        return min(final_position, self.hedge_strategy.max_position_size)

    def evaluate_hedge_pair(self, hedge_pair: HedgePair) -> Dict[str, Any]:
        """
        评估对冲对

        Args:
            hedge_pair: 对冲对

        Returns:
            评估结果
        """
        # 基础验证
        if not hedge_pair.is_valid():
            return {
                "recommend": "skip",
                "reason": "对冲对未通过基础验证"
            }

        # 成本检查
        if hedge_pair.hedge_cost > self.max_hedge_cost:
            return {
                "recommend": "skip",
                "reason": f"对冲成本过高: {hedge_pair.hedge_cost:.2%} > {self.max_hedge_cost:.2%}"
            }

        # 利润检查
        if hedge_pair.expected_profit < self.min_hedge_profit:
            return {
                "recommend": "skip",
                "reason": f"预期利润过低: {hedge_pair.expected_profit:.2%} < {self.min_hedge_profit:.2%}"
            }

        # 风险检查
        if hedge_pair.risk_level == "high":
            return {
                "recommend": "skip",
                "reason": "风险等级过高"
            }

        # 综合评分
        score = (
            hedge_pair.correlation * 0.3 +
            hedge_pair.coverage_ratio * 0.3 +
            hedge_pair.confidence * 0.2 +
            min(hedge_pair.expected_profit / 0.05, 1) * 0.2
        )

        recommendation = "execute" if score >= 0.7 else "skip"

        return {
            "recommend": recommendation,
            "score": score,
            "reasoning": hedge_pair.reasoning
        }

    def execute_hedge(self, hedge_pair: HedgePair,
                     web3_trader: Any) -> HedgeExecutionResult:
        """
        执行对冲交易

        Args:
            hedge_pair: 对冲对
            web3_trader: Web3 交易客户端

        Returns:
            执行结果
        """
        start_time = datetime.now()

        try:
            self.logger.info(f"开始执行对冲: {hedge_pair.market1_id} <-> {hedge_pair.market2_id}")

            # 评估是否应该执行
            evaluation = self.evaluate_hedge_pair(hedge_pair)
            if evaluation["recommend"] != "execute":
                if not self.auto_execute:
                    self.logger.info(f"对冲未通过评估: {evaluation['reason']}")
                    return HedgeExecutionResult(
                        success=False,
                        hedge_pair=hedge_pair,
                        trades=[],
                        total_cost=0,
                        expected_profit=0,
                        error=f"评估未通过: {evaluation['reason']}"
                    )

            # 确定交易方向
            if hedge_pair.direction == "long":
                # 做多：买市场1 YES，买市场2 NO（如果相关）
                trades = self._execute_long_hedge(hedge_pair, web3_trader)
            elif hedge_pair.direction == "short":
                # 做空：买市场1 NO，买市场2 YES（如果相关）
                trades = self._execute_short_hedge(hedge_pair, web3_trader)
            else:
                return HedgeExecutionResult(
                    success=False,
                    hedge_pair=hedge_pair,
                    trades=[],
                    total_cost=0,
                    expected_profit=0,
                    error="无效的方向: neutral"
                )

            # 计算总成本
            total_cost = sum(t.get("cost", 0) for t in trades)

            # 检查是否有失败交易
            failed_trades = [t for t in trades if not t.get("success", False)]

            if failed_trades:
                error_msg = f"部分交易失败: {len(failed_trades)}/{len(trades)}"
                self.logger.error(error_msg)
                return HedgeExecutionResult(
                    success=False,
                    hedge_pair=hedge_pair,
                    trades=trades,
                    total_cost=total_cost,
                    expected_profit=hedge_pair.expected_profit,
                    error=error_msg
                )

            # 成功
            execution_time = (datetime.now() - start_time).total_seconds()

            result = HedgeExecutionResult(
                success=True,
                hedge_pair=hedge_pair,
                trades=trades,
                total_cost=total_cost,
                expected_profit=hedge_pair.expected_profit,
                execution_time=execution_time
            )

            # 记录到历史
            self.hedge_history.append(result)

            # 保存到状态管理器
            self._save_hedge_to_state(result)

            self.logger.info(f"对冲执行成功，成本: {total_cost:.2f} USDC，预期利润: {hedge_pair.expected_profit:.2%}")

            return result

        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            self.logger.error(f"对冲执行异常: {e}")

            return HedgeExecutionResult(
                success=False,
                hedge_pair=hedge_pair,
                trades=[],
                total_cost=0,
                expected_profit=0,
                error=str(e),
                execution_time=execution_time
            )

    def _execute_long_hedge(self, hedge_pair: HedgePair,
                           web3_trader: Any) -> List[Dict[str, Any]]:
        """
        执行做多对冲

        Args:
            hedge_pair: 对冲对
            web3_trader: Web3 交易客户端

        Returns:
            交易结果列表
        """
        trades = []

        # 交易1：市场1 YES
        trade1 = web3_trader.execute_trade(
            market_id=hedge_pair.market1_id,
            amount_usdc=hedge_pair.position_size,
            outcome="YES"
        )

        trades.append({
            "market_id": hedge_pair.market1_id,
            "outcome": "YES",
            "amount": hedge_pair.position_size,
            "cost": hedge_pair.position_size,
            "success": "error" not in trade1,
            "tx_hash": trade1.get("split_hash", ""),
            "details": trade1
        })

        # 交易2：市场2 NO（如果覆盖度允许）
        if hedge_pair.coverage_ratio < 1.0:
            amount2 = hedge_pair.position_size * (1 - hedge_pair.coverage_ratio)
            if amount2 > 1:  # 最小1 USDC
                trade2 = web3_trader.execute_trade(
                    market_id=hedge_pair.market2_id,
                    amount_usdc=amount2,
                    outcome="NO"
                )

                trades.append({
                    "market_id": hedge_pair.market2_id,
                    "outcome": "NO",
                    "amount": amount2,
                    "cost": amount2,
                    "success": "error" not in trade2,
                    "tx_hash": trade2.get("split_hash", ""),
                    "details": trade2
                })

        return trades

    def _execute_short_hedge(self, hedge_pair: HedgePair,
                            web3_trader: Any) -> List[Dict[str, Any]]:
        """
        执行做空对冲

        Args:
            hedge_pair: 对冲对
            web3_trader: Web3 交易客户端

        Returns:
            交易结果列表
        """
        trades = []

        # 交易1：市场1 NO
        trade1 = web3_trader.execute_trade(
            market_id=hedge_pair.market1_id,
            amount_usdc=hedge_pair.position_size,
            outcome="NO"
        )

        trades.append({
            "market_id": hedge_pair.market1_id,
            "outcome": "NO",
            "amount": hedge_pair.position_size,
            "cost": hedge_pair.position_size,
            "success": "error" not in trade1,
            "tx_hash": trade1.get("split_hash", ""),
            "details": trade1
        })

        # 交易2：市场2 YES（如果覆盖度允许）
        if hedge_pair.coverage_ratio < 1.0:
            amount2 = hedge_pair.position_size * (1 - hedge_pair.coverage_ratio)
            if amount2 > 1:  # 最小1 USDC
                trade2 = web3_trader.execute_trade(
                    market_id=hedge_pair.market2_id,
                    amount_usdc=amount2,
                    outcome="YES"
                )

                trades.append({
                    "market_id": hedge_pair.market2_id,
                    "outcome": "YES",
                    "amount": amount2,
                    "cost": amount2,
                    "success": "error" not in trade2,
                    "tx_hash": trade2.get("split_hash", ""),
                    "details": trade2
                })

        return trades

    def _save_hedge_to_state(self, result: HedgeExecutionResult):
        """
        保存对冲结果到状态管理器

        Args:
            result: 执行结果
        """
        try:
            hedge_data = {
                "market1_id": result.hedge_pair.market1_id,
                "market2_id": result.hedge_pair.market2_id,
                "direction": result.hedge_pair.direction,
                "total_cost": result.total_cost,
                "expected_profit": result.expected_profit,
                "success": result.success,
                "execution_time": result.execution_time,
                "trades_count": len(result.trades),
                "timestamp": datetime.now().isoformat()
            }

            # 保存到机会记录
            self.state_manager.save_opportunity({
                "market_id": f"{result.hedge_pair.market1_id}_{result.hedge_pair.market2_id}",
                "opportunity_type": "hedge",
                "status": "executed" if result.success else "failed",
                "analysis_data": hedge_data
            })

        except Exception as e:
            self.logger.error(f"保存对冲记录失败: {e}")

    def get_hedge_history(self, limit: int = 20) -> List[HedgeExecutionResult]:
        """
        获取对冲历史记录

        Args:
            limit: 返回数量限制

        Returns:
            历史记录列表
        """
        return self.hedge_history[-limit:]

    def get_hedge_performance(self) -> Dict[str, Any]:
        """
        获取对冲策略表现

        Returns:
            表现统计
        """
        if not self.hedge_history:
            return {
                "total_hedges": 0,
                "success_rate": 0,
                "total_cost": 0,
                "total_expected_profit": 0
            }

        total = len(self.hedge_history)
        successful = sum(1 for h in self.hedge_history if h.success)
        total_cost = sum(h.total_cost for h in self.hedge_history)
        total_profit = sum(h.expected_profit * h.total_cost for h in self.hedge_history if h.success)

        return {
            "total_hedges": total,
            "successful_hedges": successful,
            "success_rate": successful / total if total > 0 else 0,
            "total_cost": total_cost,
            "total_expected_profit": total_profit,
            "avg_execution_time": sum(h.execution_time for h in self.hedge_history) / total if total > 0 else 0
        }
