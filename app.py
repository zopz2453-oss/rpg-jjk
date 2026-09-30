import streamlit as st
import google.generativeai as genai
import json
import os
from datetime import datetime

# Puxa a chave de segurança que você colou no 'Advanced Settings' do Streamlit
GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
genai.configure(api_key=GEMINI_API_KEY)

# Configuração da página do site
st.set_page_config(page_title="Alto Escalão Jujutsu - RPG", page_icon="🔮", layout="wide")

# Inicialização do Banco de Dados em arquivos JSON locais
def carregar_dados(arquivo, padrao):
    if not os.path.exists(arquivo):
        with open(arquivo, 'w', encoding='utf-8') as f:
            json.dump(padrao, f, ensure_ascii=False, indent=4)
    with open(arquivo, 'r', encoding='utf-8') as f:
        return json.load(f)

def salvar_dados(arquivo, dados):
    with open(arquivo, 'w', encoding='utf-8') as f:
        json.dump(dados, f, ensure_ascii=False, indent=4)

usuarios = carregar_dados('usuarios.json', {"admin": "mestre123"})
jogadores = carregar_dados('jogadores.json', {})
memorial = carregar_dados('memorial.json', [])
missoes = carregar_dados('missoes.json', [])

# Função para chamar o cérebro da IA (Alto Escalão)
def consultar_alto_escalao(prompt_sistema, comando_usuario):
    try:
        model = genai.GenerativeModel(
            model_name="gemini-1.5-pro",
            generation_config={"temperature": 0.5},
            system_instruction=prompt_sistema
        )
        response = model.generate_content(comando_usuario)
        return response.text
    except Exception as e:
        return f"Erro de comunicação com o Alto Escalão: {str(e)}"

# --- INTERFACE DE USUÁRIO ---
st.title("🔮 Sistema de Monitoramento e Diretrizes do Alto Escalão")
st.subheader("Colégio Técnico de Magia Metropolitana de Tôquio")

if 'autenticado' not in st.session_state:
    st.session_state['autenticado'] = False
    st.session_state['usuario_atual'] = ""

if not st.session_state['autenticado']:
    st.sidebar.title("🔐 Acesso ao Sistema")
    aba_login, aba_cadastro = st.sidebar.tabs(["Login", "Cadastrar"])
    
    with aba_login:
        user = st.text_input("Usuário")
        password = st.text_input("Senha", type="password")
        if st.button("Entrar"):
            if user in usuarios and usuarios[user] == password:
                st.session_state['autenticado'] = True
                st.session_state['usuario_atual'] = user
                st.rerun()
            else:
                st.error("Usuário ou senha incorretos.")
                
    with aba_cadastro:
        novo_user = st.text_input("Novo Usuário")
        nova_senha = st.text_input("Nova Senha", type="password")
        if st.button("Criar Conta"):
            if novo_user in usuarios:
                st.error("Usuário já existe.")
            elif novo_user and nova_senha:
                usuarios[novo_user] = nova_senha
                salvar_dados('usuarios.json', usuarios)
                st.success("Conta criada! Faça o login.")
    st.stop()

st.sidebar.write(f"Conectado como: **{st.session_state['usuario_atual']}**")
if st.sidebar.button("Sair da Conta"):
    st.session_state['autenticado'] = False
    st.session_state['usuario_atual'] = ""
    st.rerun()

abas = st.tabs(["👤 Fichas", "⚔️ Combate & IA", "📜 Missões", "🗄️ Consulta", "🪦 Memorial"])

