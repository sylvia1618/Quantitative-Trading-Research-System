# QuantFlow Lab 变更日志

所有对本项目的显著改动都会被记录在此文件中。

本项目遵循 [语义化版本](https://semver.org/lang/zh-CN/) 规则。

## [未发布]

### 计划中
- [ ] 因子库扩展：组合类因子、非线性因子
- [ ] 模型优化：深度学习模型支持
- [ ] 实时监控：因子信号实时追踪
- [ ] 性能优化：GPU 并行计算支持
- [ ] 风险管理：投资组合最优化

---

## [0.1.0] - 2024-03-03

### 新增 ✨
- 初始项目框架搭建
- 数据层（DataEngine）：支持 Tushare/AkShare 数据获取
- 因子库：完整的动量因子和基本面因子实现
  - 动量因子：RSI、MACD、Momentum、ROC、Bollinger Bands、VWAP
  - 基本面因子：PE、PB、PS、ROE、ROA、增长率、流动性指标
- 预处理模块（DataPreprocessor）：去极值、标准化、行业中性化
- 审计模块（FactorAuditor）：IC/ICIR 计算、分组收益分析
- 回测引擎（Backtester）：高性能回测、风险指标计算
- 模型层：基于 XGBoost/LightGBM 的多因子模型训练
- 特征选择：相关性、互信息、RFE、特征重要性分析
- Streamlit 应用框架：交互式分析平台
- 单元测试框架

### 配置 🛠️
- config.yaml：全局配置管理
- requirements.txt：项目依赖管理
- .gitignore：Git 忽略规则
- 项目初始化脚本（init.py）

### 文档 📖
- 详细的 README.md
- 开发贡献指南（CONTRIBUTING.md）
- MIT 许可证

### 修复 🔧
- 无

### 已弃用 ⚠️
- 无

---

## 版本对比

### v0.1.0 vs 预期的 v1.0.0

| 功能 | v0.1.0 | v1.0.0 | 说明 |
|------|--------|--------|------|
| 数据获取 | ✅ | ✅ | 完整实现 |
| 因子计算 | ✅ | 📈 | 需扩展非线性因子 |
| 模型训练 | ✅ | 📈 | 计划添加深度学习 |
| 回测引擎 | ✅ | 🔄 | 需性能优化 |
| Web 应用 | 🟡 | ✅ | 功能完善中 |
| GPU 支持 | ❌ | 📋 | 计划中 |
| 实时监控 | ❌ | 📋 | 计划中 |

---

## 升级指南

### 从 v0.0.x 到 v0.1.0

1. 更新依赖：`pip install -r requirements.txt`
2. 配置文件：创建 `config.yaml` 并填入 API Token
3. 运行初始化脚本：`python init.py`
4. 阅读新文档：查看更新的 README.md

---

## 贡献者

- [@sylvia1618](https://github.com/sylvia1618) - 项目创建者

---

## 许可证

本项目遵循 MIT License - 详见 [LICENSE](LICENSE)
