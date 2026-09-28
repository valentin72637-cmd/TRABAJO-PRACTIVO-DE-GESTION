/* Sin dependencias: node --test tests/frontend.test.cjs */
const {test} = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const root = path.resolve(__dirname, "..");

class Node {
    constructor(tag="div") { this.tagName=tag; this.children=[]; this.style={}; this.dataset={}; this.attrs={}; this.hidden=false; this.text=""; this.events={}; }
    set textContent(value) { this.text=String(value); this.children=[]; }
    get textContent() { return this.text + this.children.map(x=>x.textContent||"").join(""); }
    set innerHTML(value) { if (value) throw new Error("No se permite HTML dinámico en informes"); this.replaceChildren(); }
    append(...nodes) { this.children.push(...nodes); }
    appendChild(node) { this.append(node); return node; }
    prepend(node) { this.children.unshift(node); }
    replaceChildren(...nodes) { this.children=nodes; this.text=""; }
    setAttribute(key,value) { this.attrs[key]=value; }
    addEventListener(name,handler) { this.events[name]=handler; }
    remove() {}
    click() {}
}
function harness(role="cliente", shared={}, initial=null) {
    shared.local ||= new Map([["token","legacy-shared-token"]]);
    shared.locks ||= new Set();
    const events = {};
    const locks = {request(name, options, callback) {
        if (shared.locks.has(name)) return Promise.resolve(callback(null));
        shared.locks.add(name);
        return Promise.resolve(callback({name})).finally(()=>shared.locks.delete(name));
    }};
    const nodes = new Map();
    for (const id of ["filtros","pendientes","aplicados","cards","porEstado","porTipo","porVencer","resumen","paginacion","exportar","error","cargando","cliente","main","tbody"])
        nodes.set(id,new Node());
    const storage = new Map(initial || [["token","test-token"],["role","admin"],["segurar.tabId",require("node:crypto").randomUUID()]]);
    const storageAPI = map => ({getItem:key=>map.get(key)||null,setItem:(key,value)=>map.set(key,String(value)),removeItem:key=>map.delete(key)});
    const sessionStorage=storageAPI(storage), localStorage=storageAPI(shared.local);
    const doc={body:new Node("body"),events:{},getElementById:id=>nodes.get(id),
        createElement:tag=>new Node(tag),createTextNode:text=>Object.assign(new Node("#text"),{text:String(text)}),
        querySelector:selector=>selector==="#tabla tbody"?nodes.get("tbody"):selector==="main"?nodes.get("main"):null,
        addEventListener:(name,fn)=>doc.events[name]=fn};
    doc.body.dataset.role=role;
    const calls=[]; let filters=[];
    const location={pathname:"/app/informes_"+role+".html",replace:value=>{location.redirect=value;},reload:()=>{}};
    const summary={indicadores:{total_polizas:1,vigentes:1,proximas_a_vencer:0,vencidas:0},
        por_estado:[{categoria:"Vigente",cantidad:1}],por_tipo:[{categoria:"Auto",cantidad:1}],
        vencimientos_por_tramo:[{tramo:"Más de 60 días",cantidad:1}],
        resumen_textual:"0 pólizas próximas.",fecha_referencia:"2026-09-27"};
    const listing={items:[{numero:"<img src=x onerror=alert(1)>",tipo:"Auto",inicio:"2026-01-01",
        vencimiento:"2027-01-01",estado:"Vigente",mensaje:"<script>alert(1)</script>"}],
        pagination:{page:1,page_size:20,total_items:1,total_pages:1}};
    let responder=async url=>({ok:true,status:200,
        json:async()=>url.includes("resumen")?summary:url.includes("listado")?listing:{id:2,nombre:"Cliente",email:"c@example.com",role},
        blob:async()=>new Blob(["pdf"])});
    const context=vm.createContext({console,Headers,URLSearchParams,AbortController,AbortSignal,Blob,
        URL:{createObjectURL:()=>"blob:test",revokeObjectURL:()=>{}},
        setTimeout:fn=>fn(),document:doc,localStorage,sessionStorage,location,
        navigator:{locks},crypto:require("node:crypto").webcrypto,
        addEventListener:(name,callback)=>{events[name]=callback;},
        FormData:class { [Symbol.iterator]() {return filters[Symbol.iterator]();} },
        fetch:async(url,options)=>{calls.push({url,options});return responder(url,options);}});
    context.window=context;
    const run=file=>vm.runInContext(fs.readFileSync(path.join(root,"login/app",file),"utf8"),context);
    run("common.js");
    context.segurarReady=Promise.resolve(true);
    return {context,nodes,storage,calls,doc,location,run,summary,listing,shared,events,
        setFilters:value=>{filters=value;},setResponder:value=>{responder=value;}};
}
test("errores 422 legibles, escape HTML y fecha civil local",()=>{
    const h=harness();
    assert.equal(h.context.SegurAR.errorMessage([{loc:["body","email"],msg:"Inválido"}]),"email: Inválido");
    assert.equal(h.context.SegurAR.escapeHTML('<img a="x">&'),"&lt;img a=&quot;x&quot;&gt;&amp;");
    assert.equal(h.context.SegurAR.localDate({getFullYear:()=>2026,getMonth:()=>8,getDate:()=>27}),"2026-09-27");
});
test("guard conserva la sesión ante 500 y fallo de red",async()=>{
    for(const network of [false,true]) {
        const h=harness();
        h.setResponder(async()=>{if(network)throw new Error("offline");return {ok:false,status:500,json:async()=>({})};});
        h.run("guard.js");
        assert.equal(await h.context.segurarReady,false);
        assert.equal(h.storage.get("token"),"test-token");
        assert.equal(h.nodes.get("main").hidden,true);
        assert.equal(h.location.redirect,undefined);
    }
});
test("guard verifica el rol real también en informes y limpia solo un 401",async()=>{
    const h=harness("admin");
    h.setResponder(async()=>({ok:true,status:200,json:async()=>({id:2,nombre:"Cliente",role:"cliente",email:"c@example.com"})}));
    h.run("guard.js"); assert.equal(await h.context.segurarReady,false);
    assert.equal(h.nodes.get("main").hidden,true);
    const invalid=harness();
    invalid.setResponder(async()=>({ok:false,status:401,json:async()=>({})}));
    invalid.run("guard.js"); await invalid.context.segurarReady;
    assert.equal(invalid.storage.has("token"),false);
    assert.match(invalid.location.redirect,/index.html/);
});
test("informe sin Chart.js, XSS mostrado como texto y PDF con filtros aplicados",async()=>{
    const h=harness();
    h.setFilters([["tipo","Auto"]]);
    h.run("informes.js"); await h.doc.events.DOMContentLoaded();
    assert.match(h.nodes.get("tbody").textContent,/<img src=x/);
    assert.match(h.nodes.get("porTipo").textContent,/CantidadAuto1/);
    assert.equal(h.nodes.get("exportar").disabled,false);
    h.setFilters([["tipo","Vida"]]);
    h.context.filterNotice();
    assert.match(h.nodes.get("pendientes").textContent,/sin aplicar/);
    await h.context.pdf();
    assert.match(h.calls.at(-1).url,/exportar.pdf\?tipo=Auto$/);
});
test("fallo al filtrar no deja datos anteriores ni permite exportar",async()=>{
    const h=harness();h.run("informes.js");await h.doc.events.DOMContentLoaded();
    h.setResponder(async()=>({ok:false,status:500,json:async()=>({detail:"Servidor caído"})}));
    await h.context.cargar(new URLSearchParams("tipo=Vida"),1);
    assert.equal(h.nodes.get("tbody").textContent,"");
    assert.equal(h.nodes.get("cards").textContent,"");
    assert.equal(h.nodes.get("exportar").disabled,true);
    assert.match(h.nodes.get("error").textContent,/Servidor caído/);
});
test("respuestas anteriores no pisan el filtro más reciente",async()=>{
    const h=harness();h.run("informes.js");
    let release;
    const first=new Promise(resolve=>{release=resolve;});
    h.setResponder(async url=>{
        if(url.includes("tipo=Auto"))await first;
        return {ok:true,status:200,json:async()=>url.includes("resumen")?h.summary:h.listing};
    });
    const old=h.context.cargar(new URLSearchParams("tipo=Auto"),1);
    await h.context.cargar(new URLSearchParams("tipo=Vida"),1);
    release();await old;
    assert.match(h.nodes.get("aplicados").textContent,/Vida/);
    assert.doesNotMatch(h.nodes.get("aplicados").textContent,/Auto/);
});
test("vacíos y empates tienen explicaciones sin ganador falso",async()=>{
    const h=harness();h.run("informes.js");
    assert.match(h.context.summary([{categoria:"Auto",cantidad:2},{categoria:"Vida",cantidad:2}]),/Empatan/);
    assert.match(h.context.summary([]),/No hay/);
    h.listing.items=[];h.listing.pagination.total_items=0;h.listing.pagination.total_pages=0;
    await h.doc.events.DOMContentLoaded();
    assert.match(h.nodes.get("tbody").textContent,/Todavía no hay/);
});
test("logout revoca antes de borrar y conserva token si el servidor falla",async()=>{
    const h=harness();h.setResponder(async()=>({ok:false,status:500}));
    h.run("logout.js");await new Promise(resolve=>setImmediate(resolve));
    assert.equal(h.storage.has("token"),true);
    assert.match(h.calls[0].url,/auth\/logout$/);
    assert.equal(h.calls[0].options.method,"POST");
    h.setResponder(async()=>({ok:true,status:204}));
    h.run("logout.js");await new Promise(resolve=>setImmediate(resolve));
    assert.equal(h.storage.has("token"),false);
    assert.equal(h.location.redirect,"../index.html");
});
test("HTML mantiene listado sobre gráficos y etiquetas vinculadas",()=>{
    for(const role of ["admin","cliente"]) {
        const html=fs.readFileSync(path.join(root,"login/app/informes_"+role+".html"),"utf8");
        assert.ok(html.indexOf('id="tabla"')<html.indexOf('id="porEstado"'));
        for(const id of ["estado","tipo","vencimiento-desde","vencimiento-hasta"]) {
            assert.ok(html.includes('for="'+id+'"'));
            assert.ok(html.includes('id="'+id+'"'));
        }
        assert.ok(!html.includes("chart.js"));
    }
});

