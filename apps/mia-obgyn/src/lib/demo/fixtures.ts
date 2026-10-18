import type { Appointment, Patient, QuestionnaireResponse, QuestionnaireTemplate } from "../domain/types";

export const patients: Patient[] = [
  { id:"demo-patient-001",isSynthetic:true,demoName:"Demo Patient 01",displayId:"DEMO-001",ageYears:29,phone:"+20 100 000 0001",email:"patient01@example.invalid",allergyStatus:"confirmed-none",allergies:[],medicines:[{name:"Prenatal vitamin (demo)",ingredient:null,strength:null,route:"oral",status:"unverified",provenance:"synthetic-demo",lastVerified:null}],conditions:["Antenatal follow-up (synthetic)"],obstetricHistory:{gravidity:2,parity:1,lastMenstrualPeriod:"2026-03-02",gestationalWeeks:32,breastfeeding:"no",notes:["All data fictional; not a medical recommendation."]},encounters:[{date:"2026-09-20",label:"Antenatal review",note:"Fictional follow-up; values intentionally incomplete.",provenance:"synthetic-demo"},{date:"2026-10-18",label:"Current visit",note:"Pre-visit questionnaire submitted.",provenance:"synthetic-demo"}],questionnaireIds:["demo-response-001"]},
  { id:"demo-patient-002",isSynthetic:true,demoName:"Demo Patient 02",displayId:"DEMO-002",ageYears:34,phone:"+20 100 000 0002",email:"patient02@example.invalid",allergyStatus:"known-allergies",allergies:[{substance:"Example medicine (fictional)",reaction:"Itching (fictional)",severity:"mild",provenance:"synthetic-demo",lastConfirmed:"2026-10-01"}],medicines:[{name:"Example iron product (demo)",ingredient:null,strength:null,route:"oral",status:"unverified",provenance:"synthetic-demo",lastVerified:null}],conditions:["Postpartum review (synthetic)"],obstetricHistory:{gravidity:1,parity:1,lastMenstrualPeriod:null,gestationalWeeks:null,breastfeeding:"yes",notes:["Breastfeeding status is fictional and requires confirmation in real care."]},encounters:[{date:"2026-10-08",label:"Postpartum contact",note:"Synthetic note; not a clinical assessment.",provenance:"synthetic-demo"}],questionnaireIds:["demo-response-002"]},
  { id:"demo-patient-003",isSynthetic:true,demoName:"Demo Patient 03",displayId:"DEMO-003",ageYears:41,phone:"+20 100 000 0003",email:"patient03@example.invalid",allergyStatus:"not-reviewed",allergies:[],medicines:[],conditions:["Gynaecology consultation (synthetic)"],obstetricHistory:{gravidity:null,parity:null,lastMenstrualPeriod:null,gestationalWeeks:null,breastfeeding:"unknown",notes:["History intentionally incomplete."]},encounters:[{date:"2026-08-26",label:"Prior consultation",note:"Fictional record with history requiring review.",provenance:"synthetic-demo"}],questionnaireIds:[]},
  { id:"demo-patient-004",isSynthetic:true,demoName:"Demo Patient 04",displayId:"DEMO-004",ageYears:25,phone:"+20 100 000 0004",email:"patient04@example.invalid",allergyStatus:"unknown",allergies:[],medicines:[],conditions:["Family planning (synthetic)"],obstetricHistory:{gravidity:0,parity:0,lastMenstrualPeriod:"2026-10-02",gestationalWeeks:null,breastfeeding:"no",notes:["Unknown allergies must not be interpreted as no allergies."]},encounters:[],questionnaireIds:[]},
  { id:"demo-patient-005",isSynthetic:true,demoName:"Demo Patient 05",displayId:"DEMO-005",ageYears:31,phone:"+20 100 000 0005",email:"patient05@example.invalid",allergyStatus:"known-allergies",allergies:[{substance:"Fictional adhesive",reaction:"Rash (fictional)",severity:"unknown",provenance:"synthetic-demo",lastConfirmed:null}],medicines:[],conditions:["Antenatal consultation (synthetic)"],obstetricHistory:{gravidity:3,parity:2,lastMenstrualPeriod:"2026-07-01",gestationalWeeks:15,breastfeeding:"no",notes:["All information is synthetic; gestational dates are illustrative."]},encounters:[{date:"2026-10-10",label:"Intake started",note:"Questionnaire incomplete.",provenance:"synthetic-demo"}],questionnaireIds:[]},
  { id:"demo-patient-006",isSynthetic:true,demoName:"Demo Patient 06",displayId:"DEMO-006",ageYears:28,phone:"+20 100 000 0006",email:"patient06@example.invalid",allergyStatus:"confirmed-none",allergies:[],medicines:[],conditions:["Gynaecology review (synthetic)"],obstetricHistory:{gravidity:null,parity:null,lastMenstrualPeriod:null,gestationalWeeks:null,breastfeeding:"unknown",notes:[]},encounters:[],questionnaireIds:[]}
];

