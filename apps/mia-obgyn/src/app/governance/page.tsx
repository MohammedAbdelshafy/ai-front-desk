import Link from "next/link";
import { ArrowUpRight, FileText, ShieldAlert, ShieldCheck } from "lucide-react";
import { AppShell, PageHeading, StatusPill } from "@/components/app-shell";
import manifest from "@/data/governance-docs.json";

export default function GovernancePage(){
 const required=manifest.documents.length;
 return <AppShell active="/governance"><PageHeading eyebrow="LAUNCH READINESS" title="Safety & governance" description="Required review pack for future clinical use. All items are templates, not signed policies."/>
 <div className="governance-banner"><ShieldAlert size={20}/><div><b>NOT CLEARED FOR LIVE PATIENT DATA OR CLINICAL USE</b><p>{manifest.notice}</p></div></div>
 <section className="governance-metrics"><article><span>DOCUMENT TEMPLATES</span><b>{required}</b><small>Drafts to prepare/review</small></article><article><span>APPROVED</span><b>0</b><small>None approved by this prototype</small></article><article><span>LIVE-USE BLOCKERS</span><b>{required}</b><small>All require professional review</small></article></section>
 <div className="section-heading"><h2>Required document register</h2><StatusPill kind="warn">Review required</StatusPill></div>
 <div className="table-panel governance-table"><div className="table-header"><span>DOCUMENT</span><span>ACCOUNTABLE REVIEW ROLE</span><span>STATUS</span><span>BLOCKS LIVE USE</span><span></span></div>{manifest.documents.map(doc=><div className="patient-row governance-row" key={doc.id}><span className="patient-name-cell"><span className="source-book-icon"><FileText size={14}/></span><span><b>{doc.title}</b><small>{doc.id}</small></span></span><span className="table-context">{doc.ownerRole}</span><span><StatusPill kind="warn">{doc.status.replaceAll("_"," ")}</StatusPill></span><span className="block-flag">YES</span><span/></div>)}</div>
 <article className="panel governance-next"><ShieldCheck size={18}/><div><b>Before any real clinic is onboarded</b><p>Complete local legal/regulatory review, clinical/pharmacist approval, privacy and vendor review, threat-model verification, clinical validation, and release sign-off. Do not send data to any external model until provider terms and processing location are approved.</p><Link href="https://pdpc.gov.eg/" target="_blank">Egyptian Personal Data Protection Center <ArrowUpRight size={13}/></Link><span> · </span><Link href="https://www.edaegypt.gov.eg/" target="_blank">Egyptian Drug Authority <ArrowUpRight size={13}/></Link></div></article>
 </AppShell>
}
