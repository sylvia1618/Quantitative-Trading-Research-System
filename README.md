# QuantFlow Lab 📊

一个专业的**量化选股研究平台**，集数据获取、因子挖掘、模型训练、回测分析于一体。

## 🎯 核心特性

### 1. **数据层** 💾
- 对接 **Tushare** 和 **AkShare** 获取实时数据
- 支持日线、财务、行业分类等多类型数据
- 自动化增量更新机制
- 数据版本管理与缓存

### 2. **因子库** 🧬
- **动量因子**: RSI, MACD, Momentum, ROC, Bollinger Bands, VWAP
- **基本面因子**: PE, PB, PS, ROE, ROA, 增长率等
- **自定义因子**: 支持扩展因子库
- **因子预处理**: 去极值、标准化、行业中性化

### 3. **审计引擎** 📈
- **IC/ICIR 计算**: 衡量因子有效性
- **分组收益分析**: 评估因子选股能力
- **因子穩定性检验**: 排序有效性检验

### 4. **机器学习** 🤖
- **XGBoost/LightGBM**: 多因子预测模型
- **特征选择**: 相关性、互信息、RFE、特征重要性
- **交叉验证**: 防止过拟合

### 5. **回测引擎** ⚙️
- **高性能回测**: 基于数组计算
- **风险指标**: 夏普比率、最大回撤、Calmar 比率
- **可视化分析**: 净值、回撤、分布等
- **经济学有效性**: 考虑手续费与滑点

### 6. **展示平台** 🚀
- **Streamlit 界面**: 交互式分析工具
- **数据管理**: 上传、清洗原始数据，生成标准因子
- **单因子分析**: 因子有效性可视化
- **多因子模型**: 模型性能对比和特征选择
- **组合回测**: 策略回测与指标展示
- **风险面板**: 实时风险监控

---

## 📁 项目结构

```
QuantFlow_Lab/
├── data/                      # 【数据层】
│   ├── raw/                   # 原始数据 (CSV/Parquet)
│   ├── processed/             # 清洗、中性化后的标准数据
│   └── metadata/              # 股票列表、行业分类、交易日历
│
├── research/                  # 【研究层】Jupyter Notebook
│   ├── alpha_discovery/       # 因子挖掘脚本
│   └── EDA/                   # 数据探索性分析
│
├── core/                      # 【核心逻辑层】Python 包
│   ├── __init__.py
│   ├── data_engine.py         # 数据获取与管理
│   ├── preprocessor.py        # 数据预处理 (去极值、标准化等)
│   ├── auditor.py             # 因子审计 (IC/ICIR 计算)
│   ├── backtester.py          # 回测引擎
│   └── factors/               # 因子库
│       ├── momentum.py        # 动量因子
│       └── fundamental.py     # 基本面因子
│
├── models/                    # 【机器学习层】
│   ├── trainer.py             # 模型训练流程
│   └── feature_select.py      # 特征选择
│
├── app/                       # 【展示层】Streamlit 应用
│   ├── main.py                # 主入口
│   └── pages/                 # 多页面
│       ├── data_manager.py    # 数据管理与清洗
│       ├── single_factor.py   # 单因子分析
│       ├── multi_factor.py    # 多因子模型
│       ├── backtest.py        # 回测分析
│       └── risk_analysis.py   # 风险面板
│
├── tests/                     # 单元测试
├── config.yaml                # 全局配置
├── requirements.txt           # 环境依赖
├── .gitignore                 # Git 忽略规则
└── README.md                  # 项目说明
```

---

## 🚀 快速开始

### 1️⃣ 环境准备

```bash
# 克隆项目
git clone https://github.com/sylvia1618/Sylvia-s-Quant.git
cd QuantFlow_Lab

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

### 2️⃣ 配置 API

编辑 `config.yaml`，填入相关 API Token：

```yaml
data:
  tushare_token: "your_token_here"
```

获取 Tushare Token：https://tushare.pro/

### 3️⃣ 获取数据

```python
from core.data_engine import DataEngine

config = {"tushare_token": "your_token"}
engine = DataEngine(config)

# 获取股票列表
stocks = engine.get_stock_list()

# 获取日线数据
df = engine.get_daily_data("000001.SZ", "2020-01-01", "2023-12-31")
```

### 4️⃣ 计算因子

```python
from core.factors.momentum import MomentumFactors
from core.factors.fundamental import FundamentalFactors

# 计算 RSI
rsi = MomentumFactors.calculate_rsi(df['close'], period=14)

# 计算 PE 比率
pe = FundamentalFactors.calculate_pe(market_cap, earnings)
```

### 5️⃣ 因子评估

```python
from core.auditor import FactorAuditor

