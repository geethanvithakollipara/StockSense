import { useState, useEffect } from "react";
import "./App.css";



/* =========================================================
   BACKEND CONNECTION LAYER
   Point API_BASE at your running server (see server.js).
   Every screen calls the API first; if the request fails
   (no backend running, network error, etc.) it falls back
   to local demo data so the UI still works standalone.
========================================================= */
const API_BASE = window.STOCKSENSE_API_BASE || "http://localhost:5000/api";

async function apiFetch(path, options={}){
  try{
    const res = await fetch(API_BASE+path, {
      headers:{"Content-Type":"application/json", ...(options.headers||{})},
      ...options,
    });
    if(!res.ok) throw new Error("HTTP "+res.status);
    return await res.json();
  }catch(err){
    return null; // caller falls back to demo data
  }
}

function useApiData(path, fallback){
  const [data,setData] = useState(fallback);
  const [live,setLive] = useState(false);
  useEffect(()=>{
    let cancelled=false;
    apiFetch(path).then(d=>{
      if(cancelled) return;
      if(d){ setData(d); setLive(true); } else { setLive(false); }
    });
    return ()=>{cancelled=true;};
  },[path]);
  return [data,live];
}

function ConnBadge({live}){
  return (
    <span className="conn">
      <span className="dot2" style={{background: live? "var(--ok)":"var(--muted)"}}/>
      {live? "API connected" : "Demo data"}
    </span>
  );
}

/* ---------- fallback / demo data (used until the backend responds) ---------- */
const FALLBACK_DASHBOARD = {
  kpis:{stock:"4,820",stockDelta:"▲ 12%",shortages:"14",shortagesDelta:"3 urgent",
    receipts:"8",receiptsDelta:"2 arriving today",deliveries:"19",deliveriesDelta:"6 ready · Carrier"},
  zones:[["Zone A · Bays","8/10 Active · Bay Storage"],["Dock 1","Cold Storage"]],
  manifests:[
    ["REC-2024-0088","Apex Industrial Metals Ltd.","100 kg High-Grade Steel Rods","Bay 4 · North","Ready","ok"],
    ["DEL-2024-0142","10 Ergonomic Mesh Chairs","Acme Corp Logistics · Order #PO-9140","Dock 1","Waiting Pickup","warn"],
    ["TRF-2024-0033","50 Circuit Boards MCU-X9","Main Store → Production Rack B","Logged 14:23 PM","In Transit","warn"],
    ["ADJ-2024-0012","-3 kg Damaged Steel","Scrap write-off · Approved by supervisor","","Done","muted"],
  ],
};
const FALLBACK_PRODUCTS = {
  kpis:{skus:"342",low:"14!",facilities:"4 Hubs"},
  products:[
    ["High-Grade Steel Rods","WSTL-ROD-0102","Available count 100 kg · 2 Locations",null,"ok","In Stock",["Transfer","Adjust","Details"]],
    ["OmniTech Components","MFRN-CHR-882","Min rule 15 pcs · Warehouse Zone B1 5pcs, Downtown Showroom 3pcs","8 pcs","bad","Low Stock",["View Locations","Reorder Now"]],
    ["Industrial Circuit Board PCB-X","MFRLE-PCB-990","Clean Room Rack B · Last cycle count 2h ago","240 pcs","ok","In Stock · Lead time 1d",["Transfer","Details"]],
    ["Heavy Duty Corrugated Boxes 12x12","MFPKG-BOX-1212","Restocking Alert triggered","0 pcs","bad","Out of Stock",["Reorder Now"]],
  ],
};
const FALLBACK_OPERATIONS = {
  items:[
    ["PREC-8842","PO-9812 · Apex Industrial Metals Ltd.","100 kg Steel Rods · SKU-STL-01 · Validated by Alex R.","+100 Units · Ledger","Done","ok"],
    ["PREC-8845","PO-9817 · OmniTech Components","25x Power Supply Units · SKU-PSU-450 · 0/25 Checked","Today, 2:00 PM · Receiving Dock 1","Waiting","warn"],
    ["PREC-8848","INTERNAL NOTE · Global Pack Solutions","500x Corrugated Boxes 12x12 · SKU-BOX-012","Tomorrow, 09:00 AM · Warehouse B","Draft","muted"],
  ],
  steps:[["Create Receipt","Log reference PO"],["Assign Items","Supplier & SKU"],
    ["Count & Scan","Input quantities"],["Validate","Auto-updates stock"]],
};
const FALLBACK_TRANSFERS = {
  lifecycle:[["Step 1 · Vendor → Main","Done","ok"],["Step 2 · Main → Production","Ready to Move","warn"]],
  manifests:[
    ["#TRF-9021 · Standard Move","Ready","warn","High-Grade Steel Rods · 30 kg","SOURCE: Main WH (Rack 04-A) → Production Floor (Rack P3)"],
    ["#TRF-9018 · Refrigerated","Delivered Batch 1","ok","Thermal Paste Syringes · 150 units","Cold Vault (Zone C) → Rack B1"],
  ],
};
const FALLBACK_SETTINGS = {
  profile:{name:"Alex Rivera",meta:"Lead Inventory Manager · EMP-4081 · WH-2 Sector A"},
  ops:[["Critical Stock Alerts","Notify when safety stock dips under 15%",true],
    ["Auto-Reconcile on Doc Transfer","Update ledger the instant scans confirm",true],
    ["Strict 3-Step Count Verification","Enforce secondary supervisor sign-off above $500",false]],
  sec:[["Biometric Unlock","Expose password during active shift",true],
    ["Offline Manifest Cache","Last synced 3 minutes ago",true]],
};

