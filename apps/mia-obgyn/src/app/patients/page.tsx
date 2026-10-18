import Link from "next/link";
import { ArrowUpRight, Search, Users } from "lucide-react";
import { AppShell, Eyebrow, PageHeading, StatusPill } from "@/components/app-shell";
import { getPatients } from "@/lib/demo/repositories";

export default function PatientsPage() {
 const patients=getPatients();
 return <AppShell active="/patients"><PageHeading eyebrow="PATIENT DIRECTORY" title="Patients" description="Synthetic OB-GYN records for testing the full clinical workflow." action={<span className="count-pill"><Users size={14}/>{patients.length} demo records</span>}/>
 <div className="search-panel"><Search size={16}/><input aria-label="Search demo patients" placeholder="Search by demo name or ID (fictional data only)"/><kbd>⌘ K</kbd></div>
 <section className="table-panel"><div className="table-header"><span>DEMO PATIENT</span><span>OB-GYN CONTEXT</span><span>ALLERGY STATUS</span><span>RECENT ENCOUNTER</span><span>OPEN</span></div>{patients.map((p)=>{const last=p.encounters[p.encounters.length-1];return <Link className="patient-row" key={p.id} href={`/patients/${p.id}`}><span className="patient-name-cell"><span className="patient-initial">{p.displayId.slice(-2)}</span><span><b>{p.demoName}</b><small>{p.displayId} · Age {p.ageYears}</small></span></span><span className="table-context">{p.conditions[0]??"No condition recorded"}</span><span><StatusPill kind={p.allergyStatus==="known-allergies"?"warn":p.allergyStatus==="confirmed-none"?"good":"neutral"}>{p.allergyStatus==="confirmed-none"?"No known allergies":p.allergyStatus==="known-allergies"?"Allergy on record":p.allergyStatus==="unknown"?"Unknown":"Not reviewed"}</StatusPill></span><span className="table-context">{last?.label??"No encounters"}</span><span className="table-arrow"><ArrowUpRight size={15}/></span></Link>;})}</section>
 <p className="page-disclaimer">All records, contact details, dates and histories on this screen are synthetic. The search box is a UI prototype and does not perform a secure patient lookup.</p>
 </AppShell>;
}
