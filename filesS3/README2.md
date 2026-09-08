curl -X 'POST' \
  'http://localhost:5002/s3?caminho_destino_s3=datasets/janeiro' \
  -H 'accept: application/json' \
  -H 'Content-Type: multipart/form-data' \
  -F 'arquivo=@/caminho/do/seu/arquivo/local.txt'

curl -X 'DELETE' \
  'http://localhost:5002/s3?caminho_objeto_s3=datasets/janeiro/local.txt' \
  -H 'accept: application/json'

curl -X 'GET' \
  'http://localhost:5002/s3?prefixo=datasets' \
  -H 'accept: application/json'
