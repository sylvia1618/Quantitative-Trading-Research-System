# app/utils.py

FACTOR_NAME_MAP = {
    # 动量类 (Momentum)
    'FACTOR_MOM_3': '动量_3日收益',
    'FACTOR_MOM_5': '动量_5日收益',
    'FACTOR_MOM_20': '动量_1月收益',
    'FACTOR_MOM_60': '动量_1季收益',
    'FACTOR_MOM_120': '动量_半年收益',
    'FACTOR_VW_MOM': '成交量加权动量',
    'FACTOR_RISK_ADJ_MOM': '风险调整动量(夏普)',
    
    # 反转类 (Reversal)
    'FACTOR_SHORT_REVERSAL': '短期反转(昨日)',
    'FACTOR_INTRADAY_REVERSAL': '日内反转(乖离率)',
    'FACTOR_OVERREACTION': '过度反应指标',
    
    # 波动率类 (Volatility)
    'FACTOR_VOL_20': '20日收益波动率',
    'FACTOR_PARKINSON_VOL': 'Parkinson高低价波动',
    'FACTOR_UPSIDE_VOL': '上行波动率',
    'FACTOR_DOWNSIDE_VOL': '下行波动率',
    
    # 流动性类 (Liquidity)
    'FACTOR_AMIHUD_ILLIQ': 'Amihud非流动性',
    'FACTOR_AMT_TURNOVER_PROXY': '成交额强度',
    'FACTOR_PV_CORR': '量价相关性',
    
    # 估值与基本面 (Valuation/Fundamental)
    'FACTOR_EP': '盈利收益率(1/PE)',
    'FACTOR_BP': '账面市值比(1/PB)',
    'FACTOR_VALUE_COMPOSITE': '价值因子合成',
    'FACTOR_AMOUNT_STABILITY': '成交额稳定性',
    
    # 标准化版本 (可选)
    'FACTOR_MOM_20_Z': '标准化_1月动量',
    'FACTOR_VOL_Z': '标准化_波动率',
    'FACTOR_VALUE_Z': '标准化_价值'
}

def get_chinese_name(factor_id):
    """根据因子ID获取中文名，找不到则返回原名"""
    return FACTOR_NAME_MAP.get(factor_id, factor_id)