function Item({name,meta,right,tone="muted",children}){
  return (
    <div className="item">
      <div><div className="name">{name}</div>{meta && <div className="meta">{meta}</div>}{children}</div>
      {right && <span className={"pill "+tone}>{right}</span>}
    </div>
  );
}

function Toggle({on}){ return <div className={"toggle "+(on?"on":"off")}><div className="dot"/></div>; }

/* ---------- LOGIN ---------- */
function Login({onLogin,goSignup}){
  const [id,setId]=useState("");
  const [pw,setPw]=useState("");
  const [busy,setBusy]=useState(false);
  const [err,setErr]=useState("");

  async function submit(){
    setBusy(true); setErr("");
    const result = await apiFetch("/auth/login", {
      method:"POST",
      body: JSON.stringify({email:id, password:pw}),
    });
    setBusy(false);
    // No backend reachable -> still let the demo proceed with local session.
    if(!result){ onLogin({demo:true, user:{name:id.split("@")[0], email:id}}); return; }
    if(result.token){ onLogin({demo:false, user:result.user}); }
    else { setErr(result.message || "Invalid credentials."); }
  }

  return (
    <div className="body" style={{display:"flex",flexDirection:"column",justifyContent:"center",minHeight:"100%"}}>
      <div style={{textAlign:"center",marginBottom:18}}>
        <div style={{width:52,height:52,borderRadius:14,background:"linear-gradient(135deg,#3d84ff,#7c5cff)",
          margin:"0 auto 12px",display:"flex",alignItems:"center",justifyContent:"center",fontWeight:800,fontSize:22}}>S</div>
        <div style={{fontSize:19,fontWeight:700}}>StockSense</div>
        <div style={{fontSize:10.5,color:"var(--muted)",letterSpacing:.4,marginTop:2}}>ENTERPRISE INVENTORY &amp; WAREHOUSE SYSTEM</div>
        <div className="badge-top" style={{marginTop:10}}>WAREHOUSE STAFF &amp; MANAGER PORTAL</div>
      </div>
      <div className="field"><label>Work email or employee ID</label>
        <input value={id} onChange={e=>setId(e.target.value)} placeholder="you@stocksense.co / EMP-4081"/></div>
      <div className="field">
        <div style={{display:"flex",justifyContent:"space-between"}}><label>Password</label>
          <span style={{fontSize:10.5,color:"var(--accent)"}}>Forgot Password? (OTP Reset)</span></div>
        <input type="password" value={pw} onChange={e=>setPw(e.target.value)}/>
      </div>
      {err && <div style={{color:"var(--bad)",fontSize:11,marginBottom:10}}>{err}</div>}
      <button className="btn" disabled={busy}
        style={{alignSelf:"center",flex:"0 0 auto",width:"auto",padding:"7px 16px",fontSize:11,marginBottom:14,opacity:busy?.6:1}}
        onClick={submit}>{busy? "Signing in…" : "Sign In to Warehouse →"}</button>
      <div style={{textAlign:"center",fontSize:10,color:"var(--muted)",margin:"4px 0 14px"}}>— OR FAST TAP —</div>
      <button className="btn ghost"
        style={{alignSelf:"center",flex:"0 0 auto",width:"auto",padding:"7px 16px",fontSize:11,marginBottom:18}}>⌗ Scan Badge / RFID Card</button>
      <div style={{textAlign:"center",fontSize:11.5,color:"var(--muted)"}}>
        Don't have an account? <span style={{color:"var(--accent)"}} onClick={goSignup}>Sign Up / Request Access</span>
      </div>
      <div style={{textAlign:"center",fontSize:9.5,color:"var(--muted)",marginTop:16}}>🔒 256-bit Encrypted · SOC2 Type II Certified</div>
    </div>
  );
}

