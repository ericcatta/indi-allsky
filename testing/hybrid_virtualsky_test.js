const assert = require('node:assert/strict');
const {overlayOptions} = require('../indi_allsky/flask/static/modern_admin/virtualsky.js');
const values = {AZIMUTH_ANGLE:30, LATITUDE_OFFSET:2, LONGITUDE_OFFSET:-3,
    IMAGE_CIRCLE_DIAMETER:800, OFFSET_X:20, OFFSET_Y:10, MAGNITUDE:6,
    CONSTELLATIONS:true, CONSTELLATIONLABELS:false, SHOWSTARS:true,
    SHOWSTARLABELS:false, SHOWPLANETS:true, SHOWPLANETLABELS:true};
const frame = {width:1000,height:600,timestamp:1700000000};
const config = {latitude:46,longitude:8,timeOffset:3600};
const result = overlayOptions(values,frame,500,config);
assert.equal(result.width,400); assert.equal(result.left,60); assert.equal(result.top,-55);
assert.equal(result.az,210); assert.equal(result.latitude,48); assert.equal(result.longitude,5);
assert.equal(result.clock.getTime(),(frame.timestamp-3600)*1000);
assert.equal(result.constellations,true); assert.equal(result.showstarlabels,false);
const half = overlayOptions(values,frame,250,config);
assert.equal(half.left,result.left/2); assert.equal(half.top,result.top/2);
for (const [key,value] of [['IMAGE_CIRCLE_DIAMETER',0],['MAGNITUDE',''],['OFFSET_X','invalid'],['LATITUDE_OFFSET',100]])
    assert.throws(() => overlayOptions({...values,[key]:value},frame,500,config));
assert.throws(() => overlayOptions(values,{...frame,width:0},500,config));
assert.throws(() => overlayOptions(values,{...frame,timestamp:'invalid'},500,config));
assert.throws(() => overlayOptions(values,frame,500,{...config,latitude:null}), /location is unavailable/);
for (const angle of [0,180,359.9]) {
    let oldAz = 180-angle;
    if (oldAz >= 360) oldAz -= 360; else if (oldAz < 0) oldAz += 360;
    oldAz = 360-oldAz;
    assert.equal(overlayOptions({...values,AZIMUTH_ANGLE:angle},frame,500,config).az%360,oldAz%360);
}
console.log('VirtualSky geometry, capture time, legacy azimuth parity, flags, resize and invalid values: PASS');
