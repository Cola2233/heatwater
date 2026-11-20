/* Public-source and standalone checks. No local rasters or design skill required. */
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||"playwright");
const assert=require("node:assert/strict");
const {pathToFileURL}=require("node:url");
const path=require("node:path");
const fs=require("node:fs");

async function check(browser,file,singleFile){
 const page=await browser.newPage({viewport:{width:1440,height:900},offline:true});
 const errors=[],requests=[];
 page.on("pageerror",e=>errors.push(e.message));
 page.on("request",r=>requests.push(r.url()));
 try{
  await page.goto(pathToFileURL(file).href);
  await page.waitForFunction(()=>document.querySelector("#metric-area").textContent!=="—");
  assert.equal(await page.locator("#error-message").isVisible(),false);
  assert.equal(await page.locator("#dataset option").count(),1);
  assert.equal(await page.locator("#dataset").inputValue(),"demo");
  assert.ok((await page.locator("#dataset-tag").textContent()).includes("模拟"));
  assert.equal(await page.locator("#metric-area").textContent(),"1.68");
  assert.equal(await page.locator("#metric-both").textContent(),"0.18");
  assert.deepEqual(await page.evaluate(()=>Object.keys(window.HEATWATER_DATASETS)),["demo"]);
  const baseline=await page.locator("#metric-score").textContent();
  await page.locator("#heat-weight").fill("70");
  await page.waitForFunction(()=>document.querySelector("#weight-output").textContent==="70%");
  assert.notEqual(await page.locator("#metric-score").textContent(),baseline);
  assert.equal(await page.locator("#metric-both").textContent(),"0.18");
  const thresholdLine=await page.locator("#bivariate path").last().getAttribute("d");
  await page.locator("#threshold").fill("80");
  await page.waitForFunction(()=>document.querySelector("#threshold-output").textContent==="0.80");
  assert.notEqual(await page.locator("#bivariate path").last().getAttribute("d"),thresholdLine);
  await page.locator("#reset-parameters").click();
  assert.equal(await page.locator("#metric-score").textContent(),baseline);
  for(const layer of ["zones","heat","water","compound","exposure","expansion"]){
   await page.locator(`[data-layer="${layer}"]`).click();
   assert.equal(await page.locator(`[data-layer="${layer}"]`).getAttribute("aria-pressed"),"true");
  }
  const map=page.locator("#map");
  const initial=await map.evaluate(e=>e.toDataURL());
  await page.locator("#zoom-in").click();
  assert.notEqual(await map.evaluate(e=>e.toDataURL()),initial);
  await page.locator("#zoom-reset").click();
  await page.locator("#focus-toggle").click();
  assert.equal(await page.locator(".story-copy").isVisible(),false);
  await page.locator("#focus-toggle").click();
  assert.equal(await page.locator(".story-copy").isVisible(),true);
  assert.equal(await page.locator("#exposure-bars .hist-bin").count(),5);
  assert.ok(await page.locator("#bivariate rect").count()>0);
  for(const [id,extension]of [["download-map",".png"],["download-csv",".csv"],["download-settings",".json"]]){
   const pending=page.waitForEvent("download");
   await page.locator("#"+id).click();
   const download=await pending;
   assert.ok(download.suggestedFilename().endsWith(extension));
   assert.equal(await download.failure(),null);
  }
  const out=path.resolve("artifacts/frontend/public");fs.mkdirSync(out,{recursive:true});
  for(const width of [1440,1024,768,375]){
   await page.setViewportSize({width,height:900});
   await page.evaluate(()=>scrollTo(0,0));
   assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);
   if(width===1440||width===375)await page.screenshot({path:path.join(out,(singleFile?"standalone":"source")+"-"+width+".png"),fullPage:true});
  }
  assert.deepEqual(errors,[]);
  assert.equal(requests.filter(u=>/^https?:/.test(u)).length,0);
  assert.equal(requests.some(u=>u.includes("local.js")),false);
  if(singleFile)assert.equal(requests.length,1);
  return {entry:path.basename(file),syntheticOnly:true,offline:true,sliders:true,charts:true,layers:6,exports:3,responsiveWidths:[1440,1024,768,375],errors};
 }finally{await page.close();}
}
(async()=>{
 const browser=await chromium.launch({headless:true,...(process.env.HEATWATER_BROWSER_CHANNEL?{channel:process.env.HEATWATER_BROWSER_CHANNEL}:{})});
 try{
  const results=[await check(browser,path.resolve("website/index.html"),false)];
  if(process.env.HEATWATER_PUBLIC_BUNDLE)results.push(await check(browser,path.resolve(process.env.HEATWATER_PUBLIC_BUNDLE),true));
  console.log(JSON.stringify(results));
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
