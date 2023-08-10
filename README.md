# Datatank News Papers Data Pipeline

This is a data pipeline that scrapes the [Datatank](https://datatank.org/) for news papers and their articles. 

The goal is to create a database of news papers and their articles that can be used for further analysis.

The data is then stored in a MongoDB database.

## Contributors
⚠️ ⚠️ ⚠️ **This project has not been done by me. This is the result of the hard work from the Becode Bouman6 learners! All credits goes to them.** ⚠️ ⚠️ ⚠️

## Technologies used
- [Python 3.11](https://www.python.org/)
- [Docker](https://www.docker.com/)
- [MongoDB](https://www.mongodb.com/)
- [Airflow](https://airflow.apache.org/)

## How to run
1. Build & push the docker images to Docker Hub
```bash
# You need to modify the build_push_images.sh file to include your Docker Hub username
bash build_push_images.sh
```
2. Run airflow
```bash
docker-compose up
```
3. Set the MONGO_URI environment variable in the airflow UI's variables tab
```
The URI should be in the following format:
mongodb://<username>:<password>@<host>:<port>/<database_name>

The Airflow's variable should be nammed: mongodb_uri
```
4. Connect to the airflow UI: [http://localhost:8080](http://localhost:8080) The default username and password are both `airflow`.
5. Trigger the `news_papers_data_pipeline` DAG 
