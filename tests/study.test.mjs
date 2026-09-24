import {test} from 'node:test';
import assert from 'node:assert/strict';
import {products,sources,totals,csvCell,parseRecords,corpus,topicStats} from '../static/study-data.js';
test('paired comparison keeps width constant and computes explicit phone totals',()=>{
 assert.equal(products[0].width,products[1].width);
 assert.deepEqual(totals('5k'),{depth:16.4,weight:292});
 assert.deepEqual(totals('10k'),{depth:22.5,weight:385.9});
 assert.deepEqual(totals('5k',false),{depth:8.6,weight:122});
 assert.throws(()=>totals('other'));
});
test('sources have unique identifiers, bilingual limits and HTTPS provenance',()=>{
 assert.equal(new Set(sources.map(s=>s.id)).size,15);
 for(const s of sources){assert.equal(new URL(s.url).protocol,'https:');assert.ok(s.limits.zh&&s.limits.en&&s.summary.zh&&s.summary.en)}
 assert.equal(sources.filter(s=>s.type==='discussion').length,6);
 assert.deepEqual({pages:corpus.sourcePages,statements:corpus.consumerStatements,products:corpus.productSnapshots},{pages:15,statements:19,products:8});
 assert.equal(topicStats[0].count,9);
 assert.ok(topicStats.every(x=>x.share<=100&&['A','B','C'].includes(x.strength)));
});
test('invalid local records do not become research observations',()=>{
 for(const input of ['{}','null','invalid','[null,{},1]'])assert.deepEqual(parseRecords(input),[]);
 const r={id:'1',variant:'A',task:'topup',choice:'5k',seconds:10,reason:'actual response',understood:true};
 assert.equal(parseRecords(JSON.stringify([r,{...r,seconds:-1},{...r,variant:'C'}])).length,1);
});
test('CSV escapes quotes and guards spreadsheet formula injection',()=>{
 assert.equal(csvCell('a,"b"'),'"a,""b"""');
 assert.equal(csvCell('=1+1'),'"\'=1+1"');
 assert.equal(csvCell('line\nnext'),'"line\nnext"');
});
