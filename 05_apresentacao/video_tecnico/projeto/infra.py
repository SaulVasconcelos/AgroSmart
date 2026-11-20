"""Infraestrutura da gravação do vídeo técnico: tela virtual, gravador, navegador real, terminal real e
visualizador local dos arquivos do repositório. Tudo o que aparece no vídeo é capturado desta tela."""
import csv
import html
import http.server
import io
import os
import re
import subprocess
import threading
import time
import urllib.parse
from pathlib import Path

import markdown

DISPLAY = ":99"
L, A = 1920, 1080
FUNDO_TERMINAL = "#0d1f1a"
REPO = Path(os.environ.get("AGROSMART_REPO", Path(__file__).resolve().parents[3]))
PORTA_DOCS = 8600
PLATAFORMA = "http://127.0.0.1:8517"
ENV = dict(os.environ, DISPLAY=DISPLAY)


# ---------------------------------------------------------------- tela virtual e gravador
def iniciar_tela():
    subprocess.run(["pkill", "-f", f"Xvfb {DISPLAY}"], check=False)
    time.sleep(0.5)
    p = subprocess.Popen(["Xvfb", DISPLAY, "-screen", "0", f"{L}x{A}x24", "-nolisten", "tcp"],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(1.5)
    subprocess.run(["xsetroot", "-solid", FUNDO_TERMINAL], env=ENV, check=False)
    return p


class Gravador:
    """Grava a tela inteira. O relógio da cena começa em iniciar(); cortar() devolve o trecho exato."""

    def __init__(self, bruto):
        self.bruto = str(bruto)

    def iniciar(self):
        self.p = subprocess.Popen(
            ["ffmpeg", "-y", "-v", "error", "-f", "x11grab", "-framerate", "30", "-video_size", f"{L}x{A}", "-draw_mouse", "0",
             "-i", DISPLAY, "-copyts", "-c:v", "libx264", "-preset", "ultrafast", "-crf", "12", "-pix_fmt", "yuv420p", self.bruto],
            stdin=subprocess.PIPE, env=ENV)
        time.sleep(1.2)
        self.t0 = time.time()
        return self.t0

    def agora(self):
        return time.time() - self.t0

    def ate(self, t):
        falta = t - self.agora()
        if falta > 0:
            time.sleep(falta)
        return -falta if falta < 0 else 0.0   # atraso em relação à agenda

    def parar(self, duracao, saida):
        self.ate(duracao + 0.4)
        self.p.communicate(b"q", timeout=30)
        ini = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=start_time", "-of", "csv=p=0", self.bruto],
                                   capture_output=True, text=True).stdout.strip())
        corte = self.t0 - ini
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{corte:.3f}", "-i", self.bruto, "-t", f"{duracao:.3f}",
                        "-vf", "fps=30,format=yuv420p", "-c:v", "libx264", "-preset", "medium", "-crf", "17", "-an", str(saida)], check=True)
        return corte


# ---------------------------------------------------------------- visualizador dos arquivos do repositório
CSS_DOC = """
*{box-sizing:border-box} body{margin:0;background:#f6f8f6;color:#122923;font:17px/1.55 Inter,'DejaVu Sans',Arial,sans-serif}
.barra{position:sticky;top:0;background:#0c3028;color:#e6efe9;padding:11px 28px;font-size:15px;z-index:5;display:flex;gap:10px}
.barra b{color:#f2c66d;font-weight:600} .barra span{opacity:.75}
main{max-width:1180px;margin:0 auto;padding:22px 28px 240px} main.largo{max-width:1500px}
h1{font-size:30px;margin:.6em 0 .4em;color:#0c3028} h2{font-size:23px;margin:1.3em 0 .4em;color:#0c3028;border-bottom:1px solid #d9e3dc;padding-bottom:5px}
h3{font-size:19px;margin:1.1em 0 .3em;color:#0c3028} p,li{max-width:1100px}
table{border-collapse:collapse;margin:12px 0;font-size:15px;background:#fff} th,td{border:1px solid #d9e3dc;padding:6px 10px;text-align:left;vertical-align:top}
th{background:#e9f0eb;color:#0c3028} td{overflow-wrap:anywhere} td:first-child,td:nth-child(2){overflow-wrap:normal} td:nth-child(n+4){font-size:13px} code{background:#e9f0eb;padding:1px 5px;border-radius:4px;font:14px 'DejaVu Sans Mono',monospace}
pre{background:#0d1f1a;color:#e6efe9;padding:12px 16px;border-radius:8px;overflow:auto} pre code{background:none;color:inherit}
a{color:#17633f} img{max-width:100%} blockquote{border-left:4px solid #c1d9cb;margin:10px 0;padding:2px 14px;color:#52695e}
.figura{display:flex;justify-content:center;padding:10px} .figura img{max-height:calc(100vh - 80px);width:auto;background:#fff;border:1px solid #d9e3dc}
.csv td,.csv th{white-space:nowrap;font:13px 'DejaVu Sans Mono',monospace;padding:4px 8px} .nota{color:#52695e;font-size:14px}
"""


