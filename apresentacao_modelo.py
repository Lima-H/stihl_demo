import json
import re
from sentence_transformers import SentenceTransformer, util
import numpy as np
import fitz  # PyMuPDF  
import os

model = SentenceTransformer('all-MiniLM-L6-v2')

def extrair_pagina_pdf_como_imagem(pdf_path, pagina, pasta_saida="imagens_extraidas"):  
    os.makedirs(pasta_saida, exist_ok=True)  
    doc = fitz.open(pdf_path)  
    pagina_idx = pagina - 1  # PyMuPDF usa índice começando em 0  
    if pagina_idx < 0 or pagina_idx >= len(doc):  
        raise ValueError("Página fora do intervalo do PDF.")  
    page = doc.load_page(pagina_idx)  
    pix = page.get_pixmap(dpi=200)  
    nome_arquivo = f"{os.path.splitext(os.path.basename(pdf_path))[0]}_pagina_{pagina}.png"  
    caminho_saida = os.path.join(pasta_saida, nome_arquivo)  
    pix.save(caminho_saida)  
    return caminho_saida

def extrair_pdf_e_pagina(fonte):
    match = re.match(r"(.+\.pdf), página: (\d+)", fonte)
    if match:
        pdf, pagina = match.groups()
        return pdf.strip(), int(pagina)
    return None, None

with open('apresentacao_respostas.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

db_perguntas = [item['pergunta'] for item in data]
db_respostas = [item['resposta'] for item in data]

# Embeddings do banco de dados
embeddings_perguntas_db = model.encode(db_perguntas, convert_to_tensor=True)

def encontrar_melhor_resposta(pergunta_usuario):    
    embedding_usuario = model.encode(pergunta_usuario, convert_to_tensor=True)
    cos_scores = util.pytorch_cos_sim(embedding_usuario, embeddings_perguntas_db)[0]
    melhor_indice = np.argmax(cos_scores)
    melhor_pergunta = db_perguntas[melhor_indice]
    melhor_resposta = db_respostas[melhor_indice]
    fonte = data[melhor_indice].get("fonte", "")
    procedimento_pdf = data[melhor_indice].get("procedimento", "")
    
    caminho_imagem = None
    caminho_pdf_procedimento = None
    
    # Extrai imagem usando o campo "fonte"
    if fonte:
        pdf_nome, pagina = extrair_pdf_e_pagina(fonte)
        if pdf_nome and pagina:
            caminho_pdf = os.path.join("imagens", pdf_nome)
            try:
                caminho_imagem = extrair_pagina_pdf_como_imagem(caminho_pdf, pagina)
            except Exception as e:
                print(f"Erro ao extrair imagem: {e}")
    
    # lógica do procedimento
    if procedimento_pdf:
        caminho_pdf_procedimento = os.path.join("imagens", procedimento_pdf)
        if not os.path.exists(caminho_pdf_procedimento):
            caminho_pdf_procedimento = None
    
    return melhor_pergunta, melhor_resposta, caminho_imagem, fonte, caminho_pdf_procedimento