"use client";
import { useMemo, useState } from "react";
import { ArrowUpRight, BookOpen, ExternalLink, Filter, Search } from "lucide-react";
import { AppShell, PageHeading, SourceTag, StatusPill } from "@/components/app-shell";
import { loadObgynCatalog, sourceMatchesJurisdiction, type Jurisdiction } from "@/lib/evidence/catalog";

export default function EvidencePage(){
 const [query,setQuery]=useState("");const [jurisdiction,setJurisdiction]=useState<Jurisdiction>("EG");const [kind,setKind]=useState("all");
 const sources=loadObgynCatalog();
 const filtered=useMemo(()=>sources.filter(s=>{
  const text=`${s.title} ${s.publisher??""} ${s.topics.join(" ")} ${s.id}`.toLowerCase();
  const matches=!query.trim()||text.includes(query.toLowerCase());
  const scope=kind==="all"||s.ingest_status.toLowerCase().includes(kind)||s.reuse_rights.toLowerCase().includes(kind);
  return matches&&scope&&sourceMatchesJurisdiction(s,jurisdiction);
 }),[query,jurisdiction,kind,sources]);
 return <AppShell active="/evidence"><PageHeading eyebrow="KNOWLEDGE CENTER" title="Evidence library" description={`${sources.length} OB-GYN references · directory only, not a prescribing knowledge base.`}/>
 <div className="library-tools"><div className="search-panel"><Search size={16}/><input aria-label="Search evidence sources" placeholder="Search source, topic or publisher…" value={query} onChange={e=>setQuery(e.target.value)}/></div><label className="filter-select"><span>JURISDICTION</span><select value={jurisdiction} onChange={e=>setJurisdiction(e.target.value as Jurisdiction)}><option value="EG">Egypt first</option><option value="GLOBAL">Global references</option><option value="US">United States</option><option value="UK">United Kingdom</option></select></label><label className="filter-select"><span>RIGHTS / STATUS</span><select value={kind} onChange={e=>setKind(e.target.value)}><option value="all">All statuses</option><option value="link_only">Link-only</option><option value="commercial">Commercial rights</option><option value="review">Review</option><option value="candidate">Candidate</option></select></label></div>
 <div className="library-summary"><span><Filter size={14}/> {filtered.length} sources displayed</span><span>Directory match ≠ evidence quality</span></div>
 <div className="source-directory">{filtered.map(s=><article className="source-directory-card" key={s.id}><div className="source-card-head"><span className="source-book-icon"><BookOpen size={17}/></span><div className="source-card-title"><h3>{s.title}</h3><p>{s.publisher??"Publisher not recorded"}</p></div><ArrowUpRight size={14}/></div><div className="source-tags">{s.jurisdiction.map(j=><SourceTag key={j}>{j}</SourceTag>)}</div><p className="source-topics">{s.topics.slice(0,7).join(" · ")}</p><div className="source-meta"><span>{s.version??"Version/date not recorded"}</span><StatusPill kind={s.ingest_status.includes("rights_restricted")||s.ingest_status.includes("copyrighted")?"warn":"neutral"}>{s.ingest_status.replaceAll("_"," ")}</StatusPill></div><div className="source-meta"><span className="rights-line">{s.reuse_rights}</span><a href={s.url} target="_blank" rel="noreferrer">Open source <ExternalLink size={12}/></a></div></article>)}</div>
 <p className="page-disclaimer">Sources are not copied into the app. Individual rights, version, relevance, jurisdiction and clinical applicability must be verified before an evidence card can be approved.</p>
 </AppShell>
}
