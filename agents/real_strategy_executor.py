"""
Real Trading Agent - 集成真实Web3交易功能
基于官方polymarket.py的Web3能力
"""

import sys
from pathlib import Path
from typing import Dict, Any

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.agent_base import BaseAgent
from core.state_manager import StateManager
from core.web3_trader import Web3Trader


class RealStrategyExecutorAgent(BaseAgent):
    """真实的策略执行员（支持真实交易）"""

    def __init__(self, state_manager: StateManager, config: Dict[str, Any]):
        super().__init__("strategy_executor", state_manager, config)

        self.auto_execute = config.get("auto_execute", False)
        self.max_concurrent_trades = config.get("max_concurrent_trades", 3)

        # 初始化Web3交易客户端
        private_key = config.get("private_key", None)
        polygon_rpc = config.get("polygon_rpc", "https://polygon-rpc.com")

        self.web3_trader = Web3Trader(
            private_key=private_key,
            polygon_rpc=polygon_rpc
        )

    def run(self):
        """主运行循环"""
        if not self.check_enabled():
            return

        self.set_status("running")
        self.log("INFO", "真实策略执行员启动...")

        try:
            # 检查钱包状态
            wallet_status = self.web3_trader.check_wallet_status()

            if "error" in wallet_status:
                self.log("ERROR", f"钱包检查失败: {wallet_status['error']}")
                return

            self.log("INFO", f"钱包地址: {wallet_status['address']}")
            self.log("INFO", f"USDC余额: {wallet_status['usdc_balance']:.2f}")
            self.log("INFO", f"POL余额: {wallet_status['pol_balance']:.4f}")

            # 检查approvals
            if "error" not in wallet_status:
                # 检查是否需要设置approvals
                # 这里应该添加检查逻辑
                pass

            # 处理交易机会
            self._process_trading_opportunities()

        except KeyboardInterrupt:
            self.set_status("stopped")
            self.log("INFO", "真实策略执行员停止")

    def _process_trading_opportunities(self):
        """处理交易机会"""
        try:
            opportunities = self.state_manager.get_pending_opportunities(limit=10)

            if not opportunities:
                return

            self.log("INFO", f"发现{len(opportunities)}个待执行机会")

            for opp in opportunities:
                if opp["status"] == "analyzed":
                    # 自动执行模式
                    if self.auto_execute:
                        self._execute_trading_opportunity(opp)
                    else:
                        # 非自动模式，只记录
                        self.log("INFO", f"非自动模式，跳过市场{opp['market_id']}")

        except Exception as e:
            self.log("ERROR", f"处理交易机会失败: {str(e)}")

    def _execute_trading_opportunity(self, opportunity: Dict[str, Any]):
        """
        执行交易机会

        Args:
            opportunity: 机会数据
        """
        try:
            analysis_data = opportunity.get("analysis_data", {})
            risk_level = analysis_data.get("risk_level", "high")

            # 风险过高则跳过
            if risk_level == "high":
                self.log("INFO", f"风险过高，跳过市场{opportunity['market_id']}")
                self.state_manager.update_opportunity_status(
                    opportunity_id=opportunity["id"],
                    status="skipped_high_risk"
                )
                return

            # 检查金额限制
            amount_usdc = analysis_data.get("strategy_params", {}).get("position_size", 10)
            expected_profit = analysis_data.get("expected_profit", 0)

            self.log("INFO", f"执行交易: 市场={opportunity['market_id']}, 金额={amount_usdc} USDC, 预期利润={expected_profit:.2%}")

            # 执行真实交易
            trade_result = self.web3_trader.execute_trade(
                market_id=opportunity["market_id"],
                amount_usdc=amount_usdc,
                outcome="YES",  # 简化：默认买YES
                expected_profit=expected_profit
            )

            if "error" in trade_result:
                self.log("ERROR", f"交易失败: {trade_result['error']}")

                self.state_manager.update_opportunity_status(
                    opportunity_id=opportunity["id"],
                    status="failed"
                )
                return

            # 交易成功
            self.log("INFO", f"交易成功: {trade_result['split_result'].get('split_hash', 'N/A')}")

            self.state_manager.update_opportunity_status(
                opportunity_id=opportunity["id"],
                status="executed"
            )

            # 更新状态
            self._update_state_field("trades_executed",
                                  self.state["data"].get("trades_executed", 0) + 1)

        except Exception as e:
            self.log("ERROR", f"执行交易机会失败: {str(e)}")

    def process_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """处理收到的消息"""
        message_type = message.get("message_type", "")
        message_data = message.get("message_data", {})

        response = {
            "status": "processed",
            "data": {}
        }

        if message_type == "wallet_status":
            # 查询钱包状态
            wallet_status = self.web3_trader.check_wallet_status()
            response["data"]["wallet_status"] = wallet_status

        elif message_type == "approve":
            # 设置approvals
            self.log("INFO", "开始设置approvals...")

            # 从环境变量获取私钥（如果未设置）
            import os
            private_key = message_data.get("private_key") or os.getenv("POLYGON_WALLET_PRIVATE_KEY", "")

            # 更新Web3交易客户端的私钥
            self.web3_trader.private_key = private_key

            # 重新初始化
            self.web3_trader = Web3Trader(
                private_key=private_key,
                polygon_rpc=message_data.get("polygon_rpc", "https://polygon-rpc.com")
            )

            # 执行approval
            approve_result = self.web3_trader.set_approvals()

            response["data"]["approve_result"] = approve_result

        elif message_type == "execute_trade":
            # 执行交易
            market_id = message_data.get("market_id")
            amount = message_data.get("amount", 10)
            outcome = message_data.get("outcome", "YES")

            self.log("INFO", f"收到交易请求: 市场={market_id}, 金额={amount}, 方向={outcome}")

            # 执行交易
            trade_result = self.web3_trader.execute_trade(
                market_id=market_id,
                amount_usdc=amount,
                outcome=outcome
            )

            response["data"]["trade_result"] = trade_result

        elif message_type == "status_request":
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
                "trades_executed": 0,
                "open_positions": 0,
                "total_profit": 0.0,
                "wallet_initialized": False
            }
        }
