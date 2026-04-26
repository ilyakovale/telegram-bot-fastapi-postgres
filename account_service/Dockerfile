FROM python:3.14-alpine3.22
WORKDIR /python-app
ENV PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache -r requirements.txt

COPY . ./account_service/

RUN mkdir -p /python-app/requests_templates
COPY ../requests_templates/* /python-app/requests_templates/

EXPOSE 8001

CMD ["python", "account_service/__main__.py"]