# Choros — Source Material: Production CTE Systems

> **Purpose:** This is the full inventory of real CTE systems built and deployed across a large urban district (31K+ students, 50+ campuses, 17 production systems).
> Choros will either replace, absorb, or learn from these. Better to have the full list and edit down than miss something that mattered.

---

## How to use this for Choros

Each system below represents **real work that shipped**. For Choros timeline planning:

- **COMPLETE** = already exists, Choros needs to match or exceed
- **PARTIAL** = exists but has gaps Choros fills
- **LEARN** = approach worth studying, not feature parity

---

## 1. Teacher Management Systems

### Teacher Tracking & Assignment

| Original Name | Professional Title | What It Does | Choros Relevance |
|---|---|---|---|
| teacher-tracker | **Teacher Assignment & Roster Management System** | Canonical deployed GAS tool tracking every CTE teacher, their campus, and their course assignments | COMPLETE — core teacher record |
| CTE Teacher Change Tracker | **Teacher Role Change Detection Engine** | Detects when teachers change assignments, campuses, or leave — alerts central office | COMPLETE — teacher lifecycle |
| Teacher certification checker | **CTE Certification Compliance Validator** | Python tool that checks every CTE teacher's certifications against state requirements | COMPLETE — certification audit |
| Teacher Assignment Letter | **Teacher Placement Letter Generator** | Generates formal assignment letters for teacher placements | PARTIAL — document generation |
| Onboarding | **New CTE Teacher Onboarding Automation** | Materials and automation for onboarding new CTE teachers | LEARN — onboarding workflow |

### Teacher Communication

| Original Name | Professional Title | What It Does | Choros Relevance |
|---|---|---|---|
| Campus Contact Merge | **Campus Contact Directory & Mail-Merge** | Merges campus contact information for department-wide communication | PARTIAL — contact management |
| Mass Email | **Department-Wide Communication Tool** | Bulk email tool for department announcements | COMPLETE — teacher messaging |
| Teacher Campus Visit update | **Campus Visit Scheduling & Tracking System** | Tracks and updates campus visit schedules for CTE staff | LEARN — scheduling pattern |

### Teacher Reporting

| Original Name | Professional Title | What It Does | Choros Relevance |
|---|---|---|---|
| o-weekly-report | **Weekly CTE Operations Report Engine** | Main Python repo building weekly teacher/roster report + warehouse audit | COMPLETE — flagship reporting |
| EIF Teacher Weekly Mailmerge | **Weekly Teacher Enrollment Update** | Weekly mail-merge pushing enrollment data to teachers | PARTIAL — teacher data feed |
| TeacherTracker (Reports) | **Teacher Assignment & Roster Report** | Report variant tracking teacher assignments across campuses | COMPLETE — roster visibility |
| TeacherTracker (ToolKit) | **Teacher Management Toolkit** | Toolkit version with extended teacher management features | LEARN — toolkit pattern |

---

## 2. Student Program Systems

### Certification & IBC Tracking

| Original Name | Professional Title | What It Does | Choros Relevance |
|---|---|---|---|
| IBC Tracker | **District-Wide Industry Certification Tracking System** | Canonical IBC tracking tool (GAS-connected), tracks student certifications across all campuses | COMPLETE — core IBC pipeline |
| 23-24 IBC Earnings Report | **Annual IBC Earnings & Attainment Report** | Full reporting package for IBCs earned in 2023-24 school year | LEARN — annual reporting |
| IBC Tracker Post Script | **IBC Data Validation & Cleanup Pipeline** | Post-processing scripts that clean and finalize IBC tracker data | PARTIAL — data quality |
| IBC Sorter | **IBC Record Classification Engine** | Node tool that sorts and categorizes raw IBC records | PARTIAL — IBC processing |
| Campus IBC Percentage Calculator | **Per-Campus IBC Attainment Analytics** | Calculates per-campus IBC attainment percentages | COMPLETE — campus metrics |
| IBC Sort (Report) | **IBC Classification Report** | Sorted/categorized IBC report | LEARN — report variant |
| Custom IBC (Report) | **Custom IBC Attainment Report** | Custom IBC report for individual staff requests | LEARN — ad-hoc reporting |
| q2-ibc-crosswalk | **Quarterly IBC Standards Crosswalk** | Maps IBC certifications to program standards quarterly | PARTIAL — compliance crosswalk |
| pos-ibc-official-doc | **POS-to-IBC Crosswalk Documentation** | Official documentation mapping Programs of Study to IBCs | COMPLETE — standards alignment |
| grads-ibc-l2 | **Graduate Level-2 IBC Attainment Report** | Reports Level-2 IBC attainment for graduating class | LEARN — graduation metric |

