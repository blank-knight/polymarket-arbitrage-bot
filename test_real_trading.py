"""
Real Trading Test
测试真实的Web3交易功能
"""

import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.web3_trader import Web3Trader


def test_real_trading():
    """测试真实交易功能"""
    print("\n🚀 真实交易功能测试")
    print("=" * 60)

    print("\n⚠️  重要提醒:")
    print("   这是真实交易功能，会使用你的钱包私钥")
    print("   任何错误都可能导致资金损失")
    print("   请确保:")
    print("     1. 设置 POLYGON_WALLET_PRIVATE_KEY 环境变量")
    print("     2. 设置 OPENROUTER_API_KEY 环境变量（如需LLM分析）")
    print("     3. 钱包中有足够的USDC和POL（用于gas）")
    print("\n")

    # 检查环境变量
    import os

    private_key = os.getenv("POLYGON_WALLET_PRIVATE_KEY")
    openrouter_key = os.getenv("OPENROUTER_API_KEY")

    if not private_key:
        print("❌ 未设置 POLYGON_WALLET_PRIVATE_KEY 环境变量")
        print("   用法: export POLYGON_WALLET_PRIVATE_KEY=\"0x...\"")
        return

    if not openrouter_key:
        print("⚠️  未设置 OPENROUTER_API_KEY 环境变量")
        print("   LLM功能将不可用，但不影响基础交易功能")

    print(f"✅ 私钥已设置: {private_key[:10]}...{private_key[-4:]}")
    print(f"✅ OpenRouter API Key: {openrouter_key[:10] if openrouter_key else 'N/A'}...")

    # 初始化Web3交易客户端
    print("\n🔄 初始化Web3交易客户端...")

    trader = Web3Trader(
        private_key=private_key,
        polygon_rpc="https://polygon-rpc.com"
    )

    # 测试钱包状态
    print("\n📊 测试1: 钱包状态")
    print("-" * 60)

    wallet_status = trader.check_wallet_status()

    if "error" in wallet_status:
        print(f"❌ 钱包检查失败: {wallet_status['error']}")
        return

    print(f"✅ 钱包地址: {wallet_status['address']}")
    print(f"✅ USDC余额: {wallet_status['usdc_balance']:.2f} USDC")
    print(f"✅ POL余额: {wallet_status['pol_balance']:.4f} POL")

    # 检查余额
    usdc_balance = wallet_status['usdc_balance']

    if usdc_balance < 1.0:
        print("\n⚠️  警告: USDC余额不足")
        print(f"   当前余额: {usdc_balance:.2f} USDC")
        print("   建议至少存入10 USDC用于测试")
        print("\n")

        # 是否继续？
        user_input = input("是否继续测试(y/n)? ").strip().lower()

        if user_input != 'y':
            print("已取消测试")
            return

    # 测试设置approvals
    print("\n📊 测试2: 设置Approvals")
    print("-" * 60)

    print("⚠️  注意: 首次设置approvals需要消耗约0.01 POL")
    print("   这会从你的POL余额中扣除gas费")

    # 是否设置approvals？
    user_input = input("\n是否设置approvals (y/n)? ").strip().lower()

    if user_input == 'y':
        print("🔄 开始设置approvals...")

        approve_result = trader.set_approvals()

        if "error" in approve_result:
            print(f"❌ Approvals设置失败: {approve_result['error']}")
            return

        print(f"✅ CLOB Exchange approval: {approve_result.get('clob_approval_hash', 'N/A')[:20]}...")
        print(f"✅ Neg Risk CTF approval: {approve_result.get('neg_approval_hash', 'N/A')[:20]}...")

        print("\n⏸️  等待交易确认（最多60秒）...")
        print("   这可能需要一些时间，请耐心等待...")

    # 测试split交易
    print("\n📊 测试3: Split交易")
    print("-" * 60)

    test_amount = 2.0  # 测试2 USDC
    test_market_id = "test_market_001"  # 模拟市场ID

    user_input = input(f"\n是否执行split测试 (测试金额: {test_amount} USDC) (y/n)? ").strip().lower()

    if user_input == 'y':
        print(f"\n🔄 执行split交易...")
        print(f"   市场: {test_market_id}")
        print(f"   金额: {test_amount} USDC")
        print(f"   方向: YES")

        split_result = trader.split_and_buy(
            market_id=test_market_id,
            amount_usdc=test_amount,
            outcome="YES"
        )

        if "error" in split_result:
            print(f"❌ Split失败: {split_result['error']}")
        else:
            print(f"✅ Split完成: {split_result.get('split_hash', 'N/A')[:20]}...")
            print(f"   状态: {split_result.get('status', 'N/A')}")

    # 测试完成
    print("\n" + "=" * 60)
    print("✅ 真实交易功能测试完成！")
    print("\n📝 总结:")
    print(f"   - Web3客户端: {'正常' if trader.w3 else '未初始化'}")
    print(f"   - 钱包状态: {'正常' if 'error' not in wallet_status else '错误'}")
    print(f"   - Approval设置: {'已完成' if user_input == 'y' else '跳过'}")
    print(f"   - Split测试: {'已完成' if user_input == 'y' else '跳过'}")

    print("\n📝 下一步:")
    print("   1. 在主程序中运行: python main.py --real-trading --config config/test_real_trading.yaml")
    print("   2. 使用交互模式管理真实交易")
    print("   3. 在交互界面输入: wallet_status, approve, execute_trade")
    print("\n")


if __name__ == "__main__":
    test_real_trading()
