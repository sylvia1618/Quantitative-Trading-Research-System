import streamlit as st
import pandas as pd


def show_risk_analysis():
    st.header("⚠️ 风险分析")

    st.write("本模块依赖最近一次回测结果，或允许你上传已有的回测输出。")

    if 'last_backtest' in st.session_state:
        result = st.session_state['last_backtest']
    else:
        uploaded = st.file_uploader("上传回测结果 (pickle/json) ", type=["pkl", "json"])
        result = None
        if uploaded:
            try:
                if uploaded.name.endswith('.pkl'):
                    import pickle
                    result = pickle.load(uploaded)
                else:
                    result = pd.read_json(uploaded)
                st.success("已加载回测结果")
            except Exception as e:
                st.error(f"读取回测结果失败: {e}")
    if result is not None:
        # 计算简单风险指标
        pv = result.get('portfolio_values')
        if isinstance(pv, pd.Series) or isinstance(pv, pd.DataFrame):
            st.line_chart(pv)
        st.write("主要指标")
        metrics = {k: v for k, v in result.items() if k not in ['portfolio_values']}
        st.json(metrics)

        # 计算滚动指标
        if isinstance(pv, pd.Series):
            returns = pv.pct_change().dropna()
            roll_sharpe = returns.rolling(21).mean() / returns.rolling(21).std() * (252**0.5)
            st.subheader("滚动夏普")
            st.line_chart(roll_sharpe)
    else:
        st.info("暂无回测结果，请先执行组合回测或上传文件。")
