const fs=require('fs'),vm=require('vm'),assert=require('assert');
const image={complete:true,naturalWidth:0,hidden:false,addEventListener(event,fn){this[event]=fn;}},status={hidden:true};
const card={querySelector:selector=>selector==='img'?image:status};
vm.runInNewContext(fs.readFileSync('indi_allsky/flask/static/modern_admin/now-frames.js','utf8'),{document:{querySelectorAll:()=>[card,{querySelector:()=>null}]}});
assert(image.hidden && !status.hidden);
image.load();assert(!image.hidden && status.hidden);
image.error();assert(image.hidden && !status.hidden);
console.log('Now frames: cached failure, load recovery, error and missing image: PASS');
