import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from pathlib import Path
import importlib

# 核心模块导入与强制重载
import core.auditor as auditor_module
importlib.reload(auditor_module)
from core.auditor import FactorAuditor
from app.utils import get_chinese_name

# --- 基础配置 ---
BASE_DIR = Path(r"D:\量化平台\QuantFlow_Lab")
FACTOR_DIR = BASE_DIR / "data" / "factors"
NAME_DATA_PATH = BASE_DIR / "data" / "raw" / "all_stock_info.csv"

# --- 数据加载与缓存 ---

@st.cache_data(show_spinner="📥 正在同步大数据集...")
def load_processed_data(file_name: str):
    path = FACTOR_DIR / f"{file_name}.parquet"
    if not path.exists(): return None
    df = pd.read_parquet(path)
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'])
    return df

@st.cache_data
def get_stock_name_map():
    """加载全市场代码与名称映射"""
    if NAME_DATA_PATH.exists():
        df_names = pd.read_csv(NAME_DATA_PATH)
        return dict(zip(df_names['code'], df_names['display_name']))
    return {}

def show_single_factor():
    st.title("🧬 Factor Auditor Pro")
    st.caption("实验级单因子审计平台 | 样本外禁区验证模式")

    # 加载名称映射表
    name_map = get_stock_name_map()

    # --- 1. 审计配置中心 ---
    with st.container(border=True):
        st.subheader("🛠️ 审计配置中心")
        
        # 第一行：数据源、因子、周期
        col_src, col_factor, col_param = st.columns([1.5, 2, 1.5])
        
        with col_src:
            data_ver = st.radio("数据版本", ["原始精炼 (raw)", "全中性化 (neutral)"], horizontal=True)
            file_key = "refined_raw" if "raw" in data_ver else "refined_neutralized"
            raw_df = load_processed_data(file_key)
            if raw_df is None: 
                st.error("未找到数据文件，请检查路径。"); return

        with col_factor:
            factor_list = sorted([c for c in raw_df.columns if c.startswith('FACTOR_')])
            target_f = st.selectbox("核心审计因子", factor_list, 
                                  format_func=lambda x: f"{get_chinese_name(x)} ({x})")
        
        with col_param:
            period = st.select_slider("预测周期 (d)", options=[1, 5, 10, 20], value=5)
            ret_col = f"ret_{period}d"

        st.divider()

        # 第二行：时间区间与禁区控制
        st.markdown("#### 📅 时间区间与禁区验证")
        t_col1, t_col2, t_col3 = st.columns([2, 2, 2])
        
        with t_col1:
            audit_mode = st.selectbox("审计区间模式", 
                                    ["全量区间", "指定日期范围", "实验区 vs 禁区对比"], 
                                    index=2)
        
        with t_col2:
            split_date = st.date_input("隔离红线 (禁区起点)", value=pd.to_datetime("2025-01-01"))
            split_dt = pd.to_datetime(split_date)

        with t_col3:
            if audit_mode == "指定日期范围":
                start_d = st.date_input("开始日期", value=raw_df['date'].min())
                end_d = st.date_input("结束日期", value=raw_df['date'].max())
            else:
                st.info("💡 对比模式下将自动切分数据")

        st.divider()

        # 第三行：行业池构建与【成分股穿透】
        st.markdown("#### 🏗️ 行业池构建与成分股穿透")
        all_industries = sorted([i for i in raw_df['industry'].unique() if pd.notna(i)])
        
        btn_c1, btn_c2, _ = st.columns([1, 1, 4])
        if btn_c1.button("全选行业", use_container_width=True):
            st.session_state.selected_inds = all_industries
            st.rerun()
        if btn_c2.button("清空选择", use_container_width=True):
            st.session_state.selected_inds = []
            st.rerun()

        # 使用 session_state 初始化的已选行业
        if 'selected_inds' not in st.session_state:
            st.session_state.selected_inds = []

        selected_inds = st.multiselect("包含行业", options=all_industries, key="selected_inds")

        # --- 重点：个股穿透展示区 (独立于审计按钮) ---
        if selected_inds:
            with st.expander(f"🔍 查看已选 {len(selected_inds)} 个行业的成分股明细 (卡片模式)", expanded=False):
                target_df = raw_df[raw_df['industry'].isin(selected_inds)][['code', 'industry']].drop_duplicates('code')
                target_df['name'] = target_df['code'].map(name_map).fillna("未知")
                
                for ind in selected_inds:
                    stocks_in_ind = target_df[target_df['industry'] == ind]
                    if stocks_in_ind.empty: continue
                    
                    st.markdown(f"##### 📂 {ind} ({len(stocks_in_ind)} 只)")
                    
                    # 限制单行业显示，防止渲染过多导致卡顿
                    display_stocks = stocks_in_ind.head(100)
                    if len(stocks_in_ind) > 100:
                        st.caption(f"注：该行业股票较多，仅展示前 100 只")

                    cols_per_row = 5
                    for i in range(0, len(display_stocks), cols_per_row):
                        row_data = display_stocks.iloc[i : i + cols_per_row]
                        cols = st.columns(cols_per_row)
                        for j, (_, stock) in enumerate(row_data.iterrows()):
                            with cols[j]:
                                with st.container(border=True):
                                    st.markdown(f"""
                                    <div style="text-align: center; line-height: 1.2;">
                                        <div style="font-size: 0.8rem; font-weight: bold; color: #1E88E5; overflow: hidden; white-space: nowrap;">{stock['name']}</div>
                                        <div style="font-size: 0.65rem; color: #757575;">{stock['code']}</div>
                                    </div>
                                    """, unsafe_allow_html=True)
        else:
            st.warning("⚠️ 请至少选择一个行业以继续审计。")

        st.divider()

        # 第四行：审计执行控制
        col_inv, col_q, col_run = st.columns([1.5, 1.5, 2])
        with col_inv: is_inverse = st.toggle("🔄 手动翻转因子方向", value=False)
        with col_q: q_groups = st.select_slider("分层组数", options=list(range(2, 11)), value=5)
        with col_run: run_audit = st.button("🚀 开始执行全维度审计", use_container_width=True, type="primary")

    # --- 2. 核心计算逻辑 ---
    if run_audit and selected_inds:
        df_pool = raw_df[raw_df['industry'].isin(selected_inds)].copy()
        if is_inverse: 
            df_pool[target_f] = -df_pool[target_f]

        with st.spinner("正在进行多时空因子审计..."):
            try:
                if audit_mode == "实验区 vs 禁区对比":
                    # 对比报告
                    comparison = FactorAuditor.compare_periods(df_pool, target_f, split_dt, ret_col=ret_col)
                    st.session_state.compare_report = comparison
                    # 全量报告用于绘图
                    auditor = FactorAuditor(df_pool, target_f, ret_col=ret_col)
                elif audit_mode == "指定日期范围":
                    auditor = FactorAuditor(df_pool, target_f, ret_col=ret_col, start_date=start_d, end_date=end_d)
                    st.session_state.compare_report = None
                else:
                    auditor = FactorAuditor(df_pool, target_f, ret_col=ret_col)
                    st.session_state.compare_report = None
                
                st.session_state.audit_report = auditor.full_report()
                st.session_state.last_factor_name = get_chinese_name(target_f) + (" (反转)" if is_inverse else "")
            except Exception as e:
                st.error(f"审计失败: {str(e)}")

    # --- 3. 结果渲染 ---
    if 'audit_report' in st.session_state:
        report = st.session_state.audit_report
        
        st.header(f"📊 因子审计报告: {st.session_state.get('last_factor_name', '')}")
        
        # 1. 如果存在对比报告，优先显示
        if st.session_state.get('compare_report') is not None:
            st.subheader("⚖️ 样本内外性能对比 (In-Sample vs Out-of-Sample)")
            comp_df = st.session_state.compare_report
            # 使用带颜色渐变的表格 (前提是已安装 matplotlib)
            try:
                st.dataframe(comp_df.style.background_gradient(axis=1, cmap='RdYlGn'), use_container_width=True)
            except:
                st.dataframe(comp_df, use_container_width=True)
            
            # 风险强提示
            icir_in = comp_df.loc['ICIR', '实验区 (In-Sample)']
            icir_out = comp_df.loc['ICIR', '禁区 (Out-of-Sample)']
            if icir_out < icir_in * 0.6:
                st.error(f"🚨 严重警告：禁区 (2025+) 的稳定性 (ICIR) 较实验区大幅衰减！因子过拟合风险极高。")

        # 2. KPI 指标卡
        s = report['ic_stats']
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Mean Rank IC", f"{s['IC Mean']:.4f}")
        c2.metric("ICIR (稳定性)", f"{s['ICIR']:.4f}")
        c3.metric("IC 胜率", f"{s['IC > 0']:.1%}")
        c4.metric("样本覆盖率", f"{report['coverage']:.1%}")

        st.write("---")

        t1, t2, t3, t4 = st.tabs(["📈 收益与 IC", "⏳ 衰减与稳定性", "🏢 行业归因", "🔍 分布质量"])

        with t1:
            col_a, col_b = st.columns(2)
            with col_a:
                cum_ret = (1 + report['group_ret'].fillna(0)).cumprod()
                fig_q = px.line(cum_ret, title="分层累计净值 (已自动对齐)")
                if audit_mode == "实验区 vs 禁区对比":
                    fig_q.add_vline(x=split_dt.strftime('%Y-%m-%d'), line_dash="dash", line_color="red", annotation_text="隔离红线")
                st.plotly_chart(fig_q, use_container_width=True)
            with col_b:
                fig_ic = px.line(report['ic_series'].cumsum(), title="累计 Rank IC 曲线")
                if audit_mode == "实验区 vs 禁区对比":
                    fig_ic.add_vline(x=split_dt.strftime('%Y-%m-%d'), line_dash="dash", line_color="red")
                st.plotly_chart(fig_ic, use_container_width=True)

        with t2:
            col_c, col_d = st.columns(2)
            with col_c:
                fig_decay = px.bar(report['decay'], title="因子预测力衰减 (IC Decay)")
                st.plotly_chart(fig_decay, use_container_width=True)
            with col_d:
                fig_roll = px.line(report['rolling_ic'], title="60日滚动 Rank IC")
                st.plotly_chart(fig_roll, use_container_width=True)

        with t3:
            if 'industry_ic' in report:
                ind_ic = report['industry_ic'].sort_values()
                fig_ind = px.bar(ind_ic, orientation='h', title="各行业平均 Rank IC (穿透分析)")
                st.plotly_chart(fig_ind, use_container_width=True)

        with t4:
            st.json(report['distribution'])

if __name__ == "__main__":
    show_single_factor()