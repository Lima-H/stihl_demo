import streamlit as st
from apresentacao_modelo import encontrar_melhor_resposta

import uuid

# fix botões 
st.markdown(
    """
    <style>
    div[data-testid="stButton"] button {
        width: 200px;
        height: 50px;
        font-size: 18px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown("""
<style>
  .robot-cards-row { margin: 0 0 1.25rem 0; }

    .stButton > button {  
    border: 1px solid #e9e9e9 !important;  
    border-radius: 14px !important;  
    padding: 5px 8px !important; /* Padding vertical diminuído */  
    background: linear-gradient(180deg, #ffffff 0%, #fcfcfc 100%) !important;  
    box-shadow: 0 4px 9px rgba(0,0,0,0.06) !important;  
    transition: box-shadow .2s ease, transform .1s ease, border-color .2s ease !important;  
    min-height: 30px !important; /* Altura mínima diminuída */  
    font-weight: 700 !important;  
    font-size: 0.5rem !important; /* Tamanho da fonte diminuído */  
    color: #333 !important;  
    width: 50% !important;  
    margin: 0 auto !important;        /* centraliza o botão na coluna */  
    display: block !important;
  }

  .stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 12px 26px rgba(0,0,0,0.10) !important;
    border-color: #e9e9e9 !important;
  }

  /* Estilo para botão selecionado (primary) */
  .stButton > button[kind="primary"] {
    border-color: #FF7A00 !important;
    box-shadow: 0 12px 28px rgba(255,122,0,0.20) !important;
    background: linear-gradient(180deg, #fff5f0 0%, #ffeee6 100%) !important;
  }

  .stButton > button[kind="primary"]:hover {
    border-color: #FF7A00 !important;
    box-shadow: 0 12px 28px rgba(255,122,0,0.25) !important;
  }
</style>
""", unsafe_allow_html=True)

###


# CSS
st.markdown("""
<style>
    .main .block-container {
        padding-top: 1rem;
        padding-bottom: 2rem;
        max-width: 100%;
    }

    .header-container {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        margin-bottom: 3rem;
        padding: 1rem 2rem;
    }

    .logo-left, .logo-right {
        height: 50px;
        width: auto;
    }

    .title-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        text-align: center;
        margin: 2rem 0 3rem 0;
    }

    .main-title {
        font-size: 2.2rem;
        font-weight: bold;
        color: #333;
        margin: 0 0 0.5rem 0;
        letter-spacing: 1px;
    }

    .subtitle {
        font-size: 1rem;
        color: #666;
        font-style: italic;
        margin: 0;
    }
</style>
""", unsafe_allow_html=True)

# Header com logos
col1, col2, col3 = st.columns([1, 2, 1])

with col1:
    st.image("imagens/cma.jpg", width=620)

with col2:
    st.write("")

with col3:
    st.image("imagens/stihl.jpg", width=620)

# Títulos 
st.markdown("""
<div class="title-container">
    <h1 class="main-title">MAINBOT - STIHL</h1>
    <p class="subtitle">Assistente Inteligente para Manutenção</p>
</div>
""", unsafe_allow_html=True)

if "messages" not in st.session_state:
    st.session_state.messages = []

# Exibe mensagens do histórico  
for i, message in enumerate(st.session_state.messages):  
    with st.chat_message(message["role"]):  
        st.markdown(message["content"])  
          
        if message["role"] == "assistant":  
            # Exibe botão do PDF se existir (ANTES da imagem)  
            if "pdf_procedimento" in message and message["pdf_procedimento"]:  
                with open(message["pdf_procedimento"], "rb") as pdf_file:  
                    pdf_data = pdf_file.read()  
                    nome_arquivo = message["pdf_procedimento"].split("/")[-1]  
                    st.download_button(  
                        label="Visualizar Procedimento Interno",  
                        data=pdf_data,  
                        file_name=nome_arquivo,  
                        mime="application/pdf",  
                        key=f"view_pdf_hist_{i}"   # agora é garantido único pelo índice  
                    )  
              
            # Exibe imagem se existir  
            if "image_path" in message and message["image_path"]:  
                fonte_caption = f"Fonte: {message.get('fonte', 'Página do PDF relacionada')}"  
                st.image(message["image_path"], caption=fonte_caption, use_container_width=True)  
              
            # Exibe fonte se não houver imagem  
            if "fonte" in message and not message.get("image_path"):  
                st.markdown(f"**Fonte:** {message['fonte']}")

# Campo de entrada do usuário
if prompt := st.chat_input("Qual é a sua dúvida?"):
    # Adiciona mensagem do usuário
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Exibe mensagem do usuário
    with st.chat_message("user"):
        st.markdown(prompt)

    # Busca resposta
    pergunta_encontrada, resposta, caminho_imagem, fonte, pdf_procedimento = encontrar_melhor_resposta(prompt, st.session_state.robo)

    # Monta resposta do assistente
    full_response = f"**Resposta do assistente**\n\n{resposta}"

    # Salva no histórico
    st.session_state.messages.append({
        "role": "assistant", 
        "content": full_response,
        "image_path": caminho_imagem,
        "fonte": fonte,
        "pdf_procedimento": pdf_procedimento
    })

    # Exibe resposta do assistente  
    with st.chat_message("assistant"):    
        st.markdown(full_response)  

        # Exibe botão do PDF se existir (ANTES da imagem)  
        if pdf_procedimento:  
            with open(pdf_procedimento, "rb") as pdf_file:  
                pdf_data = pdf_file.read()  
                nome_arquivo = pdf_procedimento.split("/")[-1]  
                st.download_button(  
                    label="Visualizar Procedimento Interno",  
                    data=pdf_data,  
                    file_name=nome_arquivo,  
                    mime="application/pdf",  
                    key=f"view_pdf_now_{uuid.uuid4()}"   # sempre único  
                )  

        # Exibe imagem se existir   
        if caminho_imagem:    
            st.image(caminho_imagem, caption=f"Fonte: {fonte}", use_container_width=True)

if "robo" not in st.session_state:
    st.session_state.robo = "FANUC"  # padrão

st.markdown('<div class="robot-cards-row"></div>', unsafe_allow_html=True)

col_fanuc, col_abb = st.columns(2, gap="large")

with col_fanuc:
    fanuc_click = st.button(
        "Robô FANUC",
        key="btn_card_fanuc",
        type="primary" if st.session_state.robo == 'FANUC' else "secondary",
        use_container_width=True
    )

with col_abb:
    abb_click = st.button(
        "Robô ABB",
        key="btn_card_abb",
        type="primary" if st.session_state.robo == 'ABB' else "secondary",
        use_container_width=True
    )

# Atualiza seleção conforme clique
if fanuc_click:
    st.session_state.robo = "FANUC"
    st.rerun()
if abb_click:
    st.session_state.robo = "ABB"
    st.rerun()
###