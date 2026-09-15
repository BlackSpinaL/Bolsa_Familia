# Calculadora de Frequência — Bolsa Família 2026

App em Streamlit que calcula o percentual de frequência escolar dos alunos
para preenchimento no formulário do Bolsa Família, replicando a lógica da
planilha original — incluindo a regra especial do 3º ano do Ensino Médio
(turmas 21301 e 21302), que soma as aulas da manhã com o contraturno de
terças e quintas-feiras.

## Arquivos

- `app.py` — aplicativo Streamlit (interface e cálculos).
- `calendario_2026.json` — dados do calendário letivo 2026 (dias letivos por
  mês, aulas por dia de cada turma/ano, e o contraturno das turmas de 3º ano).
  **Edite este arquivo em anos futuros** — não é necessário mexer no código.
- `requirements.txt` — dependências do projeto.

## Como rodar localmente

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Como publicar no GitHub + Streamlit Cloud

1. Crie um repositório novo no GitHub e suba estes 3 arquivos (`app.py`,
   `calendario_2026.json`, `requirements.txt`) para a raiz do repositório.
2. Acesse [share.streamlit.io](https://share.streamlit.io), conecte sua conta
   do GitHub e clique em **"New app"**.
3. Selecione o repositório, a branch (geralmente `main`) e o arquivo
   `app.py` como *main file path*.
4. Clique em **Deploy**. Em alguns minutos o app estará publicado com uma URL
   pública que você pode acessar do celular ou computador.

Sempre que você editar `calendario_2026.json` (por exemplo, ao atualizar o
calendário escolar do próximo ano) e enviar (`git push`) a alteração, o app
publicado atualiza automaticamente.

## Como o cálculo funciona

**Turmas regulares** (1º ao 5º, 6º ao 9º, 1º e 2º ano do EM):

```
Total de aulas no mês = dias letivos no mês × aulas por dia
```

**3º ano do EM (21301 e 21302)** — aulas da manhã + contraturno:

```
Total de aulas no mês = (dias letivos × 7 aulas de manhã)
                       + (nº de terças letivas × aulas na terça à tarde)
                       + (nº de quintas letivas × aulas na quinta à tarde)
```

**Percentual de frequência** (igual em todas as turmas):

```
% Frequência = 1 − (faltas no mês ÷ total de aulas no mês)
```

O Bolsa Família normalmente exige um mínimo de 75% de frequência — o app
sinaliza automaticamente quando um aluno fica abaixo disso, mas confirme
sempre as regras vigentes com a coordenação/Ministério.

## Funcionalidades

- **Cálculo individual**: escolha turma, mês e nº de faltas de um aluno e veja
  o percentual na hora, com o detalhamento do contraturno para o 3º ano.
- **Cálculo em lote**: cole ou importe (CSV/Excel) uma lista de alunos com
  turma, mês e faltas, calcule tudo de uma vez, veja os alunos abaixo de 75%
  destacados em vermelho, e baixe o resultado em Excel para anexar ao
  formulário do Bolsa Família.
- **Aba Calendário**: mostra de forma transparente todos os números usados
  no cálculo (dias letivos, aulas por turma, contraturno mês a mês).
