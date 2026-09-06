FROM python:3.11-slim
WORKDIR /app
COPY etl_env.txt .
RUN pip install --no-cache-dir -r etl_env.txt
COPY etl_script.py .
CMD ["python", "etl_script.py"]