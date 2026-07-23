FROM python:3.14-alpine3.22
WORKDIR /python-app
ENV PYTHONUNBUFFERED=1

COPY ./order_service/requirements.txt .
RUN pip install --no-cache -r requirements.txt

COPY ./order_service/ ./order_service/

EXPOSE 8002

CMD ["python", "order_service/__main__.py"]