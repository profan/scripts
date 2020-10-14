import os
import csv
import requests
import datetime
import argparse
import webbrowser
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

# our utils
import util

base_url = "https://rast.nmpdr.org/"
login_url = "https://rast.nmpdr.org/rast.cgi"
download_url = "https://rast.nmpdr.org/download.cgi"
job_page_url = "https://rast.nmpdr.org/rast.cgi?page=JobDetails&job=%s"

login_headers = {
    'User-Agent': 'Mozilla/5.0'
}

def login_to_rast_selenium(driver, username, password):
    driver.get(login_url)
    userfield = driver.find_element_by_name("login")
    passfield = driver.find_element_by_name("password")
    submit = driver.find_element_by_xpath("//input[@title='Click here to login!']")
    userfield.send_keys(username)
    passfield.send_keys(password)
    submit.click()

def extract_genome_url_for_job_id(driver, job_id):
    driver.get(job_page_url % job_id)
    soup = BeautifulSoup(driver.page_source, "lxml")
    e = soup.find('a', string="Browse annotated genome in SEED Viewer")
    return base_url + "/" + e['href']

def extract_subsystem_data(driver, url):
    driver.get(url) # first go to the right page
    are_we_ready = False
    while not are_we_ready:
        tab_button = driver.find_element_by_xpath("//td[text()='Features in Subsystems']")
        tab_button.click()
        export_button = driver.find_element_by_xpath("//input[@value='export to file']")
        if export_button.is_displayed():
            are_we_ready = True
    export_button.click()

parser = argparse.ArgumentParser(description='Fetches all feature subsystem data for a given job.')
parser.add_argument(
    '--username', metavar='username', type=str, required=True,
    help='your login username'
)
parser.add_argument(
    '--password', metavar='password', type=str, required=True,
    help='your login password'
)
parser.add_argument(
    '--filename', metavar='filename', type=str, required=True,
    help='csv with submitted jobs'
)
parser.add_argument(
    '--output-dir', metavar='output_dir', type=str, default=os.getcwd(),
    help='csv with submitted jobs'
)

args = parser.parse_args()

# else we'll be loading forever due to google analytics shite
capabilities = DesiredCapabilities().FIREFOX
capabilities["pageLoadStrategy"] = "eager"

# save file shite
profile = webdriver.FirefoxProfile()
profile.set_preference("browser.download.dir", args.output_dir);
profile.set_preference("browser.download.folderList", 2);
profile.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/x-download")
profile.set_preference("browser.download.manager.showWhenStarting", False)
profile.set_preference("browser.download.panel.shown", False)

driver = webdriver.Firefox(desired_capabilities=capabilities, firefox_profile=profile)
login_to_rast_selenium(driver, args.username, args.password)

all_job_ids = util.collect_job_ids_from_csv(args.filename)
print("[fetch_subsystems] got %d job ids to fetch" % len(all_job_ids))

for i, job_id in enumerate(all_job_ids):
    genome_url = extract_genome_url_for_job_id(driver, job_id)
    extract_subsystem_data(driver, genome_url)
    print("[fetch_subsystems] downloaded table for %d of %d" % (i + 1, len(all_job_ids)))

driver.quit()
