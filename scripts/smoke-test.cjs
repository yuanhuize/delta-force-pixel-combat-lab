const { chromium } = require('playwright');
const fs = require('fs');
const http = require('http');
const path = require('path');

const root = path.resolve(__dirname, '../build/web-desktop');
const artifactDir = path.resolve(__dirname, '../artifacts');
fs.mkdirSync(artifactDir, { recursive: true });

const mime = {
  '.html': 'text/html; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8',
  '.json': 'application/json',
  '.css': 'text/css; charset=utf-8',
  '.wasm': 'application/wasm',
  '.bin': 'application/octet-stream',
  '.ico': 'image/x-icon',
};

const server = http.createServer((request, response) => {
  const requestPath = decodeURIComponent((request.url || '/').split('?')[0]);
  const relative = requestPath === '/' ? 'index.html' : requestPath.replace(/^\/+/, '');
  const target = path.resolve(root, relative);
  if (!target.startsWith(root) || !fs.existsSync(target) || fs.statSync(target).isDirectory()) {
    response.writeHead(404);
    response.end('Not found');
    return;
  }
  response.writeHead(200, { 'Content-Type': mime[path.extname(target)] || 'application/octet-stream' });
  fs.createReadStream(target).pipe(response);
});

(async () => {
  await new Promise(resolve => server.listen(8468, '127.0.0.1', resolve));
  const browser = await chromium.launch({
    headless: true,
    executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
  });
  const page = await browser.newPage({ viewport: { width: 1280, height: 720 }, deviceScaleFactor: 1 });
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  page.on('console', message => {
    if (message.type() === 'error') errors.push(message.text());
  });

  await page.goto('http://127.0.0.1:8468', { waitUntil: 'networkidle' });
  await page.waitForSelector('canvas');
  await page.waitForTimeout(1400);
  await page.screenshot({ path: path.join(artifactDir, '01_front_direction.png') });

  await page.mouse.move(640, 105);
  await page.waitForTimeout(250);
  await page.screenshot({ path: path.join(artifactDir, '02_back_direction.png') });

  await page.mouse.click(640, 105);
  await page.waitForTimeout(20);
  await page.screenshot({ path: path.join(artifactDir, '03_back_fire_peak.png') });

  const canvas = await page.locator('canvas').boundingBox();
  console.log(JSON.stringify({ canvas, errors }));
  await browser.close();
  await new Promise(resolve => server.close(resolve));
  if (errors.length > 0) process.exitCode = 1;
})().catch(error => {
  console.error(error);
  server.close();
  process.exitCode = 1;
});
