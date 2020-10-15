import os
import csv
import xlrd

# reused functions
def csv_from_excel(src_path, target_path):
    wb = xlrd.open_workbook(src_path)
    sh = wb.sheet_by_name('Sheet1') # WHAT THE FUCK
    with open(target_path, 'w') as csv_file:
        wr = csv.writer(csv_file, quoting=csv.QUOTE_ALL)
        for rownum in xrange(sh.nrows):
            wr.writerow(sh.row_values(rownum))

def collect_job_ids_from_csv(job_csv_file_path):
    job_ids = []
    with open(job_csv_file_path, 'r') as csvfile:
        reader = csv.DictReader(csvfile) # fieldnames=['job_id', 'file_name', 'success']
        for row in reader:
            if row['success'] == 'True':
                job_ids.append(row['job_id'])
    return job_ids

def create_output_directory_if_not_exists(cwd):
    output_dir_path = os.path.join(cwd, 'output')
    if os.path.exists(output_dir_path) and os.path.isfile(output_dir_path):
        raise Exception("output exists but is a file, expected output to be a directory!")
    elif not os.path.exists(output_dir_path):
        os.mkdir(output_dir_path)

def get_files_in_folder_with_ext(directory, extension):
    paths = []
    for entry in os.listdir(directory):
        name, ext = os.path.splitext(entry)
        full_path = os.path.join(directory, entry)
        if os.path.isfile(full_path) and ext == extension:
            paths.append(full_path)
    return paths

