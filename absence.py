import pandas as pd
from pathlib import Path
import os


class AbsenceFile:
    df = pd.DataFrame()

    def __init__(self, file_location):
        self.file_path = Path(file_location)
        self.df = pd.read_excel(self.file_path)
        self._cleanup_columns()
        self._cleanup_time()

    def _cleanup_columns(self):
        self.df.columns = self.df.columns.str.replace(' ', '', regex=False)
        self.df.rename(columns={
            'Nombre': 'name',
            'Mail': 'email',
            'Fecha': 'date'
        }, inplace=True)

    def _cleanup_time(self):
        self.df['date'] = pd.to_datetime(self.df['date'])
        self.df['date'] = self.df['date'].dt.strftime('%d/%m')

    def output_to_csv(self, output_dir='output'):
        os.makedirs(output_dir, exist_ok=True)
        output_path = Path(output_dir) / 'ausencias_processed.csv'
        self.df.to_csv(output_path, index=False)
        return output_path

    def print_data(self):
        print(self.df)
