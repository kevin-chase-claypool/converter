/* XY-Theta portrait HMI — standalone navigation/UI preview.
 * Deliberately no RP23CNC or camera commands: see README.md for adapter contract.
 * Any simulation is visibly labeled and never calls a hardware endpoint.
 */
(function () {
  "use strict";
  var pages = {
    home: ["Home", null],
    run: ["Run", "home"], feed: ["Feed override", "run"],
    jog: ["Jog", "home"],
    tools: ["Tools", "home"], register: ["Optical registration", "tools"],
    fiducials: ["Fiducial diagnostics", "tools"], camera: ["Camera", "tools"],
    pen: ["Pen tools", "tools"], frames: ["Coordinates", "tools"],
    settings: ["Pi settings", "tools"],
    inspect: ["Inspection", "home"], scan: ["Scan progress", "inspect"],
    sync: ["Windows sync", "inspect"], results: ["Results", "inspect"],
    profiles: ["Calibration profiles", "inspect"], system: ["System status", "home"]
  };
  var q = new URLSearchParams(window.location.search);
  var app = {
    demo: q.get("demo") === "1",
    page: "home",
    machine: "idle",
    stage: "ready",
    loaded: true,
    done: false,
    progress: 0,
    scanProgress: 0,
    regIndex: 0,
    positions: {X:0,Y:0,A:0,Z:0,B:0},
    override: 100,
    jogSystem: "pen",
    jogStep: 1,
    cameraMode: "preview",
    dialog: null,
    brightness: null,
    timeoutMinutes: 5,
    networkActive: "—",
    networkMode: "—",
    networkInterface: "—",
    settingsAttempted: false,
    settingsLoading: false,
    settingsError: "",
    systemActionPending: false,
    splashMode: "startup"
  };
  if (!app.demo) app.loaded = false;
  var root = document.getElementById("view");
  var statusNames = {
    ready:"Ready",drawing:"Drawing",held:"Feed hold",registering:"Registering",
    scanning:"Scanning",awaiting_windows:"Awaiting Windows",evaluating:"Evaluating"
  };
  function status() {
    return app.demo ? statusNames[app.stage] : "Not connected";
  }
  function locked() { return !app.demo || app.stage !== "ready"; }
  function canJog() { return app.demo && app.machine === "idle" && app.stage === "ready"; }
  function canStart() { return app.demo && app.loaded && app.stage === "ready" && app.machine === "idle"; }
  function canHold() { return app.demo && app.machine === "run"; }
  function canResume() { return app.demo && app.machine === "hold"; }
  function canStop() { return app.demo && (app.machine === "run" || app.machine === "hold"); }
  function badge(label,kind) { return '<span class="badge '+(kind||"")+'">'+label+"</span>"; }
  function button(label,action,style,enabled) {
    return '<button type="button" class="btn '+(style||"")+'" data-action="'+action+'"'+(enabled?"":' disabled title="Unavailable in this state"')+'>'+label+"</button>";
  }
  function nav(page,icon,label,desc) {
    return '<button type="button" class="nav-item" data-page="'+page+'"><span class="nav-icon" aria-hidden="true">'+icon+'</span><span class="nav-info"><b>'+label+'</b><small>'+desc+'</small></span><span class="chevron" aria-hidden="true">›</span></button>';
  }
  function tile(page,icon,label,desc) {
    return '<button type="button" class="tile" data-page="'+page+'"><span class="nav-icon" aria-hidden="true">'+icon+'</span><b>'+label+'</b><small>'+desc+'</small></button>';
  }
  function card(content,compact) { return '<section class="card'+(compact?' compact':'')+'">'+content+'</section>'; }
  function strip(message,kind) { return '<div class="info-strip '+(kind||"")+'">'+message+'</div>'; }
  function metric(label,value) { return '<div class="metric"><small>'+label+'</small><b>'+value+'</b></div>'; }
  function meta(pairs) {
    var s='<div class="meta">';
    pairs.forEach(function(p){ s+='<span>'+p[0]+'</span><span>'+p[1]+'</span>'; });
    return s+"</div>";
  }
  function choose(type,value,label,current,enabled) {
    return '<button type="button" class="choice'+(current===value?' active':'')+'" data-choose="'+type+'" data-value="'+value+'" aria-pressed="'+(current===value)+'"'+(enabled===false?' disabled':'')+'>'+label+"</button>";
  }
  function motionBanner() {
    return app.demo ? strip("<b>DEMO MODE.</b> These controls simulate state only. No commands are sent to hardware.","warn"):
      strip("<b>Read-only preview.</b> No sender/supervisor connection exists. Motion, homing, scanning and approval actions are disabled.","warn");
  }
  function cameraView(){
    var mode = app.cameraMode === "preview" ? "Live preview" :
      app.cameraMode === "still" ? "Last captured image" : "Calibration overlay";
    return '<div class="camera" role="img" aria-label="'+mode+' is unavailable; no live image connected"><div class="crosshair"></div><div class="camera-label"><b>◎ '+mode+'</b><div class="small">Image source not connected</div></div></div>';
  }
  function progress(value) {
    return '<div class="progress" role="progressbar" aria-valuemin="0" aria-valuemax="100" aria-valuenow="'+value+'"><div style="width:'+value+'%"></div></div>';
  }
  var SETTINGS_API = "http://127.0.0.1:8765";
  function settingsRequest(path, payload) {
    if (typeof fetch !== "function") {
      return Promise.reject(new Error("Local settings service unavailable"));
    }
    var options = {method: payload === undefined ? "GET" : "POST", headers:{}};
    if (payload !== undefined) {
      options.headers["Content-Type"] = "application/json";
      options.body = JSON.stringify(payload);
    }
    return fetch(SETTINGS_API + path, options).then(function(response) {
      return response.json().then(function(data) {
        if (!response.ok) throw new Error(data.error || "Settings request failed");
        return data;
      });
    });
  }
  function refreshPiSettings(force) {
    if (app.settingsLoading || (!force && app.settingsAttempted)) return;
    app.settingsAttempted = true;
    app.settingsLoading = true;
    app.settingsError = "";
    Promise.all([
      settingsRequest("/status"),
      settingsRequest("/timeout")
    ]).then(function(results) {
      var network = results[0];
      app.brightness = Number(network.brightness);
      app.networkActive = network.active || "Not connected";
      app.networkMode = network.mode || "unknown";
      app.networkInterface = network.interface || "—";
      app.timeoutMinutes = Number(results[1].minutes);
      resetIdleTimer();
    }).catch(function(error) {
      app.settingsError = error.message || "Local settings service unavailable";
    }).finally(function() {
      app.settingsLoading = false;
      if (app.page === "settings") render();
    });
  }
  function saveBrightness(value) {
    value = Math.max(1, Math.min(31, Number(value)));
    app.brightness = value;
    settingsRequest("/brightness", {value:value}).then(function() {
      toast("Display brightness set to " + Math.round(value * 100 / 31) + "%.");
    }).catch(function(error) {
      toast("Brightness unavailable: " + error.message);
    });
  }
  function saveTimeout(value) {
    app.timeoutMinutes = Number(value);
    settingsRequest("/timeout", {minutes:app.timeoutMinutes}).then(function() {
      resetIdleTimer();
      toast(app.timeoutMinutes ? "Display timeout set to " + app.timeoutMinutes + " minutes." : "Display timeout disabled.");
    }).catch(function(error) {
      toast("Timeout unavailable: " + error.message);
    });
  }
  function requestSystemAction(action) {
    var path = action === "reboot" ? "/reboot" : "/poweroff";
    var confirmation = action === "reboot" ? "RESTART" : "POWER OFF";
    app.systemActionPending = true;
    render();
    settingsRequest(path, {confirm:confirmation}).then(function(result) {
      toast(result.message || (action === "reboot" ? "Restart requested." : "Power off requested."));
    }).catch(function(error) {
      app.systemActionPending = false;
      toast("System action failed: " + error.message);
      render();
    });
  }
  function renderHome(){
    return '<div class="stack">'+
      '<div class="section-head"><h1>Machine overview</h1>'+badge(status(),app.demo?"blue":"warn")+'</div>'+
      (!app.demo?motionBanner():strip("Simulation enabled. The interface is interactive; no machine is being controlled."))+
      card('<div class="split"><h2>XY-Theta</h2>'+badge(app.demo?"Controller (demo)":"Controller offline",app.demo?"good":"warn")+'</div>'+
        meta([["Job",app.demo?"calibration_test.gcode":"None loaded"],["Motion",app.demo?(app.machine==="idle"?"Idle":app.machine):"Unknown"],["Inspection",status()],["Next job",locked()?"Locked":"Available"]]),true)+
      '<div class="home-grid">'+
        tile("run","▶","Run","Plot, pause, stop & feed")+
        tile("jog","✥","Jog","Pen, camera & rotary")+
        tile("tools","⚙","Tools","Optical registration & setup")+
        tile("inspect","▧","Inspect","Scan, sync & calibration")+
      '</div>'+
      nav("system","ℹ","System status","Controller, camera, Windows and diagnostic preview")+
      '</div>';
  }
  function renderRun(){
    return '<div class="stack">'+motionBanner()+
      card('<div class="split"><h2>Current job</h2>'+badge(app.demo?app.machine.toUpperCase():"NO SENDER",app.demo?"blue":"warn")+'</div>'+
        meta([["File",app.demo?"calibration_test.gcode":"No G-code loaded"],["Progress",app.demo?app.progress+"%":"—"],["ETA","Unavailable"]])+
        progress(app.demo?app.progress:0),true)+
      card('<div class="split"><h2>Camera</h2>'+badge("Still/preview","blue")+'</div>'+cameraView()+
        button("Open camera views","camera-page","ghost",true),true)+
      nav("feed","⇅","Feed override",app.demo?app.override+"% commanded override":"Adjust commanded feed and reset to 100%")+
      strip((locked()?"New G-code submission is locked or unavailable.":"Next job submission available (simulation only).")+" Physical emergency stop remains separate.","")+
      '</div>';
  }
  function renderFeed(){
    return '<div class="stack">'+motionBanner()+card(
      '<h2>Commanded feed override</h2><div class="split"><span class="muted">Override setting</span><b id="override-label">'+app.override+'%</b></div>'+
      '<input type="range" class="slider" min="10" max="200" step="10" value="'+app.override+'" data-input="override" aria-label="Commanded feed override"'+(!app.demo?' disabled':'')+'>'+
      '<div class="btn-row">'+button("−10%","feed-down","ghost",app.demo)+button("Reset 100%","feed-reset","primary",app.demo)+button("+10%","feed-up","ghost",app.demo)+'</div>'+
      strip("The override is a command, not the reported actual feed rate. Final sender integration must supply and verify acknowledgements."),false)+'</div>';
  }
  function renderJog(){
    var axisHint = app.jogSystem==="pen"?"Pen X/Y axes":
      app.jogSystem==="camera"?"Raw grblHAL Z/B axes — do not assume Cartesian camera X/Y":"Controller A axis (motor-shaft degrees until conversion is commissioned)";
    function jog(label,direction,active) {
      return '<button class="btn ghost" type="button" data-jog="'+direction+'"'+(active&&canJog()?'':' disabled')+' aria-label="Jog '+label+'">'+label+"</button>";
    }
    return '<div class="stack">'+motionBanner()+
      card('<h2>Motion system</h2><div class="choice-row">'+
        choose("jogSystem","pen","Pen XY",app.jogSystem)+
        choose("jogSystem","camera","Camera ZB",app.jogSystem)+
        choose("jogSystem","rotary","Rotary A",app.jogSystem)+'</div>'+
        '<p class="small muted">'+axisHint+'</p>'+
        '<div class="split"><span class="field-label">Jog increment</span>'+badge(app.jogStep+(app.jogSystem==="rotary"?"°":" mm"),"blue")+'</div>'+
        '<div class="choice-row">'+choose("jogStep","0.1","0.1",String(app.jogStep))+
        choose("jogStep","1","1",String(app.jogStep))+
        choose("jogStep","10","10",String(app.jogStep))+'</div>',false)+
      card('<div class="split"><h2>Manual positioning</h2>'+badge(canJog()?"Jog permitted (demo)":"JOG LOCKED",canJog()?"good":"warn")+'</div>'+
        '<div class="jog-pad"><span></span>'+jog("↑","up",app.jogSystem!=="rotary")+'<span></span>'+
          jog("←","left",true)+'<span class="center">'+(app.jogSystem==="rotary"?"A":app.jogSystem==="camera"?"Z / B":"X / Y")+'</span>'+jog("→","right",true)+
          '<span></span>'+jog("↓","down",app.jogSystem!=="rotary")+'<span></span></div>'+
        '<p class="small muted">Jog controls are locked during drawing, inspection, faults or uncertain controller state. Camera Z/B kinematics and limits must be commissioned first.</p>',false)+
      nav("tools","⚙","Homing and protected macros","Home & Register, Pen Lift & Park")+
      '</div>';
  }
  function renderTools(){
    return '<div class="stack"><h1>Machine tools</h1><div class="nav-list">'+
      nav("register","◎","Optical registration","Bed center first, then B00 Theta zero")+
      nav("fiducials","▦","Fiducial diagnostics","20 permanent outer-ring AprilTags")+
      nav("camera","▣","Camera inspection station","Preview, last image, and overlays")+
      nav("pen","✎","Pen and homing tools","Protected park and controller-owned macros")+
      nav("frames","⌖","Coordinates & work zero","Five-axis coordinates and reference frames")+
      nav("settings","⏻","Pi settings & power","Display, network and safe system actions")+
      nav("system","ℹ","System diagnostics","Connection health and demo controls")+
      '</div></div>';
  }
  function regSteps(){
    var labels=["Home CoreZB and verify geometry","Fit bed center from rotating fiducials","Align B00 to calibrated east-side θ=0°","Check outer fiducial ring","Save registration evidence"];
    return '<div class="steps">'+labels.map(function(t,i){
      var k=app.demo&&app.regIndex>i?"done":app.demo&&app.stage==="registering"&&app.regIndex===i?"active":"";
      return '<div class="step '+k+'"><span class="step-number">'+(k==="done"?"✓":i+1)+'</span><span>'+t+'</span></div>';
    }).join("")+'</div>';
  }
  function renderRegister(){
    return '<div class="stack">'+motionBanner()+
      strip("Leave the completed artwork taped in place. Keep all permanent outer-ring AprilTags unobstructed.")+
      card('<div class="split"><h2>Registration sequence</h2>'+badge(app.stage==="registering"?"In progress (demo)":"Not running",app.stage==="registering"?"blue":"")+'</div>'+
        regSteps()+
        button(app.stage==="registering"?"Advance simulation":"Run registration",app.stage==="registering"?"advance-register":"start-register","primary",app.demo&&(app.machine==="idle")&&(app.stage==="ready"||app.stage==="registering")),false)+
      card('<h2>Measured references</h2><div class="metrics">'+
        metric("Rotation center X",app.demo&&app.regIndex>=2?"0.00 mm (demo)":"— mm")+
        metric("Rotation center Y",app.demo&&app.regIndex>=2?"0.00 mm (demo)":"— mm")+
        metric("Optical θ zero",app.demo&&app.regIndex>=3?"B00 (demo)":"Unverified")+
        metric("Fiducials",app.demo&&app.regIndex>=4?"20 / 20 (demo)":"— / 20")+
      '</div><p class="small muted">No numerical measurement is shown until a calibrated camera and motion supervisor provide evidence.</p>',true)+
      '</div>';
  }
  function renderFiducials(){
    var count=app.demo&&app.regIndex>=4?20:0;
    var tags=Array.from({length:20},function(_,i){ var id="B"+String(i).padStart(2,"0");return '<div class="tag '+(i<count?"found":"")+'" title="'+id+'">'+id+'</div>';}).join("");
    return '<div class="stack">'+card('<div class="split"><h2>Permanent ring</h2>'+badge(count?(count+"/20 detected · DEMO"):"No scan","blue")+'</div>'+
      '<div class="tag-grid">'+tags+'</div>'+
      strip("These are nominal tag IDs, not detected live markers. Actual positions/orientations are measured during commissioning.")+
      button("Open optical registration","open-register","primary",true),false)+
      nav("camera","▣","Inspect camera image","Verify field of view and fiducial visibility")+'</div>';
  }
  function renderCamera(){
    return '<div class="stack">'+motionBanner()+
      card('<h2>Image source</h2><div class="choice-row">'+
      choose("cameraMode","preview","Preview",app.cameraMode)+
      choose("cameraMode","still","Last still",app.cameraMode)+
      choose("cameraMode","overlay","Overlay",app.cameraMode)+'</div>'+
      cameraView()+
      '<p class="small muted">Frames must be stamped with actual CoreZB pose and Theta position at exposure. Overlays remain unavailable until calibrated capture data exists.</p>',false)+
      nav("fiducials","▦","Fiducial visibility","View expected tag IDs and registration status")+'</div>';
  }
  function renderPen(){
    return '<div class="stack">'+motionBanner()+
      card('<h2>Protected operations</h2><p class="small muted">These actions require a verified Idle state and use established controller macros and toolhead handshakes — never generic homing G-code.</p>'+
      button("Home & Register","home-park","primary",canJog())+
      button("Pen Lift & Park","pen-park","ghost",canJog()),false)+
      strip("M5 is PEN_CLEAR, not proof of full retract. Controller-owned P100/P116 and the verified park contract must be honored.","warn")+
      '</div>';
  }
  function renderFrames(){
    return '<div class="stack">'+card('<h2>Coordinate references</h2>'+
      meta([["Work offset","G54 (when supplied)"],["Pen","X / Y"],["Bed controller axis","A — motor-shaft degrees"],["CoreZB raw axes","Z / B"],["Optical rotary center","Unverified"],["Optical zero","Unverified"]])+
      strip("Optical θ=0° and the controller A-axis coordinate must be explicitly reconciled. A commanded angle is not itself an optical measurement."),false)+'</div>';
  }
  function renderPiSettings(){
    var brightness = app.brightness === null ? "Reading…" :
      (app.brightness + " / 31 · " + Math.round(app.brightness * 100 / 31) + "%");
    var brightnessValue = app.brightness === null ? 1 : app.brightness;
    var settingsReady = app.brightness !== null && !app.settingsError;
    var powerEnabled = settingsReady && !app.systemActionPending && app.machine === "idle";
    return '<div class="stack">'+
      strip("<b>LOCAL PI CONTROLS.</b> Brightness, timeout and power actions affect this Raspberry Pi immediately. They are not simulation controls.","warn")+
      (app.settingsError?strip("<b>Settings service unavailable.</b> "+app.settingsError,"danger"):'')+
      card('<div class="split"><h2>Display brightness</h2>'+badge(settingsReady?"LOCAL":"CHECKING",settingsReady?"good":"warn")+'</div>'+
        '<div class="split"><span class="field-label">Panel brightness</span><b id="brightness-label">'+brightness+'</b></div>'+
        '<input type="range" class="slider" min="1" max="31" step="1" value="'+brightnessValue+'" data-input="brightness" aria-label="Display brightness"'+(settingsReady?'':' disabled')+'>'+
        '<div class="choice-row">'+
          button("25%","brightness-8","ghost",settingsReady)+
          button("50%","brightness-16","ghost",settingsReady)+
          button("75%","brightness-23","ghost",settingsReady)+
          button("100%","brightness-31","ghost",settingsReady)+
        '</div>',false)+
      card('<h2>Display inactivity</h2>'+
        '<p class="small muted">After the selected idle period, the HMI dims to a touch-to-resume screen.</p>'+
        '<div class="choice-row">'+
          choose("timeout","0","Off",String(app.timeoutMinutes),settingsReady)+
          choose("timeout","1","1 min",String(app.timeoutMinutes),settingsReady)+
          choose("timeout","5","5 min",String(app.timeoutMinutes),settingsReady)+
          choose("timeout","10","10 min",String(app.timeoutMinutes),settingsReady)+
          choose("timeout","30","30 min",String(app.timeoutMinutes),settingsReady)+
        '</div>',false)+
      card('<div class="split"><h2>Network status</h2>'+button("Refresh","refresh-settings","ghost",!app.settingsLoading)+'</div>'+
        meta([["Connection",app.networkActive],["Interface",app.networkInterface],["Mode",app.networkMode]])+
        '<p class="small muted">Wi-Fi connection changes remain unavailable here until a reliable on-screen keyboard is configured.</p>',false)+
      card('<h2>System power</h2>'+
        meta([["Cutting power",app.machine==="idle"?"Machine state is idle":"Stop or hold before proceeding"],["Scope","The Raspberry Pi only"]])+
        '<div class="btn-row two">'+
          button("Restart Pi","reboot-pi","primary",powerEnabled)+
          button("Power off Pi","poweroff-pi","red",powerEnabled)+
        '</div>'+
        strip("Restart and power off always require confirmation. Ensure any plot or inspection is stopped and the pen is safely parked.","warn"),false)+
      '</div>';
  }
  function renderInspect(){
    var s=app.demo?status():"Service unavailable";
    return '<div class="stack">'+motionBanner()+
      card('<div class="split"><h2>Post-print workflow</h2>'+badge(s,app.demo?"blue":"warn")+'</div>'+
      meta([["Inspection",s],["Submission gate",locked()?"Locked":"Ready (demo)"],["Completed job",app.demo&&app.done?"Verified (demo)":"Unverified"],["Capture queue",app.demo&&app.stage==="awaiting_windows"?"1 pending (demo)":"—"]])+
      progress(app.demo?app.scanProgress:0)+
      '<p class="small muted">Automatic inspection starts only after a confirmed normal program end, Idle, full pen retract and park. Not just 100% of lines sent.</p>',false)+
      '<div class="nav-list">'+
        nav("scan","▤","Scan progress","Center → Theta zero → ring → artwork")+
        nav("sync","⇄","Windows synchronization","Pending packages and safe recovery")+
        nav("results","◎","Inspection results","Executed strokes versus observed ink")+
        nav("profiles","◴","Approved calibration","Current generation and two previous")+
      '</div>'+
      '</div>';
  }
  function renderScan(){
    var steps=["Verify normal job end and pen park","Register bed center optically","Establish B00 optical Theta zero","Inspect bed fiducials","Capture artwork tiles","Queue images for Windows"];
    return '<div class="stack">'+card('<div class="split"><h2>Capture workflow</h2>'+badge(status(),app.demo?"blue":"warn")+'</div>'+
      '<div class="steps">'+steps.map(function(t,i){var complete=app.demo&&app.stage==="awaiting_windows";return '<div class="step '+(complete?"done":"")+'"><span class="step-number">'+(complete?"✓":i+1)+'</span><span>'+t+'</span></div>';}).join("")+'</div>'+
      '<div class="split"><span class="muted">Scan coverage (simulation)</span><b>'+(app.demo?app.scanProgress+"%":"—")+'</b></div>'+
      progress(app.demo?app.scanProgress:0)+
      button("Advance scan simulation","advance-scan","primary",app.demo&&app.stage==="scanning")+
      button("Start manual scan (after verified completion)","manual-scan","ghost",app.demo&&app.machine==="idle"&&app.done&&app.stage==="ready"),false)+
      strip("The scan does not move the pen to correct this drawing. Still images are acquired one at a time and queued for Windows analysis.")+'</div>';
  }
  function renderSync(){
    var pending=app.demo&&(app.stage==="awaiting_windows"||app.stage==="evaluating");
    return '<div class="stack">'+motionBanner()+
      card('<h2>Inspection package</h2>'+
        meta([["Windows",app.demo?"Offline (demo)":"Not connected"],["Queued jobs",pending?"1 (demo)":"None available"],["Transfer",pending?"Pending / evaluating":"Not started"],["Approved profile",app.demo?"CAL-003 (demo)":"Unknown"]])+
        '<p class="small muted">JPEG tiles are retained until a successful committed result or acknowledged cancellation. G-code submissions remain locked while unresolved.</p>',false)+
      card('<h2>Recovery</h2><div class="btn-row two">'+
        button("Retry Sync","retry-sync","primary",app.demo&&app.stage==="awaiting_windows")+
        button("Cancel & Revert","cancel-sync","red",pending)+'</div>'+
        button("Finalize evaluation (demo)","finish-evaluation","ghost",app.demo&&app.stage==="evaluating")+
        strip("Cancellation requires confirmation and preserves the last approved profile; it cannot erase an unresolved transaction without an acknowledgment.","warn"),false)+
      '</div>';
  }
  function renderResults(){
    return '<div class="stack">'+card('<h2>Artwork comparison</h2>'+
      strip("No verified results. Windows must match captured ink against the executed G-code stroke manifest and validate any candidate compensation.")+
      meta([["Missing strokes","—"],["Extra marks","—"],["Path deviation","—"],["Validation","Not available"]])+
      '<p class="small muted">Do not apply a free best-fit alignment that erases global placement errors. Without optional paper markers, some paper slips are ambiguous.</p>',false)+
      nav("profiles","◴","Calibration history","View approved rolling generations")+'</div>';
  }
  function renderProfiles(){
    var names=app.demo?["CAL-003 — approved (demo)","CAL-002 — previous (demo)","CAL-001 — oldest retained (demo)"]:[];
    return '<div class="stack">'+card('<h2>Approved profiles</h2>'+
      (names.length?names.map(function(n,i){return '<div class="split" style="padding:10px 0;border-bottom:1px solid #e1e7f0"><span class="strong">'+n+'</span>'+badge(i===0?"ACTIVE":"ARCHIVED",i===0?"good":"")+'</div>';}).join(""):'<p class="muted">No calibration store connected.</p>')+
      strip("Keep exactly three approved generations: current, N−1, N−2. Failed or canceled candidates do not consume a generation.")+
      '<p class="small muted">Windows fits and validates candidates. The Pi stores only committed approvals and enforces profile/hash checks before accepting new G-code.</p>',false)+'</div>';
  }
  function renderSystem(){
    return '<div class="stack">'+card('<h2>Connection health</h2>'+
      meta([["RP23CNC",app.demo?"Simulated Idle":"Unavailable"],["ESP32-P4",app.demo?"Simulated endpoint":"Unavailable"],["Windows analysis",app.demo?"Disconnected (demo)":"Unavailable"],["Motion authority","Not integrated"],["Last valid status","Not available"],["Emergency stop","External physical circuit"]])+
      strip("This frontend does not connect to grblHAL, send G-code, control motors, capture live frames, or approve calibration. It is an interface preview.","warn"),false)+
      card('<h2>Preview controls</h2>'+
        (app.demo?
          button("Exit demo","exit-demo","ghost",true)+
          button("Simulate verified job completion","sim-complete","primary",app.machine==="run"||app.machine==="hold")+
          button("Reset simulation","reset-demo","ghost",true)
          :button("Try interactive demo","enter-demo","primary",true))+
        '<p class="small muted">Demo transitions are synthetic and do not prove park sensing, machine homing or image accuracy. No demonstration action talks to hardware.</p>',false)+'</div>';
  }
  var renderers = {
    home:renderHome,run:renderRun,feed:renderFeed,jog:renderJog,tools:renderTools,
    register:renderRegister,fiducials:renderFiducials,camera:renderCamera,pen:renderPen,
    frames:renderFrames,settings:renderPiSettings,inspect:renderInspect,scan:renderScan,sync:renderSync,
    results:renderResults,profiles:renderProfiles,system:renderSystem
  };
  function renderTransport(){
    document.getElementById("transport").innerHTML=
      button(canResume()?"Resume":"Start",canResume()?"resume":"start","green",canResume()||canStart())+
      button("Pause","hold","amber",canHold())+
      button("Stop","stop","red",canStop());
  }
  function render(){
    var page=pages[app.page]?app.page:"home";
    var bar = '<div class="brand-mark" aria-hidden="true">XYθ</div>';
    if(page!=="home") bar='<button class="back" type="button" data-action="back" aria-label="Go back">‹</button>';
    document.getElementById("app-bar").innerHTML=bar+
      '<div class="bar-title">'+pages[page][0]+'<div class="bar-sub">XY-Theta Plotter · '+(app.demo?"SIMULATION":"UI PREVIEW")+'</div></div>'+
      badge(app.demo?"DEMO":"OFFLINE",app.demo?"blue":"warn");
    var ax=app.positions;
    document.getElementById("dro").innerHTML=["X","Y","A","Z","B"].map(function(a){
      return '<div class="axis"><small>'+a+(a==="A"?" °":" mm")+'</small><strong>'+(app.demo?ax[a].toFixed(a==="A"?1:2):"—")+'</strong></div>';
    }).join("");
    root.innerHTML=renderers[page]();
    renderTransport();
    document.getElementById("footer").innerHTML='<span>● '+(app.demo?"DEMO — no hardware control":"DISCONNECTED — UI only")+'</span><span>'+(locked()?"Next job locked":"Next job ready (demo)")+'</span>';
    root.scrollTop=0;
    if(page==="settings"||!app.settingsAttempted)refreshPiSettings(false);
  }
  function go(page) {
    if(!pages[page])return;
    app.page=page;
    var depth=(window.history.state&&window.history.state.depth||0)+1;
    window.history.pushState({page:page,depth:depth},"","#/"+page);
    render();
    root.focus({preventScroll:true});
  }
  function back(){
    if(app.page==="home")return;
    if(window.history.state&&window.history.state.depth>0)window.history.back();
    else {
      app.page=pages[app.page][1]||"home";
      window.history.replaceState({page:app.page,depth:0},"","#/"+app.page);
      render();root.focus({preventScroll:true});
    }
  }
  window.addEventListener("popstate",function(){
    var next=window.location.hash.replace(/^#\//,"");
    app.page=pages[next]?next:"home";
    render();
  });
  document.addEventListener("keydown",function(e){
    if(app.splashMode){
      dismissSplash();
      e.preventDefault();
      return;
    }
    resetIdleTimer();
    if(e.key==="Escape"){
      if(app.dialog){app.dialog=null;drawDialog();e.preventDefault();}
      else if(app.page!=="home"){back();e.preventDefault();}
    }
    if(e.key==="Backspace"&&!["INPUT","TEXTAREA"].includes(document.activeElement.tagName)&&app.page!=="home"){
      back();e.preventDefault();
    }
  });
  document.addEventListener("pointerdown",function(e){
    if(app.splashMode){
      e.preventDefault();
      e.stopPropagation();
      dismissSplash();
      return;
    }
    resetIdleTimer();
  });
  var toastTimeout;
  function toast(msg){
    var t=document.getElementById("toast");t.textContent=msg;t.classList.add("visible");
    clearTimeout(toastTimeout);toastTimeout=setTimeout(function(){t.classList.remove("visible");},3000);
  }
  var idleTimer;
  var startupSplashTimer;
  var splashOverlay=document.getElementById("splash-overlay");
  var splashTitle=document.getElementById("splash-title");
  var splashMessage=document.getElementById("splash-message");
  var splashMode=document.getElementById("splash-mode");
  function setSplash(mode) {
    app.splashMode=mode;
    splashOverlay.hidden=false;
    splashOverlay.classList[mode==="timeout"?"add":"remove"]("timeout");
    splashTitle.textContent=mode==="timeout"?"DISPLAY INACTIVITY TIMEOUT":"INITIALIZING OPERATOR INTERFACE";
    splashMessage.textContent=mode==="timeout"?"No controller connection is configured. Motion remains locked.":"Preparing local console";
    splashMode.textContent=app.demo?"SIMULATION · NO HARDWARE CONTROL":"UI PREVIEW · MOTION LOCKED";
    splashOverlay.focus();
  }
  function dismissSplash() {
    clearTimeout(startupSplashTimer);
    app.splashMode=null;
    splashOverlay.hidden=true;
    splashOverlay.classList.remove("timeout");
    resetIdleTimer();
  }
  function showIdle() {
    if (app.dialog || app.systemActionPending) {
      resetIdleTimer();
      return;
    }
    setSplash("timeout");
  }
  function resetIdleTimer() {
    clearTimeout(idleTimer);
    if(app.splashMode==="startup")return;
    if (app.timeoutMinutes > 0) {
      idleTimer=setTimeout(showIdle,app.timeoutMinutes*60000);
    }
  }
  function ask(title,message,proceed,confirmLabel){
    app.dialog={title:title,message:message,proceed:proceed,confirmLabel:confirmLabel||"Confirm"};
    drawDialog();
  }
  function drawDialog(){
    var area=document.getElementById("dialog-root");
    if(!app.dialog){area.innerHTML="";return;}
    area.innerHTML='<div class="scrim" role="presentation"><section class="dialog" role="alertdialog" aria-modal="true" aria-labelledby="dialog-title" aria-describedby="dialog-body">'+
      '<h2 id="dialog-title">'+app.dialog.title+'</h2><p id="dialog-body">'+app.dialog.message+'</p>'+
      '<div class="btn-row two">'+button("Cancel — Do Nothing","dialog-cancel","ghost",true)+button(app.dialog.confirmLabel,"dialog-confirm","red",true)+'</div></section></div>';
    area.querySelector('[data-action="dialog-cancel"]').focus();
  }
  function nextRegister(){
    if(app.stage!=="registering")return;
    app.regIndex+=1;
    if(app.regIndex>=5){app.regIndex=5;app.stage=app.done?"scanning":"ready";toast("Registration sequence finished (simulation only).");}
  }
  function action(name){
    if(name==="back"){back();return;}
    if(name==="camera-page"){go("camera");return;}
    if(name==="open-register"){go("register");return;}
    if(name==="enter-demo"){window.location.search="?demo=1";return;}
    if(name==="exit-demo"){window.location.search="";return;}
    if(name==="refresh-settings"){refreshPiSettings(true);return;}
    if(name.indexOf("brightness-")===0){saveBrightness(Number(name.split("-")[1]));return;}
    if(name==="reboot-pi"){
      if(app.machine!=="idle"){toast("Stop or safely hold the machine before restarting the Pi.");return;}
      ask("Restart the Raspberry Pi?","All local processes will stop and the display will disconnect. Ensure any plot or inspection is stopped, the pen is safely parked, and there is no active machine motion.",function(){requestSystemAction("reboot");},"Restart Pi");
      return;
    }
    if(name==="poweroff-pi"){
      if(app.machine!=="idle"){toast("Stop or safely hold the machine before powering off the Pi.");return;}
      ask("Power off the Raspberry Pi?","The HMI and all local services will stop, and the Touch Display will go dark. Ensure any plot or inspection is stopped and the pen is safely parked.",function(){requestSystemAction("poweroff");},"Power off");
      return;
    }
    if(!app.demo){toast("Unavailable: no motion supervisor is connected.");return;}
    if(name==="dialog-cancel"){app.dialog=null;drawDialog();return;}
    if(name==="dialog-confirm"){var f=app.dialog&&app.dialog.proceed;app.dialog=null;drawDialog();if(f)f();render();return;}
    if(name==="start"&&canStart()){
      app.machine="run";app.stage="drawing";app.done=false;toast("Simulated drawing started.");
    }else if(name==="hold"&&canHold()){
      app.machine="hold";app.stage="held";toast("Simulated feed hold.");
    }else if(name==="resume"&&canResume()){
      app.machine="run";app.stage="drawing";toast("Simulated run resumed.");
    }else if(name==="stop"&&canStop()){
      ask("Stop the current job?","This is a simulation. A real job stop would require sender acknowledgment and would not count as a completed print.",function(){
        app.machine="idle";app.stage="ready";app.done=false;app.progress=0;toast("Simulated job stopped.");
      });
    }else if(name==="feed-down"||name==="feed-up"||name==="feed-reset"){
      app.override=name==="feed-reset"?100:Math.max(10,Math.min(200,app.override+(name==="feed-down"?-10:10)));
      toast("Override preview: "+app.override+"% (not sent)");
    }else if(name==="home-park"||name==="pen-park"){
      if(canJog())ask(name==="home-park"?"Home & Register?":"Lift & Park Pen?","Controller-owned macros and toolhead clearance must be verified before this can operate real hardware. Demo will not move anything.",function(){toast("Protected operation simulated only.");});
    }else if(name==="start-register"&&app.machine==="idle"&&app.stage==="ready"){
      ask("Begin optical registration?","The bed and camera would move. Completed artwork must remain installed, with the outer fiducial ring uncovered. In demo, no motion occurs.",function(){app.stage="registering";app.regIndex=0;toast("Registration simulation started.");});
    }else if(name==="advance-register"){
      nextRegister();
    }else if(name==="advance-scan"&&app.stage==="scanning"){
      app.scanProgress=Math.min(100,app.scanProgress+25);
      if(app.scanProgress===100){app.stage="awaiting_windows";toast("Image package queued (simulation only).");}
    }else if(name==="manual-scan"&&app.done&&app.machine==="idle"&&app.stage==="ready"){
      ask("Inspect finished artwork?","Only safe after the entire program ends normally, full pen retract is confirmed, and the controller is Idle. Cancel does nothing.",function(){app.stage="registering";app.regIndex=0;app.scanProgress=0;});
    }else if(name==="retry-sync"&&app.stage==="awaiting_windows"){
      app.stage="evaluating";toast("Simulated Windows evaluation started.");
    }else if(name==="finish-evaluation"&&app.stage==="evaluating"){
      app.stage="ready";app.done=false;toast("Simulated outcome acknowledged; job gate released.");
    }else if(name==="cancel-sync"&&(app.stage==="awaiting_windows"||app.stage==="evaluating")){
      ask("Cancel sync & revert?","Discard this unresolved inspection transaction only after explicit acknowledgment. Preserve the last approved calibration profile. In demo, this changes simulated state only.",function(){app.stage="ready";app.done=false;app.scanProgress=0;toast("Simulated cancellation acknowledged.");});
    }else if(name==="sim-complete"&&(app.machine==="run"||app.machine==="hold")){
      ask("Simulate verified completion?","This test bypasses hardware validation ONLY in demo mode. A real completed print requires successful M2, drained sender, Idle, pen full-retract and park acknowledgments.",function(){
        app.machine="idle";app.done=true;app.progress=100;app.stage="registering";app.regIndex=0;app.scanProgress=0;toast("Post-print optical registration simulation started.");
      });
    }else if(name==="reset-demo"){
      window.location.search="?demo=1";return;
    }
    render();
  }
  root.addEventListener("click",function(e){
    var b=e.target.closest("[data-page], [data-action], [data-choose], [data-jog]");
    if(!b||b.disabled)return;
    if(b.dataset.page){go(b.dataset.page);return;}
    if(b.dataset.choose){
      var type=b.dataset.choose,val=b.dataset.value;
      if(type==="jogSystem")app.jogSystem=val;
      else if(type==="jogStep")app.jogStep=Number(val);
      else if(type==="cameraMode")app.cameraMode=val;
      else if(type==="timeout"){saveTimeout(val);}
      render();return;
    }
    if(b.dataset.jog){
      if(!canJog())return;
      var dir=b.dataset.jog,axis=app.jogSystem==="pen"?(dir==="left"||dir==="right"?"X":"Y"):
        app.jogSystem==="camera"?(dir==="left"||dir==="right"?"Z":"B"):"A";
      var sign=(dir==="left"||dir==="down")?-1:1;
      app.positions[axis]+=sign*app.jogStep;
      toast("Simulated "+axis+" jog only; no motor movement.");
      render();return;
    }
    if(b.dataset.action)action(b.dataset.action);
  });
  document.getElementById("app-bar").addEventListener("click",function(e){
    var b=e.target.closest("[data-action]");
    if(b)action(b.dataset.action);
  });
  document.getElementById("transport").addEventListener("click",function(e){
    var b=e.target.closest("[data-action]");
    if(b&&!b.disabled)action(b.dataset.action);
  });
  document.getElementById("dialog-root").addEventListener("click",function(e){
    var b=e.target.closest("[data-action]");
    if(b)action(b.dataset.action);
  });
  root.addEventListener("input",function(e){
    if(e.target.dataset.input==="override"&&app.demo){
      app.override=Number(e.target.value);
      var label=document.getElementById("override-label");if(label)label.textContent=app.override+"%";
    }else if(e.target.dataset.input==="brightness"){
      app.brightness=Number(e.target.value);
      var brightnessLabel=document.getElementById("brightness-label");
      if(brightnessLabel)brightnessLabel.textContent=app.brightness+" / 31 · "+Math.round(app.brightness*100/31)+"%";
    }
  });
  root.addEventListener("change",function(e){
    if(e.target.dataset.input==="override"&&app.demo)toast("Override preview: "+app.override+"% (not sent)");
    else if(e.target.dataset.input==="brightness")saveBrightness(app.brightness);
  });
  var initial=window.location.hash.replace(/^#\//,"");
  app.page=pages[initial]?initial:"home";
  window.history.replaceState({page:app.page,depth:0},"","#/"+app.page);
  render();
  setSplash("startup");
  startupSplashTimer=setTimeout(function(){
    if(app.splashMode==="startup")dismissSplash();
  },4000);
})();
