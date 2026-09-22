FROM python:3.12-slim

# ============================================================
# System dependencies
# ============================================================

RUN apt-get update && apt-get install -y \
    curl \
    gnupg \
    gcc \
    g++ \
    unixodbc \
    unixodbc-dev \
    && rm -rf /var/lib/apt/lists/*


# ============================================================
# Microsoft ODBC Driver 18 for SQL Server
# ============================================================

RUN curl -fsSL https://packages.microsoft.com/keys/microsoft.asc \
    | gpg --dearmor -o /usr/share/keyrings/microsoft-prod.gpg

RUN curl https://packages.microsoft.com/config/debian/12/prod.list \
    > /etc/apt/sources.list.d/mssql-release.list

RUN apt-get update \
    && ACCEPT_EULA=Y apt-get install -y msodbcsql18 \
    && rm -rf /var/lib/apt/lists/*


# ============================================================
# Application directory
# ============================================================

WORKDIR /app


# ============================================================
# Python dependencies
# ============================================================

COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt


# ============================================================
# Application source
# ============================================================

COPY src ./src
COPY data ./data
COPY docs ./docs


# ============================================================
# Streamlit configuration
# ============================================================

EXPOSE 8501


# ============================================================
# Start application
# ============================================================

CMD ["python", "-m", "streamlit", "run", "src/ui.py", "--server.address=0.0.0.0", "--server.port=8501"]