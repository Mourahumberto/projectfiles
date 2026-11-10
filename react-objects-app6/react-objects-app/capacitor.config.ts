import type { CapacitorConfig } from '@capacitor/cli'

const config: CapacitorConfig = {
  appId: 'com.objectsmanager.app',
  appName: 'Objects Manager',
  webDir: 'dist',
  // bundledWebRuntime: false (padrao no Capacitor 6, nao precisa declarar)
  server: {
    // Durante o desenvolvimento, descomente e aponte para o IP da sua
    // maquina rodando "npm run dev" para ter live-reload no celular:
    // url: 'http://192.168.0.53:5173',
    // cleartext: true,
    androidScheme: 'https',
  },
}

export default config
