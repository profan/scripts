import os
import csv
import datetime
import subprocess
import argparse
import shutil
import re

# our utils
import util

# Klebsiella pneumoniae
# https://www.uniprot.org/taxonomy/573

path_to_submit_fasta_cmd = shutil.which("svr_submit_RAST_job")
submit_fasta_job_cmd = " --taxon_ID 573 --determine_family --user %s --passwd %s --fasta %s"
absolute_cmd_path = path_to_submit_fasta_cmd + submit_fasta_job_cmd
fasta_job_output_regex = re.compile(r"'(\d+)'")

parser = argparse.ArgumentParser(description='Batch upload a directory of fasta files.')
parser.add_argument(
    '--username', metavar='username', type=str, required=True,
    help='your login username'
)
parser.add_argument(
    '--password', metavar='password', type=str, required=True,
    help='your login password'
)
parser.add_argument(
    'directory', type=str, default=os.getcwd(), nargs="?",
    help='the directory with the fasta (.fa) files in it to upload'
)

def write_job_id_to_file(job_id, file_name, success):
    output_timestamp = util.get_current_timestamp()
    output_filename = f"output/submitted_jobs_{output_timestamp}.csv"
    if not os.path.exists(output_filename):
        print(f"[batch] writing id: {job_id} to new file: {output_filename}")
        with open(output_filename, 'w') as csvfile:
            our_writer = csv.writer(csvfile)
            our_writer.writerow(['job_id', 'file_name', 'success'])
            our_writer.writerow([job_id, file_name, success])
    else:
        print(f"[batch] writing id: {job_id} to existing file: {output_filename}")
        with open(output_filename, 'a') as csvfile:
            our_writer = csv.writer(csvfile)
            our_writer.writerow([job_id, file_name, success])

def submit_fasta_files_in_dir(username, password, directory):
    all_job_paths = util.get_files_in_folder_with_ext(directory, ".fa")
    total_jobs_in_folder = len(all_job_paths)
    print("[batch] total jobs to submit: %d at: %s" % (total_jobs_in_folder, datetime.datetime.now()))
    total_successful_jobs = 0
    total_failed_jobs = 0
    for entry in all_job_paths:
        try:
            print("[batch] trying to submit: %s at %s" % (entry, datetime.datetime.now()))
            output = subprocess.getoutput(absolute_cmd_path % (args.username, args.password, entry))
            our_match = fasta_job_output_regex.search(output)
            submitted_job_id = our_match.group(1)
            write_job_id_to_file(submitted_job_id, entry, success = True)
            total_successful_jobs += 1
        except:
            total_failed_jobs += 1
            print("[batch] failed to submit: %s at %s" % (entry, datetime.datetime.now()))
            write_job_id_to_file(-1, entry, success = False)
    print("[batch] total successful jobs: %d" % total_successful_jobs)
    print("[batch] total failed jobs: %d" % total_failed_jobs)
    print("[batch] finished at %s" % datetime.datetime.now())

args = parser.parse_args()
util.create_output_directory_if_not_exists(os.getcwd())
submit_fasta_files_in_dir(args.username, args.password, args.directory)
