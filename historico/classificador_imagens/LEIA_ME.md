# Histórico: protótipo de classificação de imagens (fases anteriores)

Estes arquivos estavam na raiz do repositório antes da Fase 7 e foram movidos para cá com `git mv`, o que preserva o histórico.

| Arquivo | O que é |
|---|---|
| `agrosmart_local.py` | Protótipo local (Keras + OpenCV + Tkinter) que classifica a imagem de uma folha em três classes (doença detectada, folha saudável, outro patógeno) e grava o resultado em CSV |
| `plant_disease_model.h5` | Modelo treinado usado pelo protótipo |
| `Img_Teste.zip` | 3 imagens de teste |
| `resultados_agrosmart.csv` | Exemplo de saída do protótipo (`Data_Hora;Nome_Imagem;Diagnostico;Confianca;Fonte_Imagem`) |

A plataforma atual **não executa** esse modelo nem faz inferência ao vivo. O formato de CSV gerado pelo protótipo é o mesmo que a plataforma lê como "Diagnósticos Históricos", independentes dos sensores (ver `02_plataforma/origens/resultados_agrosmart.csv`). Confiança registrada não é acurácia validada.
