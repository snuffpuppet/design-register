// Run against a disposable direct-write engagement, never a real register.
const puppeteer = require('puppeteer-core');
const assert = require('node:assert/strict');
(async () => {
 const browser = await puppeteer.launch({headless:true, executablePath:process.env.PUPPETEER_EXECUTABLE_PATH, args:['--no-sandbox','--disable-dev-shm-usage']});
 try {
  const page = await browser.newPage(); await page.setViewport({width:1600,height:1000});
  const errors=[]; page.on('pageerror', e=>errors.push(e.message));
  await page.goto(process.env.CONSOLE_URL, {waitUntil:'networkidle0'}); await page.waitForSelector('.rail');
  const click = async (selector, text) => page.evaluate((selector,text)=>{
   const el=[...document.querySelectorAll(selector)].find(e=>e.textContent.trim()===text);
   if(!el || el.disabled) throw Error('Unavailable: '+text); el.click();
  },selector,text);
  await page.type('.madeby','Browser operator');
  await click('.rail .rl-it','Rationalise');
  await page.waitForFunction(()=>Store.ui.mode==='rationalise');
  const ids=await page.evaluate(()=>Store.state.items.filter(i=>i.kind==='LIM').slice(0,2).map(i=>i.id));
  assert.equal(ids.length,2);
  await page.evaluate(async id=>{await Store.post('/api/edit',{id,fields:{Status:'Identified'}});await Store.load();},ids[0]);
  await page.evaluate(ids=>Store.set({view:'LIM',open:ids[0]}),ids);
  await page.waitForSelector('.panel .st.lnk'); await page.click('.panel .st.lnk');
  await click('.panel .mi span','Accepted');
  await page.waitForFunction(id=>Store.byId[id].status==='Accepted',{},ids[0]);
  assert.equal(await page.evaluate(id=>Store.byId[id].history.at(-1).includes('Correction'),ids[0]),true);
  await page.evaluate(ids=>Store.set({open:null,selection:new Set(ids)}),ids);
  await click('.bulk button','Set field');
  await page.select('.bulk select','closed-on'); await page.type('.bulk input','1 September 2026');
  await click('.bulk button','Apply to 2');
  await page.waitForFunction(ids=>ids.every(id=>Store.byId[id]['closed-on']==='1 September 2026'),{},ids);
  await page.evaluate(ids=>Store.set({selection:new Set(ids)}),ids);
  await click('.bulk button','Set field'); await page.select('.bulk select','closed-on');
  await click('.bulk button','Apply to 2');
  await page.waitForFunction(ids=>ids.every(id=>Store.byId[id]['closed-on']===''),{},ids);
  const scope=await page.evaluate(()=>Store.model.scopes[0]); assert(scope);
  await page.evaluate(ids=>Store.set({selection:new Set(ids)}),ids);
  await click('.bulk button','Set field'); await page.select('.bulk select','scope');
  await page.select('.bulk select:nth-of-type(2)',scope); await click('.bulk button','Apply to 2');
  await page.waitForFunction((ids,scope)=>ids.every(id=>Store.byId[id].scope===scope),{},ids,scope);
  await click('.rail .rl-it',scope);
  await page.waitForFunction(scope=>Store.ui.mode==='desktop' && Store.ui.filter.scopes[0]===scope,{},scope);
  assert.equal(await page.evaluate(()=>Store.rows().every(i=>i.scope===Store.ui.filter.scopes[0])),true);
  await page.evaluate(id=>Store.set({open:id}),ids[0]);
  await page.waitForSelector('.panel .st.lnk'); await page.click('.panel .st.lnk');
  assert.match(await page.$eval('.panel .menu',e=>e.textContent),/not from Accepted/);
  assert.equal(await page.evaluate(id=>Store.byId[id].status,ids[0]),'Accepted');
  const result=await page.evaluate(async id=>{
   const r=await fetch('/api/transition',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id,to:'Identified',madeBy:'Browser operator'})});return {status:r.status,body:await r.json()};
  },ids[0]);
  assert.equal(result.status,400); assert(result.body.error);
  await page.screenshot({path:'/output/simple-desktop.png',fullPage:true});
  await click('.rail .rl-it','Rationalise');
  await page.screenshot({path:'/output/simple-rationalise.png',fullPage:true});
  assert.deepEqual(errors,[]); console.log('PASS: immediate status correction; bulk date set/clear and scope; scoped Desktop restores workflow checks; no browser errors.');
 } finally {await browser.close();}
})().catch(e=>{console.error(e);process.exit(1);});
