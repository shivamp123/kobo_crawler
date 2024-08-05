# Kobo Scraper

This project is designed to scrape book information from the Kobo website and store it in a MongoDB database. It uses Selenium for web scraping, Scrapy for parsing HTML responses, and MongoDB for data storage.

## Prerequisites

Ensure you have the following installed on your system:

- Python 3.x
- MongoDB
- Google Chrome
- ChromeDriver

## Installation

1. **Clone the repository:**

    ```sh
    git clone https://github.com/yourusername/kobo-scraper.git
    cd kobo-scraper
    ```

2. **Install the required Python libraries:**

    ```sh
    pip install pymongo selenium scrapy random-user-agent fake_useragent pandas
    ```

3. **Download ChromeDriver:**

    - Download the ChromeDriver that matches your version of Chrome from [here](https://sites.google.com/a/chromium.org/chromedriver/downloads).
    - Place the ChromeDriver executable in a known location and update the `CHROMEDRIVER_PATH` in the script with this location.

## Configuration

- Ensure MongoDB is installed and running on your local machine or a server.
- Update the MongoDB connection string in the script if necessary: `"mongodb://localhost:27017/"`.

## Usage

### Script Workflow

The script is divided into two main functions:

1. **get_response**: Scrapes data from the Kobo website.
2. **get_output**: Processes and stores the scraped data into MongoDB.

### Running the Script

1. **Scraping Data:**

    Set the `flag` variable to `0` to scrape data from the Kobo website.

    ```python
    flag = 0
    if flag == 0:
        get_response("https://www.kobo.com/us/en")
    ```

    Run the script using a Python interpreter:

    ```sh
    python script_name.py
    ```

2. **Processing and Storing Data:**

    Set the `flag` variable to `1` to process and store the scraped data into MongoDB.

    ```python
    flag = 1
    if flag == 1:
        get_output()
    ```

    Run the script using a Python interpreter:

    ```sh
    python script_name.py
    ```

## Code Overview

1. Using "input_function" selenium download the all pages (if there are any changes we can read the page and get the data no need to run everytime).
2. using "get_output" function read the all pages and save all data on database.
