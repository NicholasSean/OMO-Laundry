import pandas as pd
import streamlit as st

# Function to process the log file
def process_log(file, salary_file, start_day, end_day):
    df = pd.read_excel(file)
    salary_df = pd.read_excel(salary_file)
    # Drop unused columns
    drop_columns = ['Latitude', 'Longitude', 'Sumber Pencatatan']
    df = df.drop(columns=drop_columns)

    # Extract the day from the 'Tanggal Absen' column
    df['Tanggal Absen'] = df['Tanggal Absen'].str[:2].astype(int)

    # Filter the data to include only the specified day range
    df = df[(df['Tanggal Absen'] >= start_day) & (df['Tanggal Absen'] <= end_day)]

    # Sort values
    df = df.sort_values(by='Nama Karyawan')

    # Group by and count attendance statuses
    work_count = df.groupby('Nama Karyawan')['Status Kehadiran'].value_counts().unstack().fillna(0)

    # Filter for rows where the worker worked
    df = df[df['Status Kehadiran'] == 'Masuk']

    # Process time columns
    df['Absen Masuk'] = df['Absen Masuk'].str.split(' - ').str[1]
    df['Absen Pulang'] = df['Absen Pulang'].str.split(' - ').str[1]

    # Handle missing 'Absen Pulang'
    tidak_absen_pulang = df[df['Absen Pulang'].isna() | (df['Absen Pulang'] == '')]
    tidak_absen_pulang_count = tidak_absen_pulang['Nama Karyawan'].value_counts().reset_index()
    tidak_absen_pulang_count.columns = ['Nama Karyawan', 'No Clock Out']

    df = df.dropna(subset=['Absen Pulang'])
    df = df[df['Absen Pulang'] != '']

    # Convert time columns to datetime
    df['Absen Masuk'] = pd.to_datetime(df['Absen Masuk'], format='%H:%M:%S')
    df['Absen Pulang'] = pd.to_datetime(df['Absen Pulang'], format='%H:%M:%S')

    # Calculate hours worked
    df['hours_worked'] = (df['Absen Pulang'] - df['Absen Masuk']).dt.total_seconds() / 3600
    Long_shift = df[df['hours_worked'] >= 14].groupby('Nama Karyawan').size().reset_index(name='Long Shift')

    # Determine scheduled start time
    def round_to_nearest_start_time(time):
        schedule_times = [pd.to_datetime('06:00:00', format='%H:%M:%S'),
                          pd.to_datetime('09:00:00', format='%H:%M:%S'),
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

    # Create a final DataFrame with the breakdown of shifts for easy payment
    final_df = pd.merge(work_count, Long_shift, on='Nama Karyawan')
    final_df['Short Shift'] = final_df['Masuk'] - final_df['Long Shift']

    # Highlight shifts that did not clock out
    final_df = pd.merge(final_df, late_offences_summary, on='Nama Karyawan')
    final_df = pd.merge(final_df, tidak_absen_pulang_count, on='Nama Karyawan', how='left').fillna(0)
    final_df = pd.merge(final_df, salary_df, on='Nama Karyawan', how='left').fillna(0)
    # Calculate Salary
    final_df['Salary'] = (final_df['Short Shift'] * final_df['Short Shift Pay']) + (final_df['Long Shift'] * final_df['Long Shift Pay']) - (final_df['Late Offences'] * 10000)

    return final_df

# Streamlit UI
st.title("Attendance Log Processor")

# Upload log file
uploaded_file = st.file_uploader("Upload Log file", type="xlsx")
salary_file = st.file_uploader("Upload Salary file", type="xlsx")
# Date range input
start_day = st.number_input("Start Day", min_value=1, max_value=31, value=8)
end_day = st.number_input("End Day", min_value=1, max_value=31, value=14)

# Process the file when uploaded
if uploaded_file is not None and salary_file is not None:
    df = process_log(uploaded_file, salary_file, start_day, end_day)
    st.write(df)

    # Download the processed file
    processed_file = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Download Processed Data as CSV",
        data=processed_file,
        file_name='final_report.csv',
        mime='text/csv',
    )
