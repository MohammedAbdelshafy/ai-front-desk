import Link from "next/link";

const navItems = [
  { href: "/dashboard", label: "Overview", glyph: "◈" },
  { href: "/patients", label: "Patients", glyph: "◉" },
  { href: "/appointments", label: "Appointments", glyph: "◷" },
  { href: "/questionnaires", label: "Questionnaires", glyph: "▤" },
  { href: "/mia", label: "Mia chat", glyph: "✳" },
  { href: "/evidence", label: "Evidence library", glyph: "⌘" },
  { href: "/governance", label: "Safety & governance", glyph: "⛨" },
];

const focusCards = [
  { href: "/appointments/demo-appt-001", eyebrow: "09:30 · ANTENATAL REVIEW", title: "Antenatal follow-up", patient: "Demo Patient 01", status: "Questionnaire received", color: "mint" },
  { href: "/appointments/demo-appt-002", eyebrow: "11:00 · POSTPARTUM REVIEW", title: "Postpartum check-in", patient: "Demo Patient 02", status: "Review intake", color: "blue" },
  { href: "/appointments/demo-appt-003", eyebrow: "12:15 · GYNAECOLOGY", title: "Gynaecology consultation", patient: "Demo Patient 03", status: "Awaiting responses", color: "violet" },
];

