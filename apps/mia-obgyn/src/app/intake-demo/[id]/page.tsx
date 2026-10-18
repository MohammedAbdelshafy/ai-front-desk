"use client";
import { useMemo, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { ArrowLeft, Check, Send } from "lucide-react";
import { AppShell, DemoWarning, Eyebrow, PageHeading, StatusPill } from "@/components/app-shell";
import { buildAppointmentContext, getQuestionnaireTemplate } from "@/lib/demo/repositories";
import { shouldShowQuestion, validateQuestionnaire } from "@/lib/questionnaires/engine";

export default function IntakeDemoPage() {
 const params=useParams<{id:string}>(); const context=buildAppointmentContext(params.id);
 const template=getQuestionnaireTemplate("obgyn-general-intake");
 const [answers,setAnswers]=useState<Record<string,string>>({});
 const [submitted,setSubmitted]=useState(false);
 const [message,setMessage]=useState("");
 const validation=useMemo(()=>template?validateQuestionnaire(template,answers):{valid:false,missing:[],hiddenUnanswered:[]},[template,answers]);
 if(!context||!template) return <AppShell active="/questionnaires"><PageHeading eyebrow="INTAKE PREVIEW" title="Demo case not found"/><p>Choose an appointment from the demo schedule.</p><Link href="/appointments">Back to schedule</Link></AppShell>;
 return <AppShell active="/appointments"><div className="backline"><Link href={`/appointments/${context.appointment.id}`}><ArrowLeft size={14}/> Appointment</Link><span>/</span> Patient intake demo</div>
 <PageHeading eyebrow="PATIENT-FACING PREVIEW" title="Before your visit" description={`${context.patient.demoName} · ${context.appointment.service} · Fictional example`} action={<StatusPill>Template v{template.version}</StatusPill>}/>
 <DemoWarning>This is a preview using fictional data. Do not enter real health information. Submitting does not send or save answers to a clinic.</DemoWarning>
 {submitted?<section className="panel success-panel"><div className="success-mark"><Check size={22}/></div><Eyebrow>DEMO SUBMISSION COMPLETE</Eyebrow><h2>Answers reviewed locally</h2><p>The prototype validated the form in browser state only. Nothing was transmitted.</p><Link className="button-primary" href={`/appointments/${context.appointment.id}`}>Return to appointment</Link></section>:<form className="form-panel intake-form" onSubmit={(e)=>{e.preventDefault();if(!validation.valid){setMessage("Please complete the required fields.");return;}setMessage("");setSubmitted(true);}}>
 <div className="form-progress"><span>OB-GYN PRE-VISIT QUESTIONNAIRE</span><span>{template.questions.filter(q=>shouldShowQuestion(q,answers)&&answers[q.id]?.trim()).length} answered</span></div>
 {template.questions.map((q,index)=>shouldShowQuestion(q,answers)&&<div className="question-block" key={q.id}><label htmlFor={q.id}><span className="question-index">{String(index+1).padStart(2,"0")}</span>{q.label}{q.required&&<i>Required</i>}</label>
 {q.type==="text"?<textarea id={q.id} rows={3} value={answers[q.id]??""} required={q.required} onChange={(e)=>setAnswers(s=>({...s,[q.id]:e.target.value}))} placeholder="Your answer…"/>:
 q.type==="yesno"||q.type==="select"?<select id={q.id} value={answers[q.id]??""} required={q.required} onChange={(e)=>setAnswers(s=>({...s,[q.id]:e.target.value}))}><option value="">Choose an answer</option>{(q.type==="yesno"?["yes","no","not sure","prefer not to answer"]:q.options??[]).map(x=><option key={x} value={x}>{x}</option>)}</select>:
 q.type==="date"?<input id={q.id} type="date" value={answers[q.id]??""} required={q.required} onChange={(e)=>setAnswers(s=>({...s,[q.id]:e.target.value}))}/>:
 <input id={q.id} type="number" min="0" max="45" value={answers[q.id]??""} required={q.required} onChange={(e)=>setAnswers(s=>({...s,[q.id]:e.target.value}))}/>}
 </div>)}
 {message&&<p role="alert" className="form-error">{message} {validation.missing.length? `Missing: ${validation.missing.join(", ")}`:""}</p>}
 <div className="form-actions"><Link href={`/appointments/${context.appointment.id}`} className="button-quiet">Cancel</Link><button type="submit" className="button-primary"><Send size={14}/> Validate demo answers</button></div>
 <p className="form-fineprint">If you have severe symptoms or believe it is an emergency, do not wait for a questionnaire or online response. Seek urgent local care.</p>
 </form>}
 </AppShell>;
}
