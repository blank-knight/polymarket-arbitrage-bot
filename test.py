"""
测试脚本 - 测试LLM Agent Trading Bot的基础功能
不依赖真实的API keys，使用模拟数据
"""

import sys
from pathlib import Path

# 添加项目路径到sys.path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.state_manager import StateManager
from core.agent_base import BaseAgent


class MockAgent(BaseAgent):
    """模拟Agent（用于测试）"""

    def __init__(self, agent_id: str, state_manager: StateManager):
        super().__init__(agent_id, state_manager, {"enabled": True})

    def run(self):
        """模拟运行"""
        while True:
            import time
            time.sleep(1)

    def process_message(self, message: dict) -> dict:
        """处理消息"""
        self.log("INFO", f"收到消息: {message}")
        return {"status": "processed", "data": message}

    def _init_default_state(self):
        """默认状态"""
        return {
            "status": "idle",
            "messages_processed": 0,
            "test_data": {}
        }


def test_state_manager():
    """测试状态管理器"""
    print("\n🧪 测试1: 状态管理器")
    print("=" * 50)

    # 创建临时数据库
    db_path = "/tmp/test_agent_state.db"
    state_manager = StateManager(db_path)

    # 测试设置状态
    print("✅ 测试设置Agent状态...")
    success = state_manager.set_agent_state(
        agent_id="test_agent",
        state_data={"status": "running", "counter": 10}
    )

    print(f"   状态设置: {'成功' if success else '失败'}")

    # 测试获取状态
    print("\n✅ 测试获取Agent状态...")
    state = state_manager.get_agent_state("test_agent")

    if state:
        print(f"   状态数据: {state}")
    else:
        print("   ❌ 未能获取状态")

    # 测试发送消息
    print("\n✅ 测试Agent间消息...")
    success = state_manager.send_message(
        from_agent="agent_a",
        to_agent="agent_b",
        message_type="test",
        message_data={"test": "data"}
    )

    print(f"   消息发送: {'成功' if success else '失败'}")

    # 测试获取消息
    print("\n✅ 测试获取消息...")
    messages = state_manager.get_messages(to_agent="agent_b", limit=5)

    print(f"   消息数量: {len(messages)}")
    for msg in messages:
        print(f"   - {msg}")

    # 测试保存机会
    print("\n✅ 测试保存机会...")
    success = state_manager.save_opportunity(
        market_id="market_test_001",
        opportunity_type="arbitrage",
        analysis_data={"test": "analysis"}
    )

    print(f"   机会保存: {'成功' if success else '失败'}")

    # 测试获取待处理机会
    print("\n✅ 测试获取待处理机会...")
    opportunities = state_manager.get_pending_opportunities(limit=3)

    print(f"   机会数量: {len(opportunities)}")
    for opp in opportunities:
        print(f"   - 市场: {opp['market_id']}, 类型: {opp['opportunity_type']}")

    # 清理
    state_manager.close()

    print("\n✅ 状态管理器测试完成！")


def test_polymarket_client():
    """测试Polymarket客户端"""
    print("\n🧪 测试2: Polymarket API客户端")
    print("=" * 50)

    try:
        from core.polymarket_client import PolymarketClient

        # 创建客户端（使用默认API URL）
        client = PolymarketClient(
            gamma_api_url="https://gamma-api.polymarket.com",
            chainstack_node=None
        )

        print("✅ 测试获取热门市场...")
        markets = client.get_trending_markets(limit=5)

        print(f"   获取到{len(markets)}个市场")
        print(f"   市场类型: {type(markets)}")
        if len(markets) > 0:
            print(f"   第一个市场类型: {type(markets[0])}")
            print(f"   第一个市场内容: {markets[0] if len(markets) < 50 else '过长已截断'}")

        if markets:
            # 显示前3个市场
            for i, market in enumerate(markets[:3], 1):
                # markets是一个list，每个元素是dict
                print(f"\n   市场 {i}:")
                print(f"      ID: {market.get('marketId', 'N/A')}")
                print(f"      问题: {str(market.get('question', 'N/A'))[:50]}...")
                print(f"      成交量: {market.get('volume24h', 'N/A')}")

            # 测试套利分析
            if len(markets) > 0:
                print("\n✅ 测试套利分析...")
                # 确保传入的是dict
                market_to_analyze = markets[0] if isinstance(markets[0], dict) else markets[0]
                analysis = client.analyze_market_arbitrage(market_to_analyze)

                print(f"   套利机会: {'是' if analysis['has_arbitrage'] else '否'}")
                print(f"   YES价格: {analysis.get('yes_price', 'N/A')}")
                print(f"   NO价格: {analysis.get('no_price', 'N/A')}")
                print(f"   价格偏差: {analysis.get('price_deviation', 'N/A')}")

        print("\n✅ Polymarket客户端测试完成！")

    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")


