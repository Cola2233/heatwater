const {chromium}=require('playwright'),assert=require('node:assert/strict'),path=require('node:path'),fs=require('node:fs'),{pathToFileURL}=require('node:url');
(async()=>{
 const browser=await chromium.launch({headless:true,channel:process.platform==='win32'?'msedge':undefined});
 try{
  for(const file of ['website/index.html',...(process.env.HEATWATER_FEEDBACK_ENTRY?[process.env.HEATWATER_FEEDBACK_ENTRY]:[])]){
   const p=await browser.newPage({viewport:{width:1440,height:1100},offline:true}),errors=[];
   p.on('pageerror',e=>errors.push(e.message));await p.goto(pathToFileURL(path.resolve(file)).href);
   await p.waitForFunction(()=>document.querySelector('#metric-area').textContent!=='—');
   const canvas=p.locator('#map'),image=()=>canvas.evaluate(e=>e.toDataURL());
   await p.locator('[data-layer=water]').click();const before=await image();
   await p.locator('#heat-weight').fill('70');await p.waitForFunction(()=>document.querySelector('#weight-output').textContent==='70%');
   assert.equal(await p.locator('[data-layer=compound]').getAttribute('aria-pressed'),'true');
   assert.notEqual(await image(),before);assert.equal(await p.locator('#map-change-legend').isVisible(),true);
   const changeImage=await image();await p.locator('#compare-map').click();
   assert.equal(await p.locator('#compare-map').getAttribute('aria-pressed'),'true');assert.notEqual(await image(),changeImage);
   await p.locator('#compare-map').click();assert.equal(await image(),changeImage);
   await p.locator('#threshold').fill('80');await p.waitForFunction(()=>document.querySelector('#threshold-output').textContent==='0.80');
   assert.equal(await p.locator('[data-layer=zones]').getAttribute('aria-pressed'),'true');assert.notEqual(await image(),changeImage);
   await p.locator('#follow-map-parameters').uncheck();await p.locator('[data-layer=water]').click();
   const water=await image();await p.locator('#heat-weight').fill('30');await p.waitForFunction(()=>document.querySelector('#weight-output').textContent==='30%');
   assert.equal(await p.locator('[data-layer=water]').getAttribute('aria-pressed'),'true');assert.notEqual(await image(),water);
   await p.locator('#show-map-change').uncheck();assert.equal(await image(),water);
   await p.locator('#show-map-change').check();
   const out=path.resolve('artifacts/frontend/feedback');fs.mkdirSync(out,{recursive:true});
   await p.locator('#map').screenshot({path:path.join(out,path.basename(file)+'-weight.png')});
   await p.locator('#view-raster').click();const raster=await image();
   await p.locator('#threshold').fill('60');await p.waitForFunction(()=>document.querySelector('#threshold-output').textContent==='0.60');assert.notEqual(await image(),raster);
   const download=p.waitForEvent('download');await p.locator('#download-map').click();assert.equal(await (await download).failure(),null);
   await p.locator('#view-blocks').click();await canvas.scrollIntoViewIfNeeded();
   const point=await p.evaluate(()=>{const r=document.querySelector('#map').getBoundingClientRect();return {x:r.x+r.width/2,y:r.y+r.height/2-5};});
   await p.mouse.move(point.x,point.y);
   assert.equal(await p.locator('#map-hover-card').isVisible(),true);
   assert.ok((await p.locator('#map-hover-values').textContent()).includes('复合'));
   await p.setViewportSize({width:375,height:812});assert.equal(await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);
   assert.deepEqual(errors,[]);console.log(JSON.stringify({file,weightChangesMap:true,thresholdChangesMap:true,compare:true,rawWaterPreserved:true,rasterFeedback:true,hover:true,export:true,mobile:true,errors}));await p.close();
  }
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
