const puppeteer = require('puppeteer');
const path = require('path');
const fs = require('fs');

async function screenshotTanuki(version = 'initial') {
  const browser = await puppeteer.launch({ headless: true });
  const page = await browser.newPage();

  // Set viewport to see the right sidebar
  await page.setViewport({ width: 1400, height: 900 });

  // Navigate to the app
  await page.goto('http://localhost:5173', { waitUntil: 'networkidle2', timeout: 30000 });

  // Wait for the tanuki to render
  await page.waitForSelector('.tanuki-container', { timeout: 10000 });

  // Give animations a moment to settle
  await new Promise(r => setTimeout(r, 500));

  // Ensure screenshots directory exists
  const screenshotsDir = path.join(__dirname, 'tanuki-screenshots');
  if (!fs.existsSync(screenshotsDir)) {
    fs.mkdirSync(screenshotsDir);
  }

  // Take full page screenshot
  const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
  const fullPath = path.join(screenshotsDir, `tanuki-${version}-full-${timestamp}.png`);
  await page.screenshot({ path: fullPath, fullPage: false });
  console.log(`Full screenshot saved: ${fullPath}`);

  // Take focused screenshot of just the tanuki section
  const tanukiElement = await page.$('.tanuki-container');
  if (tanukiElement) {
    const tanukiPath = path.join(screenshotsDir, `tanuki-${version}-close-${timestamp}.png`);
    await tanukiElement.screenshot({ path: tanukiPath });
    console.log(`Tanuki close-up saved: ${tanukiPath}`);
  }

  // Also capture the right sidebar
  const rightSidebar = await page.$('.right-sidebar.expanded');
  if (rightSidebar) {
    const sidebarPath = path.join(screenshotsDir, `tanuki-${version}-sidebar-${timestamp}.png`);
    await rightSidebar.screenshot({ path: sidebarPath });
    console.log(`Sidebar screenshot saved: ${sidebarPath}`);
  }

  await browser.close();
  console.log('Done!');
}

// Get version from command line args
const version = process.argv[2] || 'initial';
screenshotTanuki(version).catch(console.error);
