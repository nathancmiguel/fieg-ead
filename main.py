import os
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright, Playwright, Browser, BrowserContext, Page, Locator
import time
from ead.home import Home
from ead.content import Content

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
    home.do_login(CPF, PASSWORD)

    # Course page
    home.load_classes()
    home.course_selector()

    time.sleep(4)
    browser.close()


