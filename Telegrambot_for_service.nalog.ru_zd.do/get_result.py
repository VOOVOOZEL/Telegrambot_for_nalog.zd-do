import os
import glob
import random
import string
import time
import requests
import solve_captchas_for_nalog
from PIL import Image
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException

DRIVER = "chromedriver"
CAPTCHA_IMAGE_FOLDER = "generated_captcha_images"
VOWELS = "aeiou"
CONSONANTS = "".join(set(string.ascii_lowercase) - set(VOWELS))

# Generate name of file
def generate_word(length, fmt):
    word = ""
    for i in range(length):
        if i % 2 == 0:
            word += random.choice(CONSONANTS)
        else:
            word += random.choice(VOWELS)
    return word + fmt


def download_picture(CAPTCHA_IMAGE_FOLDER, s, image):

    for i in range(50):
        picture_request = s.get(image)

        image_name = generate_word(6, '.jpg')

        path = os.path.join(CAPTCHA_IMAGE_FOLDER, image_name)

        if picture_request.ok:
            with open(path, 'wb') as f:
                f.write(picture_request.content)

            im = Image.open(path)
            rgb_im = im.convert('RGB')
            rgb_im.save(path)
        else:
            print(picture_request.raise_for_status)


def request(driver):
    s = requests.Session()
    cookies = driver.get_cookies()
    for cookie in cookies:
        s.cookies.set(cookie['name'], cookie['value'])
    return s


def input_data(driver, captcha, inn):
    driver.find_element_by_xpath('//*[@id="inn"]').clear()
    for i in inn:
        driver.find_element_by_xpath('//*[@id="inn"]').send_keys(i)
    driver.find_element_by_xpath('//*[@id="captcha"]').clear()
    for j in captcha:
        driver.find_element_by_xpath('//*[@id="captcha"]').send_keys(j)
    driver.find_element_by_xpath('//*[@id="btn_send"]').click()
    time.sleep(1)
    result_msg = driver.find_element_by_xpath('//*[@id="resultData"]').text

    try:
        result_msg = driver.find_element_by_xpath('//*[@id="errors_inn"]/li/label').text
    except NoSuchElementException:
        pass

    try:
        captcha_err = driver.find_element_by_xpath('//*[@id="errors_captcha"]/li/label').text
    except NoSuchElementException:
        captcha_err = ''

    return result_msg, captcha_err


def get_result_from_site(inn):
    if not inn:
        result_msg = 'Введите ИНН'
        return result_msg
    page = 'https://service.nalog.ru/zd.do'
    driver = webdriver.Chrome('/home/evgeny/Python projects/solving_captchas_code/chromedriver')
    driver.get(page)
    driver.maximize_window()
    driver.execute_script('window.scrollTo(0, 300);')

    s = request(driver)

    image = driver.find_elements_by_tag_name('img')[0].get_attribute('src')
    download_picture(CAPTCHA_IMAGE_FOLDER, s, image)

    captcha = solve_captchas_for_nalog.solve()

    result_msg, captcha_err = input_data(driver, captcha, inn)

    captcha_image_files = glob.glob(os.path.join(CAPTCHA_IMAGE_FOLDER, "*"))
    for file in captcha_image_files:
        os.remove(file)

    if captcha_err:
        result_msg, captcha_err = input_data(driver, captcha, inn)

    driver.quit()
    return result_msg


if __name__ == '__main__':
    print(get_result_from_site('7736050003'))