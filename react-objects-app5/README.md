# Objects Manager — Web (React + Vite)

Frontend web para gerenciar objetos/arquivos em duas fontes, cada uma em
sua aba:

- **Local** — API REST `/local/objects` (upload, listagem e remoção de
  arquivos/pastas em disco).
- **S3** — API REST `/s3` (upload, listagem e remoção de objetos em um
  bucket S3).

Construído pensando em reuso futuro do mesmo padrão de API no app Android
e em uma futura integração de autenticação JWT via Keycloak.

## Rodando o projeto

Pré-requisito: Node.js 18+.

```bash
npm install
cp .env.example .env   # ajuste as URLs se suas APIs não estiverem nas portas padrão
npm run dev
```

A aplicação sobe em `http://localhost:5173`.

**CORS:** as duas APIs FastAPI precisam liberar a origem do Vite
(`http://localhost:5173`) no `CORSMiddleware`, senão o navegador bloqueia
as chamadas. Veja a seção de CORS mais abaixo.

## Endpoints consumidos

### Local (`VITE_API_BASE_URL`, padrão `http://localhost:8000`)

| Ação     | Método | Rota                                          |
|----------|--------|------------------------------------------------|
| Listar   | GET    | `/local/objects`                                |
| Enviar   | POST   | `/local/objects` (multipart, campo `arquivo`)   |
| Remover  | DELETE | `/local/objects/{nome_arquivo}`                 |
| Baixar   | GET    | `/local/objects/{nome_arquivo}`                 |

### S3 (`VITE_S3_API_BASE_URL`, padrão `http://localhost:5002`)

| Ação    | Método | Rota                                                              |
|---------|--------|---------------------------------------------------------------------|
| Listar  | GET    | `/s3`                                                              |
| Enviar  | POST   | `/s3?caminho_destino_s3=...` (multipart, campo `arquivo`)          |
| Remover | DELETE | `/s3?caminho_objeto_s3=...`                                        |

> O exemplo de `curl` do DELETE do S3 que você mandou usa a porta `8000`
> (`http://localhost:8000/s3?...`), mas o GET e o POST usam `5002`. Assumi
> que foi um typo e que o DELETE também é servido em `5002`, já que faz
> parte do mesmo recurso `/s3`. Se não for o caso, é só trocar
> `VITE_S3_API_BASE_URL` para apontar pra API certa, ou ajustar
> `deleteS3Object` em `src/api/s3Service.js` para usar um client próprio.

## Estrutura

```
src/
  api/
    httpClient.js         # fabrica de clientes HTTP (um por API/porta) + injecao de token
    objectsService.js      # listObjects / uploadObject / deleteObject (Local)
    s3Service.js            # listS3Objects / uploadS3Object / deleteS3Object (S3)
  auth/
    keycloakPlaceholder.js  # guia de como plugar o Keycloak quando chegar a hora
  hooks/
    useObjects.js           # estado da aba Local
    useS3Objects.js          # estado da aba S3
  components/
    Tabs.jsx                 # alterna entre as abas Local / S3
    LocalView.jsx             # composicao da aba Local (status bar + upload + tabela)
    S3View.jsx                 # composicao da aba S3
    UploadPanel.jsx            # drag-and-drop / selecao de arquivo (reutilizavel, aceita campos extras)
    ObjectsTable.jsx            # tabela da aba Local (arquivos + pastas)
    S3ObjectsTable.jsx           # tabela da aba S3 (chave, tamanho, data)
    StatusBar.jsx                 # barra de status generica (base URL + caminho + contagem)
  App.jsx
  main.jsx
```

A ideia é que **todas** as chamadas HTTP passem por `createHttpClient` em
`httpClient.js`. Isso significa que quando o JWT do Keycloak entrar em
cena, você só precisa:

1. Trocar a função `getAuthToken()` dentro de `httpClient.js` para
   retornar o token real (hoje ela retorna `null`). Como os dois clientes
   (`localHttpClient` e `s3HttpClient`) usam a mesma fábrica, o token
   passa a ser enviado nas duas APIs automaticamente.
2. Inicializar o `keycloak-js` em `main.jsx` (há um passo a passo comentado
   em `src/auth/keycloakPlaceholder.js`).

