import cv2
import numpy as np
import pandas as pd
import datetime
import os
import tkinter as tk
from tkinter import filedialog


from keras.models import load_model
from keras.utils import img_to_array

# 1. Carregando o Modelo 
caminho_modelo = 'plant_disease_model.h5'

try:
    print("Carregando o modelo de Inteligência Artificial. Aguarde...")
    model = load_model(caminho_modelo)
    print(f"Modelo '{caminho_modelo}' carregado com sucesso!\n")
except Exception as e:
    print(f"Erro ao carregar o modelo: {e}")
    print("Verifique se o arquivo .h5 foi baixado corretamente e está na mesma pasta.")
    exit()

# 2. Mapeamento de Classes
class_names = {
    0: 'Doença_Detectada (Ex: Ferrugem/Mancha)',
    1: 'Folha_Saudavel',
    2: 'Outro_Patogeno'
}

# 3. Configurando a exportação de dados para CSV
arquivo_csv = 'resultados_agrosmart.csv'
if not os.path.exists(arquivo_csv):
    df_inicial = pd.DataFrame(columns=['Data_Hora', 'Nome_Imagem', 'Diagnostico', 'Confianca', 'Fonte_Imagem'])
    df_inicial.to_csv(arquivo_csv, index=False, sep=';', encoding='utf-8')

# Função unificada para processar a imagem e salvar os dados
def processar_imagem_e_salvar(frame_imagem, fonte_origem):
    tamanho_input = (256, 256) 
    
    # Redimensiona e formata para a rede neural
    img_redimensionada = cv2.resize(frame_imagem, tamanho_input)
    img_array = img_to_array(img_redimensionada)
    img_array = np.expand_dims(img_array, axis=0)
    img_array = img_array / 255.0  # Normalização

    # Executando a Predição
    previsoes = model.predict(img_array)
    indice_classe = np.argmax(previsoes[0])
    confianca = np.max(previsoes[0]) * 100

    status_folha = class_names.get(indice_classe, f"Categoria_{indice_classe}")

    print(f"\n[RESULTADO] Diagnóstico: {status_folha} | Confiança: {confianca:.2f}%")

    # Gerando timestamps e salvando a imagem analisada
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    nome_imagem = f"captura_agro_{timestamp}.jpg"
    cv2.imwrite(nome_imagem, frame_imagem)

    # Inserindo os dados no arquivo CSV
    novo_dado = pd.DataFrame([{
        'Data_Hora': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'Nome_Imagem': nome_imagem,
        'Diagnostico': status_folha,
        'Confianca': f"{confianca:.2f}%",
        'Fonte_Imagem': fonte_origem
    }])
    
    novo_dado.to_csv(arquivo_csv, mode='a', header=False, index=False, sep=';', encoding='utf-8')
    print(f"[SISTEMA] Registro salvo no arquivo '{arquivo_csv}'.")
    
    return status_folha, confianca

# 4. Menu Principal
print("="*40)
print(" SISTEMA AGROSMART LOCAL INICIADO ")
print("="*40)
print("Como você deseja inserir a imagem para análise?")
print("[ 1 ] - Usar a Webcam ao vivo")
print("[ 2 ] - Fazer upload de um arquivo de imagem (.jpg, .png)")

opcao = input("\nDigite 1 ou 2 e pressione ENTER: ")

if opcao == '1':
    # Webcam
    cap = cv2.VideoCapture(0)
    print("\n-> Posicione a folha na frente da câmera.")
    print("-> Pressione 's' para analisar e exportar.")
    print("-> Pressione 'q' para encerrar.\n")

    while True:
        ret, frame = cap.read()
        if not ret: break

        cv2.imshow('AgroSmart - Camera', frame)
        key = cv2.waitKey(1) & 0xFF

        if key == ord('s'):
            print("\nProcessando imagem da webcam...")
            processar_imagem_e_salvar(frame, "Webcam")
        elif key == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

elif opcao == '2':
    # Upload de Arquivo
    print("\nAbrindo janela para seleção de arquivo...")
    root = tk.Tk()
    root.withdraw() # Oculta a janela principal do Tkinter
    
    # Abre o explorador de arquivos
    caminho_arquivo = filedialog.askopenfilename(
        title="Selecione uma imagem de folha",
        filetypes=[("Imagens", "*.jpg *.jpeg *.png")]
    )
    
    if caminho_arquivo:
        print(f"Arquivo selecionado: {caminho_arquivo}")
        frame = cv2.imread(caminho_arquivo)
        
        if frame is not None:
            # Processa e exibe o resultado na tela
            status, conf = processar_imagem_e_salvar(frame, "Upload Local")
            
            # Mostra a imagem estática com o texto do resultado
            texto_resultado = f"{status} ({conf:.1f}%)"
            cv2.putText(frame, texto_resultado, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
            cv2.imshow('AgroSmart - Resultado da Analise', frame)
            
            print("\nPressione qualquer tecla na janela da imagem para encerrar.")
            cv2.waitKey(0)
            cv2.destroyAllWindows()
        else:
            print("Erro ao ler a imagem. Arquivo corrompido ou formato inválido.")
    else:
        print("Nenhum arquivo foi selecionado. Encerrando.")

else:
    print("Opção inválida. Reinicie o programa e escolha 1 ou 2.")