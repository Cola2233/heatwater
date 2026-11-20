const {chromium}=require('playwright'),assert=require('node:assert/strict'),path=require('node:path'),fs=require('node:fs'),{pathToFileURL}=require('node:url');
(async()=>{
 const browser=await chromium.launch({headless:true,channel:process.platform==='win32'?'msedge':undefined,args:['--use-angle=swiftshader','--enable-unsafe-swiftshader']});
 try{
  const page=await browser.newPage({viewport:{width:1440,height:1000},offline:true}),errors=[],requests=[];
  page.on('pageerror',e=>errors.push(e.message));page.on('request',r=>{if(/^https?:/.test(r.url()))requests.push(r.url());});
  const entry=process.env.HEATWATER_MAPLIBRE_ENTRY||'artifacts/opensource-pilot/changchun-maplibre.html',prefix=process.env.HEATWATER_RESEARCH_REPORT_PREFIX||'research';
  await page.goto(pathToFileURL(path.resolve(entry)).href);
  await page.waitForFunction(()=>window.heatwaterPilot?.ready,{},{timeout:60000});
  // A real gesture during the background sweep must still update the current result.
  await page.locator('#weight').fill('70');
  await page.waitForFunction(()=>document.querySelector('#weight-value').textContent==='70%');
  await page.locator('#reset').click();
  await page.waitForFunction(()=>window.HeatwaterResearch?.output,{},{timeout:120000});
  const summary=await page.evaluate(()=>{
   const out=HeatwaterResearch.output,rows=heatwaterPilot.rows,j=out.settings.findIndex(x=>x.heatWeight===.55&&x.threshold===.67);
   const mismatch=out.rows.filter(r=>Math.abs((r.cases[j].share??0)-(rows.find(x=>x.id===r.id).high_exposure_share??0))>1e-12);
   return {cases:out.settings.length,units:out.rows.length,eligible:out.rows.filter(r=>r.eligible).length,stable:out.rows.filter(r=>r.frequency>=.8).length,
    selected:rows.filter(r=>HeatwaterStability.supported(r)&&r.high_exposure_share>=.2).length,mismatch:mismatch.length};
  });assert.equal(summary.cases,72);assert.equal(summary.mismatch,0);assert.ok(summary.eligible>0);
  await page.locator('#shortlist-rows button').first().click();
  await page.waitForFunction(()=>heatwaterPilot.selected!==null);
  assert.match(await page.locator('#selection').textContent(),/全域均值/);assert.match(await page.locator('#selection').textContent(),/入选频率/);
  await page.locator('#selection summary').click();assert.equal(await page.locator('#selection .scenario-scroll tr').count(),73);
  await page.locator('#show-stability').click();assert.equal(await page.locator('#metric').inputValue(),'selection_frequency');
  await page.locator('#shortlist-filter').selectOption('stable');
  const listCount=await page.evaluate(()=>heatwaterPilot.rows.filter(HeatwaterResearch.matches).length);assert.equal(listCount,summary.stable);
  await page.waitForFunction(()=>heatwaterPilot.renderedRevision===heatwaterPilot.revision);
  // Filter must also suppress map fills, not merely change the list.
  assert.equal(await page.evaluate(()=>heatwaterPilot.rows.filter(r=>heatwaterPilot.map.getFeatureState({source:'units',id:r.id}).valid).length),summary.stable);
  let exportedCount=summary.stable;
  if(!summary.stable){assert.equal(await page.locator('#export-shortlist').isDisabled(),true);await page.locator('#shortlist-filter').selectOption('all');exportedCount=await page.evaluate(()=>heatwaterPilot.rows.filter(HeatwaterResearch.matches).length);}
  const [download]=await Promise.all([page.waitForEvent('download'),page.locator('#export-shortlist').click()]);
  const csv=fs.readFileSync(await download.path(),'utf8');assert.match(csv,/selection_frequency/);assert.match(csv,/parameter_selection_frequency_not_event_probability/);
  assert.equal(csv.trim().split(/\r?\n/).length,exportedCount+1);
  await page.locator('#shortlist-filter').selectOption('all');
  await page.locator('#shortlist-search').fill('no-such-unit');assert.match(await page.locator('#shortlist-rows').textContent(),/没有匹配/);
  await page.locator('#shortlist-search').fill('');
  await page.locator('#weight').fill('65');await page.waitForFunction(()=>document.querySelector('#weight-value').textContent==='65%');
  assert.equal(await page.locator('#metric').inputValue(),'compound_mean');
  await page.locator('#compare').click();assert.match(await page.locator('#selection').textContent(),/始终解释当前参数/);
  await page.locator('#compare').click();await page.locator('#reset').click();
  await page.locator('#show-stability').click();
  await page.locator('#fit').click();await page.evaluate(()=>scrollTo({top:0,behavior:'instant'}));
  await page.waitForFunction(()=>heatwaterPilot.map.loaded()&&!heatwaterPilot.map.isMoving());
  await page.screenshot({path:'artifacts/opensource-pilot/'+prefix+'-desktop.png',fullPage:true});
  const options=await page.locator('#scale option').count();
  if(options>1){await page.locator('#scale').selectOption('detail');await page.waitForFunction(()=>HeatwaterResearch.output?.rows.length===2304,{},{timeout:120000});
   assert.equal(await page.evaluate(()=>heatwaterPilot.rows.reduce((s,r)=>s+r.valid_pixels,0)),436411);
   await page.locator('#scale').selectOption('overview');await page.waitForFunction(()=>HeatwaterResearch.output?.rows.length===528);
  }
  await page.setViewportSize({width:375,height:900});await page.locator('#show-stability').click();
  assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);
  await page.evaluate(()=>scrollTo({top:0,behavior:'instant'}));
  await page.screenshot({path:'artifacts/opensource-pilot/'+prefix+'-mobile.png',fullPage:true});
  assert.deepEqual(errors,[]);assert.deepEqual(requests,[]);
  const report={...summary,offline:true,httpRequests:requests.length,backgroundResponsive:true,explanation:true,scenarioEvidence:true,filterMap:true,csv:true,mobile:true,errors};
  fs.writeFileSync('artifacts/opensource-pilot/'+prefix+'-check.json',JSON.stringify(report,null,2));console.log(JSON.stringify(report));
 }finally{await browser.close();}
})().catch(error=>{console.error(error);process.exitCode=1;});
