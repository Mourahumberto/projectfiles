"""
Serviço de Gerenciamento de Arquivos para AWS S3
"""

import os
import mimetypes
from pathlib import Path
from typing import Optional, List, Dict, Any, BinaryIO
from dataclasses import dataclass, field
from datetime import datetime

import boto3
from boto3.s3.transfer import TransferConfig
from botocore.exceptions import ClientError, NoCredentialsError


@dataclass
class S3Object:
    key: str
    size: int
    last_modified: datetime
    etag: str
    storage_class: str = "STANDARD"
    content_type: Optional[str] = None
    metadata: Dict[str, str] = field(default_factory=dict)

    def __str__(self) -> str:
        size_str = self._format_size(self.size)
        return f"{self.key} ({size_str}) - {self.last_modified.strftime('%Y-%m-%d %H:%M:%S')}"

    @staticmethod
    def _format_size(size_bytes: int) -> str:
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f} PB"


@dataclass
class UploadResult:
    success: bool
    bucket: str
    key: str
    etag: Optional[str] = None
    url: Optional[str] = None
    error: Optional[str] = None


@dataclass
class DownloadResult:
    success: bool
    local_path: Optional[str] = None
    size: Optional[int] = None
    error: Optional[str] = None


class S3Manager:
    """
    Serviço completo de gerenciamento de arquivos para AWS S3.

    Funcionalidades:
    - Upload de arquivos (simples e multipart)
    - Download de arquivos
    - Listagem de objetos e buckets
    - Cópia e movimentação de objetos
    - Exclusão de objetos e buckets
    - Geração de URLs presignadas
    - Gerenciamento de metadados
    - Controle de permissões (ACL)
    """

    # Threshold para multipart upload (padrão: 8 MB)
    MULTIPART_THRESHOLD = 8 * 1024 * 1024
    # Tamanho de cada parte no multipart (padrão: 8 MB)
    MULTIPART_CHUNKSIZE = 8 * 1024 * 1024

    def __init__(
        self,
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
        aws_session_token: Optional[str] = None,
        region_name: str = "us-east-1",
        profile_name: Optional[str] = None,
    ):
        """
        Inicializa o S3Manager.

        Credenciais podem ser passadas diretamente ou via variáveis de ambiente:
        - AWS_ACCESS_KEY_ID
        - AWS_SECRET_ACCESS_KEY
        - AWS_SESSION_TOKEN (opcional, para credenciais temporárias)
        - AWS_DEFAULT_REGION

        Args:
            aws_access_key_id: Chave de acesso AWS
            aws_secret_access_key: Chave secreta AWS
            aws_session_token: Token de sessão (opcional)
            region_name: Região AWS (padrão: us-east-1)
            profile_name: Nome do perfil AWS CLI (opcional)
        """
        session_kwargs: Dict[str, Any] = {"region_name": region_name}

        if profile_name:
            session_kwargs["profile_name"] = profile_name

        session = boto3.Session(**session_kwargs)

        client_kwargs: Dict[str, Any] = {}
        if aws_access_key_id:
            client_kwargs["aws_access_key_id"] = aws_access_key_id
        if aws_secret_access_key:
            client_kwargs["aws_secret_access_key"] = aws_secret_access_key
        if aws_session_token:
            client_kwargs["aws_session_token"] = aws_session_token

        self.s3 = session.client("s3", **client_kwargs)
        self.region = region_name

        self._transfer_config = TransferConfig(
            multipart_threshold=self.MULTIPART_THRESHOLD,
            multipart_chunksize=self.MULTIPART_CHUNKSIZE,
            max_concurrency=10,
            use_threads=True,
        )

    # ─────────────────────────────────────────────
    # BUCKETS
    # ─────────────────────────────────────────────

    def list_buckets(self) -> List[Dict[str, Any]]:
        """Lista todos os buckets disponíveis na conta."""
        try:
            response = self.s3.list_buckets()
            return [
                {
                    "name": b["Name"],
                    "created_at": b["CreationDate"].strftime("%Y-%m-%d %H:%M:%S"),
                }
                for b in response.get("Buckets", [])
            ]
        except (ClientError, NoCredentialsError) as e:
            raise RuntimeError(f"Erro ao listar buckets: {e}") from e

    def create_bucket(
        self,
        bucket_name: str,
        region: Optional[str] = None,
        private: bool = True,
    ) -> bool:
        """
        Cria um novo bucket S3.

        Args:
            bucket_name: Nome do bucket
            region: Região (usa a região padrão se não informada)
            private: Se True, bloqueia acesso público (recomendado)
        """
        region = region or self.region
        try:
            kwargs: Dict[str, Any] = {"Bucket": bucket_name}
            if region != "us-east-1":
                kwargs["CreateBucketConfiguration"] = {"LocationConstraint": region}

            self.s3.create_bucket(**kwargs)

            if private:
                self.s3.put_public_access_block(
                    Bucket=bucket_name,
                    PublicAccessBlockConfiguration={
                        "BlockPublicAcls": True,
                        "IgnorePublicAcls": True,
                        "BlockPublicPolicy": True,
                        "RestrictPublicBuckets": True,
                    },
                )

            return True
        except ClientError as e:
            raise RuntimeError(f"Erro ao criar bucket '{bucket_name}': {e}") from e

    def delete_bucket(self, bucket_name: str, force: bool = False) -> bool:
        """
        Exclui um bucket S3.

        Args:
            bucket_name: Nome do bucket
            force: Se True, exclui todos os objetos antes de deletar o bucket
        """
        try:
            if force:
                self.delete_all_objects(bucket_name)

            self.s3.delete_bucket(Bucket=bucket_name)
            return True
        except ClientError as e:
            raise RuntimeError(f"Erro ao excluir bucket '{bucket_name}': {e}") from e

    def bucket_exists(self, bucket_name: str) -> bool:
        """Verifica se um bucket existe e está acessível."""
        try:
            self.s3.head_bucket(Bucket=bucket_name)
            return True
        except ClientError:
            return False

    # ─────────────────────────────────────────────
    # UPLOAD
    # ─────────────────────────────────────────────

    def upload_file(
        self,
        local_path: str,
        bucket_name: str,
        s3_key: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None,
        content_type: Optional[str] = None,
        acl: Optional[str] = None,
        progress_callback=None,
    ) -> UploadResult:
        """
        Faz upload de um arquivo local para o S3.
        Usa multipart upload automaticamente para arquivos grandes.

        Args:
            local_path: Caminho do arquivo local
            bucket_name: Nome do bucket de destino
            s3_key: Chave no S3 (usa o nome do arquivo se não informado)
            metadata: Metadados extras do objeto
            content_type: Content-Type (detectado automaticamente se não informado)
            acl: ACL do objeto (ex: 'private', 'public-read')
            progress_callback: Função de callback para progresso (bytes_transferred)
        """
        path = Path(local_path)
        if not path.exists():
            return UploadResult(False, bucket_name, "", error=f"Arquivo não encontrado: {local_path}")

        s3_key = s3_key or path.name
        content_type = content_type or mimetypes.guess_type(local_path)[0] or "application/octet-stream"

        extra_args: Dict[str, Any] = {"ContentType": content_type}
        if metadata:
            extra_args["Metadata"] = metadata
        if acl:
            extra_args["ACL"] = acl

        try:
            self.s3.upload_file(
                Filename=local_path,
                Bucket=bucket_name,
                Key=s3_key,
                ExtraArgs=extra_args,
                Config=self._transfer_config,
                Callback=progress_callback,
            )
            head = self.s3.head_object(Bucket=bucket_name, Key=s3_key)
            url = f"https://{bucket_name}.s3.{self.region}.amazonaws.com/{s3_key}"
            return UploadResult(True, bucket_name, s3_key, etag=head["ETag"], url=url)
        except ClientError as e:
            return UploadResult(False, bucket_name, s3_key, error=str(e))

    def upload_fileobj(
        self,
        file_obj: BinaryIO,
        bucket_name: str,
        s3_key: str,
        metadata: Optional[Dict[str, str]] = None,
        content_type: str = "application/octet-stream",
    ) -> UploadResult:
        """Faz upload de um objeto de arquivo (file-like object) para o S3."""
        extra_args: Dict[str, Any] = {"ContentType": content_type}
        if metadata:
            extra_args["Metadata"] = metadata
        try:
            self.s3.upload_fileobj(
                Fileobj=file_obj,
                Bucket=bucket_name,
                Key=s3_key,
                ExtraArgs=extra_args,
                Config=self._transfer_config,
            )
            url = f"https://{bucket_name}.s3.{self.region}.amazonaws.com/{s3_key}"
            return UploadResult(True, bucket_name, s3_key, url=url)
        except ClientError as e:
            return UploadResult(False, bucket_name, s3_key, error=str(e))

    def upload_directory(
        self,
        local_dir: str,
        bucket_name: str,
        s3_prefix: str = "",
        recursive: bool = True,
    ) -> List[UploadResult]:
        """
        Faz upload de um diretório inteiro para o S3.

        Args:
            local_dir: Caminho do diretório local
            bucket_name: Nome do bucket de destino
            s3_prefix: Prefixo/pasta no S3
            recursive: Se True, inclui subdiretórios
        """
        results = []
        base_path = Path(local_dir)

        pattern = "**/*" if recursive else "*"
        for file_path in base_path.glob(pattern):
            if file_path.is_file():
                relative = file_path.relative_to(base_path)
                s3_key = f"{s3_prefix}/{relative}".lstrip("/") if s3_prefix else str(relative)
                result = self.upload_file(str(file_path), bucket_name, s3_key)
                results.append(result)

        return results

    # ─────────────────────────────────────────────
    # DOWNLOAD
    # ─────────────────────────────────────────────

    def download_file(
        self,
        bucket_name: str,
        s3_key: str,
        local_path: Optional[str] = None,
        progress_callback=None,
    ) -> DownloadResult:
        """
        Faz download de um objeto do S3 para um arquivo local.

        Args:
            bucket_name: Nome do bucket
            s3_key: Chave do objeto no S3
            local_path: Caminho local de destino (usa o nome do key se não informado)
            progress_callback: Função de callback para progresso
        """
        local_path = local_path or Path(s3_key).name
        Path(local_path).parent.mkdir(parents=True, exist_ok=True)

        try:
            head = self.s3.head_object(Bucket=bucket_name, Key=s3_key)
            size = head["ContentLength"]

            self.s3.download_file(
                Bucket=bucket_name,
                Key=s3_key,
                Filename=local_path,
                Config=self._transfer_config,
                Callback=progress_callback,
            )
            return DownloadResult(True, local_path=local_path, size=size)
        except ClientError as e:
            return DownloadResult(False, error=str(e))

    def download_fileobj(self, bucket_name: str, s3_key: str, file_obj: BinaryIO) -> bool:
        """Faz download de um objeto do S3 para um objeto de arquivo (file-like)."""
        try:
            self.s3.download_fileobj(bucket_name, s3_key, file_obj, Config=self._transfer_config)
            return True
        except ClientError:
            return False

    # ─────────────────────────────────────────────
    # LISTAGEM
    # ─────────────────────────────────────────────

    def list_objects(
        self,
        bucket_name: str,
        prefix: str = "",
        delimiter: str = "",
        max_keys: int = 1000,
    ) -> List[S3Object]:
        """
        Lista objetos em um bucket.

        Args:
            bucket_name: Nome do bucket
            prefix: Filtro por prefixo/pasta
            delimiter: Delimitador para simular estrutura de pastas (ex: '/')
            max_keys: Número máximo de objetos retornados
        """
        objects = []
        kwargs: Dict[str, Any] = {
            "Bucket": bucket_name,
            "MaxKeys": max_keys,
        }
        if prefix:
            kwargs["Prefix"] = prefix
        if delimiter:
            kwargs["Delimiter"] = delimiter

        paginator = self.s3.get_paginator("list_objects_v2")
        for page in paginator.paginate(**kwargs):
            for obj in page.get("Contents", []):
                objects.append(
                    S3Object(
                        key=obj["Key"],
                        size=obj["Size"],
                        last_modified=obj["LastModified"],
                        etag=obj["ETag"].strip('"'),
                        storage_class=obj.get("StorageClass", "STANDARD"),
                    )
                )
        return objects

    def list_folders(self, bucket_name: str, prefix: str = "") -> List[str]:
        """Lista 'pastas' (prefixos comuns) em um bucket usando o delimitador '/'."""
        response = self.s3.list_objects_v2(
            Bucket=bucket_name,
            Prefix=prefix,
            Delimiter="/",
        )
        return [cp["Prefix"] for cp in response.get("CommonPrefixes", [])]

    # ─────────────────────────────────────────────
    # OPERAÇÕES EM OBJETOS
    # ─────────────────────────────────────────────

    def object_exists(self, bucket_name: str, s3_key: str) -> bool:
        """Verifica se um objeto existe no S3."""
        try:
            self.s3.head_object(Bucket=bucket_name, Key=s3_key)
            return True
        except ClientError:
            return False

    def get_object_info(self, bucket_name: str, s3_key: str) -> Optional[S3Object]:
        """Retorna informações detalhadas de um objeto."""
        try:
            head = self.s3.head_object(Bucket=bucket_name, Key=s3_key)
            return S3Object(
                key=s3_key,
                size=head["ContentLength"],
                last_modified=head["LastModified"],
                etag=head["ETag"].strip('"'),
                storage_class=head.get("StorageClass", "STANDARD"),
                content_type=head.get("ContentType"),
                metadata=head.get("Metadata", {}),
            )
        except ClientError:
            return None

    def copy_object(
        self,
        source_bucket: str,
        source_key: str,
        dest_bucket: str,
        dest_key: str,
    ) -> bool:
        """Copia um objeto dentro do S3 (sem download/upload)."""
        try:
            self.s3.copy_object(
                CopySource={"Bucket": source_bucket, "Key": source_key},
                Bucket=dest_bucket,
                Key=dest_key,
            )
            return True
        except ClientError:
            return False

    def move_object(
        self,
        source_bucket: str,
        source_key: str,
        dest_bucket: str,
        dest_key: str,
    ) -> bool:
        """Move um objeto (copia e exclui o original)."""
        if self.copy_object(source_bucket, source_key, dest_bucket, dest_key):
            return self.delete_object(source_bucket, source_key)
        return False

    def delete_object(self, bucket_name: str, s3_key: str) -> bool:
        """Exclui um único objeto do S3."""
        try:
            self.s3.delete_object(Bucket=bucket_name, Key=s3_key)
            return True
        except ClientError:
            return False

    def delete_objects(self, bucket_name: str, keys: List[str]) -> Dict[str, Any]:
        """
        Exclui múltiplos objetos em lote (mais eficiente que exclusão individual).
        Retorna dict com 'deleted' e 'errors'.
        """
        if not keys:
            return {"deleted": [], "errors": []}

        # S3 aceita no máximo 1000 objetos por requisição
        deleted_all, errors_all = [], []
        for i in range(0, len(keys), 1000):
            batch = keys[i : i + 1000]
            try:
                resp = self.s3.delete_objects(
                    Bucket=bucket_name,
                    Delete={"Objects": [{"Key": k} for k in batch]},
                )
                deleted_all.extend([d["Key"] for d in resp.get("Deleted", [])])
                errors_all.extend(resp.get("Errors", []))
            except ClientError as e:
                errors_all.append({"Error": str(e)})

        return {"deleted": deleted_all, "errors": errors_all}

    def delete_all_objects(self, bucket_name: str, prefix: str = "") -> int:
        """Exclui todos os objetos de um bucket (ou de um prefixo). Retorna a quantidade excluída."""
        objects = self.list_objects(bucket_name, prefix=prefix)
        if not objects:
            return 0
        keys = [obj.key for obj in objects]
        result = self.delete_objects(bucket_name, keys)
        return len(result["deleted"])

    # ─────────────────────────────────────────────
    # URLs PRESIGNADAS
    # ─────────────────────────────────────────────

    def generate_presigned_url(
        self,
        bucket_name: str,
        s3_key: str,
        operation: str = "get_object",
        expiration: int = 3600,
    ) -> Optional[str]:
        """
        Gera uma URL presignada para acesso temporário a um objeto.

        Args:
            bucket_name: Nome do bucket
            s3_key: Chave do objeto
            operation: 'get_object' (download) ou 'put_object' (upload)
            expiration: Tempo de validade em segundos (padrão: 1 hora)
        """
        try:
            return self.s3.generate_presigned_url(
                ClientMethod=operation,
                Params={"Bucket": bucket_name, "Key": s3_key},
                ExpiresIn=expiration,
            )
        except ClientError:
            return None

    def generate_presigned_post(
        self,
        bucket_name: str,
        s3_key: str,
        expiration: int = 3600,
        max_size_mb: int = 10,
    ) -> Optional[Dict[str, Any]]:
        """
        Gera dados para upload direto via formulário HTML (POST presignado).
        Útil para upload direto do browser sem passar pelo seu servidor.

        Retorna dict com 'url' e 'fields'.
        """
        try:
            return self.s3.generate_presigned_post(
                Bucket=bucket_name,
                Key=s3_key,
                Conditions=[["content-length-range", 1, max_size_mb * 1024 * 1024]],
                ExpiresIn=expiration,
            )
        except ClientError:
            return None

    # ─────────────────────────────────────────────
    # METADADOS E TAGS
    # ─────────────────────────────────────────────

    def update_metadata(
        self,
        bucket_name: str,
        s3_key: str,
        metadata: Dict[str, str],
    ) -> bool:
        """
        Atualiza os metadados de um objeto (faz uma cópia in-place no S3).
        """
        try:
            head = self.s3.head_object(Bucket=bucket_name, Key=s3_key)
            self.s3.copy_object(
                Bucket=bucket_name,
                Key=s3_key,
                CopySource={"Bucket": bucket_name, "Key": s3_key},
                Metadata=metadata,
                MetadataDirective="REPLACE",
                ContentType=head.get("ContentType", "application/octet-stream"),
            )
            return True
        except ClientError:
            return False

    def put_object_tags(self, bucket_name: str, s3_key: str, tags: Dict[str, str]) -> bool:
        """Adiciona ou sobrescreve as tags de um objeto."""
        try:
            self.s3.put_object_tagging(
                Bucket=bucket_name,
                Key=s3_key,
                Tagging={"TagSet": [{"Key": k, "Value": v} for k, v in tags.items()]},
            )
            return True
        except ClientError:
            return False

    def get_object_tags(self, bucket_name: str, s3_key: str) -> Dict[str, str]:
        """Retorna as tags de um objeto."""
        try:
            resp = self.s3.get_object_tagging(Bucket=bucket_name, Key=s3_key)
            return {t["Key"]: t["Value"] for t in resp.get("TagSet", [])}
        except ClientError:
            return {}
