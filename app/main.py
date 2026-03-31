import sys
import os
import importlib 
from pathlib import Path
import streamlit as st

# =========================================================
# 1. 环境与路径配置 (精简合并)
# =========================================================
current_file = Path(__file__).resolve()
root_dir = current_file.parent.parent
os.chdir(root_dir) 

if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

# =========================================================
# =========================================================
# 2. 页面配置与视觉主题 (Pink Edition)
# =========================================================
st.set_page_config(
    page_title="QuantFlow Lab | 交互式量化研究平台",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 🔥 核心视觉修改：在这里注入全局粉色样式
st.markdown("""
    <style>
    /* 1. 主界面背景 */
    .main { background-color: #fff5f8; }

    /* 2. 侧边栏：彻底改为清晰的粉色系 */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #fff0f6 0%, #ffdeeb 100%) !important;
        border-right: 2px solid #f783ac;
    }
    
    /* 3. 侧边栏文字：深玫瑰红（解决看不清的问题） */
    [data-testid="stSidebar"] .stText, 
    [data-testid="stSidebar"] label, 
    [data-testid="stSidebar"] .stMarkdown p,
    [data-testid="stSidebar"] .stRadio label {
        color: #ad1457 !important; 
        font-weight: 700 !important;
        font-size: 1rem;
    }

    /* 4. 侧边栏标题 */
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
        color: #d81b60 !important;
    }

    /* 5. 所有的 Metric 指标卡：变粉白相间 */
    .stMetric {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(247, 131, 172, 0.1);
        border: 2px solid #ffdeeb;
    }
    
    /* 6. 指标卡数值颜色 */
    [data-testid="stMetricValue"] {
        color: #d81b60 !important;
    }

    /* 7. 分割线颜色 */
    hr { border-top: 1px solid #f783ac !important; }

    /* 8. Radio 选中项的圆点颜色 */
    div[data-testid="stMarkdownContainer"] > p { font-weight: 600; }
    </style>
    """, unsafe_allow_html=True)

# =========================================================
# 3. 核心功能函数 (看板展示)
# =========================================================
def show_home():
    st.title("🚀 QuantFlow Lab - 数字化量化研究中心")
    st.info("欢迎来到 Sylvia 的量化实验室。本平台专注于因子挖掘、审计与策略回测。")
    
    col1, col2, col3, col4 = st.columns(4)
    # 此处数据未来可以从 data_manager 动态获取
    with col1: st.metric("本地票池", "5,662", delta="A-Share Full")
    with col2: st.metric("审计版本", "Dual-Pool", delta="Raw & Neutral")
    with col3: st.metric("计算引擎", "Vectorized", delta="High Speed")
    with col4: st.metric("系统版本", "v1.3.0", delta="Stable")
    
    st.divider()
    
    st.header("📋 研究工作流")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.subheader("1. 🔬 因子审计")
        st.write("从预测力、稳定性、单调性、分布质量四个维度对因子进行全方位体检。")
    with c2:
        st.subheader("2. 🤖 因子合成")
        st.write("处理因子共线性，使用机器学习或 IC 加权合成最终信号。")
    with c3:
        st.subheader("3. 📈 组合回测")
        st.write("验证策略在真实市场环境下的盈利能力与回撤特征。")

# =========================================================
# 4. 主程序入口与动态路由
# =========================================================
def main():
    with st.sidebar:
        st.image("https://img.icons8.com/fluency/96/000000/bar-chart.png", width=80)
        st.header("QuantFlow 导航")
        
        menu_options = {
            "🏠 主页": "Home",
            "📂 数据管理": "Data",
            "🔬 单因子审计": "SingleFactor",
            "🔗 因子相关性": "Correlation",
            "🤖 多因子模型": "MultiFactor",
            "📈 组合回测": "Backtest",
            "⚠️ 风险分析": "Risk"
        }
        
        selection = st.radio("前往功能模块", list(menu_options.keys()))
        
        st.divider()
        st.caption(f"🐍 Python: {sys.version.split()[0]}")
        st.caption(f"📂 Root: `{root_dir.name}/`")

    # --- 路由分发 ---
    try:
        if "主页" in selection:
            show_home()
            
        elif "数据管理" in selection:
            import app.pages.data_manager as dm_page
            importlib.reload(dm_page)
            dm_page.show_data_manager()
            
        elif "单因子审计" in selection:
            # 💡 核心：强制重载核心算法与交互页面
            import core.auditor as auditor_module
            import app.pages.single_factor as sf_page
            
            importlib.reload(auditor_module)
            importlib.reload(sf_page)
            
            sf_page.show_single_factor()
            
        elif "因子相关性" in selection:
            import app.pages.factor_correlation as corr_page
            importlib.reload(corr_page)
            corr_page.show_correlation_page()
            
        elif "多因子模型" in selection:
            import app.pages.multi_factor as mf_page
            importlib.reload(mf_page)
            mf_page.show_multi_factor()
            
        elif "组合回测" in selection:
            import app.pages.backtest as bt_page
            importlib.reload(bt_page)
            bt_page.show_backtest()
            
        elif "风险分析" in selection:
            import app.pages.risk_analysis as risk_page
            importlib.reload(risk_page)
            risk_page.show_risk_analysis()

    except ModuleNotFoundError as e:
        st.error(f"❌ 运行失败：找不到模块 `{e.name}`。请检查 `core/` 目录下的文件是否存在。")
    except Exception as e:
        st.error(f"💥 系统捕获到异常")
        st.warning(f"错误详情: {str(e)}")
        with st.expander("查看完整错误堆栈 (Traceback)"):
            st.exception(e)

if __name__ == "__main__":
    main()