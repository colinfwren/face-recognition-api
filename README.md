# face-recognition-api
A basic Flask based face recognition API using face_recognition and PostgreSQL

Based on the following repo: [https://github.com/vearutop/face-postgre](https://github.com/vearutop/face-postgre)

The API exposes two POST endpoints:
- `faces` which adds a face to the database and the remote URL of the image file
- `faces/searches` which finds a face in the database

## Running

```
mkdir uploads # needed to store the files temporarily
docker-compose up
python3 setup-db.py # needed to setup PostgreSQL properly
DATABASE_STRING="pq://user:pass@localhost:5434/db" python3 app.py
```

## (Coming Soon) Running with Docker
The docker image takes some time as `dlib` needs to be built manually and then run the docker compose set up by removing the commented lines

In the docker compose are 2 services:
- `db` which is the PostgreSQL database
- `api` which is the API server itself

```
docker build --tag face_rec_api .
docker-compose up
python3 setup-db.py # needed to setup PostgreSQL properly
```

> issue currently with Flask saying that POST methods aren't allowed