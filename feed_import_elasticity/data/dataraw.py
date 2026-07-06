import dask.dataframe as dd
from dask.diagnostics import ProgressBar  # 可选：显示进度条
import os  # 用于检查文件是否存在

# 定义文件夹路径
input_folder = "/Users/hanxinru/Library/CloudStorage/OneDrive-个人/科研/数据/进出口数据/usd"
output_folder = "/Users/hanxinru/Library/CloudStorage/OneDrive-个人/科研/数据/进出口数据"

# 指定dtypes以优化内存和避免类型转换错误（针对报错列和潜在混合类型列，包括2022年的数量列问题）
dtypes = {
    '商品编码': 'object',  # 用于提取，确保字符串
    '金额': 'object',      # 修复之前年份ValueError：包含带逗号字符串如'978,825'
    '第一数量': 'object',   # 修复2022年ValueError：包含字符串如'-'
    '第二数量': 'object',   # 修复2022年ValueError：包含字符串如'-'
    '电子邮件': 'object',   # 修复之前ValueError：包含字符串如邮箱
    '邮政编码': 'object',   # 修复之前ValueError和DtypeWarning：混合类型如'37松信'
    '地址': 'object',      # 潜在混合类型
    '传真': 'object',      # 潜在混合类型
    '电话': 'object',      # 潜在混合类型
    '公司': 'object',      # 潜在混合类型
    '联系人': 'object'     # 潜在混合类型
}

# 循环处理2000-2014年（修改range以包括2022或其他年份，例如 range(2000, 2023)）
for year in range(2000, 2025):  # 包括2014；修改为 range(2000, 2023) 以包括2022
    input_file = f"{input_folder}/{year}.csv"
    
    # 检查文件是否存在
    if not os.path.exists(input_file):
        print(f"警告: 文件 {input_file} 不存在。跳过 {year} 年。")
        continue
    
    feed_output_file = f"{output_folder}/{year}-feed.csv"
    food_output_file = f"{output_folder}/{year}-food.csv"
    
    print(f"处理 {year} 年数据: {input_file}")
    
    try:
        # 使用Dask读取大CSV（并行、多核，支持大文件）
        df_dask = dd.read_csv(input_file, dtype=dtypes, blocksize="64MB", assume_missing=True)
        
        # 调试：打印列名（仅为第一个年份，或移除以加速）
        if year == 2000:
            print("列名列表 (示例):", df_dask.columns.tolist())
        
        # 如果"商品编码"存在，继续处理
        if '商品编码' in df_dask.columns:
            # 调试：打印原始的前5行以检查格式（仅为第一个年份，或移除以加速）
            if year == 2000:
                print("商品编码前5行 (示例):", df_dask['商品编码'].head(5).tolist())
            
            # 提取feed样本：前4位 in ['1002','1003','1004','1005','1007'] 或 前6位 in ['230330','071410']
            feed_condition = (
                df_dask['商品编码'].str[:4].isin(['1002', '1003', '1004', '1005', '1007']) |
                df_dask['商品编码'].str[:6].isin(['230330', '071410'])
            )
            df_feed = df_dask[feed_condition]
            
            # 调试：检查是否有任何feed匹配
            with ProgressBar():
                has_feed = (df_feed.shape[0].compute() > 0)
                print(f"{year} 年是否有feed匹配样本:", has_feed)
                # 保存（并行计算并写入CSV）
                df_feed.to_csv(feed_output_file, single_file=True, index=False)
                print(f"{year} 年Feed samples saved to: {feed_output_file} (Rows: computed during save)")
            
            # 提取food样本：前2位 from '01' to '24' (inclusive)
            food_prefixes = [f"{i:02d}" for i in range(1, 25)]  # ['01', '02', ..., '24']
            food_condition = df_dask['商品编码'].str[:2].isin(food_prefixes)
            df_food = df_dask[food_condition]
            
            # 调试：检查是否有任何food匹配
            with ProgressBar():
                has_food = (df_food.shape[0].compute() > 0)
                print(f"{year} 年是否有food匹配样本:", has_food)
                # 保存（并行计算并写入CSV）
                df_food.to_csv(food_output_file, single_file=True, index=False)
                print(f"{year} 年Food samples saved to: {food_output_file} (Rows: computed during save)")
        else:
            print(f"错误: {year} 年'商品编码'列不存在。请检查数据。")
    except Exception as e:
        print(f"错误处理 {year} 年数据: {e}")
    
print("所有年份处理完成！")