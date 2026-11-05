# Spec: Versión estática de motricidadlaboral.com

Estado: **aprobada, pendiente de publicación** · Fecha: 2026-11-05

## Objetivo

Sustituir el WordPress (tema Enfold) de https://motricidadlaboral.com/, que no se va a actualizar más, por una copia estática igual en diseño y contenido, con las mismas URLs y el mismo dominio. Los visitantes no deben notar el cambio y WordPress debe poder apagarse sin que nada falle.

### Principio: no se remaqueta nada

La web publicada es el mismo HTML que genera WordPress y el mismo CSS, sin tocar:

- **CSS y fuentes:** copia idéntica byte a byte, salvo las URLs del dominio en 7 archivos CSS (cambio 8). No se añade, se reescribe ni se minifica ningún CSS.
- **HTML:** se conserva tal cual. Solo se aplican las ediciones de «Únicos cambios».
- **JS:** copia idéntica, salvo que se retiren los scripts de reCAPTCHA y Analytics, que se quitan del HTML.
- **Diseño:** no hay ningún cambio. La única excepción acordada es el formulario de `/contacto/`.

### Alcance

| Contenido | Cantidad | Origen |
|---|---|---|
| Páginas | 10 | `page-sitemap.xml` |
| Entradas | 25 + la home, que también aparece en este sitemap | `post-sitemap.xml` |
| Categorías, con su paginación (`/category/noticias/page/2/`, `/page/3/`) | 4 | `category-sitemap.xml` |
| Etiquetas, con su paginación si la tienen | 9 | `post_tag-sitemap.xml` |
| Imágenes, documentos, CSS, JS y fuentes usados por lo anterior | según rastreo | mismas rutas `/wp-content/...` |
| Páginas de autor, con su paginación (`/author/commotricidad/`) | 3 | enlazadas desde las entradas |
| Página 404 con el diseño de la web | 1 | la 404 actual |

### Únicos cambios respecto a la original

1. `/contacto/`: el formulario se sustituye por un enlace a `mailto:info@motricidadlaboral.com`, usando solo clases que ya existen en el CSS del tema. Desaparece reCAPTCHA.
2. Se eliminan las 7 URLs de demo (`/portfolio-item/*` y `/portfolio_entries/classes/`), también del sitemap.
3. Se quita Google Analytics (`UA-53062585-29`).
4. El mapa de `/contacto/` se conserva con su clave de API. Solo pasa a `iframe` sin clave si esa clave falla en el nuevo alojamiento.
5. `/noticias/`: la paginación con `?avia-element-paging=N` no funciona en GitHub Pages. Sus páginas pasan a `/noticias/page/N/`, con el HTML original y cambiando solo esos enlaces. Un enlace antiguo con el parámetro mostrará la primera página.
6. Los correos ofuscados por Cloudflare (`data-cfemail`) pasan a texto normal y se retira su script `email-decode`. No cambia lo que ve el visitante.
7. Se retira el script contra bots que Cloudflare añade al HTML (`__CF$cv$params`). Es un añadido de Cloudflare, no de WordPress, y no se ve.
8. Las URLs absolutas de recursos y enlaces internos pasan a rutas relativas, en HTML y CSS, para que todo se pida al dominio donde se abre la web. Siguen absolutas la canónica, los metadatos, el JSON-LD, los `<link>` técnicos, el sitemap, el feed y el texto. La página 404 usa rutas desde la raíz, porque se sirve desde cualquier ruta: en `github.io`, que está en una subcarpeta, se verá sin estilos.

reCAPTCHA se desactiva quitando del HTML solo la variable `AviaReCAPTCHA_front`: el JS del tema no se toca y, sin ella, no lo carga.

Los fallos que ya tiene la web actual (enlace a `/entorno-activo/`, fuente `medical.woff2` ausente) se dejan como están.

Se mantienen sin cambios Google Maps, YouTube, el enlace a Vimeo, el vídeo MP4 y el banner de cookies, que sigue bloqueando los servicios externos hasta que se aceptan.

