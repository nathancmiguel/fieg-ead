from playwright.sync_api import sync_playwright, Playwright, Browser, BrowserContext, Page, Locator
from ead.exception import RedirectError, ElementNotFound
from ead.home import Home

with sync_playwright() as pw:
    navegador: Browser = pw.chromium.launch(headless=False)
    ctx = navegador.new_context()
    pagina: Page = ctx.new_page()

    # Login page
    pagina.goto("https://ead.fieg.com.br/login/index.php")
    print(f"Entering with your account!")
    home = Home(pagina)
    try:
        home.fazer_login()

        # Course page
        home.buscar_cursos()
        home.seletor_curso()
    except RedirectError as e:
        print(e)
    except ElementNotFound as e:
        print(e)

    navegador.close()


