FROM python:3.12-slim

# Install essential packages for development and VS Code remote containers
RUN apt-get update && \
    apt-get install -y \
    git \
    curl \
    wget \
    ca-certificates \
    gnupg \
    sudo \
    openssh-server \
    procps \
    lsb-release \
    locales \
    build-essential \
    coreutils \
    && rm -rf /var/lib/apt/lists/*

# Configure locale
RUN echo "en_US.UTF-8 UTF-8" > /etc/locale.gen && \
    locale-gen

ENV LANG=en_US.UTF-8 \
    LANGUAGE=en_US:en \
    LC_ALL=en_US.UTF-8

# Install Node.js (required for Claude Code CLI)
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs && \
    rm -rf /var/lib/apt/lists/*

# Install Claude Code CLI globally
RUN npm install -g @anthropic-ai/claude-code

# Install uv package manager
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:${PATH}"

# Set working directory (workspace will be mounted here)
WORKDIR /workspace

ARG INSTALL_MCP=false

# Copy project files and install Python dependencies using uv
COPY . /workspace/
RUN if [ "$INSTALL_MCP" = "true" ]; then cd /workspace && uv sync; fi

# Default command (will be overridden by docker-compose)
CMD ["/usr/bin/sleep", "infinity"]
