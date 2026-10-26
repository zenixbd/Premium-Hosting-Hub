import crypto from "node:crypto";
const name="phh_session";function sign(v){return crypto.createHmac("sha256",process.env.SESSION_SECRET||"").update(v).digest("base64url")}
export function json(res,status,obj){res.statusCode=status;res.setHeader("Content-Type","application/json; charset=utf-8");res.end(JSON.stringify(obj))}
export async function readJson(req){let s="";for await(const c of req)s+=c;try{return JSON.parse(s||"{}")}catch{return {}}}
export function setCookie(res,v,max=86400){res.setHeader("Set-Cookie",`${name}=${v}.${sign(v)}; HttpOnly; Secure; SameSite=Lax; Path=/; Max-Age=${max}`)}
export function clearCookie(res){res.setHeader("Set-Cookie",`${name}=; HttpOnly; Secure; SameSite=Lax; Path=/; Max-Age=0`)}
export function isAuthed(req){if(!process.env.SESSION_SECRET)return false;let c=(req.headers.cookie||"").split(";").map(x=>x.trim()).find(x=>x.startsWith(name+"="));if(!c)return false;let t=c.slice(name.length+1),i=t.lastIndexOf(".");if(i<1)return false;let v=t.slice(0,i),s=t.slice(i+1),e=sign(v);return v==="admin"&&s.length===e.length&&crypto.timingSafeEqual(Buffer.from(s),Buffer.from(e))}
export async function runnerFetch(path,opt={}){let base=(process.env.RUNNER_URL||"").replace(/\/+$/,""),token=process.env.RUNNER_TOKEN||"";if(!base||!token)throw Error("Vercel Environment Variables RUNNER_URL এবং RUNNER_TOKEN সেট করা নেই");let h=new Headers(opt.headers||{});h.set("Authorization","Bearer "+token);return fetch(base+path,{...opt,headers:h,signal:AbortSignal.timeout(25000)})}
export async function bytes(req){let a=[];for await(const c of req)a.push(c);return Buffer.concat(a)}
