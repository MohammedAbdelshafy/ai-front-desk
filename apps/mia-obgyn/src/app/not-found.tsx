import Link from "next/link";
import { ArrowLeft, SearchX } from "lucide-react";
export default function NotFound(){return <main className="not-found-screen"><span className="not-found-icon"><SearchX size={22}/></span><p className="eyebrow">RECORD NOT FOUND</p><h1>This page isn’t in the demo workspace.</h1><p>Check the synthetic record ID or return to the clinical dashboard.</p><Link className="button-primary" href="/dashboard"><ArrowLeft size={14}/> Back to dashboard</Link></main>}
