import { useEffect, useMemo, useRef, useState } from 'react';
import {
  Activity,
  AlertTriangle,
  ArrowUpRight,
  Bell,
  BookOpen,
  GraduationCap,
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
  Copy,
  FileText,
  Filter,
  HeartPulse,
  Home,
  Languages,
  Menu,
  MessageCircle,
  MoreHorizontal,
  Pill,
  Plus,
  Search,
  Send,
  Settings2,
  ShieldCheck,
  Sparkles,
  Stethoscope,
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
import {
  APPROVED_PATHWAYS,
  PATHWAY_APPROVAL_REQUIREMENTS,
} from './medication-pathways';
import {
  CANDIDATE_PATHWAY_EVIDENCE,
  CANDIDATE_CASE_URLS,
} from './candidate-pathway-evidence';
import {
  searchDiagnosisMedications,
  type DiagnosisMedicationHit,
} from './diagnosis-medication-search';
import { ACADEMY_CASES } from './academy-cases';
import TrialsInformationPage from './TrialsInformationPage';
import MedicationPathwaysPage from './MedicationPathwaysPage';

type Section =
  | 'overview'
  | 'patients'
  | 'appointments'
  | 'questionnaires'
  | 'mia'
  | 'medications'
  | 'medication'
  | 'trials'
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
    id: 'medications',
    label: 'Medication pathways',
    ar: 'مسارات الأدوية',
    icon: Pill,
    group: 'INTELLIGENCE',
  },
  {
    id: 'medication',
    label: 'Mia Academy',
    ar: 'أكاديمية ميا',
    icon: Pill,
    group: 'INTELLIGENCE',
  },
  {
    id: 'trials',
    label: 'Trials & info',
    ar: 'التجارب والمعلومات',
    icon: Activity,
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
    file: '01-intended-use-and-data-classes.md',
    title: 'Intended use & prohibited use',
    owner: 'Product + clinical lead',
    state: 'Draft required',
    description: 'Defines exactly what the OB-GYN prototype can and cannot do.',
  },
  {
    id: 'GOV-02',
    file: '02-data-inventory-and-data-flow.md',
    title: 'Data inventory & flow map',
    owner: 'Privacy lead',
    state: 'Not started',
    description:
      'What data are collected, why, where they go, and when they are deleted.',
  },
  {
    id: 'GOV-03',
    file: '03-privacy-notice-and-consent-template.md',
    title: 'Patient and staff privacy notices',
    owner: 'Local counsel',
    state: 'Review required',
    description:
      'Jurisdiction-specific notices, lawful basis, patient rights, and processing transparency.',
  },
  {
    id: 'GOV-04',
    file: '05-security-threat-model-and-incident-response.md',
    title: 'Security risk assessment',
    owner: 'Security lead',
    state: 'Not started',
    description:
      'Threat model, access boundaries, encryption, secrets, backups, and incident response.',
  },
  {
    id: 'GOV-05',
    file: '06-clinical-risk-and-validation-plan.md',
    title: 'Clinical hazard & validation plan',
    owner: 'OB-GYN lead + pharmacist',
    state: 'Not started',
    description:
      'Evidence quality, unsafe-answer evaluation, escalation, clinical validation and release approval.',
  },
  {
    id: 'GOV-06',
    file: '07-source-rights-and-evidence-card-template.md',
    title: 'Source rights register',
    owner: 'Content + legal review',
    state: 'Draft required',
    description:
      'License, attribution, source version, jurisdiction, and permission to adapt each source.',
  },
  {
    id: 'GOV-07',
    file: '08-regulatory-classification-and-launch-gates.md',
    title: 'Regulatory classification memo',
    owner: 'Local regulatory counsel',
    state: 'Review required',
    description:
      'Assess applicable medical software, privacy and cross-border data requirements.',
  },
  {
    id: 'GOV-08',
    file: '04-vendor-and-cross-border-review.md',
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

// Bundled official Mia portrait (public/mia-avatar.jpg). Shown by default
// everywhere the avatar appears; the settings popover can switch to an
// icon preset or a user-uploaded photo instead.
const MIA_PHOTO_URL = 'mia-avatar.jpg';

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
        <img src={image} alt="Mia" />
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
  const [avatarImage, setAvatarImage] = useState<string | null>(MIA_PHOTO_URL);
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
  const floatBottom = useRef<HTMLDivElement | null>(null);
  const medBottom = useRef<HTMLDivElement | null>(null);

  // Floating Mia assistant — follows the doctor across every section.
  const [miaFloatOpen, setMiaFloatOpen] = useState(false);
  const [floatQuery, setFloatQuery] = useState('');
  // Travelling companion: brief glide + section tag on every section change,
  // and a minimise control so it never blocks content on small screens.
  const [companionGlide, setCompanionGlide] = useState(false);
  const [companionHidden, setCompanionHidden] = useState(false);
  useEffect(() => {
    setCompanionGlide(true);
    const timer = window.setTimeout(() => setCompanionGlide(false), 800);
    return () => window.clearTimeout(timer);
  }, [section]);

  // Medication assist chatbox (Academy page) — same shared conversation.
  const [medQuery, setMedQuery] = useState('');
  const [medClip, setMedClip] = useState(0);

  // Medication reference workspace — doctor enters the clinical picture,
  // Mia retrieves references and safety checks. Mia never selects,
  // ranks, doses or recommends a medicine.
  const [medDiagnosis, setMedDiagnosis] = useState('');
  const [academyOpenCase, setAcademyOpenCase] = useState<string | null>(null);
  const [academyRevealed, setAcademyRevealed] = useState<
    Record<string, boolean>
  >({});
  const [medSymptoms, setMedSymptoms] = useState('');
  const [medAllergies, setMedAllergies] = useState('');
  const [medCurrent, setMedCurrent] = useState('');
  const [medPregnancy, setMedPregnancy] = useState('pregnant');
  const [medMedicine, setMedMedicine] = useState('');
  const [medChecks, setMedChecks] = useState({
    allergies: false,
    meds: false,
    pregnancy: false,
    protocol: false,
    pharmacist: false,
  });
  const [medResult, setMedResult] = useState<null | {
    sources: EvidenceSource[];
    medicationHits: DiagnosisMedicationHit[];
    allergyList: string[];
    medicine: string;
    urgent: boolean;
    retrievedAt: string;
  }>(null);
  const [medCopied, setMedCopied] = useState(false);

  function copyMedicationPack() {
    if (!medResult) return;
    const lines: string[] = [
      'Mia OB-GYN — medication reference pack (REFERENCE ONLY, not a prescription)',
      `Retrieved: ${medResult.retrievedAt}`,
    ];
    if (medDiagnosis.trim()) lines.push(`Diagnosis: ${medDiagnosis.trim()}`);
    if (medSymptoms.trim()) lines.push(`Symptoms: ${medSymptoms.trim()}`);
    if (medPregnancy) lines.push(`Pregnancy state: ${medPregnancy}`);
    lines.push('', 'Guideline references:');
    medResult.sources.forEach(s =>
      lines.push(`- ${s.title} (${s.publisher}${s.year ? ', ' + s.year : ''}) — ${s.url}`)
    );
    if (medResult.medicine) {
      lines.push('', `Label & safety sources for ${medResult.medicine}:`);
      medicineReferenceLinks(medResult.medicine).forEach(l =>
        lines.push(`- ${l.label} — ${l.url}`)
      );
    }
    lines.push(
      '',
      `Pre-prescribing checklist: ${Object.values(medChecks).filter(Boolean).length}/${MED_CHECKS.length} confirmed`,
      'Mia does not choose, rank, dose or recommend any medicine. The prescribing decision stays with the doctor.'
    );
    navigator.clipboard
      .writeText(lines.join('\n'))
      .then(() => {
        setMedCopied(true);
        window.setTimeout(() => setMedCopied(false), 2000);
      })
      .catch(() => setMedCopied(false));
  }

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
      medications: locale === 'ar' ? 'مسارات الأدوية' : 'Medication pathways',
      medication: locale === 'ar' ? 'أكاديمية ميا' : 'Mia Academy',
      trials: locale === 'ar' ? 'التجارب والمعلومات' : 'Trials & info',
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

  useEffect(() => {
    if (miaFloatOpen)
      floatBottom.current?.scrollIntoView({ block: 'end', behavior: 'smooth' });
  }, [messages, miaFloatOpen]);

  useEffect(() => {
    if (section === 'medication')
      medBottom.current?.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
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

  function sendQuestion(question?: string, navigate = true) {
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
    if (navigate) setSection('mia');
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
                  maxLength={600}
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


  // ------------------------------------------------------------------
  // Medication reference workspace.
  // The doctor enters the clinical picture; Mia retrieves guideline
  // references, medicine label sources and safety checks. Mia never
  // selects, ranks, doses or recommends a medicine — that decision and
  // its responsibility stay with the doctor.
  // ------------------------------------------------------------------
  const EMERGENCY_RE =
    /(heavy bleeding|severe bleeding|haemorrhage|hemorrhage|seizure|collapse|unconscious|severe breathlessness|difficulty breathing|fainting|fits|convulsion)/i;

  const MED_CHECKS = [
    {
      key: 'allergies',
      label:
        locale === 'ar'
          ? 'تم تأكيد الحساسية مع المريضة مباشرة — لا يُفترض من الملف'
          : 'Allergies confirmed directly with the patient — never assumed from the chart',
    },
    {
      key: 'meds',
      label:
        locale === 'ar'
          ? 'تمت مراجعة الأدوية الحالية — أحضرت المريضة القائمة أو تم التحقق منها'
          : 'Current medicines reconciled — the patient brought the list or it was verified',
    },
    {
      key: 'pregnancy',
      label:
        locale === 'ar'
          ? 'تم تأكيد حالة الحمل / ما بعد الولادة / الرضاعة وتحديد تاريخها'
          : 'Pregnancy / postpartum / lactation state confirmed and dated',
    },
    {
      key: 'protocol',
      label:
        locale === 'ar'
          ? 'تمت مراجعة بروتوكول المستشفى المحلي لهذه الدواعي'
          : 'Local hospital protocol for this indication checked',
    },
    {
      key: 'pharmacist',
      label:
        locale === 'ar'
          ? 'تم طلب مراجعة الصيدلي للحالات عالية الخطورة أو المعقدة أو غير المؤكدة'
          : 'Pharmacist review requested for high-risk, complex or uncertain cases',
    },
  ] as const;

  function runMedicationReference() {
    const stateTerms =
      medPregnancy === 'pregnant'
        ? 'pregnancy'
        : medPregnancy === 'breastfeeding'
          ? 'breastfeeding lactation'
          : medPregnancy === 'postpartum'
            ? 'postpartum'
            : '';
    const query = [medDiagnosis, medSymptoms, stateTerms]
      .filter(part => part.trim())
      .join(' ');
    const sources = searchObgynSources(query || 'obstetrics', jurisdiction, 6);
    const diagnosisQuery = [medDiagnosis, medSymptoms]
      .filter(part => part.trim())
      .join(' ');
    const medicationHits = diagnosisQuery
      ? searchDiagnosisMedications(diagnosisQuery, jurisdiction).medicines
      : [];
    const allergyList = medAllergies
      .split(/[,\n;]+/)
      .map(part => part.trim())
      .filter(Boolean);
    const urgent = EMERGENCY_RE.test(medSymptoms + ' ' + medDiagnosis);
    setMedResult({
      sources,
      medicationHits,
      allergyList,
      medicine: medMedicine.trim(),
      urgent,
      retrievedAt: new Date().toLocaleString(
        locale === 'ar' ? 'ar-EG' : 'en-GB',
        { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' }
      ),
    });
  }

  function medicineReferenceLinks(medicine: string) {
    const enc = encodeURIComponent(medicine);
    const eda = EVIDENCE_SOURCES.find(source => source.id === 'eda-drug-register');
    return [
      {
        label: 'DailyMed — product label',
        hint: 'Contraindications · warnings · pregnancy & lactation sections',
        url: 'https://dailymed.nlm.nih.gov/dailymed/search.cfm?query=' + enc,
      },
      {
        label: 'EMC — UK product information',
        hint: 'Summary of Product Characteristics · patient leaflet',
        url: 'https://www.medicines.org.uk/emc/search?q=' + enc,
      },
      {
        label: 'LactMed — drugs and lactation',
        hint: 'Peer-reviewed monographs; check the individual entry',
        url: 'https://www.ncbi.nlm.nih.gov/books/NBK501922/',
      },
      {
        label: 'MotherToBaby — pregnancy exposures',
        hint: 'Fact sheets and pregnancy studies',
        url: 'https://mothertobaby.org/',
      },
      {
        label: 'Egyptian Drug Register',
        hint: 'National registration and product identity',
        url: eda ? eda.url : 'https://www.edaegypt.gov.eg/',
      },
    ];
  }

  function renderMedicationPage() {
    const checksDone = Object.values(medChecks).filter(Boolean).length;
    const t = (en: string, ar: string) => (locale === 'ar' ? ar : en);
    return (
      <>
        {renderHeader(
          t('Mia Academy', 'أكاديمية ميا'),
          t(
            'The medication teaching workspace — learn to prescribe with the why. Enter the clinical picture; Mia retrieves the guidelines, label sources and safety checks — instantly.',
            'مساحة تعليم الأدوية — تعلّم وصف الدواء مع السبب. أدخل الصورة السريرية؛ تسترد ميا الإرشادات ومصادر النشرات وفحوصات السلامة — فورًا.'
          ),
          <span className="source-mode-pill">
            <span className="pulse-dot" /> {t('REFERENCE ONLY', 'للمرجعية فقط')}
          </span>
        )}
        <div className="medref-boundary" role="note">
          <ShieldCheck size={17} />
          <div>
            <strong>{t('Clinical boundary.', 'حد سريري.')}</strong>{' '}
            {t(
              'Mia does not choose, rank, dose or recommend any medicine. The prescribing decision — and its responsibility — stays with the doctor. Everything below is a reference to verify, not an instruction to follow.',
              'لا تختار ميا أي دواء ولا ترتبه ولا تحدد جرعته ولا توصي به. قرار وصف الدواء — ومسؤوليته — يبقى مع الطبيب. كل ما يلي مرجع للتحقق، وليس تعليمات للاتباع.'
            )}
          </div>
        </div>
        <section className="panel medassist-panel" aria-label={t('Medication assist chat', 'محادثة مساعدة الأدوية')}>
          <div className="medassist-video" aria-hidden="true">
            <video
              key={medClip}
              src={MED_ASSIST_CLIPS[medClip]}
              poster="mia-avatar.jpg"
              autoPlay
              muted
              playsInline
              onEnded={() => setMedClip(clip => (clip + 1) % MED_ASSIST_CLIPS.length)}
            />
            <span className="medassist-live">
              <span className="online-dot" /> Dr. Mia
            </span>
          </div>
          <div className="medassist-main">
            <div className="medassist-head">
              <h3>
                {t('Medication assist — ask Dr. Mia', 'مساعدة الأدوية — اسأل د. ميا')}
              </h3>
              <p>
                {t(
                  'Guidelines, label sources and safety checks, in conversation. Reference & teaching only — Mia never prescribes; the doctor decides.',
                  'الإرشادات ومصادر النشرات وفحوصات السلامة، في محادثة. للمرجعية والتعليم فقط — ميا لا تصف الدواء أبدًا؛ الطبيب هو من يقرر.'
                )}
              </p>
            </div>
            <div className="medassist-messages">
              {messages.slice(-6).map((message, index) => (
                <div
                  className={'message-row message-' + message.role}
                  key={index}
                >
                  <div className="message-body">
                    <div className="message-author">
                      {message.role === 'assistant' ? 'Mia' : t('Doctor', 'الطبيب')}
                    </div>
                    <div className="message-bubble">
                      {message.text.split('\n').map((line, lineIndex) =>
                        line ? (
                          <p key={lineIndex}>{line}</p>
                        ) : (
                          <div className="message-space" key={lineIndex} />
                        )
                      )}
                    </div>
                    {message.sources && message.sources.length ? (
                      <div className="mia-float-sources">
                        {message.sources.slice(0, 3).map(source => (
                          <a
                            key={source.id}
                            href={source.url}
                            target="_blank"
                            rel="noopener noreferrer"
                          >
                            {source.title} <ArrowUpRight size={12} />
                          </a>
                        ))}
                      </div>
                    ) : null}
                  </div>
                </div>
              ))}
              <div ref={medBottom} />
            </div>
            <div className="mia-float-chips">
              {MED_ASSIST_CHIPS.map(chip => (
                <button
                  type="button"
                  key={chip}
                  onClick={() => sendMedQuestion(chip)}
                >
                  {chip}
                </button>
              ))}
            </div>
            <form
              className="mia-float-form"
              onSubmit={event => {
                event.preventDefault();
                sendMedQuestion();
              }}
            >
              <div className="mia-float-input-wrap">
                <input
                  aria-label={t('Ask Dr. Mia about a medicine or guideline', 'اسأل د. ميا عن دواء أو إرشاد')}
                  value={medQuery}
                  maxLength={600}
                  onChange={event => setMedQuery(event.target.value)}
                  placeholder={t(
                    'Ask about a guideline, drug reference, pregnancy or lactation…',
                    'اسأل عن إرشاد أو مرجع دواء أو الحمل أو الرضاعة…'
                  )}
                />
                {medQuery.length > 480 ? (
                  <span className="mia-float-count">{medQuery.length}/600</span>
                ) : null}
              </div>
              <button
                type="submit"
                className="send-button"
                aria-label={t('Send to Dr. Mia', 'أرسل إلى د. ميا')}
                disabled={!medQuery.trim()}
              >
                <Send size={15} />
              </button>
            </form>
          </div>
        </section>
        <div className="medref-grid">
          <section className="panel medref-form-panel">
            <h3>
              <Stethoscope size={17} /> {t('Clinical picture', 'الصورة السريرية')}
            </h3>
            <label className="medref-field">
              <span>{t('Diagnosis / indication', 'التشخيص / دواعي الاستعمال')}</span>
              <input
                value={medDiagnosis}
                onChange={e => setMedDiagnosis(e.target.value)}
                placeholder={t(
                  'e.g. Postpartum haemorrhage, preeclampsia…',
                  'مثال: نزيف ما بعد الولادة، تسمم الحمل…'
                )}
              />
            </label>
            <label className="medref-field">
              <span>{t('Symptoms and observations', 'الأعراض والملاحظات')}</span>
              <textarea
                value={medSymptoms}
                onChange={e => setMedSymptoms(e.target.value)}
                placeholder={t(
                  'e.g. Heavy vaginal bleeding 30 min after delivery, BP 150/100…',
                  'مثال: نزيف مهبلي غزير بعد 30 دقيقة من الولادة، ضغط الدم 150/100…'
                )}
                rows={3}
              />
            </label>
            <div className="medref-row">
              <label className="medref-field">
                <span>{t('Pregnancy state', 'حالة الحمل')}</span>
                <select
                  value={medPregnancy}
                  onChange={e => setMedPregnancy(e.target.value)}
                >
                  <option value="pregnant">{t('Pregnant', 'حامل')}</option>
                  <option value="postpartum">{t('Postpartum', 'بعد الولادة')}</option>
                  <option value="breastfeeding">{t('Breastfeeding', 'مرضعة')}</option>
                  <option value="not-pregnant">{t('Not pregnant', 'غير حامل')}</option>
                  <option value="unknown">{t('Unknown — confirm', 'غير معروف — يجب التأكيد')}</option>
                </select>
              </label>
              <label className="medref-field">
                <span>{t('Medicine you are considering (optional)', 'الدواء الذي تفكر فيه (اختياري)')}</span>
                <input
                  value={medMedicine}
                  onChange={e => setMedMedicine(e.target.value)}
                  placeholder={t(
                    'Type the exact product or generic name',
                    'اكتب الاسم التجاري أو العلمي بدقة'
                  )}
                />
              </label>
            </div>
            <label className="medref-field">
              <span>{t('Known allergies (comma-separated)', 'الحساسية المعروفة (افصل بفاصلة)')}</span>
              <input
                value={medAllergies}
                onChange={e => setMedAllergies(e.target.value)}
                placeholder={t(
                  'e.g. Penicillin — rash, Sulfa — anaphylaxis',
                  'مثال: بنسلين — طفح جلدي، سلفا — صدمة تحسسية'
                )}
              />
            </label>
            <label className="medref-field">
              <span>{t('Current medicines', 'الأدوية الحالية')}</span>
              <input
                value={medCurrent}
                onChange={e => setMedCurrent(e.target.value)}
                placeholder={t(
                  'e.g. Ferrous sulfate, methyldopa…',
                  'مثال: كبريتات الحديدوز، ميثيل دوبا…'
                )}
              />
            </label>
            <button
              type="button"
              className="btn btn-primary medref-submit"
              onClick={runMedicationReference}
              disabled={!medDiagnosis.trim() && !medSymptoms.trim()}
            >
              <Search size={16} /> {t('Retrieve references', 'استرداد المراجع')}
            </button>
            <small className="medref-hint">
              {t(
                'Nothing is sent anywhere — matching runs locally against the curated source directory.',
                'لا يُرسل أي شيء إلى أي مكان — تتم المطابقة محليًا ضمن دليل المصادر المنسق.'
              )}
            </small>
          </section>

          <section className="panel medref-results-panel">
            <h3>
              <BookOpen size={17} /> {t('Instant reference pack', 'حزمة المراجع الفورية')}
            </h3>
            {medResult ? (
              <div className="medref-pack-meta">
                <span className="medref-timestamp">
                  <Clock size={13} />{' '}
                  {t('Retrieved', 'تم الاسترداد')} {medResult.retrievedAt}
                </span>
                <button
                  type="button"
                  className="btn btn-ghost btn-sm"
                  onClick={copyMedicationPack}
                >
                  {medCopied ? (
                    <>
                      <Check size={14} /> {t('Copied', 'تم النسخ')}
                    </>
                  ) : (
                    <>
                      <Copy size={14} /> {t('Copy pack', 'نسخ الحزمة')}
                    </>
                  )}
                </button>
              </div>
            ) : null}
            {!medResult ? (
              <p className="medref-empty">
                {t(
                  'Enter a diagnosis or symptoms and press Retrieve references. Mia will assemble the guideline links, label sources and safety checks for this case here.',
                  'أدخل التشخيص أو الأعراض واضغط استرداد المراجع. ستجمع ميا روابط الإرشادات ومصادر النشرات وفحوصات السلامة لهذه الحالة هنا.'
                )}
              </p>
            ) : (
              <>
                {medResult.urgent ? (
                  <div className="medref-urgent" role="alert">
                    <AlertTriangle size={16} />
                    <span>
                      {t(
                        'Urgent pattern detected in what you entered. If this is a real deteriorating patient, activate your hospital’s emergency pathway now — do not wait for this prototype.',
                        'تم رصد نمط عاجل فيما أدخلته. إذا كانت هذه مريضة حقيقية تتدهور حالتها، فعّل مسار الطوارئ في مستشفاك الآن — لا تنتظر هذا النموذج الأولي.'
                      )}
                    </span>
                  </div>
                ) : null}
                <div className="medref-block">
                  <strong className="medref-block-title">
                    {t('Guideline references', 'مراجع الإرشادات')} ({medResult.sources.length})
                  </strong>
                  {medResult.sources.length ? (
                    medResult.sources.map(source => (
                      <a
                        key={source.id}
                        className="medref-source"
                        href={source.url}
                        target="_blank"
                        rel="noopener noreferrer"
                      >
                        <div>
                          <strong>{source.title}</strong>
                          <small>
                            {source.publisher}
                            {source.year ? ' · ' + source.year : ''} ·{' '}
                            {source.type}
                          </small>
                        </div>
                        <ArrowUpRight size={15} />
                      </a>
                    ))
                  ) : (
                    <p className="medref-empty">
                      {t(
                        'No strong match in the directory. Broaden the terms or try the Evidence library.',
                        'لا توجد مطابقة قوية في الدليل. وسّع المصطلحات أو جرّب مكتبة المراجع.'
                      )}
                    </p>
                  )}
                </div>
                <div className="medref-block">
                  <strong className="medref-block-title">
                    {t(
                      'Medicines named in our evidence for this diagnosis',
                      'الأدوية المذكورة في أدلتنا لهذا التشخيص'
                    )}{' '}
                    ({medResult.medicationHits.length})
                  </strong>
                  <p className="medref-note">
                    {t(
                      'Searched across the full library — every book and information centre — not just trials. These medicines are NAMED in candidate guideline evidence; that is discovery, not a recommendation. No approved pathway exists until a named clinician and pharmacist sign one off. The doctor decides.',
                      'تم البحث عبر المكتبة كاملة — كل الكتب ومراكز المعلومات — وليس التجارب فقط. هذه الأدوية مذكورة في أدلة إرشادية مرشحة؛ هذا اكتشاف وليس توصية. لا يوجد مسار معتمد حتى يوقّع عليه طبيب وصيدلي بالاسم. الطبيب يقرر.'
                    )}
                  </p>
                  {medResult.medicationHits.length ? (
                    medResult.medicationHits.map(hit => (
                      <div key={hit.name}>
                        <strong>{hit.name}</strong>
                        {hit.statements.map((statement, i) => (
                          <div key={i}>
                            <p className="medref-note">{statement.text}</p>
                            <small>
                              {statement.condition} · {statement.aspect} ·{' '}
                              <a
                                href={statement.citation.url}
                                target="_blank"
                                rel="noopener noreferrer"
                              >
                                {statement.citation.title} (
                                {statement.citation.publisher})
                              </a>
                            </small>
                            {statement.flags.length ? (
                              <p className="medref-note">
                                {t(
                                  'Disagreement / flag: ',
                                  'اختلاف / ملاحظة: '
                                )}
                                {statement.flags.join(' ')}
                              </p>
                            ) : null}
                          </div>
                        ))}
                      </div>
                    ))
                  ) : (
                    <p className="medref-empty">
                      {t(
                        'No medicine named in our candidate evidence for this diagnosis. The books and centres above are where to look — this list stays empty rather than guessed.',
                        'لا يوجد دواء مذكور في أدلتنا المرشحة لهذا التشخيص. الكتب والمراكز أعلاه هي مصدر البحث — هذه القائمة تبقى فارغة بدلًا من التخمين.'
                      )}
                    </p>
                  )}
                </div>
                {medResult.medicine ? (
                  <div className="medref-block">
                    <strong className="medref-block-title">
                      {t('Label & safety references —', 'مراجع النشرات والسلامة —')}{' '}
                      {medResult.medicine}
                    </strong>
                    <p className="medref-note">
                      {t(
                        'You named this medicine; Mia only fetched where to verify it. Open the label and read Contraindications, Warnings and Use in Specific Populations before prescribing.',
                        'أنت من سمّى هذا الدواء؛ ميا جلبت فقط مصادر التحقق منه. افتح النشرة واقرأ موانع الاستعمال والتحذيرات والاستعمال في فئات معينة قبل الوصف.'
                      )}
                    </p>
                    {medicineReferenceLinks(medResult.medicine).map(link => (
                      <a
                        key={link.label}
                        className="medref-source"
                        href={link.url}
                        target="_blank"
                        rel="noopener noreferrer"
                      >
                        <div>
                          <strong>{link.label}</strong>
                          <small>{link.hint}</small>
                        </div>
                        <ArrowUpRight size={15} />
                      </a>
                    ))}
                  </div>
                ) : (
                  <div className="medref-block">
                    <strong className="medref-block-title">
                      {t('Considering a specific medicine?', 'تفكر في دواء معين؟')}
                    </strong>
                    <p className="medref-note">
                      {t(
                        'Type its exact name in the form and retrieve again — Mia will pull the label and safety references for it. Mia will not suggest which medicine to use.',
                        'اكتب اسمه بدقة في النموذج واسترد المراجع مجددًا — ستجلب ميا مراجع النشرة والسلامة الخاصة به. لن تقترح ميا أي دواء للاستعمال.'
                      )}
                    </p>
                  </div>
                )}
                <div className="medref-block">
                  <strong className="medref-block-title">
                    {t('Allergy cross-check', 'فحص الحساسية المتقاطع')}
                  </strong>
                  {medResult.allergyList.length ? (
                    <>
                      <div className="medref-allergies">
                        {medResult.allergyList.map(allergy => (
                          <span key={allergy} className="medref-allergy-chip">
                            <AlertTriangle size={13} /> {allergy}
                          </span>
                        ))}
                      </div>
                      <p className="medref-note">
                        {t(
                          'Verify each of these against the product label’s Contraindications and Warnings sections before prescribing. When in doubt, escalate to pharmacy — do not rely on this list alone.',
                          'تحقق من كل واحد منها مقابل قسمي موانع الاستعمال والتحذيرات في نشرة المنتج قبل الوصف. عند الشك، ارجع إلى الصيدلية — لا تعتمد على هذه القائمة وحدها.'
                        )}
                      </p>
                    </>
                  ) : (
                    <p className="medref-note">
                      {t('No allergies entered.', 'لم تُدخل أي حساسية.')}{' '}
                      <strong>
                        {t(
                          'Confirm allergies directly with the patient before any prescription',
                          'أكّد الحساسية مع المريضة مباشرة قبل أي وصفة'
                        )}
                      </strong>{' '}
                      — {t('"unknown" is not "none".', '"غير معروف" ليس "لا يوجد".')}
                    </p>
                  )}
                </div>
                <div className="medref-block">
                  <strong className="medref-block-title">
                    {t('Pre-prescribing safety checklist', 'قائمة فحص السلامة قبل الوصف')} ({checksDone}/
                    {MED_CHECKS.length})
                  </strong>
                  {MED_CHECKS.map(check => (
                    <label key={check.key} className="medref-check">
                      <input
                        type="checkbox"
                        checked={medChecks[check.key]}
                        onChange={() =>
                          setMedChecks(prev => ({
                            ...prev,
                            [check.key]: !prev[check.key],
                          }))
                        }
                      />
                      <span>{check.label}</span>
                    </label>
                  ))}
                </div>
              </>
            )}
          </section>
        </div>
        <section className="panel medref-pathways-panel">
          <div className="medref-pathways-head">
            <h3>
              <ShieldCheck size={17} /> {t('Approved medication pathways', 'مسارات الأدوية المعتمدة')}
            </h3>
            <span className="medref-pathway-count">
              {APPROVED_PATHWAYS.length} {t('approved', 'معتمد')}
            </span>
          </div>          {APPROVED_PATHWAYS.length === 0 ? (
            <>
              <p className="medref-note">
                {t(
                  'No pathway has cleared the approval gate yet, so Mia suggests no medicines. A suggestion appears here only after all five of these are recorded:',
                  'لم يجتز أي مسار بوابة الاعتماد بعد، لذا لا تقترح ميا أي أدوية. لا يظهر أي اقتراح هنا إلا بعد تسجيل هذه الشروط الخمسة:'
                )}
              </p>
              <ol className="medref-approval-list">
                {(locale === 'ar'
                  ? [
                      'مراجع طبي مسمّى مع المؤهل وتاريخ المراجعة',
                      'مراجع صيدلي مسمّى مع المؤهل وتاريخ المراجعة',
                      'الإرشادات المستشهد بها بدقة: العنوان، الناشر، الإصدار، القسم، الرابط',
                      'الولايات القضائية التي ينطبق عليها المسار',
                      'تاريخ مراجعة مجدول — المسارات منتهية الصلاحية تختفي تلقائيًا',
                    ]
                  : PATHWAY_APPROVAL_REQUIREMENTS
                ).map(requirement => (
                  <li key={requirement}>{requirement}</li>
                ))}
              </ol>
              <p className="medref-note">
                {t(
                  'This is the quality-control contract: “most accurate” is earned by named clinician and pharmacist review against a cited guideline — never asserted by the software. To approve the first pathway, a clinician reviews a diagnosis against its guideline, a pharmacist countersigns, and both names go on the record above.',
                  'هذا هو عقد ضبط الجودة: "الأكثر دقة" يُكتسب بمراجعة طبيب وصيدلي مسمّيين مقابل إرشادات موثقة — ولا تدّعيه البرمجية أبدًا. لاعتماد المسار الأول، يراجع طبيب التشخيص مقابل الإرشادات، ويوقّع الصيدلي، ويُسجَّل الاسمان أعلاه.'
                )}
              </p>
            </>
          ) : (
            APPROVED_PATHWAYS.map(pathway => (
              <article key={pathway.id} className="medref-pathway">
                <header>
                  <strong>{pathway.diagnosis}</strong>
                  <span className="medref-pathway-jurisdiction">
                    {pathway.jurisdictions.join(' · ')}
                  </span>
                </header>
                <ul>
                  {pathway.medicines.map(medicine => (
                    <li key={medicine.name}>
                      <span
                        className={
                          'medref-role medref-role-' + medicine.role
                        }
                      >
                        {medicine.role.replace(/-/g, ' ')}
                      </span>
                      <strong>{medicine.name}</strong>
                      <span>{medicine.note}</span>
                    </li>
                  ))}
                </ul>
                <footer>
                  <span>
                    Guideline: {pathway.guideline.title} (
                    {pathway.guideline.publisher},{' '}
                    {pathway.guideline.edition}) —{' '}
                    {pathway.guideline.section}
                  </span>
                  <span>
                    Reviewed by {pathway.clinicianReviewer.name} (
                    {pathway.clinicianReviewer.credential},{' '}
                    {pathway.clinicianReviewer.date}) and{' '}
                    {pathway.pharmacistReviewer.name} (
                    {pathway.pharmacistReviewer.credential},{' '}
                    {pathway.pharmacistReviewer.date}). Re-review due{' '}
                    {pathway.reviewDue}.
                  </span>
                  <a
                    href={pathway.guideline.url}
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    Open the cited guideline <ArrowUpRight size={12} />
                  </a>
                </footer>
              </article>
            ))
          )}
        </section>
        <section className="panel medref-pathways-panel">
          <div className="medref-pathways-head">
            <h3>
              <BookOpen size={17} /> {t('Candidate evidence for clinician review', 'أدلة مرشحة لمراجعة الطبيب')}
            </h3>
            <span className="medref-pathway-count">
              {CANDIDATE_PATHWAY_EVIDENCE.length} {t('candidates', 'مرشح')}
            </span>
          </div>
          <p className="medref-note">
            {t(
              'Research candidates only — not approved pathways. Each entry records what a named public guideline states, with its citation. A reviewing clinician must verify every item against the primary source before anything becomes an approved pathway.',
              'مرشحات بحثية فقط — ليست مسارات معتمدة. يسجل كل عنصر ما تنص عليه إرشادات عامة مسماة، مع توثيقها. يجب على الطبيب المراجع التحقق من كل عنصر مقابل المصدر الأصلي قبل اعتماد أي مسار.'
            )}
          </p>
          {CANDIDATE_PATHWAY_EVIDENCE.map(candidate => (
            <article key={candidate.id} className="medref-pathway">
              <header>
                <strong>{candidate.condition}</strong>
                <span className="medref-pathway-jurisdiction">
                  {candidate.aspect}
                </span>
              </header>
              <ul>
                {candidate.statements.map((statement, index) => (
                  <li key={index}>
                    <span>{statement.text}</span>
                  </li>
                ))}
              </ul>
              {candidate.flags.length > 0 ? (
                <div className="medref-flags">
                  {candidate.flags.map((flag, index) => (
                    <p key={index} className="medref-flag">
                      ⚠ {flag}
                    </p>
                  ))}
                </div>
              ) : null}
              <footer>
                <span>
                  {candidate.citation.title} — {candidate.citation.publisher},{' '}
                  {candidate.citation.edition} ({candidate.citation.section})
                </span>
                <a
                  href={candidate.citation.url}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  Open the cited source <ArrowUpRight size={12} />
                </a>
              </footer>
            </article>
          ))}
          <div className="medref-case-links">
            <h4>{t('Open-access case studies', 'دراسات حالة مفتوحة')}</h4>
            <ul>
              {CANDIDATE_CASE_URLS.map(entry => (
                <li key={entry.url}>
                  <a href={entry.url} target="_blank" rel="noopener noreferrer">
                    {entry.label} <ArrowUpRight size={12} />
                  </a>
                </li>
              ))}
            </ul>
            <p className="medref-note">
              {t(
                'Single-case and small-series evidence is hypothesis-generating only — illustrative, low-certainty.',
                'أدلة الحالة الواحدة والسلاسل الصغيرة لتوليد الفرضيات فقط — توضيحية ومنخفضة اليقين.'
              )}
            </p>
          </div>
        </section>
        <section className="panel academy-panel">
          <div className="medref-pathways-head">
            <h3>
              <GraduationCap size={17} />{' '}
              {t('Teaching cases — learn the why', 'حالات تعليمية — تعلّم السبب')}
            </h3>
            <span className="medref-pathway-count">
              {ACADEMY_CASES.length} {t('cases', 'حالات')}
            </span>
          </div>
          <p className="medref-note">
            {t(
              'Synthetic patients, real guidelines. Work each case: read the patient, reason through the decision, then reveal what WHO, ACOG and NICE each state — including where they disagree. Teaching only: nothing here prescribes for a real patient.',
              'مرضى افتراضيون، وإرشادات حقيقية. اعمل على كل حالة: اقرأ المريضة، وفكّر في القرار، ثم اكشف ما تقوله منظمة الصحة العالمية والكلية الأمريكية وNICE — بما في ذلك مواضع اختلافهم. للتعليم فقط: لا شيء هنا يصف دواءً لمريضة حقيقية.'
            )}
          </p>
          {ACADEMY_CASES.map(academyCase => {
            const isOpen = academyOpenCase === academyCase.id;
            const isRevealed = !!academyRevealed[academyCase.id];
            return (
              <article key={academyCase.id} className="academy-case">
                <button
                  className="academy-case-head"
                  onClick={() =>
                    setAcademyOpenCase(isOpen ? null : academyCase.id)
                  }
                  aria-expanded={isOpen}
                >
                  <span>
                    <strong>
                      {locale === 'ar' ? academyCase.titleAr : academyCase.title}
                    </strong>
                    <small>{academyCase.topic}</small>
                  </span>
                  <ChevronDown
                    size={16}
                    className={isOpen ? 'chevron-open' : ''}
                  />
                </button>
                {isOpen ? (
                  <div className="academy-case-body">
                    <p className="academy-patient">
                      {locale === 'ar' ? academyCase.patientAr : academyCase.patient}
                    </p>
                    <div className="academy-decision">
                      <strong>
                        {t('The decision', 'القرار')}
                      </strong>
                      <p>
                        {locale === 'ar'
                          ? academyCase.decisionPointAr
                          : academyCase.decisionPoint}
                      </p>
                    </div>
                    {!isRevealed ? (
                      <button
                        className="academy-reveal-btn"
                        onClick={() =>
                          setAcademyRevealed(prev => ({
                            ...prev,
                            [academyCase.id]: true,
                          }))
                        }
                      >
                        {t(
                          'Reveal the guideline teaching',
                          'اكشف شرح الإرشادات'
                        )}
                      </button>
                    ) : (
                      <>
                        <div className="academy-block">
                          <strong>
                            {t('Think first', 'فكّر أولًا')}
                          </strong>
                          <ul>
                            {academyCase.thinking.map((point, i) => (
                              <li key={i}>{point}</li>
                            ))}
                          </ul>
                        </div>
                        <div className="academy-block">
                          <strong>
                            {t(
                              'What the guidelines state — in parallel',
                              'ما تقوله الإرشادات — بالتوازي'
                            )}
                          </strong>
                          {academyCase.positions.map(position => (
                            <div
                              key={position.authority}
                              className="academy-position"
                            >
                              <span>{position.authority}</span>
                              <p>{position.text}</p>
                            </div>
                          ))}
                        </div>
                        <div className="academy-disagreement" role="note">
                          <strong>
                            {t(
                              'Where they disagree — this is the lesson',
                              'موضع الاختلاف — هذا هو الدرس'
                            )}
                          </strong>
                          <p>{academyCase.disagreement}</p>
                        </div>
                        <div className="academy-block">
                          <strong>
                            {t('Safety checklist', 'قائمة السلامة')}
                          </strong>
                          <ul>
                            {academyCase.safetyChecklist.map((item, i) => (
                              <li key={i}>{item}</li>
                            ))}
                          </ul>
                        </div>
                        <footer className="academy-case-foot">
                          <span>
                            {t(
                              'Teaching only. The prescribing decision — and its responsibility — stays with the doctor.',
                              'للتعليم فقط. قرار وصف الدواء — ومسؤوليته — يبقى مع الطبيب.'
                            )}
                          </span>
                          <a
                            href={academyCase.citation.url}
                            target="_blank"
                            rel="noopener noreferrer"
                          >
                            {academyCase.citation.label}{' '}
                            <ArrowUpRight size={12} />
                          </a>
                        </footer>
                      </>
                    )}
                  </div>
                ) : null}
              </article>
            );
          })}
        </section>
      </>
    );
  }

  // ------------------------------------------------------------------
  // Floating Mia — she moves with the doctor across every section.
  // ------------------------------------------------------------------
  const FLOAT_CHIPS: Record<Section, string[]> = {
    overview: ['What can this prototype do?', 'Show me the safety gates'],
    patients: [
      'What must I confirm before prescribing?',
      'Find lactation references',
    ],
    appointments: ['Find postpartum haemorrhage guidance'],
    questionnaires: ['What does the intake check for?'],
    mia: ['Find preeclampsia guidance'],
    medications: [
      'Review approved medication pathways',
      'Explain why an unapproved medicine is withheld',
    ],
    medication: [
      'What does the allergy cross-check cover?',
      'Find magnesium sulfate references',
    ],
    trials: [
      'Find registered trials for endometriosis',
      'Search published evidence for a medicine',
    ],
    evidence: ['Show WHO maternal health guidelines'],
    governance: ['What is still blocked before live use?'],
  };

  function sendFloatQuestion(question?: string) {
    const value = (question ?? floatQuery).trim();
    if (!value) return;
    const patientId = chatContext === 'none' ? '' : chatContext;
    const answer = makeAnswer(value, patientId);
    setMessages(previous => [
      ...previous,
      { role: 'user', text: value },
      answer,
    ]);
    setFloatQuery('');
  }

  // Medication assist chatbox — same engine, same shared conversation.
  const MED_ASSIST_CLIPS = ['mia-med-1.mp4', 'mia-med-2.mp4', 'mia-med-3.mp4'];
  const MED_ASSIST_CHIPS = [
    'Find magnesium sulfate references',
    'What does the allergy cross-check cover?',
    'Postpartum haemorrhage guidelines',
    'Where do I verify a medicine in lactation?',
  ];

  function sendMedQuestion(question?: string) {
    const value = (question ?? medQuery).trim();
    if (!value) return;
    const patientId = chatContext === 'none' ? '' : chatContext;
    const answer = makeAnswer(value, patientId);
    setMessages(previous => [
      ...previous,
      { role: 'user', text: value },
      answer,
    ]);
    setMedQuery('');
  }

  function renderMiaFloat() {
    const recent = messages.slice(-8);
    if (companionHidden) {
      return (
        <button
          type="button"
          className="mia-companion-restore"
          onClick={() => setCompanionHidden(false)}
          aria-label="Show Dr Mia assistant"
        >
          <Avatar image={avatarImage} preset={avatarPreset} />
          Show Mia
        </button>
      );
    }
    return (
      <>
        <div className="mia-companion">
          <button
            type="button"
            className={
              'mia-fab' +
              (miaFloatOpen ? ' mia-fab-open' : '') +
              (companionGlide ? ' mia-companion-glide' : '')
            }
            onClick={() => setMiaFloatOpen(open => !open)}
            aria-label={miaFloatOpen ? 'Close Dr Mia assistant' : 'Open Dr Mia assistant'}
          >
            <Avatar image={avatarImage} preset={avatarPreset} size="md" />
            <span className="mia-fab-ping" />
          </button>
          <button
            type="button"
            className="mia-companion-minimise"
            onClick={() => {
              setMiaFloatOpen(false);
              setCompanionHidden(true);
            }}
            aria-label="Minimise Dr Mia assistant"
          >
            <X size={12} />
          </button>
          {companionGlide && !miaFloatOpen ? (
            <span className="mia-companion-tag">
              Following you · {labels[section]}
            </span>
          ) : null}
        </div>
        {miaFloatOpen ? (
          <div className="mia-float-panel" role="dialog" aria-label="Mia assistant">
            <div className="mia-float-header">
              <Avatar image={avatarImage} preset={avatarPreset} size="md" />
              <div>
                <strong>Mia · with you here</strong>
                <small>
                  <span className="online-dot" /> Reference mode ·{' '}
                  {labels[section]}
                </small>
              </div>
              <button
                type="button"
                className="icon-btn"
                onClick={() => setMiaFloatOpen(false)}
                aria-label="Close Mia assistant"
              >
                <X size={15} />
              </button>
            </div>
            <div className="mia-float-messages">
              {recent.map((message, index) => (
                <div
                  className={'message-row message-' + message.role}
                  key={index}
                >
                  <div className="message-body">
                    <div className="message-author">
                      {message.role === 'assistant' ? 'Mia' : 'Doctor'}
                    </div>
                    <div className="message-bubble">
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
                    {message.sources && message.sources.length ? (
                      <div className="mia-float-sources">
                        {message.sources.slice(0, 3).map(source => (
                          <a
                            key={source.id}
                            href={source.url}
                            target="_blank"
                            rel="noopener noreferrer"
                          >
                            {source.title} <ArrowUpRight size={12} />
                          </a>
                        ))}
                        {message.sources.length > 3 ? (
                          <span>
                            +{message.sources.length - 3} more in Mia chat
                          </span>
                        ) : null}
                      </div>
                    ) : null}
                  </div>
                </div>
              ))}
              <div ref={floatBottom} />
            </div>
            <div className="mia-float-chips">
              {FLOAT_CHIPS[section].map(chip => (
                <button
                  type="button"
                  key={chip}
                  onClick={() => sendFloatQuestion(chip)}
                >
                  {chip}
                </button>
              ))}
            </div>
            <form
              className="mia-float-form"
              onSubmit={event => {
                event.preventDefault();
                sendFloatQuestion();
              }}
            >
              <div className="mia-float-input-wrap">
                <input
                  aria-label="Ask Mia"
                  value={floatQuery}
                  maxLength={600}
                  onChange={event => setFloatQuery(event.target.value)}
                  placeholder="Ask Mia anything…"
                />
                {floatQuery.length > 480 ? (
                  <span className="mia-float-count">{floatQuery.length}/600</span>
                ) : null}
              </div>
              <button
                type="submit"
                className="send-button"
                aria-label="Send to Mia"
                disabled={!floatQuery.trim()}
              >
                <Send size={15} />
              </button>
            </form>
            <button
              type="button"
              className="mia-float-full"
              onClick={() => {
                setMiaFloatOpen(false);
                setSection('mia');
              }}
            >
              Open full Mia chat <ArrowUpRight size={13} />
            </button>
            <button
              type="button"
              className="mia-float-full"
              onClick={() => {
                setMiaFloatOpen(false);
                setSection('medication');
              }}
            >
              Open medication assist <ArrowUpRight size={13} />
            </button>
          </div>
        ) : null}
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
                <a
                  className="icon-btn"
                  href={'https://github.com/MohammedAbdelshafy/ai-front-desk/blob/feat/mia-clinical-os/docs/clinical-governance/' + doc.file}
                  target="_blank"
                  rel="noopener noreferrer"
                  aria-label={'Open draft document ' + doc.title}
                >
                  <ArrowUpRight size={15} />
                </a>
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
              avatarImage === MIA_PHOTO_URL
                ? 'preset-option preset-selected'
                : 'preset-option'
            }
            onClick={() => {
              setAvatarImage(MIA_PHOTO_URL);
            }}
          >
            <Avatar image={MIA_PHOTO_URL} preset="ai" />
            <span>
              <strong>Mia</strong>
              <small>Official portrait</small>
            </span>
            <Check size={15} />
          </button>
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
      <div className="mia-ambient" aria-hidden="true">
        <span className="mia-ambient-grid" />
        <span className="mia-orb mia-orb-a" />
        <span className="mia-orb mia-orb-b" />
        <span className="mia-orb mia-orb-c" />
      </div>
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
            MIA OB-GYN <span>BUILD 1.0.0</span>
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
          {section === 'medications' ? <MedicationPathwaysPage /> : null}
          {section === 'medication' ? renderMedicationPage() : null}
          {section === 'trials' ? <TrialsInformationPage /> : null}
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
      {renderMiaFloat()}
    </div>
  );
}

export default MiaApp;
