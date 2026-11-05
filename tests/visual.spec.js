import { expect, test } from '@playwright/test';
import { ACCEPTED_COOKIES, allRoutes, scrollThrough, serveFromCopy, url } from './helpers.js';

const WIDTHS = { desktop: [1440, 900], mobile: [390, 844] };
// /contacto/ cambia por el formulario y se revisa a mano.
const ROUTES = allRoutes().filter((route) => route !== '/contacto/');

// La altura de algunas páginas varía 1 px entre cargas, también en la versión sin rutas relativas.
test.describe.configure({ retries: 2 });

function baselineName(route) {
  const paging = route.match(/^\/noticias\/page\/(\d+)\/$/);
  if (paging) return `noticias_avia-element-paging_${paging[1]}`;
  return route.replace(/[/?=&]+/g, '_').replace(/^_|_$/g, '') || 'home';
}

for (const accepted of [false, true]) {
  const folder = accepted ? ['accepted'] : [];
  const label = accepted ? 'con cookies ' : '';
  for (const [name, [width, height]] of Object.entries(WIDTHS)) {
    for (const route of ROUTES) {
      test(`${label}${name} ${route}`, async ({ page, context }) => {
        await page.setViewportSize({ width, height });
        await serveFromCopy(context);
        if (accepted) await context.addCookies(ACCEPTED_COOKIES);
        await page.goto(url(route), { waitUntil: 'load' });
        await scrollThrough(page);
        await page.waitForTimeout(1500);
        // Se repite la captura para dar tiempo a las animaciones cíclicas, como el rotador de /concepto/.
        await expect(async () => {
          const shot = await page.screenshot({ fullPage: true, animations: 'disabled' });
          expect(shot).toMatchSnapshot([...folder, name, `${baselineName(route)}.png`], { maxDiffPixelRatio: 0.001 });
        }).toPass({ timeout: 20000 });
      });
    }
  }
}
