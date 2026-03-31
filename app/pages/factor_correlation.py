import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path
import importlib
import os

# 1. 核心模块导入与路径配置 (硬核粉色版)
import core.analysis as analysis_module
importlib.reload(analysis_module)
from core.analysis import FactorAnalyzer
from app.utils import get_chinese_name

# --- 路径对齐 ---
BASE_DIR = Path(r"D:\量化平台\QuantFlow_Lab")
# 你的因子数据实际所在地
DATA_DIR = BASE_DIR / "data" / "factors" 

@st.cache_data(show_spinner="📥 正在读取因子池数据...")
def load_factor_data(file_name: str):
    """专门从 data/factors 目录下读取 Parquet"""
    file_path = DATA_DIR / f"{file_name}.parquet"
    if not file_path.exists():
        st.error(f"❌ 找不到文件: {file_path}")
        return None
    return pd.read_parquet(file_path)

def show_correlation_page():
    # 注入局部 CSS 确保按钮也是粉色的
    st.markdown("""
        <style>
        div.stButton > button:first-child {
            background-color: #f06292 !important;
            color: white !important;
            border-radius: 20px;
        }
        </style>
    """, unsafe_allow_html=True)

    st.header("🔗 因子相关性分析 (Correlation Matrix)")
    st.caption(f"当前数据源: {DATA_DIR}")

    # --- 2. 侧边栏配置 ---
    with st.sidebar:
        st.write("---")
        st.subheader("🛠️ 矩阵配置")
        
        # 自动发现目录下的所有 parquet 文件
        available_files = [f.stem for f in DATA_DIR.glob("*.parquet")]
        if not available_files:
            st.error("📂 文件夹内没有因子文件！")
            return

        target_file = st.selectbox("选择审计数据集", available_files, index=0)
        method = st.radio("相关性算法", ["spearman", "pearson"], help="Spearman 对异常值更稳健")
        
        # 加载数据以获取因子列表
        raw_df = load_factor_data(target_file)
        if raw_df is None: return
        
        # 筛选以 FACTOR_ 开头的列
        all_factors = [c for c in raw_df.columns if c.startswith('FACTOR_')]
        
        selected_factors = st.multiselect(
            "参与计算的因子", 
            options=all_factors,
            default=all_factors[:10] if len(all_factors) > 10 else all_factors,
            format_func=lambda x: f"{get_chinese_name(x)} ({x})"
        )
        
        run_btn = st.button("🚀 计算相关性矩阵", use_container_width=True)

    # --- 3. 核心计算与展示 ---
    # app/pages/factor_correlation.py 里的部分逻辑
    if run_btn and selected_factors:
        analyzer = FactorAnalyzer(raw_df[['date'] + selected_factors])
        corr_matrix = analyzer.calc_correlation_matrix(method=method)
        
        # 如果用户勾选了“开启聚类优化”
        if st.checkbox("开启层次聚类 (让相关因子靠拢)", value=True):
            corr_matrix = analyzer.get_hierarchical_clusters(corr_matrix)
        
        with st.spinner("💓 正在执行截面相关性均值运算..."):
            try:
                corr_matrix = analyzer.calc_correlation_matrix(method=method)
                
                # 转换显示名称为中文
                chinese_names = [get_chinese_name(c) for c in corr_matrix.columns]
                corr_matrix.columns = chinese_names
                corr_matrix.index = chinese_names

                # 绘制热力图
                fig = px.imshow(
                    corr_matrix,
                    text_auto=".2f",
                    color_continuous_scale='RdPu', # 粉紫渐变
                    aspect="auto",
                    labels=dict(color="相关系数")
                )
                
                fig.update_layout(
                    margin=dict(l=20, r=20, t=50, b=20),
                    font=dict(color="#ad1457")
                )
                
                st.plotly_chart(fig, width='stretch')
                
                # --- 4. 冗余预警 ---
                st.write("---")
                st.subheader("📝 冗余度体检报告")
                
                # 找出相关性绝对值 > 0.7 的对
                redundant = []
                for i in range(len(corr_matrix)):
                    for j in range(i + 1, len(corr_matrix)):
                        val = corr_matrix.iloc[i, j]
                        if abs(val) > 0.7:
                            redundant.append((corr_matrix.columns[i], corr_matrix.columns[j], val))
                
                if redundant:
                    for f1, f2, v in redundant:
                        st.warning(f"⚠️ **{f1}** 与 **{f2}** 高度相关 (corr: {v:.2f})")
                    st.info("💡 建议：在后续的多因子合成中，尝试对这些因子进行正交化处理。")
                else:
                    st.success("✅ 因子独立性良好，未发现显著冗余。")

            except Exception as e:
                st.error(f"计算出错: {e}")
    
    elif not run_btn:
        st.info("👈 请在左侧勾选因子并点击“计算”按钮开始分析。")

if __name__ == "__main__":
    show_correlation_page()