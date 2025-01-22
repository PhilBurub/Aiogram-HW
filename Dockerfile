FROM python:3.12

RUN pip install -r requirements.txt

CMD ["python", "app.py"]