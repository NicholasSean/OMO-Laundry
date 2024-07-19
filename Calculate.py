import pandas as pd
import streamlit as st

file = "log.xlsx"
df = pd.read_excel(file)
# Drop unused columns.
drop_columns = ['Latitude', 'Longitude', 'Sumber Pencatatan']
df = df.drop(columns = drop_columns)
df['Tanggal Absen'] = df['Tanggal Absen'].str[:2].astype(int)
df = df[(df['Tanggal Absen'] >= 8) & (df['Tanggal Absen'] <= 14)]
df = df.sort_values(by='Nama Karyawan')
work_count = df.groupby('Nama Karyawan')['Status Kehadiran'].value_counts().unstack().fillna(0)
# Only leave row entries when worker worked.
df = df[df['Status Kehadiran'] == 'Masuk']
# Calculate time difference for number of hours worked.
df['Absen Masuk'] = df['Absen Masuk'].str.split(' - ').str[1]
df['Absen Pulang'] = df['Absen Pulang'].str.split(' - ').str[1]

tidak_absen_pulang = df[df['Absen Pulang'].isna() | (df['Absen Pulang'] == '')]
tidak_absen_pulang .to_csv('tidak_absen pulang .csv', index=False)
tidak_absen_pulang_count = tidak_absen_pulang['Nama Karyawan'].value_counts().reset_index()
tidak_absen_pulang_count.columns = ['Nama Karyawan', 'No Clock Out']
df = df.dropna(subset=['Absen Pulang'])
df = df[df['Absen Pulang'] != '']
# Calculate Hours Worked.
df['Absen Masuk'] = pd.to_datetime(df['Absen Masuk'], format='%H:%M:%S')
df['Absen Pulang'] = pd.to_datetime(df['Absen Pulang'], format='%H:%M:%S')

# Calculate the time difference and convert it to hours
df['hours_worked'] = (df['Absen Pulang'] - df['Absen Masuk']).dt.total_seconds() / 3600
Long_shift = df[df['hours_worked'] >= 14].groupby('Nama Karyawan').size().reset_index(name='Long Shift')
# Determine scheduled start time.
def round_to_nearest_start_time(time):
    schedule_times = [pd.to_datetime('06:00:00', format='%H:%M:%S'),
                      pd.to_datetime('08:00:00', format='%H:%M:%S'),
                      pd.to_datetime('11:00:00', format='%H:%M:%S')]
    nearest_time = min(schedule_times, key=lambda x: abs(time - x))
    return nearest_time
df['Scheduled Start Time'] = df['Absen Masuk'].apply(round_to_nearest_start_time)
df['late_minutes'] = (df['Absen Masuk'] - df['Scheduled Start Time']).dt.total_seconds() / 60
df['late_minutes'] = df['late_minutes'].apply(lambda x: x if x > 0 else 0)

# Calculate offences
def calculate_offences(late_minutes):
    if late_minutes <= 10:
        return 0
    return (late_minutes - 10) // 10

df['late_offences'] = df['late_minutes'].apply(calculate_offences)
late_offences_summary = df.groupby('Nama Karyawan')['late_offences'].sum().reset_index(name='Late Offences')

df.to_csv('cleaned_data_with_hours_worked.csv', index=False)
# Create a df with the breakdown of shifts for easy payment
final_df = pd.merge(work_count, Long_shift, on='Nama Karyawan')
final_df['Short Shift'] = final_df['Masuk'] - final_df['Long Shift']
# Highlight shifts that did not clock out.
final_df = pd.merge(final_df, late_offences_summary, on='Nama Karyawan')
final_df = pd.merge(final_df, tidak_absen_pulang_count, on='Nama Karyawan', how='left').fillna(0)
# Calculate Salary.
final_df['Salary'] = (final_df['Short Shift'] * 50000) + (final_df['Long Shift'] * 75000) - (final_df['Late Offences'] * 10000)
print(final_df)