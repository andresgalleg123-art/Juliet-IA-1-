\
    # main.py - Juliet (complete, lightweight)
    import os, io, uuid
    from fastapi import FastAPI, HTTPException
    from fastapi.responses import HTMLResponse, StreamingResponse, FileResponse, JSONResponse
    from pydantic import BaseModel
    from typing import Optional, List, Dict

    app = FastAPI(title="Juliet - Complete (lightweight)")

    # --------------- Helpers ---------------
    EMOTION_KEYWORDS = {
        'happy': ['happy', 'feliz', 'genial', 'excelente', ':)'],
        'sad': ['triste', 'mal', 'deprimido', ':('],
        'angry': ['enojado', 'cabreado', 'molesto'],
        'question': ['?', 'como', 'qué', 'por qué', 'cuando', 'how', 'why']
    }

    def detect_emotion(text: str) -> Dict[str, float]:
        t = (text or "").lower()
        scores = {k:0.0 for k in EMOTION_KEYWORDS}
        for k, kws in EMOTION_KEYWORDS.items():
            for w in kws:
                if w in t:
                    scores[k] += 1.0
        s = sum(scores.values())
        if s > 0:
            for k in scores:
                scores[k] = round(scores[k]/s, 3)
        return scores

    # --------------- Chat ---------------
    class ChatIn(BaseModel):
        message: str

    @app.post("/chat")
    async def chat_endpoint(inp: ChatIn):
        msg = (inp.message or "").strip()
        emo = detect_emotion(msg)
        if not msg:
            reply = "No escribiste nada. Prueba a preguntarme algo."
        elif any(q in msg.lower() for q in ['como', 'qué', 'que', 'por qué', 'cuando', '?']):
            reply = "Buena pregunta — cuéntame más detalle y te ayudo."
        elif len(msg.split()) < 6:
            reply = f"Interesante. Me dijiste: «{msg}». ¿Quieres que lo explique más?"
        else:
            if any(w in msg.lower() for w in ['explica','resume','resumen','sintetiza']):
                reply = "Resumen breve: " + " ".join(msg.split()[:30]) + "..."
            else:
                reply = "Entendido. " + msg[:400]
        return {"response": reply, "emotion": emo}

    # --------------- Search (offline simple + online optional) ---------------
    DOCS: List = []
    class AddDoc(BaseModel):
        id: Optional[str]
        text: str

    @app.post("/search/add")
    async def add_doc(d: AddDoc):
        id = d.id or str(uuid.uuid4())
        DOCS.append((id, d.text))
        return {"id": id}

    @app.get("/search/query")
    async def search_query(q: str, k: int = 5):
        offline = []
        for id,text in DOCS:
            if q.lower() in text.lower():
                offline.append({"id": id, "text": text})
                if len(offline) >= k: break
        online = []
        try:
            from duckduckgo_search import ddg
            online = ddg(q, max_results=k) or []
        except Exception:
            online = []
        return {"query": q, "offline": offline, "online": online}

    # --------------- Diagram (DOT -> PNG) ---------------
    @app.post("/diagram")
    async def diagram(dot_text: str):
        try:
            import graphviz
            s = graphviz.Source(dot_text)
            fname = f"/tmp/diagram_{uuid.uuid4().hex}.png"
            s.format = 'png'
            path = s.render(filename=fname, cleanup=True)
            return FileResponse(path, media_type="image/png")
        except Exception:
            from PIL import Image, ImageDraw, ImageFont
            img = Image.new('RGB', (900, 300), color=(255,255,255))
            d = ImageDraw.Draw(img)
            try:
                font = ImageFont.load_default()
            except Exception:
                font = None
            d.text((10,10), dot_text[:400], fill=(0,0,0), font=font)
            buf = io.BytesIO()
            img.save(buf, format='PNG')
            buf.seek(0)
            return StreamingResponse(buf, media_type="image/png")

    # --------------- Math render ---------------
    @app.post("/math")
    async def math_render(expr: str):
        try:
            import sympy as sp
            import matplotlib.pyplot as plt
            try:
                e = sp.sympify(expr)
                text = sp.latex(e)
            except Exception:
                text = expr
            fig = plt.figure(figsize=(6,2))
            plt.axis('off')
            plt.text(0.01, 0.5, f"${text}$", fontsize=18)
            buf = io.BytesIO()
            fig.savefig(buf, format='png', bbox_inches='tight', dpi=150)
            plt.close(fig)
            buf.seek(0)
            return StreamingResponse(buf, media_type="image/png")
        except Exception:
            from PIL import Image, ImageDraw, ImageFont
            img = Image.new('RGB', (800, 200), color=(255,255,255))
            d = ImageDraw.Draw(img)
            try:
                font = ImageFont.load_default()
            except Exception:
                font = None
            d.text((10,10), "Sympy not available. Expr: " + (expr or "")[:300], fill=(0,0,0), font=font)
            buf = io.BytesIO()
            img.save(buf, format='PNG')
            buf.seek(0)
            return StreamingResponse(buf, media_type="image/png")

    # --------------- Simple homepage (mobile friendly) ---------------
    @app.get("/", response_class=HTMLResponse)
    async def homepage():
        html = \"\"\"<!doctype html><html lang='es'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>Juliet — Demo</title><meta name='description' content='Juliet - asistente IA demo'><style>body{font-family:system-ui,Arial;margin:16px;max-width:900px}textarea{width:100%}button{padding:8px 12px;border-radius:6px}</style></head><body><h1>Juliet — Demo</h1><div><textarea id='msg' rows='3' placeholder='Escribe...'></textarea><br><button onclick='send()'>Enviar</button><pre id='resp' style='background:#f3f4f6;padding:12px;border-radius:6px'></pre></div><hr><p>Funciones adicionales: /diagram (POST DOT) y /math (POST expr)</p><script>async function send(){const msg=document.getElementById('msg').value;const res=await fetch('/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message:msg})});const j=await res.json();document.getElementById('resp').innerText=JSON.stringify(j,null,2);}</script></body></html>\"\"\"
        return HTMLResponse(content=html)
