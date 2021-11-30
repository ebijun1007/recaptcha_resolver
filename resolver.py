from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from time import sleep
from random import randint
import pydub
import urllib
from speech_recognition import Recognizer, AudioFile, UnknownValueError
import os
import random


class recaptchaResolver():
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
        self.retry = 0

    def click_recaptcha_checkbox(self):
        self.driver.switch_to.default_content()
        self.driver.switch_to.frame(self.driver.find_element_by_xpath(
            '//*[@class="g-recaptcha"]/div/div/iframe'))
        self.driver.find_element_by_id('rc-anchor-container').click()
        self.driver.switch_to.default_content()
        sleep(10)

    def solved_recaptcha(self):
        result = False
        try:
            self.driver.switch_to.default_content()
            self.driver.switch_to.frame(self.driver.find_element_by_xpath(
                '//*[@class="g-recaptcha"]/div/div/iframe'))
            result = self.driver.find_element_by_id(
                'recaptcha-anchor').get_attribute('aria-checked') == 'true'
            self.driver.switch_to.default_content()
        except:
            self.driver.save_screenshot("check_solved.png")
            raise
        return result

    def resolve_recaptcha(self):
        try:
            path = os.path.abspath(os.getcwd())

            self.driver.switch_to.default_content()
            frames = self.driver.find_elements_by_tag_name("iframe")
            self.driver.switch_to.frame(frames[-1])
            self.driver.find_element_by_id("recaptcha-audio-button").click()
            self.driver.switch_to.default_content()
            frames = self.driver.find_elements_by_tag_name("iframe")
            self.driver.switch_to.frame(frames[-1])
            sleep(randint(2, 4))

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
            sleep(10)

            if not self.solved_recaptcha():
                self.retry += 1
                if self.retry > 3:
                    raise
                self.resolve_recaptcha()
            print("Success")
            self.driver.save_screenshot("ss_success.png")

        except UnknownValueError:
            self.retry += 1
            self.resolve_recaptcha()

        except Exception:
            print("Failed")
            self.driver.save_screenshot("ss_failed.png")


if __name__ == "__main__":
    url = "https://www.google.com/recaptcha/api2/demo"
    recaptcha_resolver = recaptchaResolver()
    recaptcha_resolver.driver.get(url)
    recaptcha_resolver.click_recaptcha_checkbox()
    recaptcha_resolver.resolve_recaptcha()
    recaptcha_resolver.driver.quit()
