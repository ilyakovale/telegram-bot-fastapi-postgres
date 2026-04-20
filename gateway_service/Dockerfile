FROM python:3.14-alpine3.22
WORKDIR /python-app
ENV PYTHONUNBUFFERED=1

COPY gateway_service/requirements.txt .
RUN pip install --no-cache -r requirements.txt

COPY gateway_service/ gateway_service/

RUN mkdir -p /python-app/requests_templates
VOLUME [ "/python-app/requests_templates" ]

EXPOSE 8000

CMD ["python", "gateway_service/__main__.py"]