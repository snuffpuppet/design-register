// Use Dockerfile.browser-test and an isolated fixture with no pending change sets.
const puppeteer = require('puppeteer-core');
const assert = require('node:assert/strict');
(async()=>{
 const browser=await puppeteer.launch({headless:true,executablePath:process.env.PUPPETEER_EXECUTABLE_PATH,timeout:60000,args:['--no-sandbox','--disable-dev-shm-usage']});
 try {
  const page=await browser.newPage();await page.setViewport({width:1500,height:1000});
  const errors=[],requests=[];
  page.on('pageerror',e=>errors.push(e.message));
  page.on('request',r=>requests.push(r.url()));
  page.on('response',async r=>{if(r.status()>=400)console.log('HTTP',r.status(),r.url(),await r.text());});
  const base=process.env.CONSOLE_URL || 'http://host.docker.internal:18085';
  await page.goto(base,{waitUntil:'networkidle0',timeout:60000});await page.waitForSelector('.rail');
  await page.evaluate(()=>{Store.set({madeBy:'Browser reviewer'});localStorage.setItem('madeBy','Browser reviewer');Store.set({view:'reviews'});});
  await page.waitForSelector('[aria-label="Session name"]');await page.type('[aria-label="Session name"]','Browser review');
  const click=async text=>page.evaluate(t=>{const b=[...document.querySelectorAll('button')].find(b=>b.textContent.trim()===t);if(!b||b.disabled)throw Error('Button unavailable: '+t);b.click();},text);
  await click('Create');await page.waitForSelector('.agenda-item');
  const reviewedId=await page.evaluate(()=>Store.state.reviews.find(r=>'reviews:'+r.id===Store.ui.view).ids[0]);
  const reviewId=await page.evaluate(()=>Store.ui.view.split(':')[1]);
  const newTitle='Browser historical correction '+Date.now();
  assert.match(await page.$eval('.workspace',e=>e.textContent),/At start of review/);
  await (await page.$('.review-detail > .card select')).select('corrected');await page.waitForSelector('.review-fields');
  const fill=async(label,value)=>{
   const handle=await page.evaluateHandle(l=>[...document.querySelectorAll('.review-detail label')].find(e=>e.firstChild.textContent===l)?.querySelector('textarea,input'),label);
   const el=handle.asElement();assert(el,'Missing '+label);await el.click({clickCount:3});await el.press('Backspace');await el.type(value);
  };
  await fill('Title',newTitle);await fill('Review reason','Verified historical position');await fill('Evidence','Workshop record');
  await click('Save and next unresolved');
  await page.waitForFunction((r,id)=>Store.state.reviews.find(x=>x.id===r)?.entries[id]?.reason,{},reviewId,reviewedId);
  await click('Preview corrections');await page.waitForSelector('.preview');
  assert.match(await page.$eval('.preview',e=>e.textContent),/Browser historical correction/);
  await page.screenshot({path:'/output/review.png',fullPage:true});
  await click('Apply 1 corrections');
  await page.waitForFunction((id,title)=>Store.byId[id]?.title===title,{},reviewedId,newTitle);
  await page.reload({waitUntil:'networkidle0'});await page.waitForSelector('.rail');
  assert.equal(await page.evaluate(id=>Store.byId[id].title,reviewedId),newTitle);
  await page.evaluate(()=>Store.set({view:'meetings'}));await page.waitForSelector('[aria-label="Session name"]');
  await page.type('[aria-label="Session name"]','Browser meeting');await click('Create');
  await page.waitForFunction(()=>document.querySelector('.workspace h2')?.textContent==='Browser meeting');
  await page.waitForSelector('.agenda-item');
  const meetingId=await page.evaluate(()=>Store.ui.view.split(':')[1]);
  const agendaId=await page.evaluate(()=>Store.state.meetings.find(r=>'meetings:'+r.id===Store.ui.view).ids[0]);
  await (await page.$('.review-detail > .card select')).select('discussed');
  await fill('Outcome','Agreed follow-up');await fill('Evidence','Meeting discussion');await fill('Follow-up action','Confirm the current position');await fill('Owner','Browser reviewer');
  await click('Create follow-up open item');
  await page.waitForFunction((m,id)=>Store.state.meetings.find(r=>r.id===m)?.entries[id]?.actionItem,{},meetingId,agendaId);
  assert.equal(await page.evaluate(()=>[...document.querySelectorAll('button')].find(b=>b.textContent==='Create follow-up open item').disabled),true);
  await page.screenshot({path:'/output/meeting.png',fullPage:true});
  const summary=await page.evaluate(m=>Store.post('/api/meetings/summary',{batch:m}),meetingId);assert.match(summary.text,/Agreed follow-up/);
  await page.evaluate(()=>Store.set({view:'report:0'}));await page.waitForSelector('.rep');
  await page.waitForFunction(()=>document.querySelector('.rep-main')?.textContent.includes('Historical corrections'));
  assert.deepEqual(errors,[]);assert(requests.every(url=>url.startsWith(base)||url.startsWith('data:')),'Unexpected external browser request');
  console.log('Browser passed: offline assets, correction preview/apply/reload, meeting follow-up and summary, report correction separation.');
 } finally { await browser.close(); }
})().catch(e=>{console.error(e);process.exit(1);});
