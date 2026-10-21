// Every API request uses disposable storage; no production learner state touched.
const assert=require('node:assert/strict');
const {chromium}=require(process.env.LDPC_PLAYWRIGHT_MODULE);
const origin=process.env.FLOW_WEB_URL||'http://127.0.0.1:3021';
(async()=>{
  const browser=await chromium.launch({headless:true});
  const page=await browser.newPage({viewport:{width:1500,height:1000}});
  const errors=[];let preview=false,guideCalls=0,course;
  page.on('pageerror',e=>errors.push(e.message));
  await page.route('**/api/**',async route=>{
    const req=route.request(),url=new URL(req.url());
    if(req.method()==='POST'&&/chat|tutor/.test(url.pathname))guideCalls++;
    const response=await route.fetch({url:'http://127.0.0.1:8021'+url.pathname+url.search});
    if(response.headers()['content-type']?.includes('application/json')){
      const data=await response.json();
      if(data.manifest?.id==='optical-flow')course=data;
      if(preview&&data.course_id==='optical-flow'&&data.checkpoints){data.checkpoints.forEach(c=>c.status='available');await route.fulfill({response,json:data});return;}
    }
    await route.fulfill({response});
  });
  const visual=id=>page.locator(`[data-visual="${id}"]`);
  const status=id=>visual(id).locator('p[role="status"]').innerText();
  const slider=async(id,label,value,min=-2,step=.25)=>{const control=visual(id).getByLabel(label,{exact:true});await control.focus();await control.press('Home');for(let i=0;i<Math.round((value-min)/step);i++)await control.press('ArrowRight');};
  const reset=async id=>visual(id).getByRole('button',{name:'Reset demonstration',exact:true}).click();
  const next=()=>page.getByRole('button',{name:'Next theory page →',exact:true}).click();
  const prev=()=>page.getByRole('button',{name:'← Previous theory page',exact:true}).click();
  async function mobile(name){
    await page.setViewportSize({width:390,height:844});
    assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false,name+' mobile overflow');
    await page.screenshot({path:`/tmp/flow-${name}-mobile.png`,fullPage:true});
    await page.setViewportSize({width:1500,height:1000});
  }
  try{
    await page.goto(origin+'/?course=optical-flow');
    await page.getByRole('heading',{name:'From image gradients to image motion',exact:true}).waitFor();
    assert.equal(course.manifest.checkpoints.length,12);
    assert.match(await page.locator('.desktop-tutor').innerText(),/Motion guide/);
    assert.equal(await page.getByRole('button',{name:/Run public tests/}).count(),0);
    assert.match(await page.getByRole('article',{name:'Chapter explanation'}).innerText(),/fixed-reference approximation/);
    assert.match(await status('correspondence'),/Time 0\/4/);
    const controls=visual('correspondence');
    const sceneReadout=controls.locator('[aria-label="Live scene and brightness readout"]');
    await controls.getByLabel('Flow scene').selectOption('edge');
    assert.match(await sceneReadout.innerText(),/Vertical ramp[\s\S]*I0=2, I1=2, It=0/);
    await controls.getByLabel('Flow scene').selectOption('flat');
    assert.match(await sceneReadout.innerText(),/Flat region[\s\S]*I0=4, I1=4, It=0/);
    await controls.getByLabel('Brightness change').selectOption('0.15');
    assert.match(await sceneReadout.innerText(),/Brightness offset \+0.15[\s\S]*I0=4, I1=4.15, It=0.15/);
    const flatFrames=await controls.locator('figure svg').evaluateAll(nodes=>nodes.slice(0,2).map(svg=>Array.from(new Set(Array.from(svg.querySelectorAll('rect[fill]')).map(rect=>rect.getAttribute('fill')))).filter(fill=>fill!=='none')));
    assert.equal(flatFrames[0].length,1);assert.equal(flatFrames[1].length,1);assert.notEqual(flatFrames[0][0],flatFrames[1][0]);
    await reset('correspondence');
    await visual('correspondence').getByRole('button',{name:'Single step',exact:true}).click();
    assert.match(await status('correspondence'),/Displacement \[0.125,0\]/);
    await slider('correspondence','Scene horizontal motion',1,0);
    assert.match(await status('correspondence'),/Displacement \[0.25,0\]/);
    await slider('correspondence','Selected x',3,0,1);await slider('correspondence','Selected y',1,0,1);
    assert.match(await status('correspondence'),/I0=3, I1=2.75/);
    await visual('correspondence').getByLabel('Flow scene').selectOption('flat');
    assert.match(await visual('correspondence').innerText(),/Intentional invariance: flat/);
    await visual('correspondence').getByLabel('Brightness change').selectOption('0.15');
    assert.match(await status('correspondence'),/It=0.15/);
    await visual('correspondence').getByLabel('Flow scene').selectOption('edge');
    assert.match(await visual('correspondence').innerText(),/Intentional invariance: the vertical/);
    await reset('correspondence');
    await visual('correspondence').getByRole('button',{name:'Play',exact:true}).click();
    await page.waitForTimeout(1050);await visual('correspondence').getByRole('button',{name:'Pause',exact:true}).click();
    const paused=await status('correspondence');await page.waitForTimeout(1050);assert.equal(await status('correspondence'),paused);
    await visual('correspondence').getByRole('button',{name:'Rewind timeline',exact:true}).click();
    assert.match(await status('correspondence'),/Time 0\/4/);
    await mobile('motion');
    await visual('correspondence').getByRole('button',{name:'Play',exact:true}).click();
    await next();await prev();assert.match(await status('correspondence'),/Time 0\/4/);
    await page.waitForTimeout(1050);assert.match(await status('correspondence'),/Time 0\/4/);
    await page.emulateMedia({reducedMotion:'reduce'});
    await page.waitForFunction(()=>Array.from(document.querySelectorAll('[data-visual=correspondence] button')).some(b=>b.textContent==='Play'&&b.disabled));
    assert.equal(await visual('correspondence').getByRole('button',{name:'Play',exact:true}).isDisabled(),true);
    await visual('correspondence').getByRole('button',{name:'Single step',exact:true}).click();
    assert.match(await status('correspondence'),/Time 1\/4/);
    await page.emulateMedia({reducedMotion:'no-preference'});
    await next();
    for(let i=0;i<9;i++){await visual('patch').getByRole('group',{name:'Patch selection'}).getByRole('button').nth(i).click();assert.match(await status('patch'),new RegExp('Row '+(i+1)+','));}
    await slider('patch','Candidate u',0);await slider('patch','Candidate v',0);
    assert.match(await status('patch'),/Total squared error=4.125/);
    await slider('patch','Candidate u',.5);assert.match(await status('patch'),/Total squared error=2.625/);
    await reset('patch');assert.match(await status('patch'),/Total squared error=0/);
    for(const kind of ['flat','edge','corner']){
      await visual('ambiguity').getByLabel('Gradient evidence',{exact:true}).selectOption(kind);
      await slider('ambiguity','Candidate v',1);await slider('ambiguity','Candidate u',1);
      assert.match(await status('ambiguity'),kind==='flat'?/Squared error=0/:kind==='edge'?/eigenvalues \[0,1\]/:/Both candidate/);
    }
    await visual('ambiguity').getByLabel('Gradient evidence',{exact:true}).selectOption('edge');
    const edgeError=(await status('ambiguity')).match(/Squared error=([^.]*(?:\.\d+)?)/)[0];
    await slider('ambiguity','Candidate v',-1);assert.ok((await status('ambiguity')).includes(edgeError));
    await reset('ambiguity');await mobile('patches');await next();
    assert.match(await status('sampling'),/sampled intensity=12.5/);
    assert.match(await visual('sampling').getByRole('table').innerText(),/0.375[\s\S]*0.125[\s\S]*7.5[\s\S]*3.75/);
    await slider('sampling','Sample x',1,0);await slider('sampling','Sample y',1,0);
    assert.match(await status('sampling'),/sampled intensity=30/);await reset('sampling');
    await slider('alignment','Proposed horizontal flow',.5);
    assert.match(await status('alignment'),/Photometric RMS: 0.0000/);
    await visual('alignment').getByLabel('Brightness change').selectOption('0.15');
    assert.match(await status('alignment'),/Photometric RMS: 0.1500/);
    await slider('alignment','Selected x',4,0,1);await slider('alignment','Selected y',3,0,1);
    assert.match(await status('alignment'),/sampled=outside/);
    await reset('alignment');await visual('alignment').getByLabel('Flow scene').selectOption('edge');
    await slider('alignment','Proposed horizontal flow',.5);await slider('alignment','Proposed vertical flow',1);
    assert.match(await status('alignment'),/Photometric RMS: 0.0000/);
    await visual('alignment').getByLabel('Flow scene').selectOption('flat');await slider('alignment','Proposed horizontal flow',-1);
    assert.match(await status('alignment'),/Photometric RMS: 0.0000/);
    await slider('alignment','Scene horizontal motion',2,0);assert.match(await status('alignment'),/Scene \[2,0\]/);
    await reset('alignment');
    for(let i=1;i<=4;i++){await visual('refinement').getByRole('button',{name:'Single step',exact:true}).click();assert.match(await status('refinement'),new RegExp('Step '+i+':'));}
    assert.match(await status('refinement'),/Residual is zero/);await reset('refinement');
    await visual('refinement').getByRole('button',{name:'Play',exact:true}).click();await page.waitForTimeout(1050);
    await visual('refinement').getByRole('button',{name:'Pause',exact:true}).click();const rp=await status('refinement');await page.waitForTimeout(1050);assert.equal(await status('refinement'),rp);
    await reset('refinement');assert.match(await status('refinement'),/Step 0:/);
    await page.screenshot({path:'/tmp/flow-alignment-desktop.png',fullPage:true});
    await visual('alignment').screenshot({path:'/tmp/flow-lookup-detail.png'});
    await visual('refinement').screenshot({path:'/tmp/flow-refinement-detail.png'});await mobile('alignment');
    await visual('refinement').getByRole('button',{name:'Play',exact:true}).click();
    await next();await prev();assert.match(await status('refinement'),/Step 0:/);
    await page.waitForTimeout(1050);assert.match(await status('refinement'),/Step 0:/);await next();
    for(let i=0;i<3;i++){await visual('pyramid').getByRole('button',{name:new RegExp('Level '+i+' ·')}).click();assert.match(await status('pyramid'),new RegExp('spacing '+(2**i)));}
    await reset('pyramid');assert.match(await status('pyramid'),/Level 0:/);await mobile('scales');await next();
    assert.match(await status('evaluation'),/mean endpoint error=2.5/);
    const mask=visual('evaluation').getByRole('group',{name:'Evaluation mask'}).getByRole('button');
    await mask.nth(0).click();await mask.nth(1).click();assert.match(await status('evaluation'),/NaN \(no measurements\)/);
    for(let i=0;i<6;i++)await mask.nth(i).click();assert.match(await status('evaluation'),/Count=6\/6/);
    await reset('evaluation');assert.match(await status('evaluation'),/Count=2\/6/);
    await slider('consistency','Backward horizontal bias',.5,-.5);assert.match(await status('consistency'),/consistent=true/);
    await slider('consistency','Round-trip threshold',.45,0,.05);assert.match(await status('consistency'),/consistent=false/);
    await reset('consistency');await visual('consistency').getByRole('checkbox').uncheck();assert.match(await status('consistency'),/sampled validity=0.5; consistent=false/);
    await reset('consistency');assert.match(await status('consistency'),/Round-trip error=0; sampled validity=1; consistent=true/);
    await mobile('trust');
    await page.getByRole('button',{name:'Continue to assignments →',exact:true}).click();
    await page.getByRole('heading',{name:'Image change becomes a motion equation',exact:true}).waitFor();
    assert.match(await page.getByRole('article',{name:'Assignment explanation'}).innerText(),/Both are arrays with H rows and W columns/);
    await page.getByRole('button',{name:/Run public tests/}).click();
    await page.getByText('3 public check(s) need attention',{exact:true}).waitFor({timeout:45000});
    await page.locator('.cm-content').click();await page.keyboard.press('Control+a');
    await page.keyboard.insertText('import numpy as np\ndef gradients(frame0, frame1):\n    a=np.asarray(frame0,float); b=np.asarray(frame1,float)\n    iy,ix=np.gradient(a)\n    return ix,iy,b-a\n');
    await page.getByRole('button',{name:/Submit checkpoint/}).click();
    await page.getByText('Checkpoint passed',{exact:true}).waitFor({timeout:45000});
    assert.equal(await page.locator('.desktop-rail').getByRole('button',{name:/One patch, many equations/}).isDisabled(),false);
    const flowSession=await page.evaluate(()=>localStorage.getItem('optical-flow-lab-session'));
    assert.ok(flowSession);assert.equal(await page.evaluate(()=>localStorage.getItem('ldpc-lab-session')),null);
    preview=true;await page.reload();
    await page.getByRole('heading',{name:'Image change becomes a motion equation',exact:true}).waitFor();
    assert.match(await page.locator('.cm-content').innerText(),/np.gradient/);
    for(const cp of course.manifest.checkpoints){
      const escaped=cp.title.replace(/[.*+?^${}()|[\]\\]/g,'\\$&');
      await page.locator('.desktop-rail').getByRole('button',{name:new RegExp(escaped)}).click();
      await page.getByRole('heading',{name:cp.title,exact:true}).waitFor();
      assert.match(await page.getByRole('article',{name:'Assignment explanation'}).innerText(),/What the public checks reveal/);
      await page.getByText('Concrete invocation (inputs are constructed here, not assumed):',{exact:true}).waitFor();
      await page.getByText('Hints for this implementation',{exact:true}).click();await page.getByText('Hint 1',{exact:true}).click();
      await page.getByText('Try an experiment and reflect',{exact:true}).click();
      await mobile(cp.id);
    }
    assert.equal(guideCalls,0);
    preview=false;await page.goto(origin+'/?course=ldpc-5g');
    await page.getByRole('heading',{name:'Why do we need error correction?',exact:true}).waitFor();
    await page.getByText('Optional: explore the explanation visually',{exact:true}).click();
    assert.equal(await page.locator('.primer-flow').count(),1);
    await page.goto(origin+'/?course=optical-flow');
    await page.getByRole('heading',{name:'One patch, many equations',exact:true}).waitFor();
    assert.equal(await page.evaluate(()=>localStorage.getItem('optical-flow-lab-session')),flowSession);
    await page.goto(origin+'/?course=cache-lab');
    await page.getByRole('heading',{name:'Decode the Address',exact:true}).waitFor();
    assert.deepEqual(errors,[]);
    console.log('PASS: all 9 section visuals and controls; playback/pause/reset/navigation/reduced motion; 5 mobile chapters and 12 assignments; TODO failure, submit/unlock, saved code, course isolation, legacy LDPC/cache, zero AI requests.');
  }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
