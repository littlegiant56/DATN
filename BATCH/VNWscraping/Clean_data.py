import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import re

yesterday = datetime.now() #- timedelta(1)
input_csv_filename = "Rawdata/Jobs/VNW_" + yesterday.strftime("%d-%m-%Y") + "_jobs.csv"
output_csv_filename = "VNW_" + yesterday.strftime("%d-%m-%Y") + "_jobs_cleaned.csv"
# Đọc dữ liệu gốc
df = pd.read_csv(input_csv_filename)

# Chuyển cột 'Date Posted' về datetime
if 'Date Posted' in df.columns:
    df['Date Posted'] = pd.to_datetime(df['Date Posted'], format='%d/%m/%Y', errors='coerce')

# Chuẩn hóa cột 'Work Date'
replacements = {
    'T2': 'Thứ 2', 'T3': 'Thứ 3', 'T4': 'Thứ 4', 'T5': 'Thứ 5',
    'T6': 'Thứ 6', 'T7': 'Thứ 7', 'CN': 'Chủ Nhật',
    ',': ' và',
    '-': ' đến'
}
if 'Work Date' in df.columns:
    df['Work Date'] = df['Work Date'].replace(replacements, regex=True)

# Chuyển cột 'Experience'
if 'Experience' in df.columns:
    df['Experience'] = df['Experience'].replace('Không yêu cầu', '0')
    df['Experience'] = pd.to_numeric(df['Experience'], errors='coerce')

# Tách cột 'Industry' thành 2 cấp
if 'Industry' in df.columns:
    df[['Industry', 'Industry1']] = df['Industry'].str.split(' > ', expand=True)

# Tách khoảng tuổi từ cột 'Age'
def extract_age_range(age_str):
    if pd.isna(age_str) or age_str == "Không hiển thị":
        return 0, 100
    parts = re.findall(r"\d+", str(age_str))
    if len(parts) >= 2:
        return int(parts[0]), int(parts[1])
    return 0, 100

if 'Age' in df.columns:
    df[['Age Min', 'Age Max']] = df['Age'].apply(lambda x: pd.Series(extract_age_range(x)))
    df = df.drop(columns=['Age'])

# Chuẩn hóa cột 'Work Time' về định dạng HH:MM - HH:MM
def standardize_time(time_str):
    if isinstance(time_str, str):
        ts = time_str.replace('A.M.', 'AM').replace('P.M.', 'PM')
        ts = ts.replace('a.m.', 'AM').replace('p.m.', 'PM')
        ts = ts.replace(' A.M', ' AM').replace(' P.M', ' PM')
        if 'AM' in ts or 'PM' in ts:
            try:
                start, end = ts.split(' - ')
                start = datetime.strptime(start, '%I:%M %p').strftime('%H:%M')
                end = datetime.strptime(end, '%I:%M %p').strftime('%H:%M')
                return f'{start} - {end}'
            except:
                return np.nan
        elif 'h' in ts:
            ts = ts.replace('h', ':')
            try:
                start, end = ts.split(' - ')
                return f'{start} - {end}'
            except:
                return np.nan
        else:
            return ts.strip()
    return np.nan

if 'Work Time' in df.columns:
    df['Work Time'] = df['Work Time'].apply(standardize_time)

# Loại bỏ cột không cần thiết
drop_cols = ['Marital Status']
for col in drop_cols:
    if col in df.columns:
        df = df.drop(columns=[col])

# === Bắt đầu phần làm sạch cột Salary và quy về VND ===
# Tỷ giá USD→VND (có thể tuỳ chỉnh)
EXCHANGE_RATE_USD_TO_VND = 23000

