import os,re,io,json,uuid,zipfile,shutil,subprocess,secrets
from pathlib import Path
from typing import Optional
from fastapi import FastAPI,Header,HTTPException,UploadFile,File
app=FastAPI(title="PHH Runner",docs_url=None,redoc_url=None)
TOKEN=os.getenv("RUNNER_TOKEN","");ROOT=Path("/srv/bots");MAX=int(os.getenv("MAX_UPLOAD_MB","20"))*1024*1024
ROOT.mkdir(parents=True,exist_ok=True)
def auth(v):
 if not TOKEN or not v or not secrets.compare_digest(v,"Bearer "+TOKEN): raise HTTPException(401,"Unauthorized")
def cmd(*args,timeout=30):
 p=subprocess.run(["docker",*args],capture_output=True,text=True,timeout=timeout)
 if p.returncode: raise HTTPException(400,detail=(p.stderr or p.stdout or "Docker error")[-2000:])
 return p.stdout.strip()
def path_for(i):
 if not re.fullmatch(r"[a-f0-9]{12}",i): raise HTTPException(400,"Invalid bot id")
 p=(ROOT/i).resolve()
 if not p.is_relative_to(ROOT.resolve()) or not p.is_dir(): raise HTTPException(404,"Bot not found")
 return p
def status(i):
 p=subprocess.run(["docker","inspect","-f","{{.State.Status}}","phh-bot-"+i],capture_output=True,text=True)
 return p.stdout.strip() if p.returncode==0 else "stopped"
def launch(i):
 p=path_for(i);entry=json.loads((p/"hub.json").read_text()).get("entrypoint","main.py");n="phh-bot-"+i
 if status(i)!="stopped": cmd("rm","-f",n)
 cmd("run","-d","--name",n,"--restart=no","--memory=256m","--cpus=0.50","--pids-limit=128","--cap-drop=ALL","--security-opt=no-new-privileges","--user","10001:10001","-v",f"{p}:/bot:ro","-w","/bot","python:3.12-slim","sh","-lc","python -m pip install --disable-pip-version-check --no-cache-dir --target /tmp/botpkgs -r requirements.txt >/tmp/pip.log 2>&1; export PYTHONPATH=/tmp/botpkgs; exec python -u "+entry)
 return {"ok":True,"id":i,"status":"running"}
@app.get("/health")
def health(): return {"ok":True,"service":"runner"}
@app.get("/bots")
def bots(authorization:Optional[str]=Header(default=None)):
 auth(authorization);out=[]
 for p in sorted(ROOT.iterdir()):
  if p.is_dir() and re.fullmatch(r"[a-f0-9]{12}",p.name):
   try:m=json.loads((p/"hub.json").read_text())
   except:m={}
   out.append({"id":p.name,"name":m.get("name",p.name),"entrypoint":m.get("entrypoint","main.py"),"status":status(p.name)})
 return {"bots":out}
@app.post("/upload")
async def upload(authorization:Optional[str]=Header(default=None),file:UploadFile=File(...)):
 auth(authorization)
 if not file.filename or not file.filename.lower().endswith(".zip"):raise HTTPException(400,"Upload a .zip file")
 raw=await file.read(MAX+1)
 if len(raw)>MAX:raise HTTPException(413,f"ZIP limit is {MAX//1048576} MB")
 i=uuid.uuid4().hex[:12];tmp=ROOT/(".tmp-"+i);dest=ROOT/i
 try:
  tmp.mkdir()
  with zipfile.ZipFile(io.BytesIO(raw)) as z:
   infos=z.infolist()
   if len(infos)>500:raise HTTPException(400,"Too many files")
   total=0
   for x in infos:
    q=Path(x.filename)
    if q.is_absolute() or ".." in q.parts:raise HTTPException(400,"Unsafe ZIP path")
    total+=x.file_size
    if total>100*1048576:raise HTTPException(413,"Uncompressed ZIP too large")
   z.extractall(tmp)
  kids=list(tmp.iterdir())
  if len(kids)==1 and kids[0].is_dir():
   nested=kids[0]
   for x in list(nested.iterdir()):shutil.move(str(x),str(tmp/x.name))
   nested.rmdir()
  entry="main.py" if (tmp/"main.py").is_file() else "app.py" if (tmp/"app.py").is_file() else ""
  if not entry:raise HTTPException(400,"ZIP root needs main.py or app.py")
  if not (tmp/"requirements.txt").exists():(tmp/"requirements.txt").write_text("")
  (tmp/"hub.json").write_text(json.dumps({"name":Path(file.filename).stem[:80],"entrypoint":entry}))
  tmp.rename(dest);return {"ok":True,"id":i,"name":Path(file.filename).stem,"entrypoint":entry}
 except zipfile.BadZipFile:
  shutil.rmtree(tmp,ignore_errors=True);raise HTTPException(400,"Invalid ZIP")
 except Exception:
  shutil.rmtree(tmp,ignore_errors=True);raise
@app.post("/bots/{i}/start")
def start(i:str,authorization:Optional[str]=Header(default=None)):auth(authorization);return launch(i)
@app.post("/bots/{i}/restart")
def restart(i:str,authorization:Optional[str]=Header(default=None)):auth(authorization);return launch(i)
@app.post("/bots/{i}/stop")
def stop(i:str,authorization:Optional[str]=Header(default=None)):
 auth(authorization);path_for(i)
 if status(i)!="stopped":cmd("rm","-f","phh-bot-"+i)
 return {"ok":True,"id":i,"status":"stopped"}
@app.get("/bots/{i}/logs")
def logs(i:str,authorization:Optional[str]=Header(default=None)):
 auth(authorization);path_for(i)
 p=subprocess.run(["docker","logs","--tail","250","phh-bot-"+i],capture_output=True,text=True,timeout=20)
 return {"id":i,"logs":((p.stdout or "")+(p.stderr or ""))[-24000:]}
