from selenium import webdriver
import re
import fake_useragent
import time
import google_api_test
from typing import Union, Optional, Iterator
from threading import Thread, Lock, currentThread, BoundedSemaphore
import sys
import logging

#Настройка логирования
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(stream=sys.stdout)
formatter = logging.Formatter(fmt='[%(asctime)s] %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
def get_info(msg):
    logger.info(str(msg))
threads: list[Thread] = []
sem = BoundedSemaphore(value=10)
lock = Lock()
latitudes: list[str] = ["Latitude"]
longitudes: list[str] = ["Longitude"]
cities: list[str] = ["City"]
addresses: list[str] = ['Address']
names: list[str] = ["Name"]
types: list[str] = ["Type"]
squares: list[Union[str, int]] = ["Square"]
guests_counts: list[Union[str, int]] = ["Guests_count"]
prices: list[Union[str, int]] = ['Price']
average_ratings: list[Union[str, float]] = ["Average_rating"]
reviews_counts: list[Union[str, int]] = ["Reviews_count"]

USER:fake_useragent.UserAgent = fake_useragent.UserAgent(verify_ssl=False).random
HEADERS: dict = {'user-agent': USER}
URL = 'https://sutochno.ru/front/searchapp/search/?guests_adults=1&id=1&type=country&term=Россия&SW.lat=41.1850968&SW.lng=19.6389&NE.lat=82.0586232&NE.lng=180#filter_on'
options = webdriver.ChromeOptions()
options.add_argument(f"user-agent={USER}")
options.add_argument("--disable-blink-features=AutomationControlled")

advanced_options = webdriver.ChromeOptions()
advanced_options.add_argument(f"user-agent={USER}")
advanced_options.add_argument("--disable-blink-features=AutomationControlled")
advanced_options.headless = True

def init_chromedriver(options) -> webdriver.Chrome:
    return webdriver.Chrome(executable_path='/Users/bulat/PycharmProjects/pythonProject2/sutochno_ru/chromedriver',
                            options=options)

def get_rid_of_garbage(bot: webdriver.Chrome) -> None:
    bot.find_element_by_xpath('/html/body/div/div[1]/div[2]/div[2]/div/div[1]/span').click()

def get_source_code(bot: webdriver.Chrome) -> str:
    return bot.page_source

def move_to_next_page(bot: webdriver.Chrome, idx:int) -> None:
    if idx == 0: idx = 2
    elif idx == 1: idx = 4
    elif idx == 2: idx = 5
    elif idx == 3: idx = 6
    else: idx = 7
    bot.find_element_by_xpath(f'//*[@id="app"]/div[1]/div[2]/div[4]/div[2]/ul/li[{idx}]').click()

def get_offers_url(bot: webdriver.Chrome) -> list[str]:
    urls: list[str] = []
    for element in bot.find_elements_by_class_name('card-content'):
        urls.append(
            element.get_attribute('href')
        )
    return urls

def parse_coord(url: str):
    with sem:
        get_info('cur_thr: ' + str(currentThread().getName()))
        lat = lon = None
        browser = init_chromedriver(advanced_options)
        try:
            browser.get(url)
            time.sleep(5)
            logger.info(browser.current_url)
            lat = re.search(r'lat=(\d+\.\d+)', browser.current_url).group(1)
            lon = re.search(r'lng=(\d+\.\d+)', browser.current_url).group(1)
            logger.info(lat + ' ' + lon)
        except Exception as ex:
            logger.exception(ex)
        finally:
            with lock:
                browser.close()
                latitudes.append(lat)
                longitudes.append(lon)

def is_clear(col: Iterator) -> bool:
    return not None in col

def combine_all_columns(*args):
    return [list(row) for row in zip(*args) if is_clear(row)]

def parse_prices(bot: webdriver.Chrome, block):
    #price
    try:
        element = block.find_element_by_class_name('price discount').find_elements_by_tag_name('span')
    except Exception as ex:
        element = block.find_element_by_class_name('price')
    for span in element.find_elements_by_tag_name('span'):
        if re.search(r'\d+', span.text):
            price = re.sub(r'\s|₽', '', span.text)
            return int(price)

def parse_offers(bot: webdriver.Chrome):
    price = address = name = type = square = guests_count = city = None
    average_rating = None
    reviews_count = None
    for block in bot.find_elements_by_class_name('card'):
        try:
            subblock = block.find_element_by_class_name('card-content__object-hotel')
            type:Optional[str] = subblock.text.strip()
            name:Optional[str] = block.find_element_by_tag_name\
                ('h2').text.strip()
            if type == '':
                type = name
            full_address = block.find_element_by_class_name('card-content__address').\
                find_element_by_tag_name('p').text
            full_address= re.split(r',\s*',full_address, maxsplit=1)
            city: Optional[str] = full_address[0]
            city = 'Санкт-Петербург' if city == 'СПб' else city
            address: Optional[str] = full_address[1]
            guests_count: Optional[int] = int(re.search(r'\d+', block.find_element_by_class_name('facilities__main')
                    .find_elements_by_tag_name('p')[0].text).group())
            square: Optional[int] = int(re.search(r'\d+(?=\s*м²)',
                                        block.find_element_by_class_name('facilities__size')
                                        .find_element_by_tag_name('span').text).group())
            price: Optional[int] = parse_prices(bot, block)
            rating_block = block.find_element_by_class_name("card-prices").find_elements_by_tag_name('span')
            try:
                for canditate in rating_block:
                    if re.search(r'\d{1,2},\d',canditate.text) is not None:
                        average_rating = float(canditate.text.replace(',', '.'))
                    if re.search(r'\(\d+\)', canditate.text) is not None:
                        reviews_count = int(re.sub(r'[()]','',canditate.text))
            except Exception as ex:
                 logger.exception(ex)
                 average_rating = 8.0
                 reviews_count = 0
            get_info("price: " + str(price))
            get_info("address: " + address)
            get_info("average_rating: " + str(average_rating))
            get_info("name: " + name)
            get_info('type: ' + type)
            get_info('square: ' + str(square))
            get_info('guests_count: ' + str(guests_count))
            get_info('reviews_count: ' + str(reviews_count))
        except Exception as ex:
            logger.exception(ex)
        finally:
            cities.append(city)
            prices.append(price)
            addresses.append(address)
            names.append(name)
            types.append(type)
            average_ratings.append(average_rating)
            guests_counts.append(guests_count)
            reviews_counts.append(reviews_count)
            squares.append(square)

def main() -> None:
    bot = init_chromedriver(options)
    bot.get(URL)
    for index in range(30):
        try:
            if index == 0:
                get_rid_of_garbage(bot)
            time.sleep(5)
            offers_list: list[str] = get_offers_url(bot)
            for offer in offers_list:
                threads.append(Thread(target=parse_coord, args=(offer, )))
                threads[-1].start()
            for item in threads:
                item.join()
            parse_offers(bot)
            move_to_next_page(bot, index)
        except Exception as ex:
            logger.exception(ex)
            print(combine_all_columns(latitudes, longitudes, cities, addresses, prices, squares, names, types, guests_counts, average_ratings, reviews_counts))
            #google_api_test.execute_google_api_sheets(combine_all_columns(latitudes, longitudes, cities, addresses, prices, squares, names, types, guests_counts, average_ratings, reviews_counts))
            bot.close()
            break
    else:
        print(combine_all_columns(latitudes, longitudes, cities, addresses, prices, squares, names, types, guests_counts, average_ratings, reviews_counts))
        #google_api_test.execute_google_api_sheets(combine_all_columns(latitudes, longitudes, cities, addresses, prices, squares, names, types, guests_counts, average_ratings, reviews_counts))

if __name__ == '__main__':
    main()

