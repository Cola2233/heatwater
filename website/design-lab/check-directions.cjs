const {chromium}=require(process.env.PLAYWRIGHT_MODULE||"playwright");
const assert=require("node:assert/strict");
const path=require("node:path");
const {pathToFileURL}=require("node:url");
const fs=require("node:fs");
(async()=>{
 const browser=await chromium.launch({headless:true,...(process.platform==="win32"?{channel:"msedge"}:{})});
 const rows=[];
 try{
  for(let i=1;i<=3;i++){
   const dir=path.resolve("design-demos/2026-11-02"),file=path.join(dir,"dir-"+i+".html");
   const p=await browser.newPage({viewport:{width:1440,height:900},offline:true});
   const errors=[],requests=[];
   p.on("pageerror",e=>errors.push(e.message));p.on("request",r=>requests.push(r.url()));
   await p.goto(pathToFileURL(file).href,{waitUntil:"networkidle"});
   await p.waitForFunction(()=>document.querySelector("#metric-area").textContent!=="—");
   assert.equal(await p.locator("#error-message").isVisible(),false);
   assert.equal(await p.locator("#metric-area").textContent(),"392.77");
   assert.equal(await p.locator("#metric-both").textContent(),"52.87");
   const original=await p.locator("#metric-score").textContent();
   await p.locator("#heat-weight").evaluate(el=>{el.value=70;el.dispatchEvent(new Event("input",{bubbles:true}));});
   await p.waitForFunction(()=>document.querySelector("#weight-output").textContent==="70%");
   assert.notEqual(await p.locator("#metric-score").textContent(),original);
   assert.equal(await p.locator("#metric-both").textContent(),"52.87");
   await p.locator("#reset-parameters").click();
   await p.locator("[data-layer=zones]").click();
   assert.equal(await p.locator("[data-layer=zones]").getAttribute("aria-pressed"),"true");
   await p.locator("[data-layer=compound]").click();
   const dl=p.waitForEvent("download");await p.locator("#download-csv").click();assert.ok((await dl).suggestedFilename().endsWith(".csv"));
   await p.evaluate(()=>scrollTo(0,0));
   await p.screenshot({path:path.join(dir,"dir-"+i+".png"),fullPage:true});
   await p.screenshot({path:path.join(dir,"dir-"+i+"-screen.png")});
   assert.equal(await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);
   const desktopFonts=await p.evaluate(()=>[...document.querySelectorAll("body *")].filter(e=>[...e.childNodes].some(n=>n.nodeType===3&&n.textContent.trim())&&e.getBoundingClientRect().height>0).filter(e=>parseFloat(getComputedStyle(e).fontSize)<12).slice(0,10).map(e=>({tag:e.tagName,text:e.textContent.slice(0,40),size:getComputedStyle(e).fontSize})));
   const lintFile=path.resolve("artifacts/design-references/huashu-design/scripts/design_lint.py");
   const collector=fs.readFileSync(lintFile,"utf8").match(/COLLECT_JS = r"""([\s\S]*?)"""/)[1];
   const designFacts=await p.evaluate("("+collector+")()");
   await p.setViewportSize({width:375,height:812});
   assert.equal(await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);
   await p.evaluate(()=>scrollTo(0,0));
   await p.screenshot({path:path.join(dir,"dir-"+i+"-mobile.png"),fullPage:true});
   assert.deepEqual(errors,[]);assert.equal(requests.filter(x=>x.startsWith("http")).length,0);
   rows.push({direction:i,errors,offline:true,sliders:true,export:true,desktopFonts,sourceRequests:requests.length,designCheck:{small:designFacts.small,lowContrast:designFacts.lowContrast,bodySmall:designFacts.bodySmall,arrows:designFacts.arrows,dots:designFacts.dots}});
   await p.close();
  }
  fs.writeFileSync("design-demos/2026-11-02/browser-results.json",JSON.stringify(rows,null,2));
  console.log(JSON.stringify(rows));
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1});