### Student Enrollment & Pathways

| Original Name | Professional Title | What It Does | Choros Relevance |
|---|---|---|---|
| student-enrollment | **Student Enrollment Analytics System** | Python analysis and reporting system for student enrollment patterns | COMPLETE — enrollment analytics |
| CTE Middle School Experience Tracker | **Middle School CTE Pathway Tracker** | Tracks MS students through CTE exploration experiences | COMPLETE — pathway tracking |
| MS POS DATA | **Middle School Program of Study Selection Portal** | Deployed MS POS selection system (canonical clasp) | COMPLETE — course selection |
| 8th-grade-forecast | **8th Grade Enrollment Projection Model** | Projects 8th grade enrollment for upcoming school years | PARTIAL — forecasting |
| 9th Grade Count | **9th Grade Transition Enrollment Count** | Quick 9th grade count for incoming cohort sizing | LEARN — cohort tracking |
| Enrollment Seat Count | **Campus Enrollment Capacity Analyzer** | Computes available vs used enrollment seats per campus | PARTIAL — capacity planning |
| Course Enrollment Report | **Course Enrollment & Sequence Report** | Tracks course enrollment and sequence completion | COMPLETE — course-level data |

### CCMR & Readiness

| Original Name | Professional Title | What It Does | Choros Relevance |
|---|---|---|---|
| Projected CCMR | **College, Career & Military Readiness Projection Engine** | Work-in-progress CCMR projection calculator | COMPLETE — CCMR forecasting |
| seniors-ccmr | **Senior CCMR Readiness Report** | CCMR readiness report for graduating seniors | COMPLETE — graduation readiness |

---

## 3. Program & Curriculum Systems

### Program of Study Management

| Original Name | Professional Title | What It Does | Choros Relevance |
|---|---|---|---|
| POS Sequence | **Program of Study Sequence Validator** | Builds and validates POS course sequences against requirements | COMPLETE — POS integrity |
| pos-sequence | **Program of Study Sequence Builder** | One-off POS sequence construction tool | LEARN — POS builder |
| pos-courses | **POS Course Listing Generator** | Generates course lists for Programs of Study | PARTIAL — course catalog |
| program-of-study-sheet | **Program of Study Summary Sheet Builder** | Produces summary sheets for each POS | PARTIAL — POS documentation |
| tea-cte-teks | **TEA CTE Standards Alignment System** | Maps TEA courses to TEKS standards (apps_script + syllabi) | COMPLETE — standards mapping |
| teks-pdf-scraper | **TEKS Standards Document Parser** | Node scraper that extracts TEKS data from TEA PDFs | PARTIAL — standards extraction |

### Course Management

| Original Name | Professional Title | What It Does | Choros Relevance |
|---|---|---|---|
| cte-course-audit | **CTE Course Offering Compliance Audit** | Git-tracked audit of CTE course offerings against requirements | COMPLETE — course audit |
| course-catalog | **CTE Course Catalog Generator** | Generates the district CTE course catalog | COMPLETE — catalog production |
| course-catalog-master-schedule | **Course Catalog & Master Schedule Integrator** | Ties course catalog to master schedule data | COMPLETE — scheduling alignment |
| course-cost-analysis | **CTE Course Cost Analysis Tool** | Analyzes per-course costs for budget planning | PARTIAL — cost analytics |
| Next Class | **Course Sequencing Utility** | Utility for "next class" scheduling logic | LEARN — sequencing logic |

