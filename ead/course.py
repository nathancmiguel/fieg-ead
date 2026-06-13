from ead.exception import ElementNotFound
from ead.quiz import Quiz
from utils.cli import clear_console
from typing import Dict
from playwright.sync_api import Page, Locator

class EvalInfo:
    def __init__(self, title: str, url: str):
        self.title = title
        self.url = url
        

class Course:
    def __init__(self, page: Page, theme: str):
        self.__page = page
        self.__exams: list[EvalInfo] = []
        self.url = page.url
        self.theme = theme

    @property
    def page(self) -> Page:
        return self.__page
    
    @property
    def exams(self) -> list[EvalInfo]:
        return self.__exams

    def load_exams(self):
        page = self.page
        exams: list[EvalInfo] = []

        print(self.page.title())
        print(f"Buscando avaliações")

        table = page.locator('table[style="width: 100%; border-collapse: collapse; font-family: Arial,Helvetica,sans-serif;"]')
        if table.is_visible():
            abtn = table.locator('a[href*="/mod/quiz/view.php"]').all()
            if len(abtn) > 0:
                for a in abtn:
                    attr = a.get_attribute('href')
                    title = a.inner_text()
                    exams.append(EvalInfo(title, attr))

        tree_view = page.locator("#tabs-tree-start")
        wrapper = tree_view.locator(".tabs-wrapper")

        course_content_btn = wrapper.get_by_title("Conteúdo do curso")
        if course_content_btn.is_visible():
            course_content_btn.click()
            tab_body = page.locator(".onetopic-tab-body")
            abtn = tab_body.locator('a[href*="/mod/quiz/view.php"]').all()
            if len(abtn) > 0:
                for a in abtn:
                    attr = a.get_attribute('href')
                    title = a.inner_text()
                    exams.append(EvalInfo(title, attr))

        evaluation_btn = wrapper.get_by_title("Avaliação")
        if evaluation_btn.is_visible():
            evaluation_btn.click()
            tab_body = tree_view.locator(".onetopic-tab-body")
            abtn = tab_body.locator('a[href*="/mod/quiz/view.php"]').all()
            if len(abtn) > 0:
                for a in abtn:
                    attr = a.get_attribute('href')
                    title = a.inner_text()
                    exams.append(EvalInfo(title, attr))

        if len(exams) == 0:
            raise ElementNotFound("Nenhuma avaliação foi encontrada!")
        self.__exams = exams

    def exam_selector(self):
        opts: Dict[int, EvalInfo] = {
            index + 1: item for index, item in enumerate(self.exams)
        }
        while(True):
            print(f"Selecione uma avaliação: ")
            first = 0
            last = 0
            for i, l in opts.items():
                if i > last: last = i
                print(f"    {i} - {l.title}: {l.url}")
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
            
            exam = opts[opt]
            self.page.goto(exam.url)
            clear_console()
            try:
                c = Quiz(self.page, self.theme)
                c.init_quiz()
            except ElementNotFound as e:
                print(e)
            self.page.goto(self.url)
            clear_console()