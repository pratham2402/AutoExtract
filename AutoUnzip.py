import os
import zipfile
import rarfile  
import time

# Paths to the directories and files (generalized placeholders)
downloads_folder = 'path/to/downloads/folder'  # Replace with the actual path to the Downloads folder
unzip_to_folder = 'path/to/extracted/files/folder'  # Replace with the path to extract files
processed_files_file = 'path/to/processed_files.txt'  # Replace with the path to store processed file names

def unzip_file(zip_path, extract_to):
    """Unzips a .zip file to the specified location."""
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_to)
    print(f"Unzipped: {zip_path} to {extract_to}")

def unrar_file(rar_path, extract_to):
    """Extracts a .rar file to the specified location."""
    with rarfile.RarFile(rar_path) as rar_ref:
        rar_ref.extractall(extract_to)
    print(f"Unrarred: {rar_path} to {extract_to}")

def load_processed_files():
    """Loads the list of processed files from the processed_files.txt."""
    if os.path.exists(processed_files_file):
        with open(processed_files_file, 'r') as f:
            return set(f.read().splitlines())
    return set()

def save_processed_files(processed_files):
    """Saves the processed files list to the processed_files.txt file."""
    with open(processed_files_file, 'w') as f:
        for file_name in processed_files:
            f.write(file_name + '\n')

def monitor_and_unzip():
    """Monitors the downloads folder and extracts any new .zip or .rar files."""
    processed_files = load_processed_files()
    while True:
        files = os.listdir(downloads_folder)
        for file_name in files:
            if (file_name.endswith(".zip") or file_name.endswith(".rar")) and file_name not in processed_files:
                file_path = os.path.join(downloads_folder, file_name)

                # Determine file type and extract accordingly
                if file_name.endswith(".zip"):
                    unzip_file(file_path, unzip_to_folder)
                elif file_name.endswith(".rar"):
                    unrar_file(file_path, unzip_to_folder)

                # Mark the file as processed
                processed_files.add(file_name)

                # Save the updated processed files list
                save_processed_files(processed_files)

        time.sleep(10)  # Wait for 10 seconds before checking again

if __name__ == "__main__":
    monitor_and_unzip()