# ABA 1: FICHAS
with abas[0]:
    st.header("Gerenciamento de Feiticeiros")
    with st.expander("➕ Registrar Novo Feiticeiro"):
        nome = st.text_input("Nome do Feiticeiro")
        tecnica = st.text_area("Descrição da Técnica Amaldiçoada")
        grade_inicial = st.selectbox("Grade Inicial", ["4º Grau", "3º Grau", "2º Grau", "1º Grau"])
        if st.button("Enviar para Avaliação"):
            if nome and tecnica:
                prompt_ia = "Você é o Alto Escalão de JJK. Determine: 1) Grade justa (4º a Especial), 2) XP para o próximo nível, 3) Alerta de Execução caso apele."
                resposta = consultar_alto_escalao(prompt_ia, f"Nome: {nome}. Técnica: {tecnica}.")
                jogadores[nome] = {
                    "usuario": st.session_state['usuario_atual'], "tecnica": tecnica, "grade": grade_inicial,
                    "hp_max": 100, "hp_atual": 100, "energia_amaldiçoada": 50, "xp": 0, "status": "Ativo",
                    "avaliacao_alto_escalao": resposta, "data_criacao": str(datetime.now().date())
                }
                salvar_dados('jogadores.json', jogadores)
                st.success(f"{nome} registrado!")
                st.rerun()

    if jogadores:
        for j_nome, j_dados in list(jogadores.items()):
            if j_dados["status"] == "Ativo":
                with st.container(border=True):
                    st.subheader(j_nome)
                    st.write(f"**Grau:** {j_dados['grade']} | **Técnica:** {j_dados['tecnica']}")
                    st.info(f"**Parecer:** {j_dados['avaliacao_alto_escalao']}")
                    c1, c2, c3 = st.columns(3)
                    j_dados["hp_atual"] = c1.number_input(f"HP ({j_nome})", 0, j_dados["hp_max"], j_dados["hp_atual"])
                    j_dados["energia_amaldiçoada"] = c2.number_input(f"Energia ({j_nome})", 0, 200, j_dados["energia_amaldiçoada"])
                    j_dados["xp"] = c3.number_input(f"XP ({j_nome})", 0, 10000, j_dados["xp"])
                    if st.button(f"🚨 Declarar Óbito: {j_nome}"):
                        j_dados["status"] = "Morto"
                        j_dados["causa_morte"] = "Morto em combate"
                        j_dados["data_morte"] = str(datetime.now().date())
                        memorial.append(j_dados)
                        del jogadores[j_nome]
                        salvar_dados('jogadores.json', jogadores)
                        salvar_dados('memorial.json', memorial)
                        st.rerun()

# ABA 2: COMBATE
with abas[1]:
    st.header("Simulador de Turnos")
    maldicao_alvo = st.text_input("Inimigo (Ex: Mahito)")
    hp_maldicao = st.number_input("HP Inimigo", 1, 2000, 100)
    acao_jogador = st.text_area("Ação do jogador e dados rolados:")
    if st.button("💥 Calcular Turno"):
        prompt_combate = f"Você é o sistema de regras de JJK. Calcule o dano contra {maldicao_alvo} (HP: {hp_maldicao}) e o contra-ataque."
        st.write(consultar_alto_escalao(prompt_combate, acao_jogador))

# ABA 3: MISSÕES
with abas[2]:
    st.header("Missões Oficiais")
    if st.button("🎯 Gerar Missão da IA"):
        st.info(consultar_alto_escalao("Gere uma missão de Jujutsu com cenário, Grau e XP.", "Gerar"))
    detalhes_missao = st.text_area("Relatório da missão realizada:")
    if st.button("Enviar Relatório"):
        st.write(consultar_alto_escalao("Avalie o relatório. Confisque itens perigosos ou aprove o XP.", detalhes_missao))

# ABA 4: CONSULTA
with abas[3]:
    st.header("Arquivo Secreto de Jujutsu")
    pergunta_lore = st.text_input("Dúvida sobre poderes ou choque de expansão:")
    if st.button("Pesquisar"):
        st.write(consultar_alto_escalao("Responda com base oficial no mangá de JJK.", pergunta_lore))

# ABA 5: MEMORIAL
with abas[4]:
    st.header("🪦 Memorial")
    for morto in memorial:
        st.error(f"💀 {morto.get('nome', 'Feiticeiro')} | Causa: {morto.get('causa_morte')}")
