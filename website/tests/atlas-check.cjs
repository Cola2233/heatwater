/* Verify the approved atlas layout and the extra chart/focus interactions. */
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||"playwright");
const assert=require("node:assert/strict");
const fs=require("node:fs");
const path=require("node:path");
const {pathToFileURL}=require("node:url");
(async()=>{
 const browser=await chromium.launch({headless:true,...(process.platform==="win32"?{channel:"msedge"}:{})});
 try{
  const p=await browser.newPage({viewport:{width:1440,height:900},offline:true});
  const errors=[];p.on("pageerror",e=>errors.push(e.message));
  await p.goto(process.env.HEATWATER_URL||pathToFileURL(path.resolve("../热水共治_长春交互地图_单文件.html")).href);
  await p.waitForFunction(()=>document.querySelector("#metric-both").textContent==="52.87");
  assert.equal(await p.locator("#exposure-bars .hist-bin").count(),5);
  assert.ok(await p.locator("#bivariate rect").count()>0);
  const plot=await p.locator("#bivariate").innerHTML();
  await p.locator("#threshold").evaluate(e=>{e.value="80";e.dispatchEvent(new Event("input"));});
  await p.waitForFunction(()=>document.querySelector("#threshold-output").textContent==="0.80");
  assert.notEqual(await p.locator("#bivariate").innerHTML(),plot);
  await p.locator("#reset-parameters").click();
  await p.locator("#focus-toggle").click();
  assert.equal(await p.locator(".story-copy").isVisible(),false);
  assert.equal(await p.locator("#analysis").isVisible(),false);
  await p.locator("#focus-toggle").click();
  assert.equal(await p.locator(".story-copy").isVisible(),true);
  assert.equal(await p.locator("#analysis").isVisible(),true);
  const lintPath=path.resolve("artifacts/design-references/huashu-design/scripts/design_lint.py");
  const collector=fs.existsSync(lintPath)?fs.readFileSync(lintPath,"utf8").match(/COLLECT_JS = r"""([\s\S]*?)"""/)[1]:null;
  const checks=[];
  for(const width of [1440,1024,768,375]){
   await p.setViewportSize({width,height:width===375?812:900});
   await p.evaluate(()=>scrollTo(0,0));
   assert.equal(await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);
   if(collector){
    const facts=await p.evaluate("("+collector+")()");
    assert.deepEqual(facts.small,[]);assert.deepEqual(facts.lowContrast,[]);assert.deepEqual(facts.bodySmall,[]);
    checks.push({width,small:facts.small,lowContrast:facts.lowContrast,bodySmall:facts.bodySmall});
   }
   if(width===1440||width===375)await p.screenshot({path:path.resolve("artifacts/frontend/atlas-"+width+".png"),fullPage:true});
  }
  assert.deepEqual(errors,[]);
  console.log(JSON.stringify({charts:true,thresholdLinked:true,focusMode:true,checks,errors}));
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
