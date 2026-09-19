from pathlib import Path
import os

def patch(path_str):
    p=Path(path_str)
    s=p.read_text(encoding="utf-8")
    version=os.environ.get("KPC_APP_VERSION","").strip()
    if not version:
        raise SystemExit("KPC_APP_VERSION missing")

    badge='<span class="kpc-version-badge">Version '+version+'</span>'

    if 'kpc-version-badge' not in s:
        css='''<style id="kpc-version-badge-style">
.kpc-version-badge{display:inline-flex;align-items:center;margin-top:6px;padding:3px 8px;border:1px solid rgba(229,184,77,.45);border-radius:999px;background:rgba(229,184,77,.08);color:#e5b84d;font-size:10px;font-weight:800;letter-spacing:.06em;text-transform:uppercase;white-space:nowrap}
@media(max-width:430px){.kpc-version-badge{font-size:9px;padding:3px 7px}}
</style>'''
        s=s.replace('</head>',css+'</head>',1)

        needle='<div class="brand-copy"><span>Kings Poker Club</span><h1>'
        i=s.find(needle)
        if i<0:
            raise SystemExit("Brand header not found")
        h1_end=s.find('</h1>',i)
        if h1_end<0:
            raise SystemExit("Brand h1 end not found")
        insert_at=h1_end+5
        s=s[:insert_at]+badge+s[insert_at:]
    else:
        import re
        s=re.sub(r'<span class="kpc-version-badge">Version [^<]+</span>',badge,s,count=1)

    p.write_text(s,encoding="utf-8")

if __name__=="__main__":
    target=os.environ.get("KPC_APP_HTML","app/src/main/assets/index.html")
    patch(target)
    print("KPC version badge applied")