Nenhuma tela, hook ou service precisa ser alterado além disso.

## Sobre o formato das respostas

### Local — `GET /local/objects`

```json
{
  "caminho_solicitado": "/code",
  "total_arquivos": 2,
  "total_pastas": 1,
  "arquivos": ["image.png", "requirements.txt"],
  "pastas": ["app"]
}
```

`arquivos` e `pastas` são combinados em uma lista única de itens
`{ tipo, nome, caminho }`, onde `caminho` é montado como
`caminho_solicitado + "/" + nome`. Pastas são exibidas mas não têm botão
de remover (a API não deixou claro se `DELETE` funciona para pastas).

**Sobre `{nome_arquivo}` do DELETE/download local:** o backend resolve o
arquivo como `Path("/files") / nome_arquivo`, ou seja, `nome_arquivo` é
relativo à raiz fixa `/files` — na prática, para arquivos listados
diretamente (sem navegação em subpastas na UI), isso é só o **nome do
arquivo** (`obj.nome`), não o `caminho` completo com `caminho_solicitado`
na frente. É isso que o frontend usa hoje em `ObjectsTable.jsx`
(`onDelete(obj.nome)` / `getDownloadUrl(obj.nome)`).

Se no futuro a UI passar a navegar dentro das `pastas` retornadas pelo
`GET` (hoje elas só aparecem na lista, sem drill-down), o valor enviado
para `DELETE`/`GET` precisará virar o caminho relativo à raiz `/files`
incluindo essa subpasta (ex.: `app/data.txt`), não apenas o nome do
arquivo.

O botão **baixar** usa `getDownloadUrl(nome)`, que monta a URL completa
do `GET /local/objects/{nome_arquivo}` e vira um `<a href download>`
— como o backend já responde com `FileResponse` (que define
`Content-Disposition: attachment`), o navegador baixa o arquivo direto,
sem precisar de `fetch` + blob. **Atenção:** por ser uma navegação normal
(não uma chamada `fetch`), esse link **não** passa pelo `httpClient` — ou
seja, quando o JWT do Keycloak entrar em cena, esse botão de download
não vai enviar o token automaticamente. Nesse momento, será necessário
trocar para `fetch` + `blob` (baixando com o header `Authorization` e
criando um `URL.createObjectURL` manualmente) ou usar uma URL assinada
vinda do backend.

### S3 — `GET /s3`

```json
{
  "bucket": "filess3humberto",
  "prefixo_buscado": "",
  "total_objetos": 5,
  "objetos": [
    {
      "chave": "datasets/janeiro/dataset-sa.sh",
      "tamanho_bytes": 1153,
      "ultima_modificacao": "2026-07-07T18:27:06+00:00"
    }
  ]
}
```

Aqui a `chave` já vem como caminho completo dentro do bucket, então o
`DELETE` usa `chave` diretamente como `caminho_objeto_s3` — sem
necessidade de montar path manualmente.

O upload (`POST /s3?caminho_destino_s3=...`) tem um campo de texto na UI
para você digitar a pasta/prefixo de destino (ex.: `datasets/janeiro`)
antes de soltar o arquivo. Deixando em branco, o backend decide o
comportamento padrão.

O `GET /s3` também aceita busca por prefixo (`listS3Objects(prefixo)` já
está pronto em `s3Service.js`), mas a UI atual não expõe esse filtro —
é só plugar um campo de busca na `S3View` reaproveitando essa função se
precisar.

## CORS (FastAPI)

Ambos os backends (local e S3) precisam do `CORSMiddleware` liberando a
origem do Vite:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Próximos passos sugeridos

- [ ] Integrar `keycloak-js` e proteger as duas abas por login.
- [ ] Enviar o token JWT nas chamadas (`Authorization: Bearer ...`).
- [ ] Reaproveitar `objectsService.js`/`s3Service.js` como referência para
      o client HTTP do app Android (mesmos contratos de request/response).
- [ ] Expor busca por prefixo na aba S3 (função já existe em `s3Service.js`).
- [ ] Tratar upload de múltiplos arquivos, se as APIs vierem a suportar.
