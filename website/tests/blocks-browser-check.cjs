const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const assert=require('node:assert/strict'),path=require('node:path'),fs=require('node:fs'),{pathToFileURL}=require('node:url');
(async()=>{
 const browser=await chromium.launch({headless:true,channel:process.env.HEATWATER_BROWSER_CHANNEL||(process.platform==='win32'?'msedge':undefined)});
 try{
  const p=await browser.newPage({viewport:{width:1440,height:1000},offline:true});
  const errors=[],requests=[];p.on('pageerror',e=>errors.push(e.message));p.on('request',r=>requests.push(r.url()));
  const file=process.env.HEATWATER_BLOCK_ENTRY||'website/index.html';
  await p.goto(pathToFileURL(path.resolve(file)).href);
  await p.waitForFunction(()=>document.querySelector('#metric-area').textContent!=='—');
  assert.equal(await p.locator('#error-message').isVisible(),false);
  assert.equal(await p.locator('#view-blocks').getAttribute('aria-pressed'),'true');
  const real=await p.locator('#dataset').inputValue()==='changchun';
  const valid=real?436411:1872;
  const profile=await p.evaluate(()=>{const raw=window.HEATWATER_DATASETS[document.querySelector('#dataset').value];return {count:raw.blocks.features.length,firstName:raw.blocks.features[0].name,scale:raw.blocks.diagnostics.scale||'detail'};});
  assert.ok((await p.locator('#block-overview').textContent()).includes(String(profile.count)));
  if(real){assert.equal(profile.scale,'overview');assert.equal(profile.count,528);}
  const out=path.resolve('artifacts/frontend/blocks');fs.mkdirSync(out,{recursive:true});
  await p.screenshot({path:path.join(out,real?'changchun-desktop.png':'demo-desktop.png'),fullPage:true});
  const target=await p.evaluate(()=>{
   const raw=window.HEATWATER_DATASETS[document.querySelector('#dataset').value],{width,height}=raw.meta;
   const bytes=Uint8Array.from(atob(raw.arrays.block_ids),c=>c.charCodeAt(0)),ids=new Uint32Array(bytes.buffer);
   const col=Math.floor(width/2),row=Math.floor(height/2),feature=raw.blocks.features.find(f=>f.id===ids[row*width+col]);
   const rect=document.querySelector('#map').getBoundingClientRect(),scale=Math.min((rect.width-70)/width,(rect.height-75)/height);
   return {name:feature.name,x:rect.x+(rect.width-width*scale)/2+(col+.5)*scale,y:rect.y+(rect.height-height*scale)/2-5+(row+.5)*scale};
  });
  await p.mouse.click(target.x,target.y);
  assert.equal(await p.locator('#block-detail h3').textContent(),target.name);
  await p.mouse.move(target.x,target.y);await p.mouse.down();await p.mouse.move(target.x+50,target.y+25);await p.mouse.up();
  assert.equal(await p.locator('#block-detail h3').textContent(),target.name);
  await p.locator('#zoom-reset').click();
  await p.locator('#block-search').fill(profile.firstName.split(' ').pop());
  await p.locator('#block-quality').selectOption('all');
  assert.equal(await p.locator('.block-row').count(),1);
  await p.locator('.block-row').click();
  assert.equal(await p.locator('#block-detail h3').textContent(),profile.firstName);
  await p.locator('#block-search').fill('not-a-block');assert.equal(await p.locator('.block-row').count(),0);
  await p.locator('#block-search').fill('');await p.locator('#block-sort').selectOption('heat_mean');
  const ranks=await p.locator('.block-row>b').allTextContents();
  assert.ok(Number(ranks[0])>=Number(ranks[ranks.length-1]));
  await p.locator('#threshold').fill('80');await p.waitForFunction(()=>document.querySelector('#threshold-output').textContent==='0.80');
  await p.locator('#reset-parameters').click();
  const pending=p.waitForEvent('download');await p.locator('#download-blocks').click();const download=await pending;
  const csv=fs.readFileSync(await download.path(),'utf8').replace(/^\uFEFF/,'').trim().split(/\r?\n/);
  const header=csv.shift().split(',').map(v=>v.replaceAll('"',''));
  const counts=csv.map(line=>Number(line.split(',')[header.indexOf('valid_pixels')].replaceAll('"','')));
  assert.equal(counts.reduce((a,b)=>a+b,0),valid);
  await p.locator('#view-raster').click();assert.equal(await p.locator('#view-raster').getAttribute('aria-pressed'),'true');
  await p.locator('#view-blocks').click();assert.equal(await p.locator('#view-blocks').getAttribute('aria-pressed'),'true');
  if(real){
   await p.locator('#block-scale').selectOption('detail');
   assert.ok((await p.locator('#block-overview').textContent()).includes('2304'));
   assert.equal(await p.locator('#metric-area').textContent(),'392.77');
   await p.locator('#block-scale').selectOption('overview');
   assert.ok((await p.locator('#block-overview').textContent()).includes('528'));
   assert.equal(await p.locator('#metric-both').textContent(),'52.87');
  }
  await p.locator('#zoom-reset').click();
  await p.setViewportSize({width:375,height:812});await p.evaluate(()=>scrollTo(0,0));
  assert.equal(await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);
  await p.screenshot({path:path.join(out,real?'changchun-mobile.png':'demo-mobile.png'),fullPage:true});
  assert.equal(requests.some(u=>/^https?:/.test(u)),false);assert.deepEqual(errors,[]);
  console.log(JSON.stringify({real,blocks:profile.count,scale:profile.scale,scaleSwitch:real,click:true,drag:true,filter:true,sort:true,csvValidPixels:valid,offline:true,mobile:true,errors}));
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1});
