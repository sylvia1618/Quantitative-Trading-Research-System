import pandas as pd
import streamlit as st
import plotly.express as px
from pathlib import Path
import importlib
import os
import sys

# =========================================================
# 1. 环境加载与核心逻辑导入
# =========================================================

import app.utils as utils
importlib.reload(utils)
from app.utils import get_chinese_name

import core.composite as composite_module
importlib.reload(composite_module)
from core.composite import AlphaComposer

BASE_DIR = Path(os.getcwd())
FACTOR_DIR = BASE_DIR / "data" / "factors"

@st.cache_data
def load_processed_data(ver):
    file_path = FACTOR_DIR / f"{ver}.parquet"
    if not file_path.exists():
        st.error(f"❌ 找不到数据文件: {file_path}")
        return None
    df = pd.read_parquet(file_path)
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'])
    return df

def show_multi_factor():
    st.sidebar.title("🧬 Multi-Factor Engine")
    
    # --- 侧边栏：配置区 ---
    with st.sidebar:
        st.subheader("🏗️ 训练环境配置")
        data_ver = st.radio("数据集版本", ["refined_raw", "refined_neutralized"], index=1)
        raw_df = load_processed_data(data_ver)
        if raw_df is None: return

        st.write("---")
        run_mode = st.radio("🎯 运行模式", ["实验室模式 (只跑2024以前)", "全量/禁区模式 (跑全段数据)"])

        st.subheader("📅 时间区间划分")
        all_dates = sorted(raw_df['date'].unique())
        min_date, max_date = all_dates[0], all_dates[-1]
        
        research_end_val = pd.to_datetime("2024-12-31")
        if research_end_val > max_date: research_end_val = max_date

        research_end_date = st.date_input("实验区截止日期", value=research_end_val)
        research_end_date = pd.to_datetime(research_end_date)

        all_industries = sorted([i for i in raw_df['industry'].unique() if pd.notna(i)])
        if 'mf_selected_inds' not in st.session_state:
            st.session_state.mf_selected_inds = all_industries

        selected_inds = st.multiselect("包含行业", options=all_industries, key="mf_selected_inds")
        
        st.write("---")
        st.subheader("🤖 模型配置")
        model_type = st.selectbox("合成算法", ["LGBM", "XGBoost", "RandomForest"])
        factor_list = sorted([c for c in raw_df.columns if c.startswith('FACTOR_')])

        selected_factors = st.multiselect(
            "参与合成的因子", options=factor_list,
            default=factor_list[:10] if len(factor_list)>10 else factor_list,
            format_func=lambda x: f"{get_chinese_name(x)} ({x})"
        )
        
        target_p = st.selectbox("预测目标周期", [1, 5, 10, 20], index=1)
        run_train = st.button("🚀 开始熔炼", type="primary", use_container_width=True)

    # --- 逻辑预设 ---
    if run_mode == "实验室模式 (只跑2024以前)":
        train_df_input = raw_df[raw_df['date'] <= research_end_date].copy()
        save_prefix = "ML_RESEARCH"
    else:
        train_df_input = raw_df.copy()
        save_prefix = "ML_FINAL"

    st.header(f"🧬 多因子合成实验室 ({model_type})")
    
    # 状态提示
    st.info(f"当前模式：{run_mode} | 样本量：{len(train_df_input):,}")

    # --- 执行训练 ---
    if run_train:
        if not selected_inds:
            st.error("❌ 请至少选择一个行业！"); return

        target_col = f'ret_{target_p}d'
        composer = AlphaComposer(train_df_input, selected_factors, target=target_col)
        
        with st.spinner(f"正在以 {run_mode} 模式滚动训练..."):
            try:
                final_df, importance_df = composer.train_rolling(
                    model_type=model_type, 
                    selected_industries=selected_inds,
                    step=20 
                )
                # ✨ 核心修正：存入 Session State，防止点击保存按钮后丢失数据
                st.session_state['last_train_results'] = final_df
                st.session_state['last_importance'] = importance_df
                st.session_state['last_save_filename'] = f"{save_prefix}_{model_type}_{target_col}.parquet"
                st.balloons()
            except Exception as e:
                st.error("💥 引擎崩溃"); st.exception(e)

    # --- 结果展示与保存逻辑 ---
    if 'last_train_results' in st.session_state:
        final_df = st.session_state['last_train_results']
        importance_df = st.session_state['last_importance']
        save_filename = st.session_state['last_save_filename']

        # 结果简报
        st.success(f"✅ 训练完成！结果集包含日期：{final_df['date'].min().date()} 至 {final_df['date'].max().date()}")
        
        # 1. 指标计算 (IC)
        target_col = [c for c in final_df.columns if c.startswith('ret_')][0]
        oos_ic = final_df.groupby('date').apply(lambda x: x['FINAL_SCORE'].corr(x[target_col])).mean()
        st.metric("平均样本外 IC", f"{oos_ic:.4f}")

        # 2. 保存区域
        st.divider()
        c1, c2 = st.columns([3, 1])
        c1.info(f"准备存入：`{save_filename}` ({len(final_df)} 行)")
        
        if c2.button("💾 确认存入本地"):
            save_path = FACTOR_DIR / save_filename
            # 自动补全 ret_1d 逻辑
            cols_to_save = ['date', 'code', 'industry', 'FINAL_SCORE']
            for c in ['ret_1d', 'ret_5d', 'ret_10d', 'ret_20d']:
                if c in final_df.columns: cols_to_save.append(c)
            
            final_df[final_df.columns.intersection(cols_to_save)].to_parquet(save_path)
            st.success(f"已持久化存入 data/factors 目录！")

if __name__ == "__main__":
    show_multi_factor()