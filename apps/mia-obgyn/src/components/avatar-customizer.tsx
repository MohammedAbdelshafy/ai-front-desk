"use client";
import { useRef, useState } from "react";
import { UserRound, Upload, RotateCcw } from "lucide-react";

const presets = [
 { id:"mia",label:"Mia",face:"✳" },
 { id:"clinician-f",label:"Clinician",face:"◉" },
 { id:"clinician-m",label:"Clinician",face:"◈" },
 { id:"neutral",label:"Neutral",face:"◎" },
];

export function AvatarCustomizer() {
 const [selected,setSelected]=useState("mia");
 const [photo,setPhoto]=useState<string|null>(null);
 const input=useRef<HTMLInputElement>(null);
 function upload(file?:File) {
  if(!file) return;
  if(!["image/png","image/jpeg","image/webp"].includes(file.type) || file.size > 8*1024*1024) { window.alert("Choose a JPEG, PNG or WebP under 8 MB."); return; }
  const url=URL.createObjectURL(file);
  setPhoto(url); setSelected("photo");
 }
 function reset(){if(photo) URL.revokeObjectURL(photo);setPhoto(null);setSelected("mia");if(input.current)input.current.value="";}
 return <div className="avatar-widget">
  <div className="avatar-preview" aria-label="Mia avatar preview">{photo?<img src={photo} alt="Local avatar preview"/>:<span className={`avatar-face ${selected}`}>{presets.find(x=>x.id===selected)?.face??"✳"}</span>}</div>
  <div className="avatar-copy"><b>Make Mia feel like yours</b><small>Personalize this browser preview.</small>
   <div className="avatar-presets">{presets.map(p=><button key={p.id} className={selected===p.id?"preset selected":"preset"} type="button" title={p.label} aria-pressed={selected===p.id} onClick={()=>{if(photo){URL.revokeObjectURL(photo);setPhoto(null);}setSelected(p.id);}}>{p.face}</button>)}
    <button type="button" className={selected==="photo"?"preset selected":"preset"} title="Upload portrait" aria-pressed={selected==="photo"} onClick={()=>input.current?.click()}><Upload size={14}/></button>
   </div>
  </div>
  <input ref={input} className="visually-hidden" type="file" accept="image/png,image/jpeg,image/webp" onChange={(e)=>upload(e.target.files?.[0])} aria-label="Upload a Mia avatar image"/>
  <button type="button" className="avatar-reset" onClick={reset} aria-label="Reset Mia avatar"><RotateCcw size={13}/></button>
  <small className="avatar-privacy"><UserRound size={12}/> Local preview only. Image is not uploaded.</small>
 </div>;
}
