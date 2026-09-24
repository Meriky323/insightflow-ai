// Local preview of the exact public Worker handler; no analyst services.
import http from 'node:http';
import {readFile} from 'node:fs/promises';
import {resolve,sep,extname} from 'node:path';
import worker from '../cloudflare/worker-built.mjs';
const root=resolve('cloudflare/public');
const types={'.html':'text/html; charset=utf-8','.css':'text/css','.js':'text/javascript','.pdf':'application/pdf','.csv':'text/csv','.docx':'application/vnd.openxmlformats-officedocument.wordprocessingml.document'};
const env={ASSETS:{fetch:async req=>{
  let name=decodeURIComponent(new URL(req.url).pathname);if(name==='/')name='/index.html';
  const file=resolve(root,'.'+name);
  if(!file.startsWith(root+sep)||name.includes('_worker'))return new Response('Not found',{status:404});
  try{return new Response(await readFile(file),{headers:{'Content-Type':types[extname(file)]||'application/octet-stream'}})}catch{return new Response('Not found',{status:404})}
}}};
http.createServer(async(req,res)=>{
  try{const chunks=[];for await(const c of req)chunks.push(c);
  const request=new Request('http://127.0.0.1:8787'+req.url,{method:req.method,headers:req.headers,...(!['GET','HEAD'].includes(req.method)?{body:Buffer.concat(chunks)}:{})});
  const response=await worker.fetch(request,env);res.writeHead(response.status,Object.fromEntries(response.headers));res.end(Buffer.from(await response.arrayBuffer()));
  }catch{res.writeHead(500);res.end('Preview error');}
}).listen(8787,'127.0.0.1',()=>console.log('Public preview http://127.0.0.1:8787'));
