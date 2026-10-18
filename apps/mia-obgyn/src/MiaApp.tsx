import { useEffect, useMemo, useRef, useState } from 'react';
import {
  Activity,
  AlertTriangle,
  ArrowDownRight,
  ArrowUpRight,
  Bell,
  BookOpen,
  Bot,
  CalendarClock,
  CalendarDays,
  Check,
  CheckCircle2,
  ChevronDown,
  ChevronRight,
  CircleHelp,
  ClipboardCheck,
  ClipboardList,
  Clock,
  FileText,
  Filter,
  HeartPulse,
  Home,
  Languages,
  Menu,
  MessageCircle,
  MoreHorizontal,
  Paperclip,
  Pill,
  Plus,
  Search,
  Send,
  Settings2,
  ShieldCheck,
  Sparkles,
  Stethoscope,
  UserRound,
  UsersRound,
  X,
  type LucideIcon,
} from 'lucide-react';
import {
  EVIDENCE_SOURCES,
  searchObgynSources,
  type EvidenceSource,
  type Jurisdiction,
} from './obgyn-data';

type Section =
  | 'overview'
  | 'patients'
  | 'appointments'
  | 'questionnaires'
  | 'mia'
  | 'evidence'
  | 'governance';
type Patient = {
  id: string;
  name: string;
  age: number;
  initials: string;
  stage: string;
  status: string;
  nextVisit: string;
  reason: string;
  allergyStatus: string;
  allergies: string;
  medicines: string;
  history: string[];
  pregnancy: string;
  email: string;
  lastVisit: string;
};
type Appointment = {
  id: string;
  patientId: string;
  title: string;
  time: string;
  date: string;
  status: string;
  room: string;
  duration: string;
  note: string;
};
type ChatMessage = {
  role: 'assistant' | 'user';
  text: string;
  sources?: EvidenceSource[];
  urgent?: boolean;
  context?: string;
};

const NAV: {
  id: Section;
  label: string;
  ar: string;
  icon: LucideIcon;
  group: string;
}[] = [
  {
    id: 'overview',
    label: 'Overview',
    ar: 'نظرة عامة',
    icon: Home,
    group: 'WORKSPACE',
  },
  {
    id: 'patients',
    label: 'Patients',
    ar: 'المريضات',
    icon: UsersRound,
    group: 'WORKSPACE',
  },
  {
    id: 'appointments',
    label: 'Appointments',
    ar: 'المواعيد',
    icon: CalendarDays,
    group: 'WORKSPACE',
  },
  {
    id: 'questionnaires',
    label: 'Questionnaires',
    ar: 'الاستبيانات',
    icon: ClipboardList,
    group: 'WORKSPACE',
  },
  {
    id: 'mia',
    label: 'Mia chat',
    ar: 'محادثة ميا',
    icon: MessageCircle,
    group: 'INTELLIGENCE',
  },
  {
    id: 'evidence',
    label: 'Evidence library',
    ar: 'مكتبة المراجع',
    icon: BookOpen,
    group: 'INTELLIGENCE',
  },
  {
    id: 'governance',
    label: 'Safety & readiness',
    ar: 'السلامة والجاهزية',
    icon: ShieldCheck,
    group: 'SYSTEM',
  },
];

const INITIAL_PATIENTS: Patient[] = [
  {
    id: 'M-OB-001',
    name: 'Demo Patient A',
    age: 29,
    initials: 'DA',
    stage: 'Antenatal · 28 weeks',
    status: 'Needs review',
    nextVisit: 'Today, 09:30',
    reason: 'Antenatal follow-up',
    allergyStatus: 'Unknown',
    allergies: 'Not confirmed in this synthetic chart',
    medicines: 'Medication list not reconciled',
    history: [
      'First antenatal appointment in this demo timeline',
      'Prior history: not yet reviewed',
    ],
    pregnancy: 'Synthetic example · 28 weeks',
    email: 'demo.patient.a@example.invalid',
    lastVisit: '12 Oct 2026',
  },
  {
    id: 'M-OB-002',
    name: 'Demo Patient B',
    age: 34,
    initials: 'DB',
    stage: 'Postpartum · day 4',
    status: 'Questionnaire pending',
    nextVisit: 'Today, 10:15',
    reason: 'Postpartum follow-up',
    allergyStatus: 'Unknown',
    allergies: 'Not confirmed in this synthetic chart',
    medicines: 'Post-discharge medicines require reconciliation',
    history: [
      'Synthetic postpartum visit',
      'Birth details are not clinically validated',
    ],
    pregnancy: 'Synthetic example · postpartum day 4',
    email: 'demo.patient.b@example.invalid',
    lastVisit: '14 Oct 2026',
  },
  {
    id: 'M-OB-003',
    name: 'Demo Patient C',
    age: 25,
    initials: 'DC',
    stage: 'Gynaecology',
    status: 'Ready for review',
    nextVisit: 'Today, 11:00',
    reason: 'Gynaecology consultation',
    allergyStatus: 'Patient-reported: unknown',
    allergies: 'No confirmed allergy information in this demo',
    medicines: 'Not collected in this synthetic example',
    history: [
      'Gynaecology consultation requested',
      'Cycle details pending intake',
    ],
    pregnancy: 'Not established in the synthetic record',
    email: 'demo.patient.c@example.invalid',
    lastVisit: '29 Sep 2026',
  },
  {
    id: 'M-OB-004',
    name: 'Demo Patient D',
    age: 31,
    initials: 'DD',
    stage: 'Antenatal · 12 weeks',
    status: 'Questionnaire complete',
    nextVisit: 'Today, 11:45',
    reason: 'First-trimester review',
    allergyStatus: 'Unknown',
    allergies: 'Not confirmed in this synthetic chart',
    medicines: 'Not reconciled',
    history: ['New synthetic patient in demo', 'Obstetric history incomplete'],
    pregnancy: 'Synthetic example · 12 weeks',
    email: 'demo.patient.d@example.invalid',
    lastVisit: 'First visit',
  },
  {
    id: 'M-OB-005',
    name: 'Demo Patient E',
    age: 27,
    initials: 'DE',
    stage: 'Gynaecology',
    status: 'Needs review',
    nextVisit: 'Today, 12:30',
    reason: 'Cycle symptoms review',
    allergyStatus: 'Unknown',
    allergies: 'Not confirmed in this synthetic chart',
    medicines: 'Not collected',
    history: ['Synthetic symptom review', 'No prior encounter detail in demo'],
    pregnancy: 'Not established in the synthetic record',
    email: 'demo.patient.e@example.invalid',
    lastVisit: '05 Oct 2026',
  },
];

const INITIAL_APPOINTMENTS: Appointment[] = [
  {
    id: 'APT-001',
    patientId: 'M-OB-001',
    title: 'Antenatal follow-up',
    time: '09:30',
    date: 'Today',
    status: 'Needs review',
    room: 'Room 02',
    duration: '20 min',
    note: 'Check intake completeness and reconcile medicines and allergy status.',
  },
  {
    id: 'APT-002',
    patientId: 'M-OB-002',
    title: 'Postpartum follow-up',
    time: '10:15',
    date: 'Today',
    status: 'Questionnaire pending',
    room: 'Room 01',
    duration: '25 min',
    note: 'Review patient-reported postpartum symptoms and source of discharge medicines.',
  },
  {
    id: 'APT-003',
    patientId: 'M-OB-003',
    title: 'Gynaecology consultation',
    time: '11:00',
    date: 'Today',
    status: 'Ready for review',
    room: 'Room 03',
    duration: '30 min',
    note: 'History-taking and clinician assessment.',
  },
  {
    id: 'APT-004',
    patientId: 'M-OB-004',
    title: 'First-trimester review',
    time: '11:45',
    date: 'Today',
    status: 'Questionnaire complete',
    room: 'Room 02',
    duration: '20 min',
    note: 'Review submitted questionnaire; verify all clinical history with patient.',
  },
  {
    id: 'APT-005',
    patientId: 'M-OB-005',
    title: 'Cycle symptoms review',
    time: '12:30',
    date: 'Today',
    status: 'Needs review',
    room: 'Room 04',
    duration: '20 min',
    note: 'Review symptom timeline and decide which questions need follow-up.',
  },
];