Cloudflare añade al HTML de la web actual una etiqueta de Google (`/fc3l/`, `G-Y5DLKVMXY6`) que no está en WordPress. La copia no la lleva, pero Cloudflare puede seguir añadiéndola si su proxy queda activado (ver `GUIA-CAMBIO.md`).

### Fuera de alcance

Rediseño, mejoras de contenido o SEO, panel de edición, analítica nueva, formulario de comentarios, cambio de DNS y publicación final en producción.

### Supuestos (corrígelos si no encajan)

1. **Comentarios:** la entrada que he revisado no tiene formulario de comentarios. Si el rastreo encuentra alguno en otra entrada, te aviso antes de tocarlo.
2. **Archivos por fecha** (`/2019/`, etc.): no están en el sitemap ni he visto enlaces a ellos en las páginas revisadas, así que no se copian salvo que el rastreo encuentre alguno enlazado. Si no, responderán 404.
3. **Rutas técnicas de WordPress** (`/wp-json/`, `/wp-admin/`, `/xmlrpc.php`): las rutas desaparecen. Las etiquetas `<link>` que apuntan a ellas se quedan, porque no tienen efecto visible. Solo se retira una referencia si provoca una petición desde el navegador.
4. **Parámetros de versión** (`estilo.css?ver=8.1`): el HTML no cambia. El archivo se guarda sin el parámetro, porque GitHub Pages lo ignora al servirlo.
5. **Feed RSS** (`/feed/`): se conserva como XML estático si GitHub Pages lo sirve correctamente en esa URL. Si no, se quitan sus enlaces y se avisa.
6. **Sitemap:** un único `/sitemap.xml` regenerado reemplaza a los de SmartCrawl. Los sub-sitemaps responderán 404.
7. **Etiquetas `<head>`:** títulos, descripciones, canónicas y metadatos sociales se conservan tal cual.

## Stack

- **Captura:** rastreador propio en Python y un rastreo con navegador para detectar recursos que solo se piden al ejecutar JS.
- **Transformación:** Python 3 con biblioteca estándar.
- **Verificación:** Node con Playwright como dependencia de desarrollo (no llega a la web publicada).
- **Publicación:** repositorio público en GitHub (`edupoch/motricidad-web-estatica`), con GitHub Pages desde la carpeta `docs/`, dominio propio y DNS en Cloudflare.

El resultado no usa generador de sitios: es el HTML de la web original con ediciones puntuales, para no introducir diferencias visuales.

El archivo `CNAME` se añade en el momento del cambio, no antes, para que GitHub Pages no intente usar el dominio mientras sigue apuntando al WordPress.

## Comandos

```bash
python3 -I scripts/mirror.py            # descarga la web original a mirror/
python3 -I scripts/build.py            # genera docs/ a partir de mirror/
python3 -m http.server 8765 -d docs    # sirve el resultado en http://localhost:8765/
npx playwright test                    # enlaces, recursos, dependencias y comparación visual
```

## Estructura

```
SPEC.md
scripts/mirror.py   → captura de la web original
scripts/build.py    → transformaciones (los cambios de esta spec y nada más)
mirror/             → copia sin tocar del WordPress, es el respaldo tras apagarlo
baseline/           → capturas de pantalla de la web original
tests/              → pruebas de Playwright
GUIA-CAMBIO.md      → pasos para cambiar el dominio y marcha atrás
docs/               → web publicada (incluye .nojekyll y 404.html; CNAME al hacer el cambio)
```

`mirror/` y `baseline/` deben generarse **antes de apagar WordPress**, porque después no se pueden volver a crear.

El repositorio es público: se ve todo su contenido, también `mirror/` y `baseline/`. La clave de Google Maps ya es visible hoy en el HTML, y conviene que tenga restricción por dominio.

## Estilo de código

