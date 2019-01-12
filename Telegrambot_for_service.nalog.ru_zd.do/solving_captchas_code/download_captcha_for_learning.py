import os
import re
import random
import string
import time
import requests

from PIL import Image


CAPTCHA_IMAGE_FOLDER = "generated_captcha_images"
VOWELS = "aeiou"
CONSONANTS = "".join(set(string.ascii_lowercase) - set(VOWELS))

def generate_word(length, fmt):
    word = ""
    for i in range(length):
        if i % 2 == 0:
            word += random.choice(CONSONANTS)
        else:
            word += random.choice(VOWELS)
    return word + fmt

def download_picture(CAPTCHA_IMAGE_FOLDER, s):

    page = 'https://service.nalog.ru'
    response = s.get(url=page + '/zd.do')
    img = re.search(r'img src="/static/captcha.bin?([^"]+)"', response.text).group(0).replace('\"','').replace('img src=','')
    picture_request = requests.get(page + img)

    image_name = generate_word(6, '.jpg')

    path = os.path.join(CAPTCHA_IMAGE_FOLDER, image_name)

    if picture_request.ok:
        with open(path, 'wb') as f:
            f.write(picture_request.content)

        im = Image.open(path)
        rgb_im = im.convert('RGB')
        rgb_im.save(path)
    else:
        picture_request.raise_for_status

if __name__ == "__main__":
    s = requests.Session()
    for i in range(2):
        try:
            download_picture(CAPTCHA_IMAGE_FOLDER, s)
        except:
            time.sleep(1)