export default function HomePage() {
  return (
    <main className="app-frame">
      <aside className="sidebar">
        <Link className="brand-lockup" href="/" aria-label="Mia OB-GYN home">
          <span className="brand-emblem" aria-hidden="true"><span>m</span><i /></span>
          <span className="brand-word">mia<span>.</span><small>WOMEN&apos;S HEALTH OS</small></span>
        </Link>
        <div className="clinic-selector">
          <span className="clinic-orb">+</span><span><b>Dr. Shafy&apos;s Clinic</b><small>OB-GYN · Egypt</small></span><span className="chevron">⌄</span>
        </div>
        <div className="nav-label">WORKSPACE</div>
        <nav className="main-nav" aria-label="Main navigation">
          {navItems.map((item) => <Link key={item.href} href={item.href} className={item.href === "/dashboard" ? "nav-item active" : "nav-item"}><span className="nav-glyph" aria-hidden="true">{item.glyph}</span>{item.label}{item.href === "/appointments" && <span className="nav-count">3</span>}</Link>)}
        </nav>
        <div className="sidebar-spacer" />
        <div className="sidebar-signal"><span className="signal-pulse" /><span><b>Evidence mode</b><small>Local reference search</small></span></div>
        <div className="profile-mini"><div className="profile-avatar">DS</div><span><b>Dr. Shafy</b><small>Clinician workspace</small></span><span className="dots">•••</span></div>
      </aside>
      <section className="workspace">
        <div className="topline"><div className="crumbs">Workspace <span>/</span> Overview</div><div className="top-actions"><span className="demo-chip"><i /> PROTOTYPE · SYNTHETIC DATA ONLY</span><button className="icon-button" aria-label="Notifications" type="button">♧<i /></button><button className="language-toggle" type="button" aria-label="Language selector">EN <span>⌄</span></button></div></div>
        <div className="page-content">
          <header className="welcome-row"><div><div className="eyebrow"><span className="eyebrow-line" /> SUNDAY, 18 OCTOBER 2026</div><h1>Your clinic,<br/><em>in a new light.</em></h1><p className="welcome-copy">Good evening, Dr. Shafy. Your women&apos;s health workspace is ready.</p></div><div className="hero-orbit" aria-hidden="true"><div className="orbit orbit-one" /><div className="orbit orbit-two" /><div className="orbit orbit-three" /><div className="orbit-core"><div className="core-eye eye-left" /><div className="core-eye eye-right" /><div className="core-mouth" /><span className="core-spark">✦</span></div><span className="orbit-label orbit-label-one">MIA / 01</span><span className="orbit-label orbit-label-two">CLINICAL COMPANION</span></div></header>
          <section className="metric-grid" aria-label="Today's overview">
            <article className="metric-card"><div className="metric-top"><span>APPOINTMENTS TODAY</span><span className="metric-icon mint-icon">◷</span></div><div className="metric-number">08<span>/12</span></div><div className="metric-foot"><span className="metric-bar"><i style={{width:"66%"}} /></span><span>4 upcoming</span></div></article>
            <article className="metric-card"><div className="metric-top"><span>INTAKE RECEIVED</span><span className="metric-icon blue-icon">▤</span></div><div className="metric-number">06<span> of 08</span></div><div className="metric-foot"><span className="metric-status-dot" /> 2 still pending</div></article>
            <article className="metric-card"><div className="metric-top"><span>REVIEW QUEUE</span><span className="metric-icon violet-icon">✳</span></div><div className="metric-number">03</div><div className="metric-foot"><span className="small-muted">Questionnaires to check</span><Link href="/questionnaires">Open queue ↗</Link></div></article>
            <article className="metric-card"><div className="metric-top"><span>EVIDENCE LIBRARY</span><span className="metric-icon gold-icon">⌘</span></div><div className="metric-number">23<span> refs</span></div><div className="metric-foot"><span className="metric-status-dot gold-dot" /> Source directory only</div></article>
          </section>
          <div className="section-heading"><div><div className="eyebrow">CLINICAL FLOW</div><h2>Today&apos;s appointments <span className="heading-count">03 DEMO CASES</span></h2></div><Link className="text-link" href="/appointments">View all appointments <span>↗</span></Link></div>
          <section className="appointment-grid" aria-label="Demo appointments">
            {focusCards.map((card, i) => <Link href={card.href} className="appointment-card" key={card.href}><div className="appointment-kicker"><span className={`case-symbol ${card.color}`}>{i === 0 ? "◌" : i === 1 ? "✧" : "⌖"}</span><span>{card.eyebrow}</span><span className="card-menu">•••</span></div><h3>{card.title}</h3><p>{card.patient}</p><div className="appointment-divider" /><div className="appointment-status"><span className={i === 1 ? "status-dot blue-status" : i === 2 ? "status-dot muted-status" : "status-dot"} />{card.status}<span className="row-arrow">↗</span></div></Link>)}
          </section>
          <section className="lower-grid">
            <article className="panel chat-launch"><div className="panel-top"><div><div className="eyebrow">YOUR CLINICAL COMPANION</div><h2>Ask Mia.</h2></div><div className="chat-mini-orb">✳</div></div><p>Search trusted women&apos;s health references, explore evidence, and see the sources behind every result.</p><div className="quick-prompts"><Link href="/mia?q=hypertension%20in%20pregnancy">Hypertension in pregnancy <span>↗</span></Link><Link href="/mia?q=medicine%20during%20breastfeeding">Medicine &amp; breastfeeding <span>↗</span></Link><Link href="/mia?q=postpartum%20bleeding">Postpartum bleeding guidance <span>↗</span></Link></div><Link href="/mia" className="primary-link">Open Mia chat <span>↗</span></Link></article>
            <article className="panel readiness-panel"><div className="eyebrow">SAFETY BY DESIGN</div><h2>Trust is built<br/>into the workflow.</h2><p>The demo uses fictional records and a curated source directory. It does not prescribe or make live clinical decisions.</p><div className="readiness-row"><span className="readiness-icon">✓</span><span><b>Source provenance</b><small>Every reference has a source link</small></span><span className="ready-state">ACTIVE</span></div><div className="readiness-row"><span className="readiness-icon warn">!</span><span><b>Clinical pathways</b><small>Require clinician approval</small></span><span className="review-state">PENDING</span></div><Link href="/governance" className="text-link">Read safety &amp; governance <span>↗</span></Link></article>
          </section>
          <footer className="app-footer"><span>✳ MIA CLINICAL OS <span className="footer-divider">/</span> OB-GYN EDITION</span><span>Prototype · Synthetic data only · Not for live patient care</span></footer>
        </div>
      </section>
    </main>
  );
}
