import pandas as pd

# 读取Excel文件
excel_file = '中国食物成分表.xlsx'
xl = pd.ExcelFile(excel_file)

print("工作表列表:", xl.sheet_names)

# 将每个工作表转换为CSV，跳过第一行（工作表名称行）
for sheet_name in xl.sheet_names:
    df = pd.read_excel(excel_file, sheet_name=sheet_name, header=1)
    csv_file = f"{sheet_name}.csv"
    df.to_csv(csv_file, index=False, encoding='utf-8-sig')
    print(f"已保存: {csv_file}，共 {len(df)} 行数据")