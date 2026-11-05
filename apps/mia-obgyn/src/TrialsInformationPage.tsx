import { useMemo, useState } from 'react';
import { Activity, BookOpen, ExternalLink, FlaskConical, Info, Search, ShieldCheck } from 'lucide-react';
import { searchObgynSources } from './obgyn-data';
import type { EvidenceSource } from './obgyn-data';
import './trials-information.css';

type ResearchLink = {
  id: string;
  title: string;
  description: string;
  kind: 'trial-registry' | 'literature' | 'medicine-info' | 'guideline' | 'safety';
  url: (condition: string, intervention: string, location: string) => string;
  note: string;
};

function searchUrl(base: string, params: Record<string, string>): string {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value.trim()) query.set(key, value.trim());
  });
  return base + (query.toString() ? '?' + query.toString() : '');
}

const RESEARCH_LINKS: ResearchLink[] = [
  {
    id: 'clinicaltrials',
    title: 'ClinicalTrials.gov',
    description: 'Search registered and completed studies, study status, locations, eligibility criteria and whether results have been posted.',
    kind: 'trial-registry',
    url: (condition, intervention, location) => searchUrl('https://clinicaltrials.gov/search', {
      cond: condition,
      term: intervention,
      locStr: location === 'Egypt' ? 'Egypt' : '',
    }),
    note: 'Registry record is sponsor-submitted research information. Registration is not clinical guideline endorsement and does not make a treatment appropriate.',
  },
  {
    id: 'who-ictrp',
    title: 'WHO ICTRP Search Portal',
    description: 'Cross-registry discovery for ongoing and completed trials from participating registries.',
    kind: 'trial-registry',
    url: () => 'https://trialsearch.who.int/Default.aspx',
    note: 'Search the condition/intervention on the portal. WHO notes that registry records are not endorsed by WHO and should not be used in care without a licensed professional.',
  },
  {
    id: 'pubmed',
    title: 'PubMed · clinical studies and systematic reviews',
    description: 'Find peer-reviewed papers that may report trial outcomes and systematic reviews.',
    kind: 'literature',
    url: (condition, intervention) => {
      const query = [
        condition ? '(' + condition + '[Title/Abstract])' : '',
        intervention ? '(' + intervention + '[Title/Abstract])' : '',
        '(Clinical Trial[Publication Type] OR Randomized Controlled Trial[Publication Type] OR Systematic Review[Publication Type] OR Meta-Analysis[Publication Type])',
      ].filter(Boolean).join(' AND ');
      return searchUrl('https://pubmed.ncbi.nlm.nih.gov/', {term: query});
    },
    note: 'Check the actual methods, population, comparator, outcomes, harms and whether findings are applicable to the intended patient group.',
  },
  {
    id: 'pubmed-clinical-queries',
    title: 'PubMed Clinical Queries',
    description: 'A clinical-study search interface with filters for evidence discovery.',
    kind: 'literature',
    url: (condition, intervention) => searchUrl('https://pubmed.ncbi.nlm.nih.gov/', {
      term: [condition, intervention, 'clinical trial'].filter(Boolean).join(' '),
    }),
    note: 'Search results are literature leads, not automatically assessed evidence or a prescription pathway.',
  },
  {
    id: 'lactmed',
    title: 'NIH LactMed',
    description: 'Drug-specific literature on breast-milk levels, possible infant effects and reported therapeutic alternatives.',
    kind: 'medicine-info',
    url: (_condition, intervention) => intervention
      ? searchUrl('https://www.ncbi.nlm.nih.gov/books/', {term: intervention + ' LactMed'})
      : 'https://www.ncbi.nlm.nih.gov/books/NBK501922/',
    note: 'Use for lactation research only alongside current clinical review. It is not a pregnancy-safety guarantee.',
  },
  {
    id: 'dailymed',
    title: 'NIH DailyMed · current submitted drug labels',
    description: 'Review official label text for indications, contraindications, warnings, adverse reactions, interactions and dosage information.',
    kind: 'medicine-info',
    url: (_condition, intervention) => intervention
      ? searchUrl('https://dailymed.nlm.nih.gov/dailymed/search.cfm', {query: intervention})
      : 'https://dailymed.nlm.nih.gov/dailymed/',
    note: 'US labeling may not match Egyptian registration, brand, availability or local prescribing guidance.',
  },
  {
    id: 'eda-drug-info',
    title: 'Egyptian Drug Authority · Drug Information Center',
    description: 'Egypt-specific medicine information inquiry service through the Egyptian Pharmaceutical Information Center.',
    kind: 'medicine-info',
    url: () => 'https://edaegypt.gov.eg/en/about-us/home-page-services/home-page-services/inquire-about-reliable-drug-information/',
    note: 'Published contact: 02 2535 4188 · did.admin@edaegypt.gov.eg · Sunday–Thursday, 9:00–15:00 Egypt time. Confirm current details on the official site.',
  },
  {
    id: 'eda-guidance',
    title: 'Egyptian Drug Authority · regulatory and pharmacovigilance guidance',
    description: 'Reference for Egypt-specific medicine regulation and adverse-reaction reporting resources.',
    kind: 'safety',
    url: () => 'https://edaegypt.gov.eg/en/the-regulatory-reference-of-the-egyptian-drug-authority-eda/guidance/',
    note: 'Use the currently applicable Egyptian product registration, labeling and safety guidance; do not import US approvals as proof of Egypt authorization.',
  },
  {
    id: 'eda-adverse-reactions',
    title: 'Egyptian Drug Authority · adverse-effect reporting',
    description: 'Official reporting route for suspected adverse reactions and medicine/device safety events.',
    kind: 'safety',
    url: () => 'https://edaegypt.gov.eg/en/about-us/home-page-services/home-page-services/reporting-side-effects/',
    note: 'For emergencies, use the local emergency pathway rather than an asynchronous reporting form.',
  },
  {
    id: 'who-guidelines',
    title: 'WHO guidelines and recommendations',
    description: 'International guidance for evidence synthesis and background review.',
    kind: 'guideline',
    url: () => 'https://www.who.int/publications/who-guidelines',
    note: 'International guidance still needs applicability review against Egypt’s local policy, facility protocol and authorized product information.',
  },
];

