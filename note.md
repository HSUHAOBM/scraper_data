docker build -t flask-app .

docker run -p 5000:5000 --name flask_app -v templates:/app/templates -d flask-app


---

docker compose up
