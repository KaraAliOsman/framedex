import { chromium } from "@playwright/test";
import { readFile, writeFile, mkdir } from "node:fs/promises";
import { fileURLToPath } from "node:url";

const publicDir = fileURLToPath(new URL("../public/", import.meta.url));
const browser = await chromium.launch();
try {
  for (const theme of ["light", "dark"]) {
    const optical = await readFile(`${publicDir}favicon-${theme}.svg`, "utf8");
    const standard = optical
      .replace("M3 3V21H21V3Z", "M2.5 2.5V21.5H21.5V2.5Z")
      .replace("M6.875 3H9.125V21H6.875Z", "M7 2.5H9V21.5H7Z");
    for (const size of [16, 32, 180, 192, 512]) {
      const page = await browser.newPage({
        viewport: { width: size, height: size },
        deviceScaleFactor: 1,
      });
      await page.setContent(
        `<style>html,body{margin:0}svg{display:block;width:100%;height:100%}</style>${size < 24 ? optical : standard}`,
      );
      const png = await page.screenshot();
      await writeFile(`${publicDir}icon-${theme}-${size}.png`, png);
      if (theme === "light") await writeFile(`${publicDir}icon-${size}.png`, png);
      await page.close();
    }
  }
  const lockup = await readFile(new URL("../src/brand/doc-lockup.svg", import.meta.url), "utf8");
  const page = await browser.newPage({
    viewport: { width: 528, height: 144 },
    deviceScaleFactor: 1,
  });
  await page.setContent(
    `<style>html,body{margin:0;color:#161C1F;background:#FCFDFC}svg{display:block;width:100%;height:100%}</style>${lockup}`,
  );
  const png = await page.screenshot();
  await writeFile(`${publicDir}mail-lockup.png`, png);
  const assets = new URL("../../backend/notifications/assets/", import.meta.url);
  await mkdir(assets, { recursive: true });
  await writeFile(new URL("mail-lockup.png", assets), png);
  await page.close();
} finally {
  await browser.close();
}
