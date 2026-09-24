import {test} from 'node:test';
import assert from 'node:assert/strict';
import worker from '../cloudflare/worker.mjs';
import data from '../cloudflare/snapshot.json' with {type:'json'};
const rid=data.demo.current_id;
const call=(path,method='GET',body)=>worker.fetch(new Request('https://test.invalid'+path,{method,...(body?{body:JSON.stringify(body)}:{})}),{ASSETS:{fetch:async()=>new Response('asset')}});
test('public API exposes only saved cases and never connector settings',async()=>{
  for(const path of ['/api/health','/api/config','/api/researches',`/api/research/${rid}`,`/api/research/${rid}/summary`,`/api/research/${rid}/products`,`/api/research/${rid}/trends`])assert.equal((await call(path)).status,200);
  assert.equal((await call('/api/demo/load','POST')).status,200);
  assert.equal((await call('/api/research/999999/summary')).status,404);
  const config=await (await call('/api/config')).json();assert.equal(config.llm_base_url,'');assert.equal(config.allow_public_live_research,false);
  for(const path of ['/api/settings','/api/research',`/api/research/${rid}/import`])assert.equal((await call(path,'POST',{})).status,403);
  assert.equal((await call('/api/connections/test')).status,403);
  const research=await (await call(`/api/research/${rid}`)).json();
  assert.match(research.status_message,/67 coded signals/);
  const summary=await (await call(`/api/research/${rid}/summary`)).json();
  assert.match(summary.research.decision.demo_meta.executive_recommendation,/device fit before capacity/i);
  assert.match(summary.opportunities.find(x=>x.decision).decision.gtm_action,/device check/);
});
test('review filtering, pagination, unknown fields and source boundaries',async()=>{
  const rows=await (await call(`/api/research/${rid}/reviews?limit=2`)).json();assert.equal(rows.rows.length,2);assert.ok(rows.has_more);
  const empty=await (await call(`/api/research/${rid}/reviews?market=AU`)).json();assert.equal(empty.total,0);
  assert.equal((await call(`/api/research/${rid}/reviews?limit=-1`)).status,422);
  assert.equal((await call(`/api/research/${rid}/reviews?offset=NaN`)).status,422);
  assert.equal((await call(`/api/research/${rid}/secret`)).status,404);
});
test('Ask admits insufficiency and cites matching saved evidence',async()=>{
  const ask=async question=>(await (await call(`/api/research/${rid}/ask`,'POST',{question})).json()).answer;
  assert.match(await ask('What is the orbital period of Neptune?'),/Evidence insufficient/);
  assert.match(await ask('What evidence supports portability?'),/\[E\d+\].*GLOBAL/);
  assert.match(await ask('Compare US and AU consumers'),/do not establish/);
  assert.equal((await call(`/api/research/${rid}/ask`,'POST',{question:'x'})).status,422);
});
test('historical comparison and downloadable exports remain available',async()=>{
  const r=await (await call(`/api/research/${rid}/compare/${data.demo.baseline_id}`)).json();assert.ok(r.common_sources.length);
  for(const kind of ['pdf','csv','docx']){const r=await call(`/api/research/${rid}/export/${kind}`);assert.equal(r.status,200);assert.match(r.headers.get('Content-Disposition'),/attachment/);}
});
