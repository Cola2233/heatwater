/* Small startup comparison, not an FPS or general performance benchmark. */
const {chromium}=require('playwright'),fs=require('node:fs'),path=require('node:path'),{pathToFileURL}=require('node:url');
(async()=>{const browser=await chromium.launch({headless:true,channel:process.platform==='win32'?'msedge':undefined,args:['--use-angle=swiftshader','--enable-unsafe-swiftshader']});
const results={canvas:[],maplibre:[]};try{
 for(const order of [['canvas','maplibre'],['maplibre','canvas'],['canvas','maplibre']])for(const name of order){
  const page=await browser.newPage({viewport:{width:1440,height:1000},offline:true});
  const file=path.resolve(name==='canvas'?'../热水共治_长春交互地图_单文件.html':'artifacts/opensource-pilot/changchun-maplibre.html');const start=Date.now();
  await page.goto(pathToFileURL(file).href);
  if(name==='maplibre')await page.waitForFunction(()=>window.heatwaterPilot?.ready);else await page.waitForFunction(()=>document.querySelector('#metric-area')?.textContent==='392.77');
  await page.evaluate(()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve))));
  results[name].push(Date.now()-start);await page.close();
 }
 const output={runsMs:results,medianMs:Object.fromEntries(Object.entries(results).map(([key,values])=>[key,[...values].sort((a,b)=>a-b)[1]])),
 bytes:{canvas:fs.statSync('../热水共治_长春交互地图_单文件.html').size,maplibre:fs.statSync('artifacts/opensource-pilot/changchun-maplibre.html').size},
 caveat:'Same headless Edge process, 1440x1000, offline, SwiftShader. Readiness differs by engine. Approximate startup only; not evidence about interactive FPS.'};
 fs.writeFileSync('artifacts/opensource-pilot/startup-comparison.json',JSON.stringify(output,null,2));console.log(JSON.stringify(output));
}finally{await browser.close();}})().catch(e=>{console.error(e);process.exitCode=1;});
