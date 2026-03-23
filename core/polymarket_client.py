"""
Polymarket API Client
集成polyclaw的Polymarket API访问
"""

import os
from typing import Dict, Any, List, Optional
import requests


class PolymarketClient:
    """Polymarket API客户端"""

    def __init__(self, gamma_api_url: str, chainstack_node: Optional[str] = None):
        """
        Args:
            gamma_api_url: Gamma API URL
            chainstack_node: Polygon RPC节点（可选，用于链上查询）
        """
        self.gamma_api_url = gamma_api_url
        self.chainstack_node = chainstack_node
        self.session = requests.Session()

    def get_markets(self, limit: int = 100, offset: int = 0,
                    active: bool = True, order_by: str = "volume_24h") -> List[Dict[str, Any]]:
        """
        获取市场列表

        Args:
            limit: 返回数量限制
            offset: 偏移量
            active: 是否只返回活跃市场
            order_by: 排序字段

        Returns:
            市场列表
        """
        try:
            params = {
                "limit": limit,
                "offset": offset,
                "order_by": order_by
            }

            if active:
                params["active"] = "true"

            response = self.session.get(
                f"{self.gamma_api_url}/markets",
                params=params,
                timeout=30
            )
            response.raise_for_status()

            return response.json().get("markets", [])

        except requests.exceptions.RequestException as e:
            print(f"获取市场列表失败: {str(e)}")
            return []

    def get_market(self, market_id: str) -> Optional[Dict[str, Any]]:
        """
        获取单个市场详情

        Args:
            market_id: 市场ID

        Returns:
            市场详情
        """
        try:
            response = self.session.get(
                f"{self.gamma_api_url}/markets/{market_id}",
                timeout=30
            )
            response.raise_for_status()

            return response.json()

        except requests.exceptions.RequestException as e:
            print(f"获取市场详情失败: {str(e)}")
            return None

    def get_trending_markets(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        获取热门市场（24h成交量排序）

        Args:
            limit: 返回数量

        Returns:
            热门市场列表
        """
        return self.get_markets(limit=limit, order_by="volume_24h")

    def search_markets(self, query: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        搜索市场

        Args:
            query: 搜索关键词
            limit: 返回数量

        Returns:
            匹配的市场列表
        """
        try:
            params = {
                "search": query,
                "limit": limit
            }

            response = self.session.get(
                f"{self.gamma_api_url}/markets",
                params=params,
                timeout=30
            )
            response.raise_for_status()

            return response.json().get("markets", [])

        except requests.exceptions.RequestException as e:
            print(f"搜索市场失败: {str(e)}")
            return []

    def get_orderbook(self, market_id: str, asset_id: str) -> Optional[Dict[str, Any]]:
        """
        获取CLOB订单簿（用于套利检测）

        Args:
            market_id: 市场ID
            asset_id: 资产ID（YES或NO token）

        Returns:
            订单簿数据
        """
        try:
            # 这里需要CLOB API，暂时返回None
            # 实际实现需要py-clob-client
            print(f"获取订单簿: 市场={market_id}, 资产={asset_id}")
            return None

        except Exception as e:
            print(f"获取订单簿失败: {str(e)}")
            return None

    def analyze_market_arbitrage(self, market: Dict[str, Any]) -> Dict[str, Any]:
        """
        分析市场的套利机会

        Args:
            market: 市场数据

        Returns:
            套利分析结果
        """
        try:
            # 提取价格
            outcome_prices = market.get("outcomePrices", {})
            if len(outcome_prices) < 2:
                return {
                    "has_arbitrage": False,
                    "reason": "价格数据不完整"
                }

            yes_price = outcome_prices[0].get("price", 0)
            no_price = outcome_prices[1].get("price", 0)
            price_sum = yes_price + no_price

            # 计算套利空间
            arbitrage_space = 1.0 - price_sum

            # 考虑费用（3.15%）
            fee = 0.0315
            profit_after_fees = arbitrage_space - fee

            # 判断是否有套利机会
            has_arbitrage = profit_after_fees > 0

            result = {
                "market_id": market.get("marketId"),
                "question": market.get("question"),
                "yes_price": yes_price,
                "no_price": no_price,
                "price_sum": price_sum,
                "arbitrage_space": arbitrage_space,
                "fee": fee,
                "profit_after_fees": profit_after_fees,
                "has_arbitrage": has_arbitrage,
                "volume_24h": market.get("volume24h", 0),
                "liquidity_score": self._calculate_liquidity_score(market)
            }

            return result

        except Exception as e:
            return {
                "has_arbitrage": False,
                "reason": f"分析失败: {str(e)}"
            }

    def _calculate_liquidity_score(self, market: Dict[str, Any]) -> float:
        """
        计算流动性分数

        Args:
            market: 市场数据

        Returns:
            流动性分数（0-1）
        """
        volume = market.get("volume24h", 0)

        # 标准化成交量分数
        if volume < 100:
            return 0.2
        elif volume < 1000:
            return 0.5
        elif volume < 10000:
            return 0.8
        else:
            return 1.0

    def scan_for_arbitrage_opportunities(self, markets: List[Dict[str, Any]],
                                      min_profit: float = 0.02) -> List[Dict[str, Any]]:
        """
        扫描多个市场的套利机会

        Args:
            markets: 市场列表
            min_profit: 最小利润率

        Returns:
            套利机会列表
        """
        opportunities = []

        for market in markets:
            analysis = self.analyze_market_arbitrage(market)

            if analysis["has_arbitrage"] and analysis["profit_after_fees"] >= min_profit:
                opportunities.append(analysis)

        # 按利润排序
        opportunities.sort(key=lambda x: x["profit_after_fees"], reverse=True)

        return opportunities

    def find_hedge_pairs(self, markets: List[Dict[str, Any]],
                        min_coverage: float = 0.9) -> List[Dict[str, Any]]:
        """
        查找对冲对（需要LLM分析）

        Args:
            markets: 市场列表
            min_coverage: 最小覆盖度

        Returns:
            可能的对冲对
        """
        # 简化实现：返回相关性高的市场对
        # 实际应该使用LLM分析逻辑关系
        hedge_pairs = []

        # 这里可以使用polyclaw的hedge scan逻辑
        for i, market1 in enumerate(markets):
            for j, market2 in enumerate(markets[i+1:], i+1):
                # 简单判断：问题相似度
                question1 = market1.get("question", "")
                question2 = market2.get("question", "")

                # 如果问题有相似关键词，可能相关
                if self._are_questions_related(question1, question2):
                    hedge_pairs.append({
                        "market1": market1.get("marketId"),
                        "market2": market2.get("marketId"),
                        "confidence": 0.6  # 简化评分
                    })

        return hedge_pairs

    def _are_questions_related(self, question1: str, question2: str) -> bool:
        """
        判断两个问题是否相关

        Args:
            question1: 问题1
            question2: 问题2

        Returns:
            是否相关
        """
        # 简化实现：检查关键词重叠
        words1 = set(question1.lower().split())
        words2 = set(question2.lower().split())

        overlap = words1 & words2

        return len(overlap) > 2

    def get_market_summary(self, market: Dict[str, Any]) -> Dict[str, Any]:
        """
        获取市场摘要（用于LLM分析）

        Args:
            market: 市场数据

        Returns:
            摘要字典
        """
        outcome_prices = market.get("outcomePrices", [])

        summary = {
            "market_id": market.get("marketId"),
            "question": market.get("question"),
            "end_time": market.get("endTimestamp"),
            "volume_24h": market.get("volume24h", 0),
            "liquidity_score": self._calculate_liquidity_score(market),
            "yes_price": outcome_prices[0].get("price", 0) if len(outcome_prices) > 0 else 0,
            "no_price": outcome_prices[1].get("price", 0) if len(outcome_prices) > 1 else 0,
            "price_sum": sum([op.get("price", 0) for op in outcome_prices]),
            "slug": market.get("slug", "")
        }

        return summary
