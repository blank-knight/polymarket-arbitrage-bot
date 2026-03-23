"""
LLM Agent Trading Bot - Main Entry
基于LLM的智能预测市场套利交易系统
"""

import os
import sys
import yaml
import argparse
from pathlib import Path

# 添加项目路径到sys.path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.state_manager import StateManager
from core.polymarket_client import PolymarketClient
from core.llm_client import LLMAnalyst
from agents.market_scout import MarketScoutAgent
from agents.simplified_agents import (
    StrategyExecutorAgent,
    RiskManagerAgent,
    TradeLoggerAgent
)
from agents.real_strategy_executor import RealStrategyExecutorAgent


class TradingBotOrchestrator:
    """交易机器人控制器"""

    def __init__(self, config_path: str = "config/settings.yaml",
                 use_real_executor: bool = False):
        """
        Args:
            config_path: 配置文件路径
            use_real_executor: 是否使用真实的策略执行员
        """
        self.config_path = config_path
        self.use_real_executor = use_real_executor
        self.config = self._load_config()

        # 初始化组件
        self._init_components()

        # Agents
        self.agents = {}

    def _load_config(self) -> dict:
        """加载配置"""
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)

            # 环境变量覆盖
            if not config.get("llm", {}).get("api_key"):
                config["llm"]["api_key"] = os.getenv("OPENROUTER_API_KEY", "")

            if not config.get("polymarket", {}).get("chainstack_node"):
                config["polymarket"]["chainstack_node"] = os.getenv("CHAINSTACK_NODE", "")

            return config

        except Exception as e:
            print(f"加载配置失败: {str(e)}")
            sys.exit(1)

    def _init_components(self):
        """初始化所有组件"""
        # 状态管理器
        db_path = self.config["database"]["agent_state_db"]
        self.state_manager = StateManager(db_path)

        # Polymarket客户端
        polymarket_config = self.config["polymarket"]
        self.polymarket_client = PolymarketClient(
            gamma_api_url=polymarket_config["gamma_api_url"],
            chainstack_node=polymarket_config["chainstack_node"]
        )

        # LLM客户端
        llm_config = self.config["llm"]
        self.llm_client = LLMAnalyst(
            api_key=llm_config["api_key"],
            model=llm_config["model"]
        )

        # 初始化Agents
        self._init_agents(use_real_executor=True)

    def _init_agents(self, use_real_executor: bool = False):
        """
        初始化所有Agents

        Args:
            use_real_executor: 是否使用真实的策略执行员
        """
        # 市场情报员
        self.agents["market_scout"] = MarketScoutAgent(
            state_manager=self.state_manager,
            config=agents_config.get("market_scout", {}),
            polymarket_client=self.polymarket_client
        )

        # LLM分析师
        self.agents["llm_analyst"] = LLMAnalystAgent(
            state_manager=self.state_manager,
            config=agents_config.get("llm_analyst", {})
        )

        # 策略执行员
        if use_real_executor:
            # 使用真实的策略执行员（支持真实交易）
            self.agents["strategy_executor"] = RealStrategyExecutorAgent(
                state_manager=self.state_manager,
                config=agents_config.get("strategy_executor", {})
            )
        else:
            # 使用简化的策略执行员（模拟）
            self.agents["strategy_executor"] = StrategyExecutorAgent(
                state_manager=self.state_manager,
                config=agents_config.get("strategy_executor", {})
            )

        # 风险管家
        self.agents["risk_manager"] = RiskManagerAgent(
            state_manager=self.state_manager,
            config=agents_config.get("risk_manager", {})
        )

        # 记录员
        self.agents["trade_logger"] = TradeLoggerAgent(
            state_manager=self.state_manager,
            config=agents_config.get("trade_logger", {})
        )

        print(f"✅ 已初始化{len(self.agents)}个Agents")
        if use_real_executor:
            print("✅ 使用真实交易模式")

    def start_agent(self, agent_id: str):
        """
        启动单个Agent

        Args:
            agent_id: Agent ID
        """
        if agent_id not in self.agents:
            print(f"❌ 未找到Agent: {agent_id}")
            return

        agent = self.agents[agent_id]
        print(f"🚀 启动Agent: {agent_id}")
        agent.run()

    def start_all_agents(self):
        """启动所有Agents"""
        print(f"\n🚀 启动所有Agents...\n")

        # 简化：只启动市场情报员和LLM分析师
        # 其他agents以消息驱动方式运行

        agents_to_start = ["market_scout", "llm_analyst"]

        for agent_id in agents_to_start:
            print(f"🚀 启动Agent: {agent_id}")
            self.agents[agent_id].run()

    def get_agent_status(self) -> dict:
        """获取所有Agents的状态"""
        status = {}

        for agent_id, agent in self.agents.items():
            agent_state = self.state_manager.get_agent_state(agent_id)
            status[agent_id] = agent_state

        return status

    def send_message_to_agent(self, from_agent: str, to_agent: str,
                            message_type: str, message_data: dict) -> bool:
        """
        发送消息给Agent

        Args:
            from_agent: 发送方Agent ID
            to_agent: 接收方Agent ID
            message_type: 消息类型
            message_data: 消息数据

        Returns:
            是否成功
        """
        return self.state_manager.send_message(
            from_agent=from_agent,
            to_agent=to_agent,
            message_type=message_type,
            message_data=message_data
        )

    def run_interactive(self):
        """交互模式"""
        print("\n🎮 LLM Agent Trading Bot - 交互模式")
        print("=" * 50)

        while True:
            try:
                cmd = input("\n[主控] > ").strip()

                if not cmd:
                    continue

                if cmd in ["exit", "quit", "q"]:
                    print("👋 退出")
                    break

                elif cmd == "status":
                    self._show_status()

                elif cmd == "help":
                    self._show_help()

                elif cmd.startswith("scan"):
                    self._handle_scan_command(cmd)

                elif cmd.startswith("agent"):
                    self._handle_agent_command(cmd)

                else:
                    print(f"❌ 未知命令: {cmd}")
                    print("输入 'help' 查看帮助")

            except KeyboardInterrupt:
                print("\n👋 退出")
                break

    def _show_status(self):
        """显示状态"""
        print("\n📊 Agents状态:")
        print("-" * 50)

        status = self.get_agent_status()

        for agent_id, agent_state in status.items():
            state = agent_state.get("state", {})
            agent_status = state.get("status", "unknown")

            print(f"  {agent_id:20s}: {agent_status:10s} - {state.get('last_run', 'N/A')}")

        print("-" * 50)

    def _show_help(self):
        """显示帮助"""
        print("\n📖 命令帮助:")
        print("-" * 50)
        print("  status              - 显示所有Agents状态")
        print("  scan               - 执行市场扫描")
        print("  agent <id>         - 查看Agent状态")
        print("  start <id>         - 启动指定Agent")
        print("  start all          - 启动所有Agents")
        print("  help               - 显示此帮助")
        print("  exit/quit          - 退出")
        print("-" * 50)

    def _handle_scan_command(self, cmd: str):
        """处理扫描命令"""
        parts = cmd.split()
        if len(parts) > 1:
            # 扫描指定市场
            market_ids = parts[1:]
            market_data = {"message_type": "scan_request", "message_data": {"market_ids": market_ids}}

            # 发送给市场情报员
            self.state_manager.send_message(
                from_agent="main",
                to_agent="market_scout",
                message_type="scan_request",
                message_data={"market_ids": market_ids}
            )

            print(f"🔍 已请求扫描{len(market_ids)}个市场")
        else:
            # 扫描热门市场
            print("🔍 开始扫描热门市场...")

    def _handle_agent_command(self, cmd: str):
        """处理Agent命令"""
        parts = cmd.split()

        if len(parts) < 2:
            print("❌ 用法: agent <id> [start|status]")
            return

        agent_id = parts[1]

        if len(parts) > 2:
            action = parts[2]

            if action == "start":
                self.start_agent(agent_id)
            elif action == "status":
                agent_state = self.state_manager.get_agent_state(agent_id)
                print(f"\n📊 Agent: {agent_id}")
                print(f"  状态: {agent_state.get('state', {}).get('status', 'unknown')}")
                print(f"  数据: {agent_state.get('state', {})}")
        else:
            print(f"❌ 未知操作: {action}")
        else:
            # 显示Agent状态
            agent_state = self.state_manager.get_agent_state(agent_id)
            print(f"\n📊 Agent: {agent_id}")
            print(f"  状态: {agent_state.get('state', {}).get('status', 'unknown')}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="LLM Agent Trading Bot - 智能预测市场套利交易系统"
    )

    parser.add_argument(
        "--config",
        default="config/settings.yaml",
        help="配置文件路径"
    )

    parser.add_argument(
        "--mode",
        choices=["interactive", "auto"],
        default="interactive",
        help="运行模式: interactive（交互）或 auto（自动）"
    )

    parser.add_argument(
        "--agent",
        help="启动指定Agent"
    )

    parser.add_argument(
        "--real-trading",
        action="store_true",
        help="启用真实交易模式（使用Web3执行）"
    )

    args = parser.parse_args()

    # 检查环境变量
    if not os.getenv("OPENROUTER_API_KEY"):
        print("⚠️  警告: 未设置 OPENROUTER_API_KEY 环境变量")
        print("   LLM分析功能将无法使用")

    if not os.getenv("CHAINSTACK_NODE"):
        print("⚠️  警告: 未设置 CHAINSTACK_NODE 环境变量")

    # 创建控制器
    use_real_executor = args.real_trading
    orchestrator = TradingBotOrchestrator(
        config_path=args.config,
        use_real_executor=use_real_executor
    )

    # 根据模式运行
    if args.mode == "auto":
        if args.agent:
            orchestrator.start_agent(args.agent)
        else:
            orchestrator.start_all_agents()
    else:
        orchestrator.run_interactive()


if __name__ == "__main__":
    main()