/* ---------- SIGNUP ---------- */
function Signup({goLogin}){
  const [role,setRole]=useState(0);
  const [form,setForm]=useState({name:"",email:"",empId:"",hub:"",pw:"",pw2:""});
  const [status,setStatus]=useState("");
  const roles=[["Warehouse Operator / Picker","Scanning, picking, dispatch packing and dock work"],
    ["Inventory Manager","Stock reconciliation, purchase receipts, relocations"],
    ["Auditor / Supervisor","Quality control, shrinkage audits, compliance logs"]];
  const set = k => e => setForm({...form,[k]:e.target.value});

  async function submit(){
    setStatus("Creating account…");
    const result = await apiFetch("/auth/signup", {
      method:"POST",
      body: JSON.stringify({...form, role: roles[role][0]}),
    });
    setStatus(result ? "Account created — check your email for the OTP." : "Saved locally (backend offline) — demo mode.");
  }

  return (
    <div className="body">
      <div className="badge-top">FACILITY ONBOARDING</div>
      <div style={{fontSize:17,fontWeight:700,marginBottom:2}}>Create Operator Account</div>
      <div style={{fontSize:11,color:"var(--muted)"}}>Join your facility's inventory management system and access real-time manifest tracking</div>
      <div style={{fontSize:10,color:"var(--muted)",marginTop:10}}>STEP 1 OF 2 · Profile &amp; Facility Assignment</div>
      <div className="progress"><div style={{width:"50%"}}/></div>

      <div className="sec-title">Personal &amp; Facility Details</div>
      <div className="field"><label>Full legal name</label><input value={form.name} onChange={set("name")} placeholder="e.g. Marcus Kelly"/></div>
      <div className="field"><label>Work email</label><input value={form.email} onChange={set("email")} placeholder="m.kelly@logistics.com"/></div>
      <div className="field"><label>Employer ID</label><input value={form.empId} onChange={set("empId")} placeholder="E.G. EMP-8824"/></div>
      <div className="field"><label>Primary warehouse hub</label><input value={form.hub} onChange={set("hub")} placeholder="Select assigned location..."/></div>

      <div className="sec-title">Assigned Role · Access clearance</div>
      {roles.map(([t,d],i)=>(
        <div key={t} className={"role-card"+(role===i?" sel":"")} onClick={()=>setRole(i)}>
          <div className="name" style={{fontSize:12}}>{t}</div>
          <div className="meta">{d}</div>
        </div>
      ))}

      <div className="sec-title">Security &amp; Credentials</div>
      <div className="field"><label>Operator password</label><input type="password" value={form.pw} onChange={set("pw")} placeholder="Enter secure password"/></div>
      <div className="field"><label>Confirm password</label><input type="password" value={form.pw2} onChange={set("pw2")} placeholder="Re-type password"/></div>
      <div className="req">SECURITY REQUIREMENTS</div>
      <div className="req">✓ 8+ characters length</div>
      <div className="req">✓ At least 1 numerical char</div>
      <div className="req">✓ 1 uppercase letter (A–Z)</div>

      <label style={{display:"flex",gap:8,fontSize:10.5,color:"var(--muted)",margin:"14px 0"}}>
        <input type="checkbox" style={{width:"auto",marginTop:2}}/>
        I certify that I have read and agree to the Warehouse Security &amp; Inventory Handling SOPs and OSHA regulatory requirements.
      </label>
      {status && <div style={{fontSize:11,color:"var(--accent)",marginBottom:10}}>{status}</div>}
      <button className="btn" style={{width:"100%",padding:11,marginBottom:12}} onClick={submit}>Create Account &amp; Verify OTP →</button>
      <div style={{textAlign:"center",fontSize:11.5,color:"var(--muted)"}}>
        Already registered with StockSense? <span style={{color:"var(--accent)"}} onClick={goLogin}>Sign in instead</span>
      </div>
    </div>
  );
}

