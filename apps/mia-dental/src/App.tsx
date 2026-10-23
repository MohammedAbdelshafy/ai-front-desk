import { useMemo, useState, type FormEvent, type ReactNode } from 'react';
import {
  Activity,
  AlertTriangle,
  BookOpen,
  Check,
  ChevronRight,
  ClipboardCheck,
  ExternalLink,
  FileText,
  FlaskConical,
  HeartPulse,
  Info,
  Pill,
  Search,
  ShieldCheck,
  Stethoscope,
} from 'lucide-react';
import type { LucideIcon } from 'lucide-react';

type Tab = 'overview' | 'medication' | 'research' | 'sources';
type Jurisdiction = 'EG' | 'US';
type PregnancyStatus = 'unknown' | 'yes' | 'no' | 'not_applicable';

type NavItem = { id: Tab; label: string; icon: LucideIcon };
type ReferenceSource = {
  id: string;
  title: string;
  publisher: string;
  category: string;
  url: string;
  description: string;
  note: string;
};

const NAV: NavItem[] = [
  { id: 'overview', label: 'Overview', icon: Activity },
  { id: 'medication', label: 'Medication review', icon: Pill },
  { id: 'research', label: 'Trials & research', icon: FlaskConical },
  { id: 'sources', label: 'Information centers', icon: BookOpen },
];

/* Clinical governance must approve real pathway entries before this catalog changes. */
const APPROVED_DENTAL_PATHWAYS: readonly never[] = [];

const SOURCES: ReferenceSource[] = [
  {
    id: 'ada-pain',
    title: 'Acute dental pain management guideline',
    publisher: 'American Dental Association',
    category: 'CLINICAL GUIDELINE',
    url: 'https://www.ada.org/resources/research/science/evidence-based-dental-research/pain-management-guideline',
    description:
      'Guideline and living-guideline resources for acute oral pain in children, adolescents and adults.',
    note: 'US professional guidance. Check the population, current version and local applicability before use.',
  },
  {
    id: 'ada-antibiotics',
    title: 'Antibiotics for dental pain and swelling',
    publisher: 'American Dental Association',
    category: 'ANTIBIOTIC STEWARDSHIP',
    url: 'https://www.ada.org/resources/research/science/evidence-based-dental-research/antibiotics-for-dental-pain-and-swelling',
    description:
      'Evidence-based resources on antibiotic use in urgent pulpal/periapical pain and intraoral swelling.',
    note: 'A guideline is an input to clinician review, not a substitute for diagnosis, local policy or an individualized decision.',
  },
  {
    id: 'ada-stewardship',
    title: 'Antibiotic stewardship',
    publisher: 'American Dental Association',
    category: 'SAFETY & STEWARDSHIP',
    url: 'https://www.ada.org/resources/ada-library/oral-health-topics/antibiotic-stewardship',
    description:
      'Guidance on appropriate antibiotic use, risk factors, adverse effects and stewardship in dentistry.',
    note: 'Check the newest statement and intended population before applying a recommendation.',
  },
  {
    id: 'dailymed',
    title: 'DailyMed drug labeling',
    publisher: 'U.S. National Library of Medicine',
    category: 'OFFICIAL LABELS',
    url: 'https://dailymed.nlm.nih.gov/dailymed/',
    description:
      'Submitted labeling, including indications, contraindications, warnings, interactions and dosage sections.',
    note: 'US labeling does not establish Egyptian registration, local availability or Egypt-specific prescribing rules.',
  },
  {
    id: 'lactmed',
    title: 'LactMed',
    publisher: 'U.S. National Library of Medicine',
    category: 'LACTATION INFORMATION',
    url: 'https://www.ncbi.nlm.nih.gov/books/NBK501922/',
    description:
      'Drug-specific literature about breast-milk levels, possible infant effects and reported alternatives.',
    note: 'Lactation information is not a pregnancy-safety guarantee or a substitute for clinical review.',
  },
  {
    id: 'eda-info',
    title: 'Drug Information Center',
    publisher: 'Egyptian Drug Authority',
    category: 'EGYPT · MEDICINE INFORMATION',
    url: 'https://edaegypt.gov.eg/en/about-us/home-page-services/home-page-services/inquire-about-reliable-drug-information/',
    description:
      'Egyptian Pharmaceutical Information Center for medicine and pharmaceutical-product information inquiries.',
    note: 'The official page lists 02 2535 4188 and did.admin@edaegypt.gov.eg, Sunday–Thursday, 09:00–15:00. Verify details on the live page.',
  },
  {
    id: 'eda-guidance',
    title: 'Regulatory and safety guidance',
    publisher: 'Egyptian Drug Authority',
    category: 'EGYPT · REGULATORY',
    url: 'https://edaegypt.gov.eg/en/the-regulatory-reference-of-the-egyptian-drug-authority-eda/guidance/',
    description:
      'Egypt-specific medicine-regulation and safety reference material.',
    note: 'Use current Egyptian registration and product-information sources for local decisions.',
  },
  {
    id: 'eda-report',
    title: 'Report medicine side effects',
    publisher: 'Egyptian Drug Authority',
    category: 'EGYPT · PHARMACOVIGILANCE',
    url: 'https://edaegypt.gov.eg/en/about-us/home-page-services/home-page-services/reporting-side-effects/',
    description:
      'Official route for reporting suspected medicine or device adverse reactions.',
    note: 'For an emergency, activate local emergency care instead of waiting for a report to be processed.',
  },
  {
    id: 'ehc',
    title: 'Clinical learning resources',
    publisher: 'Egyptian Health Council',
    category: 'EGYPT · CLINICAL LEARNING',
    url: 'https://lms.ehc.gov.eg/lms/',
    description: 'Egypt-focused professional learning and reference discovery.',
    note: 'Confirm the latest applicable guideline and facility protocol independently.',
  },
  {
    id: 'who-guidelines',
    title: 'WHO guidelines',
    publisher: 'World Health Organization',
    category: 'INTERNATIONAL GUIDANCE',
    url: 'https://www.who.int/publications/who-guidelines',
    description:
      'International guideline discovery for background evidence review.',
    note: 'International guidance needs local applicability review before it supports a treatment decision.',
  },
  {
    id: 'who-ictrp',
    title: 'WHO ICTRP search portal',
    publisher: 'World Health Organization',
    category: 'TRIAL REGISTRY',
    url: 'https://trialsearch.who.int/Default.aspx',
    description:
      'Search trial registration information shared by participating registries.',
    note: 'Trial records are research data, not WHO endorsement or authorization to treat.',
  },
];

