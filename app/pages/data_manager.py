import streamlit as st
import pandas as pd
import os
from pathlib import Path

# --- 路径配置 (统一写在顶部) ---
# 这里的路径逻辑要确保能从 app/pages/ 向上找到根目录
BASE_DIR = Path(__file__).resolve().parent.parent.parent
RAW_DIR = BASE_DIR / "data" / "raw"
FACTOR_DIR = BASE_DIR / "data" / "factors"
FINAL_POOL_PATH = BASE_DIR / "data" / "final_standardized_pool.parquet"

# 确保必要的目录存在
RAW_DIR.mkdir(parents=True, exist_ok=True)
FACTOR_DIR.mkdir(parents=True, exist_ok=True)

def show_data_manager():
    st.header("🔧 数据与因子流水线管理")

    # --- 1. 展示最终因子池状态 (仅读取文件，不触发引擎) ---
    st.subheader("📊 核心因子池状态")
    if FINAL_POOL_PATH.exists():
        try:
            df_status = pd.read_parquet(FINAL_POOL_PATH)
            # 确保 date 列是时间格式
            df_status['date'] = pd.to_datetime(df_status['date'])
            last_date = df_status['date'].max().date()
            sample_size = len(df_status)
            # 排除非因子列
            exclude_cols = ['date', 'code', 'amount', 'log_size', 'next_ret']
            factor_nums = len([c for c in df_status.columns if c not in exclude_cols])
            
            c1, c2, c3 = st.columns(3)
            c1.metric("最后同步日期", str(last_date))
            c2.metric("总样本规模", f"{sample_size/10000:.1f} 万行")
            c3.metric("有效因子总数", f"{factor_nums} 个")
        except Exception as e:
            st.error(f"解析因子池统计信息失败: {e}")
    else:
        st.info("💡 尚未生成最终标准化因子池，请执行下方的一键同步流程。")

    st.markdown("---")

    # --- 2. 自动化同步核心逻辑 ---
    st.subheader("🔄 智能一键同步流水线")
    st.write("流程：**增量下载行情** ➡️ **自动计算因子** ➡️ **截面市值中性化+标准化**")
    
    # 重点：点击按钮前，不进行任何 core 模块的 import
    if st.button("🚀 启动全流程一键更新", type="primary", use_container_width=True):
        with st.status("流水线作业中，请勿关闭页面...", expanded=True) as status:
            try:
                # 🚀 【延迟导入】在此处发生，彻底阻断启动时的自动运行
                st.write("📦 正在加载核心引擎组件...")
                from core.data_engine import main as run_raw_sync
                from core.factory import run_factory
                from core.standardized_factors import aggregate_and_standardize
                
                # 步骤 1: 原始数据增量同步
                st.write("📡 **阶段 1/3: 正在增量拉取 BaoStock 最新行情...**")
                run_raw_sync() 
                
                # 步骤 2: 因子工厂生产
                st.write("🧪 **阶段 2/3: 因子工厂计算中...**")
                # 传入字符串路径以确保兼容性
                run_factory(str(FACTOR_DIR))
                
                # 步骤 3: 标准化与中性化大表合并
                st.write("⚖️ **阶段 3/3: 执行市值中性化与全量标准化合并...**")
                aggregate_and_standardize(str(FACTOR_DIR), str(FINAL_POOL_PATH))
                
                status.update(label="✅ 全流程同步圆满完成！", state="complete", expanded=False)
                st.toast("因子池数据已刷新", icon="🎉")
                st.rerun() 
                
            except Exception as e:
                status.update(label="❌ 同步中止", state="error")
                st.error(f"错误详情: {e}")
                st.exception(e)

    st.markdown("---")

    # --- 3. 原始文件详情 ---
    with st.expander("📂 查看 Raw 原始数据详情"):
        if RAW_DIR.exists():
            # 扫描目录下所有 parquet
            raw_files = []
            for root, dirs, files in os.walk(RAW_DIR):
                for f in files:
                    if f.endswith('.parquet'):
                        raw_files.append(Path(root) / f)
            
            if raw_files:
                st.write(f"共检测到 {len(raw_files)} 个原始行情文件。")
                if st.checkbox("显示文件列表预览"):
                    file_info = [{"文件名": f.name, "大小(KB)": round(f.stat().st_size/1024, 2)} for f in raw_files[:10]]
                    st.table(pd.DataFrame(file_info))
            else:
                st.write("Raw 目录暂无数据文件")

    # --- 4. 手动上传 ---
    st.subheader("📤 外部数据补丁")
    uploaded = st.file_uploader("上传 CSV/Parquet 补丁文件", type=["csv", "parquet"])
    if uploaded is not None:
        dest = RAW_DIR / uploaded.name
        with open(dest, "wb") as f:
            f.write(uploaded.getbuffer())
        st.success(f"文件 `{uploaded.name}` 已保存至 raw 目录")