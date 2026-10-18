import Link from "next/link";
import { ArrowUpRight, CalendarClock, ClipboardList } from "lucide-react";
import { AppShell, PageHeading, StatusPill } from "@/components/app-shell";
import { getAppointments, getPatients } from "@/lib/demo/repositories";

export default function AppointmentsPage() {
 const appts=getAppointments(); const patients=getPatients();
 return <AppShell active="/appointments"><PageHeading eyebrow="CLINIC SCHEDULE" title="Appointments" description="Your women’s health schedule, with intake status and appointment history."/>
 <div className="schedule-date"><CalendarClock size={16}/> Sunday, 18 October 2026 <span>·</span> All records are synthetic</div>
 <div className="table-panel"><div className="table-header appointment-table-head"><span>TIME / VISIT</span><span>PATIENT</span><span>INTAKE</span><span>STATUS</span><span>OPEN</span></div>{appts.map(a=>{const p=patients.find(x=>x.id===a.patientId);return <Link className="patient-row" href={`/appointments/${a.id}`} key={a.id}><span><b>{new Date(a.dateTime).toLocaleTimeString("en-GB",{hour:"2-digit",minute:"2-digit"})} · {a.service}</b><small>{a.reason}</small></span><span className="patient-name-cell"><span className="patient-initial">{p?.displayId.slice(-2)}</span><span><b>{p?.demoName}</b><small>{p?.displayId}</small></span></span><span>{a.questionnaireId?<StatusPill kind="good"><ClipboardList size={12}/> Received</StatusPill>:<StatusPill kind="warn">Pending</StatusPill>}</span><span><StatusPill kind={a.status==="needs-review"?"warn":a.status==="intake-received"?"blue":"neutral"}>{a.status.replaceAll("-"," ")}</StatusPill></span><span className="table-arrow"><ArrowUpRight size={15}/></span></Link>;})}</div>
 <p className="page-disclaimer">This is a demo schedule. No appointment is booked or sent to any patient.</p></AppShell>;
}
