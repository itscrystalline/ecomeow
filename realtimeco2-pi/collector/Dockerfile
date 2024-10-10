FROM python:3.9
COPY . /app

WORKDIR /app
RUN pip install -r requirements.txt
RUN playwright install-deps
RUN playwright install chromium

CMD ["python", "worldometerCollector.py"]