"""
API REST para Gerenciamento de Arquivos AWS S3
FastAPI + boto3
"""

import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, Query, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

# Importa o serviço S3 criado anteriormente
sys.path.insert(0, str(Path(__file__).parent))
from projetofiles.filesS3.s3_manager import S3Manager

# ─── Inicialização ────────────────────────────────────────────────────────────

def get_s3() -> S3Manager:
    key = os.getenv("AWS_ACCESS_KEY_ID")
    secret = os.getenv("AWS_SECRET_ACCESS_KEY")
    region = os.getenv("AWS_DEFAULT_REGION", "us-east-1")
    if not key or not secret:
        raise RuntimeError(
            "Credenciais AWS não configuradas. "
            "Defina AWS_ACCESS_KEY_ID e AWS_SECRET_ACCESS_KEY."
        )
    return S3Manager(
        aws_access_key_id=key,
        aws_secret_access_key=secret,
        aws_session_token=os.getenv("AWS_SESSION_TOKEN"),
        region_name=region,
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Valida credenciais na inicialização
    try:
        s3 = get_s3()
        s3.list_buckets()
        print("✅ Conexão com AWS S3 estabelecida.")
    except Exception as e:
        print(f"⚠️  Aviso: {e}")
    yield


app = FastAPI(
    title="S3 File Manager API",
    description="API REST para gerenciamento de arquivos no AWS S3",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def s3() -> S3Manager:
    """Dependency que retorna instância do S3Manager."""
    try:
        return get_s3()
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))


def http_error(e: Exception, default_status: int = 500) -> HTTPException:
    msg = str(e)
    code = default_status
    if "NoSuchBucket" in msg or "NoSuchKey" in msg or "404" in msg:
        code = 404
    elif "AccessDenied" in msg or "403" in msg:
        code = 403
    elif "BucketAlreadyExists" in msg or "BucketAlreadyOwnedByYou" in msg:
        code = 409
    return HTTPException(status_code=code, detail=msg)


# ═════════════════════════════════════════════════════════════════════════════
# BUCKETS
# ═════════════════════════════════════════════════════════════════════════════

@app.get("/buckets", tags=["Buckets"], summary="Listar todos os buckets")
def list_buckets():
    """Retorna todos os buckets disponíveis na conta AWS."""
    try:
        return {"buckets": s3().list_buckets()}
    except Exception as e:
        raise http_error(e)


@app.post("/buckets/{bucket_name}", tags=["Buckets"], status_code=201, summary="Criar bucket")
def create_bucket(
    bucket_name: str,
    region: str = Query(default=None, description="Região AWS (ex: sa-east-1)"),
    private: bool = Query(default=True, description="Bloquear acesso público"),
):
    """Cria um novo bucket S3. Por padrão bloqueia acesso público."""
    try:
        s3().create_bucket(bucket_name, region=region, private=private)
        return {"message": f"Bucket '{bucket_name}' criado com sucesso.", "bucket": bucket_name}
    except Exception as e:
        raise http_error(e)


@app.get("/buckets/{bucket_name}", tags=["Buckets"], summary="Verificar se bucket existe")
def check_bucket(bucket_name: str):
    """Verifica se um bucket existe e está acessível."""
    exists = s3().bucket_exists(bucket_name)
    if not exists:
        raise HTTPException(status_code=404, detail=f"Bucket '{bucket_name}' não encontrado.")
    return {"bucket": bucket_name, "exists": True}


@app.delete("/buckets/{bucket_name}", tags=["Buckets"], summary="Excluir bucket")
def delete_bucket(
    bucket_name: str,
    force: bool = Query(default=False, description="Excluir todos os objetos antes"),
):
    """
    Exclui um bucket S3.
    Use `force=true` para excluir o bucket mesmo que contenha objetos.
    """
    try:
        s3().delete_bucket(bucket_name, force=force)
        return {"message": f"Bucket '{bucket_name}' excluído com sucesso."}
    except Exception as e:
        raise http_error(e)


# ═════════════════════════════════════════════════════════════════════════════
# OBJETOS — LISTAGEM
# ═════════════════════════════════════════════════════════════════════════════

