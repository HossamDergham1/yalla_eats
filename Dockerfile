FROM python:3.11-slim
WORKDIR /app
COPY env_details.txt .
RUN pip install --no-cache-dir -r env_details.txt
COPY generator_script.py .
CMD ["python", "generator_script.py"]