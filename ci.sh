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
echo "  Building python deps for arm/v7"
echo "====================================="
echo " "
docker buildx build \
	-t selexin/microservice-pydeps:latest \
	--platform linux/arm/v7 \
	--push \
	- < Dockerfile.pydeps

exit 0

echo ""
echo "====================================="
echo "   Building GPS Service for arm/v7"
echo "====================================="
echo " "
docker buildx build ./services/gps/ \
	-f ./Dockerfile.service \
	-t selexin/gps-service:latest \
	--platform linux/arm/v7 \
	--push

echo ""
echo "====================================="
echo "   Building IMU Service for arm/v7"
echo "====================================="
echo " "
docker buildx build ./services/imu/ \
	-f ./Dockerfile.service \
	-t selexin/imu-service:latest \
	--platform linux/arm/v7 \
	--push

echo ""
echo "====================================="
echo "   Building API Service for arm/v7"
echo "====================================="
echo " "
docker buildx build ./api/ \
	-f ./Dockerfile.service \
	-t selexin/api-service:latest \
	--platform linux/arm/v7 \
	--push

echo "====================================="
echo "             All Done!"
echo "====================================="
echo " "
