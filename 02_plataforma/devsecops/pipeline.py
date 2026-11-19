#!/usr/bin/env python3
"""Pipeline DevSecOps do AgroSmart (Fase 7) — local (Windows/Linux/macOS) e GitHub Actions.

Etapas, em ordem: ambiente → ferramentas → qualidade (Ruff) → segurança estática (Bandit)
→ testes (Python + JS) → build da imagem → container ponta a ponta → vulnerabilidades e
configuração (Trivy) → relatório. Cada etapa registra comando, versão, início/fim, exit code,
saída bruta e decisão do gate em relatorios/<UTC>/. Nenhuma falha é mascarada: ferramenta que
não executou é "FALHA DE FERRAMENTA", nunca "aprovado".

Uso (na pasta 02_plataforma):
  python devsecops/pipeline.py                 # todas as etapas
  python devsecops/pipeline.py --etapas qualidade,seguranca,testes   # sem Docker
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import re
import shutil
import socket
import subprocess  # nosec B404 - ferramenta de CI executa comandos fixos, sem shell
import sys
import time
import urllib.error
import urllib.request
import venv
from datetime import datetime, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]          # 02_plataforma
REPO = RAIZ.parent                                  # FASE_7_AGROSMART
VENV = RAIZ / ".venv-devsecops"
REQUISITOS = RAIZ / "devsecops" / "requirements-dev.txt"

PYTHON_IMAGE_PADRAO = os.environ.get("AGROSMART_PYTHON_IMAGE", "python:3.13-slim")
TRIVY_IMAGE_PADRAO = os.environ.get("AGROSMART_TRIVY_IMAGE", "aquasec/trivy:0.76.1")
NODE_IMAGE_PADRAO = os.environ.get("AGROSMART_NODE_IMAGE", "node:24-slim")
IMAGEM_APP = "agrosmart:fase7-pipeline"
ETAPAS = ["ambiente", "ferramentas", "qualidade", "seguranca", "testes", "build", "container", "vulnerabilidades"]

# Políticas de gate (documentadas em docs/DEVSECOPS.md)
BANDIT_GATE = {"MEDIUM", "HIGH"}           # severidade E confiança ≥ MEDIUM reprova
TRIVY_GATE = {"CRITICAL", "HIGH"}          # vulnerabilidade CRITICAL/HIGH COM correção disponível reprova


def agora() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class Execucao:
    def __init__(self, pasta: Path, modo: str):
        self.pasta = pasta
        self.modo = modo
        self.etapas: list[dict] = []
        self.contexto: dict = {}
        pasta.mkdir(parents=True, exist_ok=True)

    def rodar(self, nome_arquivo: str, comando: list[str], cwd: Path = RAIZ, timeout: int = 1800,
              env: dict | None = None) -> tuple[int, str, dict]:
        inicio = time.monotonic()
        registro = {"comando": " ".join(comando), "inicio_utc": agora(), "arquivo": nome_arquivo}
        try:
            proc = subprocess.run(comando, cwd=cwd, capture_output=True, text=True, encoding="utf-8",  # nosec B603
                                  errors="replace", timeout=timeout, env=env)
            codigo, saida = proc.returncode, (proc.stdout or "") + (("\n" + proc.stderr) if proc.stderr else "")
        except FileNotFoundError as exc:
            codigo, saida = 127, f"executável não encontrado: {exc}"
        except subprocess.TimeoutExpired as exc:
            codigo, saida = 124, f"tempo limite excedido ({timeout}s): {exc}"
        registro.update({"fim_utc": agora(), "duracao_s": round(time.monotonic() - inicio, 2), "exit_code": codigo})
        (self.pasta / nome_arquivo).write_text(f"$ {registro['comando']}\n# exit_code={codigo}\n\n{saida}", encoding="utf-8")
        return codigo, saida, registro

    def etapa(self, nome: str, resultado: str, detalhes: dict, comandos: list[dict]):
        item = {"etapa": nome, "resultado": resultado, "detalhes": detalhes, "comandos": comandos}
        self.etapas.append(item)
        marca = {"APROVADO": "OK ", "REPROVADO": "XX ", "FALHA DE FERRAMENTA": "!! ", "NÃO EXECUTADO": "-- "}.get(resultado, "?? ")
        print(f"[{marca}] {nome}: {resultado} {json.dumps(detalhes, ensure_ascii=False)[:300]}", flush=True)
        return item


def python_venv() -> Path:
    return VENV / ("Scripts" if os.name == "nt" else "bin") / ("python.exe" if os.name == "nt" else "python")


def versao(comando: list[str]) -> str:
    try:
        r = subprocess.run(comando, capture_output=True, text=True, timeout=60)  # nosec B603
        if r.returncode != 0:
            return f"indisponível (exit {r.returncode})"
        return (r.stdout or r.stderr).strip().splitlines()[0] if (r.stdout or r.stderr).strip() else ""
    except (FileNotFoundError, subprocess.TimeoutExpired, IndexError):
        return "indisponível"


def _so_versao(nome: str, texto: str) -> str:
    achado = re.search(r"\d+\.\d+(\.\d+)?", texto)
    return f"{nome} {achado.group(0)}" if achado else texto


def _contar_js(saida: str) -> str:
    """Node 18 aninha os cenários num subteste por arquivo; Node 20+ lista cada um no topo."""
    aninhados = [ln for ln in saida.splitlines() if re.match(r"^\s+ok \d+ - ", ln)]
    falhos = [ln for ln in saida.splitlines() if re.match(r"^\s*not ok \d+ - ", ln)]
    if aninhados:
        return f"{len(aninhados)} cenários aprovados ({len(falhos)} reprovados)"
    return next((f"{ln.split()[2]} cenários aprovados" for ln in saida.splitlines() if ln.startswith("# pass")), "?")


# --------------------------------------------------------------------------- etapas
def etapa_ambiente(ex: Execucao):
    commit = versao(["git", "-C", str(REPO), "rev-parse", "HEAD"])
    alterado = versao(["git", "-C", str(REPO), "status", "--porcelain"]) if commit != "indisponível" else ""
    det = {
        "modo": ex.modo, "sistema": platform.platform(), "python": sys.version.split()[0],
        "node": versao(["node", "--version"]), "docker": versao(["docker", "version", "--format", "{{.Server.Version}}"]),
        "git_commit": commit, "arvore_com_alteracoes": bool(alterado and alterado != "exit 0"),
        "github_run": os.environ.get("GITHUB_RUN_ID") and f"{os.environ.get('GITHUB_REPOSITORY')}#{os.environ.get('GITHUB_RUN_ID')}",
    }
    ex.contexto.update(det)
    ex.etapa("ambiente", "APROVADO", det, [])


def etapa_ferramentas(ex: Execucao):
    comandos = []
    if not python_venv().exists():
        venv.create(VENV, with_pip=True)
    codigo, _, reg = ex.rodar("01_ferramentas_pip.txt", [str(python_venv()), "-m", "pip", "install", "--disable-pip-version-check",
                                                        "-r", str(REQUISITOS)])
    comandos.append(reg)
    det = {"ruff": versao([str(python_venv()), "-m", "ruff", "--version"]),
           "bandit": _so_versao("bandit", versao([str(python_venv()), "-m", "bandit", "--version"])), "requisitos": REQUISITOS.name}
    ex.contexto["ferramentas"] = det
    ex.etapa("ferramentas", "APROVADO" if codigo == 0 else "FALHA DE FERRAMENTA", det, comandos)


def etapa_qualidade(ex: Execucao):
    alvos = ["."] + (["../04_processos"] if (REPO / "04_processos").is_dir() else [])
    base = [str(python_venv()), "-m", "ruff", "check", "--config", "pyproject.toml", "--no-cache"]
    rel = ex.pasta / "02_ruff.json"
    c_json, _, reg1 = ex.rodar("02_ruff_execucao.txt", base + ["--output-format", "json", "--output-file", str(rel), *alvos])
    codigo, _, reg2 = ex.rodar("02_ruff.txt", base + ["--output-format", "concise", *alvos])
    try:
        achados = json.loads(rel.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        achados = None
    if achados is None or codigo not in (0, 1):
        ex.etapa("qualidade", "FALHA DE FERRAMENTA", {"exit_code": codigo}, [reg1, reg2])
        return
    ex.etapa("qualidade", "APROVADO" if codigo == 0 and not achados else "REPROVADO",
             {"ferramenta": ex.contexto.get("ferramentas", {}).get("ruff"), "achados": len(achados), "exit_code": codigo,
              "alvos": alvos, "politica": "zero achados nas regras E4,E7,E9,F,B (exceções escopadas em pyproject.toml)"}, [reg1, reg2])


def etapa_seguranca(ex: Execucao):
    rel = ex.pasta / "03_bandit.json"
    codigo, _, reg1 = ex.rodar("03_bandit_execucao.txt", [str(python_venv()), "-m", "bandit", "-c", "pyproject.toml", "-r",
                                                          "agrosmart", "main.py", "-f", "json", "-o", str(rel)])
    _, _, reg2 = ex.rodar("03_bandit.txt", [str(python_venv()), "-m", "bandit", "-c", "pyproject.toml", "-r", "agrosmart", "main.py"])
    try:
        dados = json.loads(rel.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        ex.etapa("seguranca", "FALHA DE FERRAMENTA", {"exit_code": codigo}, [reg1, reg2])
        return
    resultados = dados.get("results", [])
    bloqueantes = [r for r in resultados if r["issue_severity"] in BANDIT_GATE and r["issue_confidence"] in BANDIT_GATE]
    contagem = {}
    for r in resultados:
        chave = f"{r['test_id']}/{r['issue_severity']}"
        contagem[chave] = contagem.get(chave, 0) + 1
    erros = dados.get("errors", [])
    resultado = "FALHA DE FERRAMENTA" if erros else ("REPROVADO" if bloqueantes else "APROVADO")
    ex.etapa("seguranca", resultado, {"achados_por_regra": contagem, "bloqueantes": len(bloqueantes), "erros_da_ferramenta": len(erros),
                                      "exit_code_bandit": codigo, "linhas_analisadas": dados.get("metrics", {}).get("_totals", {}).get("loc"),
                                      "politica": "reprova severidade E confiança >= MEDIUM; LOW é reportado"}, [reg1, reg2])


def etapa_testes(ex: Execucao):
    comandos = []
    c_py, saida_py, reg = ex.rodar("04_testes_python.txt", [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"])
    comandos.append(reg)
    total_py = next((ln.split()[1] for ln in saida_py.splitlines() if ln.startswith("Ran ")), "?")
    if shutil.which("node"):
        c_chk, _, reg = ex.rodar("04_node_check.txt", ["node", "--check", "web/app.js"])
        comandos.append(reg)
        c_js, saida_js, reg = ex.rodar("04_testes_js.txt", ["node", "--test", "tests/test_frontend.cjs"])
        comandos.append(reg)
        origem_node = versao(["node", "--version"])
    elif shutil.which("docker"):
        montagem = f"{RAIZ}:/app:ro"
        c_chk, _, reg = ex.rodar("04_node_check.txt", ["docker", "run", "--rm", "-v", montagem, "-w", "/app", NODE_IMAGE_PADRAO,
                                                       "node", "--check", "web/app.js"])
        comandos.append(reg)
        c_js, saida_js, reg = ex.rodar("04_testes_js.txt", ["docker", "run", "--rm", "-v", montagem, "-w", "/app", NODE_IMAGE_PADRAO,
                                                            "node", "--test", "tests/test_frontend.cjs"])
        comandos.append(reg)
        origem_node = f"container {NODE_IMAGE_PADRAO}"
    else:
        ex.etapa("testes", "FALHA DE FERRAMENTA", {"python_exit": c_py, "motivo": "Node.js e Docker ausentes: testes JS não executados"}, comandos)
        return
    passou_js = _contar_js(saida_js)
    det = {"python": {"testes": total_py, "exit_code": c_py}, "javascript": {"aprovados": passou_js, "exit_code": c_js, "node": origem_node},
           "node_check_exit": c_chk}
    ex.etapa("testes", "APROVADO" if c_py == 0 and c_js == 0 and c_chk == 0 else "REPROVADO", det, comandos)


def _digests(imagem: str) -> list[str]:
    try:
        r = subprocess.run(["docker", "image", "inspect", imagem, "--format", "{{json .RepoDigests}}"],  # nosec B603
                           capture_output=True, text=True, timeout=60)
        return json.loads(r.stdout or "[]") if r.returncode == 0 else []
    except (FileNotFoundError, ValueError, subprocess.TimeoutExpired):
        return []


def etapa_build(ex: Execucao, python_image: str):
    comandos = []
    c_pull, _, reg = ex.rodar("05_pull_base.txt", ["docker", "pull", python_image])
    comandos.append(reg)
    c_build, _, reg = ex.rodar("05_build.txt", ["docker", "build", "--build-arg", f"PYTHON_IMAGE={python_image}",
                                                "--label", f"agrosmart.pipeline.execucao={ex.pasta.name}", "-t", IMAGEM_APP, "."])
    comandos.append(reg)
    if c_build != 0:
        ex.etapa("build", "REPROVADO" if c_pull == 0 else "FALHA DE FERRAMENTA", {"exit_code_build": c_build, "exit_code_pull": c_pull}, comandos)
        return False
    _, info, reg = ex.rodar("05_imagem_inspect.txt", ["docker", "image", "inspect", IMAGEM_APP, "--format",
                                                      "{{.Id}} {{.Size}} {{.Config.User}}"])
    comandos.append(reg)
    partes = info.split()
    c_ls, conteudo, reg = ex.rodar("05_conteudo_app.txt", ["docker", "run", "--rm", "--entrypoint", "python", IMAGEM_APP, "-c",
                                                           "import os,json;print(json.dumps(sorted(os.listdir('/app'))))"])
    comandos.append(reg)
    try:
        itens = json.loads(conteudo.strip().splitlines()[-1])
    except (ValueError, IndexError):
        itens = None
    c_pip, saida_pip, reg = ex.rodar("05_pip_ausente.txt", ["docker", "run", "--rm", "--entrypoint", "python", IMAGEM_APP, "-c",
                                                             "import importlib.util;print('pip_ausente' if importlib.util.find_spec('pip') is None else 'pip_presente')"])
    comandos.append(reg)
    pip_ausente = c_pip == 0 and "pip_ausente" in saida_pip
    esperado = ["agrosmart", "main.py", "semente", "web"]
    det = {"imagem": IMAGEM_APP, "id": partes[0] if partes else None,
           "tamanho_mb": round(int(partes[1]) / 1e6, 1) if len(partes) > 1 and partes[1].isdigit() else None,
           "usuario": partes[2] if len(partes) > 2 else None, "base": python_image, "base_digest": _digests(python_image),
           "conteudo_app": itens, "conteudo_esperado": esperado, "pip_ausente_no_runtime": pip_ausente}
    ex.contexto["imagem"] = det
    ok = itens == esperado and det["usuario"] == "agrosmart:agrosmart" and c_ls == 0 and pip_ausente
    ex.etapa("build", "APROVADO" if ok else "REPROVADO", det, comandos)
    return ok


def _porta_livre() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _http(url: str, corpo: dict | None = None, timeout: float = 10) -> tuple[int, dict]:
    dados = None if corpo is None else json.dumps(corpo).encode()
    req = urllib.request.Request(url, data=dados, method="POST" if corpo is not None else "GET",  # nosec B310 - URL local montada pelo pipeline
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:  # nosec B310
            return r.status, json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode("utf-8") or "{}")


def _aguardar(cond, limite: float, passo: float = 1.0) -> bool:
    fim = time.monotonic() + limite
    while time.monotonic() < fim:
        try:
            if cond():
                return True
        except (OSError, ValueError):
            pass
        time.sleep(passo)
    return False


def _inspect(ex: Execucao, nome: str, formato: str) -> str:
    r = subprocess.run(["docker", "inspect", nome, "--format", formato], capture_output=True, text=True, timeout=60)  # nosec B603
    return r.stdout.strip()


def etapa_container(ex: Execucao, manter: bool):
    sufixo = ex.pasta.name.lower().replace("_", "-")
    nome, volume, porta = f"agrosmart-pipeline-{sufixo}", f"agrosmart-pipeline-{sufixo}", _porta_livre()
    base = f"http://127.0.0.1:{porta}"
    comandos, verif = [], {}

    def ok(chave, valor, esperado=True):
        verif[chave] = {"obtido": valor, "aprovado": valor == esperado if not callable(esperado) else bool(esperado(valor))}

    run = ["docker", "run", "-d", "--name", nome, "-p", f"127.0.0.1:{porta}:8501", "-v", f"{volume}:/data", "--read-only",
           "--tmpfs", "/tmp", "--cap-drop", "ALL", "--security-opt", "no-new-privileges:true", "-e", "AGROSMART_EXECUCAO_CONTINUA=0", IMAGEM_APP]
    c, _, reg = ex.rodar("06_container_run.txt", run)
    comandos.append(reg)
    try:
        if c != 0:
            ex.etapa("container", "REPROVADO", {"exit_code_run": c}, comandos)
            return
        ok("http_host_pronto", _aguardar(lambda: _http(base + "/api/pronto")[0] == 200, 60))
        st, health = _http(base + "/api/health")
        ok("health_legado_200", st, 200)
        st, estado = _http(base + "/api/estado")
        ok("semente_144_leituras", estado.get("kpis", {}).get("leituras"), 144)
        st, alertas = _http(base + "/api/alertas")
        ok("alertas_109", alertas.get("total"), 109)
        st, sim = _http(base + "/api/simular", {"talhao": "Talhao A", "quantidade": 1})
        ok("post_simular_145", sim.get("pipeline", {}).get("raw_sensores"), 145)
        st, _ = _http(base + "/api/simular", {"quantidade": 99})
        ok("entrada_invalida_400", st, 400)
        st, ini = _http(base + "/api/operacao/iniciar", {"intervalo_s": 5, "eventos_por_ciclo": 3})
        ok("execucao_continua_iniciada", st, 200)
        ok("ciclos_reais_ge_2", _aguardar(lambda: _http(base + "/api/operacao")[1]["execucao_continua"]["ciclos_sucesso"] >= 2, 40))
        st, op = _http(base + "/api/operacao")
        ok("estado_funcional_atualizado", op.get("estado_funcional"), "atualizado")
        verif["operacao_snapshot"] = {"obtido": {k: op.get("execucao_continua", {}).get(k) for k in ("ciclos_total", "ciclos_sucesso", "falhas_total", "intervalo_s")},
                                      "aprovado": True}
        _, uid, reg = ex.rodar("06_exec_uid.txt", ["docker", "exec", nome, "id", "-u"])
        comandos.append(reg)
        ok("processo_sem_root", uid.strip().splitlines()[-1] if uid.strip() else "", lambda v: v not in ("", "0"))
        _, fuso, reg = ex.rodar("06_exec_fuso.txt", ["docker", "exec", nome, "python", "-c", "import time;print(time.strftime('%z'))"])
        comandos.append(reg)
        ok("fuso_america_sao_paulo", fuso.strip().splitlines()[-1] if fuso.strip() else "", "-0300")
        _, escrita, reg = ex.rodar("06_exec_raiz_somente_leitura.txt", ["docker", "exec", nome, "python", "-c",
                                   "import pathlib\ntry:\n pathlib.Path('/app/teste').write_text('x')\n print('GRAVOU')\nexcept OSError as e:\n print('NEGADO', type(e).__name__)"])
        comandos.append(reg)
        ok("raiz_somente_leitura", "NEGADO" in escrita)
        _, interno, reg = ex.rodar("06_exec_http_interno.txt", ["docker", "exec", nome, "python", "-c",
                                   "import urllib.request;print(urllib.request.urlopen('http://127.0.0.1:8501/api/pronto',timeout=5).status)"])
        comandos.append(reg)
        ok("http_dentro_do_container", interno.strip().splitlines()[-1] if interno.strip() else "", "200")
        ok("healthcheck_docker_healthy", _aguardar(lambda: _inspect(ex, nome, "{{.State.Health.Status}}") == "healthy", 90, 2))
        st, op = _http(base + "/api/operacao")
        raw_antes = op["dados"]["raw_sensores"]
        t0 = time.monotonic()
        c, _, reg = ex.rodar("06_restart.txt", ["docker", "restart", "-t", "15", nome])
        comandos.append(reg)
        verif["restart_segundos"] = {"obtido": round(time.monotonic() - t0, 2), "aprovado": c == 0 and time.monotonic() - t0 < 14}
        ok("pronto_apos_restart", _aguardar(lambda: _http(base + "/api/pronto")[0] == 200, 60))
        st, op = _http(base + "/api/operacao")
        ok("dados_persistidos_apos_restart", op["dados"]["raw_sensores"], lambda v: isinstance(v, int) and v >= raw_antes)
        _, logs1, reg = ex.rodar("06_logs_container.txt", ["docker", "logs", nome])
        comandos.append(reg)
        ok("encerramento_limpo_no_restart", "servidor encerrado" in logs1)
        ok("volume_existente_preservado", "semeado=False" in logs1 and "semeado=True" in logs1)
        t0 = time.monotonic()
        c, _, reg = ex.rodar("06_stop.txt", ["docker", "stop", "-t", "15", nome])
        comandos.append(reg)
        dur = round(time.monotonic() - t0, 2)
        ok("stop_exit_code_0", _inspect(ex, nome, "{{.State.ExitCode}}"), "0")
        verif["stop_segundos"] = {"obtido": dur, "aprovado": dur < 14}
        for origem, destino in (("/data/processos/event_log.csv", "06_event_log_container.csv"), ("/data/logs/agrosmart.log", "06_agrosmart_container.log"),
                                ("/data/operacao/ciclos.jsonl", "06_ciclos_container.jsonl")):
            c, _, reg = ex.rodar(f"06_cp_{destino}.txt", ["docker", "cp", f"{nome}:{origem}", str(ex.pasta / destino)])
            comandos.append(reg)
        _, logs2, reg = ex.rodar("06_logs_container_final.txt", ["docker", "logs", nome])
        comandos.append(reg)
        aprovado = all(v["aprovado"] for v in verif.values())
        ex.etapa("container", "APROVADO" if aprovado else "REPROVADO", {"porta_host": porta, "verificacoes": verif}, comandos)
    finally:
        if not manter:
            subprocess.run(["docker", "rm", "-f", nome], capture_output=True, timeout=120)  # nosec B603
            subprocess.run(["docker", "volume", "rm", "-f", volume], capture_output=True, timeout=120)  # nosec B603


def _contar_trivy(dados: dict) -> tuple[dict, list]:
    contagem, bloqueantes = {}, []
    for alvo in dados.get("Results", []) or []:
        for v in alvo.get("Vulnerabilities", []) or []:
            sev = v.get("Severity", "UNKNOWN")
            corrigivel = bool(v.get("FixedVersion"))
            chave = f"{sev}/{'com_correcao' if corrigivel else 'sem_correcao'}"
            contagem[chave] = contagem.get(chave, 0) + 1
            if sev in TRIVY_GATE and corrigivel:
                bloqueantes.append({"id": v.get("VulnerabilityID"), "pacote": v.get("PkgName"), "instalada": v.get("InstalledVersion"),
                                    "corrigida": v.get("FixedVersion"), "severidade": sev, "alvo": alvo.get("Target")})
    return contagem, bloqueantes


def etapa_vulnerabilidades(ex: Execucao, trivy_image: str):
    comandos = []
    c_pull, _, reg = ex.rodar("07_pull_trivy.txt", ["docker", "pull", trivy_image])
    comandos.append(reg)
    tar = ex.pasta / "imagem_agrosmart.tar"
    c_save, _, reg = ex.rodar("07_save.txt", ["docker", "save", "-o", str(tar), IMAGEM_APP])
    comandos.append(reg)
    cache = ["-v", "agrosmart-trivy-cache:/root/.cache/"]
    work = ["-v", f"{ex.pasta}:/work"]
    base = ["docker", "run", "--rm", *cache, *work, trivy_image]
    c_json, _, reg = ex.rodar("07_trivy_execucao.txt", base + ["image", "--input", "/work/imagem_agrosmart.tar", "--scanners", "vuln",
                                                              "--format", "json", "--output", "/work/07_trivy_imagem.json"], timeout=3600)
    comandos.append(reg)
    c_tab, _, reg = ex.rodar("07_trivy_imagem.txt", base + ["image", "--input", "/work/imagem_agrosmart.tar", "--scanners", "vuln", "--skip-db-update"],
                             timeout=1800)
    comandos.append(reg)
    plataforma_ro = ["-v", f"{RAIZ}:/src:ro"]
    c_cfg, _, reg = ex.rodar("07_trivy_config_execucao.txt", ["docker", "run", "--rm", *cache, *plataforma_ro, *work, trivy_image, "config",
                                                             "--format", "json", "--output", "/work/07_trivy_config.json", "/src/Dockerfile"],
                             timeout=1800)
    comandos.append(reg)
    try:
        tar.unlink()
    except OSError:
        pass
    try:
        dados = json.loads((ex.pasta / "07_trivy_imagem.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        ex.etapa("vulnerabilidades", "FALHA DE FERRAMENTA", {"exit_pull": c_pull, "exit_save": c_save, "exit_trivy": c_json,
                                                              "motivo": "relatório JSON do Trivy ausente; nenhuma conclusão sobre vulnerabilidades"}, comandos)
        return
    contagem, bloqueantes = _contar_trivy(dados)
    try:
        cfg = json.loads((ex.pasta / "07_trivy_config.json").read_text(encoding="utf-8"))
        falhas_cfg = [m for r in cfg.get("Results", []) or [] for m in (r.get("Misconfigurations") or []) if m.get("Status") == "FAIL"]
    except (OSError, ValueError):
        falhas_cfg = None
    graves_cfg = [m for m in (falhas_cfg or []) if m.get("Severity") in TRIVY_GATE]
    meta = dados.get("Metadata", {})
    det = {"scanner": trivy_image, "scanner_digest": _digests(trivy_image), "exit_code_trivy": c_json,
           "os_detectado": meta.get("OS"), "contagem": contagem, "bloqueantes": bloqueantes[:50], "total_bloqueantes": len(bloqueantes),
           "dockerfile_falhas": None if falhas_cfg is None else [f"{m.get('ID')}/{m.get('Severity')}: {m.get('Title')}" for m in falhas_cfg],
           "politica": "reprova CRITICAL/HIGH com versão corrigida disponível; demais são reportadas; Dockerfile reprova misconfig HIGH/CRITICAL"}
    if c_json != 0 or c_cfg != 0 or falhas_cfg is None:
        resultado = "FALHA DE FERRAMENTA"
    else:
        resultado = "REPROVADO" if bloqueantes or graves_cfg else "APROVADO"
    ex.etapa("vulnerabilidades", resultado, det, comandos)


# --------------------------------------------------------------------------- relatório
def escrever_relatorio(ex: Execucao, selecionadas: list[str]):
    resultados = [e["resultado"] for e in ex.etapas]
    nao_executadas = [n for n in ETAPAS if n not in {e["etapa"] for e in ex.etapas}]
    geral = "APROVADO" if all(r == "APROVADO" for r in resultados) and not nao_executadas else (
        "APROVADO (PARCIAL)" if all(r == "APROVADO" for r in resultados) else "REPROVADO")
    resumo = {"execucao": ex.pasta.name, "gerado_em_utc": agora(), "resultado_geral": geral, "etapas_selecionadas": selecionadas,
              "etapas_nao_executadas": nao_executadas, "contexto": ex.contexto, "etapas": ex.etapas}
    (ex.pasta / "resumo.json").write_text(json.dumps(resumo, ensure_ascii=False, indent=2), encoding="utf-8")
    linhas = [f"# Relatório do pipeline DevSecOps — {ex.pasta.name}", "",
              f"Resultado geral: **{geral}**  ", f"Modo: {ex.modo} · Commit: {ex.contexto.get('git_commit')} · Gerado em {resumo['gerado_em_utc']} (UTC)", "",
              "| Etapa | Resultado | Comandos (exit code) | Detalhes |", "|---|---|---|---|"]
    for e in ex.etapas:
        cmds = "<br>".join(f"`{c['arquivo']}` ({c['exit_code']}, {c['duracao_s']} s)" for c in e["comandos"]) or "—"
        det = json.dumps(e["detalhes"], ensure_ascii=False)
        linhas.append(f"| {e['etapa']} | {e['resultado']} | {cmds} | {det[:600].replace('|', '/')} |")
    if nao_executadas:
        linhas += ["", f"Etapas não executadas nesta rodada: {', '.join(nao_executadas)}."]
    linhas += ["", "Saídas brutas de cada comando estão nos arquivos desta pasta. Políticas de gate: docs/DEVSECOPS.md."]
    (ex.pasta / "RELATORIO_PIPELINE.md").write_text("\n".join(linhas) + "\n", encoding="utf-8")
    return geral


def main():
    ap = argparse.ArgumentParser(description="Pipeline DevSecOps AgroSmart Fase 7")
    ap.add_argument("--etapas", default=",".join(ETAPAS), help="lista separada por vírgula: " + ",".join(ETAPAS))
    ap.add_argument("--modo", choices=["local", "ci"], default="ci" if os.environ.get("GITHUB_ACTIONS") == "true" else "local")
    ap.add_argument("--python-image", default=PYTHON_IMAGE_PADRAO)
    ap.add_argument("--trivy-image", default=TRIVY_IMAGE_PADRAO)
    ap.add_argument("--manter-container", action="store_true", help="não remove container/volume de teste ao final")
    args = ap.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")  # consoles Windows sem UTF-8 não derrubam o pipeline
    selecionadas = [e.strip() for e in args.etapas.split(",") if e.strip()]
    desconhecidas = set(selecionadas) - set(ETAPAS)
    if desconhecidas:
        ap.error("etapas desconhecidas: " + ", ".join(sorted(desconhecidas)))
    pasta = RAIZ / "relatorios" / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    ex = Execucao(pasta, args.modo)
    print(f"Pipeline AgroSmart — relatórios em {pasta}", flush=True)
    etapa_ambiente(ex)
    precisa_ferramentas = bool({"qualidade", "seguranca"} & set(selecionadas))
    if "ferramentas" in selecionadas or precisa_ferramentas:
        etapa_ferramentas(ex)
    if "qualidade" in selecionadas:
        etapa_qualidade(ex)
    if "seguranca" in selecionadas:
        etapa_seguranca(ex)
    if "testes" in selecionadas:
        etapa_testes(ex)
    construida = False
    if {"build", "container", "vulnerabilidades"} & set(selecionadas):
        if not shutil.which("docker"):
            ex.etapa("build", "FALHA DE FERRAMENTA", {"motivo": "docker não encontrado no PATH"}, [])
        else:
            construida = etapa_build(ex, args.python_image)
    if construida and "container" in selecionadas:
        etapa_container(ex, args.manter_container)
    if construida and "vulnerabilidades" in selecionadas:
        etapa_vulnerabilidades(ex, args.trivy_image)
    geral = escrever_relatorio(ex, selecionadas)
    print(f"\nResultado geral: {geral}\nRelatório: {pasta / 'RELATORIO_PIPELINE.md'}", flush=True)
    sys.exit(0 if geral.startswith("APROVADO") else 1)


if __name__ == "__main__":
    main()
