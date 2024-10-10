# use playwright to scrape data from worldometer website
from typing import Dict, Union

from playwright.sync_api import Playwright


class Api:
    def __init__(self, playwright: Playwright):
        print("Starting browser...")
        self.browser = playwright.chromium.launch()
        self.page = self.browser.new_page()
        self.page.goto("https://www.worldometers.info/")
        print("Browser started. Waiting for data...")
        self.page.wait_for_timeout(1000)
        print("Data Ready.")

    def get_data(self) -> Dict[str, Union[int, float, None]]:
        return self.page.evaluate("() => rts_counters")
