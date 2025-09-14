import pandas as pd
import os
from datetime import datetime
from pathlib import Path

class LogFile:
    df = pd.DataFrame()

    def __init__(self, file_location):
        self.df = read_csv_with_header_check(file_location)
        self.cleanup_columns()
        self.cleanup_time()
        self.group_data()
        self.file_path = file_location
        self.date = self._extract_date_from_filename()
        #self.df = self._load_and_process()
        #self.df['source_date'] = self.date

    def cleanup_columns(self):
        self.df.rename(columns={
            'Name (original name)': 'name',
            'Join time': 'date',
            'Duration (minutes)': 'duration'
        }, inplace=True)

    def cleanup_time(self):
        self.df['date'] = pd.to_datetime(self.df['date'])
        self.df['date'] = self.df['date'].dt.strftime('%d/%m/%Y %I:%M:%S %p')

    def group_data(self):
        result = self.df.groupby('name').agg({
            'date': 'first',
            'duration': 'sum'
        }).reset_index()
        self.df = result

    def _extract_date_from_filename(self):
        """Extract date from filename in format like 'log_1605.csv'"""
        filename = Path(self.file_path).stem
        date_str = filename.split('_')[-1]  # Assumes format prefix_date
        return datetime.strptime(date_str, "%d%m").strftime("%d/%m")
    
    def _load_and_process(self):
        df = pd.read_excel(self.file_path)
        df['source_date'] = self.date  # Track which file this came from
        return df
    
    def output_to_csv(self, output_dir="output"):
        os.makedirs(output_dir, exist_ok=True)
        output_path = f"{output_dir}/log_processed_{self.date.replace('/', '')}.csv"
        self.df.to_csv(output_path, index=False)
        return output_path

    def print_data(self):
        print(self.df)

def read_csv_with_header_check(file_path, expected_header="Name (original name)", skip_if_missing=3):
    """Read CSV file, checking if first cell matches expected header"""
    try:
        # First try reading without skipping rows
        df_first_try = pd.read_excel(file_path, nrows=1)
        
        # Check if first column name matches expected header
        if df_first_try.columns[0] == expected_header:
            # Read full file with correct headers
            return pd.read_excel(file_path)
        else:
            # Skip specified number of rows if header doesn't match
            return pd.read_excel(file_path, skiprows=skip_if_missing)
    except Exception as e:
        print(f"Error reading {file_path}: {str(e)}")
        return pd.DataFrame(columns=[expected_header, 'date'])