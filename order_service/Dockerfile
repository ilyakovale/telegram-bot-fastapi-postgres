FROM python:3.12-alpine
WORKDIR /python-app
ENV PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache -r requirements.txt

COPY . .

EXPOSE 8002

CMD ["python", "__main__.py"]