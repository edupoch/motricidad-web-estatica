import { expect, test } from '@playwright/test';
import { ACCEPTED_COOKIES, allRoutes, scrollThrough, serveFromCopy, url } from './helpers.js';

const ROUTES = allRoutes();
const REMOVED = ['/portfolio-item/crossfit/', '/portfolio_entries/classes/', '/wp-json/', '/wp-admin/'];
// Faltan ya en la web original y se conservan así.
const KNOWN_MISSING = /medical\.woff2|^404 \/entorno-activo\/$/;

test('hay 56 páginas', () => expect(ROUTES.length).toBe(56));

for (const route of REMOVED) {
  test(`responde 404: ${route}`, async ({ page, context }) => {
    await serveFromCopy(context);
    expect((await page.goto(url(route))).status()).toBe(404);
  });
}

for (const [state, cookies] of [['sin aceptar', []], ['con cookies aceptadas', ACCEPTED_COOKIES]])
for (const route of ROUTES) {
  test(`carga sin errores (${state}): ${route}`, async ({ page, context }) => {
    await context.addCookies(cookies);
    const missing = [];
    const jsErrors = [];
    const blocked = [];
    await serveFromCopy(context, missing);
    page.on('pageerror', (error) => jsErrors.push(error.message));
    page.on('request', (request) => {
      if (/recaptcha|googletagmanager|google-analytics|admin-ajax|wp-json|xmlrpc|cdn-cgi/.test(request.url())) {
        blocked.push(request.url());
      }
    });
    expect((await page.goto(url(route))).status()).toBe(200);
    await scrollThrough(page);
    expect(missing.filter((m) => !KNOWN_MISSING.test(m))).toEqual([]);
    expect(jsErrors).toEqual([]);
    expect(blocked).toEqual([]);
  });
}

test('los enlaces internos existen', async ({ context, request }) => {
  const seen = new Set();
  const page = await context.newPage();
  await serveFromCopy(context);
  const broken = [];
  for (const route of ROUTES) {
    await page.goto(url(route), { waitUntil: 'domcontentloaded' });
    const hrefs = await page.$$eval('a[href^="https://motricidadlaboral.com/"], a[href^="/"]', (as) => as.map((a) => a.href));
    for (const href of hrefs) {
      const path = new URL(href).pathname;
      if (seen.has(path) || path === '/entorno-activo/') continue;
      seen.add(path);
      const { TARGET } = await import('./helpers.js');
      if (!(await request.get(TARGET + path)).ok()) broken.push(`${route} -> ${path}`);
    }
  }
  expect(broken).toEqual([]);
});

test.describe('interacciones', () => {
  test.beforeEach(({ context }) => serveFromCopy(context));

  test('contacto: mailto y sin formulario', async ({ page }) => {
    await page.goto(url('/contacto/'));
    await expect(page.locator('form')).toHaveCount(0);
    await expect(page.locator('.flex_column a[href="mailto:info@motricidadlaboral.com"]')).toBeVisible();
  });

  test('cookies: Maps solo se carga tras aceptar', async ({ page }) => {
    const maps = [];
    page.on('request', (r) => { if (r.url().includes('maps.googleapis.com')) maps.push(r.url()); });
    await page.goto(url('/contacto/'));
    await page.waitForTimeout(1500);
    expect(maps).toEqual([]);
    await page.locator('.avia-cookie-consent a', { hasText: 'Conforme' }).first().click();
    await page.waitForTimeout(3000);
    await page.reload();
    await expect.poll(() => maps.length, { timeout: 15000 }).toBeGreaterThan(0);
  });

  test('cookies: rechazar no carga Maps, igual que la original', async ({ page }) => {
    const maps = [];
    page.on('request', (r) => { if (r.url().includes('maps.googleapis.com')) maps.push(r.url()); });
    await page.goto(url('/contacto/'));
    await page.locator('.avia-cookie-consent a', { hasText: 'Rechazar' }).first().click();
    await page.waitForTimeout(1000);
    await page.reload();
    await page.waitForTimeout(2000);
    expect(maps).toEqual([]);
  });

  test('cookies: «Configurar» abre el panel', async ({ page }) => {
    await page.goto(url('/'));
    await page.locator('.avia-cookie-consent a', { hasText: 'Configurar' }).first().click();
    await expect(page.locator('.avia-cookie-consent-modal-buttons-wrap').first()).toBeVisible();
  });

  test('menú móvil se abre', async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto(url('/'));
    await page.locator('.av-hamburger').first().click();
    await expect(page.locator('#av-burger-menu-ul, .av-burger-overlay').first()).toBeVisible();
  });

  test('paginación de noticias', async ({ page }) => {
    await page.goto(url('/noticias/'));
    await page.locator('nav.pagination a', { hasText: '2' }).first().click();
    await expect(page).toHaveURL(/\/noticias\/page\/2\/$/);
    await expect(page.locator('.pagination-meta').first()).toHaveText('Página 2 de 4');
  });
});
