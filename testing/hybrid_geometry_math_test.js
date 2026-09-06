const assert=require('node:assert/strict');
const {overlay}=require('../indi_allsky/flask/static/modern_admin/image-geometry.js');
let count=0;
for(const width of [64,640,1920,4056]) for(const height of [48,480,1080,3040]) for(const angle of [-180,-135,-90,-45,0,30,89.9,90,135,180]) for(const offsets of [[0,0],[10,-20],[-100,300]]) {
 const [x,y]=offsets,g=overlay(width,height,300,x,y,angle);
 assert.equal(g.x,width/2+x);assert.equal(g.y,height/2-y);assert.equal(g.radius,150);
 assert(g.line.every(Number.isFinite),'Keogram must remain finite at ±90°');
 const [x1,y1,x2,y2]=g.line;
 assert(Math.abs((x1+x2)/2-g.x)<1e-9);assert(Math.abs((y1+y2)/2-g.y)<1e-9);
 if(Math.abs(Math.cos(angle*Math.PI/180))>1e-8) {
  // Same legacy line orientation, without tan(90°)'s unbounded endpoints.
  assert(Math.abs((x1-g.x)+(y1-g.y)*Math.tan(angle*Math.PI/180))<1e-6);
 }
 count++;
}
console.log('Image geometry circle/offset parity and finite keogram lines: PASS ('+count+' cases)');
