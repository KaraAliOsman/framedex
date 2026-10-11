import { createHash } from "node:crypto";
import type { Plugin } from "vite";

/** Cache app code, never a private response, login flow or document URL. */
export function fieldWorker(): Plugin {
  return {
    name: "field-offline-assets",
    apply: "build",
    generateBundle(_options, bundle) {
      const assets = Object.keys(bundle)
        .filter((name) => /\.(js|css)$/.test(name))
        .map((name) => `/${name}`);
      const fonts = ["sans", "mono"].flatMap((face) =>
        [400, 500, 600].map((weight) => `/fonts/ibm-plex-${face}-latin-${weight}-normal.woff2`),
      );
      const allowed = [...assets, ...fonts];
      const version = createHash("sha256").update(allowed.join("|")).digest("hex").slice(0, 12);
      const source = `const CACHE='dekopen-field-${version}';
const ASSETS=${JSON.stringify(allowed)};
self.addEventListener('install',event=>event.waitUntil((async()=>{const cache=await caches.open(CACHE);for(const url of ['/field',...ASSETS]){const response=await fetch(url,{credentials:'omit',cache:'reload'});if(!response.ok)throw new Error('asset unavailable');await cache.put(url,response);}await self.skipWaiting();})()));
self.addEventListener('activate',event=>event.waitUntil((async()=>{for(const key of await caches.keys()){if(key.startsWith('dekopen-field-')&&key!==CACHE)await caches.delete(key);}await self.clients.claim();})()));
self.addEventListener('fetch',event=>{const url=new URL(event.request.url);if(event.request.method!=='GET'||url.origin!==self.location.origin)return;
if(event.request.mode==='navigate'&&url.pathname==='/field'){event.respondWith(fetch(event.request).catch(async()=>{const cache=await caches.open(CACHE);return await cache.match('/field')||Response.error();}));return;}
if(ASSETS.includes(url.pathname)&&!url.search){event.respondWith((async()=>{const cache=await caches.open(CACHE);return await cache.match(url.pathname)||fetch(event.request);})());}});
`;
      this.emitFile({ type: "asset", fileName: "field-worker.js", source });
    },
  };
}
