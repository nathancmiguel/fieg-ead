from playwright.sync_api import Page, Locator
from ead.exception import RedirectError, ElementNotFound
from typing import Dict
from utils.cli import clear_console

class Home:
    def __init__(self, page: Page):
        self.__page = page
        self.__courses: list[Locator] = []

    @property
    def page(self) -> Page:
        return self.__page
    
    @property
    def courses(self) -> list[Locator]:
        return self.__courses
    
    def do_login(self, cpf: str, password: str):
        print(f"Realizando login!")
        page = self.page

        cpf_input = page.locator("#username")
        pass_input = page.locator("#password")
        login_btn = page.locator("#loginbtn")
        
        cpf_input.fill(cpf)
        pass_input.fill(password)
        login_btn.click()

        if page.url == "https://ead.fieg.com.br/login/index.php":
            raise RedirectError("O login pode ter falhado, verifique suas credenciais no arquivo .env")
        
        if page.url != "https://ead.fieg.com.br":
            page.goto("https://ead.fieg.com.br")

    def load_classes(self):
        print(f"Carregando cursos")
        cards = self.page.locator(".card.dashboard-card").all()
        if len(cards) == 0:
            raise ElementNotFound("Nenhum curso encontrado")
        
        for c in cards:
            locator = c.locator(".aalink.coursename.mr-2.mb-1").first
            self.__courses.append(locator)

    def course_selector(self):
        opts: Dict[int, Locator] = {
            index + 1: item for index, item in enumerate(self.courses)
        }
        while(True):
            print(f"Selecione um curso: ")
            first = 0
            last = 1
            print(f"    0 - sair")
            for i, l in opts.items():
                if i > last: last = i
                print(f"    {i} - {l.inner_text()}")

            try:
                opt = int(input("\nOpcao: "))
            except TypeError as e:
                print(f"Valor incorreto: {e}")
                clear_console()
                continue
            else:
                if not (opt >= first and opt <= last):
                    print("Opção invalida!")
                    clear_console()
                    continue

                if opt == 0:
                    break
            
            
            course = opts[opt]
            course.click()
            clear_console()
            
            
            
                
                
        


    
