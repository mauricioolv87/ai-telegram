FROM python:3.11-slim

WORKDIR /app

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Instalar uv (binário oficial)
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:${PATH}"

# Copiar o pyproject e lockfile primeiro (melhor cache)
COPY pyproject.toml uv.lock* ./

# Instalar dependências do projeto
RUN uv sync --frozen

# Copiar todo o código
COPY . .

# Criar diretório para áudios temporários
RUN mkdir -p data/audios

# Expor porta
EXPOSE 8080

# Rodar usando o ambiente isolado do uv
CMD ["uv", "run", "main.py"]
