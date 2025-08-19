import json
import re
from sentence_transformers import SentenceTransformer, util
import numpy as np
import fitz   
import os

model = SentenceTransformer('all-MiniLM-L6-v2')

def detectar_palavras_oleo_lubrificante(pergunta):
    """
    Detecta palavras relacionadas a óleo, lubrificante, graxa e litro
    incluindo variações e erros de digitação
    """
    # Padrões para detectar variações das palavras
    patterns = [
        r'(?i)\b[óo]leo[s]?\b',           # óleo, oleo, óleos, oleos
        r'(?i)\blubrificant[e]?[s]?\b',   # lubrificante, lubrificantes
        r'(?i)\bgrax[x]?[a]?[s]?\b',      # graxa, graxxa, graxas
        r'(?i)\blitro[s]?\b'              # litro, litros
    ]
    
    for pattern in patterns:
        if re.search(pattern, pergunta):
            return True
    return False

def extrair_pagina_pdf_como_imagem(pdf_path, pagina, pasta_saida="imagens_extraidas"):  
    os.makedirs(pasta_saida, exist_ok=True)  
    doc = fitz.open(pdf_path)  
    pagina_idx = pagina - 1  # índice começando em 0  
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
db_perguntas_fanuc = [item['pergunta'] for item in data if item.get('Referencia') == 'fanuc']
db_perguntas_abb = [item['pergunta'] for item in data if item.get('Referencia') == 'abb']

db_respostas = [item['resposta'] for item in data]
db_respostas_fanuc = [item['resposta'] for item in data if item.get('Referencia') == 'fanuc']
db_respostas_abb = [item['resposta'] for item in data if item.get('Referencia') == 'abb']

db_fonte_fanuc = [item['fonte'] for item in data if item.get('Referencia') == 'fanuc']
db_fonte_abb = [item['fonte'] for item in data if item.get('Referencia') == 'abb']

db_procedimento_fanuc = [item['procedimento'] for item in data if item.get('Referencia') == 'fanuc']
db_procedimento_abb = [item['procedimento'] for item in data if item.get('Referencia') == 'abb']

# Embeddings do banco de dados
embeddings_perguntas_db = model.encode(db_perguntas, convert_to_tensor=True)
embeddings_perguntas_fanuc = model.encode(db_perguntas_fanuc, convert_to_tensor=True)
embeddings_perguntas_abb = model.encode(db_perguntas_abb, convert_to_tensor=True)

# Erros SRVO
with open('falhas.json', 'r', encoding='utf-8') as f:
    db_falhas = json.load(f)

