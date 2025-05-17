import pandas as pd
import json
from datetime import datetime, timedelta

yesterday = datetime.now() #- timedelta(1)
input_csv_filename = "Cleandata/CSV/" + yesterday.strftime("%d-%m-%Y") + "_jobs_cleaned.csv"
output_csv_filename = yesterday.strftime("%d-%m-%Y") + "_jobs_cleaned.json"

def convert_string_to_list(text):
    if pd.isna(text):
        return []
    items = text.split(',')
    items = [item.strip() for item in items if item.strip()]
    return items

# Đọc file CSV
df = pd.read_csv(input_csv_filename)

# Xử lý cột Skills và Keyword: chuyển chuỗi thành list
if 'Skills' in df.columns:
    df['Skills'] = df['Skills'].apply(convert_string_to_list)

if 'Keyword' in df.columns:
    df['Keyword'] = df['Keyword'].apply(convert_string_to_list)

# Chuyển và lưu sang JSON
json_str = df.to_json(orient='records', force_ascii=False, indent=4)
json_str = json_str.replace('\\/', '/')

with open(output_csv_filename, 'w', encoding='utf-8') as f:
    f.write(json_str)
