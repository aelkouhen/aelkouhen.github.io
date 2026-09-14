(function(){
  const log=[]; const ok=m=>log.push("PASS "+m);
  window.confirm=()=>true; window.alert=m=>{window.__alert=m;}; window.prompt=m=>{window.__prompt=m;return "bending it because the customer moved the date";};
  const click=sel=>{const e=document.querySelector(sel); if(!e) throw new Error("no element "+sel); e.click(); return e;};
  try{
    DB={deals:[],role:"AE",lastDeal:null}; ui={tab:"phase",role:"AE",dealId:null};
    const d=newDeal("Click Test"); render();
    // tab navigation by click
    click('[data-tab="med"]');
    if(ui.tab!=="med") throw new Error("tab click");
    ok("tab click");
    // cycle a meddpicc state 0 -> 1 -> 2 -> 0
    click('[data-med="DC"]'); if(d.med.DC.s!==1) throw new Error("cycle 1");
    click('[data-med="DC"]'); if(d.med.DC.s!==2) throw new Error("cycle 2");
    click('[data-med="DC"]'); if(d.med.DC.s!==0) throw new Error("wrap to 0");
    ok("meddpicc state cycles and wraps");
    // tick a phase check
    click('[data-tab="phase"]');
    const first=document.querySelector("[data-check]");
    first.click();
    if(!d.checks[first.dataset.check]) throw new Error("check not stored");
    if(phaseStats(d).done!==1) throw new Error("check count");
    ok("exit check toggles and counts");
    // advance with open checks -> prompt path records an override
    click("#phaseFwd");
    if(d.phase!==2) throw new Error("did not advance, phase "+d.phase);
    if(d.overrides.length!==1) throw new Error("override not logged");
    if(!/still open/.test(window.__prompt||"")) throw new Error("prompt text wrong");
    ok("advance with open checks logs a deliberate bend");
    // back
    click("#phaseBack"); if(d.phase!==1) throw new Error("back");
    ok("phase back");
    // hard rule blocks advance
    d.phase=3; d.poc.needed="yes"; render();
    const before=d.phase; click("#phaseFwd");
    if(d.phase!==before) throw new Error("hard rule did not block");
    if(!/does not bend/.test(window.__alert||"")) throw new Error("hard rule alert text");
    ok("hard rule blocks the advance button");
    // satisfy it, then advance
    d.checks["p3g"]=true; render(); click("#phaseFwd");
    if(d.phase!==4) throw new Error("advance after hard rule satisfied");
    ok("advance allowed once criteria agreed");
    // brief send with missing fields -> confirm stubbed true
    d.phase=2; ui.tab="brief"; render();
    click('[data-bstatus="sent"]');
    if(d.brief.status!=="sent") throw new Error("brief status");
    ok("brief send");
    // add + remove attendee
    click("#addAtt"); if(d.brief.attendees.length!==1) throw new Error("add attendee");
    click("[data-attdel]"); if(d.brief.attendees.length!==0) throw new Error("remove attendee");
    ok("attendee add/remove");
    // SA returns the brief
    ui.role="SA"; render();
    document.getElementById("b_note").value="No named attendees and no objective.";
    click('[data-bstatus="returned"]');
    if(d.brief.status!=="returned"||!d.brief.note) throw new Error("return path");
    render();
    if(!/sent back by the SA/.test(document.getElementById("banners").innerHTML)) throw new Error("returned banner");
    ok("SA sends the brief back, AE sees the reason");
    // debrief add + delete
    ui.role="AE"; ui.tab="debrief"; render();
    document.getElementById("db_learn").value="They have three API gateways, not one.";
    document.getElementById("db_next").value="Architecture session";
    click("#addDebrief");
    if(d.debriefs.length!==1) throw new Error("debrief add");
    click("[data-dbdel]");
    if(d.debriefs.length!==0) throw new Error("debrief delete");
    ok("debrief add and delete");
    // poc checkbox
    ui.tab="poc"; d.poc.needed="yes"; render();
    document.getElementById("p_agreed").click();
    if(!d.poc.agreed) throw new Error("poc agreed checkbox");
    ok("poc agreed checkbox clears the gate");
    // persistence round-trip
    save(); const reread=JSON.parse(localStorage.getItem(KEY));
    if(!reread.deals.length||reread.deals[0].name!=="Click Test") throw new Error("persistence");
    ok("localStorage round-trip");
    // delete deal
    click("#delDeal"); if(DB.deals.length!==0) throw new Error("delete deal");
    if(!document.querySelector("#newDeal2")) throw new Error("back to empty state");
    ok("delete deal returns to empty state");
    // rules + data dialogs
    click("#rulesBtn"); if(!document.querySelector("#rulesDlg .rules-sec")) throw new Error("rules dialog");
    document.getElementById("rulesDlg").close();
    click("#dataBtn"); if(!document.querySelector("#expAll")) throw new Error("data dialog");
    document.getElementById("dataDlg").close();
    ok("rules and data dialogs");
    // theme toggle
    click("#themeBtn");
    if(document.documentElement.getAttribute("data-theme")!=="dark") throw new Error("theme");
    click("#themeBtn");
    if(document.documentElement.getAttribute("data-theme")!=="light") throw new Error("theme back");
    ok("theme toggle both ways");
    // role toggle
    click("#roleSA"); if(ui.role!=="SA") throw new Error("role");
    click("#roleAE"); if(ui.role!=="AE") throw new Error("role back");
    ok("role toggle both ways");
    // share link round trip
    const d2=newDeal("Share Me"); d2.med.M={s:2,note:"baseline 11 days"};
    const link=shareLink(d2);
    if(!/#deal=/.test(link)) throw new Error("share link shape");
    const back=JSON.parse(b64dec(link.split("#deal=")[1]));
    if(back.name!=="Share Me"||back.med.M.note!=="baseline 11 days") throw new Error("share link payload");
    ok("share link round trip ("+link.length+" chars)");
  }catch(e){ log.push("FAIL "+e.message+" | "+(e.stack||"").split("\n")[1]); }
  document.body.insertAdjacentHTML("beforeend","<pre id=RESULT>"+log.join("\n")+"</pre>");
})();
