FROM python:3.14-alpine3.22
WORKDIR /python-app
ENV PYTHONUNBUFFERED=1

COPY ./admin_service/requirements.txt .
RUN pip install --no-cache -r requirements.txt

COPY ./admin_service/ ./admin_service/

EXPOSE 8003

CMD ["python", "admin_service/__main__.py"]