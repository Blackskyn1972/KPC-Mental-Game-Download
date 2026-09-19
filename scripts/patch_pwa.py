from pathlib import Path
p=Path("app/index.html")
s=p.read_text(encoding="utf-8")

meta='''<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="KPC Mental Game et Compétition">
<link rel="manifest" href="manifest.webmanifest">
<link rel="apple-touch-icon" href="logo.svg">
<style id="kpc-ios-pwa">
html,body{min-height:100%;overscroll-behavior-y:none}
body{padding-top:env(safe-area-inset-top)}
.app{padding-bottom:calc(104px + env(safe-area-inset-bottom))!important}
.bottom-nav{padding-bottom:calc(7px + env(safe-area-inset-bottom))!important}
#kpcIosInstall{position:fixed;left:12px;right:12px;bottom:calc(14px + env(safe-area-inset-bottom));z-index:2147483000;background:#0a2139;color:#f7f3e8;border:1px solid #e5b84d;border-radius:16px;padding:14px 15px;box-shadow:0 12px 32px #0009;font-family:system-ui,-apple-system,Segoe UI,sans-serif}
#kpcIosInstall b{color:#e5b84d;display:block;margin-bottom:5px}
#kpcIosInstall p{margin:0 0 10px;line-height:1.4;font-size:14px}
#kpcIosInstall button{width:100%;border:0;border-radius:10px;padding:10px;background:#e5b84d;color:#102038;font-weight:800}
</style>'''
if 'id="kpc-ios-pwa"' not in s:
    s=s.replace("</head>",meta+"</head>",1)

reg=r'''<script id="kpc-pwa-runtime">
(function(){
  if("serviceWorker" in navigator){
    window.addEventListener("load",function(){
      navigator.serviceWorker.register("./sw.js").then(function(r){r.update().catch(function(){});}).catch(function(){});
    });
  }
  function isiOS(){
    return /iPad|iPhone|iPod/.test(navigator.userAgent) ||
      (navigator.platform==="MacIntel" && navigator.maxTouchPoints>1);
  }
  function standalone(){
    return window.navigator.standalone===true ||
      window.matchMedia("(display-mode: standalone)").matches;
  }
  function showInstallHelp(){
    if(!isiOS() || standalone() || document.getElementById("kpcIosInstall")) return;
    var el=document.createElement("div");
    el.id="kpcIosInstall";
    el.innerHTML="<b>📱 Installer KPC Mental Game et Compétition sur iPhone</b><p>Dans Safari, touche <strong>Partager</strong> (carré avec la flèche), puis <strong>Ajouter à l’écran d’accueil</strong> et enfin <strong>Ajouter</strong>.</p><button type='button'>J’ai compris</button>";
    el.querySelector("button").onclick=function(){el.remove();sessionStorage.setItem("kpc_ios_install_seen","1");};
    document.body.appendChild(el);
  }
  window.addEventListener("load",function(){
    if(sessionStorage.getItem("kpc_ios_install_seen")!=="1") setTimeout(showInstallHelp,700);
  });
})();
</script>'''
if 'id="kpc-pwa-runtime"' not in s:
    s=s.replace("</body>",reg+"</body>",1)

p.write_text(s,encoding="utf-8")
