# Tareas (ver SPEC.md)

- [x] 1. Captura: `scripts/mirror.py` descarga la web a `mirror/`.
  - Verificar: están todas las URLs del alcance y ninguna de demo; se listan los recursos que falten.
- [x] 2. Capturas de referencia de la web original en `baseline/` (1440 y 390 px).
  - Verificar: una captura por URL y anchura.
- [x] 3. Recursos que solo pide el JS: rastreo con navegador y añadido a `mirror/`.
  - Verificar: ninguna petición a recursos ausentes en local.
- [x] 4. `scripts/build.py`: copia a `docs/` con parámetros de versión normalizados, 404, sitemap, `.nojekyll`.
  - Verificar: los hashes de CSS, JS, fuentes e imágenes coinciden con `mirror/`.
- [x] 5. Ediciones de HTML: Analytics, reCAPTCHA y `mailto:` en `/contacto/`.
  - Verificar: la diferencia de cada HTML contiene solo estas ediciones.
- [x] 6. Pruebas de Playwright: URLs, enlaces, independencia de WordPress, visual, interacciones.
  - Verificar: `npx playwright test` en verde y `/contacto/` revisado a mano.
- [x] 7. Revisión de `mirror/` antes de publicar antes de publicar el repositorio.
- [ ] 8. Publicación de prueba en GitHub Pages y repetición de las pruebas.
- [x] 9. Guía de cambio en `GUIA-CAMBIO.md`: `CNAME`, DNS, SSL de Cloudflare y marcha atrás.
