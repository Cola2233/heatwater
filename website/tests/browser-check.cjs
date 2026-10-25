/* Optional browser QA: npm install playwright, then start the static preview. */
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||"playwright");
const assert=require("node:assert/strict");
const path=require("node:path");
const fs=require("node:fs");
(async()=>{
 const browser=await chromium.launch({headless:true,...(process.platform==="win32"?{channel:"msedge"}:{})});
 try{
  const singleFile=process.env.HEATWATER_SINGLE_FILE==="1";
  const page=await browser.newPage({viewport:{width:1440,height:1050},offline:singleFile});
  const requests=[];
  page.on("request",request=>requests.push(request.url()));
  const errors=[];
  page.on("pageerror",e=>errors.push(e.message));
  const url=process.env.HEATWATER_URL||"http://127.0.0.1:8765/local.html";
  await page.goto(url,{waitUntil:"networkidle"});
  await page.waitForFunction(()=>document.querySelector("#metric-area").textContent!=="—");
  assert.equal(await page.locator("#error-message").isVisible(),false);
  const area=await page.locator("#metric-area").textContent();
  const initialBoth=await page.locator("#metric-both").textContent();
  const initialScore=await page.locator("#metric-score").textContent();
  await page.locator('[data-layer="compound"]').click();
  assert.equal(await page.locator('[data-layer="compound"]').getAttribute("aria-pressed"),"true");
  await page.locator("#heat-weight").evaluate(el=>{el.value="70";el.dispatchEvent(new Event("input",{bubbles:true}));});
  await page.waitForFunction(()=>document.querySelector("#weight-output").textContent==="70%");
  assert.equal(await page.locator("#metric-both").textContent(),initialBoth);
  assert.notEqual(await page.locator("#metric-score").textContent(),initialScore);
  await page.locator("#threshold").evaluate(el=>{el.value="80";el.dispatchEvent(new Event("input",{bubbles:true}));});
  await page.waitForFunction(()=>document.querySelector("#threshold-output").textContent==="0.80");
  assert.notEqual(await page.locator("#metric-both").textContent(),initialBoth);
  await page.locator("#reset-parameters").click();
  assert.equal(await page.locator("#metric-both").textContent(),initialBoth);
  const downloaded=page.waitForEvent("download");
  await page.locator("#download-csv").click();
  assert.ok((await downloaded).suggestedFilename().endsWith(".csv"));
  const settingsDownload=page.waitForEvent("download");
  await page.locator("#download-settings").click();
  assert.ok((await settingsDownload).suggestedFilename().endsWith(".json"));
  const mapDownload=page.waitForEvent("download");
  await page.locator("#download-map").click();
  assert.ok((await mapDownload).suggestedFilename().endsWith(".png"));
  const beforeZoom=await page.locator("#map").evaluate(el=>el.toDataURL());
  await page.locator("#zoom-in").click();
  assert.notEqual(await page.locator("#map").evaluate(el=>el.toDataURL()),beforeZoom);
  await page.locator("#zoom-reset").click();
  const out=path.resolve("artifacts/frontend");
  fs.mkdirSync(out,{recursive:true});
  await page.locator('[data-layer="zones"]').click();
  await page.evaluate(()=>window.scrollTo(0,0));
  await page.screenshot({path:path.join(out,"desktop.png"),fullPage:true});
  await page.setViewportSize({width:390,height:844});
  await page.evaluate(()=>window.scrollTo(0,0));
  if(await page.locator("#nav-toggle").count()){
   await page.locator("#nav-toggle").click();
   assert.equal(await page.locator("#nav-toggle").getAttribute("aria-expanded"),"true");
   await page.locator("#main-nav a[href='#method']").click();
   assert.equal(await page.locator("#nav-toggle").getAttribute("aria-expanded"),"false");
   await page.evaluate(()=>window.scrollTo(0,0));
  }
  assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);
  await page.screenshot({path:path.join(out,"mobile.png"),fullPage:true});
  const options=await page.locator("#dataset option").count();
  if(options>1){
   await page.locator("#dataset").selectOption("demo");
   assert.ok((await page.locator("#dataset-tag").textContent()).includes("模拟"));
   assert.equal(await page.locator("#metric-area").textContent(),"1.68");
  }
  if(!singleFile){
   await page.goto(new URL("index.html",url).href,{waitUntil:"networkidle"});
   assert.ok((await page.locator("#dataset-tag").textContent()).includes("模拟"));
  }else{
   assert.equal(requests.filter(url=>url.startsWith("http")).length,0);
   assert.equal(requests.filter(url=>url.startsWith("file:")).length,1);
  }
  assert.deepEqual(errors,[]);
  console.log(JSON.stringify({area,initialBoth,initialScore,errors,desktop:true,mobile:true,sliders:true,exports:true,singleFile,offline:singleFile}));
 } finally {await browser.close();}
})().catch(error=>{console.error(error);process.exitCode=1;});