def _pagina(rel, corpo, largo=False):
    return ("<!DOCTYPE html><html lang='pt-BR'><head><meta charset='utf-8'><title>" + html.escape(rel) + " — repositório AgroSmart</title>"
            "<style>" + CSS_DOC + "</style></head><body><div class='barra'><b>Repositório AgroSmart</b><span>arquivo:</span>"
            + html.escape(rel) + "</div><main class='" + ("largo" if largo else "") + "'>" + corpo + "</main></body></html>")


class _Docs(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_GET(self):
        u = urllib.parse.urlparse(self.path)
        rel = urllib.parse.unquote(u.path).lstrip("/")
        alvo = (REPO / rel).resolve()
        if not str(alvo).startswith(str(REPO)) or not alvo.is_file():
            self.send_error(404)
            return
        bruto = "bruto" in urllib.parse.parse_qs(u.query)
        if alvo.suffix == ".md" and not bruto:
            texto = alvo.read_text(encoding="utf-8")
            corpo = markdown.markdown(texto, extensions=["tables", "fenced_code", "sane_lists"])
            dados, tipo = _pagina(rel, corpo).encode(), "text/html; charset=utf-8"
        elif alvo.suffix == ".csv" and not bruto:
            linhas = list(csv.reader(io.StringIO(alvo.read_text(encoding="utf-8"))))
            cab = "<tr><th>#</th>" + "".join(f"<th>{html.escape(c)}</th>" for c in linhas[0]) + "</tr>"
            trs = "".join(f"<tr><td>{n}</td>" + "".join(f"<td>{html.escape(c)}</td>" for c in l) + "</tr>" for n, l in enumerate(linhas[1:], 1))
            corpo = f"<p class='nota'>{len(linhas) - 1} linhas (eventos), {len(linhas[0])} colunas.</p><table class='csv'>{cab}{trs}</table>"
            dados, tipo = _pagina(rel, corpo, largo=True).encode(), "text/html; charset=utf-8"
        elif alvo.suffix in (".png", ".jpg", ".svg") and not bruto:
            larg = urllib.parse.parse_qs(u.query).get("larg", [""])[0]
            estilo = f" style='max-height:none;width:{int(larg)}px'" if larg.isdigit() else ""
            corpo = f"<div class='figura'><img id='figura'{estilo} src='/{urllib.parse.quote(rel)}?bruto=1' alt=''></div>"
            dados, tipo = _pagina(rel, corpo, largo=True).encode(), "text/html; charset=utf-8"
        else:
            dados = alvo.read_bytes()
            tipo = {".png": "image/png", ".jpg": "image/jpeg", ".svg": "image/svg+xml"}.get(alvo.suffix, "application/octet-stream")
        self.send_response(200)
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Length", str(len(dados)))
        self.end_headers()
        self.wfile.write(dados)


def iniciar_docs():
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", PORTA_DOCS), _Docs)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


def doc(rel, larg=None):
    return f"http://127.0.0.1:{PORTA_DOCS}/{urllib.parse.quote(rel)}" + (f"?larg={larg}" if larg else "")


# ---------------------------------------------------------------- navegador real (Chromium com janela)
CURSOR_JS = """
(() => {
  if (window.__cursorVideo) return; window.__cursorVideo = true;
  const criar = () => {
    const c = document.createElement('div'); c.id = '__cursor_video';
    c.style.cssText = 'position:fixed;left:0;top:0;width:26px;height:26px;z-index:2147483647;pointer-events:none;transform:translate(-200px,-200px)';
    c.innerHTML = '<svg width="26" height="26" viewBox="0 0 24 24"><path d="M4 2l15 9.5-6.6 1.3 4 7.6-2.7 1.4-4-7.7L5 18.5z" fill="#111" stroke="#fff" stroke-width="1.4" stroke-linejoin="round"/></svg>';
    const o = document.createElement('div'); o.id = '__onda_video';
    o.style.cssText = 'position:fixed;left:0;top:0;width:44px;height:44px;margin:-22px 0 0 -22px;border-radius:50%;border:3px solid #f2a93b;z-index:2147483646;pointer-events:none;opacity:0;transform:translate(-200px,-200px)';
    document.documentElement.appendChild(o); document.documentElement.appendChild(c);
    let pos = null; try { pos = JSON.parse(sessionStorage.getItem('__cursor_pos') || 'null'); } catch (e) {} if (pos) c.style.transform = `translate(${pos[0]}px,${pos[1]}px)`;
    addEventListener('mousemove', e => { c.style.transform = `translate(${e.clientX}px,${e.clientY}px)`; try { sessionStorage.setItem('__cursor_pos', JSON.stringify([e.clientX, e.clientY])); } catch (x) {} }, true);
    addEventListener('mousedown', e => { o.style.transition = 'none'; o.style.opacity = '0.95'; o.style.transform = `translate(${e.clientX}px,${e.clientY}px) scale(0.35)`;
      requestAnimationFrame(() => requestAnimationFrame(() => { o.style.transition = 'transform .45s ease-out, opacity .45s ease-out'; o.style.opacity = '0'; o.style.transform = `translate(${e.clientX}px,${e.clientY}px) scale(1.25)`; })); }, true);
  };
  if (document.documentElement) criar(); else addEventListener('DOMContentLoaded', criar);
})();
"""


class Navegador:
    def __init__(self, pw, escala=1.25):
        perfil = Path("/tmp/perfil_gravacao")
        if perfil.exists():
            import shutil
            shutil.rmtree(perfil)
        (perfil / "Default").mkdir(parents=True)
        # Perfil novo, só com a oferta de tradução desligada (a página é em português e o navegador, em inglês).
        (perfil / "Default" / "Preferences").write_text('{"translate":{"enabled":false},"translate_blocked_languages":["pt","pt-BR"]}')
        self.ctx = pw.chromium.launch_persistent_context(
            str(perfil), headless=False, env=ENV, ignore_default_args=["--enable-automation"], no_viewport=True, locale="pt-BR",
            args=["--window-position=0,0", f"--window-size={int(L / escala)},{int(A / escala)}", f"--force-device-scale-factor={escala}",
                  "--test-type", "--no-first-run", "--disable-infobars", "--hide-crash-restore-bubble",
                  "--disable-features=Translate,TranslateUI,MediaRouter", "--lang=pt-BR"])
        self.nav = self.ctx
        self.ctx.add_init_script(CURSOR_JS)
        self.pag = self.ctx.pages[0] if self.ctx.pages else self.ctx.new_page()
        self.erros = []
        self.pag.on("pageerror", lambda e: self.erros.append(str(e)))
        self.x, self.y = 700.0, 400.0
        # Tira o foco da barra de endereço (o perfil novo abre com ela selecionada).
        self.pag.goto("about:blank")
        subprocess.run(["xdotool", "key", "Escape", "Escape"], env=ENV, check=False)
        self.pag.goto(f"http://127.0.0.1:{PORTA_DOCS}/README.md")
        time.sleep(0.5)
        self.pag.goto("about:blank")

    def abrir(self, url, espera=0.6):
        self.pag.goto(url)
        self.pag.wait_for_load_state("load")
        self.pag.bring_to_front()
        self.pag.evaluate("window.focus(); document.body && document.body.focus()")
        time.sleep(espera)
        self.pag.mouse.move(self.x, self.y)

    def mover(self, x, y, dur=0.7):
        n = max(2, int(dur * 30))
        x0, y0 = self.x, self.y
        t0 = time.time()
        for i in range(1, n + 1):
            k = i / n
            k = k * k * (3 - 2 * k)
            self.pag.mouse.move(x0 + (x - x0) * k, y0 + (y - y0) * k)
            falta = t0 + dur * i / n - time.time()
            if falta > 0:
                time.sleep(falta)
        self.x, self.y = x, y

    def centro(self, seletor, dx=0.5, dy=0.5):
        loc = self.pag.locator(seletor).first
        loc.scroll_into_view_if_needed()
        time.sleep(0.25)
        b = loc.bounding_box()
        return b["x"] + b["width"] * dx, b["y"] + b["height"] * dy

    def apontar(self, seletor, dur=0.7, dx=0.5, dy=0.5):
        x, y = self.centro(seletor, dx, dy)
        self.mover(x, y, dur)

    def clicar(self, seletor, dur=0.7, pausa=0.25):
        self.apontar(seletor, dur)
        time.sleep(pausa)
        self.pag.mouse.down()
        time.sleep(0.08)
        self.pag.mouse.up()

    def rolar(self, px, dur=1.5):
        n = max(1, int(dur * 30))
        t0 = time.time()
        feito = 0.0
        for i in range(1, n + 1):
            k = i / n
            k = k * k * (3 - 2 * k)
            alvo = px * k
            self.pag.mouse.wheel(0, alvo - feito)
            feito = alvo
            falta = t0 + dur * i / n - time.time()
            if falta > 0:
                time.sleep(falta)

    def rolar_ate(self, seletor, margem=110, dur=1.4):
        y = self.pag.locator(seletor).first.evaluate("e => e.getBoundingClientRect().top")
        self.rolar(y - margem, dur)

    def fechar(self):
        self.nav.close()


# ---------------------------------------------------------------- terminal real (xterm)
class Terminal:
    def __init__(self, pasta, fonte=18, colunas=124, linhas=34):
        self.p = subprocess.Popen(
            ["xterm", "-geometry", f"{colunas}x{linhas}+0+0", "-fa", "DejaVu Sans Mono", "-fs", str(fonte), "-bg", FUNDO_TERMINAL,
             "-fg", "#e6efe9", "-bw", "0", "-b", "30", "+sb", "-xrm", "XTerm*allowSendEvents: true", "-xrm", "XTerm*cursorColor: #f2c66d",
             "-xrm", "XTerm*cursorBlink: false", "-T", "terminal", "-e", "bash", "--norc", "--noprofile"],
            env=dict(ENV, PS1=r"\[\e[38;5;114m\]agrosmart/02_plataforma\[\e[0m\] $ ", TERM="xterm-256color", LANG="C.UTF-8", LC_ALL="C.UTF-8"),
            cwd=str(pasta))
        self.id = None
        for _ in range(50):
            r = subprocess.run(["xdotool", "search", "--onlyvisible", "--name", "^terminal$"], env=ENV, capture_output=True, text=True)
            if r.stdout.strip():
                self.id = r.stdout.split()[0]
                break
            time.sleep(0.1)
        if not self.id:
            raise RuntimeError("xterm não abriu")
        subprocess.run(["xdotool", "windowraise", self.id], env=ENV, check=False)
        time.sleep(0.3)

    def digitar(self, texto, atraso_ms=45):
        subprocess.run(["xdotool", "type", "--window", self.id, "--delay", str(atraso_ms), texto], env=ENV, check=True)

    def enter(self):
        subprocess.run(["xdotool", "key", "--window", self.id, "Return"], env=ENV, check=True)

    def comando(self, texto, atraso_ms=45):
        self.digitar(texto, atraso_ms)
        time.sleep(0.35)
        self.enter()

    def tamanho(self):
        r = subprocess.run(["xwininfo", "-id", self.id], env=ENV, capture_output=True, text=True).stdout
        return tuple(int(re.search(k + r":\s+(\d+)", r).group(1)) for k in ("Width", "Height"))

    def fechar(self):
        self.p.terminate()
        try:
            self.p.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.p.kill()


def foto(caminho):
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "x11grab", "-video_size", f"{L}x{A}", "-draw_mouse", "0", "-i", DISPLAY,
                    "-frames:v", "1", str(caminho)], env=ENV, check=True)
