# Guía de cambio: de WordPress a GitHub Pages

Repositorio: `edupoch/motricidad-web-estatica` (privado). La web se publica desde la carpeta `docs/` de la rama `main`.

**No apagues WordPress hasta que la web lleve unos días funcionando:** es la marcha atrás.

## 1. Activar GitHub Pages

GitHub solo permite Pages en repositorios privados con un plan de pago (Pro, Team o Enterprise). Con el plan gratuito, la alternativa es hacer público el repositorio.

Aunque el repositorio sea privado, **la web publicada es pública**. Se ve el contenido de `docs/`, no el resto del repositorio.

En *Settings → Pages*: *Deploy from a branch*, rama `main`, carpeta `/docs`.

## 2. Probar antes de cambiar el dominio

La URL de prueba es `https://edupoch.github.io/motricidad-web-estatica/`. Abierta directamente **no sirve como prueba**: las URLs del HTML son absolutas y cargaría los estilos del WordPress. Para comprobarla:

```bash
TARGET=https://edupoch.github.io/motricidad-web-estatica npx playwright test
```

El mapa de `/contacto/` puede fallar en esa URL si la clave de Google Maps está restringida por dominio.

## 3. Preparar el dominio

1. En Cloudflare, **anota o exporta todos los registros DNS actuales**, incluida la IP real del WordPress: es lo que necesitas para volver atrás.
2. Comprueba en Cloudflare el modo SSL/TLS. Si está en *Flexible*, cámbialo a *Full (strict)* antes del paso 5: *Flexible* con HTTPS obligatorio en GitHub provoca un bucle de redirecciones.
3. Recomendado: verifica el dominio en *GitHub → Settings (de tu cuenta) → Pages*, para que nadie más pueda usarlo en GitHub Pages.

## 4. Añadir el dominio

En *Settings → Pages → Custom domain* escribe `motricidadlaboral.com` y guarda. GitHub crea el archivo `docs/CNAME` en un commit; luego haz `git pull`.

`scripts/build.py` borra `docs/` antes de generarla. Si vuelves a ejecutarlo, vuelve a crear ese archivo con `echo motricidadlaboral.com > docs/CNAME`.

## 5. Cambiar el DNS en Cloudflare

Cambia **solo** estos registros, con el proxy desactivado (*DNS only*, nube gris) para que GitHub pueda emitir el certificado:

| Tipo | Nombre | Valor |
|---|---|---|
| A | `@` | `185.199.108.153` |
| A | `@` | `185.199.109.153` |
| A | `@` | `185.199.110.153` |
| A | `@` | `185.199.111.153` |
| AAAA | `@` | `2606:50c0:8000::153` |
| AAAA | `@` | `2606:50c0:8001::153` |
| AAAA | `@` | `2606:50c0:8002::153` |
| AAAA | `@` | `2606:50c0:8003::153` |
| CNAME | `www` | `edupoch.github.io` |

**No toques:**

- `app.motricidadlaboral.com`: es la aplicación de `ACCESO ALUMNOS` y no forma parte de esta web.
- Los registros `MX` (`privateemail.com`) ni los `TXT` de correo: si cambian, deja de funcionar `info@motricidadlaboral.com`.

## 6. Activar HTTPS

1. Espera a que *Settings → Pages* indique que el DNS es correcto y que el certificado está emitido. Puede tardar desde unos minutos hasta 24 horas.
2. Marca *Enforce HTTPS*.
3. Opcional: vuelve a activar el proxy de Cloudflare (nube naranja) con SSL en *Full (strict)*, y purga su caché.

## 7. Comprobar

- La home y `/contacto/` cargan en `https://motricidadlaboral.com/`, y `www` redirige al dominio sin `www`.
- Tras pulsar «Conforme», el mapa de `/contacto/` carga. Si falla, revisa las restricciones de la clave de Google Maps.
- `ACCESO ALUMNOS` sigue funcionando y llega correo a `info@motricidadlaboral.com`.
- Una URL inexistente muestra la página 404 de la web.

## Marcha atrás

1. En Cloudflare, restaura los registros `@` y `www` que anotaste en el paso 3, con su estado de proxy original, y purga la caché.
2. En *Settings → Pages*, quita el dominio propio.

WordPress vuelve a responder en cuanto se propaga el DNS, siempre que siga encendido.
