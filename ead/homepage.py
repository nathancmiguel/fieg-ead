from playwright.sync_api import Page, Locator

class Homepage:
    def __init__(self, page: Page):
        self.__page = page
        self.__classes: list[Locator] = []

    @property
    def page(self) -> Page:
        return self.__page
    
    @property
    def classes(self) -> list[Locator]:
        return self.__classes

    def load_classes(self):
        cards = self.page.locator(".card.dashboard-card").all()
        for c in cards:
            locator = c.locator(".aalink.coursename.mr-2.mb-1").first
            self.__classes.append(locator)
            
                
                
        


    
