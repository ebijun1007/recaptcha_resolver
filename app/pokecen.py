

from resolver import RecaptchaResolver
from selenium.common.exceptions import TimeoutException
import os
import logging
logger = logging.getLogger(__name__)

POKECEN_ID = os.environ.get("POKECEN_ID")
POKECEN_PW = os.environ.get("POKECEN_PW")


class PokecenResolver(RecaptchaResolver):
    def select_audio(self):
        logger.debug("choise audio mode")
        self.driver.switch_to.default_content()
        with open("origin.html", "w") as f:
            f.write(self.driver.page_source)
        frame = self.driver.find_element_by_xpath(
            "/html/body/div[6]/div[4]/iframe")
        self.driver.switch_to.frame(frame)
        with open("search_audio_button.html", "w") as f:
            f.write(self.driver.page_source)
        button = self.driver.find_element_by_id("recaptcha-audio-button")
        if button:
            button.click()
        self.driver.switch_to.default_content()

    def login(self):
        self.resolve_recaptcha()
        if self.solved_recaptcha():
            self.driver.find_element_by_id(
                "login_mail").send_keys(POKECEN_ID)
            self.driver.find_element_by_id(
                "login_pass").send_keys(POKECEN_PW)
            self.driver.find_element_by_id("login_submit").submit()
            self.sleep()
            self.driver.save_screenshot("pokecen_submitted.png")
            logger.info("login success")


if __name__ == "__main__":
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(
        "%(levelname)s:%(name)s:%(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)
    logging.getLogger("resolver").addHandler(handler)
    logging.getLogger("resolver").setLevel(logging.DEBUG)

    login_url = "https://www.pokemoncenter-online.com/?main_page=login"
    resolver = PokecenResolver()
    resolver.driver.get(login_url)
    resolver.login()

    resolver.driver.quit()
