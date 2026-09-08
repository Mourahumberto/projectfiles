curl -X 'POST' \
  'http://localhost:8000/local/objects' \
  -H 'accept: application/json' \
  -H 'Content-Type: multipart/form-data' \
  -F 'arquivo=@/caminho/do/seu/arquivo/local.txt'

curl -X 'DELETE'   'http://localhost:5001/local/objects/dataset-sa.sh'   -H 'accept: application/json'

curl -X 'GET'   'http://localhost:8000/local/objects'

curl -X 'GET'   'http://localhost:5001/local/objects/IMG-20260715-WA0003.jpg' -H 'accept: application/json' --output teste.jpg