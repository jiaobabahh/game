'use strict';
const $ = id => document.getElementById(id);
const escapeHtml = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const modes = {
  prop: {title:'命题逻辑', help:'检查公式分类、主范式和两式等价性。不等价时给出反例赋值。', fields:[['a','公式 A','text','P → Q'],['b','公式 B（可选，用于等价判断）','text','¬P ∨ Q']]},
  set: {title:'集合', help:'填写集合断言。给出具体赋值，或留空赋值，在有限宇宙内搜索反例。', fields:[['claim','待核验断言','text','A ∩ (B ∪ C) = (A ∩ B) ∪ C'],['env','集合赋值（可选，每行一条）','textarea',''],['universe','有限宇宙（用于穷举）','text','1,2']]},
  rel: {title:'关系', help:'输入基本集与序偶，检查自反、对称、反对称、传递等性质。', fields:[['base','基本集','text','{1,2,3}'],['pairs','序偶集合','textarea','(1,1),(2,2),(3,3),(1,2),(2,1)']]},
  graph: {title:'图论', help:'输入简单无向图的边，检查连通性、度序列、欧拉回路与通路。', fields:[['edges','边列表','textarea','1-2, 2-3, 3-4, 4-1, 1-3']]},
  dissect: {title:'推理题拆解', help:'支持真话／说谎类受限句式。粘贴 AI 答案，查看已解析断言与反例。', fields:[['question','题目原文','textarea','如果甲说真话，那么乙说真话；甲和乙不可能都是真话；乙和丙至少有一个说真话。'],['extra','补充约束（可选，填写后替代原文用于解析）','textarea',''],['answer','待核验的 AI 答案（可选）','textarea','甲说的是真话。']]},
  regression: {title:'案例回归', help:'实际运行原项目预先定义的 60 条回归案例，列出每条案例的结果。', fields:[]}
};
let mode = 'prop', worker, ready = false, busy = false, requestId = 0, activeId = 0, timer, lastResult, presets = {}, drafts = {};
const safeJson = value => JSON.stringify(value, null, 2);
const showValue = value => typeof value === 'boolean' ? (value ? '真' : '假') : typeof value === 'object' && value !== null ? safeJson(value) : String(value ?? '');
function table(rows) {
  if (!rows?.length) return '<p class="note">没有可展示的行。</p>';
  const keys = [...new Set(rows.flatMap(Object.keys))];
  return '<div class="table-wrap"><table><thead><tr>' + keys.map(k=>'<th>'+escapeHtml(k)+'</th>').join('') + '</tr></thead><tbody>' + rows.map(row=>'<tr>'+keys.map(k=>'<td class="'+(row[k] === true?'yes':row[k] === false?'no':'')+'">'+escapeHtml(showValue(row[k]))+'</td>').join('')+'</tr>').join('') + '</tbody></table></div>';
}
function banner(title, text = '', state = '') {
  return `<div class="verdict ${state}"><h3>${escapeHtml(title)}</h3>${text ? `<p>${escapeHtml(text)}</p>` : ''}</div>`;
}
function block(title, content) {return '<h3>'+escapeHtml(title)+'</h3><pre>'+escapeHtml(typeof content === 'string' ? content : safeJson(content))+'</pre>';}
function graphSvg(nodes, edges, directed) {
  const n = nodes.length, radius = 96;
  const points = nodes.map((label,i)=>({label, x:210+radius*Math.cos(2*Math.PI*i/n-Math.PI/2), y:130+radius*Math.sin(2*Math.PI*i/n-Math.PI/2)}));
  const lookup = new Map(points.map(p=>[String(p.label),p]));
  let drawing = '<svg class="graph" viewBox="0 0 420 260" role="img" aria-label="输入结构示意图"><defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" fill="#7193a6"/></marker></defs>';
  edges.forEach(([a,b])=>{
    const p = lookup.get(String(a)), q = lookup.get(String(b)); if (!p || !q) return;
    if (p===q) {drawing += `<path d="M ${p.x-9},${p.y-9} C ${p.x-44},${p.y-49} ${p.x+44},${p.y-49} ${p.x+9},${p.y-9}" fill="none" stroke="#7193a6" ${directed?'marker-end="url(#arrow)"':''}/>`;return;}
    const length=Math.hypot(q.x-p.x,q.y-p.y), dx=(q.x-p.x)/length*17, dy=(q.y-p.y)/length*17;
    drawing += `<line x1="${p.x+dx}" y1="${p.y+dy}" x2="${q.x-dx}" y2="${q.y-dy}" stroke="#7193a6" stroke-width="1.5" ${directed?'marker-end="url(#arrow)"':''}/>`;
  });
  points.forEach(p=>{drawing += `<circle cx="${p.x}" cy="${p.y}" r="16" fill="#123e55"/><text x="${p.x}" y="${p.y+4}" text-anchor="middle" fill="white" font-size="11">${escapeHtml(p.label)}</text>`;});
  return drawing+'</svg><p class="note">结构示意图；详细性质以核验表为准。</p>';
}
function renderResult(r) {
  let html = '';
  if (mode === 'prop') {
    html += banner(r.title, r.detail || '已穷举该公式所有命题赋值。', r.ok === false ? 'bad':'');
    if (r.counterexample) html += block('反例赋值', r.counterexample);
    html += block('规范公式', r.formula) + block('主析取范式', r.dnf) + block('主合取范式', r.cnf);
    html += '<h3>公式 A 的真值表</h3>'+table(r.table);
  } else if (mode === 'set') {
    html += banner(r.ok === null?'尚未完成穷举':r.ok?'断言成立':'断言不成立',r.detail,r.ok===false?'bad':r.ok===null?'warn':'');
    html += '<p class="note">核验模式：'+escapeHtml(r.mode)+'</p>';
    if (r.counterexample) html += block('可复现反例',r.counterexample);
    if (r.mode==='全称验证') html+='<p class="note">结论仅覆盖本次指定的有限宇宙。</p>';
  } else if (mode === 'rel') {
    html += banner(r.title);
    html += table(Object.entries(r.properties).map(([name,[ok,reason]])=>({'性质':name,'成立':ok,'依据':reason})));
    if (r.classes.length) html += block('等价类',r.classes);
    html += graphSvg(r.nodes,r.edges,r.directed);
  } else if (mode === 'graph') {
    html += banner(r.title,r.properties['反例']);
    html += table(Object.entries(r.properties).map(([k,v])=>({'性质':({order:'顶点数',size:'边数'})[k] || k,'结果':v})));
    html += graphSvg(r.nodes,r.edges,r.directed);
  } else if (mode === 'dissect') {
    const partial = r.unsupported.length > 0;
    html += banner(partial?'部分文字尚未解析':'已解析约束',partial?'以下结果仅基于已识别条件，不能视为对整道题的完整核验。':'请核对符号化条件是否准确表达原题。',partial?'warn':'');
    if (partial) html += block('尚未解析的文字',r.unsupported.join('\n'));
    html += '<h3>原子命题</h3>'+table(r.var_table.map(v=>({'符号':v.var,'人物':v.name,'含义':v.meaning})));
    html += '<h3>已识别约束</h3>'+table(r.conditions.map(c=>({'原句':c.sent,'公式':c.fstr})));
    html += '<h3>在已解析约束下的结论</h3>'+table(Object.entries(r.verdict).map(([name,value])=>({'人物':name,'结论':value})));
    if (!r.rows.length) html += banner('已解析条件互相矛盾','没有满足全部已解析条件的赋值。','bad');
    html += '<h3>AI 断言核验</h3>';
    if (r.claims.length) html += table(r.claims.map(c=>({'断言':c.raw || c.formula || '', '成立':c.ok,'状态':c.status,'依据':c.why,'反例':c.counter || ''})));
    else html += '<p class="note">未识别到可核验的 AI 断言；不代表 AI 答案正确。</p>';
    html += '<h3>满足已解析约束的赋值</h3>'+table(r.rows);
    html += '<details><summary>查看完整真值表</summary>'+table(r.table)+'</details>';
  } else html += banner(r.title)+table(r.table);
  $('result').innerHTML='<div class="detail">'+html+'</div>';
}
function readInput() {const p={mode};modes[mode].fields.forEach(([id,,,value])=>p[id]=$(id)?.value ?? value);return p;}
function invalidate() {
  if (lastResult || busy) {
    lastResult = null; $('download').disabled=true;
    if (busy) {clearTimeout(timer); activeId=++requestId; busy=false; restart();}
    $('result').innerHTML='<p class="stale">输入已改变，请重新核验后查看或下载结果。</p>';
  }
}
function switchMode(next) {
  drafts[mode]=readInput(); invalidate(); mode=next;
  document.querySelectorAll('#tabs button').forEach(b=>{b.classList.toggle('active',b.dataset.mode===mode);if(b.dataset.mode===mode)b.setAttribute('aria-current','page');else b.removeAttribute('aria-current');});
  $('input-title').textContent=modes[mode].title;$('mode-help').textContent=modes[mode].help;
  $('example').hidden=mode==='regression';
  $('fields').innerHTML=modes[mode].fields.map(([id,label,type,value])=>'<label for="'+id+'">'+escapeHtml(label)+'</label>'+(type==='textarea'?'<textarea id="'+id+'" rows="'+(id==='question'?5:3)+'" maxlength="4000">'+escapeHtml(drafts[mode]?.[id] ?? value)+'</textarea>':'<input id="'+id+'" maxlength="4000" autocomplete="off" value="'+escapeHtml(drafts[mode]?.[id] ?? value)+'">')).join('');
  $('result').innerHTML='<div class="empty"><span>⊢</span><h3>准备核验'+escapeHtml(modes[mode].title)+'</h3><p>载入示例，或直接填写你的题目。</p></div>';
  lastResult=null;$('download').disabled=true;updateButton();
}
function updateButton() {$('run').disabled=!ready||busy;$('run').textContent=busy?'正在核验…':!ready?'正在准备引擎…':mode==='regression'?'运行全部案例':'开始核验';$('cancel').hidden=!busy;}
function fail(text) {clearTimeout(timer);busy=false;$('result').innerHTML=banner('未能完成核验',text,'bad');updateButton();}
function restart() {
  worker?.terminate();ready=false;busy=false;lastResult=null;$('download').disabled=true;
  $('engine').className='engine';$('engine-text').textContent='正在启动核验引擎…';$('retry').hidden=true;updateButton();
  worker=new Worker('./worker.js');
  worker.onmessage=({data})=>{
    if(data.type==='status'){$('engine-text').textContent=data.text;return;}
    if(data.type==='ready'){clearTimeout(timer);ready=true;presets=data.presets;$('engine').className='engine ready';$('engine-text').textContent='核验引擎已就绪 · 输入在浏览器内计算';updateButton();return;}
    if(data.type==='error'){
      if(data.id && data.id!==activeId)return;
      if(!ready){$('engine').className='engine failed';$('engine-text').textContent='引擎加载失败，请检查网络后重试。';$('retry').hidden=false;}
      fail(data.text);return;
    }
    if(data.type==='result' && data.id===activeId){clearTimeout(timer);busy=false;lastResult={input:readInput(),result:data.result,verifiedAt:new Date().toISOString()};renderResult(data.result);$('download').disabled=false;updateButton();}
  };
  worker.onerror=e=>{ready=false;$('engine').className='engine failed';$('engine-text').textContent='引擎启动失败';$('retry').hidden=false;fail(e.message);};
  worker.postMessage({type:'init'});
  timer=setTimeout(()=>{if(!ready){worker.terminate();$('engine').className='engine failed';$('engine-text').textContent='引擎加载超过 90 秒，请检查网络后重试。';$('retry').hidden=false;}},90000);
}
$('tabs').addEventListener('click',e=>{if(e.target.dataset.mode)switchMode(e.target.dataset.mode);});
$('fields').addEventListener('input',invalidate);
$('example').addEventListener('click',()=>{invalidate();modes[mode].fields.forEach(([id,, ,value])=>$(id).value=value);if(mode==='dissect'&&Object.keys(presets).length){const p=Object.values(presets)[0];$('question').value=p.question;$('answer').value=p.ai_answer;}});
$('form').addEventListener('submit',e=>{e.preventDefault();if(!ready||busy)return;lastResult=null;$('download').disabled=true;busy=true;activeId=++requestId;updateButton();$('result').innerHTML='<p class="loading" role="status">正在计算，请稍候…</p>';worker.postMessage({id:activeId,payload:readInput()});clearTimeout(timer);timer=setTimeout(()=>{restart();fail('计算超过 30 秒，请减少变量或缩小输入后重试。');},30000);});
$('cancel').addEventListener('click',()=>{clearTimeout(timer);activeId=++requestId;restart();$('result').innerHTML='<p class="stale">计算已取消。引擎重新准备后可再次核验。</p>';});
$('retry').addEventListener('click',restart);
$('download').addEventListener('click',()=>{if(!lastResult)return;const url=URL.createObjectURL(new Blob([safeJson(lastResult)],{type:'application/json;charset=utf-8'}));const a=document.createElement('a');a.href=url;a.download='离散数学核验结果.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);});
switchMode('prop');restart();
