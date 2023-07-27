FROM python:3.9



WORKDIR /BFF


COPY ./requirements.txt /BFF/requirements.txt


RUN pip install --no-cache-dir --upgrade -r /BFF/requirements.txt

COPY ./app /BFF/app


CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "9000"]
