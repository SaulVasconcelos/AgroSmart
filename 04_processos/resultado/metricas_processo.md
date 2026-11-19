# Resultado da análise do event log (gerado automaticamente)

Fontes: event_log.csv  
Janela: 2026-11-18T02:33:23.715462+00:00 → 2026-11-18T02:35:00.699251+00:00 (UTC)  
Eventos: 600 · Casos: 40 · Variantes: 8  
Resultados: {'Execução concluída': 34, 'Entrada rejeitada': 6}

Percentis por posto mais próximo; durações de atividade medidas com relógio monotônico; ponta a ponta = último − primeiro timestamp do caso.

## Por gatilho

| Gatilho | Casos | Resultados | Ponta a ponta mediana (ms) | p95 (ms) | Conformes ao esperado |
|---|---:|---|---:|---:|---|
| api_importar_observacoes | 3 | {'Execução concluída': 1, 'Entrada rejeitada': 2} | 0.788 | 22.714 | 1/3 |
| api_simular | 14 | {'Execução concluída': 11, 'Entrada rejeitada': 3} | 30.056 | 134.921 | 11/14 |
| cli_importar_sensores | 2 | {'Execução concluída': 1, 'Entrada rejeitada': 1} | 14.675 | 28.378 | 0/2 |
| cli_processar | 1 | {'Execução concluída': 1} | 26.8 | 26.8 | 1/1 |
| execucao_continua | 20 | {'Execução concluída': 20} | 25.236 | 30.144 | 20/20 |

## Variantes

| # | Casos | % | Sequência de atividades |
|---:|---:|---:|---|
| 1 | 20 | 50.0 | Entrada recebida → Gerar leituras simuladas → Validar dados de entrada → Aguardar trava de escrita → Persistir Raw → Publicar Trusted → Aplicar regras R1–R7 → Publicar Refined → Execução concluída |
| 2 | 11 | 27.5 | Entrada recebida → Validar requisição → Gerar leituras simuladas → Validar dados de entrada → Aguardar trava de escrita → Persistir Raw → Publicar Trusted → Aplicar regras R1–R7 → Publicar Refined → Resposta entregue → Execução concluída |
| 3 | 3 | 7.5 | Entrada recebida → Validar requisição → Resposta entregue → Entrada rejeitada |
| 4 | 2 | 5.0 | Entrada recebida → Validar requisição → Validar dados de entrada → Resposta entregue → Entrada rejeitada |
| 5 | 1 | 2.5 | Entrada recebida → Validar requisição → Validar dados de entrada → Aguardar trava de escrita → Persistir Raw → Publicar Trusted → Aplicar regras R1–R7 → Publicar Refined → Resposta entregue → Execução concluída |
| 6 | 1 | 2.5 | Entrada recebida → Validar dados de entrada → Persistir Raw → Publicar Trusted → Descartar duplicatas → Aplicar regras R1–R7 → Publicar Refined → Execução concluída |
| 7 | 1 | 2.5 | Entrada recebida → Validar dados de entrada → Entrada rejeitada |
| 8 | 1 | 2.5 | Entrada recebida → Publicar Trusted → Aplicar regras R1–R7 → Publicar Refined → Execução concluída |

## Atividades com duração medida

| Atividade | n | Média (ms) | Mediana (ms) | p95 (ms) | Máx (ms) | % do tempo medido |
|---|---:|---:|---:|---:|---:|---:|
| Publicar Trusted | 34 | 15.717 | 14.703 | 19.812 | 25.567 | 49.2 |
| Aguardar trava de escrita | 32 | 9.098 | 0.001 | 72.415 | 93.031 | 26.8 |
| Publicar Refined | 34 | 6.503 | 6.514 | 8.843 | 9.503 | 20.3 |
| Aplicar regras R1–R7 | 34 | 0.847 | 0.838 | 1.152 | 1.676 | 2.7 |
| Persistir Raw | 33 | 0.186 | 0.123 | 0.465 | 1.438 | 0.6 |
| Gerar leituras simuladas | 31 | 0.119 | 0.033 | 1.229 | 1.244 | 0.3 |
| Validar dados de entrada | 36 | 0.032 | 0.025 | 0.085 | 0.1 | 0.1 |
| Validar requisição | 17 | 0.023 | 0.02 | 0.075 | 0.075 | 0.0 |

## Publicar Trusted × tamanho do Raw

n=34; registros de 147.0 a 232.0; r de Pearson=0.281; inclinação=0.027207 ms/registro.

## Grafo diretamente-segue (observado)

| De | Para | Contagem | Intervalo médio (ms) |
|---|---|---:|---:|
| Aplicar regras R1–R7 | Publicar Refined | 34 | 6.704 |
| Persistir Raw | Publicar Trusted | 33 | 15.872 |
| Publicar Trusted | Aplicar regras R1–R7 | 33 | 1.103 |
| Validar dados de entrada | Aguardar trava de escrita | 32 | 9.293 |
| Aguardar trava de escrita | Persistir Raw | 32 | 0.37 |
| Gerar leituras simuladas | Validar dados de entrada | 31 | 0.366 |
| Publicar Refined | Execução concluída | 22 | 0.356 |
| Entrada recebida | Gerar leituras simuladas | 20 | 0.526 |
| Entrada recebida | Validar requisição | 17 | 2.881 |
| Publicar Refined | Resposta entregue | 12 | 1.057 |
| Resposta entregue | Execução concluída | 12 | 0.38 |
| Validar requisição | Gerar leituras simuladas | 11 | 1.505 |
| Resposta entregue | Entrada rejeitada | 5 | 0.064 |
| Validar requisição | Resposta entregue | 3 | 0.255 |
| Validar requisição | Validar dados de entrada | 3 | 0.171 |
| Validar dados de entrada | Resposta entregue | 2 | 0.227 |
| Entrada recebida | Validar dados de entrada | 2 | 0.647 |
| Validar dados de entrada | Persistir Raw | 1 | 0.221 |
| Publicar Trusted | Descartar duplicatas | 1 | 0.158 |
| Descartar duplicatas | Aplicar regras R1–R7 | 1 | 1.074 |
| Validar dados de entrada | Entrada rejeitada | 1 | 0.079 |
| Entrada recebida | Publicar Trusted | 1 | 18.574 |
