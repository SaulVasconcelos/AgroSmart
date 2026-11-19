# Relatório do pipeline DevSecOps — 20261118T024453Z

Resultado geral: **APROVADO (PARCIAL)**  
Modo: local · Commit: 6cf04b4bca2d66b8834c01f9d687a5754dfd9c9c · Gerado em 2026-11-18T02:45:11+00:00 (UTC)

| Etapa | Resultado | Comandos (exit code) | Detalhes |
|---|---|---|---|
| ambiente | APROVADO | — | {"modo": "local", "sistema": "Linux-6.18.44-fc-v595-x86_64-with-glibc2.39", "python": "3.13.18", "node": "v22.23.4", "docker": "29.9.3", "git_commit": "6cf04b4bca2d66b8834c01f9d687a5754dfd9c9c", "arvore_com_alteracoes": false, "github_run": null} |
| ferramentas | APROVADO | `01_ferramentas_pip.txt` (0, 0.4 s) | {"ruff": "ruff 0.17.5", "bandit": "bandit 1.9.4", "requisitos": "requirements-dev.txt"} |
| qualidade | APROVADO | `02_ruff_execucao.txt` (0, 0.03 s)<br>`02_ruff.txt` (0, 0.03 s) | {"ferramenta": "ruff 0.17.5", "achados": 0, "exit_code": 0, "alvos": [".", "../04_processos"], "politica": "zero achados nas regras E4,E7,E9,F,B (exceções escopadas em pyproject.toml)"} |
| seguranca | APROVADO | `03_bandit_execucao.txt` (1, 0.29 s)<br>`03_bandit.txt` (1, 0.3 s) | {"achados_por_regra": {"B311/LOW": 4}, "bloqueantes": 0, "erros_da_ferramenta": 0, "exit_code_bandit": 1, "linhas_analisadas": 1347, "politica": "reprova severidade E confiança >= MEDIUM; LOW é reportado"} |
| testes | APROVADO | `04_testes_python.txt` (0, 5.45 s)<br>`04_node_check.txt` (0, 0.03 s)<br>`04_testes_js.txt` (0, 0.13 s) | {"python": {"testes": "44", "exit_code": 0}, "javascript": {"aprovados": "18", "exit_code": 0, "node": "v22.23.4"}, "node_check_exit": 0} |
| build | APROVADO | `05_pull_base.txt` (1, 0.35 s)<br>`05_build.txt` (0, 0.3 s)<br>`05_imagem_inspect.txt` (0, 0.05 s)<br>`05_conteudo_app.txt` (0, 0.3 s) | {"imagem": "agrosmart:fase7-pipeline", "id": "sha256:740d9478e79b8616e556dbe5258fa767e10e7b870c984a644969980960ed8574", "tamanho_mb": 198.1, "usuario": "agrosmart:agrosmart", "base": "local/base-substituta:ubuntu24-python3", "base_digest": ["local/base-substituta@sha256:3d30aab63eee66928f8cce62d910cf30e25eee41bdbd84648da2313f38746daf"], "conteudo_app": ["agrosmart", "main.py", "semente", "web"], "conteudo_esperado": ["agrosmart", "main.py", "semente", "web"]} |
| container | APROVADO | `06_container_run.txt` (0, 0.18 s)<br>`06_exec_uid.txt` (0, 0.08 s)<br>`06_exec_fuso.txt` (0, 0.08 s)<br>`06_exec_raiz_somente_leitura.txt` (0, 0.11 s)<br>`06_exec_http_interno.txt` (0, 0.13 s)<br>`06_restart.txt` (0, 0.79 s)<br>`06_logs_container.txt` (0, 0.02 s)<br>`06_stop.txt` (0, 0.66 s)<br>`06_cp_06_event_log_container.csv.txt` (0, 0.03 s)<br>`06_cp_06_agrosmart_container.log.txt` (0, 0.03 s)<br>`06_cp_06_ciclos_container.jsonl.txt` (0, 0.02 s)<br>`06_logs_container_final.txt` (0, 0.02 s) | {"porta_host": 36509, "verificacoes": {"http_host_pronto": {"obtido": true, "aprovado": true}, "health_legado_200": {"obtido": 200, "aprovado": true}, "semente_144_leituras": {"obtido": 144, "aprovado": true}, "alertas_109": {"obtido": 109, "aprovado": true}, "post_simular_145": {"obtido": 145, "aprovado": true}, "entrada_invalida_400": {"obtido": 400, "aprovado": true}, "execucao_continua_iniciada": {"obtido": 200, "aprovado": true}, "ciclos_reais_ge_2": {"obtido": true, "aprovado": true}, "estado_funcional_atualizado": {"obtido": "atualizado", "aprovado": true}, "operacao_snapshot": {"obtido |

Etapas não executadas nesta rodada: vulnerabilidades.

Saídas brutas de cada comando estão nos arquivos desta pasta. Políticas de gate: docs/DEVSECOPS.md.
