from typing import Dict

from playwright.sync_api import Page, Locator

from ead.exception import ElementNotFound
from utils.cli import clear_console

class QuizReview:
    def __init__(self, question: str, answer: str):
        self.question: str = question
        self.answer: str = answer

class QuizChoices:
    def __init__(self, radio_btn: Locator, text: str):
        self.radio_btn = radio_btn
        self.text = text

class Quiz:
    def __init__(self, page: Page):
        self.page = page
        self.url = page.url
        self.reviews: Dict[int, QuizReview] = {}

    def init_quiz(self):
        clear_console()
        print("Iniciando quiz")
        page = self.page

        while(True):
            print("Buscando por revisao...")
            # Detect review
            tries = page.locator(".rounded.border.p-3").all()
            if len(tries) > 0:
                for t in tries:
                    notas_box = t.locator(
                        ".moove-infobox",
                        has=t.locator(".moove-infobox-title", has_text="Notas")
                    )

                    if notas_box.count() == 0:
                        continue

                    notas_text = notas_box.locator(".moove-infobox-content--small").inner_text()
                    notas_text = notas_text.strip()

                    nota_obtida_text, nota_total_text = notas_text.split("/")

                    nota_obtida = self._parse_brazilian_number(nota_obtida_text)
                    nota_total = self._parse_brazilian_number(nota_total_text)

                    if nota_obtida == nota_total:
                        print("Voce ja obteve nota maxima")
                        return

                first_try = tries[1]
                review = first_try.get_by_title("Analise as suas respostas a esta tentativa")
                if not review.is_visible():
                    raise ElementNotFound("Botao de acesso a revisao nao encontrado")

                print("Coletando respostas da revisao...")
                review.click()
                self._get_answers()
                page.goto(self.url)

                print("Realizando questoes com as respostas da revisao...")
                quiz_form = page.locator(".singlebutton.quizstartbuttondiv")
                quizbtn = quiz_form.locator(".btn.btn-primary")
                quizbtn.click()
                self._do_questions()
                self._submit_quiz()

                break
            else:...

    def _parse_brazilian_number(self, value: str) -> float:
        return float(value.strip().replace(".", "").replace(",", "."))

    def _get_answers(self):
        page = self.page

        form = page.locator(".questionflagsaveform")
        questions = form.locator(".que.multichoice.deferredfeedback.correct").all()
        questions = questions + form.locator(".que.multichoice.deferredfeedback.incorrect").all()
        for q in questions:
            number = int(q.locator(".rui-qno").first.inner_text())
            question = q.locator(".qtext p").inner_text()
            answer = q.locator(".rightanswer p").inner_text()
            r = QuizReview(question, answer)
            self.reviews[number] = r

        if len(self.reviews) == 0:
            raise ElementNotFound("Nao foi possivel obter as respostas")

    def _do_questions(self):
        page = self.page

        form = page.locator("#responseform")
        questions = form.locator(".que.multichoice.deferredfeedback.notyetanswered").all()
        for q in questions:
            number = int(q.locator(".rui-qno").first.inner_text())
            answer = self.reviews[number].answer

            choices: Dict[str, QuizChoices] = {}
            answer_container = q.locator(".answer")
            choice_rows = answer_container.locator("> div").all()
            for row in choice_rows:
                radio_btn = row.locator('input[type="radio"]').first

                letter_text = row.locator(".answernumber").inner_text().strip()
                letter = letter_text.replace(".", "").strip()

                choice_text = row.locator(".flex-fill").inner_text().strip()

                choices[letter] = QuizChoices(radio_btn, choice_text)

            for c, qc in choices.items():
                if qc.text == answer:
                    qc.radio_btn.check()
                    break

        submitbtn = form.locator("#mod_quiz-next-nav")
        submitbtn.click()

    def _submit_quiz(self):
        print("Finalizando...")
        page = self.page

        form = page.locator("#frm-finishattempt")
        submitbtn = form.locator(".btn.btn-primary")
        submitbtn.click()

        modal = page.locator(".modal-dialog.modal-dialog-scrollable")
        savebtn = modal.locator(".btn.btn-primary")
        savebtn.click()
