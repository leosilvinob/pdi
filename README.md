# pdi
Projeto de PDI – 2025

## Fluxo atualizado (dez/2025)

- **ESP32 XIAO S3 Sense** executa `Face_Recognition/Face_Recognition.ino`. Ele:
  1. Liga câmera e Wi-Fi.
  2. Carrega pessoas registradas do SD.
  3. Aguarda novos cadastros via `/cadastrar`.
  4. A cada 3 s captura um frame, faz reconhecimento e mantém o último resultado em memória.
  5. Expõe os dados recentes em `GET /recognition`:
     - `format=json` (padrão) → `{"id":3,"nome":"Leo","vinculo":"dev","counter":4,...}`
     - `format=plain` → string `nome;vinculo;imagem;counter` (imagem vazio por enquanto).

- **App Inventor (appinventor/...)** agora usa Wi-Fi/HTTP:
  1. No campo **TextBoxServidor** insira `http://IP-do-ESP/recognition?format=plain`.
  2. Toque em **Iniciar monitoramento**. O app passa a chamar `/recognition` a cada 1,5 s.
  3. Quando o `counter` recebido muda, a tela atualiza `LabelNome`, `LabelRelacao`, limpa a imagem e o bloco `TextToSpeech` fala `Nome - Vínculo`.

### Ajustes rápidos

- Quer alternar para JSON? Chame `/recognition` sem parâmetros e decodifique o JSON retornado.
- Para mudar o intervalo do App Inventor, ajuste o `TimerInterval` de `Clock1` em `Screen1.scm`.

Com esse fluxo, não é mais necessário Bluetooth clássico (inexistente no XIAO ESP32-S3 Sense); basta que celular e ESP estejam na mesma rede Wi-Fi.
