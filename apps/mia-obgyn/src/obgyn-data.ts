export type Jurisdiction = 'EG' | 'GLOBAL' | 'US' | 'UK';

export interface EvidenceSource {
  id: string;
  title: string;
  publisher: string;
  year?: string;
  jurisdictions: string[];
  topics: string[];
  type:
    | 'Guideline'
    | 'Regulator'
    | 'Medicine reference'
    | 'Research'
    | 'Specialist guidance';
  url: string;
  note: string;
  status: 'Reference directory';
}

export const EVIDENCE_SOURCES: EvidenceSource[] = [
  {
    id: 'who-pph-guideline-2025',
    title:
      'Consolidated guidelines for prevention, diagnosis and treatment of postpartum haemorrhage',
    publisher: 'World Health Organization',
    year: '2025',
    jurisdictions: ['GLOBAL'],
    topics: [
      'postpartum haemorrhage',
      'postpartum hemorrhage',
      'pph',
      'bleeding after birth',
      'maternal emergency',
      'uterotonic',
    ],
    type: 'Guideline',
    url: 'https://www.who.int/publications/i/item/9789240115637',
    note: 'International reference for clinician review; not a locally approved treatment order.',
    status: 'Reference directory',
  },
  {
    id: 'who-pph-implementation-2026',
    title:
      'Postpartum haemorrhage consolidated guideline: implementation guide',
    publisher: 'World Health Organization',
    year: '2026',
    jurisdictions: ['GLOBAL'],
    topics: [
      'postpartum haemorrhage',
      'postpartum hemorrhage',
      'maternal emergency',
      'obstetric emergency',
      'quality improvement',
    ],
    type: 'Guideline',
    url: 'https://www.who.int/publications/i/item/9789240116115',
    note: 'Implementation resource; local protocols and staff training remain necessary.',
    status: 'Reference directory',
  },
  {
    id: 'who-maternal-health',
    title: 'WHO recommendations on maternal health',
    publisher: 'World Health Organization',
    jurisdictions: ['GLOBAL'],
    topics: [
      'antenatal care',
      'pregnancy',
      'childbirth',
      'postnatal care',
      'maternal complications',
      'obstetrics',
    ],
    type: 'Guideline',
    url: 'https://www.who.int/publications/b/59332',
    note: 'Use the publication page to identify the relevant recommendation and current edition.',
    status: 'Reference directory',
  },
  {
    id: 'who-labour-care-guide',
    title: 'WHO Labour Care Guide implementation resources',
    publisher: 'World Health Organization',
    jurisdictions: ['GLOBAL'],
    topics: [
      'labour',
      'labor',
      'intrapartum',
      'fetal monitoring',
      'labour monitoring',
      'birth',
    ],
    type: 'Guideline',
    url: 'https://www.who.int/publications/i/item/9789240109346',
    note: 'Reference for labour monitoring and respectful intrapartum care.',
    status: 'Reference directory',
  },
  {
    id: 'who-contraceptive-mec',
    title: 'Medical eligibility criteria for contraceptive use, sixth edition',
    publisher: 'World Health Organization',
    year: '2025',
    jurisdictions: ['GLOBAL'],
    topics: [
      'contraception',
      'family planning',
      'contraceptive eligibility',
      'postpartum contraception',
    ],
    type: 'Guideline',
    url: 'https://www.who.int/publications/i/item/9789240115583',
    note: 'Eligibility guidance must be interpreted with the patient’s clinical circumstances and local policy.',
    status: 'Reference directory',
  },
  {
    id: 'acog-preeclampsia',
    title: 'Gestational hypertension and preeclampsia: Practice Bulletin',
    publisher: 'American College of Obstetricians and Gynecologists',
    jurisdictions: ['US'],
    topics: [
      'preeclampsia',
      'pre-eclampsia',
      'hypertension pregnancy',
      'eclampsia',
      'blood pressure',
      'hypertensive disorders',
    ],
    type: 'Specialist guidance',
    url: 'https://www.acog.org/clinical/clinical-guidance/practice-bulletin/articles/2020/06/gestational-hypertension-and-preeclampsia',
    note: 'US specialist guidance. It is not Egyptian policy and access/version status should be checked.',
    status: 'Reference directory',
  },
  {
    id: 'acog-pph',
    title: 'Postpartum hemorrhage: Practice Bulletin',
    publisher: 'American College of Obstetricians and Gynecologists',
    jurisdictions: ['US'],
    topics: [
      'postpartum haemorrhage',
      'postpartum hemorrhage',
      'obstetric bleeding',
      'pph',
    ],
    type: 'Specialist guidance',
    url: 'https://www.acog.org/clinical/clinical-guidance/practice-bulletin/articles/2017/10/postpartum-hemorrhage',
    note: 'US specialist guidance; confirm current status and local applicability.',
    status: 'Reference directory',
  },
  {
    id: 'rcog-green-top',
    title: 'Green-top Guidelines',
    publisher: 'Royal College of Obstetricians and Gynaecologists',
    jurisdictions: ['UK', 'GLOBAL_REFERENCE'],
    topics: [
      'obstetrics',
      'gynaecology',
      'gynecology',
      'ectopic pregnancy',
      'miscarriage',
      'maternal sepsis',
      'shoulder dystocia',
      'placenta accreta',
      'hyperemesis',
    ],
    type: 'Specialist guidance',
    url: 'https://www.rcog.org.uk/guidance/browse-all-guidance/green-top-guidelines/',
    note: 'Guideline index. Open the relevant topic and verify issue date, update status and applicability.',
    status: 'Reference directory',
  },
  {
    id: 'cdc-us-mec',
    title: 'U.S. Medical Eligibility Criteria for Contraceptive Use',
    publisher: 'Centers for Disease Control and Prevention',
    year: '2024',
    jurisdictions: ['US'],
    topics: [
      'contraception',
      'contraceptive safety',
      'medical eligibility',
      'family planning',
    ],
    type: 'Guideline',
    url: 'https://www.cdc.gov/contraception/hcp/usmec/introduction.html',
    note: 'US-specific eligibility criteria; do not present as Egyptian regulation.',
    status: 'Reference directory',
  },
  {
    id: 'lactmed',
    title: 'Drugs and Lactation Database (LactMed)',
    publisher: 'U.S. National Library of Medicine',
    jurisdictions: ['US', 'GLOBAL_REFERENCE'],
    topics: [
      'breastfeeding',
      'lactation',
      'medication in lactation',
      'postpartum medication',
      'drug transfer into breast milk',
      'medicine while breastfeeding',
    ],
    type: 'Medicine reference',
    url: 'https://www.ncbi.nlm.nih.gov/books/NBK501922/',
    note: 'Peer-reviewed lactation reference. Check the individual monograph and its revision date.',
    status: 'Reference directory',
  },
  {
    id: 'mother-to-baby',
    title: 'MotherToBaby fact sheets and pregnancy studies',
    publisher: 'Organization of Teratology Information Specialists',
    jurisdictions: ['US', 'GLOBAL_REFERENCE'],
    topics: [
      'medications in pregnancy',
      'exposure in pregnancy',
      'birth defects',
      'pregnancy medication counseling',
      'breastfeeding',
      'lactation',
      'pregnancy exposure',
      'teratology',
    ],
    type: 'Medicine reference',
    url: 'https://mothertobaby.org/fact-sheets-parent/',
    note: 'Patient-information and teratology resources; not a prescribing authorization.',
    status: 'Reference directory',
  },
  {
    id: 'uktis-bumps',
    title: 'Medicines in Pregnancy (BUMPS)',
    publisher: 'UK Teratology Information Service',
    jurisdictions: ['UK', 'GLOBAL_REFERENCE'],
    topics: [
      'medications in pregnancy',
      'teratology',
      'pregnancy exposures',
      'pregnancy medicine safety',
    ],
    type: 'Medicine reference',
    url: 'https://www.medicinesinpregnancy.org/',
    note: 'UK pregnancy-medicine information; review its source date and local relevance.',
    status: 'Reference directory',
  },
  {
    id: 'dailymed',
    title: 'DailyMed structured product labels',
    publisher: 'U.S. National Library of Medicine',
    jurisdictions: ['US'],
    topics: [
      'medicine label',
      'contraindications',
      'pregnancy',
      'lactation',
      'drug interactions',
      'product warnings',
      'adverse effects',
    ],
    type: 'Medicine reference',
    url: 'https://dailymed.nlm.nih.gov/dailymed/app-support-web-services.cfm',
    note: 'Product label directory; label text alone does not determine the appropriate treatment for a patient.',
    status: 'Reference directory',
  },
  {
    id: 'openfda-labels',
    title: 'Drug product labeling API',
    publisher: 'U.S. Food and Drug Administration',
    jurisdictions: ['US'],
    topics: [
      'drug label',
      'warnings',
      'pregnancy',
      'lactation',
      'contraindications',
      'drug interactions',
    ],
    type: 'Regulator',
    url: 'https://open.fda.gov/apis/drug/label/',
    note: 'FDA cautions that openFDA data should not be used alone to make medical-care decisions.',
    status: 'Reference directory',
  },
  {
    id: 'eda-drug-register',
    title: 'Egyptian Drug Register',
    publisher: 'Egyptian Drug Authority',
    jurisdictions: ['EG'],
    topics: [
      'Egypt product registration',
      'registered medicine',
      'national product label',
      'medicine identity',
      'drug register',
    ],
    type: 'Regulator',
    url: 'https://www.edaegypt.gov.eg/ar/%D8%A7%D9%84%D9%85%D8%B1%D8%AC%D8%B9-%D8%A7%D9%84%D8%AA%D9%86%D8%B8%D9%8A%D9%85%D9%8A-%D9%84%D9%87%D9%8A%D8%A6%D8%A9-%D8%A7%D9%84%D8%AF%D9%88%D8%A7%D8%A1-%D8%A7%D9%84%D9%85%D8%B5%D8%B1%D9%8A%D8%A9/%D8%B3%D8%AC%D9%84-%D8%A7%D9%84%D8%AF%D9%88%D8%A7%D8%A1-%D8%A7%D9%84%D9%85%D8%B5%D8%B1%D9%8A/',
    note: 'Egyptian regulatory source for product identity and registration; verify the specific product.',
    status: 'Reference directory',
  },
  {
    id: 'eda-periodic-lists',
    title: 'EDA periodic medicine lists',
    publisher: 'Egyptian Drug Authority',
    jurisdictions: ['EG'],
    topics: [
      'Egypt essential medicines',
      'high-alert medicines',
      'emergency medication lists',
      'OTC classification',
      'medicine safety',
    ],
    type: 'Regulator',
    url: 'https://edaegypt.gov.eg/en/publications-reports-and-eda-in-numbers/eda-publications/periodic-lists/',
    note: 'Regulatory listing page; confirm the exact list, publication date and current status.',
    status: 'Reference directory',
  },
  {
    id: 'eda-safety-alerts',
    title: 'Pharmacovigilance safety alerts',
    publisher: 'Egyptian Drug Authority',
    jurisdictions: ['EG'],
    topics: [
      'pregnancy',
      'lactation',
      'medicine label changes',
      'drug safety alerts',
      'pharmacovigilance',
    ],
    type: 'Regulator',
    url: 'https://www.edaegypt.gov.eg/en/awareness/ca-of-pharmaceutical-care-publications/pharmacovigilance-publications/third-safety-alerts/',
    note: 'Safety-alert directory; this interface does not automatically verify whether a specific alert applies.',
    status: 'Reference directory',
  },
  {
    id: 'eda-pharmaceutical-info',
    title: 'Reliable drug-information service',
    publisher: 'Egyptian Pharmaceutical Information Center / EDA',
    jurisdictions: ['EG'],
    topics: [
      'complex medicine question',
      'pregnancy medication query',
      'lactation medicine query',
      'drug information escalation',
    ],
    type: 'Regulator',
    url: 'https://edaegypt.gov.eg/en/about-us/home-page-services/home-page-services/inquire-about-reliable-drug-information/',
    note: 'Escalation route for complex medication-information questions.',
    status: 'Reference directory',
  },
  {
    id: 'mohp-safe-maternity',
    title: 'Safe maternity and obstetric services',
    publisher: 'Egyptian Ministry of Health and Population',
    jurisdictions: ['EG'],
    topics: [
      'obstetrics',
      'gynaecology',
      'gynecology',
      'safe delivery',
      'delivery protocols',
      'maternity emergency',
      'maternal mortality review',
      'obstetric referral',
      'labour',
      'postpartum care',
    ],
    type: 'Regulator',
    url: 'https://www.mohp.gov.eg/SectorServices.aspx?Deptcode=28&SectorCode=5',
    note: 'National service reference; follow current locally approved hospital protocols.',
    status: 'Reference directory',
  },
  {
    id: 'pubmed',
    title: 'PubMed literature search',
    publisher: 'U.S. National Library of Medicine',
    jurisdictions: ['GLOBAL_REFERENCE'],
    topics: [
      'systematic review',
      'clinical trials',
      'obstetrics',
      'gynaecology',
      'gynecology',
      'maternal medicine',
      'fertility',
      'gynecologic oncology',
    ],
    type: 'Research',
    url: 'https://pubmed.ncbi.nlm.nih.gov/',
    note: 'Search index, not a clinical recommendation. Assess study design, date, population and bias.',
    status: 'Reference directory',
  },
  {
    id: 'smfm-guidance',
    title: 'Clinical guidance and publications',
    publisher: 'Society for Maternal-Fetal Medicine',
    jurisdictions: ['US', 'GLOBAL_REFERENCE'],
    topics: [
      'maternal-fetal medicine',
      'high-risk pregnancy',
      'fetal growth restriction',
      'preterm birth',
      'pregnancy complications',
    ],
    type: 'Specialist guidance',
    url: 'https://www.smfm.org/publications',
    note: 'Specialist guidance index; verify publication date and applicability.',
    status: 'Reference directory',
  },
  {
    id: 'nice-guidance',
    title: 'NICE guidance (search: pregnancy, maternity, gynaecology)',
    publisher: 'National Institute for Health and Care Excellence',
    jurisdictions: ['UK', 'GLOBAL_REFERENCE'],
    topics: [
      'hypertension in pregnancy',
      'preeclampsia',
      'antenatal care',
      'intrapartum care',
      'postnatal care',
      'ectopic pregnancy',
      'miscarriage',
      'gynaecology',
      'caesarean',
    ],
    type: 'Guideline',
    url: 'https://www.nice.org.uk/guidance',
    note: 'UK evidence-based guidance; search the topic and confirm currency and local applicability.',
    status: 'Reference directory',
  },
  {
    id: 'figo-resources',
    title: 'FIGO resources and committee statements',
    publisher: 'International Federation of Gynecology and Obstetrics',
    jurisdictions: ['GLOBAL', 'GLOBAL_REFERENCE'],
    topics: [
      'obstetrics',
      'gynaecology',
      'maternal health',
      'postpartum haemorrhage',
      'preeclampsia',
      'contraception',
      'safe abortion care',
    ],
    type: 'Specialist guidance',
    url: 'https://www.figo.org/resources',
    note: 'Global federation statements; check publication date and whether local adaptation exists.',
    status: 'Reference directory',
  },
  {
    id: 'emc-medicines',
    title: 'Electronic Medicines Compendium (SPCs and patient leaflets)',
    publisher: 'Datapharm / UK regulators',
    jurisdictions: ['UK', 'GLOBAL_REFERENCE'],
    topics: [
      'summary of product characteristics',
      'medicine label',
      'contraindications',
      'pregnancy',
      'lactation',
      'drug interactions',
      'adverse effects',
      'dosing information',
    ],
    type: 'Medicine reference',
    url: 'https://www.medicines.org.uk/emc',
    note: 'UK-licensed product information; the searched product must match the locally available product.',
    status: 'Reference directory',
  },
  {
    id: 'who-eml-2023',
    title: 'WHO Model List of Essential Medicines, 2023',
    publisher: 'World Health Organization',
    year: '2023',
    jurisdictions: ['GLOBAL'],
    topics: [
      'essential medicines',
      'oxytocin',
      'magnesium sulfate',
      'maternal medicines',
      'contraceptives',
      'formulary',
    ],
    type: 'Guideline',
    url: 'https://www.who.int/publications/i/item/WHO-MHP-HPS-EML-2023.02',
    note: 'Global formulary reference; national formularies and local availability govern prescribing.',
    status: 'Reference directory',
  },
];

