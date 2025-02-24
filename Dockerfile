FROM python:3.12-slim

RUN pip install aiohttp

COPY gitlab_user_block_cleaner.py /app/gitlab_user_block_cleaner.py

WORKDIR /app

CMD ["python", "gitlab_user_block_cleaner.py"]

