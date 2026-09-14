(function(){
  const log=[];
  function ok(m){log.push("PASS "+m);}
  try{
    // start clean
    DB={deals:[],role:"AE",lastDeal:null}; ui={tab:"phase",role:"AE",dealId:null};
    render();
    if(!document.querySelector("#newDeal2")) throw new Error("empty state missing");
    ok("empty state");
    const d=newDeal("Fidelity Bank APIM");
    d.company="Fidelity Bank"; d.ae="A. Kouhen"; d.sa="S. Arch"; d.value="$240k"; d.closeDate="2026-09-17";
    ui.tab="phase"; render();
    if(!document.querySelector(".meter-seg.now")) throw new Error("meter missing");
    if(document.querySelectorAll("[data-check]").length!==PHASES[0].checks.length) throw new Error("checks count");
    ok("phase panel");
    // banners: 8 unknown letters -> warning
    if(!document.querySelector(".banner.warning")) throw new Error("expected blanks warning");
    ok("blank-meddpicc banner");
    // cycle every meddpicc letter to validated
    MEDDPICC.forEach(m=>{d.med[m.k]={s:2,note:"evidence"}});
    ui.tab="med"; render();
    if(document.querySelectorAll("[data-med]").length!==8) throw new Error("med grid");
    if(medStats(d).validated!==8) throw new Error("medStats");
    ok("meddpicc panel + stats");
    // brief with short notice
    const t=new Date(); t.setDate(t.getDate()+1);
    d.brief.tier="tailored"; d.brief.meetingDate=t.toISOString().slice(0,10);
    d.brief.attendees=[{name:"N",title:"T",decides:"budget",depth:"Architect",stance:"Friendly"}];
    d.brief.objective="Confirm ranked criteria"; d.brief.agenda="0-5 AE";
    ui.tab="brief"; render();
    const nc=noticeCheck(d);
    if(!nc||!nc.short) throw new Error("short notice not detected: "+JSON.stringify(nc));
    if(!document.querySelector(".banner.critical")) throw new Error("short notice banner missing");
    if(document.querySelectorAll("[data-att]").length!==5) throw new Error("attendee row fields");
    ok("brief panel + short-notice detection ("+nc.wd+" wd)");
    // SA role view
    ui.role="SA"; render();
    if(!document.querySelector('[data-bstatus="returned"]')) throw new Error("SA triage controls missing");
    ok("SA role triage controls");
    ui.role="AE";
    // debriefs
    d.debriefs.push({id:"x1",date:"2026-09-01",outcome:"Hit it",learned:"L",changed:"C",next:"N",owner:"AE",due:"2026-09-20"});
    ui.tab="debrief"; render();
    if(!document.querySelector("[data-dbdel]")) throw new Error("debrief history missing");
    ok("debrief panel");
    // poc hard rule
    d.phase=3; d.poc.needed="yes"; d.poc.start="2026-09-01"; d.poc.end="2026-11-01";
    ui.tab="poc"; render();
    if(!document.querySelector("#p_agreed")) throw new Error("poc criteria form missing");
    if(!/does not bend/.test(document.getElementById("banners").innerHTML)) throw new Error("poc hard-rule banner missing");
    if(!/Over the four week timebox/.test(document.getElementById("panel").innerHTML)) throw new Error("timebox warning missing");
    const hard=phaseStats(d).hardOpen;
    if(hard.length!==1) throw new Error("hard rule not open, got "+hard.length);
    ok("poc panel + hard rule + timebox");
    // summary + markdown
    ui.tab="summary"; render();
    const md=summaryMarkdown(d);
    if(md.indexOf("Fidelity Bank")<0||md.indexOf("MEDDPICC")<0) throw new Error("summary markdown thin");
    if(briefMarkdown(d).indexOf("| Name | Title |")<0) throw new Error("brief markdown table missing");
    if(pocMarkdown(d).indexOf("must not start")<0) throw new Error("poc markdown gate text missing");
    ok("markdown export x3 ("+md.split("\n").length+" summary lines)");
    // all phases render
    for(let i=1;i<=4;i++){d.phase=i;["phase","med","brief","debrief","poc","summary"].forEach(tb=>{ui.tab=tb;render();if(document.getElementById("panel").innerHTML.length<50)throw new Error("empty panel "+tb+" phase "+i);});}
    ok("all 4 phases x 6 tabs render");
    // working days maths
    if(workingDaysUntil(null)!==null) throw new Error("wd null");
    ok("working-day helper");
    // rules content present
    if(Object.keys(RULES).length!==5) throw new Error("rules sections");
    ok("rules content");
  }catch(e){ log.push("FAIL "+e.message); }
  document.title="RESULTS";
  document.body.insertAdjacentHTML("beforeend","<pre id=RESULT>"+log.join("\n")+"</pre>");
})();
