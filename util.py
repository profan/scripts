from typing import List

import os
import csv
import datetime
import glob

def original_file_name_from_job_id(job_csv_file_path, job_id):
    with open(job_csv_file_path, 'r') as csvfile:
        reader = csv.DictReader(csvfile) # fieldnames=['job_id', 'file_name', 'success']
        for row in reader:
            if row['job_id'] == job_id:
                base, name_and_ext = os.path.split(row['file_name'])
                name, ext = os.path.splitext(name_and_ext)
                return name

def collect_job_ids_from_csv(job_csv_file_path: str) -> List[str]:
    job_ids = []
    with open(job_csv_file_path, 'r') as csvfile:
        reader = csv.DictReader(csvfile) # fieldnames=['job_id', 'file_name', 'success']
        for row in reader:
            if row['success'] == 'True':
                job_ids.append(row['job_id'])
    return job_ids

def create_output_directory_if_not_exists(cwd: str):
    output_dir_path = os.path.join(cwd, 'output')
    if os.path.exists(output_dir_path) and os.path.isfile(output_dir_path):
        raise Exception("output exists but is a file, expected output to be a directory!")
    elif not os.path.exists(output_dir_path):
        os.mkdir(output_dir_path)

def get_files_in_folder_with_ext(directory: str, extension: str) -> List[str]:
    paths = []
    for entry in os.listdir(directory):
        name, ext = os.path.splitext(entry)
        full_path = os.path.join(directory, entry)
        if os.path.isfile(full_path) and ext == extension:
            paths.append(full_path)
    return paths

def get_current_timestamp() -> str:
    return datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc).strftime('%Y-%m-%dT%H_%M_%SZ')

def filter_for_files(path: str, ext: str, pattern: str) -> List[str]:
    matched_files = get_files_in_folder_with_ext(path, ext)
    return [f for f in matched_files if pattern in f]

def rename_most_recent_file_in_dir(directory: str, extension: str, expected_part_of_name: str, new_name: str):
    files = glob.glob(directory + "/*" + extension)
    most_recent_file = max(files, key=os.path.getctime)
    if expected_part_of_name in most_recent_file:
        path, base = os.path.split(most_recent_file)
        os.rename(most_recent_file, os.path.join(path, new_name))
        return True
    return False