import pandas as pd
from pathlib import Path

# ==============================
# 项目路径
# ==============================

ROOT = Path(__file__).resolve().parent.parent

RAW = ROOT / "data/raw"
DERIVED = ROOT / "data/derived"

DERIVED.mkdir(parents=True, exist_ok=True)

close_path = RAW / "close.parquet"
volume_path = RAW / "volume.parquet"

# ==============================
# 检查数据
# ==============================

if not close_path.exists():
    print(f"❌ 未找到 {close_path}")
    exit()

if not volume_path.exists():
    print(f"❌ 未找到 {volume_path}")
    exit()

print("📥 读取 close / volume 数据...")

close = pd.read_parquet(close_path)
volume = pd.read_parquet(volume_path)

# ==============================
# 计算成交额
# ==============================

print("⚙️ 计算 amount = close × volume ...")

amount = close * volume

# ==============================
# 计算20日平均成交额
# ==============================

print("⚙️ 计算 20 日成交额均值 amount20 ...")

amount20 = amount.rolling(20).mean()

# ==============================
# 保存
# ==============================

save_path = DERIVED / "amount20.parquet"

amount20.to_parquet(save_path)

print("✅ amount20.parquet 已生成")
print(f"📂 保存位置: {save_path}")
print(f"📊 数据形状: {amount20.shape}")