# Dockerfile - this is a comment. Delete me if you want.
FROM python:3.7
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt
RUN pip install matplotlib
RUN pip install pandas
RUN pip install scipy
ENTRYPOINT ["python"]
CMD ["app.py"]
