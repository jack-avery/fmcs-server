FROM python

WORKDIR /bot
COPY . .

RUN pip install -r requirements.txt

ENTRYPOINT [ "python3", "main.py" ]
