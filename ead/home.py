from ead.course import Course
from playwright.sync_api import Page, Locator
from ead.exception import RedirectError, ElementNotFound
from typing import Dict
from utils.cli import clear_console

class CourseInfo:
    def __init__(self, title: str, url: str):
        self.title: str = title
        self.url: str = url

class Home:
    def __init__(self, page: Page):
        self.__page = page
        self.url = page.url
        self.__courses: list[CourseInfo] = []

    @property
    def page(self) -> Page:
        return self.__page
    
    @property
    def courses(self) -> list[CourseInfo]:
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
            self.__courses.append(CourseInfo(locator.inner_text(), locator.get_attribute("href")))

    def course_selector(self):
        opts: Dict[int, CourseInfo] = {
            index + 1: item for index, item in enumerate(self.courses)
        }
        while(True):
            print(f"Selecione um curso: ")
            first = 0
            last = 0
            for i, c in opts.items():
                if i > last: last = i
                print(f"    {i} - {c.title}")
            try:
                opt = int(input("\nOpcao( 0 - sair ): "))
            except TypeError as e:
                print(f"Valor incorreto: {e}")
                clear_console()
                continue
            else:
                if not (first <= opt <= last):
                    print("Opção invalida!")
                    clear_console()
                    continue

                if opt == 0:
                    break
            
            
            course = opts[opt]
            self.page.goto(course.url)
            clear_console()

            course_page = Course(self.page, course.title)
            course_page.load_exams()
            course_page.exam_selector()

            self.page.goto(self.url)
            
            
            
            
                
                
        


    
