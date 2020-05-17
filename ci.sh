#!/bin/bash

# Setup Docker buildx builder for arm support
export DOCKER_CLI_EXPERIMENTAL=enabled

echo " "
echo "====================================="
echo " Setting up multiarch docker builder"
echo "====================================="
echo " "

# Add binfmt_misc support for arm
docker run --rm --privileged docker/binfmt:a7996909642ee92942dcd6cff44b9b95f08dad64

# Create a new builder
docker buildx create --use --name multiarch-builder

# Make sure builder is running
docker buildx inspect --bootstrap


echo ""
echo "====================================="
echo "  Building grpcio deps for arm/v7"
echo "====================================="
echo " "
docker buildx build . \
	-f Dockerfile.grpcio \
	-t selexin/grpcio:latest \
	-t selexin/grpcio:1.28.1 \
	--platform linux/arm/v7 \
	--push


echo ""
echo "====================================="
echo "   Building GPS Service for arm/v7"
echo "====================================="
echo " "
docker buildx build ./services/gps/ \
	-f ./services/gps/Dockerfile \
	-t selexin/gps-service:latest \
	--platform linux/arm/v7 \
	--push

echo ""
echo "====================================="
echo "   Building IMU Service for arm/v7"
echo "====================================="
echo " "
docker buildx build ./services/imu/ \
	-f ./services/imu/Dockerfile \
	-t selexin/imu-service:latest \
	--platform linux/arm/v7 \
	--push

echo "====================================="
echo "             All Done!"
echo "====================================="
echo " "
