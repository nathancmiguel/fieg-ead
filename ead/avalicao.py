import re
import time
from dataclasses import dataclass
from typing import Callable, Dict, Optional

from playwright.sync_api import Locator, Page

from ead.exception import ElementNotFound
from utils.gemini import client

# ---------------------------------------------------------------------------
# Seletores — início do quiz
# ---------------------------------------------------------------------------
QUIZ_START_CONTAINER_SELECTOR = ".singlebutton.quizstartbuttondiv"
QUIZ_START_BUTTON_SELECTOR = ".btn.btn-primary"

# ---------------------------------------------------------------------------
# Seletores — tentativas anteriores
# ---------------------------------------------------------------------------
ATTEMPT_CARD_SELECTOR = ".rounded.border.p-3"
REVIEW_TITLE = "Analise as suas respostas a esta tentativa"

# ---------------------------------------------------------------------------
# Seletores — formulário de revisão (gabarito)
# ---------------------------------------------------------------------------
REVIEW_FORM_SELECTOR = ".questionflagsaveform"

_BASE_DEFERRED = ".que.multichoice.deferredfeedback"
_BASE_IMMEDIATE = ".que.multichoice.immediatefeedback"

CORRECT_QUESTION_SELECTOR           = f"{_BASE_DEFERRED}.correct"
INCORRECT_QUESTION_SELECTOR         = f"{_BASE_DEFERRED}.incorrect"
CORRECT_QUESTION_IMMEDIATE_SELECTOR = f"{_BASE_IMMEDIATE}.correct"
INCORRECT_QUESTION_IMMEDIATE_SELECTOR = f"{_BASE_IMMEDIATE}.incorrect"

REVIEW_QUESTION_SELECTORS = [
    CORRECT_QUESTION_SELECTOR,
    INCORRECT_QUESTION_SELECTOR,
    CORRECT_QUESTION_IMMEDIATE_SELECTOR,
    INCORRECT_QUESTION_IMMEDIATE_SELECTOR,
]

# ---------------------------------------------------------------------------
# Seletores — formulário de resposta (tentativa ativa)
# ---------------------------------------------------------------------------
RESPONSE_FORM_SELECTOR = "#responseform"

NOT_ANSWERED_QUESTION_SELECTOR          = f"{_BASE_DEFERRED}.notyetanswered"
NOT_ANSWERED_IMMEDIATE_QUESTION_SELECTOR = f"{_BASE_IMMEDIATE}.notanswered"
NOT_YET_ANSWERED_IMMEDIATE_QUESTION_SELECTOR = f"{_BASE_IMMEDIATE}.notyetanswered"

RESPONSE_QUESTION_SELECTORS = [
    NOT_ANSWERED_QUESTION_SELECTOR,
    NOT_ANSWERED_IMMEDIATE_QUESTION_SELECTOR,
    NOT_YET_ANSWERED_IMMEDIATE_QUESTION_SELECTOR,
]

# ---------------------------------------------------------------------------
# Seletores — finalização
# ---------------------------------------------------------------------------
FINISH_ATTEMPT_FORM_SELECTOR  = "#frm-finishattempt"
FINISH_ATTEMPT_MODAL_SELECTOR = ".modal-dialog.modal-dialog-scrollable"


# ---------------------------------------------------------------------------
# Modelos de dados
# ---------------------------------------------------------------------------

@dataclass
class AvaReview:
    pergunta: str
    resposta: str


@dataclass
class AvaAlternativa:
    radio_btn: Locator
    texto: str


# ---------------------------------------------------------------------------
# Classe principal
# ---------------------------------------------------------------------------

