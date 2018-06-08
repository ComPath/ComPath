#!/bin/bash
#© 2018 Fraunhofer Gesellschaft e.V., Munich, Germany. All rights reserved.

read -p "Are you sure you want to use the latest version of ComPath (current version is 0.0.2)? (y/N) " -n 1 -r
echo    # (optional) move to a new line

HOST="docker.arty.scai.fraunhofer.de"
VERSION="0.0.2"
TAG="$HOST/compath"

# Build this image
docker build -t "$TAG:$VERSION" -t "$TAG:latest" .

# Push onto registry
read -p "Do you want to execute docker push? (y/N)" -n 1 -r
echo    # (optional) move to a new line
if [[ $REPLY =~ ^[Yy]$ ]]; then
	echo " ... executing docker push"
	docker push "$TAG:$VERSION"
	docker push "$TAG:latest"
fi