auditor = FactorAuditor()

# 计算 IC
ic = auditor.calculate_ic(factor_values, returns)

# 计算 ICIR
icir = auditor.calculate_icir(window=20)

# 分组收益
group_returns = auditor.group_returns(factor_values, returns, n_groups=5)
```

### 6️⃣ 回测策略

```python
from core.backtester import Backtester, BacktestConfig

config = BacktestConfig(initial_capital=1000000, commission=0.001)
backtester = Backtester(config)

results = backtester.run_backtest(prices, signals)
print(f"年化收益率: {results['annual_return']:.2%}")
print(f"夏普比率: {results['sharpe_ratio']:.2f}")
print(f"最大回撤: {results['max_drawdown']:.2%}")
```

### 7️⃣ 启动 Web 应用

```bash
streamlit run app/main.py
```

访问 `http://localhost:8501` 查看应用

---

## 📚 详细使用示例

### 单因子分析完整流程

```python
import pandas as pd
from core.data_engine import DataEngine
from core.preprocessor import DataPreprocessor
from core.factors.momentum import MomentumFactors
from core.auditor import FactorAuditor

# 1. 获取数据
engine = DataEngine(config)
prices = engine.get_daily_data("000001.SZ", "2020-01-01", "2023-12-31")

# 2. 数据预处理
preprocessor = DataPreprocessor()
returns = preprocessor.handle_missing(prices['close'].pct_change())

# 3. 计算因子
rsi = MomentumFactors.calculate_rsi(prices['close'], period=14)

# 4. 因子评估
auditor = FactorAuditor()
ic = auditor.calculate_ic(rsi, returns)
icir = auditor.calculate_icir(window=20)

print(f"IC = {ic:.4f}, ICIR = {icir:.4f}")
```

### 多因子模型训练

```python
from models.trainer import ModelTrainer
from models.feature_select import FeatureSelector

# 1. 特征选择
selector = FeatureSelector()
selected_features = selector.select_by_importance(X, y, n_features=20)

# 2. 准备数据
trainer = ModelTrainer(model_type="xgboost")
X_train, X_test, y_train, y_test = trainer.prepare_data(X[selected_features], y)

# 3. 训练模型
trainer.train(X_train, y_train, n_estimators=100, max_depth=6)

# 4. 评估性能
metrics = trainer.evaluate(X_test, y_test)
print(f"R² Score: {metrics['r2_score']:.4f}, RMSE: {metrics['rmse']:.4f}")

# 5. 特征重要性
importance = trainer.get_feature_importance()
```

---

## 🛠️ 核心模块 API

### DataEngine 数据引擎

| 方法 | 说明 |
|------|------|
| `get_stock_list()` | 获取股票列表 |
| `get_daily_data(code, start, end)` | 获取日线数据 |
| `get_financial_data(code, period)` | 获取财务数据 |
| `incremental_update()` | 增量更新 |

### FactorAuditor 因子审计

| 方法 | 说明 |
|------|------|
| `calculate_ic()` | 计算信息系数 |
| `calculate_icir()` | 计算 IC 信息比率 |
| `group_returns()` | 分组收益分析 |
| `calculate_cumulative_returns()` | 累积收益率 |

### Backtester 回测引擎

| 方法 | 说明 |
|------|------|
| `run_backtest()` | 执行回测 |

---

## 📊 输出报告

系统生成以下分析报告：

- **因子报告**: IC/ICIR, 分组收益, 因子稳定性
- **模型报告**: 特征重要性, 交叉验证结果, 性能对比
- **回测报告**: 累积收益, 最大回撤, 夏普比率, 风险指标

---

## 📖 参考资源

- [Tushare 数据接口](https://tushare.pro/)
- [XGBoost 文档](https://xgboost.readthedocs.io/)
- [LightGBM 文档](https://lightgbm.readthedocs.io/)
- [Streamlit 文档](https://docs.streamlit.io/)
- [量化研究指南](https://www.joinquant.com/)

---

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

如果您想贡献代码：

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 发起 Pull Request

---

## ⚖️ 免责声明

本项目仅供学习和研究使用，不构成任何投资建议。使用本项目代码进行的任何交易决策均由使用者自己承担。

---

## 📝 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

---

## 📧 联系方式

- GitHub: [sylvia1618](https://github.com/sylvia1618)
- Email: your.email@example.com

---

## 📈 更新日志

### v0.1.0 (2024-03-03)
- ✅ 项目初始化
- ✅ 核心模块框架搭建
- ✅ Streamlit 应用基础框架
- 🚧 多因子模型优化中...

---

**⭐ 如果觉得项目有帮助，请给个 Star！**
