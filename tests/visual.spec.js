import { expect, test } from '@playwright/test';
import { allRoutes, scrollThrough, serveFromCopy, url } from './helpers.js';

const WIDTHS = { desktop: [1440, 900], mobile: [390, 844] };
// /contacto/ cambia por el formulario y se revisa a mano.
const ROUTES = allRoutes().filter((route) => route !== '/contacto/');

function baselineName(route) {
  const paging = route.match(/^\/noticias\/page\/(\d+)\/$/);
  if (paging) return `noticias_avia-element-paging_${paging[1]}`;
  return route.replace(/[/?=&]+/g, '_').replace(/^_|_$/g, '') || 'home';
}

for (const [name, [width, height]] of Object.entries(WIDTHS)) {
  for (const route of ROUTES) {
    test(`${name} ${route}`, async ({ page, context }) => {
      await page.setViewportSize({ width, height });
      await serveFromCopy(context);
      await page.goto(url(route), { waitUntil: 'load' });
      await scrollThrough(page);
      await page.waitForTimeout(1500);
      const shot = await page.screenshot({ fullPage: true, animations: 'disabled' });
      expect(shot).toMatchSnapshot([name, `${baselineName(route)}.png`], { maxDiffPixelRatio: 0.001 });
    });
  }
}
