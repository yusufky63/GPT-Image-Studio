import base64,json,time,mimetypes
from pathlib import Path
import requests
from .config import API_BASE,IMAGE_DIR
from .models import GenerationResult
from .pricing import calculate_cost
from .validation import validate_size,validate_options

class Cancelled(Exception): pass
def _usage_fields(usage):
    d=(usage or {}).get("input_tokens_details") or {}
    return ((usage or {}).get("input_tokens"),d.get("text_tokens"),d.get("image_tokens"),
            (usage or {}).get("output_tokens"),(usage or {}).get("total_tokens"))

class OpenAIImageClient:
    def __init__(self,api_key,timeout=900): self.api_key=api_key; self.timeout=timeout
    def auth(self): return {"Authorization":f"Bearer {self.api_key}"}
    def generate(self,prompt,model,size,quality,output_format="png",background="opaque",
                 partial_images=2,compression=90,moderation="auto",n=1,on_event=None,cancel=None,output_dir=None):
        w,h=validate_size(size); validate_options(model,quality,output_format)
        payload={"model":model,"prompt":prompt,"n":n,"size":size,"quality":quality,"output_format":output_format,
                 "background":background,"stream":True,"partial_images":max(0,min(3,int(partial_images))),"moderation":moderation}
        if output_format in ("jpeg","webp"): payload["output_compression"]=int(compression)
        started=time.monotonic(); final_b64=None; usage=None
        if on_event:on_event("request","Generation request sent.")
        headers={**self.auth(),"Content-Type":"application/json"}
        with requests.post(f"{API_BASE}/images/generations",headers=headers,json=payload,stream=True,timeout=(15,self.timeout)) as r:
            if not r.ok: self._raise(r)
            if on_event:on_event("connected",f"Connected (HTTP {r.status_code}).")
            for raw in r.iter_lines(decode_unicode=True):
                if cancel and cancel.is_set(): raise Cancelled("Generation cancelled locally.")
                if not raw or not raw.startswith("data:"): continue
                try:e=json.loads(raw[5:].strip())
                except:continue
                typ=e.get("type","")
                if "partial_image" in typ:
                    if on_event:on_event("partial",e)
                elif "completed" in typ:
                    final_b64=e.get("b64_json") or final_b64; usage=e.get("usage") or usage
                    if on_event:on_event("completed",e)
        if not final_b64: raise RuntimeError("API completed without a final image.")
        return self._save(final_b64,model,prompt,w,h,quality,output_format,started,usage,"generate",None,output_dir)

    def edit(self,image_path,prompt,model,size,quality,output_format="png",background="opaque",
             compression=90,moderation="auto",on_event=None,cancel=None,output_dir=None):
        w,h=validate_size(size); validate_options(model,quality,output_format)
        started=time.monotonic()
        data={"model":model,"prompt":prompt,"size":size,"quality":quality,"output_format":output_format,
              "background":background,"moderation":moderation,"n":"1"}
        if output_format in ("jpeg","webp"): data["output_compression"]=str(int(compression))
        files=[]; handles=[]
        try:
            p=Path(image_path); f=open(p,"rb"); handles.append(f)
            files.append(("image[]",(p.name,f,mimetypes.guess_type(p.name)[0] or "image/png")))
            if on_event:on_event("request","Edit/reference image uploaded to OpenAI.")
            r=requests.post(f"{API_BASE}/images/edits",headers=self.auth(),data=data,files=files,timeout=(15,self.timeout))
            if cancel and cancel.is_set(): raise Cancelled("Edit cancelled locally.")
            if not r.ok:self._raise(r)
            body=r.json()
            if not body.get("data"): raise RuntimeError("API returned no edited image.")
            b64=body["data"][0].get("b64_json"); usage=body.get("usage")
            if on_event:on_event("completed","Edited image received.")
            return self._save(b64,model,prompt,w,h,quality,output_format,started,usage,"edit",str(p),output_dir)
        finally:
            for hnd in handles:hnd.close()

    def _save(self,b64,model,prompt,w,h,quality,fmt,started,usage,op,source,output_dir=None):
        blob=base64.b64decode(b64,validate=True); ext="jpg" if fmt=="jpeg" else fmt
        out=Path(output_dir) if output_dir else IMAGE_DIR
        out.mkdir(parents=True,exist_ok=True)
        stamp=time.strftime("%Y-%m-%d_%H-%M-%S")
        path=out/f"{stamp}_{op}_{w}x{h}.{ext}"
        path.write_bytes(blob)
        if not path.exists() or path.stat().st_size != len(blob):
            raise IOError(f"Save verification failed: {path}")
        a,b,c,d,e=_usage_fields(usage)
        return GenerationResult(str(path),model,prompt,w,h,quality,fmt,time.monotonic()-started,len(blob),
                                a,b,c,d,e,calculate_cost(model,usage),op,source)
    def _raise(self,r):
        try:detail=r.json().get("error",{}).get("message",r.text)
        except:detail=r.text
        raise RuntimeError(f"OpenAI API {r.status_code}: {detail}")
