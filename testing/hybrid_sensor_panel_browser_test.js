#!/usr/bin/env node
'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),path=require('node:path');
function element(){return {dataset:{},children:[],textContent:'',checked:false,appendChild(child){this.children.push(child);},replaceChildren(...children){this.children=children;},addEventListener(key,fn){this[key]=fn;}};}
const nodes=Object.fromEntries(['sensor-tool','sensor-status','sensor-refresh','sensor-show-all','sensor-user-rows','sensor-temp-rows'].map(id=>[id,element()]));
nodes['sensor-tool'].dataset={url:'/js/sensor_panel',camera:'2'};
const requests=[],events={};let poll;
vm.runInNewContext(fs.readFileSync(path.join(__dirname,'../indi_allsky/flask/static/modern_admin/sensor-panel.js'),'utf8'),{
 document:{getElementById:id=>nodes[id],createElement:element},AbortController,URLSearchParams,
 window:{setInterval:fn=>{poll=fn;return 1;},clearInterval(){},addEventListener:(key,fn)=>events[key]=fn},
 fetch:(url,options)=>new Promise(resolve=>requests.push({url,options,resolve}))});
const data={last_update:'2026-09-07 09:00:00',last_update_age_s:5,readings:Object.fromEntries(['user','temp'].map(group=>[group,Array.from({length:60},(_,i)=>({slot:`sensor_${group}_${i}`,label:'<sensor>',value:i===0?0:null,used:i===0}))]))};
const tick=()=>new Promise(resolve=>setImmediate(resolve));
const respond=(i,value,extra={})=>requests[i].resolve({ok:true,json:async()=>value,...extra});
(async()=>{
 assert(requests[0].url.endsWith('camera_id=2'));poll();assert.equal(requests.length,1);
 respond(0,data);await tick();
 const rows=nodes['sensor-user-rows'].children;
 assert.equal(rows.length,60);assert.equal(rows[0].children[2].textContent,'0');assert.equal(rows[1].children[2].textContent,'Unavailable');
 assert.equal(rows[0].children[1].textContent,'<sensor>');assert(rows[1].hidden&&!rows[0].hidden);
 nodes['sensor-show-all'].checked=true;nodes['sensor-show-all'].change();assert(rows.every(row=>!row.hidden));
 nodes['sensor-refresh'].click();respond(1,{...data,readings:{user:[],temp:[]}});await tick();
 assert(nodes['sensor-status'].textContent.includes('out of date'));assert.equal(nodes['sensor-user-rows'].children[0],rows[0]);
 poll();respond(2,null,{redirected:true});await tick();assert(nodes['sensor-status'].textContent.includes('Session expired'));
 poll();respond(3,{...data,last_update:null});await tick();assert(nodes['sensor-status'].textContent.includes('No image metadata'));
 poll();events.pagehide();assert(requests[4].options.signal.aborted);
 console.log('Sensor controller: camera scope, 120 slots, real zero, absent values, filter, atomic errors, expired session, refresh and teardown: PASS');
})().catch(error=>{console.error(error);process.exitCode=1;});
