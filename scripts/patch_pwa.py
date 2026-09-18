from pathlib import Path
p=Path("app/index.html")
s=p.read_text(encoding="utf-8")
meta='''<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="KPC Mental Game">
<link rel="manifest" href="manifest.webmanifest">
<link rel="apple-touch-icon" href="logo.svg">'''
s=s.replace("</head>",meta+"</head>",1)
reg='''<script>if("serviceWorker" in navigator){window.addEventListener("load",()=>navigator.serviceWorker.register("./sw.js").catch(()=>{}));}</script>'''
s=s.replace("</body>",reg+"</body>",1)
p.write_text(s,encoding="utf-8")