Ediciones acotadas sobre el texto original, sin reformatear el HTML. Cada transformación es una función con nombre que falla si no encuentra lo que espera, para que un cambio no se pierda en silencio:

```python
def remove_analytics(html: str) -> str:
    result, count = ANALYTICS_RE.subn("", html)
    if count == 0:
        raise ValueError("No se ha encontrado el bloque de Analytics")
    return result
```

## Estrategia de pruebas

Pruebas con Playwright contra `docs/` servido en local, y una pasada final contra la URL de prueba de GitHub Pages. La mayoría intercepta el dominio original para probar en su URL definitiva; otra abre cada página sin interceptar nada:

- **Copia exacta (la comprobación principal):** cada CSS, fuente, imagen y JS de `docs/` tiene el mismo hash que en `mirror/`, salvo las URLs del cambio 8. La diferencia de cada HTML con su original contiene solo las ediciones de «Únicos cambios».
- **Paridad de URLs:** cada URL del alcance responde 200, y las eliminadas responden 404.
- **Comparación visual:** cada página a 1440 px y 390 px, a página completa y con animaciones congeladas, frente a `baseline/`, sin aceptar cookies y con ellas aceptadas (`baseline/accepted/`). Las capturas con cookies se hicieron bloqueando Analytics en la original.
- **Enlaces y recursos:** ningún enlace interno ni recurso da error, y no hay errores nuevos en consola.
- **Independencia de WordPress:** ninguna petición llega al servidor original. El navegador no hace peticiones a `admin-ajax.php`, `wp-json`, `xmlrpc` ni `/cdn-cgi/`, y tampoco carga reCAPTCHA ni Analytics. Como el JS del tema no se toca, puede seguir conteniendo código inactivo de esos servicios, pero `UA-53062585-29` desaparece del HTML.
- **Interacción:** menú móvil, banner de cookies (aceptar, rechazar y carga de Maps y YouTube solo tras aceptar), lightbox de imágenes, reproducción del MP4, enlace `mailto:`. La web no tiene galerías ni vídeos de Vimeo incrustados: Vimeo es un enlace del menú.

## Límites

- **Siempre:** conservar las URLs públicas, los textos y el marcado originales; generar `docs/` solo mediante `scripts/build.py`; pasar las pruebas antes de dar una tarea por terminada.
- **Preguntar antes:** cualquier cambio visible que no esté en la lista de esta spec, cualquier edición de HTML no prevista, añadir dependencias a la web publicada, crear el repositorio o hacer commits y publicar en GitHub.
- **Nunca:** editar o añadir CSS, remaquetar, modificar los textos legales, tocar el DNS, ni cambiar o apagar el WordPress actual.

## Criterios de éxito

1. Las 10 páginas, las entradas, las categorías y las etiquetas responden 200 en su URL actual, y las 7 de demo responden 404.
2. El CSS (salvo sus URLs), las fuentes, las imágenes y el JS de `docs/` son idénticos a los originales, y cada HTML difiere solo en las ediciones de «Únicos cambios».
3. La comparación visual no muestra diferencias de diseño en ninguna página ni anchura. Cualquier página con más del 0,1 % de píxeles distintos se revisa a mano, y `/contacto/` se revisa siempre.
4. No hay enlaces ni recursos rotos, y ninguna petición llega al WordPress.
5. Todas las interacciones de la estrategia de pruebas funcionan en la URL de prueba de GitHub Pages.
6. Hay una guía breve para que hagas el cambio: añadir `CNAME`, registros DNS, modo SSL de Cloudflare y marcha atrás.

## Avisos sobre los textos legales (se copian sin cambios)

Quedarán desfasadas estas menciones. Decidir qué hacer con ellas queda en tus manos:

- **`/politica-de-privacidad/`:** habla de «formularios de la web» y tiene un apartado «Formulario contacto», pero la web ya no tendrá formulario.
- **`/politica-de-cookies/`:** menciona «Google Analytics y similares» como proveedor de cookies analíticas, pero la web ya no usará Analytics.
