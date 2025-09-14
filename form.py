import pandas as pd
import os
from datetime import datetime
from pathlib import Path

class FormFile:

    df = pd.DataFrame()

    def __init__(self, file_location):
        self.df = pd.read_excel(file_location)
        self.cleanup_comments()
        self.cleanup_columns()
        self.file_path = file_location
        self.date = self._extract_date_from_filename()
        #self.df = self._load_and_process()
        #self.df['source_date'] = self.date

    def cleanup_comments(self):
        self.df['Marca temporal'] = pd.to_datetime(self.df['Marca temporal'], format='%m/%d/%Y %H:%M:%S', errors='coerce')
        self.df[self.df['Marca temporal'].astype(str).str.match(r'^\d{1,2}/\d{1,2}/\d{4}')]
        self.df.dropna(subset=['Marca temporal'], inplace=True)

    def cleanup_columns(self):
        self.df.rename(columns={
            'Apellido y Nombre (RESPETAR ORDEN)': 'name',
            'Marca temporal': 'date',
            'Dirección de correo electrónico': 'email'
        }, inplace=True)
        self.df = self.df[['name', 'date', 'email']]

    def _extract_date_from_filename(self):
        """Extract date from filename in format like 'form_2305.csv'"""
        filename = Path(self.file_path).stem
        date_str = filename.split('_')[-1]  # Assumes format prefix_date
        return datetime.strptime(date_str, "%d%m").strftime("%d/%m")
    
    def _load_and_process(self):
        df = pd.read_excel(self.file_path)
        df['source_date'] = self.date  # Track which file this came from
        return df

    def output_to_csv(self, output_dir='output'):
        os.makedirs(output_dir, exist_ok=True)
        output_path = f"{output_dir}/form_processed_{self.date.replace('/', '')}.csv"
        self.df.to_csv(output_path, index=False)
        return output_path

    def print_data(self):
        print(self.df)