class Avaliacao:
    def __init__(self, pagina: Page, tema: str):
        self.pagina = pagina
        self.url = pagina.url
        self.tema = tema
        self.correcao: Dict[str, AvaReview] = {}

    # ------------------------------------------------------------------
    # Fluxo principal
    # ------------------------------------------------------------------

    def iniciar_avaliacao(self) -> None:
        print("Iniciando quiz")
        print("Buscando por revisão...")

        if self._possui_nota_maxima():
            print("Você já obteve nota máxima")
            return

        tentativas = self._buscar_tentativas()

        if not tentativas:
            print("Realizando questões com Gemini...")
            self._executar_tentativa_com_gemini()
            return

        review = self._buscar_link_revisao(tentativas)

        if review is None:
            print("Realizando questões com Gemini, revisão não encontrada...")
            self._executar_tentativa_com_gemini()
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
        questoes = self._coletar_questoes(form, REVIEW_QUESTION_SELECTORS)

        print(f"Quantidade: {len(questoes)}")

        for questao in questoes:
            pergunta = questao.locator(".qtext").inner_text().strip()
            resposta = self._extrair_resposta_correta(questao)
            self.correcao[pergunta] = AvaReview(pergunta=pergunta, resposta=resposta)

        if not self.correcao:
            raise ElementNotFound("Não foi possível obter as respostas")

    def fazer_questao(self) -> None:
        form = self.pagina.locator(RESPONSE_FORM_SELECTOR)
        questoes = self._coletar_questoes(form, RESPONSE_QUESTION_SELECTORS)

        for questao in questoes:
            pergunta = questao.locator(".qtext").inner_text().strip()
            alternativas = self._obter_alternativas(questao)
            resposta_correta = self.correcao[pergunta].resposta

            alternativa = self._buscar_alternativa_por_texto(alternativas, resposta_correta)
            if alternativa is not None:
                alternativa.radio_btn.check()

        self._avancar_questionario(self.fazer_questao)

    def fazer_questao_gemini(self) -> None:
        form = self.pagina.locator(RESPONSE_FORM_SELECTOR)
        questoes = self._coletar_questoes(form, RESPONSE_QUESTION_SELECTORS)

        for questao in questoes:
            pergunta = questao.locator(".qtext").inner_text().strip()
            alternativas = self._obter_alternativas(questao)
            prompt = self._gerar_prompt(pergunta, alternativas)

            resposta = client.models.generate_content(
                model="gemini-3.1-flash-lite",
                contents=prompt,
            )

            letra = self._normalizar_resposta_gemini(resposta.text)
            alternativa = alternativas.get(letra) or alternativas.get("a")
            if alternativa is not None:
                alternativa.radio_btn.check()

            time.sleep(15)  # delay de segurança entre requisições

        self._avancar_questionario(self.fazer_questao_gemini)

    def finalizar_ava(self) -> None:
        while True:
            try:
                val = input("Deseja finalizar( 0 - nao, 1 - sim ): ")
            except TypeError as e:
                print(f"Valor incorreto: {e}")
                continue

            if val not in ["0", "1"]:
                print("Opção incorreta")
                continue

            if val == "1":
                break
            if val == "0":
                return

        form = self.pagina.locator(FINISH_ATTEMPT_FORM_SELECTOR)
        form.locator(".btn.btn-primary").click()

        modal = self.pagina.locator(FINISH_ATTEMPT_MODAL_SELECTOR)
        modal.locator(".btn.btn-primary").click()

    # ------------------------------------------------------------------
    # Geração de prompt para o Gemini
    # ------------------------------------------------------------------

    def _gerar_prompt(
        self,
        pergunta: str,
        alternativas: Dict[str, AvaAlternativa],
    ) -> str:
        linhas = [
            "Quero que responda a pergunta apenas com uma letra, sendo elas a, b, c, d ou e, conforme as alternativas oferecidas.",
            f"Tema da pergunta: {self.tema}",
            pergunta,
        ]
        for letra, alternativa in alternativas.items():
            linhas.append(f"{letra} - {alternativa.texto}")
        return "\n".join(linhas)

    # ------------------------------------------------------------------
    # Helpers de navegação / quiz
    # ------------------------------------------------------------------

    def _executar_tentativa_com_gemini(self) -> None:
        self._iniciar_quiz()
        self.fazer_questao_gemini()
        self.finalizar_ava()

    def _iniciar_quiz(self) -> None:
        self.pagina.locator(QUIZ_START_CONTAINER_SELECTOR).locator(QUIZ_START_BUTTON_SELECTOR).click()

    def _avancar_questionario(self, proximo: Callable[[], None]) -> None:
        form = self.pagina.locator(RESPONSE_FORM_SELECTOR)
        submit_btn = form.locator("#mod_quiz-next-nav")
        label = submit_btn.get_attribute("value")
        submit_btn.click()

        if label == "Próxima página":
            proximo()

    # ------------------------------------------------------------------
    # Helpers de tentativas / notas
    # ------------------------------------------------------------------

    def _buscar_tentativas(self) -> list[Locator]:
        return self.pagina.locator(ATTEMPT_CARD_SELECTOR).all()

    def _buscar_link_revisao(self, tentativas: list[Locator]) -> Optional[Locator]:
        for tentativa in tentativas:
            review = tentativa.get_by_title(REVIEW_TITLE)
            if review.is_visible():
                return review
        return None

    def _possui_nota_maxima(self) -> bool:
        pagina = self.pagina
        feedback = pagina.locator("#feedback")
        if feedback.is_visible():
            feedback_text = feedback.inner_text().strip()
            
            match = re.search(r"([\d,]+)\s*/\s*([\d,]+)", feedback_text)
            if match:
                nota_obtida, nota_maxima = match.groups()
                if nota_obtida == nota_maxima:
                    return True
        return False

    def _obter_nota_tentativa(self, tentativa: Locator) -> Optional[tuple[float, float]]:
        notas_box = tentativa.locator(
            ".moove-infobox",
            has=tentativa.locator(".moove-infobox-title", has_text="Notas"),
        )

        if notas_box.count() == 0:
            return None

        notas_text = notas_box.locator(".moove-infobox-content--small").inner_text().strip()
        nota_obtida_text, nota_total_text = notas_text.split("/")

        return self.parse_nota(nota_obtida_text), self.parse_nota(nota_total_text)

    @staticmethod
    def parse_nota(value: str) -> float:
        return float(value.strip().replace(".", "").replace(",", "."))

    # ------------------------------------------------------------------
    # Helpers de questões / alternativas
    # ------------------------------------------------------------------

    @staticmethod
    def _coletar_questoes(form: Locator, selectors: list[str]) -> list[Locator]:
        questoes: list[Locator] = []
        for selector in selectors:
            questoes.extend(form.locator(selector).all())
        return questoes

    @staticmethod
    def _extrair_resposta_correta(questao: Locator) -> str:
        right_answer = questao.locator(".rightanswer")
        paragrafo = right_answer.locator("p")

        resposta = (
            paragrafo.inner_text().strip()
            if paragrafo.count() > 0
            else right_answer.inner_text().strip()
        )

        return resposta.replace("A resposta correta é:", "").strip()

    @staticmethod
    def _obter_alternativas(questao: Locator) -> Dict[str, AvaAlternativa]:
        alternativas: Dict[str, AvaAlternativa] = {}
        choice_rows = questao.locator(".answer > div").all()

        for row in choice_rows:
            radio_btn = row.locator('input[type="radio"]').first
            letra = row.locator(".answernumber").inner_text().strip().replace(".", "").lower()
            texto = row.locator(".flex-fill").inner_text().strip()
            alternativas[letra] = AvaAlternativa(radio_btn=radio_btn, texto=texto)

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

    @staticmethod
    def _normalizar_resposta_gemini(resposta: Optional[str]) -> str:
        if not resposta:
            return "a"
        return resposta.strip().lower()[0]