/* ---------- HEADER ---------- */
function Head({title,sub,badge,live,user}){
  return (
    <div className="head">
      <div className="titles">
        <div className="app-name">{title}</div>
        <div className="app-sub">{sub}</div>
      </div>
      <div className="head-icons">
        <ConnBadge live={live}/>
        {badge && <span className="pill ok" style={{fontWeight:700}}>{badge}</span>}
        <div className="icon-btn">🔔</div>
        <div className="avatar">{user?.name ? user.name.split(" ").map(n=>n[0]).join("").slice(0,2).toUpperCase() : (user?.email ? user.email[0].toUpperCase() : "U")}</div>
      </div>
    </div>
  );
}

/* ---------- DASHBOARD ---------- */
function Dashboard({user}){
  const [data,live] = useApiData("/dashboard", FALLBACK_DASHBOARD);
  const {kpis,zones,manifests} = data;
  return (<>
    <Head title="StockSense" sub={user?.email || "Main Hub (WH-01)"} live={live} user={user}/>
    <div className="body">
      <div className="kpi-row">
        <div className="kpi"><div className="l">Stock in hand</div><div className="v">{kpis.stock}</div><div className="d up">{kpis.stockDelta}</div></div>
        <div className="kpi"><div className="l">Shortages</div><div className="v badc">{kpis.shortages}</div><div className="d badc">{kpis.shortagesDelta}</div></div>
        <div className="kpi"><div className="l">Receipts</div><div className="v">{kpis.receipts}</div><div className="d warnc">{kpis.receiptsDelta}</div></div>
        <div className="kpi"><div className="l">Deliveries</div><div className="v">{kpis.deliveries}</div><div className="d warnc">{kpis.deliveriesDelta}</div></div>
      </div>
      <div className="sec-title">Live Yard &amp; Storage</div>
      <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:8,marginBottom:6}}>
        {zones.map(([n,d])=>(
          <div className="card" style={{marginBottom:0}} key={n}><div className="name" style={{fontSize:12}}>{n}</div><div className="meta">{d}</div></div>
        ))}
      </div>
      <div className="chips">
        {["All Ops","Receipts (8)","Waiting (10)","Ready (5)","Done (6)"].map((c,i)=>(
          <div key={c} className={"chip"+(i===0?" active":"")}>{c}</div>
        ))}
      </div>
      <div className="sec-title" style={{marginTop:0}}>Recent Manifests</div>
      <div className="card">
        {manifests.map(m=>(
          <Item key={m[0]} name={m[0]} right={m[4]} tone={m[5]} meta={<>{m[1]}<br/>{m[2]} {m[3] && "· "+m[3]}</>}/>
        ))}
      </div>
      <div className="card" style={{textAlign:"center"}}>
        <div className="name" style={{marginBottom:6}}>Ready for Scan</div>
        <div className="meta" style={{marginBottom:10}}>Trigger physical scanner or open camera</div>
        <button className="btn" style={{width:"100%"}}>📷 Trigger Barcode Scanner</button>
      </div>
    </div>
  </>);
}

