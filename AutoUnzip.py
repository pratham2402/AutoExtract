import os
import zipfile
import time

# Paths to the directories and files (generalized placeholders)
downloads_folder = 'path/to/downloads/folder'  # Replace with actual path to the Downloads folder
unzip_to_folder = 'path/to/extracted/files/folder'  # Replace with the path to extract files
processed_files_file = 'path/to/processed_files.txt'  # Replace with the path to store processed file names (A text file will be created at this location)

def unzip_file(zip_path, extract_to):
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_to)
    print(f"Unzipped: {zip_path} to {extract_to}")

def load_processed_files():
    if os.path.exists(processed_files_file):
        with open(processed_files_file, 'r') as f:
            return set(f.read().splitlines())
    return set()

def save_processed_files(processed_files):
    with open(processed_files_file, 'w') as f:
        for file_name in processed_files:
            f.write(file_name + '\n')

def monitor_and_unzip():
    processed_files = load_processed_files()
    while True:
        files = os.listdir(downloads_folder)
        for file_name in files:
            if file_name.endswith(".zip") and file_name not in processed_files:
                zip_file_path = os.path.join(downloads_folder, file_name)

                unzip_file(zip_file_path, unzip_to_folder)

                processed_files.add(file_name)

                save_processed_files(processed_files)

        time.sleep(10) 

if __name__ == "__main__":
    monitor_and_unzip()