const QUESTION_SECTIONS = [
  {
    title: 'Visit & symptoms',
    items: [
      {
        id: 'reason',
        label: 'What brings you in today?',
        ar: 'ما سبب الزيارة اليوم؟',
        type: 'textarea',
        placeholder: 'Describe the main concern in your own words',
      },
      {
        id: 'onset',
        label: 'When did it begin?',
        ar: 'متى بدأت الأعراض؟',
        type: 'select',
        options: [
          'Today',
          '1–3 days ago',
          '4–7 days ago',
          'More than a week ago',
          'Not applicable / unsure',
        ],
      },
      {
        id: 'severity',
        label: 'How severe are the symptoms?',
        ar: 'ما شدة الأعراض؟',
        type: 'select',
        options: [
          'Mild',
          'Moderate',
          'Severe',
          'Unsure / prefer not to answer',
        ],
      },
    ],
  },
  {
    title: 'Pregnancy & reproductive history',
    items: [
      {
        id: 'pregnant',
        label: 'Are you currently pregnant?',
        ar: 'هل يوجد حمل حالي؟',
        type: 'select',
        options: ['Yes', 'No', 'Unsure', 'Prefer not to answer'],
      },
      {
        id: 'gestation',
        label: 'Gestational week, if known',
        ar: 'أسبوع الحمل إن كان معروفاً',
        type: 'number',
        placeholder: 'e.g. 18',
      },
      {
        id: 'lmp',
        label: 'First day of last menstrual period, if known',
        ar: 'أول يوم لآخر دورة شهرية',
        type: 'date',
      },
      {
        id: 'obstetric',
        label: 'Pregnancy / birth history (if relevant)',
        ar: 'تاريخ الحمل والولادة عند الحاجة',
        type: 'textarea',
        placeholder: 'Include only what you are comfortable sharing',
      },
      {
        id: 'breastfeeding',
        label: 'Are you breastfeeding?',
        ar: 'هل توجد رضاعة طبيعية؟',
        type: 'select',
        options: ['Yes', 'No', 'Not applicable', 'Unsure'],
      },
    ],
  },
  {
    title: 'Medicines & safety',
    items: [
      {
        id: 'allergy',
        label: 'Medicine allergies and what happened',
        ar: 'حساسية الأدوية ورد الفعل',
        type: 'textarea',
        placeholder:
          'Medicine name, reaction, and when it occurred; write unknown if unsure',
      },
      {
        id: 'medicines',
        label: 'Current medicines, vitamins and supplements',
        ar: 'الأدوية والفيتامينات الحالية',
        type: 'textarea',
        placeholder: 'Include strength and schedule if known; do not guess',
      },
      {
        id: 'history',
        label: 'Important medical conditions or prior reactions',
        ar: 'الأمراض المهمة أو التفاعلات السابقة',
        type: 'textarea',
        placeholder:
          'Relevant conditions, procedures, or previous medicine reactions',
      },
      {
        id: 'redflags',
        label:
          'Any severe bleeding, fainting, seizure, or severe breathing trouble now?',
        ar: 'هل يوجد نزيف شديد أو إغماء أو تشنج أو صعوبة تنفس شديدة الآن؟',
        type: 'select',
        options: ['No', 'Yes', 'Unsure / prefer to discuss with clinician'],
      },
    ],
  },
];

const GOVERNANCE_DOCS = [
  {
    id: 'GOV-01',
    title: 'Intended use & prohibited use',
    owner: 'Product + clinical lead',
    state: 'Draft required',
    description: 'Defines exactly what the OB-GYN prototype can and cannot do.',
  },
  {
    id: 'GOV-02',
    title: 'Data inventory & flow map',
    owner: 'Privacy lead',
    state: 'Not started',
    description:
      'What data are collected, why, where they go, and when they are deleted.',
  },
  {
    id: 'GOV-03',
    title: 'Patient and staff privacy notices',
    owner: 'Local counsel',
    state: 'Review required',
    description:
      'Jurisdiction-specific notices, lawful basis, patient rights, and processing transparency.',
  },
  {
    id: 'GOV-04',
    title: 'Security risk assessment',
    owner: 'Security lead',
    state: 'Not started',
    description:
      'Threat model, access boundaries, encryption, secrets, backups, and incident response.',
  },
  {
    id: 'GOV-05',
    title: 'Clinical hazard & validation plan',
    owner: 'OB-GYN lead + pharmacist',
    state: 'Not started',
    description:
      'Evidence quality, unsafe-answer evaluation, escalation, clinical validation and release approval.',
  },
  {
    id: 'GOV-06',
    title: 'Source rights register',
    owner: 'Content + legal review',
    state: 'Draft required',
    description:
      'License, attribution, source version, jurisdiction, and permission to adapt each source.',
  },
  {
    id: 'GOV-07',
    title: 'Regulatory classification memo',
    owner: 'Local regulatory counsel',
    state: 'Review required',
    description:
      'Assess applicable medical software, privacy and cross-border data requirements.',
  },
  {
    id: 'GOV-08',
    title: 'Vendor & AI-provider review',
    owner: 'Security + privacy lead',
    state: 'Blocked',
    description:
      'Must be reviewed before real patient context is sent to an external service.',
  },
];

const QUICK_PROMPTS = [
  'Find guidance for postpartum haemorrhage',
  'Preeclampsia: find relevant guidance',
  'Medicine information during breastfeeding',
  'Contraception eligibility reference',
];

function statusClass(status: string) {
  const s = status.toLowerCase();
  if (s.includes('ready') || s.includes('complete') || s.includes('approved'))
    return 'status status-green';
  if (s.includes('pending') || s.includes('review') || s.includes('draft'))
    return 'status status-amber';
  if (s.includes('blocked') || s.includes('not started'))
    return 'status status-muted';
  return 'status';
}

function Avatar({
  image,
  preset = 'ai',
  size = 'md',
}: {
  image: string | null;
  preset?: string;
  size?: string;
}) {
  if (image)
    return (
      <span className={'avatar avatar-' + size + ' avatar-photo'}>
        <img src={image} alt="Custom Mia avatar" />
      </span>
    );
  return (
    <span className={'avatar avatar-' + size + ' avatar-' + preset}>
      {preset === 'clinician' ? (
        <Stethoscope size={size === 'lg' ? 28 : 17} />
      ) : preset === 'neutral' ? (
        <HeartPulse size={size === 'lg' ? 28 : 17} />
      ) : (
        <Bot size={size === 'lg' ? 28 : 17} />
      )}
    </span>
  );
}

