export DOCCANO_ADMIN_USERNAME="ann"
export DOCCANO_ADMIN_EMAIL="ann.tan@fiz-karlsruhe.de"
export DOCCANO_ADMIN_PASSWORD="D0c2@no"

docker pull doccano/doccano
docker container create --name doccano \
  -e "ADMIN_USERNAME=${DOCCANO_ADMIN_USERNAME}" \
  -e "ADMIN_EMAIL=${DOCCANO_ADMIN_EMAIL}" \
  -e "ADMIN_PASSWORD=${DOCCANO_ADMIN_PASSWORD}" \
  -v doccano-db:/Users/mta/Documents/claude/gemea/data/annotation/doccano/ \
  -p 42235:8000 doccano/doccano
