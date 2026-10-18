"use client";
import { useEffect } from "react";
import Link from "next/link";
import { AlertTriangle, RotateCcw } from "lucide-react";
export default function ErrorPage({error,reset}:{error:Error&{digest?:string};reset:()=>void}){
 useEffect(()=>{console.error("Mia OB-GYN prototype error",error.digest??"no digest");},[error]);
 return <main className="not-found-screen"><span className="not-found-icon"><AlertTriangle size={22}/></span><p className="eyebrow">SAFE ERROR STATE</p><h1>We couldn’t load this workspace.</h1><p>No clinical conclusion was generated. Retry or return to the dashboard.</p><button className="button-primary" onClick={()=>reset()}><RotateCcw size={14}/> Try again</button> <Link className="button-quiet" href="/dashboard">Dashboard</Link></main>
}