test("tablas del administrador escapan nombres y números de póliza",()=>{
    const h=harness("admin");
    const tables = {"#tablaUsuarios tbody":new Node(), "#tablaPolizas tbody":new Node()};
    h.doc.querySelector = selector => tables[selector] || h.nodes.get("main");
    for (const table of Object.values(tables)) table.insertAdjacentHTML = (_,html) => {table.html=(table.html||"")+html;};
    h.run("dashboard_admin.js");
    h.context.renderizarUsuarios([{id:2,nombre:"<img src=x onerror=alert(1)>",email:"x@example.com",role:"cliente"}]);
    assert.ok(tables["#tablaUsuarios tbody"].html.includes("&lt;img"));
    assert.ok(!tables["#tablaUsuarios tbody"].html.includes("<img"));
    vm.runInContext('usuariosCache = [{id:2,nombre:"<svg onload=alert(1)>"}]',h.context);
    h.context.renderizarPolizas([{id:1,cliente_id:2,numero:"<img src=x>",tipo:"Auto",vencimiento:"2026-10-01"}]);
    assert.ok(!tables["#tablaPolizas tbody"].html.includes("<img"));
    assert.ok(!tables["#tablaPolizas tbody"].html.includes("<svg"));
});

const tick = () => new Promise(resolve=>setImmediate(resolve));

