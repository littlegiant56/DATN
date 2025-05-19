import pandas as pd
import numpy as np
from datetime import datetime, timedelta

yesterday = datetime.now() #- timedelta(1)
input_csv_filename = "Rawdata/Jobs/VNW_" + yesterday.strftime("%d-%m-%Y") + "_jobs.csv"
output_csv_filename ="VNW_" + yesterday.strftime("%d-%m-%Y") + "_jobs_cleaned.csv"
df = pd.read_csv(input_csv_filename)

df['Date Posted'] = pd.to_datetime(df['Date Posted'], format='%d/%m/%Y')

replacements = {
    'T2': 'Thứ 2',
    'T3': 'Thứ 3',
    'T4': 'Thứ 4',
    'T5': 'Thứ 5',
    'T6': 'Thứ 6',
    'T7': 'Thứ 7',
    'CN': 'Chủ Nhật',
    ',':  'và',
    '-': 'đến'
}

# Thay thế trong cột 'Work Date'
df['Work Date'] = df['Work Date'].replace(replacements, regex=True)

df['Experience'] = df['Experience'].replace('Không yêu cầu', '0')
df['Experience'] = pd.to_numeric(df['Experience'], errors='coerce')

df[['Industry', 'Industry1']] = df['Industry'].str.split(' > ', expand=True)

def extract_age_range(age_str):
    if age_str == "Không hiển thị":
        return 0, 100
    else:
        try:
            age_min, age_max = age_str.split("-")
            return int(age_min), int(age_max)
        except:
            return 0, 100  # In case the format is not expected

# Apply the function to the "Age" column and create new "Age Min" and "Age Max" columns
df[['Age Min', 'Age Max']] = df['Age'].apply(lambda x: pd.Series(extract_age_range(x)))

df = df.drop(columns=['Age'])

def standardize_time(time_str):
    if isinstance(time_str, str):
        # Thay thế tất cả các kiểu A.M., P.M., a.m., p.m. thành AM, PM
        time_str = time_str.replace('A.M.', 'AM').replace('P.M.', 'PM').replace('a.m.', 'AM').replace('p.m.', 'PM')
        
        # Thay thế các kiểu chữ hoa "A.M" và "P.M" viết hoa
        time_str = time_str.replace(' A.M', ' AM').replace(' P.M', ' PM')

        # Xử lý trường hợp AM/PM
        if 'AM' in time_str or 'PM' in time_str:
            try:
                start, end = time_str.split(' - ')
                start = datetime.strptime(start, '%I:%M %p').strftime('%H:%M')
                end = datetime.strptime(end, '%I:%M %p').strftime('%H:%M')
                return f'{start} - {end}'
            except ValueError:
                return np.nan
        # Xử lý định dạng giờ 24h (ví dụ: 08:00 - 17:00)
        elif 'h' in time_str:
            time_str = time_str.replace('h', ':')
            try:
                start, end = time_str.split(' - ')
                return f'{start} - {end}'
            except ValueError:
                return np.nan
        # Xử lý các định dạng giờ khác
        else:
            return time_str.strip()
    return np.nan

df['Work Time'] = df['Work Time'].apply(standardize_time)

df = df.drop('Marital Status', axis=1)

df.to_csv(output_csv_filename, index=False)