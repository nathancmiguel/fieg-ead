from playwright.sync_api import Page, Locator

class Course:
    def __init__(self, page: Page):
        self.__page = page
        self.__exams: list[Locator] = []

    @property
    def page(self) -> Page:
        return self.__page
    
    @property
    def exams(self) -> list[Locator]:
        return self.__exams

    def load_exams(self):
        final_exam = self.page.get_by_title("Avaliação Final").first
        print(f"{final_exam.inner_text()}")
        #self.__exams = final_exams