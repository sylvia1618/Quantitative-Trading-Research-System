# 开发指南

## 😊 欢迎贡献

感谢您对 QuantFlow Lab 的兴趣！本指南将帮助您快速上手开发。

## 🛠️ 开发环境设置

### 1. 克隆仓库

```bash
git clone https://github.com/sylvia1618/Sylvia-s-Quant.git
cd QuantFlow_Lab
```

### 2. 创建虚拟环境

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

### 3. 安装开发依赖

```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt  # 如果有
```

## 📝 代码规范

### Python 代码风格

- 遵循 [PEP 8](https://www.python.org/dev/peps/pep-0008/) 风格指南
- 使用 `black` 进行代码格式化
- 使用 `flake8` 进行代码检查

```bash
# 格式化代码
black core/ models/ app/

# 检查代码风格
flake8 core/ models/ app/

# 类型检查
mypy core/ models/ app/
```

### 文档字符串

所有公开函数和类都应该有文档字符串：

```python
def calculate_rsi(prices: pd.Series, period: int = 14) -> pd.Series:
    """
    计算相对强度指数 (RSI)
    
    Args:
        prices: 价格序列
        period: 计算周期
    
    Returns:
        RSI 指标序列
    
    Examples:
        >>> prices = pd.Series([100, 102, 101, 103])
        >>> rsi = calculate_rsi(prices, period=14)
    """
    # 实现代码
```

## 🧪 单元测试

### 编写测试

```bash
# 在 tests/ 目录下创建测试文件
touch tests/test_new_module.py

# 编写测试
# 遵循 unittest 框架
```

### 运行测试

```bash
# 运行所有测试
python -m pytest tests/

# 运行特定测试
python -m pytest tests/test_factors.py

# 生成覆盖率报告
pytest --cov=core tests/
```

## 📦 模块开发指南

### 新增因子

1. 在 `core/factors/` 下创建对应文件
2. 实现因子计算函数
3. 添加单元测试
4. 更新 `core/factors/__init__.py`

### 新增模块

1. 在对应目录创建新文件
2. 编写逻辑代码
3. 添加充分的文档和测试
4. 更新 README.md

## 🐛 提交流程

### 1. 创建分支

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/your-bug-fix-name
```

### 2. 提交代码

```bash
git add .
git commit -m "描述你的改动"
```

### 提交信息规范

- feat: 新功能
- fix: 修复错误
- docs: 文档更改
- style: 代码风格改变（不影响功能）
- refactor: 代码重构
- test: 添加或修改测试
- perf: 性能优化

示例：
```
feat: 添加 Bollinger Bands 因子计算函数
fix: 修复 MA 计算中的缺失值处理
docs: 更新 README 中的快速开始部分
```

### 3. 推送和 PR

```bash
git push origin feature/your-feature-name
```

然后在 GitHub 上创建 Pull Request

### PR 检查清单

- [ ] 代码遵循项目风格指南
- [ ] 添加了单元测试
- [ ] 更新了相关文档
- [ ] 提交信息清晰明确
- [ ] 通过了所有 CI 检查

## 📋 项目结构维护

### 添加新依赖

```bash
# 直接安装
pip install package_name

# 添加到 requirements.txt
pip freeze > requirements.txt
```

### 配置更改

所有配置项应该在 `config.yaml` 中定义，避免硬编码。

## 💡 最佳实践

### 1. 代码复用

- 提取公共逻辑到 `core/` 模块
- 避免重复代码
- 使用继承和组合

### 2. 错误处理

```python
try:
    # 代码
except SpecificException as e:
    logger.error(f"Error: {e}")
    raise  # 或处理异常
```

### 3. 性能考虑

- 使用向量化操作（NumPy/Pandas）
- 避免循环
- 考虑内存使用

### 4. 日志记录

```python
import logging
logger = logging.getLogger(__name__)

logger.info("开始处理数据")
logger.debug("调试信息")
logger.warning("警告信息")
logger.error("错误信息")
```

## 📚 有用的资源

- [Pandas 文档](https://pandas.pydata.org/docs/)
- [NumPy 文档](https://numpy.org/doc/)
- [scikit-learn 文档](https://scikit-learn.org/stable/documentation.html)
- [PEP 8 风格指南](https://www.python.org/dev/peps/pep-0008/)

## 🚀 发布流程

### 版本号规范

遵循 [语义化版本](https://semver.org/lang/zh-CN/) (SemVer)：
- MAJOR: 有不兼容的 API 改动
- MINOR: 新增功能，向下兼容
- PATCH: 修复错误，向下兼容

### 发布步骤

1. 更新 `__version__` 和 CHANGELOG
2. 创建 Release 标签
3. 部署到生产环境

## ❓ 常见问题

### 如何报告 Bug？

在 GitHub Issues 中创建 Issue，包含：
- 详细的错误描述
- 复现步骤
- 期望行为
- 环境信息（OS、Python 版本等）

### 如何建议新功能？

在 Discussions 中提出，或创建 "Enhancement" 标签的 Issue

### 如何获得帮助？

- 查看现有 Issues 和 Discussions
- 提交问题前搜索相关关键词
- 在 Discussions 中提问

---

感谢您的贡献！🙏
