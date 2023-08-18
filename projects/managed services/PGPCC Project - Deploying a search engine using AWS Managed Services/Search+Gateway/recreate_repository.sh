#!/bin/bash

repository_name="gl-pdf-search-search-gateway-repository"
repository_description="GL Managed Services Project - Search Gateway"

# Clean up by removing the local repository
rm -rf .git

# Check if the repository already exists and delete it
aws codecommit get-repository --repository-name "$repository_name" > /dev/null 2>&1
if [ $? -eq 0 ]; then
    aws codecommit delete-repository --repository-name "$repository_name"
fi

# Create a new repository
clone_url_http=$(aws codecommit create-repository --repository-name "$repository_name" --repository-description "$repository_description" --output text --query 'repositoryMetadata.cloneUrlHttp')

# Initialize a local Git repository
git init
git add buildspec.yml lambda_function.py search_page.py search-gateway.yaml
git commit -m "initial commit"

# Add the remote repository and push the code
git remote add origin "$clone_url_http"
git push -u origin master

# Clean up by removing the local repository
# rm -rf .git
