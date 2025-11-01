"""Automated LinkedIn Easy Apply bot implementation.

This module wraps Selenium browser automation primitives in a high level API
that can be scripted or used through the command line interface.  The bot is
opinionated about the application flow and focuses on single-step "Easy Apply"
forms – more complex applications are skipped to prevent accidental submission
of incomplete data.
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Iterable, Optional
from urllib.parse import quote_plus

from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver import Chrome, ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

_LOGGER = logging.getLogger(__name__)


@dataclass
class LinkedInCredentials:
    """Simple container for LinkedIn credentials."""

    username: str
    password: str


@dataclass
class JobSearchQuery:
    """Parameters that define a LinkedIn job search."""

    keywords: str
    location: str = ""
    experience_levels: Optional[Iterable[str]] = None
    max_applications: int = 10


class LinkedInEasyApplyBot:
    """High-level automation helper for LinkedIn's "Easy Apply" flow."""

    def __init__(
        self,
        credentials: LinkedInCredentials,
        query: JobSearchQuery,
        *,
        headless: bool = False,
        implicit_wait: int = 5,
        wait_timeout: int = 10,
    ) -> None:
        self._credentials = credentials
        self._query = query
        self._headless = headless
        self._implicit_wait = implicit_wait
        self._wait_timeout = wait_timeout
        self._driver: Optional[WebDriver] = None

    def _build_driver(self) -> WebDriver:
        """Configure and build a Selenium Chrome driver."""
        options = ChromeOptions()
        if self._headless:
            options.add_argument("--headless=new")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1280,800")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--disable-extensions")
        options.add_argument("--no-sandbox")
        driver = Chrome(options=options)
        driver.implicitly_wait(self._implicit_wait)
        return driver

    def __enter__(self) -> "LinkedInEasyApplyBot":
        self._driver = self._build_driver()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if self._driver:
            self._driver.quit()
            self._driver = None

    @property
    def driver(self) -> WebDriver:
        if not self._driver:
            raise RuntimeError("The bot must be used as a context manager or manually started.")
        return self._driver

    def login(self) -> None:
        """Perform a LinkedIn login with the stored credentials."""
        _LOGGER.info("Navigating to LinkedIn login page")
        self.driver.get("https://www.linkedin.com/login")

        email_input = self.driver.find_element(By.ID, "username")
        password_input = self.driver.find_element(By.ID, "password")
        email_input.clear()
        email_input.send_keys(self._credentials.username)
        password_input.clear()
        password_input.send_keys(self._credentials.password)

        password_input.submit()
        _LOGGER.info("Submitted credentials, waiting for the feed page")
        WebDriverWait(self.driver, self._wait_timeout).until(
            EC.presence_of_element_located((By.ID, "global-nav-search"))
        )
        _LOGGER.info("Successfully logged into LinkedIn")

    def run(self) -> int:
        """Execute a full login, search and apply cycle.

        Returns the number of successfully submitted applications.
        """
        applications = 0
        with self:
            self.login()
            job_urls = self._collect_job_urls()
            for job_url in job_urls:
                if applications >= self._query.max_applications:
                    _LOGGER.info("Reached application cap, stopping early")
                    break
                if self._apply_to_job(job_url):
                    applications += 1
        return applications

    # Public helper methods -------------------------------------------------
    def search_jobs(self) -> list[str]:
        """Return job posting URLs matching the search query."""
        with self:
            self.login()
            return list(self._collect_job_urls())

    # Internal helpers ------------------------------------------------------
    def _build_search_url(self) -> str:
        params = [f"keywords={quote_plus(self._query.keywords)}", "f_AL=true"]
        if self._query.location:
            params.append(f"location={quote_plus(self._query.location)}")
        if self._query.experience_levels:
            experience = "%2C".join(self._query.experience_levels)
            params.append(f"f_E={experience}")
        return "https://www.linkedin.com/jobs/search/?" + "&".join(params)

    def _collect_job_urls(self) -> list[str]:
        search_url = self._build_search_url()
        _LOGGER.info("Opening search page: %s", search_url)
        self.driver.get(search_url)
        time.sleep(2)
        job_links = set()
        job_cards_selector = "//li[contains(@class, 'jobs-search-results__list-item')]"
        while len(job_links) < self._query.max_applications:
            cards = self.driver.find_elements(By.XPATH, job_cards_selector)
            if not cards:
                _LOGGER.warning("No job cards found on the page")
                break
            for card in cards:
                link_elements = card.find_elements(By.TAG_NAME, "a")
                for link in link_elements:
                    href = link.get_attribute("href")
                    if href and "/jobs/view/" in href:
                        job_links.add(href.split("?")[0])
            self._scroll_job_results()
            if len(job_links) >= len(cards):
                break
        return list(job_links)[: self._query.max_applications]

    def _scroll_job_results(self) -> None:
        self.driver.execute_script("window.scrollBy(0, 500);")
        time.sleep(1)

    def _apply_to_job(self, job_url: str) -> bool:
        _LOGGER.info("Processing job: %s", job_url)
        self.driver.get(job_url)
        try:
            easy_apply_button = WebDriverWait(self.driver, self._wait_timeout).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'jobs-apply-button')]"))
            )
            if "Easy Apply" not in easy_apply_button.text:
                _LOGGER.info("Job does not support Easy Apply; skipping")
                return False
            easy_apply_button.click()
        except TimeoutException:
            _LOGGER.info("Easy Apply button not available; skipping")
            return False

        try:
            submitted = self._handle_application_dialog()
        finally:
            self._dismiss_dialog_if_present()
        return submitted

    def _handle_application_dialog(self) -> bool:
        wait = WebDriverWait(self.driver, self._wait_timeout)
        while True:
            try:
                submit_button = wait.until(
                    EC.element_to_be_clickable((By.XPATH, "//button[@type='submit' and not(@aria-hidden='true')]"))
                )
            except TimeoutException:
                _LOGGER.warning("Timed out waiting for submit button; aborting application")
                return False

            label = submit_button.get_attribute("aria-label") or submit_button.text
            normalized_label = label.strip().lower() if label else ""
            if "submit" in normalized_label or "send" in normalized_label:
                submit_button.click()
                _LOGGER.info("Application submitted")
                return True
            if "next" in normalized_label or "continue" in normalized_label:
                submit_button.click()
                _LOGGER.info("Clicked next step in application dialog")
                time.sleep(1)
                continue
            _LOGGER.info("Encountered unsupported application step (%s); aborting", label)
            return False

    def _dismiss_dialog_if_present(self) -> None:
        try:
            dismiss_button = self.driver.find_element(By.XPATH, "//button[@aria-label='Dismiss']")
            dismiss_button.click()
            time.sleep(1)
        except NoSuchElementException:
            pass


__all__ = ["LinkedInEasyApplyBot", "LinkedInCredentials", "JobSearchQuery"]
