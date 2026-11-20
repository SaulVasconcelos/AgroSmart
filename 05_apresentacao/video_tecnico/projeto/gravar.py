"""Grava as cenas do vídeo final técnico do AgroSmart (Fase 7).

Tudo é capturado de uma tela virtual de 1920 x 1080: Chromium com janela (a plataforma real e os arquivos do
repositório), xterm (comandos reais digitados) e o ffmpeg gravando a tela. Os instantes das ações seguem a
duração de cada fala da narração (tempos_falas.json e frases_*.json).

Uso: python gravar.py [c1 c2 ...]   (sem argumentos, grava as 8 cenas na ordem)
Pré-requisito das cenas c3 a c5: plataforma no ar em container, execução contínua parada e Talhão B em ND (prep.py).
"""
import json
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

from playwright.sync_api import sync_playwright

import infra

AQUI = Path(__file__).resolve().parent
SAIDA = AQUI / "cenas"
SAIDA.mkdir(exist_ok=True)
TEMPOS = json.loads((AQUI / "tempos_falas.json").read_text(encoding="utf-8"))
FRASES = json.loads((AQUI / "frases_parte1.wav.json").read_text(encoding="utf-8")) + json.loads((AQUI / "frases_parte2.wav.json").read_text(encoding="utf-8"))
DUR = {(t["cena"], t["fala"]): t["fim"] - t["ini"] for t in TEMPOS}
INI = {(t["cena"], t["fala"]): t["ini"] for t in TEMPOS}
PLAT = infra.REPO / "02_plataforma"


def frase(cena, fala, i):
    """Início da i-ésima frase da fala, em segundos a partir do começo da fala."""
    fs = [f for f in FRASES if f["cena"] == cena and f["fala"] == fala]
    return fs[i]["ini"] - INI[(cena, fala)]


