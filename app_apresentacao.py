import streamlit as st
from apresentacao_modelo import encontrar_melhor_resposta

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
for message in st.session_state.messages:
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
                        key=f"view_pdf_hist_{hash(message['content'])}"
                    )
            
            # Exibe imagem se existir (DEPOIS do botão)
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
    pergunta_encontrada, resposta, caminho_imagem, fonte, pdf_procedimento = encontrar_melhor_resposta(prompt)

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
                    mime="application/pdf"
                )
        
        # Exibe imagem se existir 
        if caminho_imagem:  
            st.image(caminho_imagem, caption=f"Fonte: {fonte}", use_container_width=True)
        