def encontrar_melhor_resposta(pergunta_usuario, tipo_pergunta):    
    melhor_pergunta = None    
    melhor_resposta = None    
    fonte = None    
    procedimento_pdf = None    
      
    # Detectar códigos FANUC (SRVO-XXX)    
    match_fanuc = re.search(r'(?i)\bSRVO[-_/ ]*(\d{1,5})\b', pergunta_usuario)
    if match_fanuc:
        numero = match_fanuc.group(1)  # pega só os dígitos
        codigo_falha = f"SRVO-{int(numero):03d}"  # força no formato SRVO-XXX (3 dígitos)

        for falha in db_falhas:
            if falha['codigo'].upper() == codigo_falha:
                melhor_pergunta = codigo_falha
                melhor_resposta = falha['resposta']
                fonte = falha.get('fonte', '')
                procedimento_pdf = falha.get('procedimento', '')
                return melhor_pergunta, melhor_resposta, None, fonte, procedimento_pdf

        return None, f"Em nosso banco de dados não existe o código {codigo_falha}", None, None, None 

    if detectar_palavras_oleo_lubrificante(pergunta_usuario):
        # Se contém essas palavras, só procurar por códigos específicos
        
        # Detectar códigos ABB (IRB XXXX)    
        match_abb = re.search(r'(?i)\bIRB[-_/ ]*(\d{3,5})\b', pergunta_usuario)  
        if match_abb:   
            codigo_encontrado = "IRB" + match_abb.group(1)  # normaliza como "IRB 2400"  
            for pergunta_abb in db_perguntas_abb:    
                if codigo_encontrado in pergunta_abb.upper():    
                    melhor_pergunta = pergunta_abb    
                    for item_completo in data:    
                        if item_completo['pergunta'].upper() == melhor_pergunta.upper():    
                            melhor_resposta = item_completo['resposta']    
                            fonte = item_completo.get('fonte', '')    
                            nome_procedimento_pdf = item_completo.get('procedimento', '')  
                            procedimento_pdf = 'imagens/' + nome_procedimento_pdf  
                            return melhor_pergunta, melhor_resposta, None, fonte, procedimento_pdf
        
        # Detectar robôs FANUC
        pattern_robot_fanuc = r'\b(?:M-?\d{1,3}i[AD](?:/\d+[LS]?)?|LRMate\s?\d{3}iD(?:/\d+[LS]?)?|SR-?\d+iA\s?SCARA)\b'
        match_robot_fanuc = re.search(pattern_robot_fanuc, pergunta_usuario, re.IGNORECASE)
        
        if match_robot_fanuc:
            codigo_robot = match_robot_fanuc.group(0).upper()
            for pergunta_fanuc in db_perguntas_fanuc:
                if codigo_robot in pergunta_fanuc.upper():
                    melhor_pergunta = pergunta_fanuc
                    for item_completo in data:  
                        if item_completo['pergunta'].upper() == melhor_pergunta.upper():  
                            melhor_resposta = item_completo['resposta']  
                            fonte = item_completo.get('fonte', '')  
                            nome_procedimento_pdf = item_completo.get('procedimento', '')  
                            procedimento_pdf = 'imagens/' + nome_procedimento_pdf
                            return melhor_pergunta, melhor_resposta, None, fonte, procedimento_pdf
        
        # Se não encontrou códigos específicos, retornar mensagem padrão
        resposta_graxa_geral =   "Em nosso banco de dados, você encontra informações detalhadas sobre lubrificantes e óleos utilizados nos robôs FANUC e ABB. Para acessar, clique no botão abaixo e siga o procedimento interno."
        procedimento_graxa_geral = "imagens/Lubrificantes_STIHL.pdf"
        return None, resposta_graxa_geral, None, None, procedimento_graxa_geral

    else:
        embedding_usuario = model.encode(pergunta_usuario, convert_to_tensor=True)
        if tipo_pergunta == "FANUC":
            cos_scores = util.pytorch_cos_sim(embedding_usuario, embeddings_perguntas_fanuc)[0]
            melhor_indice = np.argmax(cos_scores)
            melhor_score = cos_scores[melhor_indice].item()
            print(melhor_score)
            if melhor_score < 0.6:
                return None, "No momento não temos uma resposta para essa pergunta em nosso banco de dados.", None, None, None

            melhor_pergunta = db_perguntas_fanuc[melhor_indice]
            melhor_resposta = db_respostas_fanuc[melhor_indice]
            fonte = db_fonte_fanuc[melhor_indice]
            procedimento_pdf = db_procedimento_fanuc[melhor_indice]
        elif tipo_pergunta == "ABB":
            cos_scores = util.pytorch_cos_sim(embedding_usuario, embeddings_perguntas_abb)[0]
            melhor_indice = np.argmax(cos_scores)
        
            melhor_score = cos_scores[melhor_indice].item()
            print(melhor_score)
            if melhor_score < 0.6:
                return None, "No momento não temos uma resposta para essa pergunta em nosso banco de dados.", None, None, None
            
            melhor_pergunta = db_perguntas_abb[melhor_indice]
            melhor_resposta = db_respostas_abb[melhor_indice]
            fonte = db_fonte_abb[melhor_indice]
            procedimento_pdf = db_procedimento_abb[melhor_indice]
        else:
            cos_scores = util.pytorch_cos_sim(embedding_usuario, embeddings_perguntas_db)[0]
            melhor_indice = np.argmax(cos_scores)

            melhor_score = cos_scores[melhor_indice].item()
            print(melhor_score, 'No else')
            if melhor_score < 0.6:
                return None, "No momento não temos uma resposta para essa pergunta em nosso banco de dados.", None, None, None
            
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