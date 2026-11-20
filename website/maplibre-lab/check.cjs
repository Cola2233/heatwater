const {chromium}=require('playwright'),assert=require('node:assert/strict'),path=require('node:path'),fs=require('node:fs'),{pathToFileURL}=require('node:url');
(async()=>{
 const browser=await chromium.launch({headless:true,channel:process.platform==='win32'?'msedge':undefined,args:['--use-angle=swiftshader','--enable-unsafe-swiftshader']});
 try{
  const page=await browser.newPage({viewport:{width:1440,height:1000},offline:true});
  const errors=[],requests=[];page.on('pageerror',e=>errors.push(e.message));page.on('request',r=>requests.push(r.url()));
  const start=Date.now();await page.goto(pathToFileURL(path.resolve(process.env.HEATWATER_MAPLIBRE_ENTRY||'artifacts/opensource-pilot/changchun-maplibre.html')).href);
  await page.waitForFunction(()=>window.heatwaterPilot?.ready||!document.querySelector('#map-error').hidden,{},{timeout:60000});
  assert.equal(await page.locator('#map-error').isVisible(),false,await page.locator('#map-error').textContent());
  const planning=await page.evaluate(()=>PILOT.raw.meta.id==='changchun-planning');
  const baseline=planning?'43.94':'52.87',validPixels=planning?325978:436411;
  const loadMs=Date.now()-start;assert.equal(await page.locator('#both').textContent(),baseline);
  assert.equal(await page.evaluate(()=>heatwaterPilot.rows.length),planning?51:528);
  if(planning){
   assert.match(await page.locator('#domain-note').textContent(),/真实四环/);
   assert.equal(await page.evaluate(()=>PILOT.raw.map_context.roads.features.length),890);
   assert.ok(await page.evaluate(()=>heatwaterPilot.map.querySourceFeatures('context-roads').length>0));
   await page.locator('#context-toggle').uncheck();
   assert.equal(await page.evaluate(()=>heatwaterPilot.map.getLayoutProperty('context-roads','visibility')),'none');
   await page.locator('#context-toggle').check();
  }
  const target=await page.evaluate(()=>{
   const map=heatwaterPilot.map,c=map.getCanvas(),rect=c.getBoundingClientRect();
   for(let y=rect.height*.3;y<rect.height*.8;y+=35)for(let x=rect.width*.3;x<rect.width*.8;x+=35){
    const f=map.queryRenderedFeatures([x,y],{layers:['unit-fill']})[0];if(f)return {x:rect.x+x,y:rect.y+y,id:f.id};
   }return null;
  });assert.ok(target);
  await page.mouse.move(target.x,target.y);await page.waitForSelector('.maplibregl-popup-content');
  await page.mouse.click(target.x,target.y);assert.equal(await page.evaluate(()=>heatwaterPilot.selected),target.id);
  await page.mouse.move(1400,30);
  const before=await page.locator('#map canvas').evaluate(c=>c.toDataURL());
  await page.locator('#weight').fill('70');await page.waitForFunction(()=>document.querySelector('#weight-value').textContent==='70%');
  await page.waitForFunction(()=>heatwaterPilot.renderedRevision===heatwaterPilot.revision);
  assert.notEqual(await page.locator('#map canvas').evaluate(c=>c.toDataURL()),before);
  await page.locator('#compare').click();assert.equal(await page.evaluate(()=>heatwaterPilot.comparing),true);
  await page.locator('#compare').click();
  await page.locator('#threshold').fill('80');await page.waitForFunction(()=>document.querySelector('#threshold-value').textContent==='0.80');
  await page.locator('#reset').click();assert.equal(await page.locator('#both').textContent(),baseline);
  if(!planning){await page.locator('#scale').selectOption('detail');await page.waitForFunction(()=>heatwaterPilot.rows.length===2304);}
  assert.equal(await page.evaluate(()=>heatwaterPilot.rows.reduce((s,r)=>s+r.valid_pixels,0)),validPixels);
  const download=page.waitForEvent('download');await page.locator('#export').click();assert.equal(await (await download).failure(),null);
  if(!planning)await page.locator('#scale').selectOption('overview');await page.locator('#metric').selectOption('water_mean');
  await page.waitForFunction(()=>heatwaterPilot.renderedRevision===heatwaterPilot.revision);
  await page.screenshot({path:path.resolve('artifacts/opensource-pilot/maplibre-desktop.png'),fullPage:true});
  await page.setViewportSize({width:375,height:812});assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);
  await page.screenshot({path:path.resolve('artifacts/opensource-pilot/maplibre-mobile.png'),fullPage:true});
  assert.deepEqual(errors,[]);assert.equal(requests.some(u=>/^https?:/.test(u)),false);
  const result={maplibre:await page.evaluate(()=>PILOT.version),loadMs,offline:true,httpRequests:0,hover:true,click:true,weight:true,threshold:true,compare:true,scales:planning?[51]:[528,2304],validPixels,download:true,mobile:true,errors};
  fs.writeFileSync('artifacts/opensource-pilot/maplibre-check.json',JSON.stringify(result,null,2));console.log(JSON.stringify(result));
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1});
