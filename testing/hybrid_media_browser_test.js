/* Regression for media filtering and FITS lightbox behavior. No browser claim. */
const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const source = fs.readFileSync('indi_allsky/flask/templates/modern_admin/media_list.html','utf8');
const start = source.indexOf("document.addEventListener('click', (event) => {");
const end = source.indexOf("document.addEventListener('keydown'", start);
for (const gallery of [false,true]) {
    let callback, prevented=false, applied=false;
    const filter = {href:'/media/fits?profile_id=1'};
    const context = {document:{addEventListener:(name,fn)=>callback=fn},
        modernAdminGalleryGrid:gallery?{}:null,
        modernAdminApplyGalleryFilter:()=>applied=true,
        modernAdminOpenLightbox:()=>assert.fail('Filter must not open lightbox')};
    vm.runInNewContext(source.slice(start,end),context);
    const event={target:{classList:{contains:()=>false},closest:selector=>selector==='.modern-admin-gallery-filter'?filter:null},
        preventDefault:()=>prevented=true,stopPropagation:()=>{}};
    callback(event);
    assert.equal(prevented,gallery,'Only the AJAX gallery may intercept the native camera link');
    assert.equal(applied,gallery);
    prevented=false; applied=false;
    callback({...event,ctrlKey:true});
    assert.equal(prevented,false,'Modified click must preserve browser navigation');
    assert.equal(applied,false);
}
const display=source.slice(source.indexOf('function modernAdminLightboxDisplayUrl'),source.indexOf('function modernAdminOpenLightbox'));
const context={modernAdminMediaKind:'fits'};
vm.createContext(context); vm.runInContext(display,context);
assert.equal(context.modernAdminLightboxDisplayUrl({preview_url:null,url:'/original.fit'}),null,
    'A FITS original must never be used as an img source when a preview is unavailable');
assert.equal(context.modernAdminLightboxDisplayUrl({preview_url:'/preview.jpg',url:'/original.fit'}),'/preview.jpg');
context.modernAdminMediaKind='image';
assert.equal(context.modernAdminLightboxDisplayUrl({preview_url:'/thumb.jpg',url:'/original.jpg'}),'/original.jpg');
console.log('Hybrid media camera navigation and source preview behavior: PASS');
