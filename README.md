# LLM Agent Trading Bot

> 基于LLM大模型的智能预测市场套利交易系统

结合 **polyclaw 的 LLM 分析能力** 和 **polymarket-arbitrage-bot 的多策略套利**，打造一个智能的 Agent 交易系统。

---

## 🎯 项目特点

### 核心能力

1. **智能市场扫描** - 自动发现套利机会和对冲机会
2. **LLM 驱动分析** - 使用大模型进行市场分析和风险评估
3. **多 Agent 协作** - 5 个专业 Agent 各司其职
4. **7 种套利策略** - 集成多种成熟的交易策略
5. **实时风险监控** - 动态风险控制和止损

### Agent 架构

| Agent | 角色 | 职责 |
|-------|------|------|
| **市场情报员** | market_scout | 扫描市场、识别机会、热点分析 |
| **LLM 分析师** | llm_analyst | 市场分析、趋势预测、风险评估 |
| **策略执行员** | strategy_executor | 执行套利策略、下单、仓位管理 |
| **风险管家** | risk_manager | 风险控制、仓位监控、止损执行 |
| **记录员** | trade_logger | 交易记录、盈亏分析、数据可视化 |

---

## 🚀 快速开始

### 1. 环境要求

- Python 3.8+
- OpenRouter API Key (用于 LLM 分析)
- Chainstack Node URL (可选，用于链上查询)

### 2. 安装依赖

```bash
cd llm-agent-trading-bot
pip install -r requirements.txt
```

### 3. 配置

复制并编辑配置文件：

```bash
cp config/settings.yaml config/settings.local.yaml
# 编辑 settings.local.yaml，设置你的 API keys
```

设置环境变量：

```bash
export OPENROUTER_API_KEY="sk-or-v1-..."
export CHAINSTACK_NODE="https://polygon-mainnet.core.chainstack.com/YOUR_KEY"
```

### 4. 运行

#### 交互模式（推荐）

```bash
python main.py --mode interactive
```

可用命令：
- `status` - 显示所有 Agents 状态
- `scan` - 执行市场扫描
- `agent <id>` - 查看/启动指定 Agent
- `help` - 显示帮助

#### 自动模式

```bash
python main.py --mode auto

# 启动所有 Agents
python main.py --mode auto

# 启动单个 Agent
python main.py --mode auto --agent market_scout
```

---

## 📊 工作流程

### 自动模式

```
市场情报员 → 扫描 Polymarket 市场
    ↓
    发现套利机会 + 对冲机会
    ↓
LLM 分析师 → 深度分析市场
    ↓
    输出分析结果 + 策略推荐
    ↓
策略执行员 → 评估机会
    ↓
    决定是否执行（考虑风险限制）
    ↓
风险管家 → 实时监控
    ↓
    止损 / 调整仓位
    ↓
记录员 → 记录所有交易
    ↓
    生成报告
```

### 交互模式

在交互模式中，你可以：

```
[主控] > status                    # 查看所有 Agents 状态
[主控] > scan                     # 扫描热门市场
[主控] > agent market_scout       # 查看市场情报员状态
[主控] > start llm_analyst        # 启动 LLM 分析师
[主控] > help                     # 查看帮助
```

---

## 💰 套利策略

本系统集成了以下 7 种策略（参考 polymarket-arbitrage-bot）：

1. **Liquidity Absorption Flip** - 利用流动性价格差
2. **Orderbook Arbitrage** - YES+NO < 1.0 时的价差套利
3. **Structural Spread** - 结构化价差锁定
4. **NO Farming** - 系统性押注 NO（利用人群过度反应）
5. **Long Tail Floor** - 长尾事件的低概率押注
6. **Spread Farming** - 高概率合约的价差复利
7. **High Probability Auto-Compounding** - 高概率自动复利

---

## ⚙️ 配置说明

主要配置项（`config/settings.yaml`）：

- `trading.enabled` - 是否启用交易
- `trading.max_position_size` - 最大单笔交易金额
- `trading.enable_auto_trade` - 是否自动执行交易
- `agents.market_scout.scan_interval` - 市场扫描间隔（秒）
- `agents.llm_analyst.model` - LLM 模型名称
- `strategies.*.enabled` - 各策略是否启用

---

## 🗂️ 项目结构

```
llm-agent-trading-bot/
├── agents/                    # Agents 实现
│   ├── market_scout.py
│   ├── llm_analyst.py
│   └── simplified_agents.py   # 策略执行员、风险管家、记录员
├── core/                     # 核心组件
│   ├── agent_base.py           # Agent 基类
│   ├── state_manager.py         # 状态管理器
│   ├── llm_client.py           # LLM 客户端
│   └── polymarket_client.py    # Polymarket API 客户端
├── database/                 # 数据库文件（运行时创建）
├── config/
│   └── settings.yaml           # 主配置文件
├── main.py                   # 主入口
├── requirements.txt            # Python 依赖
└── README.md                 # 本文件
```

---

## 🔐 安全说明

⚠️ **重要：本软件仅供教育和实验目的**

- 不构成财务建议
- 预测市场交易涉及损失风险
- 代码未经审计
- 仅使用你能承受损失的资金
- 建议先在测试环境充分测试

---

## 📝 TODO

- [ ] 完善所有 7 种套利策略的具体实现
- [ ] 集成真实的 Web3 交易执行（需要钱包私钥）
- [ ] 实现完整的对冲逻辑（polyclaw 的 hedge scan）
- [ ] 添加数据可视化和 Dashboard
- [ ] 完善风险管理和自动止损
- [ ] 添加回测功能
- [ ] 集成 OpenClaw Skill（作为 OpenClaw 插件运行）

---

## 🤝 开发阶段

当前状态：**基础框架已完成**

已完成：
- [x] Agent 框架和消息总线
- [x] 状态管理系统
- [x] 5 个 Agents 的基础实现
- [x] LLM 分析集成
- [x] Polymarket API 客户端
- [x] 配置系统
- [x] 交互和自动运行模式

待完善：
- [ ] 完整的 7 种策略实现
- [ ] Web3 交易执行
- [ ] 风险管理增强
- [ ] 数据记录和分析
- [ ] 测试和优化

---

## 📚 参考资料

- [polyclaw](https://github.com/chainstacklabs/polymarket-alpha-bot/tree/main/polyclaw) - OpenClaw 技能
- [polymarket-arbitrage-bot](https://github.com/apemoonspin/polymarket-arbitrage-trading-bot) - 套利策略
- [Polymarket API](https://docs.polymarket.com) - Polymarket 文档
- [OpenRouter](https://openrouter.ai) - LLM API

---

## 📝 License

MIT

---

**Ready to trade with AI-powered intelligence?** 🚀
