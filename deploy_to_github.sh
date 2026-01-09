#!/bin/bash
set -e

# Configuration
REPO_HOST="github.com/guyronhuji/SJR_Data.git"
BRANCH="main"

if [ -n "$GITHUB_TOKEN" ]; then
    echo "Using provided GITHUB_TOKEN for authentication."
    REPO_URL="https://oauth2:$GITHUB_TOKEN@$REPO_HOST"
else
    echo "GITHUB_TOKEN not set. Using standard HTTPS URL (requires manual login or credential helper)."
    REPO_URL="https://$REPO_HOST"
fi

echo "Using repository: $REPO_URL"

# Initialize Git if not already done
if [ ! -d ".git" ]; then
    echo "Initializing new git repository..."
    git init
else
    echo "Git repository already initialized."
fi

# Configure Remote
if git remote | grep -q "^origin$"; then
    echo "Remote 'origin' already exists. Updating URL..."
    git remote set-url origin "$REPO_URL"
else
    echo "Adding remote 'origin'..."
    git remote add origin "$REPO_URL"
fi

# Add changes
echo "Adding files..."
git add .

# Commit (allow empty if nothing changed)
echo "Committing changes..."
if ! git diff-index --quiet HEAD; then
    git commit -m "Deploy: Updated project files and build configuration"
else
    echo "No changes to commit."
fi

# Rename branch to main
git branch -M "$BRANCH"

# Push
echo "Pushing to $BRANCH..."
git push -u origin "$BRANCH"

echo "----------------------------------------"
echo "Deployment complete!"
echo "Check your Actions tab here: https://github.com/guyronhuji/SJR_Data/actions"
