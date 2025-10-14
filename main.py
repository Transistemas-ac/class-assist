from logs import LogFile
from form import FormFile
from absence import AbsenceFile
from util.datamanager import DataManager
from datetime import datetime
import pandas as pd
from pathlib import Path
import os

"""
test_log = LogFile('zoom_logs\Copy of participantes23deMayode2025.ods')
test_log.output_to_csv()

test_form = FormFile('assistance\Asistencia Clase 23_05 (Respuestas).xlsx')
test_form.output_to_csv()
"""

print("Form files found:", [str(f) for f in Path("input").glob("form_*.xlsx")])
print("Log files found:", [str(f) for f in Path("input").glob("log_*.ods")])

def process_all_files(input_dir="input"):
    # Find all relevant files
    form_files = [f for f in Path(input_dir).glob("form_*.xlsx")]
    log_files = [f for f in Path(input_dir).glob("log_*.ods")]
    absences_file = Path(input_dir) / "ausencias.xlsx"
    
    # Process all form files
    all_forms = []
    for form_file in form_files:
        form = FormFile(form_file)
        #form.output_to_csv()
        all_forms.append(form.df)
    
    # Process all log files
    all_logs = []
    for log_file in log_files:
        log = LogFile(log_file)
        #log.output_to_csv()
        all_logs.append(log.df)
    
    # Combine all processed data
    combined_form = pd.concat(all_forms) if all_forms else pd.DataFrame()
    combined_log = pd.concat(all_logs) if all_logs else pd.DataFrame()
    absences_df = AbsenceFile(absences_file).df

    combined_form.to_csv('data/comb_form.csv')
    combined_log.to_csv('data/comb_log.csv')
    absences_df.to_csv('data/absences.csv')
    
    return combined_form, combined_log, absences_df

