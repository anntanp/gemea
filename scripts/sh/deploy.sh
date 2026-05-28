# scripts/deploy.sh
# Usage: ./scripts/sh//deploy.sh
# Copies curated files to production repo and pushes.

PROD_DIR="$HOME/prod-repo"   # local clone of production repo
FILES=(
  "src/api/"
  "src/lib/"
  "config/prod.yaml"
  "requirements.txt"
)

for f in "${FILES[@]}"; do
  rsync -a "$f" "$PROD_DIR/$f"
done

cd "$PROD_DIR"
git add -A
git commit -m "deploy: sync from dev $(date +%Y-%m-%d)"
git push