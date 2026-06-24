FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY pyproject.toml requirements.txt README.md ./
COPY bitguard ./bitguard
COPY samples ./samples
COPY sample_records ./sample_records
COPY index.html style.css code.html screen.png bg.png ./

RUN pip install --no-cache-dir -r requirements.txt && pip install --no-cache-dir -e .

EXPOSE 8765

CMD ["python", "-m", "bitguard", "serve", "--host", "0.0.0.0"]
