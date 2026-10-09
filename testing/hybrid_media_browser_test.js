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

function galleryFunction(name) {
    const start = source.indexOf('function ' + name + '(');
    assert(start >= 0, name);
    const asyncPrefix = source.slice(start - 6, start) === 'async ' ? 'async ' : '';
    return asyncPrefix + source.slice(start, source.indexOf('\n}', start) + 2);
}

// Advancing a lightbox must change the exposure's detail/original link, and
// hide and clear it for a FITS entry that has no image detail destination.
{
    const element = () => ({setAttribute(k,v){this[k]=v;},removeAttribute(k){delete this[k];}});
    const details = element();
    const items = [{url:'/processed-1.jpg',detail_url:'/images/1?camera_id=1'},
        {url:'/processed-2.jpg',detail_url:'/images/2?camera_id=2'}, {url:'/source.fit'}];
    const c = {modernAdminLightboxItem:i=>items[i],modernAdminLightboxDisplayUrl:i=>i.url,
        modernAdminLightboxDetails:details,modernAdminLightboxImage:element(),
        modernAdminLightboxStatus:element(),modernAdminLightboxTitle:element(),
        modernAdminLightboxDownload:element(),
        modernAdminLightbox:{...element(),getAttribute:()=> 'true',querySelector:()=>({focus(){}})},
        document:{activeElement:{},documentElement:{classList:{add(){}}},body:{classList:{add(){}}}}};
    vm.createContext(c);vm.runInContext(galleryFunction('modernAdminOpenLightbox'),c);
    c.modernAdminOpenLightbox(0);assert.equal(details.href,items[0].detail_url);assert.equal(details.hidden,false);
    c.modernAdminOpenLightbox(1);assert.equal(details.href,items[1].detail_url);
    c.modernAdminOpenLightbox(2);assert.equal(details.hidden,true);assert.equal(details.href,undefined);
}

async function galleryStateChecks() {
    const count = {}, label = {}, requests = [], rendered = [];
    const filters = ['ASI678MC', 'IMX708 Wide'].map((textContent, i) => {
        const link = {textContent, active:i === 0, attrs:{},
            href:'https://fixture/gallery?camera_id=' + (i ? 1 : 2),
            dataset:{galleryFilterCamera:String(i ? 1 : 2)},
            setAttribute(name, value) { this.attrs[name] = value; }};
        link.classList = {toggle(_name, active) { link.active = active; }};
        return link;
    });
    const c = {
        URL, Set, modernAdminMediaItems:[{id:1}],
        modernAdminGallerySeenIds:new Set(['1']), modernAdminGalleryNextCursor:'1',
        modernAdminGalleryHasMore:true, modernAdminGalleryLoadingPage:false,
        modernAdminGalleryGrid:{dataset:{galleryPageUrl:'/gallery/page',galleryLimit:'72',galleryCameraId:'2'},
            insertAdjacentHTML(_where, html) { rendered.push(html); }},
        modernAdminGalleryLoadMore:{}, modernAdminGalleryLoading:{},
        modernAdminGalleryEnd:{}, modernAdminGalleryError:{hidden:true},
        modernAdminGalleryCardHtml:(item)=>String(item.id),
        modernAdminUpdateSelection:()=>{},
        window:{location:{href:'https://fixture/gallery'},console:{error:()=>{}},history:{pushState:()=>{}}},
        document:{getElementById:id=>id.endsWith('loaded-count')?count:id.endsWith('filter-label')?label:null,
            querySelector:()=>filters.find(f=>f.active),querySelectorAll:()=>filters},
        fetch:async url=>{ requests.push(url); return {ok:true,json:async()=>({images:[{id:1},{id:2}],next_cursor:'2',has_more:true})}; },
    };
    vm.createContext(c);
    for (const name of ['modernAdminUpdateGallerySummary','modernAdminGallerySetLoading',
        'modernAdminGallerySetEndReached','modernAdminGalleryApplyFilterParams',
        'modernAdminLoadOlderGalleryImages','modernAdminApplyGalleryFilter']) {
        vm.runInContext(galleryFunction(name), c);
    }
    await c.modernAdminLoadOlderGalleryImages();
    assert.equal(count.textContent,'2');
    assert.deepEqual(rendered,['2'],'Duplicate records must not inflate the count');
    assert.equal(new URL(requests[0]).searchParams.get('camera_id'),'2');
    c.fetch = async()=>{ throw new Error('private provider failure'); };
    await c.modernAdminLoadOlderGalleryImages();
    assert.equal(count.textContent,'2');
    assert.equal(c.modernAdminGalleryError.hidden,false);
    assert.equal(c.modernAdminGalleryError.textContent,'Could not load older images. Try Load more again.');
    assert.equal(c.modernAdminGalleryLoadMore.disabled,false);
    let finish;
    c.fetch = ()=>new Promise(resolve=>{finish=resolve;});
    const pending = c.modernAdminApplyGalleryFilter(filters[1]);
    assert.equal(count.textContent,'0','Cleared grid must not report old records while loading');
    assert.equal(label.textContent,'IMX708 Wide');
    assert.equal(filters[0].attrs['aria-pressed'],'false');
    assert.equal(filters[1].attrs['aria-pressed'],'true');
    assert.equal(c.modernAdminGalleryError.hidden,true,'Retry clears the old error');
    finish({ok:true,json:async()=>({images:[{id:3}],has_more:false})});
    await pending;
    assert.equal(count.textContent,'1');
    assert.equal(c.modernAdminGalleryLoadMore.hidden,true);
    assert.equal(c.modernAdminGalleryLoadingPage,false);
    console.log('Gallery loaded count, deduplication, accessible camera state and failure/retry feedback: PASS');
}
galleryStateChecks().catch(error=>{console.error(error);process.exitCode=1;});
