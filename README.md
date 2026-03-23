# LLM Agent Trading Bot

> 基于LLM大模型的智能预测市场套利交易系统

结合 **polyclaw 的 LLM 分析能力** 和 **polymarket-arbitrage-bot 的多策略套利**，打造一个智能的 Agent 交易系统。

---

## 🎯 项目特点

### 核心能力

1. **智能市场扫描** - 自动发现套利机会和对冲机会
2. **LLM 驱动分析** - 使用大模型进行市场分析和风险评估
3. **多 Agent 协作** - 5 个专业 Agent 各司其职
4. **三大策略系统** - 套利、对冲、趋势策略，统一管理
5. **完整对冲逻辑** - LLM 识别相关市场，智能构建对冲组合
6. **真实交易支持** - Web3 集成，支持 Polygon 链上交易
7. **策略表现追踪** - 胜率、夏普比率、最大回撤等指标
8. **实时风险监控** - 动态风险控制和止损

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
# 启动所有 Agents
python main.py --mode auto

# 启动单个 Agent
python main.py --mode auto --agent market_scout
```

#### 使用策略系统

```python
from strategies import StrategyManager
from core.polymarket_client import PolymarketClient

# 初始化
pm_client = PolymarketClient(gamma_api_url="...")
manager = StrategyManager(config)

# 扫描市场
markets = pm_client.get_markets(limit=50)

# 分析机会（所有策略）
opportunities = manager.scan_markets(markets)

# 选择最佳机会
best_signal = manager.select_best_opportunity(opportunities)

# 查看策略表现
performance = manager.get_strategy_performance()
```

#### 测试对冲逻辑

```bash
python test_hedge_logic.py
```

#### 测试真实交易（需要钱包）

```bash
# 设置环境变量
export POLYGON_WALLET_PRIVATE_KEY="0x..."
export OPENROUTER_API_KEY="sk-or-v1-..."

# 运行测试
python test_real_trading.py
```

---

## 📊 工作流程

### 自动模式

```
市场情报员 → 扫描 Polymarket 市场
    ↓
    收集市场数据（价格、成交量、流动性）
    ↓
策略管理器 → 应用多策略分析
    ├─ 套利策略：检测价格偏差
    ├─ 对冲策略：LLM分析相关性
    └─ 趋势策略：识别价格趋势
    ↓
    生成交易信号（信号类型、方向、金额、信心度）
    ↓
LLM 分析师 → 深度市场分析
    ├─ 市场情绪评估
    ├─ 风险等级判断
    └─ 策略优化建议
    ↓
策略执行员 → 评估交易信号
    ├─ 验证信号有效性
    ├─ 计算风险收益比
    └─ 检查仓位限制
    ↓
    执行交易（Web3 签名）
    ↓
风险管家 → 实时监控
    ├─ 追踪仓位价值
    ├─ 检测止损条件
    └─ 发出调整信号
    ↓
记录员 → 记录所有交易
    ├─ 保存交易历史
    ├─ 计算盈亏分析
    └─ 生成表现报告
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

## 💰 交易策略

本系统提供完整的交易策略系统，包含三大核心策略：

### 1. 套利策略（Arbitrage Strategy）
- 检测 YES/NO 价格偏差
- 自动计算套利空间（扣除 3.15% 费用）
- 流动性和成交量验证
- 自适应仓位大小调整

**特点**：
- 最低利润阈值可配置（默认 2%）
- 最大套利空间限制（避免数据错误）
- 基于流动性的仓位管理

### 2. 对冲策略（Hedge Strategy）
- LLM 驱动的市场相关性分析
- 智能发现相关市场对
- 风险对冲组合构建
- 对冲质量评分系统

**特点**：
- 自动计算覆盖度（Coverage Ratio）
- 识别做多/做空方向
- 评估对冲成本和利润
- 完整的对冲执行流程

### 3. 趋势策略（Trend Strategy）
- 基于历史价格的趋势识别
- 线性回归计算趋势强度
- 量价结合分析
- 波动性风险评估

**特点**：
- 12小时趋势窗口
- 最小趋势强度要求（默认 10%）
- 成交量验证
- 动态仓位调整

### 策略管理

所有策略由 `StrategyManager` 统一管理：
- 动态启用/禁用策略
- 自动选择最佳交易信号
- 策略表现对比（胜率、夏普比率等）
- 按利润/风险优先级排序

---

## 🔀 完整对冲逻辑

### 对冲发现流程

```
1. 市场扫描 → 提取市场摘要
                ↓
2. LLM 分析 → 识别相关市场
              计算相关性
              评估覆盖度
                ↓
3. 评估验证 → 检查成本限制
              风险等级评分
              利润潜力分析
                ↓
4. 执行交易 → 做多: 市场1 YES + 市场2 NO
              做空: 市场1 NO + 市场2 YES
                ↓
5. 记录追踪 → 保存交易结果
              更新策略表现
```