for (const first of ["admin","cliente"]) {
    test("sesiones independientes: "+first+" primero, otra identidad después",async()=>{
        const shared={};
        const a=harness(first,shared), b=harness(first==="admin"?"cliente":"admin",shared);
        await Promise.all([a.context.SegurAR.tabReady,b.context.SegurAR.tabReady]);
        a.storage.set("token","token-A");b.storage.set("token","token-B");
        await a.context.SegurAR.request("/polizas/mias");
        await b.context.SegurAR.request("/polizas/mias");
        assert.equal(a.calls.at(-1).options.headers.get("Authorization"),"Bearer token-A");
        assert.equal(b.calls.at(-1).options.headers.get("Authorization"),"Bearer token-B");
        a.context.SegurAR.clearSession();
        assert.equal(a.storage.has("token"),false);
        assert.equal(b.storage.get("token"),"token-B");
        assert.equal(shared.local.get("token"),"legacy-shared-token");
    });
}
test("401 de A no limpia B; 401 tardío no borra un nuevo login de A",async()=>{
    const shared={},a=harness("admin",shared),b=harness("cliente",shared);
    await Promise.all([a.context.SegurAR.tabReady,b.context.SegurAR.tabReady]);
    a.setResponder(async()=>({ok:false,status:401}));
    await assert.rejects(a.context.SegurAR.request("/auth/me"));
    assert.equal(b.storage.get("token"),"test-token");
    b.setResponder(async()=>{b.storage.set("token","nuevo-login");return {ok:false,status:401};});
    await assert.rejects(b.context.SegurAR.request("/auth/me"));
    assert.equal(b.storage.get("token"),"nuevo-login");
});
test("duplicar limpia solo la copia, sin revocar el token de la original",async()=>{
    const shared={},a=harness("admin",shared);
    await a.context.SegurAR.tabReady;
    const b=harness("admin",shared,[...a.storage]);
    await b.context.SegurAR.tabReady;
    assert.equal(a.storage.get("token"),"test-token");
    assert.equal(b.storage.has("token"),false);
    assert.notEqual(a.storage.get("segurar.tabId"),b.storage.get("segurar.tabId"));
    b.run("logout.js");await tick();
    assert.equal(b.calls.length,0);
    assert.equal(a.storage.get("token"),"test-token");
});
test("recarga y navegación conservan la sesión; pestaña nueva no adopta localStorage",async()=>{
    const shared={},a=harness("admin",shared);
    await a.context.SegurAR.tabReady;
    a.events.pagehide();await tick();
    const reloaded=harness("admin",shared,[...a.storage]);
    await reloaded.context.SegurAR.tabReady;
    assert.equal(reloaded.storage.get("token"),"test-token");
    const fresh=harness("cliente",shared,[]);
    await fresh.context.SegurAR.tabReady;
    assert.equal(fresh.storage.has("token"),false);
    assert.equal(shared.local.get("token"),"legacy-shared-token");
});
test("cerrar sesión en B usa solo su token y no cambia A",async()=>{
    const shared={},a=harness("admin",shared),b=harness("cliente",shared);
    await Promise.all([a.context.SegurAR.tabReady,b.context.SegurAR.tabReady]);
    a.storage.set("token","admin-A");b.storage.set("token","cliente-B");
    b.setResponder(async()=>({ok:true,status:204}));
    b.run("logout.js");await tick();
    assert.equal(b.calls[0].options.headers.Authorization,"Bearer cliente-B");
    assert.equal(b.storage.has("token"),false);
    assert.equal(a.storage.get("token"),"admin-A");
});

