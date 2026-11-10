curl -X 'POST' \
  'http://localhost:8000/local/objects' \
  -H 'accept: application/json' \
  -H 'Content-Type: multipart/form-data' \
  -F 'arquivo=@/caminho/do/seu/arquivo/local.txt'

#NOVO#
curl -X POST \
  'http://localhost:8000/local/objects/{relatorios}' \
  -H 'accept: application/json' \
  -F 'arquivo=@/caminho/do/seu/arquivo.txt'


curl -X 'DELETE'   'http://localhost:5001/local/objects/dataset-sa.sh'   -H 'accept: application/json'

curl -X 'GET'   'http://localhost:8000/local/objects'
subpastas
curl "http://localhost:8000/local/objects?pasta=relatorios"
curl "http://localhost:8000/local/objects?pasta=relatorios/2026"
Como funciona
Requisição	Diretório consultado
/local/objects	/files
/local/objects?pasta=relatorios	/files/relatorios
/local/objects?pasta=relatorios/2026	/files/relatorios/2026

curl -X 'GET'   'http://localhost:5001/local/objects/IMG-20260715-WA0003.jpg' -H 'accept: application/json' --output teste.jpg