### Program Reviews

| Original Name | Professional Title | What It Does | Choros Relevance |
|---|---|---|---|
| cosmetology-review | **Cosmetology Program Performance Review** | Deep-dive review of cosmetology program data | LEARN — program review |
| jrotc-review | **JROTC Program Data Review** | JROTC program performance analysis | LEARN — program review |
| cte-annual-evaluation | **CTE Annual Program Evaluation** | Comprehensive annual CTE program evaluation | COMPLETE — annual evaluation |

---

## 4. Operations & Data Infrastructure

### Weekly Operations (RTB Pipeline)

| Original Name | Professional Title | What It Does | Choros Relevance |
|---|---|---|---|
| o-weekly-report | **Weekly CTE Operations Report Engine** | Main Python repo: teacher/roster report + warehouse audit | COMPLETE — core operations |
| rtb-summary-data-node | **RTB Summary Data Aggregator** | Node data node feeding the RTB weekly summary | PARTIAL — data aggregation |
| google-apps-script | **Weekly Roster Publisher for Google Sheets** | Publishes the weekly roster to Google Sheets | COMPLETE — roster publishing |
| audit-tools | **Teacher-Data Alignment Audit Suite** | Scripts running warehouse/teacher-data alignment audits | COMPLETE — data quality |
| Middle School RTB Meeting Document | **MS Weekly Operations Meeting Brief** | Generates the MS weekly RTB meeting document | PARTIAL — meeting prep |
| cte-weekly-report | **Legacy Weekly CTE Operations Report** | Older standalone weekly report (predecessor) | LEARN — evolution |

### Data Warehouse & Integration

| Original Name | Professional Title | What It Does | Choros Relevance |
|---|---|---|---|
| warehouse | **CTE Data Warehouse (DuckDB)** | Local DuckDB warehouse staging budget/EIF/IBC/curriculum data | COMPLETE — data backbone |
| Exstract | **CTE Data Extraction & Export Tool** | CTE data extract tool pulling from multiple sources | COMPLETE — data extraction |
| CTE-Extract-Dev | **CTE Data Extract Development Environment** | Dev version of the CTE extract pipeline | LEARN — dev pipeline |
| cte_extract | **CTE Data Extract Report** | Report variant of CTE data extraction | LEARN — report variant |
| mydata-portal-scraper | **District Student Data Portal Scraper** | Automated scraper for the district student data portal | COMPLETE — data ingestion |
| MS Data EIF Processor | **Middle School EIF Data Pipeline** | Processes MS enrollment/funding data | PARTIAL — MS data pipeline |
| opencode-inbox | **Document Drop-Folder Processing Pipeline** | Drop-folder pipeline for CTE operational documents | LEARN — doc processing |

### Data Processing & Documents

| Original Name | Professional Title | What It Does | Choros Relevance |
|---|---|---|---|
| mail-merge | **Multi-Source Data Merge & Communication Engine** | Python course/teacher mail-merge processing system | COMPLETE — merge engine |
| Document Cloud / 2 | **Adobe Document Cloud Automation Pipeline** | Adobe Document Cloud automation (two iterations) | LEARN — doc automation |
| Document Reworker | **Bulk Document Reformatting Tool** | Reworks and reformats documents in bulk | PARTIAL — doc processing |
| PDF Extract | **PDF Data Extraction Engine** | Extracts structured data from PDF documents | COMPLETE — PDF extraction |
| PDF Budget | **Budget Document Processing Engine** | Deployed GAS budget PDF processor (canonical clasp) | COMPLETE — budget docs |
| CampusPDFCreator | **Campus PDF Document Generator** | Deployed GAS tool generating campus PDFs | COMPLETE — PDF generation |
| PDFUpload | **PDF Document Upload Pipeline** | Handles PDF uploads into the toolkit | PARTIAL — upload pipeline |
| pdf-fill | **District PDF Form Filler** | Fills district PDF forms (e.g., Travel Authorization) | PARTIAL — form automation |
| pdf-combiner | **PDF Document Merger** | Combines and merges PDF documents | LEARN — utility |

