FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

ENV IAOFFDEV_HOST=0.0.0.0
ENV IAOFFDEV_PORT=8765

EXPOSE 8765
CMD ["python", "run.py"]