@app.get("/buckets/{bucket_name}/objects", tags=["Objetos"], summary="Listar objetos")
def list_objects(
    bucket_name: str,
    prefix: str = Query(default="", description="Filtrar por prefixo/pasta"),
    max_keys: int = Query(default=1000, ge=1, le=1000, description="Máximo de resultados"),
):
    """Lista objetos em um bucket, com suporte a filtro por prefixo."""
    try:
        objects = s3().list_objects(bucket_name, prefix=prefix, max_keys=max_keys)
        return {
            "bucket": bucket_name,
            "prefix": prefix,
            "count": len(objects),
            "objects": [
                {
                    "key": o.key,
                    "size": o.size,
                    "last_modified": o.last_modified.isoformat(),
                    "etag": o.etag,
                    "storage_class": o.storage_class,
                    "content_type": o.content_type,
                }
                for o in objects
            ],
        }
    except Exception as e:
        raise http_error(e)


@app.get("/buckets/{bucket_name}/folders", tags=["Objetos"], summary="Listar pastas")
def list_folders(
    bucket_name: str,
    prefix: str = Query(default="", description="Prefixo de busca"),
):
    """Lista 'pastas' (prefixos comuns) em um bucket usando o delimitador '/'."""
    try:
        folders = s3().list_folders(bucket_name, prefix=prefix)
        return {"bucket": bucket_name, "prefix": prefix, "folders": folders}
    except Exception as e:
        raise http_error(e)