for (const order of [["admin","cliente"],["cliente","admin"]]) {
    test("formulario real de login almacena cada identidad: "+order.join(" / "),async()=>{
        const shared={}, tabs=[];
        for (const role of order) {
            const h=harness(role,shared,[]);
            await h.context.SegurAR.tabReady;
            const form=new Node("form");form.checkValidity=()=>true;
            h.nodes.set("loginForm",form);
            h.nodes.set("email",Object.assign(new Node("input"),{value:role+"@example.com"}));
            h.nodes.set("password",Object.assign(new Node("input"),{value:"SoloPruebaTemporal!"}));
            h.nodes.set("alert-container",new Node());
            h.setResponder(async url=>({ok:true,status:200,json:async()=>url.endsWith("/auth/login")
                ? {access_token:"token-"+role}
                : {id:role==="admin"?1:2,nombre:"QA "+role,email:role+"@example.com",role}}));
            h.run("script.js");await tick();
            await form.events.submit({preventDefault(){}});
            assert.equal(h.storage.get("token"),"token-"+role);
            assert.equal(h.storage.get("role"),role);
            assert.equal(h.location.href,"./app/dashboard_"+role+".html");
            tabs.push(h);
        }
        assert.equal(tabs[0].storage.get("role"),order[0]);
        assert.equal(shared.local.get("token"),"legacy-shared-token");
    });
}
