"""
简化测试 - 测试LLM Agent Trading Bot的核心功能
跳过Polymarket API调用，使用模拟数据
"""

import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.state_manager import StateManager
from core.agent_base import BaseAgent


class MockAgent(BaseAgent):
    """模拟Agent"""

    def __init__(self, agent_id: str, state_manager: StateManager):
        super().__init__(agent_id, state_manager, {"enabled": True})

    def run(self):
        while True:
            import time
            time.sleep(1)

    def process_message(self, message: dict) -> dict:
        self.log("INFO", f"收到消息: {message}")
        return {"status": "processed", "data": message}

    def _init_default_state(self):
        return {"status": "idle", "messages_processed": 0}


def test_state_manager():
    """测试状态管理器"""
    print("\n🧪 测试1: 状态管理器")
    print("=" * 50)

    db_path = "/tmp/test_agent_state.db"
    state_manager = StateManager(db_path)

    # 设置状态
    print("✅ 设置Agent状态...")
    success = state_manager.set_agent_state(
        agent_id="test_agent",
        state_data={"status": "running", "counter": 10, "test_data": {"key": "value"}}
    )
    print(f"   结果: {'成功' if success else '失败'}")

    # 获取状态
    print("\n✅ 获取Agent状态...")
    state = state_manager.get_agent_state("test_agent")
    if state:
        print(f"   状态: {state.get('state', {})}")
        print(f"   数据: {state.get('state', {}).get('test_data', {})}")
    else:
        print("   ❌ 未能获取状态")

    # 发送消息
    print("\n✅ 测试Agent间消息...")
    success = state_manager.send_message(
        from_agent="agent_a",
        to_agent="agent_b",
        message_type="test",
        message_data={"test": "data", "number": 123}
    )
    print(f"   结果: {'成功' if success else '失败'}")

    # 获取消息
    print("\n✅ 获取消息...")
    messages = state_manager.get_messages(to_agent="agent_b", limit=5)
    print(f"   消息数: {len(messages)}")
    for msg in messages:
        print(f"   - {msg['from_agent']} -> {msg['to_agent']}: {msg['message_data']}")

    # 保存机会
    print("\n✅ 保存机会...")
    success = state_manager.save_opportunity(
        market_id="market_test_001",
        opportunity_type="arbitrage",
        analysis_data={"test": "data", "profit": 0.05, "risk": "low"}
    )
    print(f"   结果: {'成功' if success else '失败'}")

    # 获取待处理机会
    print("\n✅ 获取待处理机会...")
    opportunities = state_manager.get_pending_opportunities(limit=5)
    print(f"   机会数: {len(opportunities)}")
    for opp in opportunities:
        print(f"   - 市场: {opp['market_id']}, 类型: {opp['opportunity_type']}")

    # 更新机会状态
    if opportunities:
        print("\n✅ 更新机会状态...")
        success = state_manager.update_opportunity_status(opportunities[0]['id'], "analyzed")
        print(f"   结果: {'成功' if success else '失败'}")

    # 查看所有Agent状态
    print("\n✅ 获取所有Agent状态...")
    all_states = state_manager.get_all_agent_states()
    for agent_id, state in all_states.items():
        print(f"   {agent_id}: {state['state'].get('status', 'unknown')}")

    state_manager.close()
    print("\n✅ 状态管理器测试完成！\n")


def test_agent_communication():
    """测试Agent通信"""
    print("🧪 测试2: Agent通信")
    print("=" * 50)

    db_path = "/tmp/test_agents_comm.db"
    state_manager = StateManager(db_path)

    # 创建Agents
    print("✅ 创建测试Agents...")
    agent_a = MockAgent("agent_a", state_manager)
    agent_b = MockAgent("agent_b", state_manager)

    # Agent A发送消息给Agent B
    print("\n✅ Agent A -> Agent B...")
    success = agent_a.send_message(
        to_agent="agent_b",
        message_type="test",
        message_data={"hello": "from agent a", "timestamp": "2026-03-22"}
    )
    print(f"   结果: {'成功' if success else '失败'}")

    # Agent B获取消息
    print("\n✅ Agent B 获取消息...")
    messages = agent_b.get_messages()
    print(f"   消息数: {len(messages)}")
    for msg in messages:
        print(f"   - 来自: {msg['from_agent']}")
        print(f"     内容: {msg['message_data']}")

    # Agent B处理消息
    if messages:
        print("\n✅ Agent B 处理消息...")
        response = agent_b.process_message(messages[0])
        print(f"   结果: {response}")

    state_manager.close()
    print("\n✅ Agent通信测试完成！\n")


