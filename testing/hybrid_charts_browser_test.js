#!/usr/bin/env node
'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const source = fs.readFileSync(require('node:path').join(__dirname, '../indi_allsky/flask/static/modern_admin/charts.js'), 'utf8');
const keys = ['jsqm','stars','temp','exp','gain','detection', ...Array.from({length:9}, (_,i)=>`custom_${i+1}`)];
const requests=[], charts=[], events={}, statuses=[];
const canvases=[...keys,'histogram'].map(key=>{
    const status={textContent:''}; statuses.push(status);
    return {dataset:{key,label:key},closest:()=>({querySelector:()=>status})};
});
const root={dataset:{url:'/js/chart',camera:'2',timestamp:'123',refresh:'15000'},querySelectorAll:()=>canvases};
const history={value:'900',addEventListener:(name,fn)=>events[name]=fn};
const message={textContent:''};
let poll,cleared=false;
vm.runInNewContext(source, {
    document:{getElementById:id=>id==='chart-tool'?root:id==='HISTORY_SELECT'?history:message},
    Chart:function(canvas,config){this.data=config.data;this.update=()=>{};charts.push(this);},
    AbortController, URLSearchParams,
    window:{setInterval:fn=>{poll=fn;return 7;},clearInterval:id=>{assert.equal(id,7);cleared=true;},addEventListener:(name,fn)=>events[name]=fn},
    fetch:(url,options)=>new Promise((resolve,reject)=>requests.push({url,options,resolve,reject}))
});
const tick=()=>new Promise(resolve=>setImmediate(resolve));
const payload=(value=42)=>({chart_data:Object.assign(Object.fromEntries(keys.map(key=>[key,[{x:'08:00:00',y:value}]])),
    {histogram:Object.fromEntries(['red','green','blue','gray'].map(key=>[key,[{x:'5',y:value}]]))})});
const respond=(index,data,extra={})=>requests[index].resolve({ok:true,json:async()=>data,...extra});
(async()=>{
    assert.equal(charts.length,16); assert.equal(requests.length,1);
    assert.equal(requests[0].url,'/js/chart?camera_id=2&limit_s=900&timestamp=123');
    poll(); assert.equal(requests.length,1,'No overlapping polling');
    respond(0,payload()); await tick();
    for(const chart of charts)for(const series of chart.data.datasets)assert.equal(series.data[0].y,42);
    assert(statuses.every(status=>status.textContent===''));
    poll(); const malformed=payload(99);delete malformed.chart_data.custom_9;
    respond(1,malformed);await tick();
    assert(message.textContent.includes('out of date'));
    assert.equal(charts[0].data.datasets[0].data[0].y,42,'Invalid response must not partially replace data');
    history.value='3600';events.change(); const old=requests[2];
    history.value='86400';events.change();assert(old.options.signal.aborted);
    respond(3,payload(84));await tick();respond(2,payload(11));await tick();
    assert.equal(charts[0].data.datasets[0].data[0].y,84,'Late response ignored');
    assert(requests[3].url.includes('limit_s=86400'));
    poll(); respond(4,payload(null));await tick();assert(statuses.every(status=>status.textContent.includes('No readings')));
    poll();const empty=payload();for(const key of keys)empty.chart_data[key]=[];
    for(const key of Object.keys(empty.chart_data.histogram))empty.chart_data.histogram[key]=[];
    respond(5,empty);await tick();assert(statuses.every(status=>status.textContent.includes('No readings')));
    poll();respond(6,null,{redirected:true});await tick();assert(message.textContent.includes('Session expired'));
    poll();respond(7,null,{ok:false});await tick();assert(message.textContent.includes('Could not load'));
    poll();requests[8].reject(Error('offline'));await tick();assert(message.textContent.includes('Could not load'));
    poll();events.pagehide();assert(cleared&&requests[9].options.signal.aborted);
    console.log('Charts: all 15 series and histogram, empty/null data, atomic validation, history, stale responses, polling, HTTP/session/network errors and teardown: PASS');
})().catch(error=>{console.error(error);process.exitCode=1;});
