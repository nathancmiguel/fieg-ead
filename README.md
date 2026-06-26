# Fieg EAD

Web scrapper para automatizar umas ações de um site

# Como usar?

## Linux/MacOS

```bash
# Cria o setup do projeto
./setup.sh

# Ativa o ambiente virtual caso nao esteja ativado
source .venv/bin/activate

# Executa o scrapper
python main.py
```

## Windows

```powershell
# Cria o setup do projeto
.\setup.bat

# Ativa o ambiente virtual caso nao esteja ativado
.venv\Scripts\activate.bat

# Executa o scrapper
python main.py
```
## Dotenv

- Crie um arquivo `.env` na raiz do projeto e copie e cole o codigo abaixo no `.env`

- Substitua os valores de `CPF`, `SENHA` e `GEMINI_API_KEY` pelos seus dados. Obtenha o `GEMINI_API_KEY` em [Google AI Studio](https://aistudio.google.com/api-keys) e siga os passos para gerar sua API Key.

```
CPF=SEU_CPF
SENHA=SUA_SENHA
GEMINI_API_KEY=SEU_API_KEY

```

## Como funciona

- O scrapper é dividido em modulos que podem ser executados independentes.
- A ordem de execucao e:
    1.Login
    2.Selecionar curso/modulo
    3.Selecionar avaliação
    4.Fazer avaliação
- Caso a nota nao seja maxima na primeira tentativa(feita com gemini), seleciona a avaliação novamente que o scrapper ira ler as respostas da revisao e refazer as questoes.
- Caso o scrapper nao consiga fazer a avaliação por conta de algum erro no meio do caminho, voce pode terminar de fazer manualmente.