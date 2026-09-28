FROM python:3.11-slim
WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir -e ".[tui]" && pip install pytest
CMD ["f1-tui", "--demo", "--ascii"]
