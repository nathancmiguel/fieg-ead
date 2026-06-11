import os
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright, Playwright, Browser, BrowserContext, Page, Locator
import time
from ead.homepage import Homepage
from ead.content import Content

load_dotenv()

# Login
CPF = os.getenv("CPF")
SENHA = os.getenv("SENHA")

with sync_playwright() as pw:
    browser: Browser = pw.chromium.launch(headless=False)
    page: Page = browser.new_page()

    # Pagina de login
    page.goto("https://ead.fieg.com.br/login/index.php")
    page.locator("#username").fill(CPF)
    page.locator("#password").fill(SENHA)
    page.locator("#loginbtn").click()

    # Pagina inicial
    if page.url != "https://ead.fieg.com.br":
        page.goto("https://ead.fieg.com.br")

    home_page = Homepage(page)
    home_page.load_classes()

    print("Cursos:")
    for (i, it) in enumerate(home_page.classes):
        item: Page = it
        print(f"    {i} - {item.inner_text()}")
    print("")
    i = int(input("Id do curso: "))
    course: Locator = home_page.classes[i]

    course.click()
    content = Content(page)
    content.load_exams()

    time.sleep(4)
    browser.close()


