FROM python:3.6
RUN mkdir /usr/src/app/
COPY . /usr/src/app/
WORKDIR /usr/src/app/
EXPOSE 5000
RUN pip install -r requirements.txt
# CMD ["python", "app.py"]
CMD ["gunicorn", "-w 4", "-b", "0.0.0.0:5000", "main:app"]