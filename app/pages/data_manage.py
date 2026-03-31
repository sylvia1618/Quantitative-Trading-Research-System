import streamlit as st
import pandas as pd
from pathlib import Path
import sys

# 路径挂载
ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

# 导入你的核心内核
from core.pipeline import QuantFlowPipeline # 假设你已经创建了调度类

def show():
    st.header("🔄 数据与因子流水线控制台")
    st.markdown("---")

    # 1. 状态看板
    col1, col2, col3 = st.columns(3)
    pool_path = ROOT_DIR / "data" / "final_standardized_pool.parquet"
    
    if pool_path.exists():
        df_info = pd.read_parquet(pool_path)
        col1.metric("总样本量", f"{len(df_info)/10000:.1f} 万行")
        col2.metric("当前因子数", f"{len(df_info.columns)-2} 个")
        col3.metric("最新日期", str(df_info['date'].max()))
    else:
        st.warning("⚠️ 尚未生成最终因子池，请执行同步。")

    st.divider()

    # 2. 同步操作区
    st.subheader("同步指令")
    
    # 选项：是否强制重新计算所有因子
    force_calc = st.checkbox("强制全量重算因子 (不勾选则仅增量)", value=False)

    if st.button("🚀 启动一键全流程同步", type="primary", use_container_width=True):
        pipeline = QuantFlowPipeline()
        
        with st.status("正在执行同步流水线...", expanded=True) as status:
            # 这里的 callback 可以将 core 层的 print 重定向到 UI
            def log_to_ui(msg):
                st.write(f"`{msg}`")
            
            try:
                # 调用核心逻辑
                success, msg = pipeline.run_smart_update(
                    callback=log_to_ui, 
                    force_full_calc=force_calc
                )
                
                if success:
                    status.update(label="✅ 同步任务圆满完成！", state="complete")
                    st.balloons()
                else:
                    status.update(label="❌ 同步中断", state="error")
                    st.error(msg)
            except Exception as e:
                status.update(label="💥 系统崩溃", state="error")
                st.exception(e)

    # 3. 数据预览
    if pool_path.exists():
        with st.expander("🔍 因子池详细预览"):
            st.dataframe(df_info.tail(100), use_container_width=True)