import data from './snapshot.json' with { type: 'json' };

const headers = {'Content-Type':'application/json; charset=utf-8','Cache-Control':'no-store','X-Content-Type-Options':'nosniff'};
const json = (value,status=200) => new Response(JSON.stringify(value),{status,headers});
const fail = (message,status) => json({detail:message},status);
const topics = row => {try{return JSON.parse(row.topics_json||'[]')}catch{return []}};

export function answer(question, snapshot, language='en') {
  const zh=language==='zh', q=question.toLowerCase();
  const summary=snapshot.summary;
  const insufficient=zh?'证据不足。当前保存的案例无法回答这个问题。请缩小问题范围，或在本地分析模式补充证据。':'Evidence insufficient. This saved case cannot answer that question. Narrow the question or add evidence in Local Analyst Mode.';
  const boundary=zh?'这是人工整理的案例摘要，不是逐字评论或代表性抽样；不能推断销量、市场规模、因果关系或美国与澳洲的消费者偏好差异。':'These are curated paraphrases, not verbatim reviews or a representative sample. They do not establish sales, market size, causality, or US/AU preference differences.';
  if (/cannot|can't|limitations?|weak|insufficient|us.*au|market compar|不能|不足|边界|美国|澳洲|销量|预测|forecast|sales|market size/.test(q)) return boundary;
  if (/competitor|compare.*brand|竞品/.test(q)) return boundary+'\n\n'+snapshot.products.map(p=>`${p.title}: ${p.price??'—'} ${p.currency||''}\n${p.url||''}`).join('\n\n');
  const aliases={portability:['slim','carry','portability'],便携:['slim','carry','portability'],发热:['heat','hot','thermal'],heat:['heat','hot','thermal'],磁吸:['magnet'],适配:['fit','compatib'],价格:['price','value'],充电:['charg'],可靠:['reliab','durab']};
  const stop=new Set(['what','this','that','with','does','have','evidence','supports','support','why','rising','the','and','for','can','how']);
  const tokens=(q.match(/[a-z]{3,}/g)||[]).filter(x=>!stop.has(x));
  for(const [key,values] of Object.entries(aliases)) if(q.includes(key)) tokens.push(...values);
  const matches=snapshot.reviews.map(row=>({row,score:tokens.reduce((sum,t)=>sum+Number((row.text+' '+topics(row).join(' ')).toLowerCase().includes(t)),0)})).filter(x=>x.score>0).sort((a,b)=>b.score-a.score).slice(0,5).map(x=>x.row);
  if(/product|gtm|opportunit|validation|产品|机会|验证|营销/.test(q)) {
    const opportunities=summary.opportunities.filter(x=>x.decision?.insight);
    const selected=opportunities.find(x=>tokens.some(t=>x.name.toLowerCase().includes(t)))||opportunities[0];
    if(!selected) return insufficient;
    const d=selected.decision;
    if(zh) return `待验证的行动假设\n\n${data.translations[d.insight]||d.insight}\n\n产品动作：${data.translations[d.product_action]||d.product_action}\n\nGTM 动作：${data.translations[d.gtm_action]||d.gtm_action}\n\n下一步验证：${data.translations[d.next_validation]||d.next_validation}\n\n${boundary}`;
    return `${zh?'待验证的行动假设':'Action hypothesis to validate'}: ${selected.name}\n\n${d.insight}\n\nProduct action: ${d.product_action}\nGTM action: ${d.gtm_action}\nNext validation: ${d.next_validation}\n\n${boundary}`;
  }
  if(!matches.length) return insufficient;
  const intro=/why|rising|为什么|上升/.test(q)?(zh?'案例样本的变化不能证明市场趋势或原因。以下摘要与问题相关：':'Sample changes do not establish a market trend or its cause. Relevant evidence summaries:'):(zh?'以下为相关证据摘要：':'Relevant evidence summaries:');
  return intro+'\n\n'+matches.map(row=>`[E${row.id}] ${row.source} · ${row.market}\n${row.text}\n${row.url}`).join('\n\n')+'\n\n'+boundary;
}

export default {async fetch(request,env) {
  const url=new URL(request.url), path=url.pathname.replace(/\/$/,'')||'/';
  if(!path.startsWith('/api/')) return env.ASSETS.fetch(request);
  if(path==='/api/health' && request.method==='GET') return json({ok:true,version:'3.0-cloudflare',public_deployment:true,evidence_mode:'saved-curated-paraphrases',live_api_usage:false});
  if(path==='/api/config' && request.method==='GET') return json({public_deployment:true,allow_public_live_research:false,serpapi:false,llm:false,llm_base_url:'',llm_model:''});
  if(path==='/api/demo/load' && request.method==='POST') return json(data.demo);
  if(path==='/api/researches' && request.method==='GET') return json(data.researches);
  if(['/api/settings','/api/settings/clear','/api/connections/test','/api/research'].includes(path)||path.endsWith('/import')) return fail('Public recruiter mode is read-only. Run Local Analyst Mode for private research and connectors.',403);
  const match=path.match(/^\/api\/research\/(\d+)(?:\/(.*))?$/);
  if(!match||!data.snapshots[match[1]]) return fail('research not found',404);
  const snapshot=data.snapshots[match[1]], resource=match[2]||'';
  if(resource==='ask' && request.method==='POST') {
    if(Number(request.headers.get('content-length'))>8192) return fail('Request too large',413);
    let body;try {const raw=await request.text();if(raw.length>8192)return fail('Request too large',413);body=JSON.parse(raw)}catch{return fail('Invalid JSON',400)}
    if(typeof body.question!=='string'||body.question.trim().length<2||body.question.length>1000||!['en','zh',undefined].includes(body.language)) return fail('Invalid question or language',422);
    return json({mode:'local-snapshot',answer:answer(body.question,snapshot,body.language)});
  }
  if(request.method!=='GET') return fail('Method not allowed',405);
  if(!resource) return json(snapshot.research);
  if(['summary','products','trends'].includes(resource)) return json(snapshot[resource]);
  if(resource==='reviews') {
    const p=url.searchParams,limit=Number(p.get('limit')||500),offset=Number(p.get('offset')||0);
    if(!Number.isInteger(limit)||limit<1||limit>5000||!Number.isInteger(offset)||offset<0) return fail('Invalid pagination',422);
    const rows=snapshot.reviews.filter(row=>{
      for(const key of ['source','market','sentiment']) if(p.get(key)&&row[key]!==p.get(key))return false;
      if(p.get('issue')&&row.issue!==p.get('issue')&&!topics(row).includes(p.get('issue')))return false;
      return !p.get('q')||['title','text','issue','driver','barrier','scenario'].map(k=>row[k]||'').join(' ').toLowerCase().includes(p.get('q').toLowerCase());
    });
    return json({total:rows.length,rows:rows.slice(offset,offset+limit),limit,offset,has_more:offset+limit<rows.length});
  }
  if(resource.startsWith('compare/')) return snapshot.comparisons[resource.slice(8)]?json(snapshot.comparisons[resource.slice(8)]):fail('research not found',404);
  if(/^export\/(pdf|csv|docx)$/.test(resource)) {
    const kind=resource.slice(7);url.pathname=`/downloads/${match[1]}/insightflow.${kind}`;
    const response=await env.ASSETS.fetch(new Request(url));
    const result=new Response(response.body,response);
    result.headers.set('Content-Disposition',`attachment; filename="insightflow-${match[1]}.${kind}"`);
    return result;
  }
  return fail('Not found',404);
}};