### EIF & State Reporting

| Original Name | Professional Title | What It Does | Choros Relevance |
|---|---|---|---|
| EIF Weekly Data Report | **Weekly Enrollment & Funding Data Report** | Weekly EIF enrollment/funding data report | COMPLETE — funding visibility |
| EIF Data Statistical Evaluation | **EIF Data Statistical Analysis Suite** | Statistical evaluation of EIF data patterns | PARTIAL — data analysis |
| summer-peims-validation | **Summer PEIMS Submission Validator** | Validates summer PEIMS submission data | COMPLETE — state compliance |
| Accounting Student Count | **Student Count Reconciliation Report** | Student count reconciliation for accounting department | PARTIAL — reconciliation |
| Enrollment Dump | **Enrollment Data Archive** | Raw enrollment data holding area | LEARN — data archival |
| Data Rework Request | **Ad-Hoc Data Analysis Pipeline** | Custom data rework pipeline for department requests | LEARN — ad-hoc pattern |

---

## 5. Communication & Engagement Systems

### Stakeholder Communication

| Original Name | Professional Title | What It Does | Choros Relevance |
|---|---|---|---|
| Campus Contact Merge | **Campus Contact Directory & Mail-Merge** | Mail-merge of campus contact info | COMPLETE — directory |
| Mass Email | **Department-Wide Communication Tool** | Bulk email for department announcements | COMPLETE — broadcast |
| Showcase Mailmerge | **Showcase Event Communication Campaign** | Mail-merge for showcase event communications | LEARN — event comms |
| Teacherlistpdf | **Teacher Roster PDF Generator** | Produces teacher-list PDFs for distribution | PARTIAL — roster docs |

### Trustee & Leadership

| Original Name | Professional Title | What It Does | Choros Relevance |
|---|---|---|---|
| trustee-tracker | **School Board Trustee Metrics Dashboard** | Tracks campus metrics (CCMR, IEP, IBC) for board trustees | COMPLETE — leadership reporting |
| Campus Report Gen | **Per-Campus Performance Report Generator** | Generates individual campus performance reports | COMPLETE — campus reports |

### Events & Showcase

| Original Name | Professional Title | What It Does | Choros Relevance |
|---|---|---|---|
| MS Showcase | **Middle School CTE Program Showcase** | Materials for the MS CTE showcase event | LEARN — event materials |
| Showcase Shirt Numbers | **Showcase Event Logistics Tracker** | Tracks shirt sizes and counts for showcase logistics | LEARN — event logistics |
| graphics-showcase | **Report Graphics & Visual Asset Library** | Graphics and visual assets for reporting | LEARN — visual assets |
| pd-feedback | **Professional Development Feedback Collector** | Collects and processes PD feedback | PARTIAL — feedback loop |

---

## 6. Budget & Resource Systems

| Original Name | Professional Title | What It Does | Choros Relevance |
|---|---|---|---|
| Budget Tracker | **CTE Budget Expenditure Tracker** | Tracks CTE budget spend against allocations | COMPLETE — budget tracking |
| Budget Mailmerge | **Budget Communication & Notification System** | Active budget mail-merge for stakeholders | PARTIAL — budget comms |
| Budget Projects | **Budget Project Portfolio Manager** | Collection of budget project workbooks | LEARN — portfolio view |
| Budget Toolkit | **Budget Operations Utility Suite** | Reusable budget helper tools | LEARN — utility pattern |
| budget-intake-desktop | **Budget Request Intake Desktop Tool** | Desktop tool for budget request intake | PARTIAL — intake workflow |
| Reports / BUDGET | **Budget Analytics Report Generator** | Budget-focused reporting scripts | PARTIAL — budget reports |

