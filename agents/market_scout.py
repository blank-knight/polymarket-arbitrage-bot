"""
Market Scout Agent
负责市场扫描、机会发现、热点追踪
"""

import time
from typing import Dict, Any, List
from core.agent_base import BaseAgent
from core.polymarket_client import PolymarketClient
from core.state_manager import StateManager


class MarketScoutAgent(BaseAgent):
    """市场情报员"""

    def __init__(self, state_manager: StateManager, config: Dict[str, Any],
                 polymarket_client: PolymarketClient):
        super().__init__("market_scout", state_manager, config)

        self.polymarket_client = polymarket_client
        self.scan_interval = config.get("scan_interval", 60)  # 秒
        self.max_markets = config.get("max_markets", 50)
        self.min_volume = config.get("min_volume", 1000)

    def run(self):
        """主运行循环"""
        if not self.check_enabled():
            return

        self.set_status("running")
        self.log("INFO", "市场情报员启动...")

        try:
            while True:
                self._scan_markets()
                time.sleep(self.scan_interval)

        except KeyboardInterrupt:
            self.set_status("stopped")
            self.log("INFO", "市场情报员停止")

    def _scan_markets(self):
        """扫描市场"""
        try:
            # 1. 获取热门市场
            self.log("INFO", f"扫描热门市场（最多{self.max_markets}个）...")

            trending_markets = self.polymarket_client.get_trending_markets(
                limit=self.max_markets
            )

            # 2. 过滤市场
            filtered_markets = self._filter_markets(trending_markets)

            self.log("INFO", f"发现{len(filtered_markets)}个符合条件的市场")

            # 3. 分析套利机会
            opportunities = self.polymarket_client.scan_for_arbitrage_opportunities(
                markets=filtered_markets,
                min_profit=0.02  # 2%最小利润
            )

            self.log("INFO", f"发现{len(opportunities)}个套利机会")

            # 4. 保存机会并发送给LLM分析师
            for opp in opportunities:
                self.state_manager.save_opportunity(
                    market_id=opp["market_id"],
                    opportunity_type="arbitrage",
                    analysis_data=opp
                )

                # 通知LLM分析师
                self.send_message(
                    to_agent="llm_analyst",
                    message_type="opportunity",
                    message_data={
                        "type": "arbitrage",
                        "data": opp
                    }
                )

            # 5. 查找对冲对
            hedge_pairs = self.polymarket_client.find_hedge_pairs(
                markets=filtered_markets,
                min_coverage=0.9
            )

            if hedge_pairs:
                self.log("INFO", f"发现{len(hedge_pairs)}个可能的对冲对")

                for pair in hedge_pairs:
                    self.send_message(
                        to_agent="llm_analyst",
                        message_type="hedge_pair",
                        message_data=pair
                    )

            # 6. 更新状态
            self._update_state_field("scanned_markets", len(filtered_markets))
            self._update_state_field("opportunities_found", len(opportunities))

        except Exception as e:
            self.log("ERROR", f"扫描市场失败: {str(e)}")

    def _filter_markets(self, markets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        过滤市场

        Args:
            markets: 原始市场列表

        Returns:
            过滤后的市场列表
        """
        filtered = []

        for market in markets:
            # 检查成交量
            volume = market.get("volume24h", 0)

            if volume < self.min_volume:
                continue

            # 检查是否活跃
            end_timestamp = market.get("endTimestamp")
            if not end_timestamp:
                continue

            from datetime import datetime

            end_time = datetime.fromisoformat(end_timestamp.replace("Z", "+00:00"))

            if end_time < datetime.now():
                continue

            filtered.append(market)

        return filtered

    def process_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """处理收到的消息"""
        message_type = message.get("message_type", "")
        message_data = message.get("message_data", {})

        response = {
            "status": "processed",
            "data": {}
        }

        if message_type == "scan_request":
            # 用户请求扫描特定市场
            market_ids = message_data.get("market_ids", [])
            self._scan_specific_markets(market_ids)

            response["data"]["message"] = f"已开始扫描{len(market_ids)}个指定市场"

        elif message_type == "status_request":
            # 用户请求状态
            response["data"] = self.state["data"]

        else:
            response["data"]["message"] = "未知的消息类型"

        return response

    def _scan_specific_markets(self, market_ids: List[str]):
        """扫描指定的市场"""
        try:
            self.log("INFO", f"扫描{len(market_ids)}个指定市场...")

            for market_id in market_ids:
                market = self.polymarket_client.get_market(market_id)

                if market:
                    summary = self.polymarket_client.get_market_summary(market)

                    # 发送给LLM分析师
                    self.send_message(
                        to_agent="llm_analyst",
                        message_type="market_analysis",
                        message_data=summary
                    )

            self.log("INFO", "指定市场扫描完成")

        except Exception as e:
            self.log("ERROR", f"扫描指定市场失败: {str(e)}")

    def _init_default_state(self) -> Dict[str, Any]:
        """初始化默认状态"""
        return {
            "status": "idle",
            "last_run": None,
            "data": {
                "scanned_markets": 0,
                "opportunities_found": 0,
                "last_scan_time": None
            }
        }
