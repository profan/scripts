import os
import csv
import datetime
import subprocess
import argparse
import shutil
import re

# our utils
import util
path_to_fetch_cmd = shutil.which("svr_retrieve_RAST_job")
fetch_proteins_cmd = " %s %s %s table_txt > %s"
absolute_cmd_path = path_to_fetch_cmd + fetch_proteins_cmd

parser = argparse.ArgumentParser(description='Batch download protein data for all submitted jobs')
parser.add_argument(
    '--username', metavar='username', type=str, required=True,
    help='your login username'
)
parser.add_argument(
    '--password', metavar='password', type=str, required=True,
    help='your login password'
)
parser.add_argument(
    '--filename', type=str, required=True,
    help='the path to the csv with the submitted jobs to fetch protein data for'
)
parser.add_argument(
    '--directory', type=str, required=True,
    help='the directory to place the output data into'
)
parser.add_argument(
    '--output-type', type=str, default='table_txt',
    help='the output type to fetch the jobs for'
)

def ext_for_output_type(t):
    if t == "table_txt":
        return "tsv"
    elif t == "gff3":
        return "gff"
    else:
        raise Exception("no matching extension for given output type: %s" % t)

def retrieve_proteins_for_all_jobs(username, password, all_job_ids, all_job_names, output_directory, output_type):
    total_jobs = len(all_job_ids)
    print("[batch - proteins] total jobs to fetch: %d at %s" % (total_jobs, datetime.datetime.now()))
    total_successful_jobs = 0
    total_failed_jobs = 0
    for (job_id, job_name) in zip(all_job_ids, all_job_names):
        try:
            print("[batch - proteins] trying to fetch: %s at %s" % (job_id, datetime.datetime.now()))
            target_ext = ext_for_output_type(output_type)
            target_filename = os.path.join(args.directory, "%s_rast_proteins.%s" % (job_name, target_ext))
            arguments = (args.username, args.password, job_id, target_filename)
            output = subprocess.getoutput(absolute_cmd_path % arguments)
            if not os.path.exists(target_filename):
                raise Error('[batch - protens] expected output file %s to exist? job probably failed' % target_filename)
            total_successful_jobs += 1
        except:
            total_failed_jobs += 1
            print("[batch - proteins] failed to fetch: %s at %s" % (job_id, datetime.datetime.now()))

args = parser.parse_args()
util.create_output_directory_if_not_exists(os.getcwd())

all_job_ids = util.collect_job_ids_from_csv(args.filename)
all_job_names = [util.original_file_name_from_job_id(args.filename, job_id) for job_id in all_job_ids]
retrieve_proteins_for_all_jobs(args.username, args.password, all_job_ids, all_job_names, args.directory, args.output_type)
