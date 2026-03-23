"""
测试对冲逻辑
演示完整的对冲发现、分析和执行流程
"""

import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from strategies import HedgeExecutor
from core.state_manager import StateManager
from core.polymarket_client import PolymarketClient
from core.web3_trader import Web3Trader


def test_hedge_discovery():
    """测试对冲发现"""
    print("=" * 60)
    print("测试1: 对冲发现")
    print("=" * 60)

    # 初始化状态管理器
    state_manager = StateManager(db_path="test_hedge.db")

    # 创建对冲执行器配置
    config = {
        "auto_execute": False,  # 不自动执行
        "max_hedge_cost": 0.05,
        "min_hedge_profit": 0.01,
        "hedge_strategy": {
            "enabled": True,
            "max_position_size": 100
        },
        "llm": {
            "api_key": "",  # 需要设置真实的API密钥
            "model": "nvidia/nemotron-nano-9b-v2:free"
        }
    }

    # 创建对冲执行器
    hedge_executor = HedgeExecutor(state_manager, config)

    # 模拟市场数据
    test_markets = [
        {
            "marketId": "0x1234",
            "question": "Will Bitcoin price exceed $100k by end of 2024?",
            "outcomePrices": [
                {"price": 0.45, "outcome": "YES"},
                {"price": 0.52, "outcome": "NO"}
            ],
            "volume24h": 50000,
            "liquidity_score": 0.85,
            "endTimestamp": "2024-12-31T23:59:59Z"
        },
        {
            "marketId": "0x5678",
            "question": "Will Bitcoin price be above $100k in January 2025?",
            "outcomePrices": [
                {"price": 0.48, "outcome": "YES"},
                {"price": 0.49, "outcome": "NO"}
            ],
            "volume24h": 30000,
            "liquidity_score": 0.80,
            "endTimestamp": "2025-01-31T23:59:59Z"
        }
    ]

    # 发现对冲对
    print(f"\n分析 {len(test_markets)} 个市场...")

    try:
        hedge_pairs = hedge_executor.discover_hedge_pairs(test_markets)

        print(f"\n发现 {len(hedge_pairs)} 个对冲对:")

        for i, pair in enumerate(hedge_pairs, 1):
            print(f"\n对冲对 {i}:")
            print(f"  市场1: {pair.market1_id}")
            print(f"    问题: {pair.market1_question}")
            print(f"  市场2: {pair.market2_id}")
            print(f"    问题: {pair.market2_question}")
            print(f"  相关性: {pair.correlation:.2f}")
            print(f"  覆盖度: {pair.coverage_ratio:.2f}")
            print(f"  方向: {pair.direction}")
            print(f"  仓位大小: {pair.position_size:.2f} USDC")
            print(f"  预期利润: {pair.expected_profit:.2%}")
            print(f"  对冲成本: {pair.hedge_cost:.2%}")
            print(f"  风险等级: {pair.risk_level}")
            print(f"  信心度: {pair.confidence:.2f}")
            print(f"  理由: {pair.reasoning}")

            # 评估
            evaluation = hedge_executor.evaluate_hedge_pair(pair)
            print(f"  评估: {evaluation['recommend']} (评分: {evaluation.get('score', 0):.2f})")

    except Exception as e:
        print(f"\n对冲发现失败: {e}")
        print("注意：需要设置真实的OPENROUTER_API_KEY才能使用LLM分析")


