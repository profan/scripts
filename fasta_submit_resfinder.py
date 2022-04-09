from typing import Optional, cast

from rich.progress import track
import argparse
import glob
import csv
import os

from selenium import webdriver

from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.remote.webdriver import WebDriver

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import Select

# our utils
import util

base_url = "https://cge.cbs.dtu.dk/services/ResFinder-4.1/"

def navigate_to_resfinder_page(driver: WebDriver):

    driver.get(base_url)

def select_options_for_submission(driver: WebDriver, species_value: str):

    chromosomal_point_mutations_checkbox = driver.find_element(by=By.ID, value="supplied")
    chromosomal_point_mutations_checkbox.click()

    acquired_antimicrobial_resistance_checkbox = driver.find_element(by=By.ID, value="supplied2")
    acquired_antimicrobial_resistance_checkbox.click()

    species_dropdown = Select(driver.find_element(by=By.ID, value="species"))
    species_dropdown.select_by_value(species_value)

def choose_and_upload_file(driver: WebDriver, file_path: str):

    WebDriverWait(driver, timeout=10).until(EC.frame_to_be_available_and_switch_to_it((By.ID, "myIframe")))
    all_input_elements = driver.find_elements(by=By.TAG_NAME, value="input")
    assert len(all_input_elements) == 1

    file_chooser = all_input_elements[0]
    file_chooser.send_keys(file_path)

    submit_btn = driver.find_element(by=By.CLASS_NAME, value="btn-success")
    submit_btn.click()

    # back to default context
    driver.switch_to.default_content()

def wait_for_and_extract_submitted_job_id(driver: WebDriver) -> str:

    WebDriverWait(driver, 10).until(EC.url_contains("jobid"))
    current_url_with_job_id = driver.current_url

    job_id_idx = current_url_with_job_id.find("jobid=")
    uploaded_job_id = current_url_with_job_id[job_id_idx + len("jobid="):].replace(";wait=", "")

    return uploaded_job_id

def submit_email_for_notification(driver: WebDriver, email: str):

    email_input_element = [e for e in driver.find_elements(by=By.TAG_NAME, value="input") if e.is_displayed()][0]
    email_input_element.send_keys(email)
    email_input_element.submit()

parser = argparse.ArgumentParser(description='Submits all fasta files in given folder to ResFinder.')
parser.add_argument(
    '--dirname', metavar='dirname', type=str, required=True,
    help='the path to the folder with fasta files in it to submit to ResFinder'
)
parser.add_argument(
    '--species', metavar='species', type=str, required=True,
    help='the species to select from the species dropdown'
)
parser.add_argument(
    '--email', metavar='email', type=str, required=True,
    help='the email to send the job completion email to'
)
parser.add_argument(
    '--output-dir', metavar='output_dir', type=str, default=os.getcwd(),
    help='output directory where downloaded files go'
)

args = parser.parse_args()

# else we'll be loading forever due to google analytics shite
capabilities = DesiredCapabilities().FIREFOX
# capabilities["pageLoadStrategy"] = "eager"

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

all_fasta_files_to_submit = util.get_files_in_folder_with_ext(args.dirname, ".fa")
print("[fasta_submit_resfinder] got %d fasta files to submit" % len(all_fasta_files_to_submit))

def rename_most_recent_table_in_dir(directory, new_name):
    files = glob.glob(directory + "/*.tsv")
    most_recent_file = max(files, key=os.path.getctime)
    if "table" in most_recent_file:
        path, base = os.path.split(most_recent_file)
        os.rename(most_recent_file, os.path.join(path, new_name))
        return True
    return False

def write_job_id_to_file(output_timestamp, job_id, file_name, success):
    output_filename = f"output/submitted_resfinder_jobs_{output_timestamp}.csv"
    if not os.path.exists(output_filename):
        print(f"[fasta_submit_resfinder] writing id: {job_id} to new file: {output_filename}")
        with open(output_filename, 'w') as csvfile:
            our_writer = csv.writer(csvfile)
            our_writer.writerow(['job_id', 'file_name', 'success'])
            our_writer.writerow([job_id, file_name, success])
    else:
        print(f"[fasta_submit_resfinder] writing id: {job_id} to existing file: {output_filename}")
        with open(output_filename, 'a') as csvfile:
            our_writer = csv.writer(csvfile)
            our_writer.writerow([job_id, file_name, success])

current_output_timestamp = util.get_current_timestamp()

for i, file_path in track(enumerate(all_fasta_files_to_submit), total=len(all_fasta_files_to_submit)):

    try:

        absolute_file_path = os.path.normpath(os.path.join(os.getcwd(), file_path))

        navigate_to_resfinder_page(driver)
        select_options_for_submission(driver, args.species)
        choose_and_upload_file(driver, absolute_file_path)
        uploaded_job_id = wait_for_and_extract_submitted_job_id(driver)
        submit_email_for_notification(driver, args.email)
        
        print(f"[fasta_submit_resfinder] submitted: {file_path}, with job id: {uploaded_job_id}")
        write_job_id_to_file(current_output_timestamp, uploaded_job_id, file_path, True)

    except Exception as err:

        print(f"[fasta_submit_resfinder] failed to submit: {file_path}, skipping")
        write_job_id_to_file(current_output_timestamp, -1, file_path, False)

driver.quit()
