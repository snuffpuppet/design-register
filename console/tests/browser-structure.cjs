// Requires the disposable four-record fixture described in docs/work-laptop-acceptance.md.
const puppeteer=require('puppeteer-core'),assert=require('node:assert/strict');
(async()=>{
 const browser=await puppeteer.launch({headless:true,executablePath:process.env.PUPPETEER_EXECUTABLE_PATH,args:['--no-sandbox','--disable-dev-shm-usage']});
 try{
  const page=await browser.newPage();await page.setViewport({width:1600,height:1000});const errors=[];
  page.on('pageerror',e=>{errors.push(e.message);console.log('PAGE ERROR',e.message);});
  await page.goto(process.env.CONSOLE_URL,{waitUntil:'networkidle0'});await page.waitForSelector('.rail');
  const click=async(selector,text)=>page.evaluate((s,t)=>{const e=[...document.querySelectorAll(s)].find(e=>e.textContent.trim()===t);if(!e||e.disabled)throw Error('Unavailable '+t);e.click();},selector,text);
  await page.type('.madeby','Browser operator');await click('.rail .rl-it','Rationalise');
  await page.click('tbody .st.lnk');await page.waitForSelector('tbody .menu');await page.keyboard.press('Escape');await page.waitForFunction(()=>!document.querySelector('tbody .menu'));
  await page.click('tbody .st.lnk');await page.waitForSelector('tbody .menu');await page.click('.bar.top .h2');await page.waitForFunction(()=>!document.querySelector('tbody .menu'));
  assert.equal(await page.evaluate(()=>Store.byId['LIM-0001'].status),'Identified');
  await page.evaluate(()=>Store.set({selection:new Set(['LIM-0001','LIM-0002'])}));await click('.bulk button','Merge…');
  await page.select('[aria-label="Lead record"]','LIM-0001');await page.waitForSelector('.structure-preview');
  assert.match(await page.$eval('.structure-preview',e=>e.textContent),/Other owner/);
  await page.screenshot({path:'/output/merge-preview.png',fullPage:true});
  await click('.structural button','Cancel');assert.equal(await page.evaluate(()=>!!Store.byId['LIM-0002']),true);
  await click('.bulk button','Merge…');await page.select('[aria-label="Lead record"]','LIM-0001');await page.waitForSelector('.structure-preview');await click('.structural button','Accept merge');
  await page.waitForFunction(()=>!Store.byId['LIM-0002']&&!Store.ui.structure);
  assert.deepEqual(await page.evaluate(()=>Store.byId['REQ-0001'].links),['constrained-by LIM-0001']);
  await click('.panel button','Change type');await page.select('[aria-label="New type"]','DEC');await page.select('[aria-label="New status"]','Accepted');
  await page.waitForFunction(()=>document.querySelector('.structure-preview section:nth-child(2)')?.textContent.includes('Accepted'));
  await page.screenshot({path:'/output/type-preview.png',fullPage:true});await click('.structural button','Cancel');assert.equal(await page.evaluate(()=>Store.byId['LIM-0001'].kind),'LIM');
  await click('.panel button','Change type');await page.select('[aria-label="New type"]','DEC');await page.select('[aria-label="New status"]','Accepted');
  await page.waitForFunction(()=>document.querySelector('.structure-preview section:nth-child(2)')?.textContent.includes('Accepted'));await click('.structural button','Accept type change');
  await page.waitForFunction(()=>!Store.byId['LIM-0001']&&!Store.ui.structure);
  const newId=await page.evaluate(()=>Store.state.aliases['LIM-0001'].targets[0]);assert.match(newId,/^DEC-/);
  assert.equal(await page.evaluate(id=>Store.byId[id].status,newId),'Accepted');assert.deepEqual(await page.evaluate(()=>Store.byId['REQ-0001'].links),['constrained-by '+newId]);
  await page.evaluate(()=>Store.set({open:null,selection:new Set(['OI-0001'])}));await click('.bulk button','Delete');await page.type('.bulk input','Generated duplicate');await click('.bulk button','Move 1 to rubbish bin');
  await page.waitForFunction(()=>!Store.byId['OI-0001']);await click('.rail .rl-it','Rubbish bin');await page.waitForSelector('.workspace-content');
  await page.reload({waitUntil:'networkidle0'});await page.waitForSelector('.rail');await click('.rail .rl-it','Rubbish bin');await click('.workspace-content button','Restore OI-0001');
  await page.waitForFunction(()=>!!Store.byId['OI-0001']);assert.match(await page.$eval('.workspace-content',e=>e.textContent),/bin is empty/);
  assert.deepEqual(errors,[]);console.log('PASS: status Escape/outside dismissal, merge preview/cancel/accept, type preview/cancel/accept with references, bin persistence and restore.');
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exit(1);});
