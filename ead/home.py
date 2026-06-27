from ead.curso import Curso
from playwright.sync_api import Page, Locator
from ead.exception import RedirectError, ElementNotFound
from typing import Dict
from utils.cli import clear_console
from env import env

class CursoInfo:
    def __init__(self, titulo: str, url: str):
        self.titulo = titulo
        self.url = url

class Home:
    def __init__(self, pagina: Page):
        self.pagina = pagina
        self.url = pagina.url
        self.cursos: list[CursoInfo] = []

    def navegar(self):
        self._fazer_login()
        self._buscar_cursos()
        self._menu_curso()
    
    def _fazer_login(self):
        print(f"Realizando login!")
        pagina = self.pagina

        cpf_input = pagina.locator("#username")
        pass_input = pagina.locator("#password")
        login_btn = pagina.locator("#loginbtn")
        
        cpf_input.fill(env.cpf)
        pass_input.fill(env.senha)
        login_btn.click()

        if pagina.url == "https://ead.fieg.com.br/login/index.php":
            raise RedirectError("O login pode ter falhado, verifique suas credenciais no arquivo .env")
        
        if pagina.url != "https://ead.fieg.com.br":
            pagina.goto("https://ead.fieg.com.br")

    def _buscar_cursos(self):
        print(f"Carregando cursos")
        pagina = self.pagina
        cards = pagina.locator(".card.dashboard-card").all()

        if len(cards) == 0:
            raise ElementNotFound("Nenhum curso encontrado")
        
        for c in cards:
            l = c.locator(".aalink.coursename.mr-2.mb-1")
            self.cursos.append(CursoInfo(l.inner_text(), l.get_attribute("href")))

    def _menu_curso(self):
        opts: Dict[int, CursoInfo] = {
            index + 1: item for index, item in enumerate(self.cursos)
        }
        while(True):
            print(f"Selecione um curso: ")
            first = 0
            last = 0
            for i, c in opts.items():
                if i > last: last = i
                print(f"    {i} - {c.titulo}")
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

            curso = opts[opt]
            self.pagina.goto(curso.url)
            clear_console()

            curso_pagina = Curso(self.pagina, curso.titulo)
            curso_pagina.buscar_avaliacoes()
            curso_pagina.selecionar_curso()

            self.pagina.goto(self.url)
            
            
            
            
                
                
        


    
