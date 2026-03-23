"""
Strategy Executor Agent (简化版)
负责策略执行和交易管理
"""

from typing import Dict, Any
from core.agent_base import BaseAgent
from core.state_manager import StateManager


class StrategyExecutorAgent(BaseAgent):
    """策略执行员（简化版）"""

    def __init__(self, state_manager: StateManager, config: Dict[str, Any]):
        super().__init__("strategy_executor", state_manager, config)

        self.auto_execute = config.get("auto_execute", False)
        self.max_concurrent_trades = config.get("max_concurrent_trades", 3)

    def run(self):
        """主运行循环"""
        if not self.check_enabled():
            return

        self.set_status("running")
        self.log("INFO", "策略执行员启动...")

        try:
            while True:
                # 处理交易机会
                self._process_trading_opportunities()

                # 检查新消息
                messages = self.get_messages(message_type="trading_opportunity")

                for message in messages:
                    self._handle_trading_opportunity(message["message_data"])
                    self.state_manager.mark_message_processed(message["id"])

        except KeyboardInterrupt:
            self.set_status("stopped")
            self.log("INFO", "策略执行员停止")

    def _process_trading_opportunities(self):
        """处理交易机会"""
        try:
            opportunities = self.state_manager.get_pending_opportunities(limit=10)

            if not opportunities:
                return

            self.log("INFO", f"发现{len(opportunities)}个待执行机会")

            for opp in opportunities:
                if opp["status"] == "analyzed":
                    self._execute_trade_if_allowed(opp)

        except Exception as e:
            self.log("ERROR", f"处理交易机会失败: {str(e)}")

    def _handle_trading_opportunity(self, opportunity_data: Dict[str, Any]):
        """
        处理交易机会

        Args:
            opportunity_data: 机会数据
        """
        try:
            analysis = opportunity_data.get("analysis", {})
            risk_level = analysis.get("risk_level", "high")

            self.log("INFO", f"收到交易机会: 市场={opportunity_data.get('market_id')}, 风险={risk_level}")

            # 记录机会
            self._update_state_field(
                f"pending_trade_{opportunity_data.get('market_id')}",
                opportunity_data
            )

        except Exception as e:
            self.log("ERROR", f"处理交易机会失败: {str(e)}")

    def _execute_trade_if_allowed(self, opportunity: Dict[str, Any]):
        """
        执行交易（如果允许）

        Args:
            opportunity: 机会数据
        """
        if not self.auto_execute:
            self.log("INFO", f"自动执行未启用，跳过市场{opportunity['market_id']}")
            return

        # 检查风险
        analysis = opportunity.get("analysis_data", {})
        risk_level = analysis.get("risk_level", "high")

        if risk_level == "high":
            self.log("INFO", f"风险过高，跳过市场{opportunity['market_id']}")
            return

        self.log("INFO", f"执行交易: 市场={opportunity['market_id']}, 策略={analysis.get('recommended_strategy', 'none')}")

        # TODO: 实际执行交易逻辑（需要Web3）
        # 这里只是模拟
        self.state_manager.update_opportunity_status(
            opportunity_id=opportunity["id"],
            status="executed"
        )

    def process_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """处理收到的消息"""
        message_type = message.get("message_type", "")
        message_data = message.get("message_data", {})

        response = {
            "status": "processed",
            "data": {}
        }

        if message_type == "execute_request":
            # 用户请求执行交易
            market_id = message_data.get("market_id")
            self.log("INFO", f"用户请求执行交易: {market_id}")

            response["data"]["message"] = "交易请求已接收（实际执行功能待实现）"

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
                "open_positions": 0
            }
        }


class RiskManagerAgent(BaseAgent):
    """风险管家（简化版）"""

    def __init__(self, state_manager: StateManager, config: Dict[str, Any]):
        super().__init__("risk_manager", state_manager, config)

        self.monitor_interval = config.get("monitor_interval", 10)
        self.auto_stop_loss = config.get("auto_stop_loss", True)
        self.max_position_percentage = config.get("max_position_percentage", 0.3)

    def run(self):
        """主运行循环"""
        if not self.check_enabled():
            return

        self.set_status("running")
        self.log("INFO", "风险管家启动...")

        try:
            import time

            while True:
                # 监控风险
                self._monitor_risk()

                time.sleep(self.monitor_interval)

        except KeyboardInterrupt:
            self.set_status("stopped")
            self.log("INFO", "风险管家停止")

    def _monitor_risk(self):
        """监控风险"""
        # TODO: 实现实际的风险监控逻辑
        # 这里只是模拟
        pass

    def process_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """处理收到的消息"""
        response = {
            "status": "processed",
            "data": {"message": "风险管家已处理消息"}
        }
        return response

    def _init_default_state(self) -> Dict[str, Any]:
        """初始化默认状态"""
        return {
            "status": "idle",
            "last_run": None,
            "data": {
                "total_exposure": 0,
                "stop_losses_triggered": 0
            }
        }


class TradeLoggerAgent(BaseAgent):
    """记录员（简化版）"""

    def __init__(self, state_manager: StateManager, config: Dict[str, Any]):
        super().__init__("trade_logger", state_manager, config)

        self.log_to_csv = config.get("log_to_csv", True)
        self.log_to_db = config.get("log_to_db", True)

    def run(self):
        """主运行循环"""
        if not self.check_enabled():
            return

        self.set_status("running")
        self.log("INFO", "记录员启动...")

        try:
            while True:
                # 处理日志记录
                messages = self.get_messages()

                for message in messages:
                    self._log_trade(message["message_data"])
                    self.state_manager.mark_message_processed(message["id"])

                import time
                time.sleep(1)

        except KeyboardInterrupt:
            self.set_status("stopped")
            self.log("INFO", "记录员停止")

    def _log_trade(self, trade_data: Dict[str, Any]):
        """
        记录交易

        Args:
            trade_data: 交易数据
        """
        try:
            self.log("INFO", f"记录交易: 市场={trade_data.get('market_id', 'N/A')}")

            # TODO: 实现实际的日志记录逻辑（CSV/SQLite）

        except Exception as e:
            self.log("ERROR", f"记录交易失败: {str(e)}")

    def process_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """处理收到的消息"""
        response = {
            "status": "processed",
            "data": {"message": "记录员已处理消息"}
        }
        return response

    def _init_default_state(self) -> Dict[str, Any]:
        """初始化默认状态"""
        return {
            "status": "idle",
            "last_run": None,
            "data": {
                "trades_logged": 0,
                "last_log_time": None
            }
        }
