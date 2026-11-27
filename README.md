# Laboratorio de b�squeda laboral con n8n

**Buscador de ofertas laborales** es un buscador sencillo que corre con modelos locales a trav�s de Ollama. n8n coordina las consultas a la API p�blica de Get on Board, y PostgreSQL puede conservar los avisos procesados.

La API p�blica de Get on Board es gratuita y no requiere autenticaci�n ni API key. Este proyecto usa el endpoint p�blico de b�squeda; no necesita credenciales de Get on Board.

![Interfaz del chat de b�squeda laboral](screenshots/chat.png)

![Workflow de n8n](screenshots/workflow-overview.png)

## Componentes

- **n8n**: orquesta el flujo y expone el Chat Trigger.
- **Ollama**: sirve el modelo local configurado en n8n (por ejemplo, `qwen3.5:9b`).
- **PostgreSQL**: base de datos del flujo y almacenamiento de avisos, seg�n la configuraci�n del workflow.
- **Chat web**: interfaz Flask que reenv�a mensajes a n8n y muestra las respuestas en Markdown.
- **Get on Board**: fuente de avisos usada por el workflow de ejemplo.

## Requisitos

- Docker Desktop con Docker Compose.
- Git, si vas a clonar el repositorio.
- Memoria y espacio disponibles para descargar y ejecutar el modelo elegido en Ollama.

## Inicio r�pido

1. Copi� `.env.example` a `.env`.

   ```powershell
   Copy-Item .env.example .env
   ```

2. Edit� `.env`: defin� una contrase�a propia para PostgreSQL, una clave larga y aleatoria para `N8N_ENCRYPTION_KEY`, y el identificador real del Chat Trigger en `N8N_CHAT_WEBHOOK_URL`. No publiques `.env`.
3. Inici� los servicios desde esta carpeta:

   ```powershell
   docker compose up -d --build
   ```

4. Abr� n8n en <http://localhost:5678> y la interfaz en <http://localhost:8081>.
5. Import� `workflows/buscador-ofertas-laborales.json`, configur� tus credenciales de Ollama y PostgreSQL, y public� el Chat Trigger.
6. Descarg� el modelo que elegiste en Ollama:

   ```powershell
   docker compose exec ollama ollama pull qwen3.5:9b
   ```

   En la credencial de Ollama de n8n, us� `http://ollama:11434` como direcci�n desde la red Docker.

## Configuraci�n del Chat Trigger

En el nodo **Chat Trigger**, habilit� el chat p�blico y seleccion� **Embedded Chat**. Configur� la respuesta para que devuelva la salida final del flujo. Copi� la URL de producci�n del Chat Trigger a `N8N_CHAT_WEBHOOK_URL`; desde el contenedor `chat-web`, el host debe ser `n8n`, no `localhost`.

El archivo `.env.example` contiene la URL de ejemplo con un identificador de marcador. Reemplazalo por el identificador del webhook de tu propia instancia.

## Workflow de ejemplo

El workflow de ejemplo est� exportado en `workflows/`. Al importarlo en tu instancia, volv� a asignar las credenciales de Ollama y PostgreSQL. El export trae un ID de ejemplo para el Chat Trigger; copi� su Chat URL a `.env`.

Antes de compartir un workflow:

- quit� datos de credenciales y encabezados de autorizaci�n;
- sustitu� IDs de webhooks, URLs locales o identificadores personales por marcadores documentados;
- revis� que no haya ejecuciones fijadas con conversaciones, datos personales o avisos privados;
- document� qu� credenciales debe crear cada persona que lo importe.

No exportes la base de datos de n8n ni sus vol�menes como parte del repositorio.

## Comandos �tiles

```powershell
docker compose ps
docker compose logs -f n8n
docker compose logs -f chat-web
docker compose down
```

Los datos persisten en vol�menes Docker. `docker compose down -v` tambi�n los elimina; usalo solo cuando quieras borrar el estado local del laboratorio.

## Privacidad y seguridad

- `.env` est� excluido de Git; public� solo `.env.example` con marcadores.
- No guardes contrase�as, tokens, credenciales ni datos de conversaciones en capturas o exports.
- Las publicaciones laborales provienen de un servicio externo y pueden cambiar o desaparecer.
- Este proyecto es un laboratorio educativo; revis� el aviso original antes de postularte.

## Uso de la API de Get on Board

El proyecto consulta la API p�blica de Get on Board, que es gratuita y no requiere autenticaci�n. Respet� sus condiciones de uso: atribu� la fuente a Get on Board, enlaz� cada aviso a su publicaci�n original y envi� all� a las personas que quieran postularse. Las condiciones tambi�n indican mostrar los datos sin alterarlos, mantenerlos actualizados al menos cada 24 horas, no revenderlos y no usarlos para entrenar modelos. Revis� las [condiciones y documentaci�n oficial](https://www.getonbrd.com/api-doc) antes de adaptar o republicar los datos.

## Capturas de pantalla

Las capturas incluidas muestran la interfaz de chat y la vista general del workflow. Se revisaron para evitar correos, credenciales y URLs/IDs privados. Si las reemplaz�s, verific� que no aparezcan webhooks completos, claves, datos personales ni historial de ejecuci�n.

## Licencia

Este proyecto se distribuye bajo la licencia [MIT](LICENSE).