function kindLabel(kind: ResearchLink['kind']): string {
  switch (kind) {
    case 'trial-registry': return 'TRIAL REGISTRY';
    case 'literature': return 'LITERATURE';
    case 'medicine-info': return 'MEDICINE INFORMATION';
    case 'guideline': return 'GUIDELINES';
    case 'safety': return 'MEDICINE SAFETY';
  }
}

export default function TrialsInformationPage() {
  const [condition, setCondition] = useState('');
  const [intervention, setIntervention] = useState('');
  const [location, setLocation] = useState('Egypt');
  const [searched, setSearched] = useState(false);

  const matchedGuidelines: EvidenceSource[] = useMemo(() => {
    if (!searched || !condition.trim()) return [];
    return searchObgynSources(condition + ' ' + intervention, 'EG', 5);
  }, [condition, intervention, searched]);

  const runSearch = () => {
    if (!condition.trim() && !intervention.trim()) return;
    setSearched(true);
  };

  const links = RESEARCH_LINKS.map(item => ({
    ...item,
    href: item.url(condition, intervention, location),
  }));

  return (
    <div className="trials-information-page">
      <div className="page-heading">
        <div>
          <div className="eyebrow">DR. MIA · RESEARCH INTELLIGENCE</div>
          <h1>Clinical trials &amp; information centers</h1>
          <p>Find trial records, published studies, drug labels, Egyptian medicine information and clinical guidelines for clinician review.</p>
        </div>
        <span className="status status-amber"><Activity size={13} /> Research support only</span>
      </div>

      <div className="trials-safety-notice">
        <ShieldCheck size={18} />
        <div>
          <strong>Research is not a prescribing pathway</strong>
          <p>
            Enter a condition/topic and, optionally, a medicine or intervention. Use search terms only,
            never patient names, identifiers, symptoms copied from a real chart, or other personal health information.
            A trial registration, abstract, press release or search ranking is not proof that a medicine should be used.
            Review the complete study, posted results, harms, publication status, population and current local guideline.
          </p>
        </div>
      </div>

      <section className="panel trials-search-panel">
        <div className="panel-heading">
          <div>
            <h3>Research search builder</h3>
            <p>One topic search creates separate links to independent research and medicine-information centers.</p>
          </div>
          <span className="count-chip">No patient data stored</span>
        </div>
        <div className="trials-search-grid">
          <div className="form-field">
            <label htmlFor="trial-condition">Condition or research topic</label>
            <input id="trial-condition" value={condition} maxLength={180}
              placeholder="e.g. postpartum haemorrhage, endometriosis, dental pain"
              onChange={event => { setCondition(event.target.value); setSearched(false); }} />
          </div>
          <div className="form-field">
            <label htmlFor="trial-intervention">Medicine or intervention (optional)</label>
            <input id="trial-intervention" value={intervention} maxLength={120}
              placeholder="Generic name or intervention"
              onChange={event => { setIntervention(event.target.value); setSearched(false); }} />
          </div>
          <div className="form-field">
            <label htmlFor="trial-location">Trial location focus</label>
            <select id="trial-location" value={location}
              onChange={event => { setLocation(event.target.value); setSearched(false); }}>
              <option value="Egypt">Egypt</option>
              <option value="Global">Global / any location</option>
            </select>
          </div>
        </div>
        <div className="form-actions">
          <button type="button" className="btn btn-primary" onClick={runSearch}>
            <Search size={15} /> Build source searches
          </button>
          <button type="button" className="btn btn-secondary" onClick={() => {
            setCondition('');
            setIntervention('');
            setLocation('Egypt');
            setSearched(false);
          }}>Clear</button>
        </div>
        {searched && !condition.trim() && !intervention.trim() ? (
          <p className="trials-inline-error" role="status">Enter a non-identifying research topic or medicine name.</p>
        ) : null}
        {searched ? (
          <div className="research-links-grid" aria-live="polite">
            {links.map(link => (
              <article className="research-link-card" key={link.id}>
                <span className={'research-link-kind kind-' + link.kind}>{kindLabel(link.kind)}</span>
                <h3>{link.title}</h3>
                <p>{link.description}</p>
                <p className="research-link-note">{link.note}</p>
                <a href={link.href} target="_blank" rel="noopener noreferrer">
                  Open search / information center <ExternalLink size={13} />
                </a>
              </article>
            ))}
          </div>
        ) : (
          <div className="research-links-preview">
            <h3><FlaskConical size={16} /> Search many sources from one neutral query</h3>
            <p>The page opens public sources in separate tabs. Mia does not scrape records into a treatment recommendation, store the query, or send patient data.</p>
            <div className="research-link-chips">
              <span>ClinicalTrials.gov</span><span>WHO ICTRP</span><span>PubMed</span>
              <span>NIH LactMed</span><span>DailyMed</span><span>Egyptian Drug Authority</span>
            </div>
          </div>
        )}
      </section>

      {searched && matchedGuidelines.length > 0 ? (
        <section className="panel trials-local-guidelines">
          <div className="panel-heading">
            <div>
              <h3><BookOpen size={15} /> Matching Egypt-scope guideline/reference links</h3>
              <p>Keyword relevance only. These links are not graded evidence and are not medication approvals.</p>
            </div>
            <span className="count-chip">{matchedGuidelines.length} source links</span>
          </div>
          <div className="trials-guideline-list">
            {matchedGuidelines.map(source => (
              <a key={source.id} href={source.url} target="_blank" rel="noopener noreferrer">
                <strong>{source.title}</strong>
                <span>{source.publisher} · {source.year || 'Version needs confirmation'}</span>
                <small>{source.note}</small>
              </a>
            ))}
          </div>
        </section>
      ) : null}

      <section className="trials-method-panel">
        <Info size={17} />
        <div>
          <strong>How Mia should evaluate trial evidence</strong>
          <ol>
            <li>Check the registry record, study design, phase, comparator, recruitment status, country/site, eligibility and outcome measures.</li>
            <li>Check whether results are posted and look for related peer-reviewed publications; distinguish protocol/planned outcomes from observed results.</li>
            <li>Review absolute benefit and harms, uncertainty, sample size, bias, and whether the population matches the clinical question.</li>
            <li>Prefer current approved Egypt/local guidelines and official Egyptian product information for treatment decisions. Trial evidence can inform a clinician's appraisal but cannot by itself authorize a medicine.</li>
            <li>Only after a separate clinical-governance workflow approves a narrow diagnosis pathway may it appear in Medication pathways.</li>
          </ol>
        </div>
      </section>
    </div>
  );
}
