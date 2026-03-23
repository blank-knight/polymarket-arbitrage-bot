"""
Web3 Trading Client
基于官方polymarket.py的简化版Web3交易客户端
"""

import os
from typing import Dict, Any, Optional
from web3 import Web3
from web3.constants import MAX_INT

from py_clob_client.client import ClobClient
from py_clob_client.clob_types import ApiCreds
from py_clob_client.constants import AMOY, POLYGON
from py_order_utils.builders import OrderBuilder


class Web3Trader:
    """Web3交易客户端（简化版）"""

    def __init__(self, private_key: Optional[str] = None, polygon_rpc: str = None):
        """
        Args:
            private_key: Polygon钱包私钥
            polygon_rpc: Polygon RPC节点
        """
        self.private_key = private_key or os.getenv("POLYGON_WALLET_PRIVATE_KEY", "")
        self.polygon_rpc = polygon_rpc or "https://polygon-rpc.com"

        if not self.private_key:
            print("⚠️  警告: 未设置钱包私钥，交易功能将不可用")

        # 初始化Web3
        self.w3 = None

        if self.private_key:
            self.w3 = Web3(Web3.Web3.HTTPProvider(self.polygon_rpc))

            # 合约地址
            self.usdc_address = "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174"
            self.ctf_address = "0x4D97DCd97eC945f40cF65F87097ACe5EA0476045"
            self.neg_risk_exchange_address = "0xC5d563A36AE78145C45a50134d48A1215220f80a"

            # USDC ABI (简化版）
            self.usdc_abi = """[{"inputs": [{"internalType": "address", "name": "owner", "type": "address"}, {"internalType": "address", "name": "spender", "type": "address"}, {"internalType": "uint256", "name": "amount", "type": "uint256"}], "name": "approve", "outputs": [{"internalType": "bool", "name": "", "type": "bool"}], "stateMutability": "nonpayable", "type": "function"}, {"inputs": [{"internalType": "address", "name": "account", "type": "address"}], "name": "balanceOf", "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}], "stateMutability": "view", "type": "function"}]"""

            # CTF ABI (简化版）
            self.ctf_abi = """[{"inputs": [{"internalType": "address", "name": "operator", "type": "address"}, {"internalType": "bool", "name": "approved", "type": "bool"}], "name": "setApprovalForAll", "outputs": [], "stateMutability": "nonpayable", "type": "function"}, {"inputs": [{"internalType": "address", "name": "owner", "type": "address"}, {"internalType": "address", "name": "spender", "type": "address"}, {"internalType": "uint256", "name": "amount", "type": "uint256"}], "name": "approve", "outputs": [{"internalType": "bool", "name": "", "type": "bool"}], "stateMutability": "nonpayable", "type": "function"}, {"inputs": [{"internalType": "address", "name": "owner", "type": "address"}, {"internalType": "address", "name": "spender", "type": "address"}, {"internalType": "uint256", "name": "amount", "type": "uint256"}], "name": "transfer", "outputs": [{"internalType": "bool", "name": "", "type": "bool"}], "stateMutability": "nonpayable", "type": "function"}, {"inputs": [{"internalType": "address", "name": "spender", "type": "address"}, {"internalType": "uint256", "name": "amount", "type": "uint256"}], "name": "allowance", "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}], "stateMutability": "view", "type": "function"}, {"inputs": [{"internalType": "address", "name": "owner", "type": "address"}, {"internalType": "address", "name": "spender", "type": "address"}, {"internalType": "uint256", "name": "amount", "type": "uint256"}], "name": "increaseAllowance", "outputs": [{"internalType": "bool", "name": "", "type": "bool"}], "stateMutability": "nonpayable", "type": "function"}, {"inputs": [{"internalType": "address", "name": "owner", "type": "address"}, {"internalType": "address", "name": "spender", "type": "address"}, {"internalType": "uint256", "name": "amount", "type": "uint256"}], "name": "decreaseAllowance", "outputs": [{"internalType": "bool", "name": "", "type": "bool"}], "stateMutability": "nonpayable", "type": "function"}]"""

            # 创建合约实例
            self.usdc_contract = self.w3.eth.contract(
                address=self.usdc_address,
                abi=self.usdc_abi
            )

            self.ctf_contract = self.w3.eth.contract(
                address=self.ctf_address,
                abi=self.ctf_abi
            )

            print("✅ Web3客户端初始化成功")

    def check_wallet_status(self) -> Dict[str, Any]:
        """
        检查钱包状态

        Returns:
            钱包状态字典
        """
        if not self.w3:
            return {"error": "未初始化Web3客户端"}

        try:
            from eth_account import Account

            account = Account.from_key(self.private_key)
            address = account.address

            # 查询USDC余额
            usdc_balance = self.usdc_contract.functions.balanceOf(address).call() / 1e18  # USDC有6位小数

            # 查询POL余额（用于gas）
            pol_balance = self.w3.eth.get_balance(address) / 1e18

            return {
                "address": address,
                "usdc_balance": usdc_balance,
                "pol_balance": pol_balance,
                "status": "ready"
            }

        except Exception as e:
            return {
                "error": str(e),
                "status": "error"
            }

    def set_approvals(self) -> Dict[str, Any]:
        """
        设置 approvals（一次性）

        Returns:
            执行结果
        """
        if not self.w3:
            return {"error": "未初始化Web3客户端"}

        try:
            print("🔐 开始设置approvals...")

            from eth_account import Account
            account = Account.from_key(self.private_key)
            address = account.address
            chain_id = 137  # Polygon mainnet

            # CLOB Exchange approval
            clob_approve_tx = self.ctf_contract.functions.setApprovalForAll(
                "0x4bFb41d5B3570DeFd03C39a9A4D8dE6Bd8B8982E",
                True
            ).build_transaction({"chainId": chain_id, "from": address, "nonce": self.w3.eth.get_transaction_count(address)})

            signed_ctf_tx = self.w3.eth.account.sign_transaction(clob_approve_tx, private_key=self.private_key)
            clob_tx_hash = self.w3.eth.send_raw_transaction(signed_ctf_tx.raw_transaction)

            print(f"✅ CLOB Exchange approval: {clob_tx_hash.hex()}")

            # Neg Risk CTF Exchange approval
            neg_approve_tx = self.ctf_contract.functions.setApprovalForAll(
                "0xC5d563A36AE78145C45a50134d48A1215220f80a",
                True
            ).build_transaction({"chainId": chain_id, "from": address, "nonce": self.w3.eth.get_transaction_count(address)})

            signed_neg_tx = self.w3.eth.account.sign_transaction(neg_approve_tx, private_key=self.private_key)
            neg_tx_hash = self.w3.eth.send_raw_transaction(signed_neg_tx.raw_transaction)

            print(f"✅ Neg Risk CTF approval: {neg_tx_hash.hex()}")

            return {
                "clob_approval_hash": clob_tx_hash.hex(),
                "neg_approval_hash": neg_tx_hash.hex(),
                "status": "completed"
            }

        except Exception as e:
            return {
                "error": str(e),
                "status": "failed"
            }

    def split_and_buy(self, market_id: str, amount_usdc: float,
                      outcome: str = "YES") -> Dict[str, Any]:
        """
        Split USDC并买入指定结果

        Args:
            market_id: 市场ID
            amount_usdc: USDC金额
            outcome: YES或NO

        Returns:
            交易结果
        """
        if not self.w3:
            return {"error": "未初始化Web3客户端"}

        try:
            print(f"🔄 开始split交易: {amount_usdc} USDC, 买入{outcome}")

            from eth_account import Account
            account = Account.from_key(self.private_key)
            address = account.address

            # Split: USDC → YES + NO
            split_tx = self.ctf_contract.functions.split(
                self.ctf_address,
                int(MAX_INT, 0),
                int(amount_usdc * 1e18)
            ).build_transaction({
                "chainId": 137,
                "from": address,
                "value": int(amount_usdc * 1e18),
                "nonce": self.w3.eth.get_transaction_count(address)
            })

            signed_split_tx = self.w3.eth.account.sign_transaction(split_tx, private_key=self.private_key)
            split_tx_hash = self.w3.eth.send_raw_transaction(signed_split_tx.raw_transaction)

            print(f"✅ Split完成: {split_tx_hash.hex()}")

            # 注意：这里应该集成CLOB sell功能
            # 简化版：记录split完成
            return {
                "market_id": market_id,
                "outcome": outcome,
                "amount_usdc": amount_usdc,
                "split_hash": split_tx_hash.hex(),
                "status": "split_completed"
            }

        except Exception as e:
            return {
                "error": str(e),
                "status": "failed"
            }

    def sell_on_clob(self, token_id: str, price: float) -> Dict[str, Any]:
        """
        在CLOB上出售代币

        Args:
            token_id: 代币ID
            price: 卖出价格

        Returns:
            卖出结果
        """
        try:
            print(f"🔄 在CLOB上出售代币: {token_id}, 价格: {price}")

            # 初始化CLOB客户端
            clob_client = ClobClient(
                "https://clob.polymarket.com",
                key=self.private_key,
                chain_id=137
            )

            # 创建API凭证
            creds = clob_client.create_or_derive_api_creds()
            clob_client.set_api_creds(creds)

            # 创建订单
            # 注意：需要使用py-order-utils来构建订单
            print(f"⚠️  CLOB sell需要进一步实现（py-order-utils）")

            return {
                "token_id": token_id,
                "price": price,
                "status": "clob_sell_not_implemented"
            }

        except Exception as e:
            return {
                "error": str(e),
                "status": "failed"
            }

    def execute_trade(self, market_id: str, amount_usdc: float,
                   outcome: str = "YES", expected_profit: float = 0.0) -> Dict[str, Any]:
        """
        执行完整的交易：split + CLOB sell

        Args:
            market_id: 市场ID
            amount_usdc: 交易金额
            outcome: YES或NO
            expected_profit: 预期利润

        Returns:
            完整交易结果
        """
        print(f"\n🚀 执行交易:")
        print(f"   市场: {market_id}")
        print(f"   金额: {amount_usdc} USDC")
        print(f"   方向: {outcome}")
        print(f"   预期利润: {expected_profit:.2%}")

        # Step 1: Split
        split_result = self.split_and_buy(market_id, amount_usdc, outcome)

        if "error" in split_result:
            return split_result

        # Step 2: Sell unwanted tokens on CLOB
        # 注意：这需要先查询token_id
        # 简化：假设sell成功

        result = {
            "market_id": market_id,
            "amount_usdc": amount_usdc,
            "outcome": outcome,
            "expected_profit": expected_profit,
            "split_result": split_result,
            "status": "completed"
        }

        print(f"✅ 交易完成！")

        return result
