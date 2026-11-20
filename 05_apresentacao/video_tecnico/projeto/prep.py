"""Preparação da gravação: para a execução contínua e deixa o Talhão B com a última leitura em ND (umidade >= 35%)."""
import json, urllib.request, sys
B = "http://127.0.0.1:8517"
def http(c, corpo=None):
    d = None if corpo is None else json.dumps(corpo).encode()
    r = urllib.request.Request(B + c, data=d, method="GET" if d is None else "POST", headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(r, timeout=30) as x: return json.loads(x.read())
print("parar:", json.dumps(http("/api/operacao/parar", {}), ensure_ascii=False)[:160])
for n in range(1, 30):
    t = http("/api/talhao?talhao=Talhao+B")
    l = t.get("leitura_selecionada") or t.get("ultima_leitura") or {}
    print(n, {k: l.get(k) for k in ("data_hora", "regra", "severidade", "umidade_solo", "temperatura", "avaliacao")})
    if l.get("regra") == "ND" and float(l.get("umidade_solo") or 0) >= 35 and str(l.get("data_hora", ""))[:10] == sys.argv[1]:
        print("pronto: Talhão B em ND na data de hoje"); break
    http("/api/simular", {"talhao": "Talhao B", "quantidade": 1})
print("chaves /api/talhao:", list(t.keys())[:12])
o = http("/api/operacao"); print("execução contínua:", o["execucao_continua"]["estado"], "| leituras raw:", json.dumps(o.get("dados", o.get("camadas", "")), ensure_ascii=False)[:200])