---

## 7. Platform & Infrastructure Systems

### Core Platform

| Original Name | Professional Title | What It Does | Choros Relevance |
|---|---|---|---|
| CTE MAIN / CTECERT | **CTE Teacher Certification Management Suite** | Certification tooling: CSV dedup, deploy, CTAT, helper scripts | COMPLETE — cert platform |
| cord-workstation | **CTE Operations Dashboard** | CTE Dashboard / workstation (GAS, canonical clasp) | COMPLETE — operations hub |
| InternalA | **Internal Administration Module** | Internal/admin GAS module within CTE MAIN | LEARN — admin panel |

### Middle School Systems

| Original Name | Professional Title | What It Does | Choros Relevance |
|---|---|---|---|
| Middle School Engine Room | **MS CTE Data Operations Hub** | Core MS Engine Room data tooling | COMPLETE — MS hub |
| Engine Room | **MS CTE Strategic Planning Workbook** | Annual MS planning workbook with scripts | PARTIAL — planning |
| Middle School Matrix | **MS Course & Campus Matrix Builder** | Builds the course/campus matrix for MS programs | COMPLETE — MS matrix |

### Technology & Assets

| Original Name | Professional Title | What It Does | Choros Relevance |
|---|---|---|---|
| TechnologyTracker | **Technology Asset Inventory Report** | Tracks technology devices and inventory | PARTIAL — asset tracking |
| tech-tracker | **Technology Asset Tracking System** | Device tracking system (canonical clasp) | COMPLETE — device tracking |

### Specialized Programs

| Original Name | Professional Title | What It Does | Choros Relevance |
|---|---|---|---|
| work-based-learning / WBL Engine Room | **Work-Based Learning Operations Hub** | WBL engine room tooling for internships/apprenticeships | COMPLETE — WBL operations |
| ctedataretreat | **CTE Annual Data Retreat Package** | Full data retreat package: data, IBC library, docs | LEARN — annual event |
| Code Breaker | **CTE Student Engagement Activity** | Interactive CTE activity/game for students | LEARN — student tool |
| Chat | **Data Processing Chat Interface** | Experimental chat interface for data processing | LEARN — AI interface |
| Calendar Automation | **Calendar & Schedule Automation Tool** | Automated calendar and scheduling tool | LEARN — scheduling |
| cursor-gas-demo | **AI-Assisted Apps Script Development** | Demo of driving GAS development from AI-assisted IDE | LEARN — AI in dev |

---

## Summary: What Choros Needs to Cover

Based on this inventory, Choros needs to address these capability areas:

### Tier 1 — Core (must match or exceed)
1. **Teacher Roster & Assignment** — who teaches what, where
2. **Certification Compliance** — are they certified to teach it
3. **Student Certification Tracking (IBC)** — who earned what
4. **Program of Study Management** — are sequences valid
5. **Weekly Operations Report** — the RTB heartbeat
6. **Data Warehouse** — single source of truth

### Tier 2 — Important (should cover)
7. **Stakeholder Communication** — mail-merge, mass email
8. **Enrollment & Forecasting** — seat counts, projections
9. **State Compliance (PEIMS/TEA)** — submissions, validations
10. **Budget Tracking** — spend against allocations
11. **Leadership Reporting** — trustee dashboards, campus reports
12. **Document Processing** — PDF generation, form filling

### Tier 3 — Nice to Have (learn from)
13. **Event Management** — showcase, data retreat
14. **Asset Tracking** — technology, devices
15. **Work-Based Learning** — internships, apprenticeships
16. **AI-Assisted Development** — the meta-layer

---

## Project Stats

| Metric | Count |
|---|---|
| Total production systems | 17 |
| Google Apps Script projects (clasp) | 12 |
| Python projects | 8 |
| Node.js projects | 4 |
| Complete (Choros must match) | 31 |
| Partial (Choros should cover) | 22 |
| Learn (approach worth studying) | 23 |
| Total projects inventoried | 76 |