function accessibleIn(
  jurisdiction: Jurisdiction,
  source: EvidenceSource
): boolean {
  if (jurisdiction === 'GLOBAL') return true;
  return (
    source.jurisdictions.includes(jurisdiction) ||
    source.jurisdictions.includes('GLOBAL') ||
    source.jurisdictions.includes('GLOBAL_REFERENCE')
  );
}

export function searchObgynSources(
  query: string,
  jurisdiction: Jurisdiction,
  limit = 6
): EvidenceSource[] {
  const normalized = query
    .toLowerCase()
    .normalize('NFKD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/[^a-z0-9\s-]/g, ' ');
  const tokens = normalized.split(/\s+/).filter(token => token.length >= 3);
  if (!tokens.length) return [];
  const ranked = EVIDENCE_SOURCES.filter(source =>
    accessibleIn(jurisdiction, source)
  )
    .map(source => {
      const title = source.title.toLowerCase();
      const topics = source.topics.join(' ').toLowerCase();
      const corpus = title + ' ' + topics + ' ' + source.note.toLowerCase();
      let score = 0;
      source.topics.forEach(topic => {
        if (normalized.includes(topic.toLowerCase())) score += 8;
      });
      if (title.includes(normalized.trim())) score += 10;
      tokens.forEach(token => {
        if (title.includes(token)) score += 3;
        if (topics.includes(token)) score += 2;
        if (
          corpus.includes(token) &&
          !title.includes(token) &&
          !topics.includes(token)
        )
          score += 1;
      });
      return { source, score };
    })
    .filter(item => item.score > 0)
    .sort(
      (a, b) =>
        b.score - a.score || a.source.title.localeCompare(b.source.title)
    );
  return ranked
    .slice(0, Math.max(1, Math.min(limit, 10)))
    .map(item => item.source);
}
