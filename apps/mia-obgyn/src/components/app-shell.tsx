import type { ReactNode } from "react";
import Link from "next/link";
import { ArrowUpRight, BookOpen, CalendarClock, CheckCircle2, CircleAlert, ClipboardList, FileText, HeartPulse, ShieldCheck, Users, Sparkles } from "lucide-react";
import { getPatients, getAppointments, getQuestionnaireResponses } from "@/lib/demo/repositories";

const nav = [
  { href: "/dashboard", label: "Overview", Icon: Sparkles },
  { href: "/patients", label: "Patients", Icon: Users },
  { href: "/appointments", label: "Appointments", Icon: CalendarClock },
  { href: "/questionnaires", label: "Questionnaires", Icon: ClipboardList },
  { href: "/mia", label: "Mia chat", Icon: HeartPulse },
  { href: "/evidence", label: "Evidence library", Icon: BookOpen },
  { href: "/governance", label: "Safety & governance", Icon: ShieldCheck },
];

export function AppShell({ children, active = "/dashboard" }: { children: ReactNode; active?: string }) {
  const patients = getPatients();
  const appointments = getAppointments();
  const responses = getQuestionnaireResponses();
  return <div className="app-frame">
    <aside className="sidebar">
      <Link className="brand-lockup" href="/dashboard" aria-label="Mia OB-GYN home">
        <span className="brand-emblem" aria-hidden="true"><span>m</span><i /></span>
        <span className="brand-word">mia<span>.</span><small>WOMEN&apos;S HEALTH OS</small></span>
      </Link>
      <div className="clinic-selector"><span className="clinic-orb">✳</span><span><b>Dr. Shafy&apos;s Clinic</b><small>OB-GYN · Egypt</small></span><span className="chevron">⌄</span></div>
      <div className="nav-label">WORKSPACE</div>
      <nav className="main-nav" aria-label="Main navigation">
        {nav.map(({href,label,Icon})=><Link key={href} href={href} className={active===href ? "nav-item active":"nav-item"}><Icon size={17} strokeWidth={1.7}/><span>{label}</span>{href==="/appointments"&&<span className="nav-count">{appointments.length}</span>}</Link>)}
      </nav>
      <div className="sidebar-spacer"/>
      <div className="sidebar-signal"><span className="signal-pulse"/><span><b>Evidence mode</b><small>Local reference search</small></span></div>
      <div className="profile-mini"><div className="profile-avatar">DS</div><span><b>Dr. Shafy</b><small>Clinician workspace</small></span><span className="dots">•••</span></div>
    </aside>
    <section className="workspace">
      <div className="topline"><div className="crumbs">Workspace <span>/</span> {nav.find(x=>x.href===active)?.label ?? "Clinical workspace"}</div><div className="top-actions"><span className="demo-chip"><i/> PROTOTYPE · SYNTHETIC DATA ONLY</span><span className="language-pair">EN <span>/</span> ع</span><span className="top-small-count"><Users size={13}/>{patients.length} demo patients</span></div></div>
      <main className="page-content">{children}<footer className="app-footer"><span>✳ MIA CLINICAL OS <span className="footer-divider">/</span> OB-GYN EDITION</span><span>Prototype · Synthetic data only · Not for live patient care</span></footer></main>
    </section>
  </div>;
}

export function Eyebrow({children}:{children:ReactNode}) { return <div className="eyebrow"><span className="eyebrow-line"/>{children}</div>; }
export function PageHeading({eyebrow,title,description,action}:{eyebrow:string;title:string;description?:string;action?:ReactNode}) { return <header className="page-heading"><div><Eyebrow>{eyebrow}</Eyebrow><h1>{title}</h1>{description&&<p>{description}</p>}</div>{action}</header>; }
export function StatusPill({kind="neutral",children}:{kind?:"good"|"warn"|"neutral"|"blue";children:ReactNode}) { return <span className={`status-pill ${kind}`}><i/>{children}</span>; }
export function EmptyState({title,detail}:{title:string;detail:string}) { return <div className="empty-state"><FileText size={22}/><b>{title}</b><p>{detail}</p></div>; }
export function SourceTag({children}:{children:ReactNode}) { return <span className="source-tag">{children}</span>; }
export function DemoWarning({children}:{children:ReactNode}) { return <div className="demo-warning"><CircleAlert size={16}/><span>{children}</span></div>; }
export function MetricCard({label,value,detail,icon}:{label:string;value:string;detail:string;icon:ReactNode}) { return <article className="metric-card"><div className="metric-top"><span>{label}</span><span className="metric-icon mint-icon">{icon}</span></div><div className="metric-number">{value}</div><div className="metric-foot">{detail}</div></article>; }
export function SectionHeader({title,detail,href,linkText}:{title:string;detail?:string;href?:string;linkText?:string}) { return <div className="section-heading"><div><h2>{title}</h2>{detail&&<p>{detail}</p>}</div>{href&&<Link className="text-link" href={href}>{linkText??"View all"} <ArrowUpRight size={14}/></Link>}</div>; }
export { CheckCircle2, ShieldCheck, CalendarClock, ClipboardList, ArrowUpRight };
