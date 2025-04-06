import json
import time
from typing import List, Optional

from selenium import webdriver
from selenium.common.exceptions import ElementClickInterceptedException
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait

from functions.invoice_logging import log_message


class Browser:

    def __init__(self, headless: bool = False):
        log_message("Initializing browser...")
        options = Options()
        if headless:
            options.add_argument("-headless")
            log_message("Using headless mode")

        self.driver = webdriver.Firefox(options=options)
        self.wait = WebDriverWait(self.driver, 3 * 3600)

    # ─────────────────────────────
    # Navigation
    # ─────────────────────────────

    def open_url(self, url: str) -> None:
        """Navigate to the given URL and wait for page to load."""
        self.driver.get(url)
        self._wait_for_page_ready()

    # ─────────────────────────────
    # Element Finding
    # ─────────────────────────────

    def find_element(self, by: By, selector: str) -> WebElement:
        """Find a single visible element."""
        self.wait_for_element_visible(by, selector)
        return self.driver.find_element(by, selector)

    def find_elements(self, by: By, selector: str) -> List[WebElement]:
        """Find multiple visible elements."""
        self.wait_for_element_visible(by, selector)
        return self.driver.find_elements(by, selector)

    # ─────────────────────────────
    # Content Extraction
    # ─────────────────────────────

    def get_elements_text(self, by: By, selector: str) -> List[str]:
        """Returns list of stripped text content from matching elements."""
        elements = self.find_elements(by, selector)
        return [e.text.strip() for e in elements]

    def get_first_element_text(self, by: By, selector: str) -> Optional[str]:
        """Returns text content of the first matching element or None."""
        texts = self.get_elements_text(by, selector)
        return texts[0] if texts else None

    def get_first_cell_result(self, selector, selection):
        cells_content = self.get_cells_content(selector, selection)
        return cells_content[0]

    def get_cells_content(self, selector, selection):
        cells = self.find_elements(selector, selection)
        cells_content = [cell.text.strip() for cell in cells]
        return cells_content

    def get_select_options_by_name(self, name):
        select_element = self.find_element(By.NAME, name)
        select = Select(select_element)
        options = [o.get_attribute("value") for o in select.options]
        return options

    # ─────────────────────────────
    # Click Actions
    # ─────────────────────────────

    def click_by_selector(self, by: By, selector: str) -> None:
        """Click an element with retry on intercept."""
        while True:
            try:
                self.find_element(by, selector).click()
                break
            except ElementClickInterceptedException:
                time.sleep(0.2)
        self._sleep(1)

    def click_by_css(self, selector: str):
        self.click_by_selector(By.CSS_SELECTOR, selector)

    def force_click(self, element: WebElement) -> None:
        """Force a click via JavaScript."""
        self.driver.execute_script("arguments[0].click();", element)

    def click_button_by_text(self, label: str) -> None:
        """Click a button with exact text."""
        xpath = f"//button[text()='{label}']"
        self.click_by_selector(By.XPATH, xpath)

    def click_button_by_id(self, ID: str) -> None:
        """Click a button with exact text."""
        self.click_by_selector(By.ID, ID)

    def click_button_by_name(self, name: str) -> None:
        """Click a button by its name attribute."""
        self.click_by_selector(By.NAME, name)

    def click_first_link_in_element(self, by: By, selector: str) -> None:
        """Click the first <a> inside the first matching element."""
        element = self.find_elements(by, selector)[0]
        link = element.find_element(By.TAG_NAME, "a")
        link.click()

    def click_checkboxes_by_index_and_class(self, selector: str, indexes: List[int]) -> None:
        """Click checkboxes at specific indexes (if they exist)."""

        checkboxes = self.find_elements(By.CSS_SELECTOR, f"input.{selector}[type='checkbox']")

        for i in indexes:
            if i < len(checkboxes):
                checkboxes[i].click()

    def click_radio_button_by_name(self, name: str, value: str) -> None:
        """Click a radio button by name and value."""
        selector = f"input[type='radio'][name='{name}'][value='{value}']"
        self.click_by_selector(By.CSS_SELECTOR, selector)

    # ─────────────────────────────
    # Form Interactions
    # ─────────────────────────────

    def fill_input(self, by: By, selector: str, value: str) -> None:
        """Fill an input field using .send_keys()."""
        field = self.find_element(by, selector)
        field.clear()
        field.send_keys(value)

    def fill_input_by_placeholder(self, placeholder: str, value: str) -> None:
        """Fill an input field using .send_keys()."""
        field = self.find_element(By.XPATH, f"//input[@placeholder='{placeholder}']")
        field.clear()
        field.send_keys(value)

    def fill_input_by_placeholder_js(self, placeholder: str, value: str) -> None:
        """Fill an input field using JavaScript for more reliability."""
        field = self.find_element(By.XPATH, f"//input[@placeholder='{placeholder}']")
        field.clear()
        escaped = json.dumps(value)
        self.driver.execute_script(f"arguments[0].value = {escaped};", field)

    def fill_input_by_name_js(self, name: str, value: str) -> None:
        """Fill an input field using JavaScript for more reliability."""
        field = self.find_element(By.NAME, name)
        field.clear()
        escaped = json.dumps(value)
        self.driver.execute_script(f"arguments[0].value = {escaped};", field)

    def select_dropdown_value_by_id(self, selector: str, value: str) -> None:
        """Select a dropdown value by 'value' attribute."""
        dropdown = Select(self.find_element(By.ID, selector))
        dropdown.select_by_value(value)

    def select_dropdown_value_by_name(self, selector: str, value: str) -> None:
        """Select a dropdown value by 'value' attribute."""
        dropdown = Select(self.find_element(By.NAME, selector))
        dropdown.select_by_value(value)

    # ─────────────────────────────
    # Waiting
    # ─────────────────────────────

    def wait_for_element_visible(self, by: By, selector: str) -> None:
        """Wait for an element to be visible in DOM."""
        self.wait.until(EC.presence_of_element_located((by, selector)))

    def wait_for_element_gone(self, by: By, selector: str) -> None:
        """Wait until element is no longer visible."""
        self.wait.until(EC.invisibility_of_element_located((by, selector)))

    def wait_for_text_visible(self, text: str) -> None:
        """Wait until the given text appears somewhere on the page."""
        self.wait.until(EC.presence_of_element_located((By.XPATH, f"//*[contains(text(), '{text}')]")))

    def wait_for_text_gone(self, text: str) -> None:
        """Wait until the given text disappears from the page."""
        self.wait.until(EC.invisibility_of_element_located((By.XPATH, f"//*[contains(text(), '{text}')]")))

    def _wait_for_page_ready(self) -> None:
        """Placeholder: add logic to wait for full page load if needed."""
        self._wait_for_lock_screen()
        self._sleep(1)

    def _wait_for_lock_screen(self) -> None:
        """Override this method if your app has a loading overlay to wait for."""
        pass

    def _sleep(self, seconds: int) -> None:
        """Sleep for n seconds."""
        time.sleep(seconds)

    # ─────────────────────────────
    # Misc
    # ─────────────────────────────

    def str_exists(self, string: str) -> bool:
        return string in self.get_page_source()

    def execute_script(self, script: str) -> None:
        """Execute raw JavaScript."""
        self.driver.execute_script(script)

    def get_page_source(self) -> str:
        """Return the current page source."""
        return self.driver.page_source

    def close(self) -> None:
        """Close the browser."""
        self.driver.quit()