def api(caminho, corpo=None):
    d = None if corpo is None else json.dumps(corpo).encode()
    r = urllib.request.Request(infra.PLATAFORMA + caminho, data=d, method="GET" if d is None else "POST", headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(r, timeout=30) as x:
        return json.loads(x.read())


NAV = "aside button.nav-item[data-tab={}]"
REGISTRO = {"atrasos": {}, "falas": {}, "duracao": {}, "observado": {}}


class Cena:
    def __init__(self, nome, falas, duracao):
        self.nome, self.falas, self.duracao = nome, falas, duracao
        self.g = infra.Gravador(SAIDA / f"{nome}_bruto.mkv")
        self.atrasos = []

    def __enter__(self):
        self.g.iniciar()
        return self

    def ate(self, t, rotulo=""):
        atraso = self.g.ate(t)
        if atraso > 0.25:
            self.atrasos.append((rotulo or f"{t:.1f}", round(atraso, 2)))

    def __exit__(self, tipo, valor, tb):
        if tipo is None:
            self.g.parar(self.duracao, SAIDA / f"{self.nome}.mp4")
            REGISTRO["atrasos"][self.nome] = self.atrasos
            REGISTRO["falas"][self.nome] = {str(k): round(v, 3) for k, v in self.falas.items()}
            REGISTRO["duracao"][self.nome] = self.duracao
            print(f"{self.nome}: {self.duracao:.1f}s gravados; atrasos: {self.atrasos}", flush=True)
        else:
            self.g.p.kill()


# ------------------------------------------------------------------------------------------- cenas
def c1(n):
    n.abrir(infra.doc("README.md"))
    n.mover(1150, 330, 0.3)
    f0 = 1.0
    with Cena("c1", {0: f0}, f0 + DUR[("c1", 0)] + 1.0) as c:
        c.ate(f0 + frase("c1", 0, 1) + 0.6)
        n.rolar(150, 5.5)
        c.ate(f0 + frase("c1", 0, 2) - 0.5)
        n.apontar("blockquote", 0.9, dx=0.12)
        c.ate(f0 + frase("c1", 0, 2) + 2.2)
        n.apontar("blockquote", 1.4, dx=0.62)


def _fig(n, fx, fy, dur=0.9):
    b = n.pag.locator("#figura").bounding_box()
    alt = n.pag.evaluate("innerHeight")
    y = b["y"] + b["height"] * fy
    if y > alt - 110 or y < 120:
        n.rolar(y - alt * 0.55, 0.9)
        b = n.pag.locator("#figura").bounding_box()
        y = b["y"] + b["height"] * fy
    n.mover(b["x"] + b["width"] * fx, y, dur)


def c2(n):
    n.abrir(infra.doc("01_arquitetura/arquitetura_final.png", larg=1380))
    n.pag.mouse.wheel(0, 40)
    n.mover(1380, 200, 0.3)
    f0 = 1.0
    s = lambda i: f0 + frase("c2", 0, i)   # noqa: E731
    with Cena("c2", {0: f0}, f0 + DUR[("c2", 0)] + 1.0) as c:
        c.ate(s(0) + 0.8)
        _fig(n, 0.10, 0.115, 0.9)
        _fig(n, 0.42, 0.115, 1.6)
        c.ate(s(1) + 0.2, "entradas")
        _fig(n, 0.10, 0.195, 0.9)
        c.ate(s(1) + 2.0)
        _fig(n, 0.24, 0.195, 1.2)
        c.ate(s(1) + 4.6)
        _fig(n, 0.38, 0.195, 0.9)
        c.ate(s(2) + 0.2, "validação")
        _fig(n, 0.20, 0.30, 0.9)
        c.ate(s(2) + 2.8)
        _fig(n, 0.56, 0.30, 1.0)
        c.ate(s(3) + 0.1, "raw")
        _fig(n, 0.30, 0.395, 0.9)
        c.ate(s(4) + 0.2, "trusted")
        _fig(n, 0.19, 0.49, 0.9)
        c.ate(s(5) + 0.2, "regras")
        _fig(n, 0.56, 0.49, 1.0)
        c.ate(s(5) + 4.2)
        _fig(n, 0.36, 0.59, 1.0)
        c.ate(s(6) + 0.2, "saída")
        _fig(n, 0.16, 0.69, 0.9)
        c.ate(s(6) + 1.6)
        _fig(n, 0.44, 0.69, 0.9)
        c.ate(s(6) + 3.4)
        _fig(n, 0.65, 0.69, 0.9)
        c.ate(s(7) + 0.2, "observabilidade")
        _fig(n, 0.86, 0.20, 1.1)
        c.ate(s(7) + 2.4)
        _fig(n, 0.86, 0.40, 1.0)
        c.ate(s(8) - 0.3, "pipeline")
        _fig(n, 0.22, 0.86, 1.0)
        _fig(n, 0.88, 0.86, 2.2)


def c3(n):
    t = infra.Terminal(PLAT)
    time.sleep(0.8)
    f0 = 1.0
    f1 = f0 + DUR[("c3", 0)] + 0.9
    try:
        with Cena("c3", {0: f0, 1: f1}, f1 + DUR[("c3", 1)] + 1.4) as c:
            c.ate(0.5)
            t.comando("docker compose up -d", 55)
            c.ate(f0 + frase("c3", 0, 1) + 0.2, "inspect")
            t.comando("docker inspect -f 'usuario={{.Config.User}}  raiz_somente_leitura={{.HostConfig.ReadonlyRootfs}}  volume={{range .Mounts}}{{.Destination}}{{end}}' agrosmart-agrosmart-1", 22)
            c.ate(f0 + frase("c3", 0, 2) + 0.2, "ps")
            t.comando("docker compose ps --format 'table {{.Name}}\\t{{.Status}}\\t{{.Ports}}'", 30)
            c.ate(f1 + 0.3, "imagens")
            t.comando("docker image ls", 55)
            c.ate(f1 + frase("c3", 1, 1) - 0.4, "dockerfile")
            t.comando("grep -n PYTHON_IMAGE Dockerfile", 45)
    finally:
        t.fechar()


def c4(n):
    csv_obs = infra.REPO / "05_apresentacao" / "observacao_demo.csv"
    _t = api("/api/talhao?talhao=Talhao+B")
    antes = _t.get("leitura_selecionada") or _t["ultima_leitura"]
    assert antes["regra"] == "ND" and float(antes["umidade_solo"]) >= 35, antes
    n.abrir(infra.PLATAFORMA + "/", 1.5)
    n.mover(900, 250, 0.3)
    f0, f1, f2, f3, f4, f5 = 1.0, 8.9, 22.0, 35.6, 44.9, 65.6
    with Cena("c4", {0: f0, 1: f1, 2: f2, 3: f3, 4: f4, 5: f5}, f5 + DUR[("c4", 5)] + 2.4) as c:
        # a) Visão Geral
        c.ate(f0 + frase("c4", 0, 1) - 0.2)
        for i in range(3):
            n.apontar(f"#priorityList .priority-row >> nth={i}", 0.8, dx=0.10 + 0.28 * i)
            time.sleep(0.35)
        # b) gerar uma leitura
        c.ate(f1 - 1.0, "pipeline")
        n.clicar(NAV.format("pipeline"))
        c.ate(f1 + 0.9)
        n.apontar("#sTalhao", 0.6)
        n.pag.select_option("#sTalhao", label="Talhao A")
        c.ate(f1 + 1.9)
        n.apontar("#sQuantidade", 0.5)
        n.pag.select_option("#sQuantidade", "1")
        c.ate(f1 + 2.9, "gerar")
        n.clicar("#btnSimular", 0.5)
        n.pag.wait_for_function("document.querySelector('#simMensagem').innerText.includes('gerada')", timeout=8000)
        REGISTRO["observado"]["mensagem_simulacao"] = n.pag.inner_text("#simMensagem")
        c.ate(f1 + 4.6)
        n.rolar(240, 1.0)
        n.apontar("#sampleJSON", 0.7, dx=0.3)
        c.ate(f1 + frase("c4", 1, 2) - 0.5, "auditoria")
        n.apontar("#pipelineStats", 0.9, dx=0.35, dy=0.2)
        time.sleep(0.5)
        n.apontar("#pipelineStats", 1.2, dx=0.35, dy=0.8)
        # c) Talhão B indeterminado
        c.ate(f2 - 1.5, "talhões")
        n.clicar(NAV.format("talhoes"))
        c.ate(f2 + 0.3)
        n.clicar("#plotCards a[data-talhao='Talhao B']", 0.8)
        n.pag.wait_for_selector(".panel.current-reading", timeout=8000)
        c.ate(f2 + 2.0)
        n.apontar(".current-reading .reading-heading .badge", 0.8)
        REGISTRO["observado"]["cartao_antes"] = n.pag.inner_text(".panel.current-reading")
        c.ate(f2 + frase("c4", 2, 1) + 0.3)
        n.apontar(".current-reading .field-evidence", 0.9, dx=0.3)
        c.ate(f2 + frase("c4", 2, 2) - 0.3, "orientação")
        n.apontar(".current-reading .recommendation", 0.9, dx=0.3, dy=0.35)
        # d) importar a observação de campo
        c.ate(f3 - 1.3, "pipeline 2")
        n.clicar(NAV.format("pipeline"))
        n.rolar_ate("#inputCSV", 330, 0.9)
        c.ate(f3 + 1.3)
        n.apontar("#inputCSV", 0.7, dx=0.12)
        n.pag.set_input_files("#inputCSV", str(csv_obs))
        c.ate(f3 + 3.2, "importar")
        n.clicar("#btnImportar", 0.6)
        n.pag.wait_for_function("document.querySelector('#uploadFeedback').innerText.includes('conclu')", timeout=8000)
        REGISTRO["observado"]["mensagem_importacao"] = n.pag.inner_text("#uploadFeedback")
        c.ate(f3 + 4.6)
        n.apontar("#uploadFeedback", 0.6, dx=0.2)
        # e) a mesma leitura, reavaliada
        c.ate(f4 - 1.5, "talhões 2")
        n.clicar(NAV.format("talhoes"))
        n.pag.wait_for_selector(".panel.current-reading", timeout=8000)
        c.ate(f4 + 0.3)
        n.apontar(".current-reading .reading-heading .badge", 0.8)
        REGISTRO["observado"]["cartao_depois"] = n.pag.inner_text(".panel.current-reading")
        c.ate(f4 + frase("c4", 4, 1) + 0.6, "R2")
        n.apontar(".current-reading > p.small-note", 0.8, dx=0.12)
        c.ate(f4 + frase("c4", 4, 1) + 3.4)
        n.apontar(".current-reading .field-evidence", 0.9, dx=0.3, dy=0.6)
        c.ate(f4 + frase("c4", 4, 1) + 6.2)
        n.apontar(".current-reading .recommendation", 0.9, dx=0.3, dy=0.35)
        c.ate(f4 + frase("c4", 4, 1) + 8.4, "justificativa")
        n.clicar(".current-reading details.origin summary", 0.8)
        # f) Central de Alertas
        c.ate(f5 - 1.2, "alertas")
        n.clicar(NAV.format("alertas"))
        c.ate(f5 + 0.2)
        n.apontar("#fSeveridade", 0.6)
        n.pag.select_option("#fSeveridade", label="Alta")
        time.sleep(0.5)
        hoje = time.strftime("%d/%m/%Y")
        alvo = f"#alertList details:has-text('{hoje}'):has-text('R2')"
        n.pag.wait_for_selector(alvo, timeout=5000)
        n.apontar(alvo + " >> summary", 0.8, dx=0.2)
        REGISTRO["observado"]["ocorrencia_hoje"] = n.pag.locator(alvo).first.inner_text()[:400]
    _t = api("/api/talhao?talhao=Talhao+B")
    depois = _t.get("leitura_selecionada") or _t["ultima_leitura"]
    campos = ["data_hora", "sensor_id", "regra", "severidade", "alerta", "acao", "avaliacao", "umidade_solo", "temperatura",
              "percentual_folhas_doentes", "praga_detectada", "dias_mesma_praga"]
    REGISTRO["observado"]["leitura_antes"] = {k: antes.get(k) for k in campos}
    REGISTRO["observado"]["leitura_depois"] = {k: depois.get(k) for k in campos}


def c5(n):
    n.abrir(infra.PLATAFORMA + "/#pipeline", 1.5)
    n.pag.locator("#painelOperacao").scroll_into_view_if_needed()
    n.pag.mouse.move(900, 400)
    n.rolar_ate("#painelOperacao", 95, 0.5)
    n.mover(1100, 300, 0.3)
    f0 = 1.0
    troca = f0 + DUR[("c5", 0)] + 0.7
    f1 = troca + 1.0
    t = None
    try:
        with Cena("c5", {0: f0, 1: f1}, f1 + DUR[("c5", 1)] + 3.2) as c:
            c.ate(1.2)
            n.apontar("#oIntervalo", 0.6)
            n.pag.select_option("#oIntervalo", "15")
            c.ate(2.6, "iniciar")
            n.clicar("#btnOperacaoIniciar", 0.6)
            c.ate(4.6)
            n.apontar("#operacaoMensagem", 0.7, dx=0.2)
            REGISTRO["observado"]["mensagem_operacao"] = n.pag.inner_text("#operacaoMensagem")
            c.ate(f0 + frase("c5", 0, 2) - 0.2, "painel")
            n.apontar("#operacaoStatus", 0.9, dx=0.3, dy=0.12)
            c.ate(f0 + frase("c5", 0, 2) + 2.2)
            n.apontar("#operacaoStatus", 1.2, dx=0.3, dy=0.75)
            c.ate(f0 + frase("c5", 0, 2) + 4.6)
            n.clicar("#btnOperacaoAtualizar", 0.8)
            n.apontar("#operacaoCiclos", 0.9, dx=0.4, dy=0.4)
            REGISTRO["observado"]["painel_operacao"] = n.pag.inner_text("#operacaoStatus")
            c.ate(troca, "terminal")
            t = infra.Terminal(PLAT)
            c.ate(f1 - 0.2)
            t.comando("python3 main.py monitorar --url http://127.0.0.1:8517 --intervalo 5 --vezes 3", 26)
            c.ate(f1 + 13.4, "logs")
            t.comando("docker compose logs --tail 6 --no-log-prefix", 30)
    finally:
        if t:
            t.fechar()
    REGISTRO["observado"]["operacao_depois"] = api("/api/operacao")["execucao_continua"]


def c6(n):
    rel = next((infra.REPO / "03_evidencias/devsecops_ci").glob("*_github_actions_aprovado/RELATORIO_PIPELINE.md")).relative_to(infra.REPO).as_posix()
    n.abrir(infra.doc(rel))
    n.mover(1180, 300, 0.3)
    f0 = 1.0
    f1 = f0 + DUR[("c6", 0)] + 1.6
    with Cena("c6", {0: f0, 1: f1}, f1 + DUR[("c6", 1)] + 1.2) as c:
        c.ate(f0 + 1.5)
        n.apontar("p:has-text('Resultado geral')", 0.9, dx=0.12)
        c.ate(f0 + frase("c6", 0, 1) - 0.4, "etapas")
        n.rolar_ate("table", 150, 0.9)
        linhas = n.pag.locator("table tbody tr")
        t_ini = f0 + frase("c6", 0, 2)
        passo = (DUR[("c6", 0)] - frase("c6", 0, 2) - 0.5) / 6
        for k, i in enumerate([2, 3, 4, 5, 6, 7]):          # qualidade, segurança, testes, build, container, vulnerabilidades
            c.ate(t_ini + passo * k + 0.2)
            b = linhas.nth(i).bounding_box()
            alt = n.pag.evaluate("innerHeight")
            if b["y"] + 30 > alt - 90:
                n.rolar(b["y"] - alt * 0.5, 0.7)
                b = linhas.nth(i).bounding_box()
            n.mover(b["x"] + 70, b["y"] + min(26, b["height"] / 2), 0.7)
        c.ate(f1 - 1.1, "equipe")
        n.abrir(infra.doc("03_evidencias/devsecops_equipe/LEIA_ME.md"), 0.3)
        c.ate(f1 + 0.3)
        n.apontar("h2:has-text('Execução 1')", 0.8, dx=0.3)
        c.ate(f1 + frase("c6", 1, 1) - 0.2, "achados")
        n.rolar_ate("tr:has-text('Trivy, imagem')", 200, 0.9)
        n.apontar("tr:has-text('Trivy, imagem')", 0.8, dx=0.6)
        c.ate(f1 + frase("c6", 1, 2) - 0.6, "correção")
        n.rolar_ate("h3:has-text('Achados bloqueantes')", 130, 0.9)
        n.apontar("tr:has-text('zlib1g') td >> nth=3", 0.8, dx=0.3)
        c.ate(f1 + frase("c6", 1, 2) + 2.6)
        n.apontar("tr:has-text('msgpack') td >> nth=3", 0.8, dx=0.3)
        c.ate(f1 + frase("c6", 1, 3) - 0.7, "execução 3")
        n.rolar_ate("h2:has-text('Execução 3')", 130, 1.0)
        n.apontar("h2:has-text('Execução 3')", 0.7, dx=0.45)
        c.ate(f1 + frase("c6", 1, 4) - 0.2, "47")
        n.apontar("tr:has-text('Trivy 0.76.1') td >> nth=1", 0.9, dx=0.5, dy=0.6)


def c7(n):
    n.abrir(infra.doc("04_processos/coleta/event_log.csv"))
    n.mover(700, 330, 0.3)
    f0 = 1.0
    f1 = f0 + DUR[("c7", 0)] + 1.6
    f2 = f1 + DUR[("c7", 1)] + 1.7
    f3 = f2 + DUR[("c7", 2)] + 0.7
    f4 = f3 + DUR[("c7", 3)] + 0.7
    with Cena("c7", {0: f0, 1: f1, 2: f2, 3: f3, 4: f4}, f4 + DUR[("c7", 4)] + 1.4) as c:
        c.ate(f0 + 0.8)
        n.apontar("table.csv th >> nth=4", 0.8)            # activity
        c.ate(f0 + 3.0)
        n.apontar("table.csv th >> nth=6", 0.7)            # timestamp
        c.ate(f0 + 4.6)
        n.apontar("table.csv th >> nth=8", 0.7)            # duration_ms
        c.ate(f0 + frase("c7", 0, 1) - 0.3, "rolar log")
        n.rolar(1500, DUR[("c7", 0)] - frase("c7", 0, 1) - 0.4)
        c.ate(f1 - 1.1, "processo")
        n.abrir(infra.doc("04_processos/resultado/processo_observado.png", larg=820), 0.3)
        n.mover(1250, 300, 0.3)
        c.ate(f1 + 0.6)
        n.rolar(700, DUR[("c7", 1)] - 1.2)
        c.ate(f2 - 1.2, "análise")
        n.abrir(infra.doc("04_processos/ANALISE_PROCESSO.md"), 0.2)
        n.pag.locator("h2:has-text('4. Onde')").evaluate("e => window.scrollTo(0, e.getBoundingClientRect().top + scrollY - 110)")
        n.mover(700, 300, 0.2)
        c.ate(f2 + 0.6)
        n.apontar("tr:has-text('Aplicar regras') td >> nth=4", 0.9)
        c.ate(f2 + frase("c7", 2, 1) - 0.2, "70%")
        n.apontar("tr:has-text('Publicar Trusted') td >> nth=4", 0.7)
        c.ate(f2 + frase("c7", 2, 1) + 1.8)
        n.apontar("tr:has-text('Publicar Refined') td >> nth=4", 0.7)
        c.ate(f2 + frase("c7", 2, 1) + 3.8)
        n.apontar("li:has-text('somam')", 0.8, dx=0.25)
        c.ate(f2 + frase("c7", 2, 2) - 0.6, "linear")
        n.rolar_ate("p:has-text('Insight 2')", 150, 0.9)
        n.apontar("tr:has-text('Trusted + Regras + Refined')", 0.8, dx=0.5)
        c.ate(f2 + frase("c7", 2, 2) + 3.6)
        n.apontar("li:has-text('ajuste linear')", 0.8, dx=0.2)
        c.ate(f3 - 0.5, "rajada")
        n.rolar_ate("p:has-text('Insight 3')", 150, 0.9)
        n.apontar("li:has-text('Na rajada de 6 POSTs')", 0.8, dx=0.3)
        c.ate(f3 + frase("c7", 3, 1) - 0.6, "ND")
        n.rolar_ate("h2:has-text('5. Varia')", 140, 0.9)
        n.apontar("li:has-text('18 decisões ND')", 0.8, dx=0.15)
        c.ate(f3 + frase("c7", 3, 1) + 3.6)
        n.apontar("p:has-text('Insight 4')", 0.8, dx=0.3)
        c.ate(f4 - 0.5, "melhorias")
        n.rolar_ate("h2:has-text('6. Oportunidades')", 140, 0.9)
        for k, chave in enumerate(["Processamento incremental", "Encurtar a seção crítica", "Destacar a falta"]):
            c.ate(f4 + 1.2 + k * 2.3)
            n.apontar(f"tr:has-text('{chave}') td >> nth=0", 0.7, dx=0.3)


def c8(n):
    n.abrir(infra.doc("README.md"))
    n.pag.locator("h2:has-text('Situação atual')").evaluate("e => window.scrollTo(0, e.getBoundingClientRect().top + scrollY - 100)")
    n.mover(1180, 280, 0.3)
    f0 = 1.0
    with Cena("c8", {0: f0}, f0 + DUR[("c8", 0)] + 2.2) as c:
        c.ate(f0 + 0.8)
        n.apontar("li:has-text('plataforma, execução contínua')", 0.8, dx=0.2)
        c.ate(f0 + 3.6)
        n.apontar("li:has-text('pipeline DevSecOps completo')", 0.9, dx=0.2)
        c.ate(f0 + 6.4)
        n.apontar("li:has-text('análise de processo')", 0.9, dx=0.3)
        c.ate(f0 + frase("c8", 0, 1) - 0.4, "não existe")
        n.apontar("p:has-text('Não existe no produto')", 0.9, dx=0.25)
        c.ate(f0 + frase("c8", 0, 2) - 1.0, "matriz")
        n.abrir(infra.doc("MATRIZ_RASTREABILIDADE_FASE_7.md"), 0.3)
        n.mover(1250, 330, 0.3)
        c.ate(f0 + frase("c8", 0, 2) + 0.4)
        n.rolar(1150, DUR[("c8", 0)] - frase("c8", 0, 2) + 0.6)


CENAS = {"c1": c1, "c2": c2, "c3": c3, "c4": c4, "c5": c5, "c6": c6, "c7": c7, "c8": c8}


def main():
    quais = sys.argv[1:] or list(CENAS)
    tela = infra.iniciar_tela()
    infra.iniciar_docs()
    reg_arq = AQUI / "registro_gravacao.json"
    if reg_arq.exists():
        antigo = json.loads(reg_arq.read_text(encoding="utf-8"))
        for k in REGISTRO:
            REGISTRO[k].update(antigo.get(k, {}))
    try:
        with sync_playwright() as pw:
            n = infra.Navegador(pw)
            for q in quais:
                CENAS[q](n)
            REGISTRO["erros_js"] = n.erros
            n.fechar()
    finally:
        tela.terminate()
        REGISTRO["gravado_em"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
        REGISTRO["versoes"] = {"docker": subprocess.run(["docker", "--version"], capture_output=True, text=True).stdout.strip()}
        reg_arq.write_text(json.dumps(REGISTRO, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
