import pandas as pd
file = "log.xlsx"
df = pd.read_excel(file)
# Drop unused columns.
drop_columns = ['Latitude', 'Longitude', 'Sumber Pencatatan']
df = df.drop(columns = drop_columns)
df = df.sort_values(by='Nama Karyawan')
#print(df)
work_count = df.groupby('Nama Karyawan')['Status Kehadiran'].value_counts().unstack().fillna(0)
#print(count_df)
# Only leave row entries when worker worked.
df = df[df['Status Kehadiran'] == 'Masuk']
# Calculate time difference for number of hours worked.
#df = df.dropna(subset=['Absen Masuk', 'Absen Pulang'])
df['Absen Masuk'] = df['Absen Masuk'].str.split(' - ').str[1]
df['Absen Pulang'] = df['Absen Pulang'].str.split(' - ').str[1]

tidak_absen_pulang = df[df['Absen Pulang'].isna() | (df['Absen Pulang'] == '')]
tidak_absen_pulang .to_csv('tidak_absen pulang .csv', index=False)
df = df.dropna(subset=['Absen Pulang'])
df = df[df['Absen Pulang'] != '']
# Calculate Hours Worked.
df['Absen Masuk'] = pd.to_datetime(df['Absen Masuk'], format='%H:%M:%S')
df['Absen Pulang'] = pd.to_datetime(df['Absen Pulang'], format='%H:%M:%S')

# Calculate the time difference and convert it to hours
df['hours_worked'] = (df['Absen Pulang'] - df['Absen Masuk']).dt.total_seconds() / 3600
Long_shift = df[df['hours_worked'] >= 14].groupby('Nama Karyawan').size().reset_index(name='Long Shift')
df.to_csv('cleaned_data_with_hours_worked.csv', index=False)
# Create a df with the breakdown of shifts for easy payment
final_df = pd.merge(work_count, Long_shift, on='Nama Karyawan')
final_df['Short Shift'] = final_df['Masuk'] - final_df['Long Shift']
print(final_df)