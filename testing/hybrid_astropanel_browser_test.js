#!/usr/bin/env node
'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),path=require('node:path');
const base=path.join(__dirname,'../indi_allsky/flask');
const template=fs.readFileSync(path.join(base,'templates/modern_admin/astropanel.html'),'utf8');
const source=fs.readFileSync(path.join(base,'static/modern_admin/astropanel.js'),'utf8');
function element(){return {textContent:'',children:[],appendChild(child){this.children.push(child);},replaceChildren(...children){this.children=children;},get firstChild(){return this.children[0];},addEventListener(event,fn){this[event]=fn;}};}
const nodes={};for(const id of [...template.matchAll(/id="([^"]+)"/g)].map(m=>m[1]))nodes[id]=element();
const fields=[...template.matchAll(/data-astro-field="([^"]+)"/g)].map(m=>Object.assign(element(),{dataset:{astroField:m[1]}}));
nodes['astropanel-tool'].dataset={url:'/ajax/astropanel',camera:'2'};
nodes['astropanel-tool'].querySelectorAll=()=>fields;
const pending=[],events={};let poll;
vm.runInNewContext(source,{document:{getElementById:id=>nodes[id],createElement:element},AbortController,URLSearchParams,
 window:{setInterval:fn=>{poll=fn;return 1;},clearInterval(){},addEventListener:(key,fn)=>events[key]=fn},
 fetch:(url,options)=>new Promise((resolve,reject)=>pending.push({url,options,resolve,reject}))});
const data={};for(const field of fields)data[field.dataset.astroField]='12:00';
for(const key of ['moon_phase','moon_light','moon_rise','moon_set','sun_alt','sun_rise','sun_set','polaris_hour_angle','polaris_alt'])data[key]=1;
for(const planet of ['mercury','venus','mars','jupiter','saturn','uranus','neptune'])for(const key of ['rise','transit','set','alt','az'])data[planet+'_'+key]=1;
data.satellite_list=Array.from({length:20},(_,i)=>({name:i===0?'<script>test</script>':'sat'+i,alt:1,az:2,rise:['1'],transit:['2'],set:['3'],duration:['10'],elevation:400}));
const tick=()=>new Promise(resolve=>setImmediate(resolve));
const respond=(i,value,extra={})=>pending[i].resolve({ok:true,json:async()=>value,...extra});
(async()=>{
 assert(pending[0].url.endsWith('camera_id=2'));poll();assert.equal(pending.length,1);
 respond(0,null,{ok:false});await tick();
 assert.equal(nodes['modern-admin-moon-phase'].textContent,'Unavailable');
 assert.equal(nodes['modern-admin-satellite-rows'].children[0].firstChild.colSpan,8);
 nodes['astropanel-refresh'].click();respond(1,data);await tick();
 assert.equal(nodes['modern-admin-planet-rows'].children.length,7);
 assert.equal(nodes['modern-admin-satellite-rows'].children.length,20,'No arbitrary truncation');
 assert.equal(nodes['modern-admin-satellite-rows'].children[0].firstChild.textContent,'<script>test</script>');
 assert.equal(nodes['modern-admin-satellite-rows'].children[0].children[6].textContent,'10');
 assert(fields.every(field=>field.textContent==='12:00'));
 poll();respond(2,{...data,sun_alt:{invalid:true}});await tick();
 assert(nodes['astropanel-status'].textContent.includes('out of date'));
 assert.equal(nodes['modern-admin-sun-alt'].textContent,'1 deg');
 poll();respond(3,null,{redirected:true});await tick();assert(nodes['astropanel-status'].textContent.includes('Session expired'));
 poll();respond(4,{...data,satellite_list:[],sun_alt:null});await tick();
 assert.equal(nodes['modern-admin-sun-alt'].textContent,'Unavailable');
 assert.equal(nodes['modern-admin-satellite-rows'].children[0].firstChild.textContent,'No satellite data available.');
 poll();events.pagehide();assert(pending[5].options.signal.aborted);
 console.log('Astropanel controller: all detail fields, 20 satellites, literal text, unavailable/stale/session states, refresh and polling: PASS');
})().catch(error=>{console.error(error);process.exitCode=1;});