def test_hedge_execution():
    """测试对冲执行（模拟）"""
    print("\n" + "=" * 60)
    print("测试2: 对冲执行（模拟）")
    print("=" * 60)

    # 初始化状态管理器
    state_manager = StateManager(db_path="test_hedge.db")

    config = {
        "auto_execute": True,
        "max_hedge_cost": 0.05,
        "min_hedge_profit": 0.01,
        "hedge_strategy": {
            "enabled": True,
            "max_position_size": 50
        },
        "llm": {
            "api_key": "",
            "model": "nvidia/nemotron-nano-9b-v2:free"
        }
    }

    hedge_executor = HedgeExecutor(state_manager, config)

    # 创建模拟对冲对
    from strategies.hedge_executor import HedgePair

    test_pair = HedgePair(
        market1_id="0x1234",
        market2_id="0x5678",
        market1_question="Will BTC exceed $100k?",
        market2_question="Will BTC be above $100k in Jan 2025?",
        correlation=0.90,
        coverage_ratio=0.95,
        direction="long",
        position_size=50.0,
        expected_profit=0.025,
        hedge_cost=0.03,
        risk_level="low",
        confidence=0.85,
        reasoning="高度相关，覆盖度好"
    )

    print(f"\n测试对冲对:")
    print(f"  市场1: {test_pair.market1_id}")
    print(f"  市场2: {test_pair.market2_id}")
    print(f"  预期利润: {test_pair.expected_profit:.2%}")

    # 评估
    evaluation = hedge_executor.evaluate_hedge_pair(test_pair)
    print(f"\n评估结果: {evaluation['recommend']}")
    print(f"  评分: {evaluation.get('score', 0):.2f}")
    print(f"  理由: {evaluation.get('reasoning', '')}")

    # 模拟执行（不真实交易）
    print("\n模拟对冲执行...")

    # 创建模拟的Web3交易客户端
    class MockWeb3Trader:
        def execute_trade(self, market_id, amount_usdc, outcome):
            return {
                "success": True,
                "split_hash": f"0xmock_{market_id[:8]}_{outcome}",
                "amount": amount_usdc
            }

    mock_trader = MockWeb3Trader()

    try:
        result = hedge_executor.execute_hedge(test_pair, mock_trader)

        print(f"\n执行结果: {'成功' if result.success else '失败'}")
        print(f"  总成本: {result.total_cost:.2f} USDC")
        print(f"  预期利润: {result.expected_profit:.2%}")
        print(f"  交易数量: {len(result.trades)}")

        for i, trade in enumerate(result.trades, 1):
            print(f"\n  交易 {i}:")
            print(f"    市场: {trade['market_id']}")
            print(f"    方向: {trade['outcome']}")
            print(f"    金额: {trade['amount']:.2f} USDC")
            print(f"    状态: {'成功' if trade['success'] else '失败'}")
            if trade['success']:
                print(f"    交易哈希: {trade['tx_hash']}")

        if result.error:
            print(f"\n错误: {result.error}")

    except Exception as e:
        print(f"\n执行失败: {e}")


def test_hedge_performance():
    """测试对冲表现统计"""
    print("\n" + "=" * 60)
    print("测试3: 对冲表现统计")
    print("=" * 60)

    state_manager = StateManager(db_path="test_hedge.db")
    config = {
        "auto_execute": False,
        "llm": {"api_key": "", "model": "nvidia/nemotron-nano-9b-v2:free"}
    }

    hedge_executor = HedgeExecutor(state_manager, config)

    # 获取表现统计
    performance = hedge_executor.get_hedge_performance()

    print("\n对冲策略表现:")
    print(f"  总对冲次数: {performance['total_hedges']}")
    print(f"  成功次数: {performance['successful_hedges']}")
    print(f"  成功率: {performance['success_rate']:.2%}")
    print(f"  总成本: {performance['total_cost']:.2f} USDC")
    print(f"  总预期利润: {performance['total_expected_profit']:.2f} USDC")
    if performance['avg_execution_time'] > 0:
        print(f"  平均执行时间: {performance['avg_execution_time']:.2f} 秒")

    # 获取历史记录
    print("\n最近的5次对冲记录:")
    history = hedge_executor.get_hedge_history(limit=5)

    for i, record in enumerate(history, 1):
        print(f"\n  记录 {i}:")
        print(f"    市场: {record.hedge_pair.market1_id} <-> {record.hedge_pair.market2_id}")
        print(f"    结果: {'成功' if record.success else '失败'}")
        print(f"    成本: {record.total_cost:.2f} USDC")
        print(f"    时间: {record.execution_time:.2f} 秒")


if __name__ == "__main__":
    print("对冲逻辑测试")
    print("=" * 60)

    # 测试1: 对冲发现
    test_hedge_discovery()

    # 测试2: 对冲执行
    test_hedge_execution()

    # 测试3: 表现统计
    test_hedge_performance()

    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)
    print("\n注意:")
    print("- 真实的LLM分析需要设置OPENROUTER_API_KEY")
    print("- 真实的交易执行需要设置POLYGON_WALLET_PRIVATE_KEY")
    print("- 本测试使用模拟数据和模拟交易客户端")