@app.get("/buckets/{bucket_name}/objects/{key:path}/info", tags=["Objetos"], summary="Info do objeto")
def get_object_info(bucket_name: str, key: str):
    """Retorna informações detalhadas de um objeto (tamanho, tipo, metadados, etc.)."""
    try:
        obj = s3().get_object_info(bucket_name, key)
        if not obj:
            raise HTTPException(status_code=404, detail=f"Objeto '{key}' não encontrado.")
        return {
            "key": obj.key,
            "size": obj.size,
            "last_modified": obj.last_modified.isoformat(),
            "etag": obj.etag,
            "storage_class": obj.storage_class,
            "content_type": obj.content_type,
            "metadata": obj.metadata,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise http_error(e)


# ═════════════════════════════════════════════════════════════════════════════
# OBJETOS — UPLOAD
# ═════════════════════════════════════════════════════════════════════════════

@app.post(
    "/buckets/{bucket_name}/objects",
    tags=["Upload"],
    status_code=201,
    summary="Upload de arquivo",
)
async def upload_file(
    bucket_name: str,
    file: UploadFile = File(..., description="Arquivo a ser enviado"),
    key: str = Form(default=None, description="Chave no S3 (padrão: nome do arquivo)"),
    prefix: str = Form(default="", description="Pasta/prefixo no S3"),
    metadata: str = Form(default=None, description='Metadados em JSON (ex: {"autor":"joao"})'),
):
    """
    Faz upload de um arquivo para o S3.

    - O arquivo é enviado como `multipart/form-data`
    - Use `key` para definir o nome no S3, ou `prefix` para uma pasta
    - Use multipart upload automaticamente para arquivos grandes
    """
    import json

    s3_key = key or file.filename
    if prefix:
        s3_key = f"{prefix.rstrip('/')}/{s3_key}"

    meta = {}
    if metadata:
        try:
            meta = json.loads(metadata)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="'metadata' deve ser um JSON válido.")

    try:
        content = await file.read()
        from io import BytesIO
        result = s3().upload_fileobj(
            BytesIO(content),
            bucket_name,
            s3_key,
            metadata=meta,
            content_type=file.content_type or "application/octet-stream",
        )
        if not result.success:
            raise HTTPException(status_code=500, detail=result.error)

        return {
            "message": "Upload realizado com sucesso.",
            "bucket": bucket_name,
            "key": s3_key,
            "filename": file.filename,
            "size": len(content),
            "content_type": file.content_type,
            "url": result.url,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise http_error(e)


# ═════════════════════════════════════════════════════════════════════════════
# OBJETOS — DOWNLOAD
# ═════════════════════════════════════════════════════════════════════════════

@app.get(
    "/buckets/{bucket_name}/objects/{key:path}/download",
    tags=["Download"],
    summary="Download de arquivo",
)
def download_file(bucket_name: str, key: str):
    """
    Faz download de um objeto diretamente como stream de bytes.
    O navegador iniciará o download automaticamente.
    """
    from io import BytesIO

    try:
        info = s3().get_object_info(bucket_name, key)
        if not info:
            raise HTTPException(status_code=404, detail=f"Objeto '{key}' não encontrado.")

        buf = BytesIO()
        ok = s3().download_fileobj(bucket_name, key, buf)
        if not ok:
            raise HTTPException(status_code=500, detail="Erro ao baixar o arquivo.")

        buf.seek(0)
        filename = Path(key).name
        content_type = info.content_type or "application/octet-stream"

        return StreamingResponse(
            buf,
            media_type=content_type,
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except HTTPException:
        raise
    except Exception as e:
        raise http_error(e)


# ═════════════════════════════════════════════════════════════════════════════
# OBJETOS — OPERAÇÕES
# ═════════════════════════════════════════════════════════════════════════════

@app.post(
    "/buckets/{bucket_name}/objects/{key:path}/copy",
    tags=["Objetos"],
    status_code=201,
    summary="Copiar objeto",
)
def copy_object(
    bucket_name: str,
    key: str,
    dest_bucket: str = Query(..., description="Bucket de destino"),
    dest_key: str = Query(..., description="Chave de destino"),
):
    """Copia um objeto dentro do S3 sem fazer download/upload."""
    try:
        ok = s3().copy_object(bucket_name, key, dest_bucket, dest_key)
        if not ok:
            raise HTTPException(status_code=500, detail="Erro ao copiar objeto.")
        return {
            "message": "Objeto copiado com sucesso.",
            "source": {"bucket": bucket_name, "key": key},
            "destination": {"bucket": dest_bucket, "key": dest_key},
        }
    except HTTPException:
        raise
    except Exception as e:
        raise http_error(e)


@app.post(
    "/buckets/{bucket_name}/objects/{key:path}/move",
    tags=["Objetos"],
    summary="Mover objeto",
)
def move_object(
    bucket_name: str,
    key: str,
    dest_bucket: str = Query(..., description="Bucket de destino"),
    dest_key: str = Query(..., description="Chave de destino"),
):
    """Move um objeto (copia e exclui o original)."""
    try:
        ok = s3().move_object(bucket_name, key, dest_bucket, dest_key)
        if not ok:
            raise HTTPException(status_code=500, detail="Erro ao mover objeto.")
        return {
            "message": "Objeto movido com sucesso.",
            "source": {"bucket": bucket_name, "key": key},
            "destination": {"bucket": dest_bucket, "key": dest_key},
        }
    except HTTPException:
        raise
    except Exception as e:
        raise http_error(e)


@app.delete(
    "/buckets/{bucket_name}/objects/{key:path}",
    tags=["Objetos"],
    summary="Excluir objeto",
)
def delete_object(bucket_name: str, key: str):
    """Exclui um objeto do S3."""
    try:
        ok = s3().delete_object(bucket_name, key)
        if not ok:
            raise HTTPException(status_code=500, detail="Erro ao excluir objeto.")
        return {"message": f"Objeto '{key}' excluído com sucesso."}
    except HTTPException:
        raise
    except Exception as e:
        raise http_error(e)


@app.delete("/buckets/{bucket_name}/objects", tags=["Objetos"], summary="Excluir múltiplos objetos")
def delete_objects(
    bucket_name: str,
    keys: list[str] = Query(..., description="Lista de chaves a excluir"),
):
    """Exclui múltiplos objetos em lote (mais eficiente que exclusão individual)."""
    try:
        result = s3().delete_objects(bucket_name, keys)
        return {
            "deleted": result["deleted"],
            "errors": result["errors"],
            "total_deleted": len(result["deleted"]),
        }
    except Exception as e:
        raise http_error(e)


# ═════════════════════════════════════════════════════════════════════════════
# URLs PRESIGNADAS
# ═════════════════════════════════════════════════════════════════════════════

@app.get(
    "/buckets/{bucket_name}/objects/{key:path}/presign",
    tags=["URLs Presignadas"],
    summary="Gerar URL presignada para download",
)
def presign_download(
    bucket_name: str,
    key: str,
    expires: int = Query(default=3600, ge=60, le=604800, description="Validade em segundos"),
):
    """
    Gera uma URL temporária para download direto do S3.
    Válida por até 7 dias (604800 segundos).
    """
    try:
        url = s3().generate_presigned_url(bucket_name, key, operation="get_object", expiration=expires)
        if not url:
            raise HTTPException(status_code=500, detail="Erro ao gerar URL presignada.")
        return {"url": url, "expires_in": expires, "bucket": bucket_name, "key": key}
    except HTTPException:
        raise
    except Exception as e:
        raise http_error(e)


@app.get(
    "/buckets/{bucket_name}/objects/{key:path}/presign-upload",
    tags=["URLs Presignadas"],
    summary="Gerar URL presignada para upload",
)
def presign_upload(
    bucket_name: str,
    key: str,
    expires: int = Query(default=900, ge=60, le=3600, description="Validade em segundos"),
):
    """
    Gera uma URL temporária para upload direto ao S3 (sem passar pelo servidor).
    O cliente deve fazer um PUT HTTP para esta URL com o conteúdo do arquivo.
    """
    try:
        url = s3().generate_presigned_url(bucket_name, key, operation="put_object", expiration=expires)
        if not url:
            raise HTTPException(status_code=500, detail="Erro ao gerar URL de upload.")
        return {
            "url": url,
            "method": "PUT",
            "expires_in": expires,
            "bucket": bucket_name,
            "key": key,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise http_error(e)


@app.get(
    "/buckets/{bucket_name}/objects/{key:path}/presign-post",
    tags=["URLs Presignadas"],
    summary="Gerar POST presignado para upload via formulário",
)
def presign_post(
    bucket_name: str,
    key: str,
    expires: int = Query(default=3600, description="Validade em segundos"),
    max_size_mb: int = Query(default=10, ge=1, le=5120, description="Tamanho máximo do arquivo em MB"),
):
    """
    Gera dados para upload direto via formulário HTML (multipart/form-data).
    Retorna `url` e `fields` que devem ser usados no formulário do frontend.
    """
    try:
        data = s3().generate_presigned_post(bucket_name, key, expiration=expires, max_size_mb=max_size_mb)
        if not data:
            raise HTTPException(status_code=500, detail="Erro ao gerar POST presignado.")
        return {**data, "expires_in": expires, "max_size_mb": max_size_mb}
    except HTTPException:
        raise
    except Exception as e:
        raise http_error(e)


# ═════════════════════════════════════════════════════════════════════════════
# METADADOS E TAGS
# ═════════════════════════════════════════════════════════════════════════════

@app.get(
    "/buckets/{bucket_name}/objects/{key:path}/tags",
    tags=["Metadados"],
    summary="Listar tags de um objeto",
)
def get_tags(bucket_name: str, key: str):
    try:
        tags = s3().get_object_tags(bucket_name, key)
        return {"bucket": bucket_name, "key": key, "tags": tags}
    except Exception as e:
        raise http_error(e)


@app.put(
    "/buckets/{bucket_name}/objects/{key:path}/tags",
    tags=["Metadados"],
    summary="Atualizar tags de um objeto",
)
def put_tags(bucket_name: str, key: str, tags: dict):
    """Adiciona ou sobrescreve as tags de um objeto. Body: `{"chave": "valor"}`"""
    try:
        ok = s3().put_object_tags(bucket_name, key, tags)
        if not ok:
            raise HTTPException(status_code=500, detail="Erro ao salvar tags.")
        return {"message": "Tags atualizadas com sucesso.", "tags": tags}
    except HTTPException:
        raise
    except Exception as e:
        raise http_error(e)


@app.put(
    "/buckets/{bucket_name}/objects/{key:path}/metadata",
    tags=["Metadados"],
    summary="Atualizar metadados de um objeto",
)
def update_metadata(bucket_name: str, key: str, metadata: dict):
    """Atualiza os metadados de um objeto. Body: `{"chave": "valor"}`"""
    try:
        ok = s3().update_metadata(bucket_name, key, metadata)
        if not ok:
            raise HTTPException(status_code=500, detail="Erro ao atualizar metadados.")
        return {"message": "Metadados atualizados com sucesso.", "metadata": metadata}
    except HTTPException:
        raise
    except Exception as e:
        raise http_error(e)


# ═════════════════════════════════════════════════════════════════════════════
# HEALTH CHECK
# ═════════════════════════════════════════════════════════════════════════════

@app.get("/health", tags=["Sistema"], summary="Health check")
def health():
    """Verifica se a API está online e com credenciais AWS configuradas."""
    try:
        s3().list_buckets()
        return {"status": "ok", "aws": "conectado"}
    except Exception as e:
        return {"status": "degraded", "aws": "erro", "detail": str(e)}
