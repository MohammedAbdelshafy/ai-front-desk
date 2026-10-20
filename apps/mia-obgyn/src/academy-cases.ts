// Mia Academy — teaching cases.
//
// STATUS: TEACHING ONLY. Every patient here is synthetic. Cases teach new
// doctors how prescribing decisions are reasoned from cited guidelines —
// they are never a recommendation for a real patient. Guideline positions
// are presented in parallel, in each authority's own terms; where
// authorities disagree, the disagreement is the lesson and is never
// resolved here. The prescribing decision — and its responsibility —
// always stays with the doctor.
//
// Content compiled from candidate-pathway-evidence.ts (public guidelines
// read live 2026-10-19). ACOG PB 183 statements rest on two independent
// secondary summaries (full text paywalled) — medium confidence, labelled.

export interface AcademyCase {
  id: string;
  title: string;
  titleAr: string;
  topic: string;
  /** Synthetic patient vignette. */
  patient: string;
  patientAr: string;
  /** The question the learner must reason through before revealing. */
  decisionPoint: string;
  decisionPointAr: string;
  /** What a careful prescriber checks before choosing anything. */
  thinking: string[];
  /** What each authority states, in parallel — never merged. */
  positions: { authority: string; text: string }[];
  /** Where the authorities disagree. The disagreement IS the lesson. */
  disagreement: string;
  /** Pre-prescribing safety checks for this scenario. */
  safetyChecklist: string[];
  citation: { label: string; url: string };
}

