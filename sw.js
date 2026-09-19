const C="kpc-mental-v210";
const CORE=["./","./index.html","./manifest.webmanifest","./logo.svg"];
self.addEventListener("install",e=>{self.skipWaiting();e.waitUntil(caches.open(C).then(c=>c.addAll(CORE)))});
self.addEventListener("activate",e=>{e.waitUntil(caches.keys().then(ks=>Promise.all(ks.filter(k=>k!==C).map(k=>caches.delete(k)))).then(()=>self.clients.claim()))});
self.addEventListener("fetch",e=>{
  if(e.request.method!=="GET") return;
  e.respondWith(fetch(e.request).then(r=>{
    const x=r.clone();
    caches.open(C).then(c=>c.put(e.request,x));
    return r;
  }).catch(()=>caches.match(e.request).then(r=>r||caches.match("./index.html"))));
});