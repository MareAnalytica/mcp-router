#!/usr/bin/env bash
# setup.sh — Replace MY_PROJECT with your actual project name
# Usage: ./setup.sh my-new-service
set -euo pipefail

if [ -z "${1:-}" ]; then
  echo "Usage: $0 <project-name>"
  echo "Example: $0 data-pipeline"
  exit 1
fi

PROJECT="$1"

echo "Replacing MY_PROJECT → ${PROJECT} in all template files..."

find . -type f \( -name '*.yml' -o -name '*.yaml' -o -name '*.md' \) \
  -not -path './.git/*' \
  -exec sed -i "s/MY_PROJECT/${PROJECT}/g" {} +

echo "✓ Done. Files updated:"
grep -rl "${PROJECT}" --include='*.yml' --include='*.yaml' --include='*.md' . | sort

echo ""
echo "Next steps:"
echo "  1. Add your Dockerfiles (backend/Dockerfile, frontend/Dockerfile, etc.)"
echo "  2. Update the images list in .github/workflows/ci-dev.yml"
echo "  3. Update kube/base/secrets.yaml with your DB credentials"
echo "  4. Push to main and watch the pipeline run"
echo ""
echo "Your service will be at: https://${PROJECT}-dev.mareanalytica.com"
