FROM python:3.10-slim
#ajout d'un utilisateur par sécurité
RUN useradd -ms /bin/bash pythonuser
WORKDIR /app
RUN pip install flask
COPY demo-rest-app-python/app .
RUN chown -R pythonuser:pythonuser /app
EXPOSE 5000
USER pythonuser
ENV FLASK_APP=/app/main.py
CMD ["flask", "run", "--host", "0.0.0.0"]
