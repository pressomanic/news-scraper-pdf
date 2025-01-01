import argparse
import logging
import os
import sys
import time
from io import BytesIO
from random import randrange

import dateparser
import nc_py_api
import pypdf
import requests
from dotenv import dotenv_values
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.select import Select
from thefuzz import fuzz


def perform_connection_page(driver, env):
    # Open BNF Login
    driver.get("https://bnf.idm.oclc.org/login?url=https://nouveau.europresse.com/access/ip/default.aspx?un=D000067U_1")
    username = driver.find_element(By.ID, "username")
    username.send_keys(env['BNF_LOGIN'])
    username = driver.find_element(By.ID, "password")
    username.send_keys(env['BNF_PASSWORD'])
    driver.find_element(By.XPATH, "/html/body/main/section[1]/section/form/input[1]").click()


def search_for_publication_page(driver, source_to_find):
    driver.get('https://nouveau-europresse-com.bnf.idm.oclc.org/webpages/Pdf/SearchForm.aspx')
    options_media = driver.find_element(By.ID, "lbSources").find_elements(By.XPATH, "//option")
    max_score = 0
    option_selected = options_media[0]
    for option in options_media:
        option_text = option.text.lower()
        ratio = fuzz.ratio(option_text, source_to_find)
        if ratio > max_score:
            logging.info("Found better score for \"{}\" with score {}.".format(option_text, ratio))
            max_score = ratio
            option_selected = option
    logging.info("Publication identified for \"{}\" from the given input \"{}\""
                 .format(option_selected.text, source_to_find))
    return option_selected


def merge_pdfs_from_memory(pdf_bytes_list):
    merger = pypdf.PdfWriter()
    for pdf_bytes in pdf_bytes_list:
        pdf_stream = BytesIO(pdf_bytes)
        merger.append(pdf_stream)
    output_stream = BytesIO()
    merger.write(output_stream)
    merger.close()
    return output_stream


def open_pop_up_of_publication(driver, option_selected):
    dropdown = Select(driver.find_element(By.ID, "lbSources"))
    dropdown.select_by_value(option_selected.get_attribute("value"))
    driver.find_element(By.ID, "btnSearch").click()


def switch_to_popup_and_left_iframe(driver):
    window_handle = driver.window_handles[1]
    driver.switch_to.window(window_handle)
    driver.switch_to.frame("ListDoc")


def get_publication_date(driver):
    date_text = driver.find_element(By.ID, "lblDate").text
    return dateparser.parse(date_text)


def get_pdf_links(driver, max_page):
    links = driver.find_element(By.ID, "listdoc").find_elements(By.XPATH, "//a")
    download_links = []
    for index, link in enumerate(links):
        download_links.append(link.get_attribute("href"))
        if max_page is not None and index == max_page - 1:
            break
    return download_links


def download_pdf_links(driver, links):
    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,'
                  'application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
        'Connection': 'keep-alive',
        'Referer': 'https://nouveau-europresse-com.bnf.idm.oclc.org/',
        'Sec-Fetch-Dest': 'frame',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-User': '?1',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/121.0.0.0'
                      'Safari/537.36',
        'sec-ch-ua': '"Not A(Brand";v="99", "Google Chrome";v="121", "Chromium";v="121"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"'
    }
    s = requests.session()
    s.headers.update(headers)
    for cookie in driver.get_cookies():
        c = {cookie['name']: cookie['value']}
        s.cookies.update(c)

    pdf_responses = []
    for index, download_link in enumerate(links):
        logging.info("Download page {}/{}.".format(index + 1, len(links)))
        time.sleep(randrange(10))
        pdf_responses.append(s.request("GET", download_link, headers=headers).content)

    return pdf_responses


def write_to_nextcloud(pdf_bytes, dest_path, dest_filename, env):
    nc = nc_py_api.Nextcloud(nextcloud_url=env["NEXTCLOUD_URL"], nc_auth_user=env["NEXTCLOUD_USER"],
                             nc_auth_pass=env["NEXTCLOUD_PASSWORD"])
    pdf_bytes.seek(0)
    nc.files.upload_stream("{}/{}".format(dest_path, dest_filename), pdf_bytes)


def write_on_local(pdf_bytes, dest_filename):
    with open(dest_filename, "wb") as output_file:
        pdf_bytes.seek(0)
        output_file.write(pdf_bytes.getvalue())


def is_valid_file(check_file):
    if not os.path.exists(check_file):
        raise argparse.ArgumentTypeError("{} does not exist".format(check_file))
    return check_file