/* ---------- PRODUCTS ---------- */
function Products(){
  const [data,live] = useApiData("/products", FALLBACK_PRODUCTS);
  const {kpis,products} = data;
  return (<>
    <Head title="Products Catalog" sub="Main Warehouse" live={live}/>
    <div className="body">
      <div className="kpi-row">
        <div className="kpi"><div className="l">Total SKUs</div><div className="v">{kpis.skus}</div></div>
        <div className="kpi"><div className="l">Low Stock</div><div className="v badc">{kpis.low}</div></div>
        <div className="kpi"><div className="l">Facilities</div><div className="v">{kpis.facilities}</div></div>
      </div>
      <div className="chips">
        {["All Categories","Raw Materials","Electronics","Furniture"].map((c,i)=>(
          <div key={c} className={"chip"+(i===0?" active":"")}>{c}</div>
        ))}
      </div>
      <button className="btn" style={{width:"100%",marginBottom:12}}>+ Add Product</button>
      {products.map(([name,sku,meta,stock,tone,status,actions])=>(
        <div className="card" key={sku}>
          <div style={{display:"flex",justifyContent:"space-between"}}>
            <div><div className="name">{name}</div><div className="meta">{sku}</div></div>
            {stock && <div style={{textAlign:"right"}}><div className="name">{stock}</div></div>}
          </div>
          <div style={{marginTop:6}}><span className={"pill "+tone}>{status}</span></div>
          <div className="meta" style={{marginTop:6}}>{meta}</div>
          <div className="row-actions">
            {actions.map((a,i)=>(<button key={a} className={"btn"+(i===0?"":" ghost")} style={{fontSize:10.5,padding:"6px 8px"}}>{a}</button>))}
          </div>
        </div>
      ))}
      <div className="card" style={{textAlign:"center"}}>
        <div className="meta" style={{marginBottom:8}}>End of Filtered SKUs — all monitored inventories are synchronized with real-time scanners.</div>
        <button className="btn ghost" style={{width:"100%"}}>⟳ Pull Fresh Barcode Cache</button>
      </div>
    </div>
  </>);
}

/* ---------- OPERATIONS ---------- */
function Operations(){
  const [tab,setTab]=useState(0);
  const [data,live] = useApiData("/operations", FALLBACK_OPERATIONS);
  const {items,steps} = data;
  return (<>
    <Head title="Inventory Logistics" sub="Operations Hub" badge="● Live Sync" live={live}/>
    <div className="body">
      <div className="chips">
        {["Receipts (8)","Deliveries (19)","Move (5)"].map((c,i)=>(
          <div key={c} className={"chip"+(tab===i?" active":"")} onClick={()=>setTab(i)}>{c}</div>
        ))}
      </div>
      <div className="chips">
        {["All Active","Waiting","Ready","Done","Draft"].map((c,i)=>(
          <div key={c} className={"chip"+(i===0?" active":"")}>{c}</div>
        ))}
      </div>
      <div className="card">
        {items.map(it=>(
          <Item key={it[0]} name={it[0]+" · "+it[1]} right={it[4]} tone={it[5]} meta={<>{it[2]}<br/>{it[3]}</>}/>
        ))}
      </div>
      <div className="sec-title">Standard Receipts Workflow</div>
      <div className="card">
        {steps.map(([t,d],i)=>(
          <Item key={t} name={(i+1)+". "+t} meta={d} right={"Step "+(i+1)} tone="muted"/>
        ))}
        <button className="btn" style={{width:"100%",marginTop:10}}>+ Create Receipt</button>
      </div>
    </div>
  </>);
}

/* ---------- TRANSFERS ---------- */
function Transfers(){
  const [data,live] = useApiData("/transfers", FALLBACK_TRANSFERS);
  const {lifecycle,manifests} = data;
  return (<>
    <Head title="Internal Logistics" sub="Warehouse Flow &amp; Routing" badge="2 Active Tasks" live={live}/>
    <div className="body">
      <div className="sec-title">Warehouse Flow Lifecycle</div>
      <div className="card">
        {lifecycle.map(([n,s,t])=>(<Item key={n} name={n} right={s} tone={t}/>))}
      </div>
      <div className="sec-title">Transfer Manifests</div>
      <div className="card">
        <Item name={manifests[0][0]} tone={manifests[0][2]} right={manifests[0][1]}
          meta={<>{manifests[0][3]}<br/>{manifests[0][4]}</>}/>
        <button className="btn" style={{width:"100%",marginBottom:10}}>Confirm Pick &amp; Move</button>
        <Item name={manifests[1][0]} tone={manifests[1][2]} right={manifests[1][1]}
          meta={<>{manifests[1][3]}<br/>{manifests[1][4]}</>}/>
      </div>
    </div>
  </>);
}