function makeQueryUrl(base: string, params: Record<string, string>): string {
  const search = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value.trim()) search.set(key, value.trim());
  });
  const suffix = search.toString();
  return suffix ? base + '?' + suffix : base;
}

function isUnknown(text: string): boolean {
  return /\b(unknown|not known|not assessed|not reconciled|not reviewed|unsure|uncertain|not confirmed)\b/i.test(
    text
  );
}

function Card({
  children,
  className = '',
}: {
  children: ReactNode;
  className?: string;
}) {
  return <section className={'panel ' + className}>{children}</section>;}

function PageHeader({
  eyebrow,
  title,
  description,
  right,
}: {
  eyebrow: string;
  title: string;
  description: string;
  right?: ReactNode;
}) {
  return (
    <div className="page-header">
      <div>
        <div className="eyebrow">{eyebrow}</div>
        <h1>{title}</h1>
        <p>{description}</p>
      </div>
      {right ? <div className="page-header-right">{right}</div> : null}
    </div>
  );
}

function SourceCard({ source }: { source: ReferenceSource }) {
  return (
    <article className="source-card">
      <span className="source-category">{source.category}</span>
      <h3>{source.title}</h3>
      <p className="source-publisher">{source.publisher}</p>
      <p>{source.description}</p>
      <p className="source-note">{source.note}</p>
      <a href={source.url} target="_blank" rel="noopener noreferrer">
        Open official source <ExternalLink size={14} />
      </a>
    </article>
  );
}

