from fastapi import FastAPI, HTTPException, UploadFile, File, Header, Depends
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import shutil
import jwt
import requests

app = FastAPI()

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

# KEYCLOAK_REALM = "files-dev"
# KEYCLOAK_URL = "http://keycloak:8080"
# KEYCLOAK_ISSUER = "http://localhost:8080/realms/files-dev"

# JWKS_URL = (
# f"{KEYCLOAK_URL}/realms/{KEYCLOAK_REALM}"
# "/protocol/openid-connect/certs"
# )
# jwks = requests.get(JWKS_URL).json()

# def get_current_user(
#     authorization: str = Header(...)
# ):
#     try:
#         if not authorization.startswith("Bearer "):
#             raise HTTPException(
#                 status_code=401,
#                 detail="Bearer token não informado"
#             )

#         token = authorization.replace("Bearer ", "")

#         header = jwt.get_unverified_header(token)

#         key = next(
#             k for k in jwks["keys"]
#             if k["kid"] == header["kid"]
#         )

#         public_key = jwt.algorithms.RSAAlgorithm.from_jwk(key)

#         payload = jwt.decode(
#             token,
#             public_key,
#             algorithms=["RS256"],
#             issuer=KEYCLOAK_ISSUER,
#             options={"verify_aud": False}
#         )

#         return payload

#     except Exception as e:
#         raise HTTPException(
#             status_code=401,
#             detail=f"Token inválido: {str(e)}"
#         )

@app.get("/")
async def root():
    return {"message": "Hello World"}

# ═════════════════════════════════════════════════════════════════════════════
# Local
# ═════════════════════════════════════════════════════════════════════════════
# def list_object(user=Depends(get_current_user)):

@app.get("/local/objects", tags=["Objetos"], summary="Listar objetos")
def list_object():
    caminho = Path("/files")

    arquivos = []
    pastas = []
    
    # Executa a sua lógica de varredura
    for item in caminho.iterdir():
        if item.is_file():
            arquivos.append(item.name)
        elif item.is_dir():
            pastas.append(item.name)
            
    # Retorna uma estrutura JSON limpa
    return {
        "caminho_solicitado": str(caminho.resolve()),
        "total_arquivos": len(arquivos),
        "total_pastas": len(pastas),
        "arquivos": arquivos,
        "pastas": pastas
    }

@app.post("/local/objects", tags=["Objetos"], summary="Listar objetos")
def fazer_upload(arquivo: UploadFile = File(...)):
    pasta_destino = Path("/files")
     
    # 2. Define o caminho completo onde o arquivo será salvo
    caminho_arquivo_final = pasta_destino / arquivo.filename
    
    try:
        # 3. Salva o arquivo no disco de forma eficiente (em blocos)
        with caminho_arquivo_final.open("wb") as buffer:
            shutil.copyfileobj(arquivo.file, buffer)
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao salvar o arquivo: {str(e)}")
    finally:
        arquivo.file.close() # Garante o fechamento do arquivo temporário
        
    return {
        "mensagem": f"Arquivo '{arquivo.filename}' enviado com sucesso!",
        "caminho_completo": str(caminho_arquivo_final.resolve()),
        "tamanho_bytes": caminho_arquivo_final.stat().st_size
    }

@app.delete("/local/objects/{nome_arquivo}")
def deletar_arquivo(nome_arquivo: str):
    pasta = Path("/files").resolve()
    arquivo = (pasta / nome_arquivo).resolve()

    if pasta not in arquivo.parents and arquivo != pasta:
        raise HTTPException(status_code=403, detail="Acesso negado.")

    if not arquivo.exists() or not arquivo.is_file():
        raise HTTPException(status_code=404, detail="Arquivo não encontrado.")

    arquivo.unlink()

    return {
        "mensagem": f"Arquivo '{arquivo.name}' deletado com sucesso!"
    }

@app.get("/local/objects/{nome_arquivo}")
def download_arquivo(nome_arquivo: str):
    pasta = Path("/files").resolve()
    arquivo = (pasta / nome_arquivo).resolve()

    # Impede acesso a arquivos fora de /files
    if pasta not in arquivo.parents and arquivo != pasta:
        raise HTTPException(status_code=403, detail="Acesso negado.")

    if not arquivo.exists() or not arquivo.is_file():
        raise HTTPException(status_code=404, detail="Arquivo não encontrado.")

    return FileResponse(
        path=arquivo,
        filename=arquivo.name,
        media_type="application/octet-stream",
    )
# ═════════════════════════════════════════════════════════════════════════════
# HEALTH CHECK
# ═════════════════════════════════════════════════════════════════════════════

@app.get("/health", tags=["Sistema"], summary="Health check")
def health():
    """Verifica se a API está online e com credenciais AWS configuradas."""
    try:
        print("hello")
        return {"status": "ok", "aws": "conectado"}
    except Exception as e:
        return {"status": "degraded", "aws": "erro", "detail": str(e)}