### 关键特性

**智能发现**：
- LLM 理解市场问题的语义
- 自动识别相关事件
- 计算市场相关性（0-1）

**风险评估**：
- 多维度评分系统
- 成本和利润验证
- 风险等级（low/medium/high）

**执行控制**：
- 自动/手动模式
- 最大对冲成本限制（默认 5%）
- 最小利润阈值（默认 1%）

**表现追踪**：
- 成功率统计
- 总成本和利润
- 平均执行时间

### 测试对冲逻辑

```bash
python test_hedge_logic.py
```

注意：真实的 LLM 分析需要设置 `OPENROUTER_API_KEY`

---

## ⚙️ 配置说明

主要配置项（`config/settings.yaml`）：

**交易配置**：
- `trading.enabled` - 是否启用交易
- `trading.max_position_size` - 最大单笔交易金额（USDC）
- `trading.enable_auto_trade` - 是否自动执行交易

**Agent 配置**：
- `agents.market_scout.scan_interval` - 市场扫描间隔（秒）
- `agents.llm_analyst.model` - LLM 模型名称
- `agents.strategy_executor.auto_execute` - 策略执行员自动执行

**策略配置**：
- `strategies.arbitrage.enabled` - 启用套利策略
- `strategies.arbitrage.min_arbitrage_space` - 最小套利空间（默认 3%）
- `strategies.hedge.enabled` - 启用对冲策略
- `strategies.hedge.min_coverage_ratio` - 最小覆盖度（默认 90%）
- `strategies.hedge.max_correlation_cost` - 最大对冲成本（默认 5%）
- `strategies.trend.enabled` - 启用趋势策略
- `strategies.trend.trend_window` - 趋势窗口（小时）
- `strategies.trend.min_trend_strength` - 最小趋势强度（默认 10%）

**对冲配置**：
- `hedge_executor.auto_execute` - 自动执行对冲
- `hedge_executor.max_hedge_cost` - 最大对冲成本（默认 5%）
- `hedge_executor.min_hedge_profit` - 最小利润（默认 1%）

**LLM 配置**：
- `llm.api_key` - OpenRouter API 密钥
- `llm.model` - 使用的 LLM 模型

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
│   ├── polymarket_client.py    # Polymarket API 客户端
│   └── web3_trader.py          # Web3 交易客户端
├── strategies/                # 交易策略系统
│   ├── base_strategy.py         # 策略基类
│   ├── arbitrage_strategy.py    # 套利策略
│   ├── hedge_strategy.py        # 对冲策略
│   ├── trend_strategy.py        # 趋势策略
│   ├── hedge_executor.py       # 对冲执行器
│   └── strategy_manager.py      # 策略管理器
├── lib/                       # 第三方库
│   └── polymarket_real.py       # 官方 Web3 客户端
├── database/                  # 数据库文件（运行时创建）
├── config/
│   ├── settings.yaml            # 主配置文件
│   └── test_real_trading.yaml   # 真实交易配置
├── test_*.py                  # 测试脚本
├── main.py                    # 主入口
├── requirements.txt            # Python 依赖
├── README.md                  # 本文件
├── PROJECT_SUMMARY.md          # 项目总结
├── OPTIMIZATION_PLAN.md        # 优化计划
└── LICENSE                    # MIT 许可证
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

- [ ] 集成更多高级策略（Liquidity Absorption、Structural Spread 等）
- [ ] 添加数据可视化和 Dashboard
- [ ] 实现回测功能
- [ ] 集成 OpenClaw Skill（作为 OpenClaw 插件运行）
- [ ] 添加更多链上查询功能
- [ ] 完善风险管理和自动止损（多级止损策略）
- [ ] 支持多个钱包账户

---

## 🤝 开发阶段

当前状态：**核心功能已完成，可用于实际交易**

已完成：
- [x] Agent 框架和消息总线
- [x] 状态管理系统（SQLite）
- [x] 5 个 Agents 的完整实现
- [x] LLM 分析集成（OpenRouter API）
- [x] Polymarket API 客户端
- [x] Web3 交易客户端（真实交易支持）
- [x] 配置系统（YAML）
- [x] 交互和自动运行模式
- [x] **完整的三策略系统**（套利、对冲、趋势）
- [x] **LLM 驱动的对冲逻辑**
- [x] 策略管理器（统一管理和选择）
- [x] 表现追踪和统计

待完善：
- [ ] 集成更多高级策略
- [ ] 添加数据可视化和 Dashboard
- [ ] 回测功能
- [ ] 集成 OpenClaw Skill（作为 OpenClaw 插件运行）
- [ ] 更多链上查询和优化

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
