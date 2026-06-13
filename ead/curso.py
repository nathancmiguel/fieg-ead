from ead.exception import ElementNotFound
from ead.avalicao import Avaliacao
from utils.cli import clear_console
from typing import Dict
from playwright.sync_api import Page, Locator

class AvaInfo:
    def __init__(self, title: str, url: str):
        self.title = title
        self.url = url
        

class Curso:
    def __init__(self, pagina: Page, tema: str):
        self.pagina = pagina
        self.avaliacoes: list[AvaInfo] = []
        self.url = pagina.url
        self.tema = tema

    def buscar_avaliacoes(self):
        pagina = self.pagina
        avaliacoes: list[AvaInfo] = []

        print(self.pagina.title())
        print(f"Buscando avaliações")

        table = pagina.locator('table[style="width: 100%; border-collapse: collapse; font-family: Arial,Helvetica,sans-serif;"]')
        if table.is_visible():
            abtn = table.locator('a[href*="/mod/quiz/view.php"]').all()
            if len(abtn) > 0:
                for a in abtn:
                    attr = a.get_attribute('href')
                    title = a.inner_text()
                    avaliacoes.append(AvaInfo(title, attr))

        tree_view = pagina.locator("#tabs-tree-start")
        wrapper = tree_view.locator(".tabs-wrapper")

        conteudo_btn = wrapper.get_by_title("Conteúdo do curso")
        if conteudo_btn.is_visible():
            conteudo_btn.click()
            tab_body = pagina.locator(".onetopic-tab-body")
            abtn = tab_body.locator('a[href*="/mod/quiz/view.php"]').all()
            if len(abtn) > 0:
                for a in abtn:
                    attr = a.get_attribute('href')
                    title = a.inner_text()
                    avaliacoes.append(AvaInfo(title, attr))

        avaliacao_btn = wrapper.get_by_title("Avaliação")
        if avaliacao_btn.is_visible():
            avaliacao_btn.click()
            tab_body = tree_view.locator(".onetopic-tab-body")
            abtn = tab_body.locator('a[href*="/mod/quiz/view.php"]').all()
            if len(abtn) > 0:
                for a in abtn:
                    attr = a.get_attribute('href')
                    title = a.inner_text()
                    avaliacoes.append(AvaInfo(title, attr))

        if len(avaliacoes) == 0:
            raise ElementNotFound("Nenhuma avaliação foi encontrada!")
        self.avaliacoes = avaliacoes

    def selecionar_curso(self):
        opts: Dict[int, AvaInfo] = {
            index + 1: item for index, item in enumerate(self.avaliacoes)
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
            self.pagina.goto(exam.url)
            clear_console()
            try:
                c = Avaliacao(self.pagina, self.tema)
                c.iniciar_avaliacao()
            except ElementNotFound as e:
                print(e)
            self.pagina.goto(self.url)
            clear_console()