def parse_salary(s):
    """
    Nhận chuỗi salary, trả về (min_vnd, max_vnd).
    Ưu tiên:
      1. 'triệu'/'tr' → *1e6
      2. '₫' hoặc 'đ': nếu nums[0]<1000 → USD (m=USD_RATE); else → nghìn VND (m=1e3)
      3. '$': nếu nums[0]>12000 → nghìn VND (m=1e3); else → USD (m=USD_RATE)
    Nếu chuỗi chứa '/năm' hoặc 'năm', chia 12 để ra lương tháng.
    'Thương lượng' → NaN
    """
    if pd.isna(s) or not isinstance(s, str):
        return np.nan, np.nan
    orig = s.strip()
    low = orig.lower()
    clean = re.sub(r'[\s,]', '', low)
    if 'thươnglượng' in clean:
        return np.nan, np.nan
    annual = '/năm' in low or 'năm' in low
    nums = [float(x) for x in re.findall(r"\d+\.?\d*", clean)]
    if not nums:
        return np.nan, np.nan
    # Xác định multiplier
    if 'triệu' in low or re.search(r'\d+tr', clean):
        m = 1_000_000
    elif '₫' in low or 'đ' in low:
        # Nếu giá trị nhỏ hơn 2000 ⇒ thực chất là USD
        if nums and nums[0] < 2000:
            m = EXCHANGE_RATE_USD_TO_VND
        else:
            m = 1_000
    elif '$' in low:
        # USD; nếu nums[0] lớn hơn 12000, coi là nghìn VND
        m = 1_000 if nums[0] > 12000 else EXCHANGE_RATE_USD_TO_VND
    else:
        m = 1
    vals = [v * m for v in nums]
    if annual:
        vals = [v / 12 for v in vals]
    return (vals[0], vals[1] if len(vals) > 1 else vals[0])

# Áp dụng parse_salary và drop cột gốc
if 'Salary' in df.columns:
    df[['salary_min_vnd', 'salary_max_vnd']] = df['Salary'].apply(parse_salary).tolist()
    df.drop(columns=['Salary'], inplace=True)

salary_brackets = [
    (       0,  10_000, [400, 1250, 1875, 2500, 3750, 5625]),
    (  10_000,  50_000, [100,  400,  500,   700,   800,  1000]),
    (  50_000, 100_000, [ 75,  200,  300,   400,   500,   550]),
    ( 100_000, 300_000, [ 30,   70,   90,   100,   120,   150]),
    ( 300_000, 500_000, [ 15,   25,   45,    60,   100,   120]),
    ( 500_000,1_000_000,[  7,   15,   25,    35,    45,    55]),
    (1_000_000,2_000_000,[ 3,    7,   12,    17,    20,    25]),
    (2_000_000,4_000_000,[ 2,    4,    7,     9,    10,    12]),
    (4_000_000,10_000_000,[1,    2,    3,     4,    4.5,    5]),
]

df['salary_avg_vnd'] = (df['salary_min_vnd'] + df['salary_max_vnd']) / 2


def get_salary_coeff(exp, salary):
    """
    exp: số năm kinh nghiệm (có thể >5)
    salary: giá trị salary_avg_vnd (đơn vị: VNĐ)
    Trả về hệ số tương ứng, với exp>5 sẽ được tính như exp=5
    """
    try:
        exp = int(exp)
    except:
        return np.nan

    # loại dòng không hợp lệ
    if exp < 0 or np.isnan(salary):
        return np.nan

    # clamp exp về tối đa 5
    if exp > 5:
        exp = 5

    for lower, upper, coeffs in salary_brackets:
        if lower <= salary < upper:
            return coeffs[exp]

    return np.nan

df['salary_coeff'] = df.apply(
    lambda row: get_salary_coeff(row['Experience'], row['salary_avg_vnd']),
    axis=1
)

df['salary_mins'] = df['salary_min_vnd'] * df['salary_coeff']
df['salary_maxs'] = df['salary_max_vnd'] * df['salary_coeff']

mask_no_coeff = df['salary_coeff'].isna()
df.loc[mask_no_coeff, 'salary_mins'] = df.loc[mask_no_coeff, 'salary_min_vnd']
df.loc[mask_no_coeff, 'salary_maxs'] = df.loc[mask_no_coeff, 'salary_max_vnd']

df.drop(['salary_min_vnd', 'salary_max_vnd', 'salary_coeff'], axis=1, inplace=True)


# 9. Lưu file kết quả
df.to_csv(output_csv_filename, index=False)
print(f"Đã hoàn thành làm sạch và lưu: {output_csv_filename}")