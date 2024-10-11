#!/bin/bash

# Exit the script on any error
set -e

# Get the version from `poetry version`
version_output=$(poetry version)

# Extract the version number
version=$(echo "$version_output" | awk '{print $2}')

echo "Creating Git tag: v$version"
git tag "v$version"

echo "Pushing Git tag: v$version"
git push origin "v$version"

echo "Tag v$version created and pushed successfully."
