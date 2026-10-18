"use client";
import { Suspense, useEffect, useMemo, useState } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import { ArrowUpRight, BookOpen, Bot, ChevronDown, CircleAlert, ExternalLink, HeartPulse, RotateCcw, Send, ShieldCheck, Sparkles } from "lucide-react";
import { AppShell, DemoWarning, Eyebrow, PageHeading, SourceTag, StatusPill } from "@/components/app-shell";
import { buildAppointmentContext, getPatientById } from "@/lib/demo/repositories";
import { buildReferenceAnswer, type EvidenceAnswer } from "@/lib/evidence/answer";
import type { Jurisdiction } from "@/lib/evidence/catalog";

function ChatWorkspace() {
 const params=useSearchParams();
 const [query,setQuery]=useState("");
 const [jurisdiction,setJurisdiction]=useState<Jurisdiction>("EG");
 const [contextId,setContextId]=useState("");
 const [patientId,setPatientId]=useState("");
 const [answer,setAnswer]=useState<EvidenceAnswer|null>(null);
 const [submittedQuery,setSubmittedQuery]=useState("");
 useEffect(()=>{setQuery(params.get("q")??"");setContextId(params.get("context")??"");setPatientId(params.get("patient")??"");},[params]);
 const appointmentContext=useMemo(()=>contextId?buildAppointmentContext(contextId):null,[contextId]);
 const directPatient=useMemo(()=>patientId?getPatientById(patientId):null,[patientId]);
 const selectedPatient=appointmentContext?.patient??directPatient;
 const patientContextTags=selectedPatient?[
  `Allergy status: ${selectedPatient.allergyStatus}`,
  `Medicine statements: ${selectedPatient.medicines.length}`,
  `Gestational week: ${selectedPatient.obstetricHistory.gestationalWeeks??"unknown"}`,
  `Breastfeeding: ${selectedPatient.obstetricHistory.breastfeeding}`
 ]:[];
 function ask(text=query){const clean=text.trim().slice(0,240);if(!clean)return;setQuery(clean);setSubmittedQuery(clean);setAnswer(buildReferenceAnswer({question:clean,filters:{jurisdiction},selectedContext:patientContextTags}));}
 const starters=["Preeclampsia and hypertension in pregnancy","Medication during breastfeeding","Postpartum haemorrhage guidance","Contraception eligibility"];
 return <AppShell active="/mia"><PageHeading eyebrow="EVIDENCE-FIRST ASSISTANT" title="Ask Mia." description="Fast, local search across OB-GYN reference sources. Responses are source-routing summaries, not clinical recommendations." action={<span className="mia-online"><i/> LOCAL INDEX READY</span>}/>
 <DemoWarning>Prototype only. No external AI is called. Do not enter real patient details. Mia cannot prescribe or establish that a medicine is correct.</DemoWarning>
 <div className="chat-layout">
  <aside className="chat-side"><div className="chat-side-head"><span className="chat-side-icon"><Bot size={19}/></span><div><b>Mia Clinical</b><small>OB-GYN reference mode</small></div><span className="tiny-pulse"/></div>
   <div className="chat-side-divider"/><Eyebrow>CASE CONTEXT</Eyebrow>
   {appointmentContext?<div className="context-box"><div className="context-title"><HeartPulse size={14}/><b>{appointmentContext.patient.demoName}</b><StatusPill>Demo</StatusPill></div><p>{appointmentContext.appointment.service} · {appointmentContext.appointment.id}</p><div className="context-fact"><span>Allergies</span><b>{appointmentContext.patient.allergyStatus}</b></div><div className="context-fact"><span>Gestation</span><b>{appointmentContext.patient.obstetricHistory.gestationalWeeks??"Unknown"}</b></div><div className="context-fact"><span>Medicines</span><b>{appointmentContext.patient.medicines.length} statements</b></div><button className="plain-action" type="button" onClick={()=>{setContextId("");setPatientId("");setAnswer(null);setSubmittedQuery("");}}>Remove context ×</button></div>:
   directPatient?<div className="context-box"><div className="context-title"><HeartPulse size={14}/><b>{directPatient.demoName}</b><StatusPill>Demo</StatusPill></div><p>{directPatient.displayId}</p><div className="context-fact"><span>Allergies</span><b>{directPatient.allergyStatus}</b></div><div className="context-fact"><span>Medicines</span><b>{directPatient.medicines.length} statements</b></div><button className="plain-action" type="button" onClick={()=>{setPatientId("");setAnswer(null);}}>Remove context ×</button></div>:
   <div className="no-context"><ShieldCheck size={18}/><b>No patient attached</b><p>General reference search. Open Mia from a synthetic appointment to add its limited context.</p></div>}
   <Eyebrow>TRY ASKING</Eyebrow><div className="starter-list">{starters.map(s=><button key={s} type="button" onClick={()=>{setQuery(s);ask(s);}}>{s}<ArrowUpRight size={13}/></button>)}</div>
   <div className="chat-sidebar-foot"><ShieldCheck size={14}/><span>Only selected synthetic fields are displayed to the chat. This demo sends nothing externally.</span></div>
  </aside>
  <section className="chat-main"><div className="chat-thread">
    <div className="chat-message assistant"><span className="chat-avatar"><Sparkles size={15}/></span><div><div className="message-meta">MIA <span>· EVIDENCE MODE</span></div><div className="message-bubble"><p>I can help you find OB-GYN references quickly and show what each source covers. Ask a topic or a medicine question. I will not invent a treatment recommendation when there is no approved, locally reviewed pathway.</p><div className="message-capabilities"><span><BookOpen size={12}/> Source links</span><span><ShieldCheck size={12}/> Safety gaps</span></div></div></div></div>
    {answer&&<><div className="chat-message user"><span className="user-chat-badge">DS</span><div><div className="message-meta user-meta">DR. SHAFY <span>· YOUR QUESTION</span></div><div className="message-bubble user-bubble">{submittedQuery}</div></div></div>
    <div className="chat-message assistant"><span className="chat-avatar"><Sparkles size={15}/></span><div className="answer-width"><div className="message-meta">MIA <span>· LOCAL REFERENCE RETRIEVAL</span></div><div className="message-bubble"><div className="answer-status-row"><StatusPill kind={answer.status==="references_found"?"good":"warn"}>{answer.status==="references_found"?"References found":"Insufficient evidence"}</StatusPill><span className="response-time">LOCAL SEARCH</span></div><p>{answer.summary}</p>{answer.sources.length>0&&<div className="answer-sources"><div className="source-section-title">SOURCE MATCHES <span>{answer.sources.length}</span></div>{answer.sources.map(s=><article className="evidence-result" key={s.id}><div className="evidence-result-top"><SourceTag>{s.jurisdiction.join(" · ")}</SourceTag><span className="match-score">MATCH {Math.round(s.relevance)}</span></div><h3>{s.title}</h3><p>{s.publisher??"Publisher not captured"} · {s.version??"Version requires verification"}</p><small>Matched: {s.matchReason||"source metadata"}</small><div className="evidence-result-foot"><span>{s.ingest_status.replaceAll("_"," ")}</span><a href={s.url} target="_blank" rel="noreferrer">Open official source <ExternalLink size={12}/></a></div></article>)}</div>}
     <details className="limitations-details" open><summary><CircleAlert size={14}/> Limits and clinician checks <ChevronDown size={14}/></summary><div className="detail-stack"><b>What Mia cannot conclude</b><ul>{answer.limitations.map((x)=><li key={x}>{x}</li>)}</ul><b>Verify before any clinical decision</b><ul>{answer.clinicianChecks.map((x)=><li key={x}>{x}</li>)}</ul><p className="approval-callout">Approved medication pathway: <strong>none in this prototype</strong>. No medicine, dose or regimen is being recommended.</p></div></details>
    </div></div></div></>}
   </div>
   <form className="chat-composer" onSubmit={(e)=>{e.preventDefault();ask();}}><label className="visually-hidden" htmlFor="mia-question">Ask Mia a clinical-reference question</label><textarea id="mia-question" rows={2} value={query} onChange={(e)=>setQuery(e.target.value)} placeholder="Ask about a guideline, clinical topic, or medication evidence…" maxLength={240}/><div className="composer-bottom"><span><ShieldCheck size={13}/> No external model calls · max 240 characters</span><button className="button-primary" type="submit" disabled={!query.trim()}><Send size={14}/> Search evidence</button></div></form>
   <p className="chat-disclaimer">Search ranking is not evidence quality. Verify source currency, rights, local policy and patient-specific factors. Urgent clinical situations require the hospital emergency pathway, not this app.</p>
  </section>
 </div>
 </AppShell>;
}

export default function MiaPage(){return <Suspense fallback={<div className="loading-screen">Loading Mia evidence workspace…</div>}><ChatWorkspace/></Suspense>}
