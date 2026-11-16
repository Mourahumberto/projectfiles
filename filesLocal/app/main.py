from fastapi import FastAPI, HTTPException, UploadFile, File, Header, Depends, Query
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
def list_object(pasta: str = Query(default="")):
    pasta_base = Path("/files").resolve()

    # Se pasta não for informada, utiliza /files
    caminho = (pasta_base / pasta).resolve()

    # Impede acesso a diretórios fora de /files
    if not caminho.is_relative_to(pasta_base):
        raise HTTPException(
            status_code=400,
            detail="Caminho inválido"
        )

    if not caminho.exists():
        raise HTTPException(
            status_code=404,
            detail="Pasta não encontrada"
        )

    if not caminho.is_dir():
        raise HTTPException(
            status_code=400,
            detail="O caminho informado não é uma pasta"
        )

    arquivos = []
    pastas = []

    for item in caminho.iterdir():
        if item.is_file():
            arquivos.append(item.name)
        elif item.is_dir():
            pastas.append(item.name)

    return {
        "caminho_solicitado": str(caminho),
        "total_arquivos": len(arquivos),
        "total_pastas": len(pastas),
        "arquivos": arquivos,
        "pastas": pastas
    }

@app.post("/local/objects", tags=["Objetos"], summary="Enviar múltiplos arquivos")
def fazer_upload(
    arquivos: list[UploadFile] = File(...),
    pasta: str = Query(default="")
):
    pasta_base = Path("/files").resolve()
    pasta_destino = (pasta_base / pasta).resolve()

    if not pasta_destino.is_relative_to(pasta_base):
        raise HTTPException(status_code=400, detail="Pasta inválida")

    pasta_destino.mkdir(parents=True, exist_ok=True)

    resultados = []

    try:
        for arquivo in arquivos:
            nome_arquivo = Path(arquivo.filename or "").name

            if not nome_arquivo:
                raise HTTPException(
                    status_code=400,
                    detail="Nome de arquivo inválido"
                )

            caminho_final = pasta_destino / nome_arquivo

            with caminho_final.open("wb") as buffer:
                shutil.copyfileobj(arquivo.file, buffer)

            resultados.append({
                "arquivo": nome_arquivo,
                "caminho_completo": str(caminho_final),
                "tamanho_bytes": caminho_final.stat().st_size
            })

        return {
            "mensagem": "Upload concluído",
            "total_arquivos": len(resultados),
            "arquivos": resultados
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao salvar arquivos: {str(e)}"
        )
    finally:
        for arquivo in arquivos:
            arquivo.file.close()


@app.delete("/local/objects/{caminho_arquivo:path}", tags=["Objetos"], summary="Deletar arquivo")
def deletar_arquivo(caminho_arquivo: str):
    pasta = Path("/files").resolve()
    arquivo = (pasta / caminho_arquivo).resolve()

    if pasta not in arquivo.parents and arquivo != pasta:
        raise HTTPException(status_code=403, detail="Acesso negado.")

    if not arquivo.exists() or not arquivo.is_file():
        raise HTTPException(status_code=404, detail="Arquivo não encontrado.")

    arquivo.unlink()

    return {
        "mensagem": f"Arquivo '{arquivo.name}' deletado com sucesso!"
    }

@app.get("/local/objects/{caminho_arquivo:path}", tags=["Objetos"], summary="Download de arquivo")
def download_arquivo(caminho_arquivo: str):
    pasta = Path("/files").resolve()
    arquivo = (pasta / caminho_arquivo).resolve()

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