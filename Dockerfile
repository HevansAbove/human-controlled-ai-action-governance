FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 AGH_OUTPUT_DIR=/tmp
WORKDIR /project
COPY . .
CMD ["sh", "-c", "python -m unittest discover -s tests -v && python evaluate.py"]
