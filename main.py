import os
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright, Playwright, Browser, BrowserContext, Page, Locator
import time

from ead.exception import RedirectError, ElementNotFound
from ead.home import Home
from ead.course import Course

load_dotenv()

# Login
CPF = os.getenv("CPF")
PASSWORD = os.getenv("SENHA")

with sync_playwright() as pw:
    browser: Browser = pw.chromium.launch(headless=False)
    page: Page = browser.new_page()

    # Login page
    page.goto("https://ead.fieg.com.br/login/index.php")
    print(f"Entering with your account!")
    home = Home(page)
    try:
        home.do_login(CPF, PASSWORD)

        # Course page
        home.load_classes()
        home.course_selector()
    except RedirectError as e:
        print(e)
    except ElementNotFound as e:
        print(e)

    browser.close()


