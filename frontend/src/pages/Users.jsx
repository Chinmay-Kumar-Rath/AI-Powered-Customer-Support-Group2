import React, { useCallback, useEffect, useState } from "react";
import { api, apiFetch } from "../api";
import { useAuth } from "../context/AuthContext";
import { Users, Search, Plus, RefreshCw, Pencil, ShieldCheck, UserCheck, UserX, X } from "lucide-react";

const initial = { name:"", email:"", password:"", role:"employee", team:"", department:"", is_active:true };
const panel = {background:"#fff",border:"1px solid #eee9f7",borderRadius:16,padding:20};
const field = {width:"100%",padding:"11px 12px",border:"1px solid #e5e0ef",borderRadius:9,fontSize:14,boxSizing:"border-box",background:"#fff",color:"#261b49"};

export default function UsersPage() {
  const { user } = useAuth();

  const [users,setUsers] = useState([]);
  const [loading,setLoading] = useState(true);
  const [error,setError] = useState("");
  const [message,setMessage] = useState("");
  const [search,setSearch] = useState("");
  const [roleFilter,setRoleFilter] = useState("all");
  const [activeFilter,setActiveFilter] = useState("all");
  const [editing,setEditing] = useState(null);
  const [form,setForm] = useState(initial);
  const [saving,setSaving] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      setUsers(await api.users({ limit: 500 }));
    } catch (e) {
      setError(e.message || "Unable to load users.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (user?.role === "admin") {
      load();
    } else {
      setLoading(false);
    }
  }, [user?.role, load]);

  if (user?.role !== "admin") {
    return (
      <div style={{ padding: 32, color: "#261b49" }}>
        <h2>Admin access required</h2>
        <p>Only administrators can manage user accounts.</p>
      </div>
    );
  }

  const filtered = users.filter(u => {
    const term = search.toLowerCase();
    return (!term || `${u.name} ${u.email} ${u.team||""}`.toLowerCase().includes(term))
      && (roleFilter==="all" || u.role===roleFilter)
      && (activeFilter==="all" || (activeFilter==="active" ? u.is_active : !u.is_active));
  });

  const startCreate = () => { setEditing("new"); setForm(initial); setError(""); setMessage(""); };
  const startEdit = u => {
    setEditing(u);
    setForm({name:u.name||"",email:u.email||"",password:"",role:u.role||"employee",team:u.team||"",department:u.department||"",is_active:u.is_active!==false});
    setError(""); setMessage("");
  };
  const save = async e => {
    e.preventDefault(); setSaving(true); setError(""); setMessage("");
    try {
      if(editing==="new") {
        await apiFetch("/users",{method:"POST",body:{name:form.name,email:form.email,password:form.password,role:form.role,team:form.team||null,department:form.department||null}});
        setMessage("User created successfully.");
      } else {
        const body = {name:form.name,role:form.role,team:form.team||null,department:form.department||null,is_active:form.is_active};
        if(form.password) body.password=form.password;
        await apiFetch(`/users/${editing.user_id}`,{method:"PATCH",body});
        setMessage("User updated successfully.");
      }
      setEditing(null); await load();
    } catch(err) { setError(err.message || "Could not save user."); }
    finally { setSaving(false); }
  };

  const input = (label,key,opts={}) => <label style={{display:"grid",gap:6,fontSize:13,fontWeight:650,color:"#51476d"}}>
    {label}
    {opts.options ? <select style={field} value={form[key]} onChange={e=>setForm({...form,[key]:e.target.value})}>
      {opts.options.map(x=><option key={x.value} value={x.value}>{x.label}</option>)}
    </select> : <input style={field} type={opts.type||"text"} required={!!opts.required} minLength={opts.minLength} value={form[key]} placeholder={opts.placeholder||""} onChange={e=>setForm({...form,[key]:e.target.value})}/>}
  </label>;

  return <main style={{padding:"28px 30px",background:"#f8f6fc",minHeight:"100%",color:"#261b49"}}>
    <div style={{display:"flex",justifyContent:"space-between",alignItems:"center",gap:12,flexWrap:"wrap",marginBottom:22}}>
      <div><div style={{fontSize:12,fontWeight:800,color:"#7048e8",letterSpacing:1.4}}>ADMINISTRATION</div>
        <h1 style={{fontSize:28,margin:"7px 0 5px"}}>User Management</h1>
        <p style={{margin:0,color:"#827b99",fontSize:14}}>Manage accounts, roles, teams and access.</p>
      </div>
      <div style={{display:"flex",gap:9}}>
        <button onClick={load} style={{padding:"11px 14px",border:"1px solid #e8e2f2",borderRadius:10,background:"#fff",cursor:"pointer",display:"flex",gap:7,alignItems:"center",color:"#392b60"}}><RefreshCw size={16}/> Refresh</button>
        <button onClick={startCreate} style={{padding:"11px 15px",border:0,borderRadius:10,background:"linear-gradient(120deg,#7048e8,#4930ad)",color:"#fff",fontWeight:700,cursor:"pointer",display:"flex",gap:7,alignItems:"center"}}><Plus size={17}/> Add User</button>
      </div>
    </div>

    <div style={{display:"grid",gridTemplateColumns:"repeat(auto-fit,minmax(155px,1fr))",gap:13,marginBottom:18}}>
      {[
        ["Total users",users.length,Users],
        ["Employees",users.filter(u=>u.role==="employee").length,UserCheck],
        ["Engineers",users.filter(u=>u.role==="engineer").length,ShieldCheck],
        ["Active accounts",users.filter(u=>u.is_active!==false).length,UserCheck]
      ].map(([label,value,Icon])=><div key={label} style={panel}><div style={{display:"flex",justifyContent:"space-between",color:"#827b99",fontSize:13}}>{label}<Icon size={18} color="#7048e8"/></div><div style={{fontSize:27,fontWeight:800,marginTop:9}}>{value}</div></div>)}
    </div>

    {error && !editing && <div style={{...panel,color:"#c34460",marginBottom:14}}>{error}</div>}
    {message && <div style={{...panel,color:"#12836d",marginBottom:14}}>{message}</div>}

    <section style={panel}>
      <div style={{display:"flex",gap:10,flexWrap:"wrap",marginBottom:17}}>
        <div style={{position:"relative",flex:"1 1 220px"}}>
          <Search size={17} color="#9189a7" style={{position:"absolute",left:12,top:12}}/>
          <input value={search} onChange={e=>setSearch(e.target.value)} placeholder="Search name, email or team..." style={{...field,paddingLeft:38}}/>
        </div>
        <select value={roleFilter} onChange={e=>setRoleFilter(e.target.value)} style={{...field,width:"auto",minWidth:145}}>
          <option value="all">All roles</option><option value="admin">Admin</option><option value="engineer">Engineer</option><option value="employee">Employee</option>
        </select>
        <select value={activeFilter} onChange={e=>setActiveFilter(e.target.value)} style={{...field,width:"auto",minWidth:145}}>
          <option value="all">All accounts</option><option value="active">Active</option><option value="inactive">Inactive</option>
        </select>
      </div>
      {loading ? <p style={{color:"#827b99"}}>Loading users…</p> : filtered.length===0 ? <p style={{color:"#827b99",padding:15}}>No users found. Try changing your filters.</p> :
      <div style={{overflowX:"auto"}}>
        <table style={{width:"100%",borderCollapse:"collapse",fontSize:13,minWidth:650}}>
          <thead><tr style={{textAlign:"left",color:"#827b99",borderBottom:"1px solid #eee9f7"}}>
            {["User","Role","Team / Department","Status","Action"].map(x=><th key={x} style={{padding:"12px 9px"}}>{x}</th>)}
          </tr></thead>
          <tbody>{filtered.map(u=><tr key={u.user_id} style={{borderBottom:"1px solid #f0edf6"}}>
            <td style={{padding:"13px 9px"}}><b>{u.name}</b><div style={{color:"#89829d",marginTop:4}}>{u.email}</div></td>
            <td style={{padding:"13px 9px",textTransform:"capitalize"}}>{u.role}</td>
            <td style={{padding:"13px 9px"}}>{u.team||"—"}{u.department?<div style={{color:"#89829d",marginTop:4}}>{u.department}</div>:null}</td>
            <td style={{padding:"13px 9px"}}><span style={{padding:"5px 9px",borderRadius:20,fontSize:11,fontWeight:700,background:u.is_active===false?"#fff0f2":"#e8f8f2",color:u.is_active===false?"#c34460":"#13856c"}}>{u.is_active===false?"Inactive":"Active"}</span></td>
            <td style={{padding:"13px 9px"}}><button onClick={()=>startEdit(u)} style={{border:"1px solid #e7e0f2",background:"#fff",borderRadius:8,padding:"7px 10px",cursor:"pointer",color:"#6544c5",display:"flex",alignItems:"center",gap:6}}><Pencil size={14}/> Edit</button></td>
          </tr>)}</tbody>
        </table>
      </div>}
    </section>

    {editing && <div style={{position:"fixed",inset:0,zIndex:50,background:"#17102b88",display:"grid",placeItems:"center",padding:16}}>
      <form onSubmit={save} style={{background:"#fff",borderRadius:18,padding:24,width:"min(100%,520px)",maxHeight:"90vh",overflowY:"auto",boxShadow:"0 20px 70px #17102b44"}}>
        <div style={{display:"flex",justifyContent:"space-between",alignItems:"center",marginBottom:18}}>
          <div><h2 style={{margin:0,fontSize:21}}>{editing==="new"?"Create User":"Edit User"}</h2><p style={{margin:"5px 0 0",fontSize:12,color:"#827b99"}}>Fields marked * are required.</p></div>
          <button type="button" onClick={()=>setEditing(null)} style={{border:0,background:"#f4f1fa",borderRadius:9,padding:8,cursor:"pointer"}}><X size={18}/></button>
        </div>
        <div style={{display:"grid",gap:13}}>
          {input("Full name *","name",{required:true})}
          {input("Email address *","email",{required:true,type:"email"})}
          {editing==="new" ? input("Password (minimum 8 characters) *","password",{required:true,type:"password",minLength:8}) : input("Reset password (optional, minimum 8 characters)","password",{type:"password",minLength:8,placeholder:"Leave blank to keep current password"})}
          {input("Role","role",{options:[{value:"employee",label:"Employee"},{value:"engineer",label:"Engineer"},{value:"admin",label:"Admin"}]})}
          {input("Team","team",{placeholder:"Required for engineers"})}
          {input("Department","department",{placeholder:"e.g. Customer Support"})}
          {editing!=="new" && <label style={{display:"flex",gap:9,alignItems:"center",fontSize:13,color:"#51476d"}}><input type="checkbox" checked={form.is_active} onChange={e=>setForm({...form,is_active:e.target.checked})}/> Account active</label>}
        </div>
        {error && <p style={{color:"#c34460",fontSize:13,marginTop:12}}>{error}</p>}
        <div style={{display:"flex",justifyContent:"end",gap:9,marginTop:20}}>
          <button type="button" onClick={()=>setEditing(null)} style={{padding:"10px 15px",border:"1px solid #e8e2f2",borderRadius:9,background:"#fff",cursor:"pointer"}}>Cancel</button>
          <button disabled={saving} style={{padding:"10px 17px",border:0,borderRadius:9,background:"#6544d3",color:"#fff",fontWeight:700,cursor:"pointer"}}>{saving?"Saving…":editing==="new"?"Create user":"Save changes"}</button>
        </div>
      </form>
    </div>}
  </main>;
}



