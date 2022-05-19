FROM python:3

WORKDIR /src

COPY bm_awards_scraper.py requirements.txt ./
RUN file="$(ls .)" && echo $file
RUN pip install --no-cache-dir -r requirements.txt


CMD [ "python", "./bm_awards_scraper.py"]