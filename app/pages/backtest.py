import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path
import numpy as np
from core.backtester import VectorizedBacktester

def show_backtest():
    st.header("📈 组合回测与禁区验证")

    # 1. 路径定义 (严格匹配您的文件夹结构)
    BASE_DIR = Path(r"D:\量化平台\QuantFlow_Lab")
    FACTOR_DIR = BASE_DIR / "data" / "factors"
    PATH_300 = BASE_DIR / "data" / "sh" / "000300.parquet"
    PATH_905 = BASE_DIR / "data" / "sz" / "000905.parquet"
    PATH_1000 = BASE_DIR / "data" / "sz" / "000852.parquet" # ✨ 新增中证1000路径
    
    if not FACTOR_DIR.exists():
        st.error(f"❌ 路径不存在: {FACTOR_DIR}")
        return

    # 获取所有模型预测信号文件
    score_files = sorted([f.name for f in FACTOR_DIR.glob("ML_*.parquet")], reverse=True)
    
    if not score_files:
        st.warning("⚠️ 未发现模型预测文件。请先在合成页面完成熔炼。")
        return

    # 2. 侧边栏配置
    with st.sidebar:
        st.subheader("📋 信号文件分析")
        selected_file = st.selectbox("选择预测信号文件", score_files, 
                                     help="RESEARCH 为实验数据，FINAL 为包含 2025 后的全量数据")
        
        df_score = pd.read_parquet(FACTOR_DIR / selected_file)
        
        if 'date' in df_score.columns:
            df_score['date'] = pd.to_datetime(df_score['date'])
            min_d, max_d = df_score['date'].min(), df_score['date'].max()
            
            if "FINAL" in selected_file:
                st.success(f"🔥 当前为全量文件\n范围: {min_d.date()} -> {max_d.date()}")
            else:
                st.info(f"🧪 当前为实验文件\n范围: {min_d.date()} -> {max_d.date()}")
        
        has_ret = 'ret_1d' in df_score.columns
        if not has_ret:
            st.error("❌ 缺少 'ret_1d' 列，无法计算收益！")

    # 3. 回测参数设置
    with st.expander("⚙️ 回测策略配置", expanded=True):
        col1, col2, col3 = st.columns(3)
        buy_n = col1.number_input("每日持仓个股数 (Top N)", 5, 500, 50)
        
        # 禁区红线日期
        split_date = col2.date_input("设置红线日期 (禁区起点)", value=pd.to_datetime("2025-01-01"))
        split_dt = pd.to_datetime(split_date)
        
        # ✨ 增加中证1000选项
        benchmark_choice = col3.selectbox("对比基准指数", ["无基准", "沪深300", "中证500", "中证1000"])

    # 4. 执行回测
    if st.button("🏃 启动回测引擎", type="primary", use_container_width=True):
        with st.spinner("正在对齐次日基准并计算超额收益..."):
            try:
                # ✨ 初始化增加 path_1000
                tester = VectorizedBacktester(
                    df_score, 
                    path_300=PATH_300, 
                    path_905=PATH_905, 
                    path_1000=PATH_1000, 
                    buy_count=buy_n
                )
                results = tester.run_backtest()

                # 数据切片：实验区 vs 禁区
                research_res = results[results.index < split_dt]
                holdout_res = results[results.index >= split_dt]

                # 5. 指标看板
                st.subheader("📊 绩效多维评估")
                c1, c2 = st.columns(2)
                
                def display_metrics(data, title):
                    st.markdown(f"#### {title}")
                    if not data.empty:
                        m = tester.compute_metrics(data)
                        st.dataframe(pd.Series(m, name="数值"), use_container_width=True)
                    else:
                        st.warning("该区间内无有效数据")

                with c1: display_metrics(research_res, f"🧪 实验区 (< {split_date})")
                with c2: display_metrics(holdout_res, f"🔒 禁区 (>= {split_date})")

                # 6. 曲线图绘制 (适配新引擎列名)
                st.divider()
                plot_cols = ['cum_return']
                names = {"cum_return": "策略净值", "cum_hs300": "沪深300", "cum_zz500": "中证500", "cum_zz1000": "中证1000"}
                
                # 动态匹配基准曲线
                bench_col_map = {"沪深300": "cum_hs300", "中证500": "cum_zz500", "中证1000": "cum_zz1000"}
                if benchmark_choice in bench_col_map:
                    target_col = bench_col_map[benchmark_choice]
                    if target_col in results.columns:
                        plot_cols.append(target_col)

                fig = px.line(results, y=plot_cols, title=f"策略 vs {benchmark_choice} 净值对比", labels=names)
                fig.add_vline(x=split_dt, line_width=2, line_dash="dash", line_color="red")
                st.plotly_chart(fig, use_container_width=True)

                # 7. Alpha (超额收益) 专项展示
                if benchmark_choice != "无基准":
                    st.subheader(f"🛡️ 纯超额收益 (Alpha) 曲线")
                    # ✨ 这里的 key 必须严格匹配新版 backtester.py 里的定义
                    alpha_map = {"沪深300": "cum_alpha_300", "中证500": "cum_alpha_500", "中证1000": "cum_alpha_1000"}
                    alpha_col = alpha_map.get(benchmark_choice)
                    
                    if alpha_col and alpha_col in results.columns:
                        fig_alpha = px.line(results, y=alpha_col, title=f"对标 {benchmark_choice} 的累计超额 (复利口径)")
                        fig_alpha.add_hline(y=1.0, line_dash="dot", line_color="grey")
                        fig_alpha.add_vline(x=split_dt, line_width=2, line_dash="dash", line_color="red")
                        st.plotly_chart(fig_alpha, use_container_width=True)
                    else:
                        st.error(f"⚠️ 结果中未生成 {alpha_col}，请检查基准 Parquet 是否包含有效数据。")

                # 8. 数据导出
                st.divider()
                st.subheader("📥 结果下载")
                dl_col1, dl_col2 = st.columns(2)
                
                csv_data = results.reset_index().to_csv(index=False).encode('utf-8-sig')
                
                with dl_col1:
                    st.download_button(label="💾 下载详细回测流水 (CSV)", data=csv_data,
                                       file_name=f"Backtest_{selected_file.split('.')[0]}.csv",
                                       mime="text/csv", use_container_width=True)
                
                with dl_col2:
                    full_metrics = tester.compute_metrics(results)
                    metrics_df = pd.DataFrame(full_metrics, index=["数值"]).T
                    st.download_button(label="📄 下载绩效指标简报", data=metrics_df.to_csv().encode('utf-8-sig'),
                                       file_name=f"Metrics_{selected_file.split('.')[0]}.csv",
                                       mime="text/csv", use_container_width=True)
                
                st.balloons() 

            except Exception as e:
                st.error(f"❌ 回测运行出错: {str(e)}")
                st.exception(e)