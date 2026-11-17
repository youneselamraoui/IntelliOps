FROM python:3.12-slim

WORKDIR /app

# Installer les dépendances
COPY Agent_1/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copier le code de l'agent
COPY Agent_1/ ./Agent_1/

# Copier les contrats communs
COPY shared/ ./shared/

CMD ["python", "-m", "Agent_1.agent1"]