from rich.progress import track
from time import sleep
import argparse
import os

from selenium import webdriver
from selenium.webdriver.remote.webdriver import WebDriver

from selenium.webdriver.common.by import By
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.firefox.options import Options

# our utils
import util

base_url = "https://cge.cbs.dtu.dk/services/ResFinder-4.1/"
job_url = "https://cge.cbs.dtu.dk//cgi-bin/webface.fcgi"

def job_url_with_job_id(job_id: str) -> str:
    return f"{job_url}?jobid={job_id}"

def navigate_to_resfinder_job_page(driver: WebDriver, job_id: str):
    driver.get(job_url_with_job_id(job_id))

def download_phenotype_table(driver: WebDriver, directory: str, sample_id: str):

    # find button to download the phenotype table
    all_input_elements = driver.find_elements(by=By.TAG_NAME, value="input")
    download_phenotype_button = [e for e in all_input_elements if e.get_attribute("value") == "Download phenotype table (txt)"][0]
    download_phenotype_button.submit()

    sleep(1.0)

    phenotype_table_name = f"{sample_id}_phenotypes.tsv"
    util.rename_most_recent_file_in_dir(directory, extension=".txt", expected_part_of_name="pheno_table", new_name=phenotype_table_name)

parser = argparse.ArgumentParser(description='Batch fetch results for a number of submitted ResFinder jobs, given a csv file of submitted jobs.')
parser.add_argument(
    '-f', '--file-path', metavar='file_path', type=str, required=True,
    help='the path to the file with the jobs submitted where job ids can be found to fetch the results.'
)
parser.add_argument(
    '--output-dir', metavar='output_dir', type=str, default=os.getcwd(),
    help='output directory where downloaded files go'
)

args = parser.parse_args()

# else we'll be loading forever due to google analytics shite
capabilities = DesiredCapabilities().FIREFOX
capabilities["pageLoadStrategy"] = "eager"

# save file shite
profile = webdriver.FirefoxProfile()
profile.set_preference("browser.download.dir", os.path.join(os.getcwd(), args.output_dir))
profile.set_preference("browser.download.folderList", 2)
profile.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/x-download")
profile.set_preference("browser.download.manager.showWhenStarting", False)
profile.set_preference("browser.download.panel.shown", False)

options = Options()
options.headless = True

driver = webdriver.Firefox(desired_capabilities=capabilities, firefox_profile=profile, options=options)

all_job_ids_to_fetch = util.collect_job_ids_from_csv(args.file_path)
print("[fetch_resfinder_results] got %d job ids to fetch results for" % len(all_job_ids_to_fetch))
current_output_timestamp = util.get_current_timestamp()

for i, job_id in track(enumerate(all_job_ids_to_fetch), total=len(all_job_ids_to_fetch)):

    try:

        # absolute_file_path = os.path.normpath(os.path.join(os.getcwd(), file_path))
        original_file_name = util.original_file_name_from_job_id(args.file_path, job_id)
        file_path, file_name = os.path.split(original_file_name)
        sample_id, _ = os.path.splitext(file_name)

        navigate_to_resfinder_job_page(driver, job_id)
        download_phenotype_table(driver, args.output_dir, sample_id)
        
        print(f"[fasta_submit_resfinder] fetched: {file_name}, with job id: {job_id}")

    except Exception as err:

        print(f"[fasta_submit_resfinder] failed to fetch: {file_name} with job id: {job_id}, skipping")

driver.quit()