def main():
    global_start_time = time.time()

    # Disable driver logs
    # os.environ['WDM_LOG'] = '0'

    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

    # Parse args
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=str,
                        help="Source of media to find latest publication.")
    parser.add_argument("-e", "--env", default=None, type=is_valid_file,
                        required=False, help="Specify the file env variables."
                                             "By default taking file referenced in os variable ENV_NEWS_SCRAPER. ")
    parser.add_argument("-f", "--first-pages", default=None, type=int, required=False,
                        help="Get the first N pages. Useful to test a newspaper before getting all pages.")
    parser.add_argument("-v", "--verbose", action="store_true", default=False, required=False,
                        help="Enable verbose mode.")
    parser.add_argument("-n", "--nextcloud-path", default=None, type=str, required=False,
                        help="Set Nextcloud upload directory path. Need to configure valid connection with --env")
    parser.add_argument("-o", "--output-path", default=None, type=str, required=False,
                        help="Write file to a specific path.")

    args = parser.parse_args()

    # Get variables from input
    source = args.source
    first_pages = args.first_pages
    nextcloud_upload_path = args.nextcloud_path
    env_values = args.env
    write_to_specific_path = args.output_path

    # Check input variables
    config = None
    if env_values is not None:
        config = dotenv_values(args.env)
    else:
        env_from_os = os.environ["ENV_NEWS_SCRAPER"]
        if env_from_os is None:
            logging.error("Can't parse env from os path. "
                          "Please consider to set ENV_NEWS_SCRAPER or use optioen --env.")
        if is_valid_file(env_from_os):
            config = dotenv_values(os.environ["ENV_NEWS_SCRAPER"])
            logging.error("Can't read file is os variable ENV_NEWS_SCRAPER.")
            sys.exit(1)

    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument('--log-level=3')
    # Force window size for the headless mode
    chrome_options.add_argument("--window-size=1920,1080")
    prefs = {
        "download_restrictions": 3,
        "download.default_directory": "/dev/null",
    }
    chrome_options.add_experimental_option(
        "prefs", prefs
    )
    browser_driver = webdriver.Chrome(options=chrome_options)

    # Open BNF Login
    start_time = time.time()
    perform_connection_page(browser_driver, config)
    time.sleep(2)
    logging.info("Connected to BNF in {} s.".format(time.strftime("%S", time.gmtime(time.time() -
                                                                                    start_time))))

    # Open media search page
    start_time = time.time()
    option_found = search_for_publication_page(browser_driver, source)
    time.sleep(2)
    logging.info("Search page for publication opened in {} s.".format(time.strftime("%S", time.gmtime(time.time() -
                                                                                                      start_time))))

    # Open popup of publication page
    start_time = time.time()
    open_pop_up_of_publication(browser_driver, option_found)
    time.sleep(2)
    logging.info("Search query done in {} s.".format(time.strftime("%S", time.gmtime(time.time() - start_time))))

    # Read data in popup windows
    start_time = time.time()
    switch_to_popup_and_left_iframe(browser_driver)
    time.sleep(2)
    logging.info("Switch to popup result in {} s.".format(time.strftime("%S", time.gmtime(time.time() - start_time))))

    # Get date of publication
    start_time = time.time()
    date_parsed = get_publication_date(browser_driver)
    logging.info("Publication date found in {} s.".format(time.strftime("%S", time.gmtime(time.time() - start_time))))

    # Get pdf links
    start_time = time.time()
    pdf_links = get_pdf_links(browser_driver, first_pages)
    logging.info("Get all download links  in {} s.".format(time.strftime("%S", time.gmtime(time.time() - start_time))))

    # Download pdf links
    start_time = time.time()
    pdf_files = download_pdf_links(browser_driver, pdf_links)
    logging.info("Links downloaded in {} s.".format(time.strftime("%S", time.gmtime(time.time() - start_time))))

    # Kill driver
    browser_driver.close()

    # Merge pdf files in one file
    logging.info("Merge pages into one pdf.")
    merged_pdf_bytes = merge_pdfs_from_memory(pdf_files)

    # Create filename
    filename = "{}-{}-{}.pdf".format(source, date_parsed.date().strftime('%Y-%m-%d'),
                                     date_parsed.date().strftime('%A'))
    # Write file
    default_write = True
    if nextcloud_upload_path is not None:
        default_write = False
        logging.info("Write into Nextcloud {}/{}".format(nextcloud_upload_path, filename))
        write_to_nextcloud(merged_pdf_bytes, nextcloud_upload_path, filename, config)

    if write_to_specific_path is not None:
        default_write = False
        logging.info("Write into specified directory {}".format(write_to_specific_path))
        write_on_local(merged_pdf_bytes, os.path.join(write_to_specific_path, filename))

    if default_write:
        logging.info("Write into current directory.")
        write_on_local(merged_pdf_bytes, filename)

    logging.info(
        "Script executed to get {} as {} for date of {} in {} s."
        .format(source, filename, date_parsed.date().strftime('%Y-%m-%d'),
                time.strftime("%S", time.gmtime(time.time() - global_start_time))))

    sys.exit(0)


if __name__ == '__main__':
    main()
