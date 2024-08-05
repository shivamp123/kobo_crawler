import json
import pymongo
import time
import pandas as pd
from selenium import webdriver
from scrapy.http import HtmlResponse
from random_user_agent.user_agent import UserAgent
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from random_user_agent.params import SoftwareName, OperatingSystem

# MongoDB connection
myclient = pymongo.MongoClient("mongodb://localhost:27017/")
mydb = myclient["kobo"]
input_db = mydb['kobo_input1']
output_db = mydb['kobo_output']


def get_useragent():
    software_names = [SoftwareName.CHROME.value]
    operating_systems = [OperatingSystem.WINDOWS.value, OperatingSystem.LINUX.value]
    user_agent_rotator = UserAgent(software_names=software_names, operating_systems=operating_systems, limit=1000)
    return user_agent_rotator.get_random_user_agent()

# function for page save
def read_html(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

# input function for getting HTMl page using selenium
def input_function(url):
    try:
        options = Options()
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-setuid-sandbox')
        options.add_argument('--disable-cache')
        options.add_argument('--disable-infobars')
        options.add_argument('--disable-impl-side-painting')
        options.add_argument('--disable-notifications')
        options.add_argument('--disable-plugins-discovery')
        options.add_argument('--disable-popup-blocking')
        options.add_argument('--disable-translate')
        options.add_argument('--disable-web-security')
        options.add_argument('--disable-fill-on-account-select')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--enable-multiprocess')
        options.add_argument('--enable-smooth-scrolling')
        options.add_argument('--ignore-certificate-errors')
        options.add_argument('--fast-start')
        options.add_argument('--mute-audio')
        options.add_argument(get_useragent())
        options.add_argument('window-size=1920,1080')
        options.add_experimental_option("debuggerAddress", "127.0.0.1:9028")

        CHROMEDRIVER_PATH = r"D:\\chromedriver.exe"
        datas = input_db.find({"dflag": 0})[0:500]

        for data in datas:
            isbn = data['isbn13']
            service = Service(executable_path=CHROMEDRIVER_PATH)
            with webdriver.Chrome(options=options, service=service) as driver:
                driver.get(url)

                # Simulate scrolling to ensure elements are loaded
                driver.execute_script("window.scrollBy(0, 1500);")
                time.sleep(1)

                # Interact with the search bar and search button
                search_bar = driver.find_element(By.XPATH, '//*[@id="sl"]')
                search_bar.send_keys(isbn)
                search_button = driver.find_element(By.XPATH,
                                                    '//*[@id="header-search-input"]/div/div/div/form/div/div/input[2]')
                search_button.click()

                driver.execute_script("window.scrollBy(0, 1500);")
                time.sleep(1)

                # Get the page source and create a response object
                page_source = driver.page_source
                response = HtmlResponse(url=url, body=bytes(page_source.encode('utf8')))

                # Check for results and save the page if found
                if "did not return any results" not in response.text:
                    url1 = response.xpath('//*[@rel="canonical"]/@href').get()
                    file_path = f"D:\\kobo\\{isbn}.html"
                    with open(file_path, 'w', encoding='utf-8') as file:
                        file.write(page_source)

                    print(f"Page saved to {file_path}")
                    input_db.update_one({"_id": data['_id']},
                                        {"$set": {"dflag": 1, "url": url1, 'html_path': file_path}}, upsert=True)
                else:
                    input_db.update_one({"_id": data['_id']}, {"$set": {"dflag": 2}}, upsert=True)

    except Exception as e:
        print(f"Error in get_response: {e}")


# output function for getting the main data
def get_output():
    datas = input_db.find({"dflag": 1})
    for data in datas:
        try:
            item = {}
            html_path = data['html_path']
            html_data = read_html(html_path)
            response = HtmlResponse(url="url", body=bytes(html_data.encode('utf8')))

            price_json1 = json.loads(
                response.xpath('//*[@id="ratings-widget-details-wrapper"]/@data-kobo-gizmo-config').get(default=""))
            data_json = json.loads(price_json1['googleBook'])

            item['main_url'] = response.xpath('//*[@rel="canonical"]/@href').get()
            item['region'] = "US"
            item['retailer'] = "Kobo US"
            item['isbn13'] = data['isbn13']
            item['title_name'] = data_json['name']
            item['authors'] = response.xpath('//*[@class="contributor-name"]/text()').get(default="").strip()
            item['synopsis'] = " ".join(
                [text.strip() for text in response.xpath('//*[@class="synopsis-description"]//text()').extract() if
                 text.strip()])

            item['price'] = data_json['workExample']['potentialAction']['expectsAcceptanceOf']['price']
            item['priceCurrency'] = data_json['workExample']['potentialAction']['expectsAcceptanceOf']['priceCurrency']
            item['pages'] = response.xpath(
                '//*[@class="stat-img pages-img"]/../..//*[@class="stat-desc"]/strong/text()').get(default="")
            item['hours_to_read'] = response.xpath(
                '//*[@class="stat-img hours-img"]/../..//*[@class="stat-desc"]/strong/text()').get(default="")
            item['total_words'] = response.xpath(
                '//*[@class="stat-img words-img"]/../..//*[@class="stat-desc"]/strong/text()').get(default="")

            try:
                item['brand'] = data_json['publisher']['name']
                item['release_date'] = response.xpath(
                    '//*[@class="bookitem-secondary-metadata"]/ul/li[2]/span/text()').get()
                item['imprint'] = response.xpath('//*[@class="description-anchor"]//text()').get()
                item['ISBN'] = data_json['workExample']['isbn']
                item['language'] = response.xpath(
                    '//*[@class="bookitem-secondary-metadata"]/ul/li[5]/span//text()').get()
                item['download_options'] = response.xpath(
                    '//*[@class="bookitem-secondary-metadata"]/ul/li[6]//text()').get()
            except Exception as e:
                print(f"Error in ebook details section: {e}, URL: {item.get('main_url')}")

            try:
                item['bestRating'] = data_json['aggregateRating']['bestRating']
                item['ratingValue'] = data_json['aggregateRating']['ratingValue']
                item['reviewCount'] = data_json['aggregateRating']['reviewCount']
                item['ratingCount'] = data_json['aggregateRating']['ratingCount']
            except KeyError:
                item['bestRating'] = ""
                item['ratingValue'] = ""
                item['reviewCount'] = ""
                item['ratingCount'] = ""

            print(json.dumps(item, indent=4))
            output_db.insert_one(item)
            input_db.update_one({"_id": data['_id']}, {"$set": {"dflag": 5}}, upsert=False)
        except Exception as e:
            print(f"Error in get_output: {e}")


# Set flag to control execution
flag = 0
if flag == 0:
    input_function("https://www.kobo.com/us/en")
elif flag == 1:
    get_output()
