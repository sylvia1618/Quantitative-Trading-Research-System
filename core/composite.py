import pandas as pd
import numpy as np
import lightgbm as lgb
import xgboost as xgb
from sklearn.ensemble import RandomForestRegressor
from tqdm import tqdm

class AlphaComposer:
    def __init__(self, df, features, target='ret_5d'):
        # 💡 增加 ret_1d 的保留，因为回测页面强依赖它
        extra_cols = ['ret_1d'] if 'ret_1d' in df.columns else []
        cols = ['date', 'code', 'industry'] + features + [target] + extra_cols
        
        self.df = df[cols].dropna(subset=features + [target]).sort_values(['date', 'code']).copy()
        self.features = features
        self.target = target
        self.hold_period = int(''.join(filter(str.isdigit, target)))

    def train_rolling(self, model_type='LGBM', selected_industries=None, params=None, 
                      train_window=252, step=20):
        
        data = self.df.copy()
        if selected_industries:
            data = data[data['industry'].isin(selected_industries)]
        
        if data.empty:
            raise ValueError("筛选后的数据为空，请检查行业设置！")

        all_dates = sorted(data['date'].unique())
        results = []
        importance_list = []
        
        # --- 🛠️ 修正 1：更灵活的测试集起点 ---
        # 确保即便数据量较小，也能从可训练的最小长度开始
        min_required = min(train_window + self.hold_period, len(all_dates) // 2)
        test_dates = all_dates[min_required:]

        if not test_dates:
            raise ValueError(f"数据量不足以进行滚动训练。当前有效日期数: {len(all_dates)}")

        for i in tqdm(range(0, len(test_dates), step), desc=f"Rolling {model_type}"):
            current_test_window = test_dates[i : i + step]
            first_test_date = current_test_window[0]
            current_idx = all_dates.index(first_test_date)
            
            # 1. 划分训练集 (Gap 屏蔽)
            # 确保训练结束日期与测试开始日期之间有 self.hold_period 的间隔，防止未来函数
            train_end_idx = current_idx - self.hold_period
            train_start_idx = max(0, train_end_idx - train_window)
            
            train_dates_pool = all_dates[train_start_idx : train_end_idx]
            train_df = data[data['date'].isin(train_dates_pool)]
            
            # 2. 划分测试集
            test_df = data[data['date'].isin(current_test_window)].copy()
            
            if train_df.empty or test_df.empty:
                continue

            # 3. 训练模型
            model = self._get_model(model_type, params)
            model.fit(train_df[self.features], train_df[self.target])
            
            # 4. 记录特征重要性
            imp = self._extract_importance(model, model_type)
            imp['date'] = first_test_date
            importance_list.append(imp)
            
            # 5. 预测
            test_df.loc[:, 'FINAL_SCORE_RAW'] = model.predict(test_df[self.features])
            
            # 💡 修正 2：动态保留所有 ret_* 列，方便回测
            ret_cols = [c for c in test_df.columns if c.startswith('ret_')]
            save_cols = ['date', 'code', 'industry', 'FINAL_SCORE_RAW'] + ret_cols
            results.append(test_df[save_cols])

        if not results:
            return pd.DataFrame(), pd.DataFrame()

        # 合并结果
        final_oos_df = pd.concat(results).sort_values(['date', 'code'])
        
        # 6. 截面标准化 (0~1 Rank 化)
        final_oos_df['FINAL_SCORE'] = final_oos_df.groupby('date')['FINAL_SCORE_RAW'].rank(pct=True)
        
        importance_df = pd.concat(importance_list)
        return final_oos_df, importance_df

    def _extract_importance(self, model, model_type):
        """
        优化：针对 LGBM 使用 Gain 增益
        """
        if model_type == 'LGBM':
            # 获取特征增益 (Importance Type = Gain)
            imp = model.booster_.feature_importance(importance_type='gain')
        else:
            imp = model.feature_importances_
            
        # 归一化处理，方便展示
        imp = imp / (imp.sum() + 1e-9)
        return pd.DataFrame({'factor': self.features, 'importance': imp})

    def _get_model(self, model_type, params):
        if model_type == 'LGBM':
            # 💡 默认参数微调：增加 importance_type
            default_p = {
                'n_estimators': 100, 
                'num_leaves': 31, 
                'learning_rate': 0.05, 
                'n_jobs': -1, 
                'verbose': -1,
                'importance_type': 'gain' 
            }
            return lgb.LGBMRegressor(**{**default_p, **(params or {})})
        # ... 其他模型保持原样
        elif model_type == 'XGBoost':
            return xgb.XGBRegressor(**(params or {'n_estimators': 100, 'learning_rate': 0.05}))
        elif model_type == 'RandomForest':
            return RandomForestRegressor(**(params or {'n_estimators': 100, 'max_depth': 8}))
        raise ValueError(f"Unknown model: {model_type}")