"""
LLM Client for Market Analysis
使用OpenRouter API进行市场分析
"""

import os
from typing import Dict, Any, Optional
import requests
import json


class LLMAnalyst:
    """LLM市场分析师"""

    def __init__(self, api_key: str, model: str = "nvidia/nemotron-nano-9b-v2:free"):
        """
        Args:
            api_key: OpenRouter API密钥
            model: 使用的模型
        """
        self.api_key = api_key
        self.model = model
        self.api_url = "https://openrouter.ai/api/v1/chat/completions"

    def analyze_market(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        分析单个市场

        Args:
            market_data: 市场数据字典

        Returns:
            分析结果字典
        """
        prompt = self._build_market_analysis_prompt(market_data)

        response = self._call_llm(prompt)
        return self._parse_analysis_response(response)

    def analyze_hedge_opportunity(self, market1: Dict[str, Any],
                                   market2: Dict[str, Any]) -> Dict[str, Any]:
        """
        分析对冲机会

        Args:
            market1: 第一个市场数据
            market2: 第二个市场数据

        Returns:
            对冲分析结果
        """
        prompt = self._build_hedge_analysis_prompt(market1, market2)

        response = self._call_llm(prompt)
        return self._parse_hedge_response(response)

    def recommend_strategy(self, market_data: Dict[str, Any],
                        opportunity_type: str) -> Dict[str, Any]:
        """
        推荐交易策略

        Args:
            market_data: 市场数据
            opportunity_type: 机会类型（arbitrage, hedge, speculation等）

        Returns:
            策略推荐结果
        """
        prompt = self._build_strategy_recommendation_prompt(market_data, opportunity_type)

        response = self._call_llm(prompt)
        return self._parse_strategy_response(response)

    def _build_market_analysis_prompt(self, market_data: Dict[str, Any]) -> str:
        """构建市场分析提示词"""
        prompt = f"""
        分析这个Polymarket预测市场：

        ## 市场信息
        - 问题：{market_data.get('question', 'N/A')}
        - 市场ID：{market_data.get('market_id', 'N/A')}
        - YES价格：{market_data.get('yes_price', 'N/A')}
        - NO价格：{market_data.get('no_price', 'N/A')}
        - YES+NO：{market_data.get('yes_price', 0) + market_data.get('no_price', 0)}
        - 24h成交量：{market_data.get('volume_24h', 'N/A')}
        - 结束时间：{market_data.get('end_time', 'N/A')}
        - 流动性：{market_data.get('liquidity', 'N/A')}

        ## 分析任务
        请分析以下方面：

        1. **价格合理性**：
           - YES+NO的价格之和是否接近1.0？
           - 如果偏离1.0，偏离幅度是多少？
           - 是否存在明显的套利机会？

        2. **市场流动性**：
           - 成交量是否足够支持交易？
           - 流动性是否均匀分布在YES和NO两端？

        3. **趋势和情绪**：
           - 价格是否呈现明显趋势？
           - 市场情绪是否过度偏向某一方向？

        4. **机会评估**：
           - 是否适合套利？
           - 是否适合对冲？
           - 最优的策略是什么？

        ## 输出格式
        请以JSON格式输出：
        {{
            "price_reasonable": true/false,
            "price_deviation": 0.05,
            "liquidity_adequate": true/false,
            "trend": "bullish/bearish/neutral",
            "sentiment": "overconfident/cautious/balanced",
            "opportunity_type": "arbitrage/hedge/speculation/none",
            "recommended_strategy": "strategy_name",
            "expected_profit_margin": 0.03,
            "risk_level": "low/medium/high",
            "confidence": 0.85,
            "reasoning": "简要说明分析逻辑"
        }}

        请只输出JSON，不要其他文字。
        """
        return prompt

    def _build_hedge_analysis_prompt(self, market1: Dict[str, Any],
                                     market2: Dict[str, Any]) -> str:
        """构建对冲分析提示词"""
        prompt = f"""
        分析这两个市场的对冲机会：

        ## 市场1
        - 问题：{market1.get('question', 'N/A')}
        - YES价格：{market1.get('yes_price', 'N/A')}
        - 结束时间：{market1.get('end_time', 'N/A')}

        ## 市场2
        - 问题：{market2.get('question', 'N/A')}
        - YES价格：{market2.get('yes_price', 'N/A')}
        - 结束时间：{market2.get('end_time', 'N/A')}

        ## 分析任务
        判断这两个市场是否构成逻辑对冲：

        1. **逻辑关系**：
           - 如果市场1发生，市场2是否必然发生？
           - 如果市场2发生，市场1是否必然发生？
           - 两个市场是否是同一事件的正反面？

        2. **覆盖度计算**：
           - 如果买市场1的YES和市场2的YES，覆盖度是多少？
           - 如果买市场1的YES和市场2的NO，覆盖度是多少？

        3. **利润空间**：
           - YES1 + YES2 < 1.0 ？
           - YES1 + NO2 < 1.0 ？
           - 如果是，利润空间是多少（考虑3.15%费用）？

        ## 输出格式
        {{
            "is_hedge": true/false,
            "hedge_type": "positive_correlation/negative_correlation/same_event",
            "coverage_percentage": 95,
            "profit_after_fees": 0.02,
            "optimal_combination": "YES1+YES2/YES1+NO2/NO1+YES2/NO1+NO2",
            "risk_level": "low/medium/high",
            "reasoning": "简要说明逻辑关系"
        }}
        """
        return prompt

    def _build_strategy_recommendation_prompt(self, market_data: Dict[str, Any],
                                         opportunity_type: str) -> str:
        """构建策略推荐提示词"""
        prompt = f"""
        基于市场分析推荐交易策略：

        ## 机会类型
        {opportunity_type}

        ## 市场信息
        - YES价格：{market_data.get('yes_price', 'N/A')}
        - NO价格：{market_data.get('no_price', 'N/A')}
        - 价格偏差：{market_data.get('price_deviation', 0)}
        - 流动性：{market_data.get('liquidity', 'N/A')}

        ## 可用策略
        1. **Liquidity Absorption Flip**：利用流动性吸收后的价格翻转
        2. **Orderbook Arbitrage**：YES+NO<1.0时的价差套利
        3. **Structural Spread**：结构化价差锁定
        4. **NO Farming**：系统性押注NO（适用于过度乐观市场）
        5. **Long Tail Floor**：长尾事件的低概率押注
        6. **Spread Farming**：高概率合约的价差复利
        7. **High Probability Auto-Compounding**：高概率自动复利

        ## 推荐任务
        根据市场特征，推荐最优策略：

        {{            "recommended_strategy": "strategy_name",
            "strategy_params": {{
                "entry_price": 0.5,
                "position_size": 50,
                "target_profit": 0.05,
                "stop_loss": 0.1,
                "holding_period": "short/medium/long"
            }},
            "expected_profit": 0.03,
            "risk_reward_ratio": 3,
            "execution_notes": "简要说明执行要点"
        }}
        """
        return prompt

    def _call_llm(self, prompt: str) -> str:
        """调用LLM API"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        data = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "你是一个专业的Polymarket交易分析师，擅长识别套利机会、对冲策略和市场趋势。"
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.3,
            "max_tokens": 1000
        }

        try:
            response = requests.post(
                self.api_url,
                headers=headers,
                json=data,
                timeout=30
            )
            response.raise_for_status()
            result = response.json()

            return result["choices"][0]["message"]["content"]

        except requests.exceptions.RequestException as e:
            raise Exception(f"LLM API调用失败: {str(e)}")

    def _parse_analysis_response(self, response: str) -> Dict[str, Any]:
        """解析市场分析响应"""
        try:
            # 尝试提取JSON
            start = response.find('{')
            end = response.rfind('}') + 1

            if start != -1 and end > start:
                json_str = response[start:end]
                return json.loads(json_str)
            else:
                # 无法解析，返回默认值
                return {
                    "price_reasonable": False,
                    "opportunity_type": "none",
                    "risk_level": "high",
                    "confidence": 0.5,
                    "reasoning": "无法解析LLM响应"
                }

        except Exception as e:
            return {
                "price_reasonable": False,
                "opportunity_type": "none",
                "risk_level": "high",
                "confidence": 0.5,
                "reasoning": f"解析错误: {str(e)}"
            }

    def _parse_hedge_response(self, response: str) -> Dict[str, Any]:
        """解析对冲分析响应"""
        try:
            start = response.find('{')
            end = response.rfind('}') + 1

            if start != -1 and end > start:
                json_str = response[start:end]
                return json.loads(json_str)
            else:
                return {
                    "is_hedge": False,
                    "coverage_percentage": 0,
                    "reasoning": "无法解析响应"
                }

        except Exception as e:
            return {
                "is_hedge": False,
                "coverage_percentage": 0,
                "reasoning": f"解析错误: {str(e)}"
            }

    def _parse_strategy_response(self, response: str) -> Dict[str, Any]:
        """解析策略推荐响应"""
        try:
            start = response.find('{')
            end = response.rfind('}') + 1

            if start != -1 and end > start:
                json_str = response[start:end]
                return json.loads(json_str)
            else:
                return {
                    "recommended_strategy": "none",
                    "expected_profit": 0,
                    "reasoning": "无法解析响应"
                }

        except Exception as e:
            return {
                "recommended_strategy": "none",
                "expected_profit": 0,
                "reasoning": f"解析错误: {str(e)}"
            }