function MiaApp() {
  const [section, setSection] = useState<Section>('overview');
  const [patients] = useState<Patient[]>(INITIAL_PATIENTS);
  const [appointments] = useState<Appointment[]>(INITIAL_APPOINTMENTS);
  const [selectedPatientId, setSelectedPatientId] = useState('M-OB-001');
  const [selectedAppointmentId, setSelectedAppointmentId] = useState('APT-001');
  const [patientSearch, setPatientSearch] = useState('');
  const [locale, setLocale] = useState<'en' | 'ar'>('en');
  const [jurisdiction, setJurisdiction] = useState<Jurisdiction>('EG');
  const [avatarPreset, setAvatarPreset] = useState('ai');
  const [avatarImage, setAvatarImage] = useState<string | null>(null);
  const [showAvatarSettings, setShowAvatarSettings] = useState(false);
  const [toast, setToast] = useState('');
  const [answers, setAnswers] = useState<Record<string, string>>({
    pregnant: 'Yes',
    gestation: '28',
    breastfeeding: 'No',
    allergy: 'Unknown — confirm directly with patient',
    medicines: 'Not reconciled — ask patient to bring current list',
  });
  const [intakeSubmitted, setIntakeSubmitted] = useState(false);
  const [libraryQuery, setLibraryQuery] = useState('');
  const [chatQuery, setChatQuery] = useState('');
  const [chatContext, setChatContext] = useState('M-OB-001');
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      role: 'assistant',
      text: 'Hello, Doctor. I can quickly locate OB-GYN guidelines, medicine references and official source pages. This prototype retrieves references only; it has no approved medication pathways and cannot determine or prescribe the right medicine.',
    },
  ]);
  const [mobileNav, setMobileNav] = useState(false);
  const chatBottom = useRef<HTMLDivElement | null>(null);

  const selectedPatient =
    patients.find(p => p.id === selectedPatientId) || patients[0];
  const selectedAppointment =
    appointments.find(a => a.id === selectedAppointmentId) || appointments[0];
  const appointmentPatient =
    patients.find(p => p.id === selectedAppointment.patientId) ||
    selectedPatient;
  const labels = useMemo(
    () => ({
      overview: locale === 'ar' ? 'نظرة عامة' : 'Overview',
      patients: locale === 'ar' ? 'المريضات' : 'Patients',
      appointments: locale === 'ar' ? 'المواعيد' : 'Appointments',
      questionnaires: locale === 'ar' ? 'الاستبيانات' : 'Questionnaires',
      mia: locale === 'ar' ? 'محادثة ميا' : 'Mia chat',
      evidence: locale === 'ar' ? 'مكتبة المراجع' : 'Evidence library',
      governance: locale === 'ar' ? 'السلامة والجاهزية' : 'Safety & readiness',
    }),
    [locale]
  );

  useEffect(() => {
    document.documentElement.lang = locale;
    document.documentElement.dir = locale === 'ar' ? 'rtl' : 'ltr';
  }, [locale]);

  useEffect(() => {
    if (!toast) return;
    const timer = window.setTimeout(() => setToast(''), 3200);
    return () => window.clearTimeout(timer);
  }, [toast]);

  useEffect(() => {
    chatBottom.current?.scrollIntoView({ block: 'end', behavior: 'smooth' });
  }, [messages, section]);

  function goPatient(id: string) {
    setSelectedPatientId(id);
    const nextAppt = appointments.find(a => a.patientId === id);
    if (nextAppt) setSelectedAppointmentId(nextAppt.id);
    setChatContext(id);
    setSection('patients');
    setMobileNav(false);
  }

  function goAppointment(appt: Appointment) {
    setSelectedAppointmentId(appt.id);
    setSelectedPatientId(appt.patientId);
    setChatContext(appt.patientId);
    setSection('appointments');
    setMobileNav(false);
  }

  function showToast(message: string) {
    setToast(message);
  }

  function makeAnswer(query: string, patientId: string): ChatMessage {
    const results = searchObgynSources(query, jurisdiction, 6);
    const emergency =
      /(heavy bleeding|severe bleeding|haemorrhage|hemorrhage|seizure|collapse|unconscious|severe breathlessness|difficulty breathing|fainting|fits|convulsion)/i.test(
        query
      );
    const contextPatient = patients.find(patient => patient.id === patientId);
    const evidenceText = results.length
      ? 'I found ' +
        results.length +
        ' reference link(s) by matching your question to source titles and topic tags. Open the original source and confirm its current version, population, jurisdiction and local applicability.'
      : 'I did not find a clear match in the current source directory. Try a more specific topic or change the jurisdiction. No match is not evidence that a treatment is safe or that no guidance exists.';
    const text =
      (emergency
        ? 'URGENT SAFETY NOTE: if this describes an actual patient who may be deteriorating, activate the hospital’s local emergency pathway now. Do not wait for this prototype.\n\n'
        : '') +
      evidenceText +
      '\n\nClinical boundary: this is source discovery, not a validated clinical pathway. No medication is selected or prescribed. Verify diagnosis, allergies and reaction, current medicines, gestational/postpartum state, contraindications, relevant observations/labs and the locally approved protocol with the responsible clinician/pharmacist.';
    return {
      role: 'assistant',
      text,
      sources: results,
      urgent: emergency,
      context: contextPatient
        ? contextPatient.name +
          ' · synthetic record only. Context categories visible in the record: ' +
          contextPatient.stage +
          ', allergy status: ' +
          contextPatient.allergyStatus +
          ', medication status: ' +
          contextPatient.medicines +
          '.'
        : 'General reference search · no patient context attached.',
    };
  }

  function sendQuestion(question?: string) {
    const value = (question ?? chatQuery).trim();
    if (!value) return;
    const patientId = chatContext === 'none' ? '' : chatContext;
    const answer = makeAnswer(value, patientId);
    setMessages(previous => [
      ...previous,
      { role: 'user', text: value },
      answer,
    ]);
    setChatQuery('');
    setSection('mia');
  }

  const filteredPatients = patients.filter(patient =>
    (
      patient.name +
      ' ' +
      patient.id +
      ' ' +
      patient.reason +
      ' ' +
      patient.stage
    )
      .toLowerCase()
      .includes(patientSearch.toLowerCase())
  );
  const librarySources = searchObgynSources(libraryQuery, jurisdiction, 10);
  const questionnaireAnswered = Object.values(answers).filter(v =>
    v.trim()
  ).length;
  const questionnaireTotal = QUESTION_SECTIONS.reduce(
    (sum, s) => sum + s.items.length,
    0
  );
  const navItem = NAV.find(item => item.id === section);

  function renderHeader(
    title: string,
    subtitle: string,
    action?: React.ReactNode
  ) {
    return (
      <div className="page-heading">
        <div>
          <div className="eyebrow">
            WOMEN’S HEALTH WORKSPACE <span className="live-dot" />{' '}
            <span>DEMO MODE</span>
          </div>
          <h1>{title}</h1>
          <p>{subtitle}</p>
        </div>
        {action ? <div className="heading-action">{action}</div> : null}
      </div>
    );
  }

  function renderPatientRow(patient: Patient, compact = false) {
    const appt = appointments.find(a => a.patientId === patient.id);
    return (
      <button
        type="button"
        className={
          'patient-row ' +
          (selectedPatientId === patient.id ? 'patient-row-selected ' : '') +
          (compact ? 'patient-row-compact' : '')
        }
        key={patient.id}
        onClick={() => goPatient(patient.id)}
      >
        <span className="patient-avatar">{patient.initials}</span>
        <span className="patient-info">
          <strong>{patient.name}</strong>
          <small>
            {patient.id} <span className="dot-sep">·</span> {patient.stage}
          </small>
          {!compact ? (
            <small className="patient-reason">{patient.reason}</small>
          ) : null}
        </span>
        <span className="patient-row-end">
          {appt ? (
            <>
              <small>{appt.time}</small>
              <ChevronRight size={16} />
            </>
          ) : (
            <ChevronRight size={16} />
          )}
        </span>
      </button>
    );
  }

  function renderAppointmentRow(appt: Appointment) {
    const patient = patients.find(p => p.id === appt.patientId) || patients[0];
    return (
      <button
        type="button"
        className="appointment-row"
        key={appt.id}
        onClick={() => goAppointment(appt)}
      >
        <span className="appointment-time">
          <strong>{appt.time}</strong>
          <small>{appt.duration}</small>
        </span>
        <span className="appointment-mark">
          <span />
        </span>
        <span className="appointment-content">
          <strong>{appt.title}</strong>
          <small>
            {patient.name} · {appt.room}
          </small>
          <span className={statusClass(appt.status)}>{appt.status}</span>
        </span>
        <ChevronRight size={17} className="row-chevron" />
      </button>
    );
  }

  function renderOverview() {
    return (
      <>
        {renderHeader(
          locale === 'ar' ? 'صباح الخير، دكتورة' : 'Good morning, Doctor',
          'Your clinic at a glance. Synthetic demo data only; no real patient records are stored.',
          <button
            className="btn btn-primary"
            onClick={() => setSection('questionnaires')}
          >
            <Plus size={16} /> New intake
          </button>
        )}
        <div className="hero-panel">
          <div className="hero-orb hero-orb-one" />
          <div className="hero-orb hero-orb-two" />
          <div className="hero-content">
            <div className="hero-kicker">
              <Sparkles size={14} /> YOUR CLINICAL COPILOT
            </div>
            <h2>
              Clinical work, <em>in focus.</em>
            </h2>
            <p>
              Bring the appointment, patient-reported history and trusted
              reference sources into one clear workspace.
            </p>
            <div className="hero-actions">
              <button
                className="btn btn-light"
                onClick={() => setSection('mia')}
              >
                <MessageCircle size={16} /> Ask Mia
              </button>
              <button
                className="btn btn-ghost-light"
                onClick={() => setSection('patients')}
              >
                Open patient list <ArrowUpRight size={16} />
              </button>
            </div>
          </div>
          <div className="hero-avatar-wrap">
            <div className="hero-ring ring-a" />
            <div className="hero-ring ring-b" />
            <Avatar image={avatarImage} preset={avatarPreset} size="lg" />
            <span className="avatar-ping" />
          </div>
          <div className="hero-foot">
            <span>
              <span className="pulse-dot" /> SOURCE-FIRST MODE
            </span>
            <span>OB-GYN · EGYPT FIRST</span>
            <span>NO AUTO-PRESCRIBING</span>
          </div>
        </div>
        <div className="stat-grid">
          <div className="stat-card">
            <div className="stat-top">
              <span>Appointments today</span>
              <CalendarClock size={17} />
            </div>
            <strong>05</strong>
            <div className="stat-foot">
              <span className="stat-trend">
                <ArrowUpRight size={13} /> On schedule
              </span>
              <span>synthetic</span>
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-top">
              <span>Intakes to review</span>
              <ClipboardList size={17} />
            </div>
            <strong>03</strong>
            <div className="stat-foot">
              <span className="status status-amber">Needs attention</span>
              <span>synthetic</span>
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-top">
              <span>History gaps</span>
              <AlertTriangle size={17} />
            </div>
            <strong>04</strong>
            <div className="stat-foot">
              <span className="stat-trend stat-neutral">
                Allergy / medicine checks
              </span>
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-top">
              <span>Evidence sources</span>
              <BookOpen size={17} />
            </div>
            <strong>{EVIDENCE_SOURCES.length}</strong>
            <div className="stat-foot">
              <span className="stat-trend">Linked reference directory</span>
            </div>
          </div>
        </div>
        <div className="dashboard-grid">
          <section className="panel">
            <div className="panel-heading">
              <div>
                <h3>Upcoming appointments</h3>
                <p>Next patients in the synthetic schedule</p>
              </div>
              <button
                className="text-action"
                onClick={() => setSection('appointments')}
              >
                View schedule <ChevronRight size={14} />
              </button>
            </div>
            <div className="appointment-list">
              {appointments.slice(0, 4).map(renderAppointmentRow)}
            </div>
          </section>
          <section className="panel">
            <div className="panel-heading">
              <div>
                <h3>Patient review queue</h3>
                <p>Start with missing information</p>
              </div>
              <button
                className="icon-btn"
                aria-label="Open all patients"
                onClick={() => setSection('patients')}
              >
                <ArrowUpRight size={16} />
              </button>
            </div>
            <div className="mini-queue">
              {patients.slice(0, 3).map(patient => (
                <button
                  key={patient.id}
                  className="queue-card"
                  onClick={() => goPatient(patient.id)}
                >
                  <span className="queue-initials">{patient.initials}</span>
                  <span>
                    <strong>{patient.name}</strong>
                    <small>{patient.status}</small>
                  </span>
                  <span className="queue-arrow">
                    <ChevronRight size={15} />
                  </span>
                </button>
              ))}
            </div>
            <div className="thin-callout">
              <ShieldCheck size={16} />
              <span>
                Unknown is not the same as “no allergies”. Confirm directly with
                the patient.
              </span>
            </div>
          </section>
        </div>
        <div className="bottom-note">
          <div className="bottom-note-icon">
            <ShieldCheck size={18} />
          </div>
          <div>
            <strong>Prototype safety status</strong>
            <p>
              Fictional records only · no external AI calls · no treatment
              recommendations · not for live patient care.
            </p>
          </div>
          <button onClick={() => setSection('governance')}>
            Read readiness <ChevronRight size={14} />
          </button>
        </div>
      </>
    );
  }

  function renderPatientsPage() {
    return (
      <>
        {renderHeader(
          'Patients',
          'A single view of the history relevant to the next appointment.',
          <button
            className="btn btn-primary"
            onClick={() =>
              showToast(
                'Patient creation is disabled in the synthetic-only prototype.'
              )
            }
          >
            <Plus size={16} /> Add patient
          </button>
        )}
        <div className="patient-workspace">
          <section className="panel patient-directory">
            <div className="panel-heading">
              <div>
                <h3>Patient directory</h3>
                <p>{patients.length} synthetic records</p>
              </div>
              <span className="count-chip">
                {filteredPatients.length} shown
              </span>
            </div>
            <div className="search-field">
              <Search size={16} />
              <input
                value={patientSearch}
                onChange={event => setPatientSearch(event.target.value)}
                placeholder="Search name, demo ID, or visit type"
                aria-label="Search patients"
              />
            </div>
            <div className="directory-list">
              {filteredPatients.map(patient => (
                <div key={patient.id}>{renderPatientRow(patient, true)}</div>
              ))}
              {filteredPatients.length === 0 ? (
                <div className="empty-state">
                  No matching synthetic patient. Try another search.
                </div>
              ) : null}
            </div>
          </section>
          <section className="panel patient-profile">
            <div className="profile-cover">
              <div className="profile-glow" />
              <span className="profile-kicker">
                PATIENT PROFILE / SYNTHETIC
              </span>
              <div className="profile-main">
                <span className="patient-avatar patient-avatar-xl">
                  {selectedPatient.initials}
                </span>
                <div>
                  <h2>{selectedPatient.name}</h2>
                  <p>
                    {selectedPatient.id} <span className="dot-sep">·</span>{' '}
                    {selectedPatient.age} years{' '}
                    <span className="dot-sep">·</span> {selectedPatient.stage}
                  </p>
                  <span className={statusClass(selectedPatient.status)}>
                    {selectedPatient.status}
                  </span>
                </div>
              </div>
            </div>
            <div className="profile-tabs">
              <span className="active-tab">Overview</span>
              <span>History</span>
              <span>Medicines</span>
              <span>Questionnaires</span>
            </div>
            <div className="profile-body">
              <div className="profile-contact-grid">
                <div>
                  <span className="field-label">Email</span>
                  <strong>{selectedPatient.email}</strong>
                  <small>Reserved demo address</small>
                </div>
                <div>
                  <span className="field-label">Phone</span>
                  <strong>Not collected</strong>
                  <small>No contact service connected</small>
                </div>
                <div>
                  <span className="field-label">Last encounter</span>
                  <strong>{selectedPatient.lastVisit}</strong>
                  <small>Demo timeline</small>
                </div>
                <div>
                  <span className="field-label">Next visit</span>
                  <strong>{selectedPatient.nextVisit}</strong>
                  <small>{selectedPatient.reason}</small>
                </div>
              </div>
              <div className="section-subtitle">
                <h3>Clinical history summary</h3>
                <span className="source-label">SOURCE: SYNTHETIC</span>
              </div>
              <ul className="history-list">
                {selectedPatient.history.map((item, index) => (
                  <li key={index}>
                    <span className="history-bullet" />
                    {item}
                  </li>
                ))}
              </ul>
              <div className="safety-grid">
                <div className="safety-card safety-warning">
                  <span className="field-label">Allergies & reactions</span>
                  <strong>{selectedPatient.allergyStatus}</strong>
                  <p>{selectedPatient.allergies}</p>
                  <span className="status status-amber">Must confirm</span>
                </div>
                <div className="safety-card">
                  <span className="field-label">Current medicines</span>
                  <strong>Reconciliation needed</strong>
                  <p>{selectedPatient.medicines}</p>
                  <span className="source-label">
                    PATIENT / CLINICIAN CONFIRMATION REQUIRED
                  </span>
                </div>
              </div>
              <div className="section-subtitle">
                <h3>Reproductive health context</h3>
                <span className="source-label">DEMO ONLY</span>
              </div>
              <div className="repro-context">
                <HeartPulse size={18} />
                <div>
                  <strong>{selectedPatient.pregnancy}</strong>
                  <p>
                    Verify LMP, gestational age, obstetric history and current
                    status during the actual clinical visit.
                  </p>
                </div>
              </div>
              <div className="profile-actions">
                <button
                  className="btn btn-primary"
                  onClick={() => {
                    const appt = appointments.find(
                      a => a.patientId === selectedPatient.id
                    );
                    if (appt) goAppointment(appt);
                    else setSection('appointments');
                  }}
                >
                  <CalendarDays size={15} /> Open next appointment
                </button>
                <button
                  className="btn btn-secondary"
                  onClick={() => {
                    setChatContext(selectedPatient.id);
                    setSection('mia');
                  }}
                >
                  <Sparkles size={15} /> Ask Mia about references
                </button>
              </div>
            </div>
          </section>
        </div>
      </>
    );
  }

  function renderAppointmentsPage() {
    return (
      <>
        {renderHeader(
          'Appointments',
          'Review the visit, patient-reported history and outstanding checks.',
          <span className="date-pill">
            <CalendarDays size={14} /> Sunday · 18 October 2026
          </span>
        )}
        <div className="appointments-layout">
          <section className="panel schedule-panel">
            <div className="panel-heading">
              <div>
                <h3>Today’s schedule</h3>
                <p>Five fictional appointment entries</p>
              </div>
              <span className="count-chip">05 visits</span>
            </div>
            <div className="schedule-list">
              {appointments.map(renderAppointmentRow)}
            </div>
          </section>
          <section className="panel appointment-detail">
            <div className="detail-top">
              <div>
                <span className="field-label">APPOINTMENT ID</span>
                <h2>{selectedAppointment.id}</h2>
              </div>
              <span className={statusClass(selectedAppointment.status)}>
                {selectedAppointment.status}
              </span>
            </div>
            <div className="appointment-hero">
              <div className="appointment-icon">
                <CalendarClock size={22} />
              </div>
              <div>
                <h3>{selectedAppointment.title}</h3>
                <p>
                  {selectedAppointment.date} · {selectedAppointment.time} ·{' '}
                  {selectedAppointment.duration}
                </p>
                <span>{selectedAppointment.room}</span>
              </div>
            </div>
            <div className="appointment-patient">
              <div className="patient-avatar">
                {appointmentPatient.initials}
              </div>
              <div>
                <strong>{appointmentPatient.name}</strong>
                <p>
                  {appointmentPatient.id} · {appointmentPatient.stage}
                </p>
              </div>
              <button
                className="text-action"
                onClick={() => goPatient(appointmentPatient.id)}
              >
                Profile <ChevronRight size={14} />
              </button>
            </div>
            <div className="detail-section">
              <h3>Visit preparation</h3>
              <p>{selectedAppointment.note}</p>
            </div>
            <div className="checklist">
              <div>
                <span className="check-box check-box-open" />
                Pre-visit questionnaire{' '}
                <small>
                  {selectedAppointment.status === 'Questionnaire pending'
                    ? 'Pending completion'
                    : intakeSubmitted
                      ? 'Submitted in this demo'
                      : 'Review required'}
                </small>
              </div>
              <div>
                <span className="check-box check-box-open" />
                Allergy and reaction status{' '}
                <small>{appointmentPatient.allergyStatus}</small>
              </div>
              <div>
                <span className="check-box check-box-open" />
                Medication reconciliation <small>Not verified</small>
              </div>
              <div>
                <span className="check-box check-box-open" />
                Clinician assessment <small>Not recorded in demo</small>
              </div>
            </div>
            <div className="profile-actions">
              <button
                className="btn btn-primary"
                onClick={() => {
                  setSelectedPatientId(appointmentPatient.id);
                  setChatContext(appointmentPatient.id);
                  setSection('questionnaires');
                }}
              >
                <ClipboardList size={15} /> Review questionnaire
              </button>
              <button
                className="btn btn-secondary"
                onClick={() => {
                  setChatContext(appointmentPatient.id);
                  setSection('mia');
                }}
              >
                <MessageCircle size={15} /> Ask Mia for references
              </button>
            </div>
            <div className="thin-callout">
              <AlertTriangle size={16} />
              <span>
                No diagnosis, medicine choice or prescription is generated from
                this appointment.
              </span>
            </div>
          </section>
        </div>
      </>
    );
  }

  function renderQuestionnairesPage() {
    return (
      <>
        {renderHeader(
          'Pre-visit questionnaires',
          'Doctor-configurable intake, reviewed before the consultation.',
          <span className="status status-amber">
            <ClipboardCheck size={13} /> Demo flow only
          </span>
        )}
        <div className="questionnaire-hero">
          <div>
            <span className="eyebrow">PATIENT INTAKE / MOBILE PREVIEW</span>
            <h2>
              Get the story <em>before the visit.</em>
            </h2>
            <p>
              Structured questions help the clinician spot missing history. The
              patient’s answers remain patient-reported until verified.
            </p>
          </div>
          <div className="questionnaire-progress">
            <div className="progress-ring">
              <span>
                {Math.round(
                  (questionnaireAnswered / Math.max(1, questionnaireTotal)) *
                    100
                )}
                <small>%</small>
              </span>
            </div>
            <div>
              <strong>{intakeSubmitted ? 'Submitted' : 'In progress'}</strong>
              <small>
                {questionnaireAnswered} fields answered / saved in current
                session
              </small>
            </div>
          </div>
        </div>
        <div className="questionnaire-layout">
          <section className="panel questionnaire-form-panel">
            <div className="panel-heading">
              <div>
                <h3>OB-GYN initial intake</h3>
                <p>
                  Assigned to {selectedPatient.name} · {selectedPatient.id}
                </p>
              </div>
              <span className="source-label">TEMPLATE V1 · DRAFT</span>
            </div>
            <form
              onSubmit={event => {
                event.preventDefault();
                setIntakeSubmitted(true);
                showToast(
                  'Questionnaire marked submitted in this browser demo.'
                );
              }}
            >
              {QUESTION_SECTIONS.map((group, groupIndex) => (
                <div className="question-group" key={group.title}>
                  <div className="question-group-heading">
                    <span>0{groupIndex + 1}</span>
                    <h4>{group.title}</h4>
                  </div>
                  {group.items.map(item => {
                    if (item.id === 'gestation' && answers.pregnant !== 'Yes')
                      return null;
                    const value = answers[item.id] || '';
                    return (
                      <label className="form-field" key={item.id}>
                        <span>
                          {locale === 'ar' ? item.ar : item.label}
                          {[
                            'reason',
                            'pregnant',
                            'allergy',
                            'medicines',
                          ].includes(item.id) ? (
                            <i>Required</i>
                          ) : null}
                        </span>
                        {item.type === 'textarea' ? (
                          <textarea
                            rows={2}
                            value={value}
                            required={[
                              'reason',
                              'allergy',
                              'medicines',
                            ].includes(item.id)}
                            placeholder={item.placeholder}
                            onChange={e => {
                              setAnswers(previous => ({
                                ...previous,
                                [item.id]: e.target.value,
                              }));
                              setIntakeSubmitted(false);
                            }}
                          />
                        ) : item.type === 'select' ? (
                          <select
                            value={value}
                            required={['pregnant'].includes(item.id)}
                            onChange={e => {
                              setAnswers(previous => ({
                                ...previous,
                                [item.id]: e.target.value,
                              }));
                              setIntakeSubmitted(false);
                            }}
                          >
                            <option value="">Select an answer</option>
                            {item.options?.map(option => (
                              <option key={option} value={option}>
                                {option}
                              </option>
                            ))}
                          </select>
                        ) : (
                          <input
                            type={item.type === 'date' ? 'date' : 'number'}
                            min={item.type === 'number' ? 0 : undefined}
                            max={item.type === 'number' ? 45 : undefined}
                            value={value}
                            placeholder={item.placeholder}
                            onChange={e => {
                              setAnswers(previous => ({
                                ...previous,
                                [item.id]: e.target.value,
                              }));
                              setIntakeSubmitted(false);
                            }}
                          />
                        )}
                      </label>
                    );
                  })}
                </div>
              ))}
              <div className="intake-disclaimer">
                <AlertTriangle size={17} />
                <p>
                  If the patient reports severe bleeding, fainting, seizure or
                  severe breathing difficulty now, they should not wait for a
                  questionnaire response. Follow the clinic’s emergency pathway.
                </p>
              </div>
              {intakeSubmitted ? (
                <div className="success-inline">
                  <CheckCircle2 size={17} /> Submitted in this browser session.
                  Review every response with the patient before relying on it.
                </div>
              ) : null}
              <div className="form-actions">
                <span>Patient-reported · clinician verification required</span>
                <button className="btn btn-primary" type="submit">
                  <Check size={15} /> Mark demo intake submitted
                </button>
              </div>
            </form>
          </section>
          <aside className="panel questionnaire-side">
            <span className="eyebrow">TEMPLATE BUILDER</span>
            <h3>Template settings</h3>
            <div className="template-setting">
              <div>
                <strong>OB-GYN initial intake</strong>
                <small>10+ configurable questions</small>
              </div>
              <span className="status status-amber">Draft</span>
            </div>
            <div className="template-setting">
              <div>
                <strong>Antenatal follow-up</strong>
                <small>Gestational week, symptoms, medicines</small>
              </div>
              <button
                className="icon-btn"
                onClick={() =>
                  showToast('Template editor is a planned next build slice.')
                }
                aria-label="Open antenatal template settings"
              >
                <Settings2 size={16} />
              </button>
            </div>
            <div className="template-setting">
              <div>
                <strong>Postpartum check-in</strong>
                <small>Recovery, feeding, current symptoms</small>
              </div>
              <button
                className="icon-btn"
                onClick={() =>
                  showToast('Template editor is a planned next build slice.')
                }
                aria-label="Open postpartum template settings"
              >
                <Settings2 size={16} />
              </button>
            </div>
            <div className="thin-callout">
              <ShieldCheck size={16} />
              <span>
                Patient links, real submissions and secure storage are disabled
                in this prototype.
              </span>
            </div>
            <div className="template-metrics">
              <div>
                <span>Template version</span>
                <strong>v1.0 · Draft</strong>
              </div>
              <div>
                <span>Answers stored</span>
                <strong>Browser memory only</strong>
              </div>
            </div>
          </aside>
        </div>
      </>
    );
  }

  function renderSourceCard(source: EvidenceSource, compact = false) {
    return (
      <article
        className={'source-card ' + (compact ? 'source-card-compact' : '')}
        key={source.id}
      >
        <div className="source-card-top">
          <span className="source-type">{source.type}</span>
          <span className="source-scope">
            {source.jurisdictions[0] === 'EG'
              ? 'EGYPT'
              : source.jurisdictions[0] === 'US'
                ? 'UNITED STATES'
                : source.jurisdictions[0] === 'UK'
                  ? 'UNITED KINGDOM'
                  : 'GLOBAL REF'}
          </span>
        </div>
        <h4>{source.title}</h4>
        <div className="source-publisher">
          {source.publisher}
          {source.year ? ' · ' + source.year : ''}
        </div>
        <p>{source.note}</p>
        <div className="source-card-bottom">
          <span className="source-status">
            <span className="source-dot" /> Reference directory
          </span>
          <a href={source.url} target="_blank" rel="noopener noreferrer">
            Open source <ArrowUpRight size={13} />
          </a>
        </div>
      </article>
    );
  }

  function renderChatPage() {
    return (
      <>
        {renderHeader(
          'Mia evidence chat',
          'Ask a clinical question. Get reference links fast, with the source scope visible.',
          <span className="source-mode-pill">
            <span className="pulse-dot" /> LOCAL REFERENCE SEARCH
          </span>
        )}
        <div className="chat-layout">
          <section className="panel chat-panel">
            <div className="chat-topbar">
              <Avatar image={avatarImage} preset={avatarPreset} />
              <div>
                <strong>Mia · OB-GYN evidence assistant</strong>
                <small>
                  <span className="online-dot" /> Reference index ready ·
                  external AI disabled
                </small>
              </div>
              <span className="no-prescribing-pill">
                <ShieldCheck size={13} /> No auto-prescribing
              </span>
            </div>
            <div className="chat-controls">
              <label>
                <span>Jurisdiction</span>
                <select
                  value={jurisdiction}
                  onChange={e =>
                    setJurisdiction(e.target.value as Jurisdiction)
                  }
                >
                  <option value="EG">Egypt · EG</option>
                  <option value="GLOBAL">Global reference</option>
                  <option value="US">United States · US</option>
                  <option value="UK">United Kingdom · UK</option>
                </select>
              </label>
              <label>
                <span>Attach context</span>
                <select
                  value={chatContext}
                  onChange={e => setChatContext(e.target.value)}
                >
                  <option value="none">No patient context</option>
                  {patients.map(patient => (
                    <option key={patient.id} value={patient.id}>
                      {patient.name} · synthetic
                    </option>
                  ))}
                </select>
              </label>
              <div className="privacy-pill">
                <ShieldCheck size={14} /> No data leaves this demo
              </div>
            </div>
            <div className="context-notice">
              <span className="context-dot" />{' '}
              {chatContext === 'none'
                ? 'General search. No patient context attached.'
                : 'Synthetic case selected: ' +
                  (patients.find(p => p.id === chatContext)?.name || '') +
                  '. Only a small context summary is shown; no real patient data is used.'}
            </div>
            <div className="chat-transcript">
              {messages.map((message, index) => (
                <div
                  className={'message-row message-' + message.role}
                  key={index}
                >
                  <Avatar
                    image={message.role === 'assistant' ? avatarImage : null}
                    preset={
                      message.role === 'assistant' ? avatarPreset : 'clinician'
                    }
                  />
                  <div className="message-body">
                    <div className="message-author">
                      {message.role === 'assistant' ? 'Mia' : 'Doctor'}{' '}
                      <span>
                        {message.role === 'assistant'
                          ? 'Evidence assistant'
                          : 'You'}
                      </span>
                    </div>
                    <div
                      className={
                        'message-bubble ' +
                        (message.urgent ? 'message-urgent' : '')
                      }
                    >
                      {message.text
                        .split('\n')
                        .map((line, lineIndex) =>
                          line ? (
                            <p key={lineIndex}>{line}</p>
                          ) : (
                            <div className="message-space" key={lineIndex} />
                          )
                        )}
                    </div>
                    {message.context ? (
                      <div className="context-cite">
                        <CircleHelp size={13} /> Context used: {message.context}
                      </div>
                    ) : null}
                    {message.sources && message.sources.length ? (
                      <div className="chat-sources">
                        <div className="chat-sources-title">
                          <BookOpen size={14} /> Matching references{' '}
                          <span>{message.sources.length}</span>
                        </div>
                        {message.sources.map(source => (
                          <div className="chat-source-item" key={source.id}>
                            <div>
                              <strong>{source.title}</strong>
                              <small>
                                {source.publisher}
                                {source.year ? ' · ' + source.year : ''}
                              </small>
                            </div>
                            <a
                              href={source.url}
                              target="_blank"
                              rel="noopener noreferrer"
                              aria-label={'Open ' + source.title}
                            >
                              <ArrowUpRight size={15} />
                            </a>
                          </div>
                        ))}
                        <div className="no-pathway-note">
                          <AlertTriangle size={14} />
                          <span>
                            No approved medication pathway is configured in this
                            prototype. References are for clinician review, not
                            treatment instructions.
                          </span>
                        </div>
                      </div>
                    ) : null}
                  </div>
                </div>
              ))}
              <div ref={chatBottom} />
            </div>
            <div className="quick-prompts">
              <span>Try:</span>
              {QUICK_PROMPTS.map(prompt => (
                <button
                  type="button"
                  key={prompt}
                  onClick={() => sendQuestion(prompt)}
                >
                  {prompt}
                </button>
              ))}
            </div>
            <form
              className="chat-composer"
              onSubmit={event => {
                event.preventDefault();
                sendQuestion();
              }}
            >
              <div className="composer-inner">
                <input
                  aria-label="Ask Mia a question"
                  value={chatQuery}
                  onChange={event => setChatQuery(event.target.value)}
                  placeholder="Ask about a guideline, drug reference, pregnancy or lactation…"
                />
                <button
                  className="send-button"
                  type="submit"
                  aria-label="Send question"
                  disabled={!chatQuery.trim()}
                >
                  <Send size={17} />
                </button>
              </div>
              <div className="composer-footer">
                <span>
                  <ShieldCheck size={12} /> No real patient details. Prototype
                  uses local search.
                </span>
                <span>{chatQuery.length}/600</span>
              </div>
            </form>
          </section>
          <aside className="chat-sidebar">
            <div className="panel assistant-capability">
              <div className="capability-icon">
                <Sparkles size={19} />
              </div>
              <h3>How Mia answers</h3>
              <div className="capability-step">
                <span>01</span>
                <div>
                  <strong>Search the source index</strong>
                  <p>Local topic matching, no external AI call.</p>
                </div>
              </div>
              <div className="capability-step">
                <span>02</span>
                <div>
                  <strong>Show the original sources</strong>
                  <p>
                    Jurisdiction, publisher, year where known, and source link.
                  </p>
                </div>
              </div>
              <div className="capability-step">
                <span>03</span>
                <div>
                  <strong>Expose uncertainty</strong>
                  <p>
                    No match or missing patient facts never becomes a safety
                    claim.
                  </p>
                </div>
              </div>
              <div className="capability-footer">
                <ShieldCheck size={15} /> Reference discovery only
              </div>
            </div>
            <div className="panel context-card">
              <div className="panel-heading">
                <div>
                  <h3>Safety checklist</h3>
                  <p>Before acting on medication information</p>
                </div>
                <ShieldCheck size={18} />
              </div>
              {[
                'Confirm indication & diagnosis',
                'Confirm allergies and reaction',
                'Reconcile all current medicines',
                'Check pregnancy / postpartum stage',
                'Review contraindications & monitoring',
                'Verify the local approved protocol',
              ].map(item => (
                <div className="context-check" key={item}>
                  <span />
                  <small>{item}</small>
                </div>
              ))}
              <button
                className="text-action"
                onClick={() => setSection('governance')}
              >
                Read safety gates <ChevronRight size={14} />
              </button>
            </div>
          </aside>
        </div>
      </>
    );
  }

  function renderEvidencePage() {
    return (
      <>
        {renderHeader(
          'Evidence library',
          'Source directory for OB-GYN clinicians. Search results are relevance-ranked, not evidence-graded.',
          <span className="count-chip">{EVIDENCE_SOURCES.length} sources</span>
        )}
        <div className="evidence-filter-panel panel">
          <div className="search-field evidence-search">
            <Search size={17} />
            <input
              aria-label="Search evidence library"
              value={libraryQuery}
              onChange={e => setLibraryQuery(e.target.value)}
              placeholder="Search postpartum bleeding, pregnancy medicine, breastfeeding…"
            />
          </div>
          <label className="jurisdiction-filter">
            <span>Jurisdiction</span>
            <select
              value={jurisdiction}
              onChange={e => setJurisdiction(e.target.value as Jurisdiction)}
            >
              <option value="EG">Egypt · EG</option>
              <option value="GLOBAL">Global reference</option>
              <option value="US">United States · US</option>
              <option value="UK">United Kingdom · UK</option>
            </select>
          </label>
          <div className="filter-tags">
            <span>
              <Filter size={13} /> Indexed only
            </span>
            <span>HTTPS source links</span>
            <span>Rights review required</span>
          </div>
        </div>
        <div className="evidence-notice">
          <AlertTriangle size={16} />
          <p>
            <strong>
              Reference directory, not a prescribing knowledge base.
            </strong>{' '}
            Every item requires topic-specific review. Source availability does
            not grant commercial reuse rights, and search ranking is not a
            measure of clinical quality.
          </p>
        </div>
        {libraryQuery.trim() ? (
          <div className="result-caption">
            {librarySources.length} matching references for{' '}
            <strong>“{libraryQuery}”</strong> in{' '}
            {jurisdiction === 'EG'
              ? 'Egypt mode'
              : jurisdiction === 'GLOBAL'
                ? 'global mode'
                : jurisdiction === 'US'
                  ? 'US mode'
                  : 'UK mode'}
            .
          </div>
        ) : (
          <div className="result-caption">
            Browse recent / key sources or search a topic above.
          </div>
        )}
        <div className="evidence-grid">
          {(libraryQuery.trim()
            ? librarySources
            : EVIDENCE_SOURCES.filter(
                s =>
                  jurisdiction === 'GLOBAL' ||
                  s.jurisdictions.includes(jurisdiction) ||
                  s.jurisdictions.includes('GLOBAL') ||
                  s.jurisdictions.includes('GLOBAL_REFERENCE')
              ).slice(0, 9)
          ).map(source => renderSourceCard(source))}
        </div>
        {libraryQuery.trim() && librarySources.length === 0 ? (
          <div className="panel empty-state">
            <Search size={25} />
            <h3>No direct match</h3>
            <p>
              Try synonyms, a specific clinical topic, or the global reference
              scope. No match does not mean no evidence exists.
            </p>
          </div>
        ) : null}
      </>
    );
  }

  function renderGovernancePage() {
    const counts = {
      draft: GOVERNANCE_DOCS.filter(d => /draft/i.test(d.state)).length,
      review: GOVERNANCE_DOCS.filter(d => /review/i.test(d.state)).length,
      blocked: GOVERNANCE_DOCS.filter(d => /blocked|not started/i.test(d.state))
        .length,
    };
    return (
      <>
        {renderHeader(
          'Safety & readiness',
          'Launch gates and document owners. Templates are drafts, not proof of compliance.',
          <span className="status status-amber">
            <AlertTriangle size={13} /> Live use blocked
          </span>
        )}
        <div className="readiness-banner">
          <div className="readiness-symbol">
            <ShieldCheck size={22} />
          </div>
          <div>
            <h2>Prototype only · Not approved for clinical use</h2>
            <p>
              No production identity, encrypted clinical data store, local legal
              sign-off or clinically approved treatment pathways are connected.
              Do not enter real patient data.
            </p>
          </div>
          <span className="readiness-status">BLOCKED</span>
        </div>
        <div className="readiness-stats">
          <div className="panel">
            <span>Draft documents</span>
            <strong>{counts.draft}</strong>
            <small>Need an owner / review</small>
          </div>
          <div className="panel">
            <span>Review required</span>
            <strong>{counts.review}</strong>
            <small>Local legal / professional review</small>
          </div>
          <div className="panel">
            <span>Not started or blocked</span>
            <strong>{counts.blocked}</strong>
            <small>Must close before live use</small>
          </div>
        </div>
        <section className="panel governance-panel">
          <div className="panel-heading">
            <div>
              <h3>Readiness document register</h3>
              <p>
                Every item requires accountable review and evidence of sign-off.
              </p>
            </div>
            <span className="count-chip">{GOVERNANCE_DOCS.length} items</span>
          </div>
          <div className="governance-list">
            {GOVERNANCE_DOCS.map(doc => (
              <div className="governance-row" key={doc.id}>
                <span className="doc-icon">
                  <FileText size={18} />
                </span>
                <div className="governance-detail">
                  <strong>{doc.title}</strong>
                  <small>{doc.description}</small>
                  <span>Owner: {doc.owner}</span>
                </div>
                <span className={statusClass(doc.state)}>{doc.state}</span>
                <button
                  className="icon-btn"
                  aria-label={'Open ' + doc.title}
                  onClick={() =>
                    showToast(
                      'Draft template for ' +
                        doc.title +
                        ' is planned in the repository governance pack.'
                    )
                  }
                >
                  <ArrowUpRight size={15} />
                </button>
              </div>
            ))}
          </div>
        </section>
        <div className="governance-footer-grid">
          <div className="panel">
            <span className="eyebrow">CLINICAL GATE</span>
            <h3>Doctor + pharmacist review</h3>
            <p>
              Each medication pathway needs a named clinical owner,
              jurisdiction, source version, contraindications, monitoring,
              exclusions, review date and approval record.
            </p>
          </div>
          <div className="panel">
            <span className="eyebrow">DATA GATE</span>
            <h3>Privacy + security review</h3>
            <p>
              Set the hosting/data region, identity model, retention policy,
              transfer basis, vendor contracts and security controls before real
              patient records.
            </p>
          </div>
        </div>
      </>
    );
  }

  function renderAvatarSettings() {
    return (
      <div className="avatar-popover">
        <div className="popover-heading">
          <div>
            <strong>Personalize Mia</strong>
            <small>Visible only in this browser session</small>
          </div>
          <button
            className="icon-btn"
            onClick={() => setShowAvatarSettings(false)}
            aria-label="Close avatar settings"
          >            <X size={15} />
          </button>
        </div>
        <div className="preset-list">
          <button
            className={
              avatarPreset === 'ai' && !avatarImage
                ? 'preset-option preset-selected'
                : 'preset-option'
            }
            onClick={() => {
              setAvatarPreset('ai');
              setAvatarImage(null);
            }}
          >
            <Avatar image={null} preset="ai" />
            <span>
              <strong>AI companion</strong>
              <small>Neon assistant</small>
            </span>
            <Check size={15} />
          </button>
          <button
            className={
              avatarPreset === 'clinician' && !avatarImage
                ? 'preset-option preset-selected'
                : 'preset-option'
            }
            onClick={() => {
              setAvatarPreset('clinician');
              setAvatarImage(null);
            }}
          >
            <Avatar image={null} preset="clinician" />
            <span>
              <strong>Clinician</strong>
              <small>Medical persona</small>
            </span>
            <Check size={15} />
          </button>
          <button
            className={
              avatarPreset === 'neutral' && !avatarImage
                ? 'preset-option preset-selected'
                : 'preset-option'
            }
            onClick={() => {
              setAvatarPreset('neutral');
              setAvatarImage(null);
            }}
          >
            <Avatar image={null} preset="neutral" />
            <span>
              <strong>Wellness guide</strong>
              <small>Neutral assistant</small>
            </span>
            <Check size={15} />
          </button>
        </div>
        <label className="upload-avatar">
          Upload a portrait
          <input
            type="file"
            accept="image/png,image/jpeg,image/webp"
            onChange={event => {
              const file = event.target.files?.[0];
              if (!file) return;
              if (
                !['image/png', 'image/jpeg', 'image/webp'].includes(
                  file.type
                ) ||
                file.size > 8 * 1024 * 1024
              ) {
                showToast('Use a PNG, JPEG or WebP image under 8 MB.');
                event.target.value = '';
                return;
              }
              const reader = new FileReader();
              reader.onload = () =>
                setAvatarImage(
                  typeof reader.result === 'string' ? reader.result : null
                );
              reader.readAsDataURL(file);
            }}
          />
        </label>
        <p className="popover-privacy">
          Your portrait is previewed in your browser only. It is not uploaded to
          this app or sent to an AI service.
        </p>
      </div>
    );
  }

  return (
    <div className={'mia-app ' + (locale === 'ar' ? 'rtl-shell' : '')}>
      <aside className={'sidebar ' + (mobileNav ? 'sidebar-open' : '')}>
        <div className="brand-block">
          <div className="brand-mark">
            <Activity size={21} strokeWidth={2.6} />
          </div>
          <div>
            <strong>
              mia<span>clinic</span>
            </strong>
            <small>WOMEN’S HEALTH OS</small>
          </div>
          <button
            className="sidebar-close icon-btn"
            aria-label="Close navigation"
            onClick={() => setMobileNav(false)}
          >
            <X size={17} />
          </button>
        </div>
        <div className="clinic-switcher">
          <div className="clinic-avatar">OB</div>
          <div>
            <strong>OB-GYN · Egypt</strong>
            <small>Standalone specialty app</small>
          </div>
          <ChevronDown size={15} />
        </div>
        <nav className="main-nav" aria-label="Main navigation">
          {['WORKSPACE', 'INTELLIGENCE', 'SYSTEM'].map(group => (
            <div className="nav-group" key={group}>
              <span className="nav-group-title">{group}</span>
              {NAV.filter(item => item.group === group).map(item => (
                <button
                  key={item.id}
                  className={
                    'nav-item ' + (section === item.id ? 'nav-item-active' : '')
                  }
                  onClick={() => {
                    setSection(item.id);
                    setMobileNav(false);
                  }}
                >
                  <item.icon size={18} strokeWidth={1.8} />
                  <span>{locale === 'ar' ? item.ar : item.label}</span>
                  {item.id === 'questionnaires' ? <i>3</i> : null}
                  {section === item.id ? (
                    <span className="nav-active-bar" />
                  ) : null}
                </button>
              ))}
            </div>
          ))}
        </nav>
        <div className="sidebar-safety">
          <span className="safety-mini-icon">
            <ShieldCheck size={16} />
          </span>
          <div>
            <strong>Safe mode active</strong>
            <small>Reference-only prototype</small>
          </div>
          <span className="green-led" />
        </div>
        <div className="sidebar-bottom">
          <button
            className="profile-trigger"
            onClick={() => setShowAvatarSettings(open => !open)}
          >
            <Avatar image={avatarImage} preset={avatarPreset} />
            <span>
              <strong>Dr. Amira Hassan</strong>
              <small>Demo clinician</small>
            </span>
            <MoreHorizontal size={17} />
          </button>
          <div className="sidebar-build">
            MIA OB-GYN <span>BUILD 0.1.0</span>
          </div>
        </div>
        {showAvatarSettings ? renderAvatarSettings() : null}
      </aside>
      {mobileNav ? (
        <button
          className="nav-backdrop"
          onClick={() => setMobileNav(false)}
          aria-label="Close navigation overlay"
        />
      ) : null}
      <main className="main-shell">
        <header className="topbar">
          <div className="topbar-leading">
            <button
              className="mobile-menu icon-btn"
              aria-label="Open navigation"
              onClick={() => setMobileNav(true)}
            >
              <Menu size={20} />
            </button>
            <div className="breadcrumb">
              Mia OS <ChevronRight size={14} />{' '}
              <strong>{labels[section]}</strong>
            </div>
          </div>
          <div className="topbar-tools">
            <div className="demo-chip">
              <span className="demo-chip-dot" /> SYNTHETIC DATA ONLY
            </div>
            <button
              className="language-toggle"
              onClick={() => setLocale(value => (value === 'en' ? 'ar' : 'en'))}
              aria-label="Switch interface language"
            >
              <Languages size={15} />
              <span>{locale === 'en' ? 'العربية' : 'English'}</span>
            </button>
            <button
              className="notification-btn icon-btn"
              aria-label="Notifications"
              onClick={() =>
                showToast(
                  'No live notifications are connected in this prototype.'
                )
              }
            >
              <Bell size={17} />
              <span />
            </button>
            <button
              className="topbar-avatar"
              onClick={() => setShowAvatarSettings(open => !open)}
              aria-label="Personalize Mia"
            >
              <Avatar image={avatarImage} preset={avatarPreset} />
            </button>
          </div>
        </header>
        <div className="page-body">
          {section === 'overview' ? renderOverview() : null}
          {section === 'patients' ? renderPatientsPage() : null}
          {section === 'appointments' ? renderAppointmentsPage() : null}
          {section === 'questionnaires' ? renderQuestionnairesPage() : null}
          {section === 'mia' ? renderChatPage() : null}
          {section === 'evidence' ? renderEvidencePage() : null}
          {section === 'governance' ? renderGovernancePage() : null}
          <footer className="app-footer">
            <span>© Mia Clinical Prototype · OB-GYN only</span>
            <span>
              Fictional data · No external model calls · Not for live patient
              care
            </span>
          </footer>
        </div>
      </main>
      {toast ? (
        <div className="toast-message" role="status">
          <CheckCircle2 size={17} />
          {toast}
          <button
            aria-label="Dismiss message"
            className="icon-btn"
            onClick={() => setToast('')}
          >
            <X size={14} />
          </button>
        </div>
      ) : null}
    </div>
  );
}

export default MiaApp;
