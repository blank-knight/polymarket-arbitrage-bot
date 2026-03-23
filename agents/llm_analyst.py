"""
LLM Analyst Agent
负责市场分析、趋势预测、风险评估
"""

import os
from typing import Dict, Any
from core.agent_base import BaseAgent
from core.state_manager import StateManager
from core.llm_client import LLMAnalyst


class LLMAnalystAgent(BaseAgent):
    """LLM分析师"""

    def __init__(self, state_manager: StateManager, config: Dict[str, Any]):
        super().__init__("llm_analyst", state_manager, config)

        # 获取LLM配置
        openrouter_key = os.getenv("OPENROUTER_API_KEY", "")

        model = config.get("model", "nvidia/nemotron-nano-9b-v2:free")
        self.max_analysis_time = config.get("max_analysis_time", 30)

        # 初始化LLM客户端
        self.llm_client = LLMAnalyst(
            api_key=openrouter_key,
            model=model
        )

    def run(self):
        """主运行循环"""
        if not self.check_enabled():
            return

        self.set_status("running")
        self.log("INFO", "LLM分析师启动...")

        try:
            while True:
                # 处理待分析的队列
                self._process_analysis_queue()

                # 检查新消息
                messages = self.get_messages(message_type="opportunity")

                for message in messages:
                    self._analyze_opportunity(message["message_data"])

                    # 标记为已处理
                    self.state_manager.mark_message_processed(message["id"])

                # 处理对冲对分析
                hedge_messages = self.get_messages(message_type="hedge_pair")

                for message in hedge_messages:
                    self._analyze_hedge_pair(message["message_data"])

                    # 标记为已处理
                    self.state_manager.mark_message_processed(message["id"])

                # 处理市场分析请求
                analysis_messages = self.get_messages(message_type="market_analysis")

                for message in analysis_messages:
                    self._analyze_market(message["message_data"])

                    # 标记为已处理
                    self.state_manager.mark_message_processed(message["id"])

        except KeyboardInterrupt:
            self.set_status("stopped")
            self.log("INFO", "LLM分析师停止")

    def _process_analysis_queue(self):
        """处理分析队列"""
        try:
            # 获取待处理的机会
            opportunities = self.state_manager.get_pending_opportunities(limit=5)

            if not opportunities:
                return

            self.log("INFO", f"处理{len(opportunities)}个待分析机会...")

            for opp in opportunities:
                analysis_result = self._analyze_with_llm(opp)

                # 更新机会状态
                if analysis_result.get("opportunity_type") != "none":
                    self.state_manager.update_opportunity_status(
                        opportunity_id=opp["id"],
                        status="analyzed"
                    )

                    # 通知策略执行员
                    self.send_message(
                        to_agent="strategy_executor",
                        message_type="trading_opportunity",
                        message_data={
                            "opportunity_id": opp["id"],
                            "market_id": opp["market_id"],
                            "analysis": analysis_result
                        }
                    )
                else:
                    # 无机会，标记为跳过
                    self.state_manager.update_opportunity_status(
                        opportunity_id=opp["id"],
                        status="skipped"
                    )

        except Exception as e:
            self.log("ERROR", f"处理分析队列失败: {str(e)}")

    def _analyze_opportunity(self, opportunity_data: Dict[str, Any]):
        """
        分析套利机会

        Args:
            opportunity_data: 机会数据
        """
        try:
            # 发送给LLM进行深度分析
            analysis = self.llm_client.analyze_market(opportunity_data)

            self.log("INFO", f"分析机会 {opportunity_data.get('market_id')}: {analysis.get('opportunity_type', 'none')}")

            # 保存分析结果
            self._update_state_field(
                f"analysis_{opportunity_data.get('market_id')}",
                analysis
            )

        except Exception as e:
            self.log("ERROR", f"分析机会失败: {str(e)}")

    def _analyze_hedge_pair(self, hedge_pair_data: Dict[str, Any]):
        """
        分析对冲对

        Args:
            hedge_pair_data: 对冲对数据
        """
        try:
            # 这里需要获取两个市场的完整数据
            # 简化实现，实际应该从Polymarket API获取
            market1 = {"market_id": hedge_pair_data.get("market1")}
            market2 = {"market_id": hedge_pair_data.get("market2")}

            analysis = self.llm_client.analyze_hedge_opportunity(market1, market2)

            self.log("INFO", f"分析对冲对: 覆盖度={analysis.get('coverage_percentage', 0)}%")

            # 如果是有效对冲，通知策略执行员
            if analysis.get("is_hedge"):
                self.send_message(
                    to_agent="strategy_executor",
                    message_type="hedge_opportunity",
                    message_data={
                        "analysis": analysis
                    }
                )

        except Exception as e:
            self.log("ERROR", f"分析对冲对失败: {str(e)}")

    def _analyze_market(self, market_data: Dict[str, Any]):
        """
        分析指定市场

        Args:
            market_data: 市场数据
        """
        try:
            analysis = self.llm_client.analyze_market(market_data)

            self.log("INFO", f"分析市场 {market_data.get('market_id')}: 风险={analysis.get('risk_level', 'unknown')}")

            # 保存分析结果
            self._update_state_field(
                f"market_analysis_{market_data.get('market_id')}",
                analysis
            )

        except Exception as e:
            self.log("ERROR", f"分析市场失败: {str(e)}")

    def _analyze_with_llm(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """
        用LLM分析机会

        Args:
            opportunity: 机会数据

        Returns:
            分析结果
        """
        try:
            market_summary = {
                "market_id": opportunity.get("market_id"),
                "question": "",  # 从market_data获取
                "yes_price": opportunity.get("yes_price", 0),
                "no_price": opportunity.get("no_price", 0),
                "price_sum": opportunity.get("price_sum", 0),
                "volume_24h": opportunity.get("volume_24h", 0),
                "liquidity_score": opportunity.get("liquidity_score", 0)
            }

            analysis = self.llm_client.analyze_market(market_summary)

            # 如果LLM推荐策略，获取策略详情
            if analysis.get("recommended_strategy"):
                strategy_recommendation = self.llm_client.recommend_strategy(
                    market_data=market_summary,
                    opportunity_type=analysis.get("opportunity_type", "speculation")
                )

                # 合并策略推荐
                analysis["strategy_recommendation"] = strategy_recommendation

            return analysis

        except Exception as e:
            self.log("ERROR", f"LLM分析失败: {str(e)}")
            return {
                "opportunity_type": "none",
                "risk_level": "high",
                "reasoning": f"分析失败: {str(e)}"
            }

    def process_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """处理收到的消息"""
        message_type = message.get("message_type", "")
        message_data = message.get("message_data", {})

        response = {
            "status": "processed",
            "data": {}
        }

        if message_type == "analysis_request":
            # 用户请求分析特定市场
            market_id = message_data.get("market_id")
            market = message_data.get("market_data")

            if market:
                analysis = self._analyze_market(market)
                response["data"]["analysis"] = analysis

        elif message_type == "status_request":
            # 用户请求状态
            response["data"] = self.state["data"]

        else:
            response["data"]["message"] = "未知的消息类型"

        return response

    def _init_default_state(self) -> Dict[str, Any]:
        """初始化默认状态"""
        return {
            "status": "idle",
            "last_run": None,
            "data": {
                "opportunities_analyzed": 0,
                "hedges_found": 0,
                "last_analysis_time": None
            }
        }
