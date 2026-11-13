// Dependency-free smoke test for the HMI routing and demo gating.
// Run: node hmi/tests/smoke.cjs
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const source = fs.readFileSync(path.join(__dirname, "..", "app.js"), "utf8");
new vm.Script(source, {filename:"app.js"});

function boot(search, hash) {
  const events = {};
  const nodes = {};
  const timers = [];
  ["app-bar", "dro", "view", "transport", "footer", "dialog-root", "splash-overlay", "splash-title", "splash-message", "splash-mode", "toast"].forEach((id) => {
    nodes[id] = {
      innerHTML: "", textContent: "", scrollTop: 0, hidden: false, focus() {}, addEventListener(event, callback) {events[id+":"+event]=callback;},
      classList:{add(){},remove(){}}, querySelector(){return {focus(){}}}
    };
  });
  const location = {search:search||"",hash:hash||""};
  const historyItems=[{hash:location.hash,state:{page:"home",depth:0}}];
  let at=0;
  const window={
    location,
    history:{
      get state(){return historyItems[at].state;},
      pushState(state,unused,next){
        historyItems.splice(at+1);
        historyItems.push({hash:next,state});
        at++;
        location.hash=next;
      },
      replaceState(state,unused,next){historyItems[at]={hash:next,state};location.hash=next;},
      back(){
        if(at>0){at--;location.hash=historyItems[at].hash;events["window:popstate"]();}
      }
    },
    addEventListener(name,callback){events["window:"+name]=callback;}
  };
  const document={
    getElementById(id){return nodes[id];},
    addEventListener(name,callback){events["document:"+name]=callback;}
  };
  vm.runInNewContext(source,{
    window,document,URLSearchParams,
    setTimeout(callback, milliseconds){timers.push({callback,milliseconds});return timers.length;},
    clearTimeout(){}
  });
  function click(id, attr, value){
    const element={disabled:false,dataset:{[attr]:value}};
    const callback=events[id+":click"];
    assert.ok(callback, "Missing click handler "+id);
    callback({target:{closest(){return element;}}});
  }
  function page(to){click("view","page",to);}
  function action(what,region){click(region||"view","action",what);}
  return {nodes,window,page,action,timers,events};
}
{
  const s=boot("");
  assert.match(s.nodes.view.innerHTML,/Machine overview/);
  assert.match(s.nodes.view.innerHTML,/Read-only preview/);
  assert.match(s.nodes.transport.innerHTML,/>Start<\/button>/);
  assert.match(s.nodes.transport.innerHTML,/data-action="start"[^>]+disabled/);
  assert.match(s.nodes.transport.innerHTML,/data-action="hold"[^>]+disabled/);
  assert.match(s.nodes.transport.innerHTML,/data-action="stop"[^>]+disabled/);
}
{
  const s=boot("?demo=1");
  assert.equal(s.nodes["splash-overlay"].hidden,false);
  const startupTimer=s.timers.find((timer)=>timer.milliseconds===4000);
  assert.ok(startupTimer,"Missing startup splash timer");
  startupTimer.callback();
  assert.equal(s.nodes["splash-overlay"].hidden,true);
  const idleTimer=s.timers.find((timer)=>timer.milliseconds===300000);
  assert.ok(idleTimer,"Missing five-minute idle timer");
  idleTimer.callback();
  assert.equal(s.nodes["splash-overlay"].hidden,false);
  assert.equal(s.nodes["splash-title"].textContent,"DISPLAY INACTIVITY TIMEOUT");
  s.events["document:pointerdown"]({preventDefault(){},stopPropagation(){}});
  assert.equal(s.nodes["splash-overlay"].hidden,true);
}
{
  const s=boot("?demo=1");
  const cases={
    run:"Current job",feed:"Commanded feed override",jog:"Manual positioning",
    tools:"Machine tools",register:"Registration sequence",
    fiducials:"Permanent ring",camera:"Image source",pen:"Protected operations",
    frames:"Coordinate references",settings:"Display brightness",inspect:"Post-print workflow",
    scan:"Capture workflow",sync:"Inspection package",results:"Artwork comparison",
    profiles:"Approved profiles",system:"Connection health"
  };
  for(const [page,text] of Object.entries(cases)){
    s.page(page);
    assert.ok(s.nodes.view.innerHTML.includes(text),"Failed page "+page);
    assert.match(s.nodes.transport.innerHTML,/data-action="start"/,"Missing global Start on "+page);
    assert.match(s.nodes.transport.innerHTML,/data-action="hold"[^>]+>Pause</,"Missing global Pause on "+page);
    assert.match(s.nodes.transport.innerHTML,/data-action="stop"[^>]+>Stop</,"Missing global Stop on "+page);
  }
  s.page("system");
  s.action("start","transport");
  assert.doesNotMatch(s.nodes.transport.innerHTML,/data-action="hold"[^>]+disabled/);
  s.action("hold","transport");
  assert.match(s.nodes.transport.innerHTML,/data-action="resume"[^>]*>Resume</);
  assert.doesNotMatch(s.nodes.transport.innerHTML,/data-action="resume"[^>]+disabled/);
  s.action("resume","transport");
  s.page("tools");
  s.action("stop","transport");
  assert.match(s.nodes["dialog-root"].innerHTML,/Stop the current job/);
  s.action("dialog-cancel","dialog-root");
  assert.equal(s.nodes["dialog-root"].innerHTML,"");
  s.page("system");
  s.action("sim-complete");
  assert.match(s.nodes["dialog-root"].innerHTML,/Simulate verified completion/);
  s.action("dialog-confirm","dialog-root");
  s.page("register");
  for(let i=0;i<5;i++)s.action("advance-register");
  assert.match(s.nodes.view.innerHTML,/20 \/ 20/);
  s.page("scan");
  for(let i=0;i<4;i++)s.action("advance-scan");
  assert.match(s.nodes.view.innerHTML,/100%/);
  assert.match(s.nodes.footer.innerHTML,/Next job locked/);
  s.page("sync");
  assert.match(s.nodes.view.innerHTML,/1 \(demo\)/);
  s.action("retry-sync");
  s.action("finish-evaluation");
  assert.match(s.nodes.footer.innerHTML,/Next job ready/);
}
{
  const s=boot("?demo=1","#/settings");
  assert.match(s.nodes.view.innerHTML,/System power/);
  s.action("reboot-pi");
  assert.match(s.nodes["dialog-root"].innerHTML,/Restart the Raspberry Pi/);
  s.action("dialog-cancel","dialog-root");
  assert.equal(s.nodes["dialog-root"].innerHTML,"");
}
{
  const s=boot("?demo=1","#/sync");
  s.action("back","app-bar");
  assert.match(s.nodes.view.innerHTML,/Post-print workflow/);
  assert.equal(s.window.location.hash,"#/inspect");
}
console.log("HMI smoke checks passed: offline gates, 17 views, transport, settings, splash/timeout, Back fallback and demo lifecycle.");
