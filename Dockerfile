FROM python:3.11-slim

WORKDIR /app

# Python 의존성 설치  
COPY requirements.txt .
RUN pip install --no-cache-dir fastapi uvicorn pandas numpy

# 애플리케이션 코드 복사
COPY src/ ./src/
COPY scenarios/ ./scenarios/

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

EXPOSE 8009

CMD ["python", "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8009"]