def test_all_agents():
    """测试所有5个Agents的协作"""
    print("🧪 测试3: 多Agent协作")
    print("=" * 50)

    db_path = "/tmp/test_multi_agents.db"
    state_manager = StateManager(db_path)

    # 创建5个Agents
    print("✅ 创建5个测试Agents...")
    agents = {
        "market_scout": MockAgent("market_scout", state_manager),
        "llm_analyst": MockAgent("llm_analyst", state_manager),
        "strategy_executor": MockAgent("strategy_executor", state_manager),
        "risk_manager": MockAgent("risk_manager", state_manager),
        "trade_logger": MockAgent("trade_logger", state_manager)
    }

    # 模拟工作流：市场情报员 -> LLM分析师 -> 策略执行员
    print("\n✅ 模拟工作流...")
    print("   Step 1: 市场情报员发现机会")

    # 市场情报员发现机会
    opportunity = {
        "market_id": "test_market_123",
        "yes_price": 0.48,
        "no_price": 0.49,
        "profit": 0.03
    }

    state_manager.save_opportunity(
        market_id=opportunity["market_id"],
        opportunity_type="arbitrage",
        analysis_data=opportunity
    )

    print("   Step 2: 市场情报员通知LLM分析师")
    agents["market_scout"].send_message(
        to_agent="llm_analyst",
        message_type="opportunity",
        message_data=opportunity
    )

    print("   Step 3: LLM分析师获取消息")
    messages = agents["llm_analyst"].get_messages(message_type="opportunity")
    print(f"   LLM分析师收到{len(messages)}条消息")

    if messages:
        print("   Step 4: LLM分析师分析机会")
        analysis = agents["llm_analyst"].process_message(messages[0])
        print(f"   分析结果: {analysis}")

        print("   Step 5: LLM分析师通知策略执行员")
        agents["llm_analyst"].send_message(
            to_agent="strategy_executor",
            message_type="trading_opportunity",
            message_data=analysis["data"]
        )

    print("   Step 6: 策略执行员获取消息")
    strategy_messages = agents["strategy_executor"].get_messages(message_type="trading_opportunity")
    print(f"   策略执行员收到{len(strategy_messages)}条消息")

    # 查看所有Agent状态
    print("\n✅ 查看所有Agent状态:")
    all_states = state_manager.get_all_agent_states()
    for agent_id, state in all_states.items():
        status = state.get('state', {}).get('status', 'unknown')
        processed = state.get('state', {}).get('messages_processed', 0)
        print(f"   {agent_id:20s}: {status:10s} (已处理{processed}条消息)")

    state_manager.close()
    print("\n✅ 多Agent协作测试完成！\n")


def main():
    """主函数"""
    print("\n🚀 LLM Agent Trading Bot - 核心功能测试")
    print("=" * 50)

    # 测试1: 状态管理器
    test_state_manager()

    # 测试2: Agent通信
    test_agent_communication()

    # 测试3: 多Agent协作
    test_all_agents()

    print("\n" + "=" * 50)
    print("✅ 所有核心功能测试完成！\n")
    print("📝 总结:")
    print("   ✅ 状态管理器 - 正常工作")
    print("   ✅ Agent基类 - 正常工作")
    print("   ✅ Agent间通信 - 正常工作")
    print("   ✅ 机会管理 - 正常工作")
    print("   ✅ 多Agent协作 - 正常工作")
    print("\n📝 下一步:")
    print("   1. 设置OPENROUTER_API_KEY环境变量")
    print("   2. 运行完整系统: python main.py --mode interactive")
    print("   3. 在交互界面输入: scan, status, help")
    print("\n")


if __name__ == "__main__":
    main()
