"""
Calculadora de Frequência Escolar - Bolsa Família
--------------------------------------------------
Replica e automatiza a lógica da planilha "Bolsa_Família_2026.xlsx".

Novidades desta versão:
- Uploader de JSON para restaurar o calendário sem mexer no GitHub.
- Edição do NOME das turmas (regulares e de contraturno) direto na tela.
- Botão para apagar linha selecionada na tabela de lote.
- Compatível com Streamlit >= 1.40 (ícone de lixeira no data_editor).

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
LIMITE_FREQUENCIA = 0.75

DIAS_SEMANA = ["segunda", "terca", "quarta", "quinta", "sexta"]
DIAS_SEMANA_LABEL = {
    "segunda": "Segunda",
    "terca": "Terça",
    "quarta": "Quarta",
    "quinta": "Quinta",
    "sexta": "Sexta",
}

SUFIXO_CONTRATURNO = " (contraturno)"


# ----------------------------------------------------------------------------
# Carregamento / inicialização da configuração (calendário letivo)
# ----------------------------------------------------------------------------
def carregar_calendario_do_disco(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def garantir_calendario_na_sessao():
    if "calendario" not in st.session_state:
        st.session_state["calendario"] = carregar_calendario_do_disco(CONFIG_PATH)


def salvar_calendario_no_disco():
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(st.session_state["calendario"], f, ensure_ascii=False, indent=2)


def lista_turmas(calendario: dict):
    turmas = []
    mapa = {}
    for nome in calendario["turmas_simples"]:
        turmas.append(nome)
        mapa[nome] = ("simples", nome)
    for nome in calendario.get("turmas_contraturno", {}):
        disp = f"{nome}{SUFIXO_CONTRATURNO}"
        turmas.append(disp)
        mapa[disp] = ("contraturno", nome)
    return turmas, mapa


# ----------------------------------------------------------------------------
# Lógica de cálculo
# ----------------------------------------------------------------------------
def calcular_total_aulas(calendario: dict, turma_disp: str, mes: str, mapa_turmas: dict) -> dict:
    dias_letivos = calendario["dias_letivos_por_mes"].get(mes, 0)

    if turma_disp not in mapa_turmas:
        return {
            "dias_letivos": dias_letivos,
            "aulas_por_dia": 0,
            "total_manha": 0,
            "total_contraturno": 0,
            "total_aulas": 0,
            "detalhe_contraturno": None,
        }

    tipo, chave = mapa_turmas[turma_disp]

    if tipo == "simples":
        aulas_por_dia = calendario["turmas_simples"][chave]["aulas_por_dia"]
        total = dias_letivos * aulas_por_dia
        return {
            "dias_letivos": dias_letivos,
            "aulas_por_dia": aulas_por_dia,
            "total_manha": total,
            "total_contraturno": 0,
            "total_aulas": total,
            "detalhe_contraturno": None,
        }

    info = calendario["turmas_contraturno"][chave]
    aulas_manha_dia = info["aulas_manha_por_dia"]
    total_manha = dias_letivos * aulas_manha_dia

    aulas_semana = info.get("aulas_por_dia_semana", {})
    dias_mes = info.get("dias_letivos_por_dia_semana_por_mes", {}).get(mes, {})

    detalhe_linhas = []
    total_contraturno = 0
    for dia in DIAS_SEMANA:
        aulas = aulas_semana.get(dia, 0) or 0
        n_dias = dias_mes.get(dia, 0) or 0
        if aulas or n_dias:
            subtotal = aulas * n_dias
            total_contraturno += subtotal
            detalhe_linhas.append(
                {
                    "dia_semana": DIAS_SEMANA_LABEL[dia],
                    "n_dias": n_dias,
                    "aulas_por_dia": aulas,
                    "subtotal": subtotal,
                }
            )

    total_aulas = total_manha + total_contraturno

    return {
        "dias_letivos": dias_letivos,
        "aulas_por_dia": aulas_manha_dia,
        "total_manha": total_manha,
        "total_contraturno": total_contraturno,
        "total_aulas": total_aulas,
        "detalhe_contraturno": detalhe_linhas if detalhe_linhas else None,
    }


def calcular_frequencia(total_aulas: int, faltas: int):
    if not total_aulas:
        return None
    return max(0.0, 1 - (faltas / total_aulas))


# ----------------------------------------------------------------------------
# Interface
# ----------------------------------------------------------------------------
garantir_calendario_na_sessao()
calendario = st.session_state["calendario"]
turmas, mapa_turmas = lista_turmas(calendario)
meses = calendario["meses"]

st.title("📋 Calculadora de Frequência Escolar — Bolsa Família 2026")
st.caption(
    "Calcula o percentual de frequência de cada aluno considerando as regras "
    "de nº de aulas por ano/turma, incluindo o contraturno das turmas que "
    "têm aula em turno estendido."
)

aba_individual, aba_lote, aba_calendario = st.tabs(
    ["👤 Cálculo individual", "👥 Cálculo em lote (vários alunos)", "🗓️ Calendário / Configurações"]
)

# ----------------------------------------------------------------------------
# Aba 1: cálculo individual
# ----------------------------------------------------------------------------
with aba_individual:
    if not turmas:
        st.warning("Nenhuma turma cadastrada ainda. Vá até a aba **Calendário / Configurações** para adicionar turmas.")
    else:
        col1, col2, col3 = st.columns(3)
        with col1:
            turma_sel = st.selectbox("Turma / Ano escolar", turmas, key="ind_turma")
        with col2:
            mes_sel = st.selectbox("Mês", meses, key="ind_mes")
        with col3:
            faltas_sel = st.number_input("Nº de faltas no mês", min_value=0, max_value=200, value=0, step=1, key="ind_faltas")

        resultado = calcular_total_aulas(calendario, turma_sel, mes_sel, mapa_turmas)
        freq = calcular_frequencia(resultado["total_aulas"], faltas_sel)

        st.divider()

        c1, c2, c3 = st.columns(3)
        c1.metric("Dias letivos no mês", resultado["dias_letivos"])
        c2.metric("Aulas por dia (manhã)", resultado["aulas_por_dia"])
        c3.metric("Total de aulas no mês", resultado["total_aulas"])

        if resultado["detalhe_contraturno"]:
            with st.expander("Ver detalhamento do contraturno"):
                for linha in resultado["detalhe_contraturno"]:
                    st.write(
                        f"- **{linha['dia_semana']}-feira(s) letiva(s) no mês:** {linha['n_dias']} × "
                        f"{linha['aulas_por_dia']} aulas = **{linha['subtotal']} aulas**"
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
    st.caption(
        "💡 Para apagar UM aluno: clique na linha (à esquerda) e aperte a tecla **Delete/Backspace**, "
        "ou passe o mouse sobre a linha e clique no ícone de lixeira que aparece. "
        "Para apagar TODOS de uma vez, use o botão \"🗑️ Limpar tabela\" abaixo."
    )

    colunas_lote = ["Aluno", "Turma", "Mês", "Faltas"]

    def tabela_vazia():
        return pd.DataFrame({c: pd.Series(dtype="object" if c != "Faltas" else "int64") for c in colunas_lote})

    def tabela_modelo():
        return pd.DataFrame(
            {
                "Aluno": ["Exemplo: João da Silva"],
                "Turma": [turmas[0] if turmas else ""],
                "Mês": [meses[0]],
                "Faltas": [0],
            }
        )

    if "tabela_lote" not in st.session_state:
        st.session_state["tabela_lote"] = tabela_modelo()

    col_upload, col_limpar = st.columns([3, 1])
    with col_upload:
        arquivo = st.file_uploader("Importar planilha (opcional) — colunas: Aluno, Turma, Mês, Faltas", type=["csv", "xlsx"])
    with col_limpar:
        st.write("")
        st.write("")
        if st.button("🗑️ Limpar tabela", use_container_width=True):
            st.session_state["tabela_lote"] = tabela_vazia()
            st.session_state.pop("df_resultado", None)
            st.rerun()

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
    st.session_state["tabela_lote"] = tabela_editada

    col_b1, col_b2 = st.columns([1, 3])
    with col_b1:
        if st.button("➖ Apagar última linha", use_container_width=True):
            if len(st.session_state["tabela_lote"]) > 0:
                st.session_state["tabela_lote"] = st.session_state["tabela_lote"].iloc[:-1].reset_index(drop=True)
                st.session_state.pop("df_resultado", None)
                st.rerun()
    with col_b2:
        st.caption(
            "Use este botão se o ícone de lixeira do editor não estiver aparecendo na sua versão do Streamlit."
        )

    if st.button("Calcular frequência de todos os alunos", type="primary"):
        linhas = []
        for _, row in tabela_editada.iterrows():
            if pd.isna(row.get("Turma")) or pd.isna(row.get("Mês")):
                continue
            res = calcular_total_aulas(calendario, row["Turma"], row["Mês"], mapa_turmas)
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
# Aba 3: calendário / configurações
# ----------------------------------------------------------------------------
with aba_calendario:
    st.write(
        "Aqui você pode editar **tudo** o que o cálculo usa: os dias letivos de cada mês, "
        "as turmas regulares e as turmas com contraturno — direto pela tela, sem precisar "
        "mexer em nenhum arquivo. As alterações ficam valendo nesta sessão; use o botão "
        "**\"💾 Salvar no arquivo\"** para gravar de vez, ou **\"⬇️ Baixar cópia (.json)\"** "
        "para guardar uma cópia de segurança no seu computador."
    )

    with st.expander("📤 Restaurar calendário a partir de um arquivo .json", expanded=False):
        st.caption(
            "Se você baixou uma cópia antes e o app perdeu as alterações, suba aqui o arquivo "
            "para restaurar tudo de uma vez. Depois clique em **\"💾 Salvar no arquivo\"** para gravar."
        )
        json_upload = st.file_uploader(
            "Suba o arquivo calendario_2026.json", type=["json"], key="upload_calendario"
        )
        if json_upload is not None:
            try:
                novo_calendario = json.load(json_upload)
                if "dias_letivos_por_mes" not in novo_calendario or "turmas_simples" not in novo_calendario:
                    st.error("O arquivo não parece ser um calendário válido (faltam chaves obrigatórias).")
                else:
                    st.session_state["calendario"] = novo_calendario
                    st.success("Calendário carregado! Clique em 'Salvar no arquivo' abaixo para gravar no servidor.")
                    st.rerun()
            except Exception as e:
                st.error(f"Erro ao ler o JSON: {e}")

    sub_dias, sub_simples, sub_contra = st.tabs(
        ["📅 Dias letivos por mês", "🏫 Turmas regulares", "🕑 Turmas com contraturno"]
    )

    with sub_dias:
        st.caption("Edite o número de dias letivos de cada mês. Isso vale para **todas** as turmas.")
        df_dias = pd.DataFrame(
            {"Mês": meses, "Dias letivos": [calendario["dias_letivos_por_mes"].get(m, 0) for m in meses]}
        )
        df_dias_editado = st.data_editor(
            df_dias,
            use_container_width=True,
            hide_index=True,
            disabled=["Mês"],
            column_config={
                "Dias letivos": st.column_config.NumberColumn("Dias letivos", min_value=0, max_value=31, step=1)
            },
            key="editor_dias_letivos",
        )
        if st.button("Aplicar dias letivos", key="btn_aplicar_dias"):
            for _, row in df_dias_editado.iterrows():
                calendario["dias_letivos_por_mes"][row["Mês"]] = int(row["Dias letivos"])
            st.success("Dias letivos atualizados! (lembre de salvar no arquivo, se quiser manter)")
            st.rerun()

    with sub_simples:
        st.caption(
            "Turmas regulares (sem contraturno): total de aulas no mês = dias letivos × aulas por dia. "
            "Para **adicionar** uma turma, preencha a última linha em branco. Para **remover**, "
            "clique na linha e aperte Delete, ou use o ícone de lixeira. Você também pode **editar o "
            "nome da turma** diretamente na célula."
        )
        df_simples = pd.DataFrame(
            [{"Turma": k, "Aulas por dia": v["aulas_por_dia"]} for k, v in calendario["turmas_simples"].items()]
        )
        df_simples_editado = st.data_editor(
            df_simples,
            num_rows="dynamic",
            use_container_width=True,
            hide_index=True,
            column_config={
                "Aulas por dia": st.column_config.NumberColumn("Aulas por dia", min_value=0, max_value=20, step=1)
            },
            key="editor_turmas_simples",
        )
        if st.button("Aplicar turmas regulares", key="btn_aplicar_simples"):
            novas = {}
            for _, row in df_simples_editado.iterrows():
                nome = str(row.get("Turma") or "").strip()
                if not nome or pd.isna(row.get("Aulas por dia")):
                    continue
                novas[nome] = {"aulas_por_dia": int(row["Aulas por dia"])}
            calendario["turmas_simples"] = novas
            st.success("Turmas regulares atualizadas!")
            st.rerun()

    with sub_contra:
        st.caption(
            "Turmas com aula pela manhã + contraturno em dias específicos da semana (ex.: 3º ano do EM). "
            "Você escolhe quais dias da semana têm contraturno, quantas aulas há em cada um desses dias, "
            "e quantos desses dias foram letivos em cada mês — tudo editável."
        )

        turmas_contra = calendario.setdefault("turmas_contraturno", {})

        with st.expander("➕ Adicionar nova turma com contraturno"):
            novo_nome = st.text_input("Nome/código da turma (ex.: 21301, 3ºC, etc.)", key="novo_nome_contra")
            if st.button("Adicionar turma", key="btn_add_contra"):
                nome_limpo = novo_nome.strip()
                if not nome_limpo:
                    st.warning("Digite um nome para a turma.")
                elif nome_limpo in turmas_contra:
                    st.warning("Já existe uma turma com esse nome.")
                else:
                    turmas_contra[nome_limpo] = {
                        "aulas_manha_por_dia": 0,
                        "aulas_por_dia_semana": {d: 0 for d in DIAS_SEMANA},
                        "dias_letivos_por_dia_semana_por_mes": {
                            m: {d: 0 for d in DIAS_SEMANA} for m in meses
                        },
                    }
                    st.success(f"Turma '{nome_limpo}' adicionada. Configure os detalhes dela abaixo.")
                    st.rerun()

        if not turmas_contra:
            st.info("Nenhuma turma com contraturno cadastrada ainda.")

        for nome_turma in list(turmas_contra.keys()):
            info = turmas_contra[nome_turma]
            with st.expander(f"🕑 {nome_turma}", expanded=False):
                col_nome, col_remover = st.columns([3, 1])
                with col_nome:
                    novo_nome_turma = st.text_input(
                        "Nome/código da turma (pode editar para renomear)",
                        value=nome_turma,
                        key=f"nome_{nome_turma}",
                    )
                with col_remover:
                    st.write("")
                    st.write("")
                    if st.button("🗑️ Remover turma", key=f"remover_{nome_turma}"):
                        del turmas_contra[nome_turma]
                        st.success(f"Turma '{nome_turma}' removida.")
                        st.rerun()

                aulas_manha = st.number_input(
                    "Aulas pela manhã por dia letivo",
                    min_value=0, max_value=20, step=1,
                    value=int(info.get("aulas_manha_por_dia", 0)),
                    key=f"manha_{nome_turma}",
                )

                st.markdown("**Aulas no contraturno, por dia da semana**")
                st.caption("Deixe 0 nos dias em que a turma não tem contraturno.")
                aulas_semana_atual = info.get("aulas_por_dia_semana", {d: 0 for d in DIAS_SEMANA})
                cols_semana = st.columns(len(DIAS_SEMANA))
                novos_valores_semana = {}
                for col, dia in zip(cols_semana, DIAS_SEMANA):
                    with col:
                        novos_valores_semana[dia] = st.number_input(
                            DIAS_SEMANA_LABEL[dia],
                            min_value=0, max_value=20, step=1,
                            value=int(aulas_semana_atual.get(dia, 0)),
                            key=f"semana_{nome_turma}_{dia}",
                        )

                st.markdown("**Dias letivos de contraturno por mês (quantos de cada dia da semana)**")
                dias_mes_atual = info.get("dias_letivos_por_dia_semana_por_mes", {})
                df_mensal = pd.DataFrame(
                    [
                        {
                            "Mês": m,
                            **{
                                DIAS_SEMANA_LABEL[d]: dias_mes_atual.get(m, {}).get(d, 0)
                                for d in DIAS_SEMANA
                            },
                        }
                        for m in meses
                    ]
                )
                col_config_mensal = {
                    DIAS_SEMANA_LABEL[d]: st.column_config.NumberColumn(
                        DIAS_SEMANA_LABEL[d], min_value=0, max_value=6, step=1
                    )
                    for d in DIAS_SEMANA
                }
                df_mensal_editado = st.data_editor(
                    df_mensal,
                    use_container_width=True,
                    hide_index=True,
                    disabled=["Mês"],
                    column_config=col_config_mensal,
                    key=f"editor_mensal_{nome_turma}",
                )

                if st.button("💾 Aplicar alterações desta turma", key=f"aplicar_{nome_turma}"):
                    nome_final = novo_nome_turma.strip()
                    if not nome_final:
                        st.error("O nome da turma não pode ficar vazio.")
                    else:
                        if nome_final != nome_turma:
                            if nome_final in turmas_contra:
                                st.error(f"Já existe uma turma chamada '{nome_final}'. Escolha outro nome.")
                                st.stop()
                            turmas_contra[nome_final] = turmas_contra.pop(nome_turma)
                            info = turmas_contra[nome_final]

                        info["aulas_manha_por_dia"] = int(aulas_manha)
                        info["aulas_por_dia_semana"] = {d: int(novos_valores_semana[d]) for d in DIAS_SEMANA}
                        novo_mensal = {}
                        for _, row in df_mensal_editado.iterrows():
                            novo_mensal[row["Mês"]] = {
                                d: int(row[DIAS_SEMANA_LABEL[d]]) for d in DIAS_SEMANA
                            }
                        info["dias_letivos_por_dia_semana_por_mes"] = novo_mensal
                        st.success(f"Turma '{nome_final}' atualizada!")
                        st.rerun()

    st.divider()
    col_salvar, col_baixar = st.columns(2)
    with col_salvar:
        if st.button("💾 Salvar no arquivo (calendario_2026.json)", type="primary", use_container_width=True):
            try:
                salvar_calendario_no_disco()
                st.success("Configurações salvas no arquivo calendario_2026.json!")
            except Exception as e:
                st.error(
                    f"Não foi possível salvar no arquivo do servidor ({e}). "
                    "Use o botão 'Baixar cópia' ao lado para guardar suas alterações."
                )
    with col_baixar:
        st.download_button(
            "⬇️ Baixar cópia (.json)",
            data=json.dumps(calendario, ensure_ascii=False, indent=2),
            file_name="calendario_2026.json",
            mime="application/json",
            use_container_width=True,
        )
    st.caption(
        "⚠️ Em alguns tipos de hospedagem (como o Streamlit Community Cloud), o arquivo salvo no "
        "servidor pode ser perdido quando o app reinicia ou é atualizado via GitHub. Por segurança, "
        "baixe uma cópia do JSON de vez em quando e, se precisar, use o uploader acima para restaurar."
    )

st.divider()
st.caption(
    "⚠️ O percentual mínimo de frequência exigido pelo Bolsa Família (condicionalidade de educação) "
    "é geralmente de 75%. Confirme sempre as regras vigentes com a coordenação/Ministério, pois "
    "podem mudar."
)
