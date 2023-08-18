import boto3
import git


# Initialize Boto3 client for CodeCommit
client = boto3.client('codecommit')

# Create repository
repository_name = 'gl-pdf-search-repository'
repository_description = 'GL Managed Services Project - PDFtoText'
response = client.create_repository(
    repositoryName=repository_name,
    repositoryDescription=repository_description
)
clone_url_http = response['repositoryMetadata']['cloneUrlHttp']

# Initialize a Git repository and perform initial commit and push
repo_path = './gl-pdf-search-repository'  # Path to local repository
commit_message = 'initial commit'

# Initialize GitPython repository object
repo = git.Repo.init(repo_path)

# Add all files to the index
repo.git.add('*')

# Commit changes
repo.index.commit(commit_message)

# Add remote origin
repo.create_remote('origin', clone_url_http)

# Push changes to remote
repo.git.push('--set-upstream', 'origin', 'master')
