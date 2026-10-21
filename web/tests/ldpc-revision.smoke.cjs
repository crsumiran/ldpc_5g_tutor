// Visual preview only: synthetic unlocked navigation, real disposable API.
// No grades are granted, no learner code is edited and no model is called.
const assert=require('node:assert/strict');
const {chromium}=require(process.env.LDPC_PLAYWRIGHT_MODULE);
(async()=>{
  const browser=await chromium.launch({headless:true});
  const page=await browser.newPage({viewport:{width:1500,height:1000}});
  const errors=[];let guideCalls=0,course;
  page.on('pageerror',e=>errors.push(e.message));
  await page.route('**/api/**',async route=>{
    const req=route.request(),url=new URL(req.url());
    if(req.method()==='POST'&&/chat|tutor/.test(url.pathname))guideCalls++;
    const response=await route.fetch({url:'http://127.0.0.1:8021'+url.pathname+url.search});
    if(response.headers()['content-type']?.includes('application/json')){
      const data=await response.json();
      if(data.manifest?.id==='ldpc-5g')course=data;
      if(data.course_id==='ldpc-5g'&&data.checkpoints){
        for(const c of data.checkpoints)c.status='available';
        await route.fulfill({response,json:data});return;
      }
    }
    await route.fulfill({response});
  });
  try{
    await page.goto('http://127.0.0.1:3000/?course=ldpc-5g');
    await page.getByRole('heading',{name:'Why do we need error correction?',exact:true}).waitFor();
    for(let i=0;i<3;i++)await page.getByRole('button',{name:'Next theory page →',exact:true}).click();
    await page.getByText('Optional: full worked tables and message addresses',{exact:true}).click();
    await page.getByLabel('Select edge c1 b1',{exact:true}).click();
    await page.getByRole('status').filter({hasText:'e3: bit b1'}).waitFor();
    await page.getByRole('button',{name:'Resume assignments →',exact:true}).click();
    for(const cp of course.manifest.checkpoints){
      const escaped=cp.title.replace(/[.*+?^${}()|[\]\\]/g,'\\$&');
      await page.locator('.desktop-rail').getByRole('button',{name:new RegExp(escaped)}).click();
      await page.getByRole('heading',{name:cp.title,exact:true}).waitFor();
      await page.getByRole('button',{name:'Reveal worked results',exact:true}).click();
      for(let i=0;i<cp.fixture.views.length;i++){
        const view=cp.fixture.views[i];
        await page.getByRole('group',{name:'Worked trace steps'}).getByRole('button',{name:`${i+1}. ${view.title}`,exact:true}).click();
        await page.getByRole('heading',{name:view.title,exact:true}).first().waitFor();
      }
      if(cp.fixture.variants?.length){
        await page.getByLabel('Worked fixture variant').selectOption('0');
        await page.getByRole('heading',{name:cp.fixture.variants[0].views[0].title,exact:true}).first().waitFor();
      }
      if(cp.id==='LDPC-18')assert.match(await page.locator('.cm-content').innerText(),/NotImplementedError/);
      await page.setViewportSize({width:390,height:844});
      assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>window.innerWidth),false,cp.id+' mobile overflow');
      await page.setViewportSize({width:1500,height:1000});
    }
    assert.equal(guideCalls,0);assert.deepEqual(errors,[]);
    console.log('Revision visual smoke passed: linked e3, all 18 fixtures/steps, controlled variants, min1/min2 TODO, mobile layout, no guide calls.');
  }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