function App() {
  const [activeTab, setActiveTab] = useState<Tab>('overview');
  const [diagnosisCode, setDiagnosisCode] = useState('');
  const [diagnosisLabel, setDiagnosisLabel] = useState('');
  const [diagnosisConfirmed, setDiagnosisConfirmed] = useState(false);
  const [ageYears, setAgeYears] = useState('');
  const [jurisdiction, setJurisdiction] = useState<Jurisdiction>('EG');
  const [allergies, setAllergies] = useState('');
  const [allergiesReviewed, setAllergiesReviewed] = useState(false);
  const [currentMedicines, setCurrentMedicines] = useState('');
  const [medicinesReviewed, setMedicinesReviewed] = useState(false);
  const [pregnancyStatus, setPregnancyStatus] =
    useState<PregnancyStatus>('unknown');
  const [renalStatus, setRenalStatus] = useState('unknown');
  const [hepaticStatus, setHepaticStatus] = useState('unknown');
  const [localProtocolConfirmed, setLocalProtocolConfirmed] = useState(false);
  const [caseSubmitted, setCaseSubmitted] = useState(false);

  const [condition, setCondition] = useState('');
  const [intervention, setIntervention] = useState('');
  const [trialLocation, setTrialLocation] = useState('Egypt');
  const [researchSearched, setResearchSearched] = useState(false);
  const [researchError, setResearchError] = useState('');

  const age = Number(ageYears);
  const ageComplete =
    ageYears.trim() !== '' && Number.isInteger(age) && age >= 0 && age <= 130;
  const allergiesComplete =
    allergiesReviewed && allergies.trim() !== '' && !isUnknown(allergies);
  const medicinesComplete =
    medicinesReviewed &&
    currentMedicines.trim() !== '' &&
    !isUnknown(currentMedicines);

  const blockers = useMemo(() => {
    const values: string[] = [];
    if (!diagnosisCode.trim())
      values.push('Enter the exact clinician-used diagnosis code.');
    if (!diagnosisLabel.trim())
      values.push(
        'Enter the diagnosis label confirmed by the responsible dentist.'
      );
    if (!diagnosisConfirmed)
      values.push('Confirm the diagnosis was made by the responsible dentist.');
    if (!ageComplete) values.push('Enter a valid age in years.');
    if (!allergiesComplete)
      values.push(
        'Reconcile allergies/reactions; unknown is not the same as no allergy.'
      );
    if (!medicinesComplete)
      values.push('Reconcile current medicines and supplements.');
    if (pregnancyStatus === 'unknown')
      values.push(
        'Confirm pregnancy/lactation relevance with the responsible clinician.'
      );
    if (renalStatus === 'unknown')
      values.push(
        'Review renal function or record clinician-confirmed not applicable.'
      );
    if (hepaticStatus === 'unknown')
      values.push(
        'Review hepatic function or record clinician-confirmed not applicable.'
      );
    if (!localProtocolConfirmed)
      values.push(
        'Confirm the current local dental guideline/formulary for the selected jurisdiction.'
      );
    return values;
  }, [
    diagnosisCode,
    diagnosisLabel,
    diagnosisConfirmed,
    ageComplete,
    allergiesComplete,
    medicinesComplete,
    pregnancyStatus,
    renalStatus,
    hepaticStatus,
    localProtocolConfirmed,
  ]);

  const clinicalTrialsUrl = makeQueryUrl('https://clinicaltrials.gov/search', {
    cond: condition,
    term: intervention,
    locStr: trialLocation === 'Egypt' ? 'Egypt' : '',
  });
  const pubmedTerms = [
    condition.trim() ? '(' + condition.trim() + '[Title/Abstract])' : '',
    intervention.trim() ? '(' + intervention.trim() + '[Title/Abstract])' : '',
    '(Clinical Trial[Publication Type] OR Randomized Controlled Trial[Publication Type] OR Systematic Review[Publication Type] OR Meta-Analysis[Publication Type])',
  ]
    .filter(Boolean)
    .join(' AND ');
  const pubmedUrl = makeQueryUrl('https://pubmed.ncbi.nlm.nih.gov/', {
    term: pubmedTerms,
  });
  const dailyMedUrl = intervention.trim()
    ? makeQueryUrl('https://dailymed.nlm.nih.gov/dailymed/search.cfm', {
        query: intervention,
      })
    : 'https://dailymed.nlm.nih.gov/dailymed/';
  const lactMedUrl = intervention.trim()
    ? makeQueryUrl('https://www.ncbi.nlm.nih.gov/books/', {
        term: intervention + ' LactMed',
      })
    : 'https://www.ncbi.nlm.nih.gov/books/NBK501922/';

  const researchLinks: ReferenceSource[] = [
    {
      id: 'clinical-trials',
      title: 'ClinicalTrials.gov',
      publisher: 'U.S. National Library of Medicine',
      category: 'TRIAL REGISTRY',
      url: clinicalTrialsUrl,
      description:
        'Registered studies, eligibility criteria, study locations, status and posted results.',
      note: 'A registered trial is not proof of efficacy, safety, Egyptian registration or clinical appropriateness.',
    },
    {
      id: 'who-ictrp-search',
      title: 'WHO ICTRP search portal',
      publisher: 'World Health Organization',
      category: 'TRIAL REGISTRY',
      url: 'https://trialsearch.who.int/Default.aspx',
      description: 'Cross-registry discovery of registered clinical trials.',
      note: 'Search the same topic in the portal and check related primary-registry records.',
    },
    {
      id: 'pubmed-research',
      title: 'PubMed clinical studies and reviews',
      publisher: 'U.S. National Library of Medicine',
      category: 'LITERATURE',
      url: pubmedUrl,
      description:
        'Find clinical trials, randomized trials, systematic reviews and meta-analyses.',
      note: 'Review the methods, population, comparator, outcomes, harms, uncertainty and publication status.',
    },
    {
      id: 'daily-med-search',
      title: 'DailyMed label search',      publisher: 'U.S. National Library of Medicine',
      category: 'MEDICINE INFORMATION',
      url: dailyMedUrl,
      description:
        'Search submitted labels for contraindications, warnings, interactions and dose context.',
      note: 'US label content may differ from registration and local product information in Egypt.',
    },
    {
      id: 'lactmed-search',
      title: 'NIH LactMed search',
      publisher: 'U.S. National Library of Medicine',
      category: 'LACTATION INFORMATION',
      url: lactMedUrl,
      description:
        'Find drug-specific lactation literature and possible infant-exposure information.',
      note: 'Lactation resources do not provide a general pregnancy-safety guarantee.',
    },
    {
      id: 'ada-pain-search',
      title: 'ADA acute dental pain guideline',
      publisher: 'American Dental Association',
      category: 'CLINICAL GUIDELINE',
      url: 'https://www.ada.org/resources/research/science/evidence-based-dental-research/pain-management-guideline',
      description:
        'Living guideline resources for acute dental pain management.',
      note: 'Check patient population, latest evidence update and local applicability.',
    },
    {
      id: 'ada-antibiotic-search',
      title: 'ADA antibiotic guideline',
      publisher: 'American Dental Association',
      category: 'ANTIBIOTIC STEWARDSHIP',
      url: 'https://www.ada.org/resources/research/science/evidence-based-dental-research/antibiotics-for-dental-pain-and-swelling',
      description:
        'Evidence-based guidance for urgent dental pain and intraoral swelling.',
      note: 'A trial match alone is never a reason to start an antibiotic.',
    },
  ];

  function resetCaseResult() {
    setCaseSubmitted(false);
  }

  function clearCase() {
    setDiagnosisCode('');
    setDiagnosisLabel('');
    setDiagnosisConfirmed(false);
    setAgeYears('');
    setJurisdiction('EG');
    setAllergies('');
    setAllergiesReviewed(false);
    setCurrentMedicines('');
    setMedicinesReviewed(false);
    setPregnancyStatus('unknown');
    setRenalStatus('unknown');
    setHepaticStatus('unknown');
    setLocalProtocolConfirmed(false);
    setCaseSubmitted(false);
  }

  function submitCase(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setCaseSubmitted(true);
  }

  function submitResearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!condition.trim() && !intervention.trim()) {
      setResearchSearched(false);
      setResearchError(
        'Enter a non-identifying condition/topic or medicine name.'
      );
      return;
    }
    setResearchError('');
    setResearchSearched(true);
  }

  const currentPage = NAV.find(item => item.id === activeTab);

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand-lockup">
          <div className="brand-symbol">
            <Stethoscope size={23} />
          </div>
          <div>
            <span className="brand-overline">DR. MIA</span>
            <strong>Dental OS</strong>
          </div>
        </div>
        <div className="workspace-pill">
          <span className="status-dot" /> CLINICIAN PROTOTYPE
        </div>
        <nav className="side-nav" aria-label="Main navigation">
          <span className="nav-section-label">WORKSPACE</span>
          {NAV.map(item => {
            const Icon = item.icon;
            return (
              <button
                type="button"
                key={item.id}
                className={
                  'nav-item' + (activeTab === item.id ? ' active' : '')
                }
                onClick={() => setActiveTab(item.id)}
              >
                <Icon size={17} strokeWidth={1.8} />
                <span>{item.label}</span>
                {activeTab === item.id ? (
                  <ChevronRight size={15} className="nav-arrow" />
                ) : null}
              </button>
            );
          })}
        </nav>
        <div className="sidebar-footer">
          <div className="sidebar-safe">
            <ShieldCheck size={16} />
            <span>
              Evidence-first
              <br />
              clinician control
            </span>
          </div>
          <p>Prototype only. No real patient data.</p>
        </div>
      </aside>

      <main className="main-area">
        <header className="topbar">
          <div className="crumb">
            <span>Dr. Mia</span>
            <ChevronRight size={14} />
            <strong>{currentPage?.label}</strong>
          </div>
          <div className="topbar-meta">
            <span className="meta-lock">
              <ShieldCheck size={14} /> SYNTHETIC DATA ONLY
            </span>
            <span className="avatar-chip">M</span>
          </div>
        </header>

        {activeTab === 'overview' ? (
          <div className="page-stack">
            <PageHeader
              eyebrow="DENTISTRY · EVIDENCE WORKSPACE"
              title="Clinical context first. Evidence second."
              description="A dentist-led workspace for reviewing guidance, discovering clinical trials and teaching from properly approved medication pathways."
              right={
                <span className="status-pill">
                  <span className="status-dot" /> Local demo build
                </span>
              }
            />
            <div className="hero-grid">
              <Card className="hero-card">
                <div className="hero-card-top">
                  <span className="hero-icon">
                    <HeartPulse size={19} />
                  </span>
                  <span className="micro-label">MEDICATION REVIEW ENGINE</span>
                </div>
                <div className="hero-number">
                  {APPROVED_DENTAL_PATHWAYS.length}
                </div>
                <h2>Approved medication pathways</h2>
                <p>
                  Nothing is shown as a medication candidate until the exact
                  diagnosis, jurisdiction, source, dentist review and
                  medication-safety review are approved.
                </p>
                <button
                  type="button"
                  className="button-primary"
                  onClick={() => setActiveTab('medication')}
                >
                  Open medication review <ChevronRight size={15} />                </button>
              </Card>
              <Card className="research-hero-card">
                <div className="hero-card-top">
                  <span className="hero-icon mint">
                    <FlaskConical size={19} />
                  </span>
                  <span className="micro-label">EVIDENCE DISCOVERY</span>
                </div>
                <h2>Trials &amp; information centers</h2>
                <p>
                  Build topic searches across registries, peer-reviewed
                  literature, official labels and Egypt-specific medicine
                  information.
                </p>
                <button
                  type="button"
                  className="button-secondary"
                  onClick={() => setActiveTab('research')}
                >
                  Open research navigator <ChevronRight size={15} />
                </button>
              </Card>
            </div>
            <div className="section-heading">
              <div>
                <span className="eyebrow">CLINICAL WORKFLOW</span>
                <h2>Keep the decision auditable</h2>
              </div>
            </div>
            <div className="workflow-grid">
              {[
                {
                  n: '01',
                  title: 'Confirm diagnosis',
                  text: 'The dentist enters the exact code. Mia does not diagnose from symptoms.',
                },
                {
                  n: '02',
                  title: 'Reconcile risk context',
                  text: 'Review allergies, current medicines and relevant factors before an approved pathway can be shown.',
                },
                {
                  n: '03',
                  title: 'Review the source',
                  text: 'Every enabled option must have current sources, jurisdiction, named reviewers and a review date.',
                },
                {
                  n: '04',
                  title: 'Dentist decides',
                  text: 'Mia teaches and compares reviewed evidence. It never writes or transmits a prescription.',
                },
              ].map(item => (
                <article className="workflow-card" key={item.n}>
                  <span>{item.n}</span>
                  <h3>{item.title}</h3>
                  <p>{item.text}</p>
                </article>
              ))}
            </div>
            <div className="warning-banner">
              <AlertTriangle size={19} />
              <div>
                <strong>Clinical guardrail is on</strong>
                <p>
                  There are currently zero approved medication pathways. A blank
                  catalog means no approved entry is available in this
                  prototype, not that medication is unnecessary.
                </p>
              </div>
            </div>
            <div className="section-heading">
              <div>
                <span className="eyebrow">REFERENCE STARTERS</span>
                <h2>Official sources to review</h2>
              </div>
              <button
                className="text-button"
                type="button"
                onClick={() => setActiveTab('sources')}
              >
                All information centers <ChevronRight size={14} />
              </button>
            </div>
            <div className="source-feature-grid">
              {SOURCES.slice(0, 3).map(source => (
                <SourceCard source={source} key={source.id} />
              ))}
            </div>
          </div>
        ) : null}

        {activeTab === 'medication' ? (
          <div className="page-stack">
            <PageHeader
              eyebrow="DENTAL PRESCRIBING COPILOT · REVIEW MODE"
              title="Medication pathway review"
              description="Enter a diagnosis already confirmed by a dentist. Mia checks context completeness and displays only appropriately approved pathway cards."
              right={
                <span className="count-badge">
                  <Pill size={14} /> {APPROVED_DENTAL_PATHWAYS.length} approved
                </span>
              }
            />
            <div className="warning-banner large">
              <AlertTriangle size={19} />
              <div>
                <strong>No medicines are enabled in this prototype.</strong>
                <p>
                  Use fictional case details only. The app does not select a
                  drug, calculate a dose, diagnose or create/sign/transmit a
                  prescription.
                </p>
              </div>
            </div>
            <Card className="form-panel">
              <div className="panel-title-row">
                <div>
                  <span className="eyebrow">STEP 1 · DIAGNOSIS</span>
                  <h2>Clinician-confirmed case context</h2>
                  <p>
                    All input remains in this browser tab. The form makes no API
                    calls and does not save submissions.
                  </p>
                </div>
                <span className="jurisdiction-chip">
                  {jurisdiction === 'EG' ? 'EGYPT · EG' : 'UNITED STATES · US'}
                </span>
              </div>
              <form onSubmit={submitCase}>
                <div className="form-grid">
                  <div className="form-field">
                    <label htmlFor="dental-diagnosis-code">
                      Exact diagnosis code
                    </label>
                    <input
                      id="dental-diagnosis-code"
                      value={diagnosisCode}
                      maxLength={80}
                      placeholder="Exact local code"
                      onChange={event => {
                        setDiagnosisCode(event.target.value);
                        resetCaseResult();
                      }}
                    />
                    <small>
                      Exact code only. A free-text label does not trigger fuzzy
                      medicine matching.
                    </small>
                  </div>
                  <div className="form-field">
                    <label htmlFor="dental-diagnosis-label">
                      Diagnosis label
                    </label>
                    <input
                      id="dental-diagnosis-label"
                      value={diagnosisLabel}
                      maxLength={160}
                      placeholder="Diagnosis confirmed by the dentist"
                      onChange={event => {
                        setDiagnosisLabel(event.target.value);
                        resetCaseResult();
                      }}
                    />
                  </div>
                  <div className="form-field">
                    <label htmlFor="dental-age">Age (years)</label>
                    <input
                      id="dental-age"
                      type="number"
                      min="0"
                      max="130"
                      step="1"
                      value={ageYears}
                      placeholder="Patient age"
                      onChange={event => {
                        setAgeYears(event.target.value);
                        resetCaseResult();
                      }}
                    />                  </div>
                  <div className="form-field">
                    <label htmlFor="dental-jurisdiction">Jurisdiction</label>
                    <select
                      id="dental-jurisdiction"
                      value={jurisdiction}
                      onChange={event => {
                        setJurisdiction(event.target.value as Jurisdiction);
                        resetCaseResult();
                      }}
                    >
                      <option value="EG">Egypt (EG)</option>
                      <option value="US">United States (US)</option>
                    </select>
                  </div>
                </div>
                <div className="checkbox-grid">
                  <label className="check-row">
                    <input
                      type="checkbox"
                      checked={diagnosisConfirmed}
                      onChange={event => {
                        setDiagnosisConfirmed(event.target.checked);
                        resetCaseResult();
                      }}
                    />
                    <span>
                      <strong>Diagnosis confirmed</strong>
                      <small>
                        Confirmed by the responsible dentist, not inferred by
                        Mia.
                      </small>
                    </span>
                  </label>
                  <label className="check-row">
                    <input
                      type="checkbox"
                      checked={allergiesReviewed}
                      onChange={event => {
                        setAllergiesReviewed(event.target.checked);
                        resetCaseResult();
                      }}
                    />
                    <span>
                      <strong>Allergies reviewed</strong>
                      <small>
                        Reported allergies and previous reactions reconciled.
                      </small>
                    </span>
                  </label>
                  <label className="check-row">
                    <input
                      type="checkbox"
                      checked={medicinesReviewed}
                      onChange={event => {
                        setMedicinesReviewed(event.target.checked);
                        resetCaseResult();
                      }}
                    />
                    <span>
                      <strong>Current medicines reviewed</strong>
                      <small>Includes prescriptions and supplements.</small>
                    </span>
                  </label>
                  <label className="check-row">
                    <input
                      type="checkbox"
                      checked={localProtocolConfirmed}
                      onChange={event => {
                        setLocalProtocolConfirmed(event.target.checked);
                        resetCaseResult();
                      }}
                    />
                    <span>
                      <strong>Local protocol checked</strong>
                      <small>
                        Current local guideline/formulary reviewed by the
                        dentist.
                      </small>
                    </span>
                  </label>
                </div>
                <div className="form-grid">
                  <div className="form-field">
                    <label htmlFor="dental-allergies">
                      Allergies and reactions (fictional)
                    </label>
                    <textarea
                      id="dental-allergies"
                      rows={3}
                      value={allergies}
                      maxLength={1000}
                      placeholder="e.g. none reported and confirmed; or synthetic allergy context"
                      onChange={event => {
                        setAllergies(event.target.value);
                        resetCaseResult();
                      }}
                    />
                  </div>
                  <div className="form-field">
                    <label htmlFor="dental-medicines">
                      Current medicines and supplements (fictional)
                    </label>
                    <textarea
                      id="dental-medicines"
                      rows={3}
                      value={currentMedicines}
                      maxLength={1000}
                      placeholder="e.g. none reported and confirmed; or synthetic medicine list"
                      onChange={event => {
                        setCurrentMedicines(event.target.value);
                        resetCaseResult();
                      }}
                    />
                  </div>
                  <div className="form-field">
                    <label htmlFor="dental-pregnancy">
                      Pregnancy/lactation context (where relevant)
                    </label>
                    <select
                      id="dental-pregnancy"
                      value={pregnancyStatus}
                      onChange={event => {
                        setPregnancyStatus(
                          event.target.value as PregnancyStatus
                        );
                        resetCaseResult();
                      }}
                    >
                      <option value="unknown">Unknown / not assessed</option>
                      <option value="yes">Relevant / present</option>
                      <option value="no">Reviewed, not present</option>
                      <option value="not_applicable">
                        Clinician-confirmed not applicable
                      </option>
                    </select>
                  </div>
                  <div className="form-field">
                    <label htmlFor="dental-renal">Renal function</label>
                    <select
                      id="dental-renal"
                      value={renalStatus}
                      onChange={event => {
                        setRenalStatus(event.target.value);
                        resetCaseResult();
                      }}
                    >
                      <option value="unknown">Unknown / not assessed</option>
                      <option value="normal">Known normal</option>
                      <option value="abnormal">Known abnormal</option>
                      <option value="not_applicable">
                        Clinician-confirmed not applicable
                      </option>
                    </select>
                  </div>
                  <div className="form-field">
                    <label htmlFor="dental-hepatic">Hepatic function</label>
                    <select
                      id="dental-hepatic"
                      value={hepaticStatus}
                      onChange={event => {
                        setHepaticStatus(event.target.value);
                        resetCaseResult();
                      }}
                    >
                      <option value="unknown">Unknown / not assessed</option>
                      <option value="normal">Known normal</option>
                      <option value="abnormal">Known abnormal</option>
                      <option value="not_applicable">
                        Clinician-confirmed not applicable
                      </option>
                    </select>
                  </div>
                </div>
                <div className="form-actions">
                  <button type="submit" className="button-primary">
                    <ClipboardCheck size={16} /> Review approved pathways
                  </button>
                  <button
                    type="button"                    className="button-quiet"
                    onClick={clearCase}
                  >
                    Clear review
                  </button>
                </div>
              </form>
            </Card>
            {caseSubmitted ? (
              <div className="review-results" aria-live="polite">
                {blockers.length > 0 ? (
                  <div className="result-blockers">
                    <div className="result-title">
                      <AlertTriangle size={17} />
                      <strong>
                        Review blocked · resolve the listed context first
                      </strong>
                    </div>
                    <ul>
                      {blockers.map(item => (
                        <li key={item}>{item}</li>
                      ))}
                    </ul>
                  </div>
                ) : (
                  <div className="empty-catalog">
                    <div className="empty-catalog-icon">
                      <ShieldCheck size={22} />
                    </div>
                    <span className="eyebrow">
                      EXACT CODE · {diagnosisCode.trim().toUpperCase()}
                    </span>
                    <h2>
                      No approved medication pathway is available for this code
                    </h2>
                    <p>
                      The approved dental catalog is empty. No medicine was
                      selected and no dose was calculated. This is a catalog
                      gap, not advice to start or withhold treatment.
                    </p>
                    <div className="context-summary">
                      <span>
                        <Check size={14} /> Dentist-confirmed diagnosis
                      </span>
                      <span>
                        <Check size={14} /> Allergy context reviewed
                      </span>
                      <span>
                        <Check size={14} /> Medicines reconciled
                      </span>
                      <span>
                        <Check size={14} /> Local protocol confirmed
                      </span>
                    </div>
                    <p className="next-step-copy">
                      Continue with the current local dental protocol or contact
                      a supervising dentist/pharmacist. A search match alone
                      cannot generate a medication recommendation.
                    </p>
                  </div>
                )}
                <Card className="teaching-structure">
                  <div className="panel-title-row">
                    <div>
                      <span className="eyebrow">REVIEW STANDARD</span>
                      <h2>What an approved teaching card must contain</h2>
                    </div>
                    <FileText size={19} />
                  </div>
                  <div className="teaching-grid">
                    {[
                      [
                        'Why consider',
                        'Indication and guideline rationale for this exact diagnosis.',
                      ],
                      [
                        'Mechanism & evidence',
                        'Mechanism, supporting evidence, uncertainty and alternatives.',
                      ],
                      [
                        'Adverse effects',
                        'Common effects, serious warnings and contraindications.',
                      ],
                      [
                        'Safety factors',
                        'Allergy, interaction, pregnancy/lactation and population-specific checks.',
                      ],
                      [
                        'Monitoring & counseling',
                        'Follow-up needs and clinician-reviewed patient counseling.',
                      ],
                      [
                        'Dose context',
                        'Official-label/guideline context after source review; no generated dose calculations.',
                      ],
                    ].map(item => (
                      <div className="teaching-item" key={item[0]}>
                        <h3>{item[0]}</h3>
                        <p>{item[1]}</p>
                      </div>
                    ))}
                  </div>
                  <p className="fine-print">
                    Every card also requires source version, jurisdiction, named
                    dentist reviewer, medication-safety reviewer and re-review
                    date.
                  </p>
                </Card>
              </div>
            ) : null}
          </div>
        ) : null}

        {activeTab === 'research' ? (
          <div className="page-stack">
            <PageHeader
              eyebrow="RESEARCH INTELLIGENCE"
              title="Clinical trials &amp; evidence search"
              description="Build separate public-source searches from a condition and optional intervention. Mia does not scrape results or translate them into a prescription."
              right={
                <span className="status-pill">
                  <FlaskConical size={14} /> Research only
                </span>
              }
            />
            <div className="warning-banner">
              <Info size={19} />
              <div>
                <strong>Clinical research is not prescribing approval</strong>
                <p>
                  Do not enter patient identifiers, real case histories or
                  confidential clinical data. Search terms are only sent to a
                  public source when you click that source link.
                </p>
              </div>
            </div>
            <Card className="form-panel">
              <form onSubmit={submitResearch}>
                <div className="panel-title-row">
                  <div>
                    <span className="eyebrow">SEARCH BUILDER</span>
                    <h2>One topic, several sources</h2>
                    <p>
                      Use registries for trial records and papers for reported
                      evidence and harms.
                    </p>
                  </div>
                </div>
                <div className="form-grid research-form-grid">
                  <div className="form-field">
                    <label htmlFor="research-condition">
                      Condition / research topic
                    </label>
                    <input
                      id="research-condition"
                      value={condition}
                      maxLength={180}
                      placeholder="e.g. dental pain, pulpitis, odontogenic infection"
                      onChange={event => {
                        setCondition(event.target.value);
                        setResearchSearched(false);
                        setResearchError('');
                      }}
                    />
                  </div>
                  <div className="form-field">
                    <label htmlFor="research-intervention">
                      Medicine / intervention (optional)
                    </label>
                    <input
                      id="research-intervention"
                      value={intervention}
                      maxLength={120}
                      placeholder="Generic medicine name or intervention"
                      onChange={event => {
                        setIntervention(event.target.value);
                        setResearchSearched(false);
                        setResearchError('');
                      }}
                    />                  </div>
                  <div className="form-field">
                    <label htmlFor="research-location">
                      Trial location focus
                    </label>
                    <select
                      id="research-location"
                      value={trialLocation}
                      onChange={event => {
                        setTrialLocation(event.target.value);
                        setResearchSearched(false);
                      }}
                    >
                      <option value="Egypt">Egypt</option>
                      <option value="Global">Global / any location</option>
                    </select>
                  </div>
                </div>
                {researchError ? (
                  <p className="field-error" role="status">
                    {researchError}
                  </p>
                ) : null}
                <div className="form-actions">
                  <button type="submit" className="button-primary">
                    <Search size={16} /> Build source searches
                  </button>
                  <button
                    type="button"
                    className="button-quiet"
                    onClick={() => {
                      setCondition('');
                      setIntervention('');
                      setTrialLocation('Egypt');
                      setResearchSearched(false);
                      setResearchError('');
                    }}
                  >
                    Clear search
                  </button>
                </div>
              </form>
            </Card>
            {researchSearched ? (
              <div className="research-results" aria-live="polite">
                <div className="section-heading">
                  <div>
                    <span className="eyebrow">PUBLIC SOURCES</span>
                    <h2>
                      Search links for “
                      {condition.trim() || intervention.trim()}”
                    </h2>
                    <p>
                      Open each source independently and review the full study,
                      version and applicability.
                    </p>
                  </div>
                </div>
                <div className="source-grid">
                  {researchLinks.map(link => (
                    <SourceCard source={link} key={link.id} />
                  ))}
                </div>
              </div>
            ) : (
              <div className="source-prompt">
                <div className="source-prompt-icon">
                  <Search size={21} />
                </div>
                <div>
                  <strong>Ready to build source searches</strong>
                  <p>
                    Enter a research topic, then open registry/literature links.
                    The app does not load research records into a
                    medicine-ranking system.
                  </p>
                </div>
              </div>
            )}
            <Card className="evidence-method">
              <div className="panel-title-row">
                <div>
                  <span className="eyebrow">HOW TO READ THE EVIDENCE</span>
                  <h2>Five checks before a source can support a pathway</h2>
                </div>
                <BookOpen size={20} />
              </div>
              <ol>
                <li>
                  Confirm study design, registration/status, recruitment
                  locations, eligibility and whether results are posted.
                </li>
                <li>
                  Find linked peer-reviewed reports and check for updates,
                  corrections or conflicting evidence.
                </li>
                <li>
                  Review the population, comparator, outcomes, harms,
                  limitations and certainty of evidence.
                </li>
                <li>
                  Check the current local guideline and product registration for
                  the intended jurisdiction. US labels do not establish Egypt
                  authorization.
                </li>
                <li>
                  Only a separate dentist and medication-safety review can
                  approve a narrow pathway. Trial evidence alone cannot activate
                  a medication card.
                </li>
              </ol>
            </Card>
          </div>
        ) : null}

        {activeTab === 'sources' ? (
          <div className="page-stack">
            <PageHeader
              eyebrow="REFERENCE DIRECTORY"
              title="Clinical information centers"
              description="Source-linked dental guidance, medicine labeling, lactation references and local regulatory contacts."
            />
            <div className="warning-banner">
              <ShieldCheck size={19} />
              <div>
                <strong>Prefer the local source for local decisions</strong>
                <p>
                  ADA and DailyMed are useful research sources, but do not
                  substitute for Egyptian product registration and local
                  protocols. Check source version and jurisdiction before use.
                </p>
              </div>
            </div>
            <div className="source-grid">
              {SOURCES.map(source => (
                <SourceCard source={source} key={source.id} />
              ))}
            </div>
            <Card className="contact-card">
              <div className="contact-icon">
                <HeartPulse size={19} />
              </div>
              <div>
                <span className="eyebrow">
                  EGYPT · OFFICIAL MEDICINE INFORMATION
                </span>
                <h2>Egyptian Drug Authority</h2>
                <p>
                  The EDA Drug Information Center lists these contacts on its
                  current official service page.
                </p>
                <div className="contact-lines">
                  <a href="tel:+20225354188">02 2535 4188</a>
                  <a href="mailto:did.admin@edaegypt.gov.eg">
                    did.admin@edaegypt.gov.eg
                  </a>
                  <span>Sunday–Thursday · 09:00–15:00</span>
                </div>
                <a
                  className="inline-link"
                  href="https://edaegypt.gov.eg/en/about-us/home-page-services/home-page-services/inquire-about-reliable-drug-information/"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  Verify details on the EDA website <ExternalLink size={14} />
                </a>
              </div>
            </Card>
          </div>
        ) : null}

        <footer className="app-footer">
          <div className="footer-brand">
            <Stethoscope size={16} />
            <span>Dr. Mia Dental OS</span>
          </div>
          <span>
            Local browser-only prototype · no patient records saved · no
            prescription workflow
          </span>          <span>v0.1 · Synthetic data only</span>
        </footer>
      </main>
    </div>
  );
}

export default App;
