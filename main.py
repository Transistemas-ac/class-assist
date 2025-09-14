from logs import LogFile
from form import FormFile
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

    combined_form.to_csv('data/comb_form.csv')
    combined_log.to_csv('data/comb_log.csv')
    
    return combined_form, combined_log

def generate_final_report(combined_form, combined_log, alumni_file="data/alumni.csv"):
    # Load alumni data
    names_table = pd.read_csv(alumni_file)
    
    # Process dates to get day/month format - using the combined tables passed as parameters
    combined_log['date_dm'] = pd.to_datetime(combined_log['date'], errors='coerce', format='%d/%m/%Y %H:%M:%S %p').dt.strftime('%d/%m')
    combined_form['date_dm'] = pd.to_datetime(combined_form['date'], errors='coerce', format='%Y-%m-%d %H:%M:%S.%f').dt.strftime('%d/%m')
    
    # Get unique dates from both tables
    all_dates = sorted(set(combined_log['date_dm'].dropna().unique()).union(
                       set(combined_form['date_dm'].dropna().unique())))
    
    # Create a mapping of all name variations to primary name
    name_mapping = {}
    for _, row in names_table.iterrows():
        primary_name = row['name']
        name_mapping[primary_name.lower()] = primary_name
        if pd.notna(row['alternate name']):
            name_mapping[str(row['alternate name']).lower()] = primary_name
        if pd.notna(row['email']):
            name_mapping[str(row['email']).lower()] = primary_name

    # Create presence records for each name
    results = []
    for _, name_row in names_table.iterrows():
        primary_name = name_row['name']
        record = {'Name': primary_name}
        
        # Get all identifiers for this person
        identifiers = [primary_name.lower()]
        if pd.notna(name_row['alternate name']):
            identifiers.append(str(name_row['alternate name']).lower())
        if pd.notna(name_row['email']):
            identifiers.append(str(name_row['email']).lower())
        
        # Check presence for each date
        for date in all_dates:
            in_log = False
            in_form = False
            
            # Check log table
            if not combined_log.empty:
                log_matches = combined_log[
                    (combined_log['date_dm'] == date) & 
                    (combined_log['name'].str.lower().isin(identifiers))
                ]
                in_log = not log_matches.empty
            
            # Check form table
            if not combined_form.empty:
                form_matches = combined_form[
                    (combined_form['date_dm'] == date) & 
                    ((combined_form['name'].str.lower().isin(identifiers)) | 
                    (combined_form['email'].str.lower().isin(identifiers)))
                ]
                in_form = not form_matches.empty
            
            # Determine status
            if in_log and in_form:
                record[date] = 'both'
            elif in_log:
                record[date] = 'log'
            elif in_form:
                record[date] = 'form'
            else:
                record[date] = 'absent'
        
        results.append(record)

    # Convert to DataFrame
    result_df = pd.DataFrame(results)

    # Reorder columns to have Name first, then dates in order
    columns = ['Name'] + all_dates
    result_df = result_df[columns]
    
    # Save final report
    os.makedirs('output', exist_ok=True)
    final_output = "output/final_presence_report.xlsx"
    final_csv = "output/final_results.csv"
    result_df.to_excel(final_output, index=False)
    result_df.to_csv(final_csv, index=False)
    return final_output


if __name__ == "__main__":
    combined_form, combined_log = process_all_files()
    final_report = generate_final_report(combined_form, combined_log)
    print(f"Final report saved to {final_report}")