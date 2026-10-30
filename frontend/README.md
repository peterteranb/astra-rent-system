# Frontend en React

Las pantallas del sistema hechas con React y Vite. No tienen reglas propias: todo lo piden a la API JSON de Django bajo `/api/` (contrato en [`docs/api.md`](../docs/api.md)).

## Cómo corre hoy: modo desarrollo, con dos servidores

1. **Django** en el puerto 8080 (desde la raíz del proyecto, con el entorno activado):

   ```powershell
   python manage.py runserver 8080
   ```

2. **Vite** en el puerto 5173 (en otra terminal):

   ```powershell
   cd frontend
   npm install     # solo la primera vez
   npm run dev
   ```

3. Abre `http://localhost:5173`.

Vite reenvía todo lo que empieza con `/api/` a `http://127.0.0.1:8080` (`vite.config.js`). Para el navegador es un solo sitio, así que la cookie de sesión y la de CSRF funcionan sin configurar CORS. Si Django está apagado, las pantallas muestran errores de red.

El enlace «Admin» del menú abre el admin de Django en `http://localhost:8080/admin/`.

## Por el túnel público

`vite.config.js` acepta los dominios `*.trycloudflare.com` (`allowedHosts`). Con `npm run dev` corriendo, en otra terminal:

```powershell
cloudflared tunnel --url http://localhost:5173
```

Django debe tener en `.env` `ALLOWED_HOSTS` con `.trycloudflare.com` y `CSRF_TRUSTED_ORIGINS=https://*.trycloudflare.com` (ver el README de la raíz). Por el túnel, el enlace «Admin» sigue apuntando a `localhost:8080`, así que solo funciona en la computadora que corre Django.

## Comandos

| Comando | Qué hace |
|---|---|
| `npm run dev` | Servidor de desarrollo en `http://localhost:5173` |
| `npm run build` | Revisa que todo compile y deja el resultado en `dist/` |
| `npm run lint` | Revisa el código con ESLint |

## Trabajo futuro

- Servir `dist/` desde Django en producción, para tener un solo servidor y una sola dirección.
- Reescribir la carga de datos de algunas páginas para que no llame a `setState` dentro de `useEffect` (hoy ESLint lo marca como aviso, no como error).