/* ---------- SETTINGS ---------- */
function Settings({onLogout,user}){
  const [data,live] = useApiData("/settings", FALLBACK_SETTINGS);
  const {profile,ops,sec} = data;
  return (<>
    <Head title="Settings &amp; Configuration" sub={user?.email || "Warehouse nodes, hardware & operator preferences"} live={live} user={user}/>
    <div className="body">
      <div className="card">
        <div style={{display:"flex",justifyContent:"space-between",alignItems:"center"}}>
          <div style={{display:"flex",gap:10}}>
            <div className="avatar" style={{width:38,height:38}}>{user?.name ? user.name.split(" ").map(n=>n[0]).join("").slice(0,2).toUpperCase() : (user?.email ? user.email[0].toUpperCase() : "U")}</div>
            <div><div className="name">{user?.name || profile.name}</div><div className="meta">{user?.email || profile.meta}</div></div>
          </div>
          <span style={{fontSize:10.5,color:"var(--accent)"}}>Switch</span>
        </div>
      </div>
      <div className="card">
        <Item name="Active Station" meta="Main Hub-01" right="4 Connected Hubs" tone="muted"/>
        <Item name="Storage Locations, Bins & Zones" meta="Configure zone coordinates & capacity limits"/>
        <Item name="Automated Reorder Thresholds" meta="Dynamic low-line stock alerts based on lead time"/>
      </div>
      <div className="sec-title">Hardware &amp; Peripherals</div>
      <div className="card">
        <Item name="Zebra TC-58 Rugged" meta="BT 3.2 · Range/Sector #90-C4" right="84%" tone="muted"/>
        <Item name="Zebra ZD42 Label & Placard" right="Online" tone="ok"/>
        <div className="item" style={{alignItems:"center"}}>
          <div><div className="name">Continuous Rapid Laser Scan</div><div className="meta">Bulk barcode ingestion w/o trigger hold</div></div>
          <Toggle on={true}/>
        </div>
      </div>
      <div className="sec-title">Operations &amp; Rules</div>
      <div className="card">
        {ops.map(([n,d,on])=>(
          <div className="item" style={{alignItems:"center"}} key={n}>
            <div><div className="name">{n}</div><div className="meta">{d}</div></div>
            <Toggle on={on}/>
          </div>
        ))}
      </div>
      <div className="sec-title">Security &amp; Data Cache</div>
      <div className="card">
        <div className="item" style={{alignItems:"center"}}>
          <div><div className="name">{sec[0][0]}</div><div className="meta">{sec[0][1]}</div></div><Toggle on={true}/>
        </div>
        <Item name={sec[1][0]} meta={sec[1][1]} right="Sync now" tone="muted"/>
        <Item name="CISHA &amp; Facility Safety Protocol ↗"/>
        <Item name="Barcode Symbology Standard SOP 2024 ↗"/>
      </div>
      <button className="btn bad" style={{width:"100%"}} onClick={onLogout}>⏻ End Shift &amp; Log Out</button>
      <div style={{textAlign:"center",fontSize:9.5,color:"var(--muted)",marginTop:12}}>
        StockSense Mobile v2.4.1 (Build 1189)<br/>SOC2 Type II Certified · End-to-End Encrypted
      </div>
    </div>
  </>);
}

/* ---------- APP ---------- */
function App(){
  const [screen,setScreen]=useState("login");
  const [view,setView]=useState("dashboard");
  const [currentUser,setCurrentUser]=useState(null);

  function handleLogin(session){
    setCurrentUser(session?.user || null);
    setScreen("app");
  }

  if(screen==="login") return <div className="device"><Login onLogin={handleLogin} goSignup={()=>setScreen("signup")}/></div>;
  if(screen==="signup") return <div className="device"><Signup goLogin={()=>setScreen("login")}/></div>;

  const views={
    dashboard:<Dashboard user={currentUser}/>,
    products:<Products/>,
    operations:<Operations/>,
    transfers:<Transfers/>,
    settings:<Settings user={currentUser} onLogout={()=>{setCurrentUser(null);setScreen("login");}}/>
  };
  const tabs=[["dashboard","▦","Dashboard"],["operations","⇄","Operations"],["products","📦","Products"],["transfers","⇌","Transfers"],["settings","⚙","Settings"]];
  return (
    <div className="device">
      {views[view]}
      <div className="tabbar">
        {tabs.map(([key,ico,label])=>(
          <button key={key} className={view===key?"active":""} onClick={()=>setView(key)}>
            <span className="ico">{ico}</span>{label}
          </button>
        ))}
      </div>
    </div>
  );
}

export default App;
