import { expect, test } from '@playwright/test';
import fs from 'node:fs';
import path from 'node:path';

const fixturePath = path.resolve(
  process.cwd(),
  '../backend/tests/fixtures/tracelab/sample.jsonl',
);
const mappingPath = path.resolve(
  process.cwd(),
  '../docs/data/mappings/tracelab.json',
);

test('imports a TraceLab file and displays dashboard indicators', async ({ page }) => {
  const mappingResponse = await page.request.get('/api/v1/mappings/tracelab-jsonl');
  if (mappingResponse.status() === 404) {
    const createResponse = await page.request.post('/api/v1/mappings', {
      data: {
        name: 'tracelab-jsonl',
        source_format: 'jsonl',
        definition: JSON.parse(fs.readFileSync(mappingPath, 'utf8')),
      },
    });
    expect(createResponse.ok()).toBeTruthy();
  } else {
    expect(mappingResponse.ok()).toBeTruthy();
  }

  await page.goto('/imports');

  await page.locator('#file-upload').setInputFiles(fixturePath);
  await expect(page.getByText('sample.jsonl')).toBeVisible();

  await page.getByRole('button', { name: "Lancer l'import" }).click();
  await expect(page.getByRole('heading', { name: "Bilan de l'importation" })).toBeVisible();
  await expect(page.getByText('completed')).toBeVisible();

  const indicatorsResponse = page.waitForResponse(
    (response) =>
      response.url().includes('/api/v1/metrics/indicators') && response.ok(),
  );
  await page.getByRole('link', { name: 'Dashboard' }).click();
  const indicators = await (await indicatorsResponse).json();
  await expect(page.getByRole('heading', { name: 'Tableau de bord' })).toBeVisible();

  const sessionsCard = page.getByText('Sessions totales', { exact: true }).locator('../..');
  await expect(sessionsCard).toBeVisible();
  expect(indicators.session_count).toBeGreaterThan(0);
});