def generate_final_report(combined_form, combined_log, absences_df, alumni_file="data/alumni.csv"):
    # Load alumni data
    names_table = pd.read_csv(alumni_file)

    # Process dates to get day/month format - using the combined tables passed as parameters
    combined_log['date'] = pd.to_datetime(combined_log['date'], errors='coerce', format='%d/%m/%Y %H:%M:%S %p').dt.strftime('%d/%m')
    combined_form['date'] = pd.to_datetime(combined_form['date'], errors='coerce', format='%Y-%m-%d %H:%M:%S.%f').dt.strftime('%d/%m')

    # Get unique dates from both tables and sort by date value
    all_dates_raw = set(combined_log['date'].dropna().unique()).union(
                       set(combined_form['date'].dropna().unique()))
    # Convert to datetime, sort, then back to string
    all_dates_sorted = sorted(
        [datetime.strptime(d, "%d/%m") for d in all_dates_raw if d]
    )
    all_dates = [dt.strftime("%d/%m") for dt in all_dates_sorted]

    # Create a mapping of all name variations to primary name
    name_mapping = {}
    alumni_name_identifiers = set()
    alumni_email_identifiers = set()
    for _, row in names_table.iterrows():
        if pd.notna(row['name']):
            alumni_name_identifiers.add(str(row['name']).strip().lower())
        if pd.notna(row['alternate name']):
            alternates = [alt.strip().lower() for alt in str(row['alternate name']).split(';') if alt.strip()]
            alumni_name_identifiers.update(alternates)
        if pd.notna(row['email']):
            alumni_email_identifiers.add(str(row['email']).strip().lower())

    # Create presence records for each name
    results = []
    for _, name_row in names_table.iterrows():
        primary_name = name_row['name']
        record = {'Name': primary_name}

        # Get all identifiers for this person
        identifiers = [str(primary_name).strip().lower()]
        if pd.notna(name_row['alternate name']):
            alternates = [alt.strip().lower() for alt in str(name_row['alternate name']).split(';') if alt.strip()]
            identifiers.extend(alternates)
        if pd.notna(name_row['email']):
            identifiers.append(str(name_row['email']).strip().lower())

        # Check presence for each date
        for date in all_dates:
            in_log = False
            in_form = False
            is_justified = False

            # Check log table
            if not combined_log.empty:
                log_matches = combined_log[
                    (combined_log['date'] == date) & 
                    (combined_log['name'].str.lower().isin(identifiers))
                ]
                in_log = not log_matches.empty

            # Check form table
            if not combined_form.empty:
                form_matches = combined_form[
                    (combined_form['date'] == date) & 
                    ((combined_form['name'].str.lower().isin(identifiers)) | 
                    (combined_form['email'].str.lower().isin(identifiers)))
                ]
                in_form = not form_matches.empty

            # Check absences table
            if not absences_df.empty:
                abs_matches = absences_df[
                    (absences_df['date'] == date) &
                    (
                        absences_df['name'].str.lower().isin(identifiers) |
                        absences_df['email'].str.lower().isin(identifiers)
                    )
                ]
                is_justified = not abs_matches.empty

            # Determine status with 'parcial' for short log durations
            if is_justified:
                record[date] = 'justificado'
            elif in_log and in_form:
                record[date] = 'ambos'
            elif in_log:
                # Check if all matching log durations are numeric and < 30 minutes
                try:
                    durations = pd.to_numeric(log_matches['duration'], errors='coerce')
                except Exception:
                    durations = pd.Series(dtype='float64')

                if (not durations.empty) and durations.notna().all() and (durations < 30).all():
                    record[date] = 'parcial'
                else:
                    record[date] = 'log'
            elif in_form:
                record[date] = 'form'
            else:
                record[date] = 'ausente'

        results.append(record)

    # Convert to DataFrame
    result_df = pd.DataFrame(results)

    # Reorder columns to have Name first, then dates in order
    columns = ['Name'] + all_dates
    result_df = result_df[columns]

    # Exclude the internal/team record from the report
    mask_team = result_df['Name'].astype(str).str.strip().str.lower() == 'transistemas equipo'.strip().lower()
    if mask_team.any():
        result_df = result_df[~mask_team].reset_index(drop=True)

    # Save final report and create attendance summary
    os.makedirs('output', exist_ok=True)
    final_output = "output/final_results.xlsx"
    final_csv = "output/final_results.csv"

    # Build attendance summary: presente = ambos/log/form/parcial, ausente = ausente/justificado
    date_cols = all_dates
    present_statuses = {'ambos', 'log', 'form', 'parcial'}
    absent_statuses = {'ausente', 'justificado'}

    # Count occurrences across date columns
    # Summary should be computed from the filtered result_df (team excluded)
    presente_counts = result_df[date_cols].apply(lambda row: row.isin(present_statuses).sum(), axis=1)
    ausente_counts = result_df[date_cols].apply(lambda row: row.isin(absent_statuses).sum(), axis=1)
    summary_df = pd.DataFrame({
        'Name': result_df['Name'],
        'presente': presente_counts,
        'ausente': ausente_counts
    })

    # Now compute 'Asistencias' totals per date (number of people present in each date column)
    asistencias_per_date = {col: int(result_df[col].isin(present_statuses).sum()) for col in date_cols}
    asistencias_row = {'Name': 'Asistencias'}
    asistencias_row.update(asistencias_per_date)
    # Append the asistencias row to the result_df for the Excel output
    asistencias_df = pd.DataFrame([asistencias_row])
    # Ensure same column order (Name + dates)
    asistencias_df = asistencias_df[['Name'] + date_cols]
    result_with_totals = pd.concat([result_df, asistencias_df], ignore_index=True)

    # Write both sheets to the Excel file
    try:
        with pd.ExcelWriter(final_output, engine='openpyxl') as writer:
            # write the attendance sheet with the totals row
            result_with_totals.to_excel(writer, sheet_name='attendance', index=False)
            summary_df.to_excel(writer, sheet_name='summary', index=False)
    except Exception:
        # Fallback if openpyxl isn't available: write only the main sheet
        result_with_totals.to_excel(final_output, index=False)

    # Also save CSVs
    result_with_totals.to_csv(final_csv, index=False)
    summary_df.to_csv('output/summary.csv', index=False)

    # Create review file with unmatched records:
    # Only add if neither name nor email matches any alumni identifier (main, alternate, or email)
    def is_unmatched_form(row):
        name = str(row['name']).strip().lower() if pd.notna(row['name']) else ''
        email = str(row['email']).strip().lower() if pd.notna(row['email']) else ''
        return (name not in alumni_name_identifiers) and (email not in alumni_email_identifiers)

    def is_unmatched_log(row):
        name = str(row['name']).strip().lower() if pd.notna(row['name']) else ''
        return name not in alumni_name_identifiers

    unmatched_forms = combined_form[combined_form.apply(is_unmatched_form, axis=1)]
    unmatched_logs = combined_log[combined_log.apply(is_unmatched_log, axis=1)]

    # Restrict columns to name, email (if present), and date
    form_cols = [col for col in ['name', 'email', 'date'] if col in unmatched_forms.columns]
    log_cols = [col for col in ['name', 'date', 'duration'] if col in unmatched_logs.columns]
    unmatched_forms = unmatched_forms[form_cols]
    unmatched_logs = unmatched_logs[log_cols]
    unmatched_logs['email'] = ''  # Add empty email column for logs for consistency
    unmatched_forms['duration'] = ''  # Add empty duration column for forms for consistency
    unmatched_logs = unmatched_logs[['name', 'email', 'date', 'duration']]
    unmatched_forms = unmatched_forms[['name', 'email', 'date', 'duration']]

    review_df = pd.concat([unmatched_forms, unmatched_logs], ignore_index=True)
    review_df['date'] = pd.to_datetime(review_df['date'], errors='coerce')
    review_df['date'] = review_df['date'].dt.strftime('%d/%m/%Y')
    review_path = "output/review.xlsx"
    review_csv = "output/review.csv"
    review_df.to_excel(review_path, index=False)
    review_df.to_csv(review_csv, index=False)

    return final_output


if __name__ == "__main__":
    dm = DataManager()
    #dm.download_zoom_logs()
    #dm.download_form_responses()
    #dm.download_absences_file()
    combined_form, combined_log, absences_df = process_all_files()
    final_report = generate_final_report(combined_form, combined_log, absences_df)
    print(f"Final report saved to {final_report}")
    dm.upload_file("output/final_results.xlsx")
