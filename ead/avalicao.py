from dataclasses import dataclass
from typing import Dict, Optional

from playwright.sync_api import Locator, Page

from ead.exception import ElementNotFound
from utils.gemini import client
import time

QUIZ_START_CONTAINER_SELECTOR = ".singlebutton.quizstartbuttondiv"
QUIZ_START_BUTTON_SELECTOR = ".btn.btn-primary"
ATTEMPT_CARD_SELECTOR = ".rounded.border.p-3"
REVIEW_TITLE = "Analise as suas respostas a esta tentativa"

REVIEW_FORM_SELECTOR = ".questionflagsaveform"
RESPONSE_FORM_SELECTOR = "#responseform"
QUESTION_SELECTOR = ".que.multichoice.deferredfeedback"
CORRECT_QUESTION_SELECTOR = f"{QUESTION_SELECTOR}.correct"
CORRECT_QUESTION_IMMEDIATE_SELECTOR = ".que.multichoice.immediatefeedback.correct"
INCORRECT_QUESTION_SELECTOR = f"{QUESTION_SELECTOR}.incorrect"
INCORRECT_QUESTION_IMMEDIATE_SELECTOR = ".que.multichoice.immediatefeedback.incorrect"

NOT_ANSWERED_QUESTION_SELECTOR = f"{QUESTION_SELECTOR}.notyetanswered"
NOT_YET_ANSWERED_IMMEDIATE_QUESTION_SELECTOR = f".que.multichoice.immediatefeedback.notyetanswered"
NOT_ANSWERED_IMMEDIATE_QUESTION_SELECTOR = f".que.multichoice.immediatefeedback.notanswered"

FINISH_ATTEMPT_FORM_SELECTOR = "#frm-finishattempt"
FINISH_ATTEMPT_MODAL_SELECTOR = ".modal-dialog.modal-dialog-scrollable"


@dataclass
class AvaReview:
    pergunta: str
    resposta: str


@dataclass
class AvaAlternativa:
    radio_btn: Locator
    texto: str


