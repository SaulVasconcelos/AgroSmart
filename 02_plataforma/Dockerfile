# AgroSmart / AgroMonitor — imagem de runtime (Fase 7).
# A aplicação usa somente a biblioteca padrão do Python: não há etapa pip/npm nem
# compilação de frontend. A imagem leva só o necessário para executar.
#
# PYTHON_IMAGE pode ser fixada por digest (python:3.13-slim@sha256:...) pelo pipeline;
# o digest efetivamente usado em cada build fica registrado no relatório do pipeline.
ARG PYTHON_IMAGE=python:3.13-slim
FROM ${PYTHON_IMAGE}

LABEL org.opencontainers.image.title="AgroSmart / AgroMonitor" \
      org.opencontainers.image.description="Plataforma acadêmica local de monitoramento agrícola com dados simulados (Fase 7)" \
      org.opencontainers.image.version="7.0.0"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    TZ=America/Sao_Paulo \
    AGROSMART_DATA_DIR=/data \
    AGROSMART_SEED_DIR=/app/semente

WORKDIR /app

# Endurecimento da base (achados reais do Trivy em 18/11/2026):
# 1) aplica as atualizações de segurança do Debian disponíveis no momento do build
#    (ex.: zlib1g CVE-2026-85091 corrigida em deb13u1, ainda não incorporada à tag python:3.13-slim);
# 2) remove o pip da imagem de RUNTIME: a aplicação usa só a biblioteca padrão, e as dependências
#    vendorizadas do pip (urllib3, msgpack, pkg_resources/setuptools) eram as vulnerabilidades HIGH
#    com correção encontradas. Menos software instalado = menor superfície de ataque.
RUN set -eux; \
    export DEBIAN_FRONTEND=noninteractive; \
    apt-get update; \
    apt-get -y upgrade; \
    apt-get clean; \
    rm -rf /var/lib/apt/lists/*; \
    if python -m pip --version >/dev/null 2>&1; then python -m pip uninstall -y pip; fi; \
    rm -rf /usr/local/bin/pip /usr/local/bin/pip3* /root/.cache; \
    python -c "import importlib.util, sys; sys.exit(importlib.util.find_spec('pip') is not None)"

# Usuário sem privilégios; /data pertence a ele para que um volume nomeado novo herde a permissão.
RUN groupadd --system --gid 10001 agrosmart \
 && useradd --system --uid 10001 --gid agrosmart --no-create-home --home-dir /nonexistent --shell /usr/sbin/nologin agrosmart \
 && mkdir -p /data \
 && chown agrosmart:agrosmart /data

# Código e interface pertencem ao root (somente leitura para o processo).
COPY main.py ./
COPY agrosmart/ ./agrosmart/
COPY web/ ./web/
# Amostra determinística da Fase 6: copiada para /data SOMENTE quando o volume está vazio.
COPY data/raw/ ./semente/raw/
COPY data/trusted/ ./semente/trusted/
COPY data/refined/ ./semente/refined/

USER agrosmart:agrosmart
EXPOSE 8501
VOLUME ["/data"]

# Prontidão real: pasta de dados gravável e camada Refined disponível (não só "processo vivo").
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
  CMD ["python", "-c", "import sys,urllib.request; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8501/api/pronto', timeout=4).status == 200 else 1)"]

# 0.0.0.0 somente DENTRO do container; a publicação no host fica restrita ao loopback (compose.yaml).
ENTRYPOINT ["python", "main.py"]
CMD ["web", "--host", "0.0.0.0", "--porta", "8501"]
