#!/bin/bash
docker exec -it $(docker ps --filter name=airflow-api-server --format "{{.ID}}") /bin/bash
