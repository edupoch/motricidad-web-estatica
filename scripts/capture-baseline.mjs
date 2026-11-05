// Capturas de la web original y registro de sus peticiones. Debe ejecutarse con WordPress aún en marcha.
// Uso: node scripts/capture-baseline.mjs [ruta...]   (sin rutas, recorre todas las páginas de mirror/)
import { chromium } from '@playwright/test';
import { existsSync, mkdirSync, readdirSync, writeFileSync } from 'node:fs';
import { join, relative } from 'node:path';

const BASE = 'https://motricidadlaboral.com';
const OUT = 'baseline';
const WIDTHS = { desktop: [1440, 900], mobile: [390, 844] };
// Faltan en la web actual: pedirlos suma errores 404 para el bloqueo de Defender.
const KNOWN_MISSING = /medical\.woff2|^https:\/\/motricidadlaboral\.com\/entorno-activo\/|\/cdn-cgi\/l\//;
const MAX_ERRORS = 5;

function pagesFromMirror(dir = 'mirror') {
  return readdirSync(dir, { withFileTypes: true }).flatMap((entry) => {
    const path = join(dir, entry.name);
    if (entry.isDirectory()) return pagesFromMirror(path);
    if (!entry.name.startsWith('index.html')) return [];
    const route = relative('mirror', dir).replaceAll('\\', '/');
    return [`/${route ? `${route}/` : ''}${entry.name.slice('index.html'.length)}`];
  });
}

async function scrollThrough(page) {
  await page.evaluate(async () => {
    for (let y = 0; y < document.body.scrollHeight; y += 400) {
      window.scrollTo(0, y);
      await new Promise((resolve) => setTimeout(resolve, 150));
    }
    window.scrollTo(0, 0);
  });
}

const routes = process.argv.slice(2).length ? process.argv.slice(2) : pagesFromMirror();
const browser = await chromium.launch();
const requests = new Set();
let errors = 0;

for (const [name, [width, height]] of Object.entries(WIDTHS)) {
  const context = await browser.newContext({ viewport: { width, height } });
  await context.route(KNOWN_MISSING, (route) => route.abort());
  context.on('response', (response) => {
    const url = response.url();
    if (!url.startsWith(BASE)) return;
    requests.add(url);
    if (response.status() >= 400) {
      errors += 1;
      console.error(`${response.status()} ${url}`);
    }
  });

  for (const route of routes) {
    const file = join(OUT, name, `${route.replace(/[/?=&]+/g, '_').replace(/^_|_$/g, '') || 'home'}.png`);
    if (existsSync(file)) continue;
    mkdirSync(join(OUT, name), { recursive: true });
    const page = await context.newPage();
    await page.goto(BASE + route, { waitUntil: 'load', timeout: 60000 });
    await scrollThrough(page);
    await page.waitForTimeout(1500);
    await page.screenshot({ path: file, fullPage: true, animations: 'disabled' });
    await page.close();
    console.log(`ok ${name} ${route}`);
    if (errors >= MAX_ERRORS) {
      console.error(`Demasiados errores (${errors}): me detengo para no provocar un bloqueo.`);
      await browser.close();
      process.exit(1);
    }
    await new Promise((resolve) => setTimeout(resolve, 1500));
  }
  await context.close();
}

await browser.close();
writeFileSync(join(OUT, 'requests.txt'), [...requests].sort().join('\n') + '\n');
console.log(`Peticiones al dominio: ${requests.size}. Errores: ${errors}.`);
