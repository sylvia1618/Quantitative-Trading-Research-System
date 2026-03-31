# core/analysis.py
import pandas as pd
import numpy as np

class FactorAnalyzer:
    def __init__(self, df: pd.DataFrame):
        """
        因子相关性分析引擎
        :param df: 包含 date 和多个 FACTOR_ 开头列的长表
        """
        self.df = df.copy()
        # 自动识别所有因子列
        self.factor_cols = [c for c in df.columns if c.startswith('FACTOR_')]

    def calc_correlation_matrix(self, method='spearman'):
        """
        计算截面相关系数的均值矩阵
        支持多因子同时分析
        """
        if len(self.factor_cols) < 2:
            # 如果只有一个因子，相关性矩阵没有意义，返回 1.0 的 DataFrame
            return pd.DataFrame([[1.0]], index=self.factor_cols, columns=self.factor_cols)

        # 1. 核心计算逻辑：按天分组计算
        def _daily_corr(group):
            # 检查当前日期下，哪些因子是有有效波动（不是全常量）的
            valid_cols = [c for c in self.factor_cols if group[c].nunique() > 1]
            if len(valid_cols) < 2:
                return None
            # 计算该日期下的 N x N 相关矩阵
            return group[valid_cols].corr(method=method)

        # 2. 执行分组计算 (适配 Pandas 2.2+)
        # result 此时是一个带有 (date, factor_name) 的 MultiIndex Series 或 DataFrame
        daily_corrs = self.df.groupby('date').apply(_daily_corr, include_groups=False)

        if daily_corrs.empty:
            return pd.DataFrame()

        # 3. 聚合：计算所有交易日的平均值
        # 我们需要对 MultiIndex 的第二层（因子名）进行分组求均值
        # 这样能确保即便某些天某个因子缺失，整体矩阵依然是对齐的
        avg_corr = daily_corrs.groupby(level=1).mean()
        
        # 4. 排序：确保行列顺序一致，方便热力图展示
        avg_corr = avg_corr.reindex(index=self.factor_cols, columns=self.factor_cols)
        
        return avg_corr

    def get_hierarchical_clusters(self, corr_matrix):
        """
        层次聚类：将相关性高的因子排在一起
        """
        from scipy.cluster.hierarchy import linkage, leaves_list
        from scipy.spatial.distance import squareform

        if corr_matrix.empty or corr_matrix.shape[0] < 2:
            return corr_matrix

        # 将相关性转化为距离 (1 - corr)
        # 填充 NaN 为 0 (假设不相关的距离最大)
        dist_matrix = 1 - corr_matrix.fillna(0).values
        # 确保对称
        dist_matrix = (dist_matrix + dist_matrix.T) / 2
        np.fill_diagonal(dist_matrix, 0)
        
        # 层次聚类
        linkage_matrix = linkage(squareform(dist_matrix), method='ward')
        order = leaves_list(linkage_matrix)
        
        # 返回重新排序后的矩阵
        new_order = [corr_matrix.columns[i] for i in order]
        return corr_matrix.loc[new_order, new_order]