#!/bin/bash
docker stop gps-service imu-service
docker rm gps-service
docker rm imu-service
docker pull selexin/gps-service:latest
docker pull selexin/imu-service:latest

docker run -d --privileged -p 50051:50000 --name gps-service selexin/gps-service:latest
docker run -d --privileged -p 50052:50000 --name imu-service selexin/imu-service:latest
