FROM python:3.7-slim

RUN pip install python-dotenv telebot requests
COPY LinksShorter.py .
CMD [ "python", "./LinksShorter.py" ]