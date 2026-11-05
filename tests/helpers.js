import { readFileSync, readdirSync } from 'node:fs';
import { join, relative } from 'node:path';

// Destino real: en local, docs/ servido en el puerto 8765; en la prueba final, la URL de GitHub Pages.
export const TARGET = (process.env.TARGET || 'http://localhost:8765').replace(/\/$/, '');
const ORIGIN = 'https://motricidadlaboral.com';
const LOCAL_404 = readFileSync('docs/404.html');

export function allRoutes(dir = 'docs') {
  return readdirSync(dir, { withFileTypes: true }).flatMap((entry) => {
    const path = join(dir, entry.name);
    if (entry.isDirectory()) return allRoutes(path);
    if (entry.name !== 'index.html') return [];
    const route = relative('docs', dir);
    return [`/${route ? `${route}/` : ''}`];
  });
}

// Sirve el dominio original desde la copia estática: ninguna petición llega al WordPress.
export async function serveFromCopy(context, missing = []) {
  await context.route(/^https:\/\/motricidadlaboral\.com\//, async (route) => {
    const url = new URL(route.request().url());
    try {
      const response = await route.fetch({ url: TARGET + url.pathname + url.search, maxRedirects: 5 });
      if (response.status() >= 400) missing.push(`${response.status()} ${url.pathname}`);
      if (response.status() === 404 && !process.env.TARGET) {
        return await route.fulfill({ status: 404, contentType: 'text/html', body: LOCAL_404 });
      }
      return await route.fulfill({ response });
    } catch (error) {
      // Una navegación puede cancelar peticiones en curso.
      if (!/disposed|closed|Test ended/.test(error.message)) throw error;
    }
  });
}

export async function scrollThrough(page) {
  await page.evaluate(async () => {
    for (let y = 0; y < document.body.scrollHeight; y += 400) {
      window.scrollTo(0, y);
      await new Promise((resolve) => setTimeout(resolve, 150));
    }
    window.scrollTo(0, 0);
  });
}

export const url = (route) => ORIGIN + route;

// Mismas cookies que deja el botón «Conforme» de la web original.
export const ACCEPTED_COOKIES = [
  ['aviaCookieConsent', 'a486c3809c15b1454d8af4f1454e10f7||v1.0'],
  ['aviaPrivacyMustOptInSetting', 'true'],
  ['aviaPrivacyRefuseCookiesHideBar', 'true'],
  ['aviaPrivacyEssentialCookiesEnabled', 'true'],
].map(([name, value]) => ({ name, value, domain: 'motricidadlaboral.com', path: '/' }));
