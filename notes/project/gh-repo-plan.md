## 1. Goal

Sync curated files and folders from the dev GitHub repo to a separate production GitHub repo (different accounts).

---

## 2. Approach options

### 2.1 Deploy script (manual)

A local script copies selected paths to a local clone of the production repo and pushes.

```bash
# scripts/deploy.sh
# Usage: ./scripts/deploy.sh
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
```

**Trade-off**: Full manual control; no automation needed. Good starting point.

---

### 2.2 GitHub Actions + manifest (automated)

A `deploy/manifest.txt` file lists curated paths. A GitHub Action reads it and pushes to production on every merge to `main`.

**`deploy/manifest.txt`**:
```
src/api/
src/lib/
config/prod.yaml
requirements.txt
```

**`.github/workflows/deploy.yml`**:
```yaml
name: Deploy to production
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Clone production repo
        run: |
          git clone https://x-access-token:${{ secrets.PROD_TOKEN }}@github.com/prod-account/prod-repo.git prod_repo

      - name: Sync curated files
        run: |
          while IFS= read -r path; do
            [[ -z "$path" || "$path" == \#* ]] && continue
            rsync -a "$path" "prod_repo/$path"
          done < deploy/manifest.txt

      - name: Commit and push
        run: |
          cd prod_repo
          git config user.email "deploy@ci"
          git config user.name "Deploy Bot"
          git add -A
          git diff --cached --quiet || git commit -m "deploy: sync from dev ${{ github.sha }}"
          git push
```

**Setup**: In the production account, create a PAT with `repo` scope and store it as `PROD_TOKEN` in the dev repo's **Settings → Secrets**.

**Trade-off**: Automated and auditable; manifest is version-controlled alongside code.

---

## 3. Recommendation

1. Start with **§2.1** to nail down the manifest.
2. Once the file list is stable, migrate to **§2.2**.
3. Maintain the manifest at `deploy/manifest.txt` from the start either way.