class Avaliacao:
    def __init__(self, pagina: Page, tema: str):
        self.pagina = pagina
        self.url = pagina.url
        self.tema = tema
        self.correcao: Dict[str, AvaReview] = {}

    def iniciar_avaliacao(self) -> None:
        print("Iniciando quiz")
        print("Buscando por revisão...")

        tentativas = self._buscar_tentativas()

        if not tentativas:
            print("Realizando questões com Gemini...")
            self._iniciar_quiz()
            self.fazer_questao_gemini()
            self.finalizar_ava()
            return

        if self._possui_nota_maxima(tentativas):
            print("Você já obteve nota máxima")
            return

        review = self._buscar_link_revisao(tentativas)

        if review is None:
            print("Realizando questões com Gemini, revisão não encontrada...")
            self._iniciar_quiz()
            self.fazer_questao_gemini()
            self.finalizar_ava()
            return

        print("Coletando respostas da revisão...")
        review.click()

        self.buscar_respostas()
        self.pagina.goto(self.url, wait_until="domcontentloaded")

        print("Realizando questões com as respostas da revisão...")
        self._iniciar_quiz()
        self.fazer_questao()
        self.finalizar_ava()

    def buscar_respostas(self) -> None:
        form = self.pagina.locator(REVIEW_FORM_SELECTOR)

        questoes_corretas = form.locator(CORRECT_QUESTION_SELECTOR).all()
        questoes_incorretas = form.locator(INCORRECT_QUESTION_SELECTOR).all()
        questoes_imediatas = form.locator(NOT_ANSWERED_IMMEDIATE_QUESTION_SELECTOR).all()
        questoes_imediatas_ainda = form.locator(NOT_YET_ANSWERED_IMMEDIATE_QUESTION_SELECTOR).all()
        questao_respondida_imediata = form.locator(CORRECT_QUESTION_IMMEDIATE_SELECTOR).all()
        questao_incorreta_respondida_imediata = form.locator(INCORRECT_QUESTION_IMMEDIATE_SELECTOR).all()
        questoes = questoes_corretas + questoes_incorretas + questoes_imediatas + questoes_imediatas_ainda + questao_respondida_imediata + questao_incorreta_respondida_imediata
        print(f"Quantidade: {len(questoes)}")

        for questao in questoes:
            numero = self._obter_numero_questao(questao)
            pergunta_locator = questao.locator(".qtext")
            #if not pergunta_locator.is_visible():
            #    pergunta_locator = questao.locator(".qtext")
            pergunta = pergunta_locator.inner_text().strip()
            resposta = self._extrair_resposta_correta(questao)

            self.correcao[pergunta] = AvaReview(
                pergunta=pergunta,
                resposta=resposta,
            )

        if not self.correcao:
            raise ElementNotFound("Não foi possível obter as respostas")

    def fazer_questao(self) -> None:
        form = self.pagina.locator(RESPONSE_FORM_SELECTOR)
        questoes = form.locator(NOT_ANSWERED_QUESTION_SELECTOR).all() + form.locator(NOT_ANSWERED_IMMEDIATE_QUESTION_SELECTOR).all() + form.locator(NOT_YET_ANSWERED_IMMEDIATE_QUESTION_SELECTOR).all()

        for questao in questoes:
            #numero = self._obter_numero_questao(questao)
            pergunta = questao.locator(".qtext").inner_text().strip()
            resposta_correta = self.correcao[pergunta].resposta
            alternativas = self._obter_alternativas(questao)

            alternativa_encontrada = self._buscar_alternativa_por_texto(
                alternativas=alternativas,
                texto=resposta_correta,
            )

            if alternativa_encontrada is not None:
                alternativa_encontrada.radio_btn.check()

        self._avancar_questionario()

    def fazer_questao_gemini(self) -> None:
        form = self.pagina.locator(RESPONSE_FORM_SELECTOR)
        questoes = form.locator(NOT_ANSWERED_QUESTION_SELECTOR).all() + form.locator(NOT_ANSWERED_IMMEDIATE_QUESTION_SELECTOR).all() + form.locator(NOT_YET_ANSWERED_IMMEDIATE_QUESTION_SELECTOR).all()

        for questao in questoes:
            pergunta = questao.locator(".qtext").inner_text().strip()
            alternativas = self._obter_alternativas(questao)
            prompt = self.gerar_pergunta(pergunta, alternativas)

            resposta = client.models.generate_content(
                model="gemini-3.1-flash-lite",
                contents=prompt,
            )

            letra = self._normalizar_resposta_gemini(resposta.text)

            alternativa = alternativas.get(letra) or alternativas.get("a")
            if alternativa is not None:
                alternativa.radio_btn.check()
            # delay de segurança
            time.sleep(15)

        self._avancar_questionario(True)

    def finalizar_ava(self) -> None:
        while True:
            try:
                val = input("Deseja finalizar( 0 - nao, 1 - sim ): ")
            except TypeError as e:
                print(f"Valor incorreto: {e}")
                continue
            else:
                if val not in ["0", "1"]:
                    print(f"Opçao incorreta")
                    continue

                if val == "1":
                    break
                elif val == "0":
                    return

        form = self.pagina.locator(FINISH_ATTEMPT_FORM_SELECTOR)
        form.locator(".btn.btn-primary").click()

        modal = self.pagina.locator(FINISH_ATTEMPT_MODAL_SELECTOR)
        modal.locator(".btn.btn-primary").click()

    def gerar_pergunta(
        self,
        question: str,
        choices: Dict[str, AvaAlternativa],
    ) -> str:
        linhas = [
            "Quero que responda a pergunta apenas com uma letra, sendo elas a, b, c, d ou e, conforme as alternativas oferecidas.",
            f"Tema da pergunta: {self.tema}",
            question,
        ]

        for letra, alternativa in choices.items():
            linhas.append(f"{letra} - {alternativa.texto}")

        return "\n".join(linhas)

    @staticmethod
    def parse_nota(value: str) -> float:
        return float(value.strip().replace(".", "").replace(",", "."))

    def _buscar_tentativas(self) -> list[Locator]:
        return self.pagina.locator(ATTEMPT_CARD_SELECTOR).all()

    def _possui_nota_maxima(self, tentativas: list[Locator]) -> bool:
        for tentativa in tentativas:
            nota = self._obter_nota_tentativa(tentativa)

            if nota is None:
                continue

            nota_obtida, nota_total = nota

            if nota_obtida == nota_total:
                return True

        return False

    @staticmethod
    def _extrair_resposta_correta(questao: Locator) -> str:
        right_answer = questao.locator(".rightanswer")
        resposta = right_answer.locator("p").inner_text().strip() if right_answer.locator(
            "p").count() > 0 else right_answer.inner_text().strip()

        return resposta.replace("A resposta correta é:", "").strip()

    def _obter_nota_tentativa(
        self,
        tentativa: Locator,
    ) -> Optional[tuple[float, float]]:
        notas_box = tentativa.locator(
            ".moove-infobox",
            has=tentativa.locator(".moove-infobox-title", has_text="Notas"),
        )

        if notas_box.count() == 0:
            return None

        notas_text = notas_box.locator(".moove-infobox-content--small").inner_text().strip()
        nota_obtida_text, nota_total_text = notas_text.split("/")

        return (
            self.parse_nota(nota_obtida_text),
            self.parse_nota(nota_total_text),
        )

    def _buscar_link_revisao(self, tentativas: list[Locator]) -> Optional[Locator]:
        for tentativa in tentativas:
            review = tentativa.get_by_title(REVIEW_TITLE)

            if review.is_visible():
                return review

        return None

    def _iniciar_quiz(self) -> None:
        quiz_form = self.pagina.locator(QUIZ_START_CONTAINER_SELECTOR)
        quiz_form.locator(QUIZ_START_BUTTON_SELECTOR).click()

    def _obter_numero_questao(self, questao: Locator) -> int:
        numero_text = questao.locator(".rui-qno").first.inner_text().strip()
        return int(numero_text)

    def _obter_alternativas(
        self,
        questao: Locator,
    ) -> Dict[str, AvaAlternativa]:
        alternativas: Dict[str, AvaAlternativa] = {}

        answer_container = questao.locator(".answer")
        choice_rows = answer_container.locator("> div").all()

        for row in choice_rows:
            radio_btn = row.locator('input[type="radio"]').first

            letra_text = row.locator(".answernumber").inner_text().strip()
            letra = letra_text.replace(".", "").strip().lower()

            texto = row.locator(".flex-fill").inner_text().strip()

            alternativas[letra] = AvaAlternativa(
                radio_btn=radio_btn,
                texto=texto,
            )

        return alternativas

    @staticmethod
    def _buscar_alternativa_por_texto(
        alternativas: Dict[str, AvaAlternativa],
        texto: str,
    ) -> Optional[AvaAlternativa]:
        texto_normalizado = texto.strip()

        for alternativa in alternativas.values():
            if alternativa.texto.strip() == texto_normalizado:
                return alternativa

        return None

    def _avancar_questionario(self, from_gemini: bool = False) -> None:
        form = self.pagina.locator(RESPONSE_FORM_SELECTOR)
        submit_btn = form.locator("#mod_quiz-next-nav")

        val = submit_btn.get_attribute("value")

        submit_btn.click()

        if val is not None:
            if val == "Próxima página":
                if from_gemini:
                    self.fazer_questao_gemini()
                else:
                    self.fazer_questao()

    @staticmethod
    def _normalizar_resposta_gemini(resposta: Optional[str]) -> str:
        if not resposta:
            return "a"

        return resposta.strip().lower()[0]