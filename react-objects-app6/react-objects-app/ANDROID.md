# Gerando o APK Android (Capacitor)

Este projeto já está preparado para o Capacitor. Os pacotes
(`@capacitor/core`, `@capacitor/android`, `@capacitor/cli`) já estão no
`package.json` e o `capacitor.config.ts` já existe na raiz. Falta rodar
os comandos abaixo **na sua máquina** (aqui no ambiente de geração do
projeto não há acesso ao registry do npm nem ao Android SDK/Gradle, então
essa parte precisa ser feita localmente).

## Pré-requisitos

- Node.js 18+
- [Android Studio](https://developer.android.com/studio) instalado (traz o Android SDK, o emulador e o Gradle já configurados)
- JDK 17 (o próprio Android Studio já resolve isso na maioria dos casos)

## Passo a passo

### 1. Instalar dependências e buildar o web app

```bash
npm install
cp .env.example .env
```

No `.env`, aponte as APIs para um **IP acessível pelo celular** — nunca
`localhost` (no celular, `localhost` é o próprio celular, não seu PC):

```
VITE_API_BASE_URL=http://192.168.0.53:5001
VITE_S3_API_BASE_URL=http://192.168.0.53:5002
```

```bash
npm run build
```

Isso gera a pasta `dist/`, que é o que o Capacitor empacota dentro do app.

### 2. Adicionar a plataforma Android

Isso só precisa ser feito uma vez (cria a pasta `android/` com o projeto
nativo):

```bash
npx cap add android
```

### 3. Liberar tráfego HTTP (cleartext) para suas APIs

Suas APIs rodam em `http://`, não `https://`. A partir do Android 9
(API 28), o sistema **bloqueia por padrão** conexões HTTP puras. É preciso
liberar isso explicitamente:

1. Copie o arquivo `android-config-template/network_security_config.xml`
   deste projeto para:
   ```
   android/app/src/main/res/xml/network_security_config.xml
   ```
   (crie a pasta `xml` se ela não existir) — e ajuste o(s) `<domain>`
   para o IP/host real da sua API.

2. Abra `android/app/src/main/AndroidManifest.xml` e adicione o atributo
   `android:networkSecurityConfig` na tag `<application>`:

   ```xml
   <application
       android:networkSecurityConfig="@xml/network_security_config"
       ...>
   ```

   A permissão `android.permission.INTERNET` já vem habilitada por
   padrão no template do Capacitor — não precisa mexer nela.

### 4. Sincronizar o build web com o projeto Android

Sempre que você alterar o código React e quiser refletir no app Android,
rode:

```bash
npm run cap:sync
```

(isso builda o Vite de novo e copia o resultado para dentro de
`android/app/src/main/assets/public`)

### 5. Gerar o APK

**Opção A — pelo Android Studio (recomendado para o primeiro build):**

```bash
npx cap open android
```

Isso abre o projeto no Android Studio. Lá: `Build` → `Build Bundle(s) / APK(s)`
→ `Build APK(s)`. O APK gerado fica em
`android/app/build/outputs/apk/debug/app-debug.apk`.

**Opção B — via linha de comando:**

```bash
npm run android:build
```

(equivale a `cap sync` + `./gradlew assembleDebug` dentro de `android/`)

O APK de debug já é instalável direto no celular (ative "Fontes
desconhecidas" nas configurações do Android, ou instale via
`adb install app-debug.apk`). Para publicar na Play Store ou distribuir
oficialmente, você vai precisar gerar um build **release** assinado — o
Android Studio tem um assistente pra isso (`Build` → `Generate Signed
Bundle / APK`).

## Testando no emulador vs. celular físico

- **Emulador do Android Studio:** o alias `10.0.2.2` aponta para o
  `localhost` da sua máquina — já incluí ele no
  `network_security_config.xml` de exemplo, mas seu `.env` também
  precisaria usar `http://10.0.2.2:5001` nesse caso específico.
- **Celular físico:** precisa estar na mesma rede Wi-Fi que o backend, e
  você usa o IP real da máquina (ex.: `192.168.0.53`), como já está no
  exemplo do `.env`.

## Live reload durante o desenvolvimento (opcional)

Se quiser ver as mudanças do React refletirem no app Android sem precisar
rebuildar toda vez, edite o `capacitor.config.ts` e descomente o bloco
`server.url` apontando para `npm run dev` (`http://SEU_IP:5173`) com
`cleartext: true`. Rode `npm run dev -- --host` (pra expor na rede) e
depois `npx cap sync android` uma vez. Lembre de reverter isso antes de
gerar o APK final de produção.

## Sobre o Keycloak (quando chegar a hora)

O `httpClient.js` já centraliza a injeção do token, então a mesma lógica
vale para o app Android — só que no lugar de `keycloak-js` (web), a lib
usada normalmente é `@capacitor-community/keycloak` ou um fluxo OAuth via
`@capacitor/browser` (login abre o browser do sistema e retorna o token
via deep link). Isso fica para quando a autenticação for implementada.