def test_llm_client():
    """测试LLM客户端"""
    print("\n🧪 测试3: LLM客户端")
    print("=" * 50)

    print("⚠️  警告: 此测试需要OPENROUTER_API_KEY环境变量")
    print("   如未设置，将跳过LLM调用测试")

    import os

    if not os.getenv("OPENROUTER_API_KEY"):
        print("   跳过LLM调用测试（未设置API Key）")
        return

    try:
        from core.llm_client import LLMAnalyst

        api_key = os.getenv("OPENROUTER_API_KEY")
        llm_client = LLMAnalyst(api_key=api_key)

        print("✅ 测试LLM市场分析...")

        # 模拟市场数据
        mock_market_data = {
            "market_id": "test_market_001",
            "question": "测试问题：比特币价格下周会超过100k美元吗？",
            "yes_price": 0.48,
            "no_price": 0.52,
            "price_sum": 1.0,
            "volume_24h": 50000,
            "liquidity": "high",
            "end_time": "2026-03-30T00:00:00Z"
        }

        print(f"   市场数据: {mock_market_data['question']}")
        print(f"   YES价格: {mock_market_data['yes_price']}")
        print(f"   NO价格: {mock_market_data['no_price']}")

        analysis = llm_client.analyze_market(mock_market_data)

        print(f"\n   LLM分析结果:")
        print(f"      合理性: {analysis.get('price_reasonable', 'N/A')}")
        print(f"      机会类型: {analysis.get('opportunity_type', 'N/A')}")
        print(f"      风险等级: {analysis.get('risk_level', 'N/A')}")
        print(f"      置信度: {analysis.get('confidence', 'N/A')}")

        print("\n✅ LLM客户端测试完成！")

    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")


def test_agents():
    """测试Agent"""
    print("\n🧪 测试4: Agent通信")
    print("=" * 50)

    db_path = "/tmp/test_agents.db"
    state_manager = StateManager(db_path)

    # 创建测试Agents
    print("✅ 创建测试Agents...")

    agent_a = MockAgent("agent_a", state_manager)
    agent_b = MockAgent("agent_b", state_manager)

    print(f"   已创建: {agent_a.agent_id}, {agent_b.agent_id}")

    # 测试Agent A发送消息给Agent B
    print("\n✅ 测试Agent间通信...")
    agent_a.send_message(
        to_agent="agent_b",
        message_type="test",
        message_data={"hello": "from agent a"}
    )

    # Agent B获取消息
    messages = agent_b.get_messages()
    print(f"   Agent B收到{len(messages)}条消息")

    for msg in messages:
        print(f"   - 来自: {msg['from_agent']}, 内容: {msg['message_data']}")

    # Agent B处理消息
    if messages:
        agent_b.process_message(messages[0])

    print("\n✅ Agent通信测试完成！")

    state_manager.close()


def run_all_tests():
    """运行所有测试"""
    print("\n🚀 LLM Agent Trading Bot - 测试套件")
    print("=" * 50)
    print()

    # 测试1: 状态管理器
    test_state_manager()

    # 测试2: Polymarket客户端
    test_polymarket_client()

    # 测试3: LLM客户端（需要API Key）
    test_llm_client()

    # 测试4: Agent通信
    test_agents()

    print("\n" + "=" * 50)
    print("✅ 所有测试完成！")
    print("\n📝 下一步:")
    print("   1. 如需测试LLM功能，设置OPENROUTER_API_KEY环境变量")
    print("   2. 运行主程序: python main.py --mode interactive")
    print("   3. 在交互界面输入: scan, status, help")
    print("\n")


if __name__ == "__main__":
    run_all_tests()
