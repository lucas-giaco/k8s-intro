FROM python:3-alpine

WORKDIR /app

COPY app/requirements.txt .
RUN pip install -r requirements.txt

COPY app/app.py .

ENTRYPOINT [ "python" ]
CMD [ "app.py" ]