export const appointments: Appointment[] = [
  { id:"demo-appt-001",patientId:"demo-patient-001",dateTime:"2026-10-18T09:30:00+03:00",service:"Antenatal",reason:"Routine antenatal follow-up (fictional)",status:"intake-received",questionnaireId:"demo-response-001",clinician:"Dr. Shafy (demo)",isSynthetic:true },
  { id:"demo-appt-002",patientId:"demo-patient-002",dateTime:"2026-10-18T11:00:00+03:00",service:"Postpartum",reason:"Postpartum check-in (fictional)",status:"needs-review",questionnaireId:"demo-response-002",clinician:"Dr. Shafy (demo)",isSynthetic:true },
  { id:"demo-appt-003",patientId:"demo-patient-003",dateTime:"2026-10-18T12:15:00+03:00",service:"Gynaecology",reason:"Gynaecology consultation (fictional)",status:"scheduled",questionnaireId:null,clinician:"Dr. Shafy (demo)",isSynthetic:true },
  { id:"demo-appt-004",patientId:"demo-patient-005",dateTime:"2026-10-18T13:30:00+03:00",service:"Antenatal",reason:"Antenatal assessment (fictional)",status:"scheduled",questionnaireId:null,clinician:"Dr. Shafy (demo)",isSynthetic:true },
  { id:"demo-appt-005",patientId:"demo-patient-004",dateTime:"2026-10-18T14:15:00+03:00",service:"Family planning",reason:"Family planning discussion (fictional)",status:"needs-review",questionnaireId:null,clinician:"Dr. Shafy (demo)",isSynthetic:true}
];

export const questionnaireTemplates: QuestionnaireTemplate[] = [
  { id:"obgyn-general-intake",version:1,title:"OB-GYN pre-visit questionnaire",specialty:"OB-GYN",status:"published",questions:[
    {id:"reason",label:"What would you like the doctor to help with today?",type:"text",required:true},
    {id:"symptom-onset",label:"When did this begin?",type:"select",options:["Today","1–3 days ago","4–7 days ago","More than a week ago","Not sure"],required:true},
    {id:"pain",label:"Are you experiencing pain now?",type:"yesno",required:true},
    {id:"pain-location",label:"Where is the pain located?",type:"text",required:false,showIf:{questionId:"pain",equals:"yes"}},
    {id:"bleeding",label:"Are you experiencing bleeding that concerns you?",type:"yesno",required:true},
    {id:"bleeding-details",label:"Please describe the bleeding in your own words.",type:"text",required:false,showIf:{questionId:"bleeding",equals:"yes"}},
    {id:"lmp",label:"First day of your last menstrual period (if known)",type:"date",required:false},
    {id:"pregnancy",label:"Are you currently pregnant, possibly pregnant, or unsure?",type:"select",options:["Pregnant","Possibly pregnant","Not pregnant","Not sure","Prefer not to answer"],required:true},
    {id:"gestational-week",label:"Pregnancy week if already known",type:"number",required:false,showIf:{questionId:"pregnancy",equals:"Pregnant"}},
    {id:"breastfeeding",label:"Are you currently breastfeeding?",type:"select",options:["Yes","No","Not applicable","Not sure","Prefer not to answer"],required:true},
    {id:"allergies",label:"Do you have any medicine allergies or reactions?",type:"select",options:["Yes","No known allergies","Not sure","Prefer not to answer"],required:true},
    {id:"allergy-details",label:"Which medicine and what reaction occurred?",type:"text",required:false,showIf:{questionId:"allergies",equals:"Yes"}},
    {id:"medicines",label:"Please list current medicines, vitamins and supplements.",type:"text",required:true},
    {id:"conditions",label:"Relevant medical conditions or previous complications",type:"text",required:false},
    {id:"consent-understanding",label:"I understand this questionnaire does not replace urgent medical care.",type:"select",options:["Understood"],required:true}
  ]},
  { id:"antenatal-follow-up",version:1,title:"Antenatal follow-up add-on",specialty:"OB-GYN",status:"published",questions:[
    {id:"g-p",label:"Previous pregnancies and births (if known)",type:"text",required:false},
    {id:"prior-complications",label:"Any prior pregnancy or birth complications?",type:"yesno",required:true},
    {id:"complication-details",label:"Please describe the complication",type:"text",required:false,showIf:{questionId:"prior-complications",equals:"yes"}},
    {id:"fetal-movement",label:"If applicable, has the baby's movement changed from usual?",type:"select",options:["No change","Changed","Not applicable","Not sure"],required:false},
    {id:"care-concerns",label:"What else would you like the clinician to know?",type:"text",required:false}
  ]}
];

export const questionnaireResponses: QuestionnaireResponse[] = [
  {id:"demo-response-001",templateId:"obgyn-general-intake",templateVersion:1,patientId:"demo-patient-001",appointmentId:"demo-appt-001",answers:{reason:"Routine antenatal follow-up (synthetic)", "symptom-onset":"Not sure",pain:"no",bleeding:"no",pregnancy:"Pregnant","gestational-week":"32",breastfeeding:"No",allergies:"No known allergies",medicines:"Prenatal vitamin (demo)","consent-understanding":"Understood"},status:"submitted",submittedAt:"2026-10-18T08:55:00+03:00",isSynthetic:true},
  {id:"demo-response-002",templateId:"obgyn-general-intake",templateVersion:1,patientId:"demo-patient-002",appointmentId:"demo-appt-002",answers:{reason:"Postpartum follow-up (synthetic)","symptom-onset":"Not sure",pain:"no",bleeding:"no",pregnancy:"Not pregnant",breastfeeding:"Yes",allergies:"Yes","allergy-details":"Example medicine; itching (fictional)",medicines:"Example iron product (demo)","consent-understanding":"Understood"},status:"submitted",submittedAt:"2026-10-18T10:20:00+03:00",isSynthetic:true}
];
