import os
import io
import re
import mimetypes
import gspread
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from googleapiclient.http import MediaFileUpload

class DataManager:

    def __init__(self):
        self.SCOPES = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]
        self.sheet_absent = "19gi66ttHcitgMnXFagj96pheg7aZbDMsF-mUgb4l2E0"
        self.sheet_assist = "1ANsn31hK0lGOBMr74-nR6WvzoqWuwMZdsRonXImAd-g"
        self.main_folder = "1NBN5RHLBC0AInTzzuHPuf1oSRXbx5XXi"
        self.zoom_logs = "1foe6f2ue5_x3QUjWX6r2614Qmglt0w0w"
        self.form_responses = "1pObzDeHwmHCvYjngzwh0YIx-Qm-IbtUD"
        self.absences_file = "1QXzvycOJKHtoIRcv1tUUOQCG6ROC2yT_RVK-4yjb99M"
        self.data_folder = "1tqg1QNqSdmErJX7RTZxXqhBEDBsUK_LD"
        creds = Credentials.from_service_account_file("util/keys.json", scopes=self.SCOPES)
        #self.downloader = MediaIoBaseDownload()
        self.service = build("drive", "v3", credentials=creds)
        self.client = gspread.authorize(creds)

    # Fetch files / Listing files

    # List files for a specific folder_id
    def list_files(self, folder_key="", filter_keywords=None):
        """
        List files in a folder, optionally filtering by keywords.

        Args:
            folder_key (str): Logical folder name ("", "zoom", "form").
            filter_keywords (list[str] | None): List of keywords to filter file names. Case-insensitive.

        Returns:
            list[dict]: List of file dicts from Drive API.
        """
        # Map logical folder keys to actual folder IDs
        folder_map = {
            "": self.main_folder,
            "zoom": self.zoom_logs,
            "form": self.form_responses
        }
        folder_id = folder_map.get(folder_key, folder_key)  # fallback: use folder_key as ID

        # Fetch files from Drive
        results = self.service.files().list(
            q=f"'{folder_id}' in parents and trashed = false",
            includeItemsFromAllDrives=True,
            supportsAllDrives=True,
            fields="files(id, name, mimeType)"
        ).execute()

        files = results.get("files", [])

        # Apply filtering if needed
        if filter_keywords:
            keywords_lower = [kw.lower() for kw in filter_keywords]
            files = [
                f for f in files
                if any(kw in f["name"].lower() for kw in keywords_lower)
            ]

        # Print for debug
        for f in files:
            print(f"{f['name']} ({f['id']}) - {f['mimeType']}")

        return files
    
    def get_zoom_logs(self):
        return self.list_files(self.zoom_logs)
    
    def get_form_responses(self):
        return self.list_files("form", filter_keywords=["respuestas"])
    
    def get_absences_file(self):
        return self.service.files().get(
            fileId=self.absences_file,
            fields="id, name, mimeType"
        ).execute()
    
    # Downloading files
    
    def download_file(self, file_id, file_name=None, folder_type="", output_folder="input"):
        file_meta = self.service.files().get(fileId=file_id, fields="mimeType,name").execute()
        mime_type = file_meta["mimeType"]

        if not file_name:
            file_name = file_meta.get("name") or file_id

        # Determine new name and extension
        name, ext = os.path.splitext(file_name)

        if folder_type == "zoom":
            # Match d or dd - mm - yyyy
            match = re.match(r"(\d{1,2})-(\d{2})-(\d{4})", name)
            if match:
                day = match.group(1).zfill(2)   # pad single-digit day
                month = match.group(2)
                new_file_name = f"log_{day}{month}{ext}"
            else:
                new_file_name = f"log_{name.replace('-', '')}{ext}"
        elif folder_type == "form":
            # Format: "Asistencia 1/10 (respuestas)" -> "form_0110.xlsx"
            match = re.search(r"(\d+)/(\d+)", name)
            new_name = f"form_{match.group(1).zfill(2)}{match.group(2).zfill(2)}" if match else f"form_{name}"
            new_file_name = new_name + ".xlsx"
        else:
            new_file_name = file_name

        if mime_type == "application/vnd.google-apps.spreadsheet" and not new_file_name.lower().endswith(".xlsx"):
            new_file_name = f"{os.path.splitext(new_file_name)[0]}.xlsx"

        os.makedirs(output_folder, exist_ok=True)
        file_path = os.path.join(output_folder, new_file_name)

        if os.path.exists(file_path):
            print(f"⏭️ Skipping (already downloaded): {new_file_name}")
            return file_path

        fh = io.FileIO(file_path, "wb")

        if mime_type == "application/vnd.google-apps.spreadsheet":
            # Export as XLSX
            request = self.service.files().export_media(
                fileId=file_id,
                mimeType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            request = self.service.files().get_media(fileId=file_id)

        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
            if status:
                print(f"⬇️ Download {int(status.progress() * 100)}%...")

        print(f"✅ Downloaded: {new_file_name} → {file_path}")
        return file_path
    
    def download_zoom_logs(self):
        files = self.get_zoom_logs()
        for f in files:
            self.download_file(f["id"], f["name"], folder_type="zoom", output_folder="input")

    def download_form_responses(self):
        files = self.get_form_responses()
        # Load download state to decide whether to re-download updated forms
        state_path = os.path.join('data', 'download_state.json')
        try:
            import json
            if os.path.exists(state_path):
                with open(state_path, 'r', encoding='utf-8') as sf:
                    state = json.load(sf)
            else:
                state = {}
        except Exception:
            state = {}

        updated_state = dict(state)  # copy

        for f in files:
            # get file metadata including modifiedTime
            meta = self.service.files().get(fileId=f['id'], fields='id,name,modifiedTime').execute()
            modified = meta.get('modifiedTime')
            prev_mod = state.get(f['id'])
            if prev_mod != modified:
                # download and overwrite existing local file
                path = self.download_file(f['id'], f['name'], folder_type='form', output_folder='input')
                updated_state[f['id']] = modified
            else:
                print(f"⏭️ No change for {f['name']} ({f['id']})")

        # Save updated state
        try:
            os.makedirs('data', exist_ok=True)
            with open(state_path, 'w', encoding='utf-8') as sf:
                json.dump(updated_state, sf, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️ Could not save download state: {e}")

    def download_absences_file(self):
        file_info = self.get_absences_file()
        self.download_file(file_info["id"], "ausencias", output_folder="input")

    # Here will start with sheet reading / updating later

    def get_sheet_values(self, sheet):
        match sheet:
            case "assist":
                sheet = self.client.open_by_key(self.sheet_assist)
            case "absences":
                sheet = self.client.open_by_key(self.sheet_absent)
        values_list = sheet.sheet1.get_values()
        print(values_list)

    def upload_file(self, local_path, destination_name=None, mime_type=None, folder_id=None):
        """
        Upload a local file to Google Drive into `folder_id` (defaults to self.data_folder).

        If a file with the same name already exists in the target folder, this function will
        update (overwrite) that file. Otherwise it will create a new file.

        Returns the Drive file metadata dict for the created/updated file.
        """
        if not os.path.exists(local_path):
            raise FileNotFoundError(f"Local file not found: {local_path}")

        folder_id = folder_id or self.data_folder
        destination_name = destination_name or os.path.basename(local_path)

        # Detect MIME type if not supplied
        if not mime_type:
            guess, _ = mimetypes.guess_type(local_path)
            mime_type = guess or 'application/octet-stream'

        # Find existing file with same name in the folder
        safe_name = destination_name.replace("'", "\\'")
        q = f"'{folder_id}' in parents and name = '{safe_name}' and trashed = false"
        res = self.service.files().list(q=q, fields='files(id,name)').execute()
        files = res.get('files', [])

        media = MediaFileUpload(local_path, mimetype=mime_type, resumable=True)

        if files:
            file_id = files[0]['id']
            print(f"Updating existing file {destination_name} ({file_id}) in folder {folder_id}")
            updated = self.service.files().update(fileId=file_id, media_body=media, body={'name': destination_name}).execute()
            print(f"✅ Updated: {updated.get('name')} ({updated.get('id')})")
            return updated
        else:
            body = {'name': destination_name, 'parents': [folder_id]}
            created = self.service.files().create(body=body, media_body=media, fields='id,name').execute()
            print(f"✅ Uploaded: {created.get('name')} ({created.get('id')})")
            return created



if __name__ == "__main__":
    dm = DataManager()
    files = dm.get_zoom_logs()
    for f in files:
        print(f"{f['name']} ({f['id']}) - {f['mimeType']}")
