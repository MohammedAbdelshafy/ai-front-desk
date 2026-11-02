# Data Retention & Deletion — Mia Dental OS

> **DRAFT v0.1 — 2026-10-11 — requires qualified legal review before production use or real patient data.**
> This is a starting draft, not legal advice. It has not been reviewed by an attorney.

**Operator:** MBM (Mohammed Abdelshafy), contact: abdelshafyclapps@gmail.com

## 1. What we keep while your account is active

- Account profile (name, email, clinic name, password hash, legal-acceptance record).
- Patient workspace data you enter: patient labels, allergies, medications, conditions, wizard answers, intended prescriptions, check results, your review conclusions.
- Audit log entries (actor, action, timestamp).
- Trial/subscription records.

## 2. Retention schedule

| Data | While active | After cancellation / deletion request |
|---|---|---|
| Account profile | Kept | Deleted within 30 days of verified request |
| Patient workspace data | Kept | Exportable for 90 days after cancellation; deleted within 30 days of a verified deletion request |
| Audit log (identifiable) | Kept | Anonymized (see §4) within 90 days |
| Trial/subscription records | Kept | Kept 7 years for tax/accounting where required by law, then deleted |
| Server error logs | 90 days rolling | 90 days rolling |

## 3. How to request export or deletion

Email **abdelshafyclapps@gmail.com** from your account email with subject "Data export request" or "Data deletion request." We verify your identity via your account, then:

- **Export:** we provide your patient workspace data and check history in a portable format (CSV/JSON) within 30 days.
- **Deletion:** we delete identifiable data per the schedule above and confirm in writing within 30 days.

## 4. What survives deletion (and why)

- **Anonymized audit minimums:** after deletion, we may retain de-identified records of the *fact* that checks occurred (counts, timestamps, verdict distribution — no patient labels, no dentist identity, no clinical details) for product safety monitoring and legal compliance. These cannot be re-linked to you.
- **Legal holds:** where tax, accounting, or litigation law requires retention, the minimum required records are kept for the legally required period and then deleted.

## 5. Demo data

"Explore demo" data is synthetic, shared across demo explorers, and may be wiped at any time without notice. Never put anything real in the demo.

## 6. No silent deletion

We do not silently delete your data on trial expiry or cancellation. Data is preserved per the schedule above so you can export or resubscribe.
