# 🪣 S3 File Manager — API REST

API REST para gerenciamento de arquivos no AWS S3, construída com **FastAPI**.

---

## Instalação

```bash
pip install -r requirements.txt
```

## Configuração

Copie o arquivo de exemplo e preencha com suas credenciais:

```bash
cp .env.example .env
```

```env
AWS_ACCESS_KEY_ID=sua_access_key
AWS_SECRET_ACCESS_KEY=sua_secret_key
AWS_DEFAULT_REGION=sa-east-1
CORS_ORIGINS=http://localhost:3000
```

## Iniciar o servidor

```bash
# Desenvolvimento (com auto-reload)
uvicorn main:app --reload --port 8000

# Produção
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

Acesse a documentação interativa em: **http://localhost:8000/docs**

---

## Endpoints

### 🟢 Sistema
| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/health` | Health check |

### 🪣 Buckets
| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/buckets` | Listar todos os buckets |
| POST | `/buckets/{bucket}` | Criar bucket |
| GET | `/buckets/{bucket}` | Verificar se existe |
| DELETE | `/buckets/{bucket}` | Excluir bucket |

### 📁 Objetos
| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/buckets/{bucket}/objects` | Listar objetos |
| GET | `/buckets/{bucket}/folders` | Listar pastas |
| POST | `/buckets/{bucket}/objects` | Upload de arquivo |
| GET | `/buckets/{bucket}/objects/{key}/info` | Info do objeto |
| GET | `/buckets/{bucket}/objects/{key}/download` | Download |
| POST | `/buckets/{bucket}/objects/{key}/copy` | Copiar objeto |
| POST | `/buckets/{bucket}/objects/{key}/move` | Mover objeto |
| DELETE | `/buckets/{bucket}/objects/{key}` | Excluir objeto |
| DELETE | `/buckets/{bucket}/objects` | Excluir em lote |

### 🔗 URLs Presignadas
| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/buckets/{bucket}/objects/{key}/presign` | URL de download temporária |
| GET | `/buckets/{bucket}/objects/{key}/presign-upload` | URL de upload temporária |
| GET | `/buckets/{bucket}/objects/{key}/presign-post` | POST para upload via form |

### 🏷️ Metadados
| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/buckets/{bucket}/objects/{key}/tags` | Listar tags |
| PUT | `/buckets/{bucket}/objects/{key}/tags` | Atualizar tags |
| PUT | `/buckets/{bucket}/objects/{key}/metadata` | Atualizar metadados |

---

## Exemplos de uso (curl)

```bash
# Health check
curl http://localhost:8000/health

# Listar buckets
curl http://localhost:8000/buckets

# Criar bucket
curl -X POST "http://localhost:8000/buckets/meu-bucket?region=sa-east-1"

# Listar objetos
curl "http://localhost:8000/buckets/meu-bucket/objects?prefix=imagens/"

# Upload de arquivo
curl -X POST http://localhost:8000/buckets/meu-bucket/objects \
  -F "file=@/caminho/foto.jpg" \
  -F "prefix=imagens/2024"

# Download de arquivo
curl -O http://localhost:8000/buckets/meu-bucket/objects/imagens/foto.jpg/download

# Gerar URL de download temporária (1 hora)
curl "http://localhost:8000/buckets/meu-bucket/objects/imagens/foto.jpg/presign?expires=3600"

# Copiar objeto
curl -X POST "http://localhost:8000/buckets/meu-bucket/objects/a.txt/copy?dest_bucket=outro-bucket&dest_key=copia.txt"

# Excluir objeto
curl -X DELETE http://localhost:8000/buckets/meu-bucket/objects/imagens/foto.jpg

# Excluir múltiplos objetos
curl -X DELETE "http://localhost:8000/buckets/meu-bucket/objects?keys=a.txt&keys=b.txt&keys=c.txt"

# Adicionar tags
curl -X PUT http://localhost:8000/buckets/meu-bucket/objects/foto.jpg/tags \
  -H "Content-Type: application/json" \
  -d '{"ambiente": "producao", "projeto": "site"}'
```

---

## Exemplo: Upload via frontend (JavaScript)

```js
// Upload direto pela API
async function uploadArquivo(arquivo, bucket, pasta) {
  const form = new FormData();
  form.append("file", arquivo);
  form.append("prefix", pasta);

  const res = await fetch(`http://localhost:8000/buckets/${bucket}/objects`, {
    method: "POST",
    body: form,
  });
  return res.json();
}

// Upload direto para o S3 via URL presignada (sem passar pelo servidor)
async function uploadPresignado(arquivo, bucket, key) {
  // 1. Busca a URL presignada da sua API
  const res = await fetch(
    `http://localhost:8000/buckets/${bucket}/objects/${key}/presign-upload`
  );
  const { url } = await res.json();

  // 2. Envia o arquivo diretamente para o S3
  await fetch(url, { method: "PUT", body: arquivo });
}
```

---

## Permissões IAM Necessárias

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Action": [
      "s3:ListAllMyBuckets", "s3:CreateBucket", "s3:DeleteBucket",
      "s3:PutBucketPublicAccessBlock", "s3:ListBucket",
      "s3:GetObject", "s3:PutObject", "s3:DeleteObject", "s3:CopyObject",
      "s3:GetObjectTagging", "s3:PutObjectTagging"
    ],
    "Resource": "*"
  }]
}
```
