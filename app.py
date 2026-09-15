"""
Calculadora de Frequência Escolar - Bolsa Família
--------------------------------------------------
Replica e automatiza a lógica da planilha "Bolsa_Família_2026.xlsx":

- Cada turma/ano tem um nº de aulas por dia.
- O 3º ano do Ensino Médio (turmas 21301 e 21302) tem uma regra especial:
  7 aulas pela manhã + contraturno em algumas terças e quintas-feiras,
  cuja quantidade de aulas varia mês a mês conforme o calendário escolar.
- A partir do nº de faltas informado, calcula o percentual de frequência
  do aluno no mês, para preencher no formulário do Bolsa Família.

Autor: gerado com apoio do Claude (Anthropic) a partir da planilha original do usuário.
"""

import json
import io
from pathlib import Path

import pandas as pd
import streamlit as st

# ----------------------------------------------------------------------------
# Configuração da página
# ----------------------------------------------------------------------------
st.set_page_config(
    page_title="Frequência - Bolsa Família",
    page_icon="📋",
    layout="wide",
)

CONFIG_PATH = Path(__file__).parent / "calendario_2026.json"
LIMITE_FREQUENCIA = 0.75  # 75% é o mínimo exigido pelo Bolsa Família (condicionalidade de educação)


# ----------------------------------------------------------------------------
# Carregamento da configuração (calendário letivo)
# ----------------------------------------------------------------------------
@st.cache_data
def carregar_calendario(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def lista_turmas(calendario: dict) -> list[str]:
    """Retorna a lista de todas as turmas/anos disponíveis, na ordem da planilha."""
    turmas = list(calendario["turmas_simples"].keys())
    turmas += [f"3º ano EM - {t}" for t in calendario["turmas_3ano_em"].keys()]
    return turmas


# ----------------------------------------------------------------------------
# Lógica de cálculo (equivalente às fórmulas da planilha)
# ----------------------------------------------------------------------------
def calcular_total_aulas(calendario: dict, turma: str, mes: str) -> dict:
    """
    Retorna um dicionário com o detalhamento do total de aulas no mês
    para a turma/ano e mês informados.
    """
    dias_letivos = calendario["dias_letivos_por_mes"][mes]

    if turma in calendario["turmas_simples"]:
        aulas_por_dia = calendario["turmas_simples"][turma]["aulas_por_dia"]
        total = dias_letivos * aulas_por_dia
        return {
            "dias_letivos": dias_letivos,
            "aulas_por_dia": aulas_por_dia,
            "total_manha": total,
            "total_contraturno": 0,
            "total_aulas": total,
            "detalhe_contraturno": None,
        }

    # Turmas de 3º ano do EM (21301 / 21302)
    codigo_turma = turma.split(" - ")[-1]
    info = calendario["turmas_3ano_em"][codigo_turma]
    aulas_manha_dia = info["aulas_manha_por_dia"]
    total_manha = dias_letivos * aulas_manha_dia

    contra = info["calendario_contraturno"][mes]
    n_tercas = contra["tercas"]
    n_quintas = contra["quintas"]
    aulas_terca = info["aulas_terca_tarde"]
    aulas_quinta = info["aulas_quinta_tarde"]

    total_terca = n_tercas * aulas_terca
    total_quinta = n_quintas * aulas_quinta
    total_contraturno = total_terca + total_quinta

    total_aulas = total_manha + total_contraturno

    return {
        "dias_letivos": dias_letivos,
        "aulas_por_dia": aulas_manha_dia,
        "total_manha": total_manha,
        "total_contraturno": total_contraturno,
        "total_aulas": total_aulas,
        "detalhe_contraturno": {
            "n_tercas": n_tercas,
            "aulas_terca": aulas_terca,
            "total_terca": total_terca,
            "n_quintas": n_quintas,
            "aulas_quinta": aulas_quinta,
            "total_quinta": total_quinta,
        },
    }


def calcular_frequencia(total_aulas: int, faltas: int) -> float | None:
    """Percentual de frequência = 1 - (faltas / total de aulas no mês)."""
    if not total_aulas:
        return None
    return max(0.0, 1 - (faltas / total_aulas))


# ----------------------------------------------------------------------------
# Interface
# ----------------------------------------------------------------------------
calendario = carregar_calendario(CONFIG_PATH)
turmas = lista_turmas(calendario)
meses = calendario["meses"]

st.title("📋 Calculadora de Frequência Escolar — Bolsa Família")
st.caption(
    "Calcula o percentual de frequência de cada aluno considerando as regras "
    "de nº de aulas por ano/turma, incluindo o contraturno do 3º ano do "
    "Ensino Médio (turmas 21301 e 21302)."
)

aba_individual, aba_lote, aba_calendario = st.tabs(
    ["👤 Cálculo individual", "👥 Cálculo em lote (vários alunos)", "🗓️ Calendário / Configurações"]
)

# ----------------------------------------------------------------------------
# Aba 1: cálculo individual
# ----------------------------------------------------------------------------
with aba_individual:
    col1, col2, col3 = st.columns(3)
    with col1:
        turma_sel = st.selectbox("Turma / Ano escolar", turmas, key="ind_turma")
    with col2:
        mes_sel = st.selectbox("Mês", meses, key="ind_mes")
    with col3:
        faltas_sel = st.number_input("Nº de faltas no mês", min_value=0, max_value=200, value=0, step=1, key="ind_faltas")

    resultado = calcular_total_aulas(calendario, turma_sel, mes_sel)
    freq = calcular_frequencia(resultado["total_aulas"], faltas_sel)

    st.divider()

    c1, c2, c3 = st.columns(3)
    c1.metric("Dias letivos no mês", resultado["dias_letivos"])
    c2.metric("Aulas por dia (manhã)", resultado["aulas_por_dia"])
    c3.metric("Total de aulas no mês", resultado["total_aulas"])

    if resultado["detalhe_contraturno"]:
        d = resultado["detalhe_contraturno"]
        with st.expander("Ver detalhamento do contraturno (terça/quinta à tarde)"):
            st.write(
                f"- **Terças-feiras letivas no mês:** {d['n_tercas']} × {d['aulas_terca']} aulas "
                f"= **{d['total_terca']} aulas**"
            )
            st.write(
                f"- **Quintas-feiras letivas no mês:** {d['n_quintas']} × {d['aulas_quinta']} aulas "
                f"= **{d['total_quinta']} aulas**"
            )
            st.write(f"- **Total manhã:** {resultado['total_manha']} aulas")
            st.write(f"- **Total contraturno:** {resultado['total_contraturno']} aulas")
            st.write(f"- **Total geral:** {resultado['total_aulas']} aulas")

    st.divider()

    if freq is not None:
        pct = freq * 100
        st.subheader(f"Percentual de frequência: {pct:.2f}%")
        if freq < LIMITE_FREQUENCIA:
            st.error(
                f"⚠️ Frequência abaixo de {LIMITE_FREQUENCIA*100:.0f}% "
                "(mínimo exigido pelo Bolsa Família)."
            )
        else:
            st.success("✅ Frequência dentro do mínimo exigido pelo Bolsa Família.")
    else:
        st.warning("Não foi possível calcular — verifique os dados de calendário para essa turma/mês.")

# ----------------------------------------------------------------------------
# Aba 2: cálculo em lote
# ----------------------------------------------------------------------------
with aba_lote:
    st.write(
        "Preencha a tabela abaixo com **Aluno**, **Turma**, **Mês** e **Faltas**, "
        "ou importe um arquivo CSV/Excel com essas colunas."
    )

    modelo = pd.DataFrame(
        {
            "Aluno": ["Exemplo: João da Silva"],
            "Turma": [turmas[0]],
            "Mês": [meses[0]],
            "Faltas": [0],
        }
    )

    arquivo = st.file_uploader("Importar planilha (opcional) — colunas: Aluno, Turma, Mês, Faltas", type=["csv", "xlsx"])

    if "tabela_lote" not in st.session_state:
        st.session_state["tabela_lote"] = modelo.copy()

    if arquivo is not None:
        try:
            if arquivo.name.endswith(".csv"):
                df_importado = pd.read_csv(arquivo)
            else:
                df_importado = pd.read_excel(arquivo)
            colunas_esperadas = {"Aluno", "Turma", "Mês", "Faltas"}
            if not colunas_esperadas.issubset(set(df_importado.columns)):
                st.error(f"O arquivo precisa conter as colunas: {', '.join(colunas_esperadas)}")
            else:
                st.session_state["tabela_lote"] = df_importado[["Aluno", "Turma", "Mês", "Faltas"]]
                st.success("Arquivo importado com sucesso!")
        except Exception as e:
            st.error(f"Erro ao ler o arquivo: {e}")

    tabela_editada = st.data_editor(
        st.session_state["tabela_lote"],
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "Turma": st.column_config.SelectboxColumn("Turma", options=turmas, required=True),
            "Mês": st.column_config.SelectboxColumn("Mês", options=meses, required=True),
            "Faltas": st.column_config.NumberColumn("Faltas", min_value=0, max_value=200, step=1, required=True),
        },
        key="editor_lote",
    )

    if st.button("Calcular frequência de todos os alunos", type="primary"):
        linhas = []
        for _, row in tabela_editada.iterrows():
            if pd.isna(row.get("Turma")) or pd.isna(row.get("Mês")):
                continue
            res = calcular_total_aulas(calendario, row["Turma"], row["Mês"])
            faltas = int(row["Faltas"]) if not pd.isna(row["Faltas"]) else 0
            freq = calcular_frequencia(res["total_aulas"], faltas)
            linhas.append(
                {
                    "Aluno": row["Aluno"],
                    "Turma": row["Turma"],
                    "Mês": row["Mês"],
                    "Total de aulas no mês": res["total_aulas"],
                    "Faltas": faltas,
                    "% Frequência": round(freq * 100, 2) if freq is not None else None,
                    "Abaixo de 75%": "⚠️ Sim" if (freq is not None and freq < LIMITE_FREQUENCIA) else "Não",
                }
            )

        if linhas:
            df_resultado = pd.DataFrame(linhas)
            st.session_state["df_resultado"] = df_resultado

    if "df_resultado" in st.session_state:
        st.divider()
        st.subheader("Resultado")

        def destacar_abaixo(row):
            cor = "background-color: #ffe0e0" if row["Abaixo de 75%"] == "⚠️ Sim" else ""
            return [cor] * len(row)

        st.dataframe(
            st.session_state["df_resultado"].style.apply(destacar_abaixo, axis=1),
            use_container_width=True,
        )

        # Exportar para Excel
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            st.session_state["df_resultado"].to_excel(writer, index=False, sheet_name="Frequência")
        st.download_button(
            "⬇️ Baixar resultado em Excel",
            data=buffer.getvalue(),
            file_name="frequencia_bolsa_familia.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

# ----------------------------------------------------------------------------
# Aba 3: calendário / configurações (transparência dos números usados)
# ----------------------------------------------------------------------------
with aba_calendario:
    st.write(
        "Estes são os dados de calendário letivo usados nos cálculos acima, extraídos da sua "
        "planilha original. Edite o arquivo `calendario_2026.json` para atualizar em anos futuros "
        "(dias letivos, aulas por turma e o contraturno de terças/quintas do 3º ano do EM)."
    )

    st.markdown("**Dias letivos por mês**")
    st.dataframe(
        pd.DataFrame(
            {"Mês": meses, "Dias letivos": [calendario["dias_letivos_por_mes"][m] for m in meses]}
        ),
        use_container_width=True,
        hide_index=True,
    )

    st.markdown("**Aulas por dia — turmas do 1º ao 2º ano (regulares)**")
    st.dataframe(
        pd.DataFrame(
            [{"Turma": k, "Aulas por dia": v["aulas_por_dia"]} for k, v in calendario["turmas_simples"].items()]
        ),
        use_container_width=True,
        hide_index=True,
    )

    st.markdown("**Contraturno — 3º ano do Ensino Médio (21301 e 21302)**")
    for codigo, info in calendario["turmas_3ano_em"].items():
        st.write(
            f"**{codigo}** — {info['aulas_manha_por_dia']} aulas pela manhã · "
            f"{info['aulas_terca_tarde']} aulas na terça à tarde · "
            f"{info['aulas_quinta_tarde']} aulas na quinta à tarde"
        )
        linhas_contra = [
            {"Mês": m, "Terças letivas": v["tercas"], "Quintas letivas": v["quintas"]}
            for m, v in info["calendario_contraturno"].items()
        ]
        st.dataframe(pd.DataFrame(linhas_contra), use_container_width=True, hide_index=True)

st.divider()
st.caption(
    "⚠️ O percentual mínimo de frequência exigido pelo Bolsa Família (condicionalidade de educação) "
    "é geralmente de 75%. Confirme sempre as regras vigentes com a coordenação/Ministério, pois "
    "podem mudar."
)