export const ACADEMY_CASES: AcademyCase[] = [
  {
    id: 'case-pph-treatment',
    title: 'Case 1 — The bleeding won\u2019t slow down',
    titleAr: 'الحالة ١ — النزيف لا يتباطأ',
    topic: 'Postpartum haemorrhage — first response',
    patient:
      'Synthetic patient: a 26-year-old, first baby, vaginal birth 25 minutes ago. The uterus feels soft and poorly contracted, blood loss is climbing past 700 mL, and her pulse is rising. The team is looking at you.',
    patientAr:
      'مريضة افتراضية: عمرها ٢٦ عامًا، أول ولادة، ولادة مهبقية قبل ٢٥ دقيقة. الرحم لين وضعيف الانقباض، وفقد الدم يتجاوز ٧٠٠ مل، والنبض يرتفع. الفريق ينظر إليك.',
    decisionPoint:
      'What is your first-line uterotonic — and what else belongs in the first response, in the first minutes?',
    decisionPointAr:
      'ما هو مقبّض الرحم الأول في خطتك — وما الذي ينتمي أيضًا إلى الاستجابة الأولى، في الدقائق الأولى؟',
    thinking: [
      'Name the likely cause first: a soft, poorly contracted uterus points to atony — the commonest cause of PPH — before reaching for any drug.',
      'Check what she already received for prevention: the first-line choice for treatment is reasoned against her prophylaxis, not in a vacuum.',
      'Think in bundles, not single drugs: guidelines describe a first response (uterotonic + examination + fluids + escalation), not a lone injection.',
      'Ask what would change your choice: severe hypertension or pre-eclampsia in this patient rules some second-line agents out entirely.',
    ],
    positions: [
      {
        authority: 'WHO 2025 (consolidated PPH guideline)',
        text: 'IV oxytocin is the recommended first-line uterotonic for PPH treatment, even after prophylactic use. Tranexamic acid 1 g IV belongs in the first-response bundle when given early — within 3 hours of birth. Second-line, if oxytocin is unavailable or bleeding is unresponsive: IV ergometrine, oxytocin+ergometrine, or a prostaglandin — with no evidence to rank them.',
      },
      {
        authority: 'ACOG PB 183 (2017)',
        text: 'Uterotonic agents should be first-line for atonic PPH; the choice of specific agent is at provider discretion — none identified as superior. Tranexamic acid is positioned later: when primary therapy fails, and especially effective within 3 hours of birth. (Statements verified via secondary summaries — PB 183 full text is paywalled.)',
      },
      {
        authority: 'NICE NG235 (2023)',
        text: 'First-line uterotonic depends on the prophylaxis already received (Table 12). Tranexamic acid 1 g IV over 10 minutes is given alongside uterotonics, repeated after at least 30 minutes if bleeding continues.',
      },
    ],
    disagreement:
      'Tranexamic acid timing. WHO 2025 places TXA inside the first-response bundle; ACOG positions it after initial therapy fails; NICE gives it alongside uterotonics without stating the 3-hour window in that recommendation. Same drug, three positions in the sequence — know which authority your unit follows, and why.',
    safetyChecklist: [
      'TXA: check for a clear contraindication to antifibrinolytics (e.g. known thromboembolic event during pregnancy) — WHO states this explicitly.',
      'Ergometrine-containing agents: contraindicated in severe hypertension, pre-eclampsia, eclampsia, and severe cardiac/hepatic/renal disease (NICE 1.10.9).',
      'Escalate early and examine the genital tract — the bundle includes escalation, not just medicines.',
      'Verify allergies and what was already given before any second-line agent.',
    ],
    citation: {
      label: 'WHO consolidated PPH guideline 2025 · ACOG PB 183 · NICE NG235',
      url: 'https://www.pphaction.net/papers/9789240115637-eng.pdf',
    },
  },
  {
    id: 'case-severe-preeclampsia',
    title: 'Case 2 — BP 168/112 at 34 weeks',
    titleAr: 'الحالة ٢ — ضغط ١٦٨/١١٢ في الأسبوع ٣٤',
    topic: 'Severe pre-eclampsia — acute hypertension & seizure prophylaxis',
    patient:
      'Synthetic patient: a 31-year-old at 34 weeks, severe headache since morning. BP 168/112, repeated 15 minutes later at 166/110. Urine dipstick strongly positive for protein. She has no asthma and no cardiac history.',
    patientAr:
      'مريضة افتراضية: عمرها ٣١ عامًا، في الأسبوع ٣٤، صداع شديد منذ الصباح. ضغط الدم ١٦٨/١١٢، وبعد ١٥ دقيقة ١٦٦/١١٠. شريط البول إيجابي بقوة للبروتين. لا ربو ولا تاريخ قلبي.',
    decisionPoint:
      'Two prescribing problems at once: bringing the pressure down safely, and preventing a seizure. What do the guidelines ask of you — and how fast?',
    decisionPointAr:
      'مشكلتا وصف في وقت واحد: خفض الضغط بأمان، ومنع التشنجات. ماذا تطلب الإرشادات منك — وبأي سرعة؟',
    thinking: [
      'Separate the two problems: acute antihypertensive treatment and seizure prophylaxis are different drugs with different clocks.',
      'The clock is part of the prescription: persistent severe hypertension (≥160/110 for ≥15 min) is treated within 30–60 minutes in ACOG\u2019s framing.',
      'Before choosing an agent, screen for the patient-specific exclusions: asthma, heart block, bradycardia change the antihypertensive answer; renal failure and myasthenia change the magnesium answer.',
      'Notice what this patient does NOT have: no asthma, no cardiac history — that is exactly the screening the guidelines expect you to do out loud.',
    ],
    positions: [
      {
        authority: 'ACOG PB 222 (2020)',
        text: 'Treat acute-onset severe hypertension within 30–60 minutes with IV hydralazine, IV labetalol, or oral immediate-release nifedipine — no superiority ranking; any of the three may be used. Magnesium sulfate is the drug of choice for seizure prevention and treatment in severe features/eclampsia. Avoid labetalol in asthma, preexisting myocardial disease, decompensated cardiac function, heart block, or bradycardia.',
      },
      {
        authority: 'NICE NG133 (2019, reviewed 2023)',
        text: 'Severe hypertension in critical care: labetalol (oral or IV), oral nifedipine, or IV hydralazine — treat immediately. Magnesium sulfate follows the Collaborative Eclampsia Trial regimen (4 g IV over 5–15 min, then 1 g/h for 24 h). Do NOT use diazepam, phenytoin, or other anticonvulsants as an alternative in eclampsia.',
      },
      {
        authority: 'WHO 2011 (pre-eclampsia & eclampsia)',
        text: 'Magnesium sulfate is preferred over other anticonvulsants for prevention in severe pre-eclampsia and for eclampsia treatment. For the antihypertensive itself, WHO names NO first-line agent — choice and route rest on the clinician\u2019s experience, cost, and local availability.',
      },
    ],
    disagreement:
      'The hierarchy. ACOG ranks three acute agents equally; NICE frames labetalol first in its wider hypertension pathway; WHO deliberately names none. A new prescriber must learn to hold all three positions without merging them — and to document which authority guided the choice.',
    safetyChecklist: [
      'Magnesium sulfate contraindications (ACOG, explicit): myasthenia gravis, hypocalcemia, moderate-to-severe renal failure, cardiac ischemia, heart block, myocarditis.',
      'Labetalol screen: asthma, heart block, bradycardia, decompensated cardiac function.',
      'Confirm the BP is truly persistent (repeat measurement) before acute treatment — and treat within the window once confirmed.',
      'Never substitute diazepam or phenytoin for magnesium sulfate in eclampsia prophylaxis (NICE).',
    ],
    citation: {
      label: 'ACOG PB 222 · NICE NG133 · WHO 2011',
      url: 'https://www.nice.org.uk/guidance/ng133/chapter/Recommendations',
    },
  },
  {
    id: 'case-aspirin-prevention',
    title: 'Case 3 — \u201cShould I take aspirin?\u201d',
    titleAr: 'الحالة ٣ — «هل آخذ الأسبرين؟»',
    topic: 'Pre-eclampsia prevention — the aspirin dose debate',
    patient:
      'Synthetic patient: a 29-year-old at 11 weeks, first pregnancy ended in pre-eclampsia at 35 weeks. She has read about aspirin online and asks you directly: should she take it — and how much?',
    patientAr:
      'مريضة افتراضية: عمرها ٢٩ عامًا، في الأسبوع ١١، انتهى حملها الأول بتسمم حمل في الأسبوع ٣٥. قرأت عن الأسبرين على الإنترنت وتسألك مباشرة: هل تأخذه — وبأي جرعة؟',
    decisionPoint:
      'She qualifies as high-risk in every guideline. So the drug is not the hard part — the dose is. What number do you write, and whose number is it?',
    decisionPointAr:
      'هي عالية الخطورة في كل الإرشادات. الدواء ليس الجزء الصعب — الجرعة هي الصعبة. أي رقم تكتبه، ورقم من هذا؟',
    thinking: [
      'Confirm the indication first: previous pre-eclampsia is a high-risk factor in WHO, ACOG, and NICE framings alike.',
      'Timing matters as much as dose: every authority starts prophylaxis early — the windows differ, but all are in the first half of pregnancy.',
      'This is the classic teaching trap: three respected authorities, three different doses for the same drug and the same indication. There is no way to average 75, 81, and 75–150.',
      'Learn the meta-lesson: when guidelines disagree on a number, the prescriber follows their local protocol and can say which authority it comes from.',
    ],
    positions: [
      {
        authority: 'WHO 2011',
        text: 'Aspirin 75 mg for high-risk women, initiated before 20 weeks. Also: calcium 1.5–2.0 g elemental/day in low-intake areas.',
      },
      {
        authority: 'ACOG PB 222 (2020)',
        text: 'Aspirin 81 mg/day from 12–28 weeks — optimally before 16 weeks — continued to delivery, for prophylaxis in at-risk women.',
      },
      {
        authority: 'NICE NG133 (2019, reviewed 2023)',
        text: 'Aspirin 75–150 mg daily from 12 weeks to the birth, for women at high risk or with more than one moderate risk factor.',
      },
    ],
    disagreement:
      'The dose itself: 75 mg (WHO) vs 81 mg (ACOG) vs 75–150 mg (NICE). Mia does not resolve this — no app should. The lesson is that \u201cthe guideline says\u201d is an incomplete sentence; a careful prescriber finishes it: which guideline, which edition, which setting.',
    safetyChecklist: [
      'Check aspirin allergy/intolerance and bleeding risk before any prophylaxis.',
      'Know the NOT-recommended list (WHO): vitamins C and E, diuretics for prevention, bedrest, and salt restriction are not prevention strategies.',
      'Document the authority and dose chosen in the record — future clinicians inherit your reasoning.',
      'Reassess at each visit: prophylaxis is a plan, not a one-time checkbox.',
    ],
    citation: {
      label: 'WHO 2011 · ACOG PB 222 · NICE NG133',
      url: 'https://www.acog.org/clinical/clinical-guidance/practice-bulletin/articles/2020/06/gestational-hypertension-and-preeclampsia',
    },
  },
];
