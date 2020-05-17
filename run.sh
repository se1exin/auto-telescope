#!/bin/bash
docker stop gps-service imu-service
docker rm gps-service
docker rm imu-service
#docker run --privileged -p 50051:50051 --name gps-service selexin/gps-service:latest
docker run --privileged -p 50052:50052 --name imu-service selexin/imu-service:latest
