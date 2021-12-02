from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from time import sleep
from random import randint
import pydub
import urllib
from speech_recognition import Recognizer, AudioFile, UnknownValueError
import os
import random
import logging
logger = logging.getLogger(__name__)


class RecaptchaResolver():
    def __init__(self):
        user_agent = ['Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36',
                      'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.121 Safari/537.36',
                      'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.157 Safari/537.36',
                      'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36'
                      ]
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument(
            '--user-agent=' + user_agent[random.randrange(0, len(user_agent), 1)])
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.set_page_load_timeout(30)
        self.retry = 0
        self.max_retry = 3
        self.sleep_time = 5
        logger.info("resolver initiated")

    def sleep(self, time=None):
        sleep(2)
        return
        time = time or self.sleep_time
        sleep(randint(time-1, time+1))

    def click_recaptcha_checkbox(self):
        logger.debug("click recaptcha checkbox")
        self.driver.switch_to.default_content()
        self.driver.switch_to.frame(self.driver.find_element_by_xpath(
            '//*[@class="g-recaptcha"]/div/div/iframe'))
        self.driver.find_element_by_id('rc-anchor-container').click()
        self.driver.switch_to.default_content()
        self.sleep()

    def solved_recaptcha(self):
        result = False
        try:
            self.driver.switch_to.default_content()
            self.driver.switch_to.frame(self.driver.find_element_by_xpath(
                '//*[@class="g-recaptcha"]/div/div/iframe'))
            result = self.driver.find_element_by_id(
                'recaptcha-anchor').get_attribute('aria-checked') == 'true'
            self.driver.switch_to.default_content()
        except Exception as e:
            self.driver.save_screenshot("check_solved.png")
            logger.debug(e)

        return result

    def select_audio(self):
        self.driver.switch_to.default_content()
        with open("origin.html", "w") as f:
            f.write(self.driver.page_source)
        frames = self.driver.find_elements_by_tag_name("iframe")
        self.driver.switch_to.frame(frames[2])
        with open("search_audio_button.html", "w") as f:
            f.write(self.driver.page_source)
        button = self.driver.find_element_by_id("recaptcha-audio-button")
        if button:
            self.sleep(3)
            button.click()
            logger.debug("choise audio mode")
        self.driver.switch_to.default_content()

    def answer_audio(self):
        self.select_audio()
        logger.debug("trying to answer audio")
        path = os.path.abspath(os.getcwd())
        frames = self.driver.find_elements_by_tag_name("iframe")
        self.driver.switch_to.frame(frames[-1])
        self.sleep(4)

        self.driver.find_element_by_xpath(
            "/html/body/div/div/div[3]/div/button").click()
        src = self.driver.find_element_by_id(
            "audio-source").get_attribute("src")
        urllib.request.urlretrieve(src, path+"/audio.mp3")
        pydub.AudioSegment.from_mp3(
            path+"/audio.mp3").export(path+"/audio.wav", format="wav")
        recognizer = Recognizer()
        recaptcha_audio = AudioFile(path+"/audio.wav")

        with recaptcha_audio as source:
            audio = recognizer.record(source)

        text = recognizer.recognize_google(audio, language="de-DE")

        inputfield = self.driver.find_element_by_id("audio-response")
        inputfield.send_keys(text.lower())
        inputfield.send_keys(Keys.ENTER)
        self.sleep(5)

    def resolve_recaptcha(self):
        self.click_recaptcha_checkbox()
        if self.solved_recaptcha():
            return

        logger.debug("Need to answer audio")
        while not self.solved_recaptcha():
            try:
                self.answer_audio()

            except Exception as e:
                logger.debug("resolve failed")
                logger.debug(e)

                self.driver.save_screenshot(f"ss_failed_{self.retry}.png")
                with open("page_source.html", "w") as f:
                    f.write(self.driver.page_source)
                self.retry += 1
                logger.debug(f"retry: {self.retry}")
                if self.retry > self.max_retry:
                    raise
                continue

            logger.debug("resolved")
            self.driver.save_screenshot("ss_success.png")
            self.driver.switch_to.default_content()


if __name__ == "__main__":
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(
        "%(levelname)s:%(name)s:%(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)

    url = "https://www.google.com/recaptcha/api2/demo"
    recaptcha_resolver = RecaptchaResolver()
    recaptcha_resolver.driver.get(url)
    recaptcha_resolver.resolve_recaptcha()

    if recaptcha_resolver.solved_recaptcha():
        recaptcha_resolver.driver.find_element_by_id("input1").submit()
        recaptcha_resolver.sleep()
        recaptcha_resolver.driver.save_screenshot("submitted.png")
        recaptcha_resolver.driver.quit()
