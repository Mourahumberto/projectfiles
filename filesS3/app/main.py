import os
from fastapi import FastAPI, HTTPException, UploadFile, File
import boto3
from botocore.exceptions import NoCredentialsError, ClientError
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Carrega as variáveis do arquivo .env
load_dotenv()

app = FastAPI(title="Gerenciador de Arquivos S3 Completo")
origins = [
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],   # ou explicitamente ["GET", "POST", "DELETE", "OPTIONS"]
    allow_headers=["*"],
)
# Inicializa o cliente S3 (boto3 usa automaticamente as variáveis AWS do .env)
s3_client = boto3.client('s3')
# NOME_BUCKET = os.getenv("AWS_BUCKET_NAME")
NOME_BUCKET = "filess3humberto"

# Função auxiliar para garantir que o bucket está configurado
def verificar_bucket():
    if not NOME_BUCKET:
        raise HTTPException(
            status_code=500, 
            detail="Configuração AWS_BUCKET_NAME ausente no arquivo .env"
        )

# --- 1. ROTA DE UPLOAD (MANTIDA) ---
@app.post("/s3")
def upload_para_s3(caminho_destino_s3: str, arquivo: UploadFile = File(...)):
    verificar_bucket()
    pasta = caminho_destino_s3.strip("/")
    chave_s3 = f"{pasta}/{arquivo.filename}" if pasta else arquivo.filename
    
    try:
        s3_client.upload_fileobj(arquivo.file, NOME_BUCKET, chave_s3)
    except ClientError as e:
        raise HTTPException(status_code=500, detail=f"Erro AWS S3: {str(e)}")
    finally:
        arquivo.file.close()
        
    return {"mensagem": "Upload concluído", "bucket": NOME_BUCKET, "caminho_s3": chave_s3}


# --- 2. NOVA ROTA GET (LISTAR OBJETOS DO S3) ---
@app.get("/s3")
def listar_s3(prefixo: str = ""):
    verificar_bucket()
    # O prefixo serve para filtrar por uma "pasta" específica no S3 (ex: "datasets/")
    prefixo_limpo = prefixo.strip("/")
    if prefixo_limpo and not prefixo.endswith("/"):
        prefixo_limpo += "/"

    try:
        # Chama a API do S3 para listar os objetos
        resposta = s3_client.list_objects_v2(Bucket=NOME_BUCKET, Prefix=prefixo_limpo)
        
        # 'Contents' não existirá na resposta se o bucket ou prefixo estiverem vazios
        objetos = resposta.get('Contents', [])
        
        resultado = []
        for obj in objetos:
            resultado.append({
                "chave": obj['Key'],
                "tamanho_bytes": obj['Size'],
                "ultima_modificacao": obj['LastModified'].isoformat()
            })
            
        return {
            "bucket": NOME_BUCKET,
            "prefixo_buscado": prefixo_limpo,
            "total_objetos": len(resultado),
            "objetos": resultado
        }
        
    except ClientError as e:
        raise HTTPException(status_code=500, detail=f"Erro AWS S3: {str(e)}")


# --- 3. NOVA ROTA DELETE (REMOVER OBJETo DO S3) ---
@app.delete("/s3")
def deletar_s3(caminho_objeto_s3: str):
    verificar_bucket()
    chave_s3 = caminho_objeto_s3.lstrip("/")
    
    if not chave_s3:
        raise HTTPException(status_code=400, detail="O caminho do objeto não pode ser vazio.")
        
    try:
        # Verifica primeiro se o objeto realmente existe antes de tentar deletar
        # Nota: O S3 por padrão não retorna erro ao deletar um arquivo que não existe.
        try:
            s3_client.head_object(Bucket=NOME_BUCKET, Key=chave_s3)
        except ClientError as e:
            if e.response['Error']['Code'] == "404":
                raise HTTPException(status_code=404, detail="Objeto não encontrado no S3.")
            raise e

        # Executa a deleção
        s3_client.delete_object(Bucket=NOME_BUCKET, Key=chave_s3)
        
        return {
            "mensagem": f"Objeto '{chave_s3}' removido com sucesso do S3.",
            "bucket": NOME_BUCKET
        }
        
    except ClientError as e:
        raise HTTPException(status_code=500, detail=f"Erro AWS S3: {str(e)}")
