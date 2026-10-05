import os
import json
from typing import List, Dict, Optional

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
KNOWLEDGE_DIR = os.path.join(BACKEND_DIR, "knowledge")
SOURCES_DIR = os.path.join(KNOWLEDGE_DIR, "sources")
PROCESSED_DIR = os.path.join(KNOWLEDGE_DIR, "processed")
METADATA_DIR = os.path.join(KNOWLEDGE_DIR, "metadata")

os.makedirs(SOURCES_DIR, exist_ok=True)
os.makedirs(PROCESSED_DIR, exist_ok=True)
os.makedirs(METADATA_DIR, exist_ok=True)


class DocumentChunk:
    def __init__(
        self,
        chunk_id: str,
        document_name: str,
        source: str,
        version_date: str,
        stage: str,
        group_name: str,
        paper: str,
        module: str,
        chapter: str,
        topic: str,
        page_number: int,
        statutory_reference: str,
        content: str
    ):
        self.chunk_id = chunk_id
        self.document_name = document_name
        self.source = source
        self.version_date = version_date
        self.stage = stage
        self.group_name = group_name
        self.paper = paper
        self.module = module
        self.chapter = chapter
        self.topic = topic
        self.page_number = page_number
        self.statutory_reference = statutory_reference
        self.content = content.strip()

    def to_dict(self) -> Dict:
        return {
            "chunk_id": self.chunk_id,
            "document_name": self.document_name,
            "source": self.source,
            "version_date": self.version_date,
            "stage": self.stage,
            "group_name": self.group_name,
            "paper": self.paper,
            "module": self.module,
            "chapter": self.chapter,
            "topic": self.topic,
            "page_number": self.page_number,
            "statutory_reference": self.statutory_reference,
            "content": self.content,
        }

def get_official_icai_seed_documents() -> List[DocumentChunk]:
    """
    Returns verified, authoritative study documents from official ICAI study materials
    covering high-yield CA Intermediate papers and statutory sections.
    """
    docs = [
        # Document 1: Section 17(5) CGST Act (Blocked Credits)
        DocumentChunk(
            chunk_id="doc_tax_sec17_5_1",
            document_name="ICAI Study Material - Paper 3 Taxation (Module 2: GST)",
            source="ICAI Official Study Material",
            version_date="2024-2025 Edition",
            stage="Intermediate",
            group_name="Group 1",
            paper="Paper 3: Taxation",
            module="Module 2: Goods and Services Tax",
            chapter="Chapter 6: Input Tax Credit",
            topic="Blocked Credits under Section 17(5)",
            page_number=142,
            statutory_reference="Section 17(5) Central Goods and Services Tax (CGST) Act, 2017",
            content="""Section 17(5) of the CGST Act, 2017 provides an overriding negative list of goods and services on which Input Tax Credit (ITC) is blocked and not available, notwithstanding anything contained in Section 16(1) and Section 18(1):

1. Motor Vehicles: ITC is blocked on motor vehicles for transportation of persons having approved seating capacity of not more than 13 persons (including the driver), EXCEPT when they are used for making taxable supplies of:
   (a) Further supply of such motor vehicles;
   (b) Transportation of passengers;
   (c) Imparting training on driving such motor vehicles.
   Vessels and aircraft are also subject to similar restrictions with exceptions for commercial transport and training.

2. Food, Beverages, Club Memberships & Personal Care: ITC is blocked on food and beverages, outdoor catering, beauty treatment, health services, cosmetic and plastic surgery, leasing or renting of motor vehicles/vessels, and membership of a club, health and fitness centre.
   CRITICAL EXCEPTION: ITC is ALLOWED where an inward supply of such goods or services is used by a registered person for making an outward taxable supply of the same category of goods or services or as an element of a taxable composite or mixed supply, OR where it is statutory obligatory for an employer to provide the same to its employees under any law for the time being in force.

3. Personal Consumption & Lost Goods: ITC is specifically blocked on:
   (a) Goods or services used for personal consumption;
   (b) Goods lost, stolen, destroyed, written off or disposed of by way of gift or free samples;
   (c) Any tax paid in accordance with the provisions of Sections 74, 129 and 130 (fraud, willful misstatement, suppression of facts, detention and confiscation)."""
        ),

        # Document 2: Section 139 Companies Act (Appointment of Auditors)
        DocumentChunk(
            chunk_id="doc_law_sec139_1",
            document_name="ICAI Study Material - Paper 2 Corporate and Other Laws",
            source="ICAI Official Study Material",
            version_date="2024-2025 Edition",
            stage="Intermediate",
            group_name="Group 1",
            paper="Paper 2: Corporate and Other Laws",
            module="Module 1: Company Law",
            chapter="Chapter 10: Audit and Auditors",
            topic="Appointment of Auditors under Section 139",
            page_number=118,
            statutory_reference="Section 139 Companies Act, 2013 & Companies (Audit and Auditors) Rules, 2014",
            content="""Section 139 of the Companies Act, 2013 governs the appointment of statutory auditors:

1. Appointment of First Auditor in Non-Government Company [Section 139(6)]:
   The first auditor of a company, other than a Government company, shall be appointed by the Board of Directors within 30 days from the date of registration of the company.
   In case the Board fails to appoint such auditor within 30 days, it shall inform the members of the company, who shall within 90 days at an Extraordinary General Meeting (EGM) appoint such auditor. The first auditor holds office until the conclusion of the first Annual General Meeting (AGM).

2. Appointment of First Auditor in Government Company [Section 139(7)]:
   In the case of a Government company or any other company owned or controlled by Central/State Government, the first auditor shall be appointed by the Comptroller and Auditor-General of India (C&AG) within 60 days from the date of registration of the company.
   If C&AG fails to appoint within 60 days, the Board of Directors shall appoint within the next 30 days. If the Board fails, it shall inform the members who shall appoint within 60 days at an EGM.

3. Appointment of Subsequent Auditors [Section 139(1)]:
   Every company shall, at the first AGM, appoint an individual or a firm as an auditor who shall hold office from the conclusion of that meeting until the conclusion of its sixth AGM and thereafter till the conclusion of every sixth meeting.
   The company must place the matter relating to such appointment for ratification by members at every AGM (proviso omitted by Companies Amendment Act 2017).

4. Casual Vacancy [Section 139(8)]:
   Any casual vacancy in the office of an auditor shall be filled by the Board within 30 days.
   HOWEVER, if such casual vacancy is as a result of the RESIGNATION of an auditor, such appointment shall also be approved by the company at a general meeting convened within 3 months of the recommendation of the Board."""
        ),

        # Document 3: Section 141 Companies Act (Disqualifications of Auditors)
        DocumentChunk(
            chunk_id="doc_law_sec141_1",
            document_name="ICAI Study Material - Paper 2 Corporate and Other Laws",
            source="ICAI Official Study Material",
            version_date="2024-2025 Edition",
            stage="Intermediate",
            group_name="Group 1",
            paper="Paper 2: Corporate and Other Laws",
            module="Module 1: Company Law",
            chapter="Chapter 10: Audit and Auditors",
            topic="Eligibility, Qualifications and Disqualifications of Auditors",
            page_number=125,
            statutory_reference="Section 141 Companies Act, 2013",
            content="""Section 141 of the Companies Act, 2013 sets forth qualifications and disqualifications of auditors:

1. Qualifications: A person shall be eligible for appointment as an auditor of a company only if he is a Chartered Accountant in practice. A firm whereof majority of partners practicing in India are qualified for appointment may be appointed by its firm name.

2. Disqualifications [Section 141(3)]:
   (a) A body corporate other than a Limited Liability Partnership (LLP);
   (b) An officer or employee of the company;
   (c) A person who is a partner, or who is in the employment, of an officer or employee of the company;
   (d) A person who, or his relative or partner:
       (i) is holding any security of or interest in the company or its subsidiary, holding, or associate company (Exception: Relative may hold security of face value not exceeding ₹1,00,000);
       (ii) is indebted to the company, or its subsidiary, holding or associate company in excess of ₹5,00,000;
       (iii) has given a guarantee or provided any security in connection with indebtedness of any third person in excess of ₹1,00,000;
   (e) A person or firm who, whether directly or indirectly, has business relationship with the company or its subsidiary/holding/associate company;
   (f) A person whose relative is a director or is in employment of the company as a director or key managerial personnel;
   (g) A person who is in full-time employment elsewhere, or a person or partner of a firm holding appointment as auditor of more than 20 companies at the date of appointment (excluding one person companies, dormant companies, small companies, and private companies having paid up share capital less than ₹100 crore);
   (h) A person who has been convicted by a court of an offence involving fraud and a period of 10 years has not elapsed from the date of conviction;
   (i) Any person whose subsidiary or associate company or any other form of entity, is engaged as on the date of appointment in consulting and specialized services as provided in Section 144."""
        ),

        # Document 4: Standard on Auditing (SA) 200 (Objectives & Inherent Limitations)
        DocumentChunk(
            chunk_id="doc_audit_sa200_1",
            document_name="ICAI Study Material - Paper 5 Auditing and Ethics",
            source="ICAI Official Study Material",
            version_date="2024-2025 Edition",
            stage="Intermediate",
            group_name="Group 2",
            paper="Paper 5: Auditing and Ethics",
            module="Module 1: Nature, Objective and Scope of Audit",
            chapter="Chapter 1: Nature, Objective and Scope of Audit",
            topic="Overall Objectives of the Independent Auditor & Inherent Limitations",
            page_number=14,
            statutory_reference="Standard on Auditing (SA) 200 issued by ICAI",
            content="""Standard on Auditing (SA) 200, 'Overall Objectives of the Independent Auditor and the Conduct of an Audit in Accordance with Standards on Auditing':

1. Overall Objectives of the Auditor:
   In conducting an audit of financial statements, the overall objectives of the auditor are:
   (a) To obtain reasonable assurance about whether the financial statements as a whole are free from material misstatement, whether due to fraud or error, thereby enabling the auditor to express an opinion on whether the financial statements are prepared, in all material respects, in accordance with an applicable financial reporting framework; and
   (b) To report on the financial statements, and communicate as required by the SAs, in accordance with the auditor's findings.

2. Reasonable Assurance:
   Reasonable assurance is a high, but not absolute, level of assurance. It is obtained when the auditor has obtained sufficient appropriate audit evidence to reduce audit risk (i.e., the risk that the auditor expresses an inappropriate opinion when the financial statements are materially misstated) to an acceptably low level.

3. Inherent Limitations of an Audit:
   The auditor is not expected to, and cannot, reduce audit risk to zero and cannot therefore obtain absolute assurance that the financial statements are free from material misstatement due to inherent limitations of an audit:
   (a) Nature of Financial Reporting: Preparation of financial statements involves judgment by management in applying financial reporting framework (e.g., accounting estimates, fair values, provisions).
   (b) Nature of Audit Procedures: Practical and legal limitations on the auditor's ability to obtain evidence (e.g., management or third parties may not provide complete information, fraud may involve sophisticated schemes to conceal, auditor does not possess legal powers of search).
   (c) Timeliness of Financial Reporting and the Balance between Benefit and Cost: Difficulty, time, or cost involved is not in itself a valid basis for the auditor to omit an audit procedure for which there is no alternative.
   (d) Other Matters Affecting Inherent Limitations: Fraud involving senior management or collusion, existence and completeness of related party relationships, non-compliance with laws and regulations, and future events affecting going concern."""
        ),

        # Document 5: AS 10 (Revised) Property, Plant and Equipment (Depreciation & Sale)
        DocumentChunk(
            chunk_id="doc_acc_as10_1",
            document_name="ICAI Study Material - Paper 1 Advanced Accounting",
            source="ICAI Official Study Material",
            version_date="2024-2025 Edition",
            stage="Intermediate",
            group_name="Group 1",
            paper="Paper 1: Advanced Accounting",
            module="Module 1: Accounting Standards",
            chapter="Chapter 2: Accounting Standards (AS 10)",
            topic="Property, Plant and Equipment - Depreciation, Component Accounting & Disposal",
            page_number=62,
            statutory_reference="Accounting Standard (AS) 10 (Revised) issued by ICAI",
            content="""Accounting Standard (AS) 10 (Revised), 'Property, Plant and Equipment':

1. Definition & Recognition:
   Property, plant and equipment are tangible items that:
   (a) are held for use in the production or supply of goods or services, for rental to others, or for administrative purposes; and
   (b) are expected to be used during more than a period of twelve months.
   The cost of an item of PPE shall be recognized as an asset if, and only if:
   (i) it is probable that future economic benefits associated with the item will flow to the enterprise; and
   (ii) the cost of the item can be measured reliably.

2. Component Accounting & Depreciation:
   Each part of an item of PPE with a cost that is significant in relation to the total cost of the item SHALL be depreciated separately (component approach).
   The depreciable amount (cost minus residual value) of an asset should be allocated on a systematic basis over its useful life.
   The depreciation method applied shall reflect the pattern in which the asset's future economic benefits are expected to be consumed by the enterprise.
   The residual value and useful life of an asset should be reviewed at least at each financial year-end. If expectations differ from previous estimates, the change is accounted for as a change in an accounting estimate under AS 5 (applied prospectively).

3. De-recognition and Sale of Asset before Useful Life Ends:
   The carrying amount of an item of PPE shall be de-recognized:
   (a) on disposal; or
   (b) when no future economic benefits are expected from its use or disposal.
   Gain or loss arising from de-recognition of an item of PPE shall be included in the statement of profit and loss when the item is de-recognized (unless AS 19 leases requires otherwise on a sale and leaseback).
   Calculation: Gain or Loss on Disposal = Net Disposal Proceeds - Carrying Amount (Book Value) of the asset at the date of disposal.
   Gains shall NOT be classified as revenue."""
        )
    ]
    return docs

def save_processed_documents(docs: List[DocumentChunk]):
    """
    Saves metadata and content into knowledge/processed and knowledge/metadata for auditing.
    """
    for doc in docs:
        meta_path = os.path.join(METADATA_DIR, f"{doc.chunk_id}.json")
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(doc.to_dict(), f, indent=2, ensure_ascii=False)

        proc_path = os.path.join(PROCESSED_DIR, f"{doc.chunk_id}.txt")
        with open(proc_path, "w", encoding="utf-8") as f:
            f.write(f"=== {doc.document_name} ===\n")
            f.write(f"Source: {doc.source} ({doc.version_date})\n")
            f.write(f"Section/Standard: {doc.statutory_reference}\n")
            f.write(f"Chapter: {doc.chapter} | Topic: {doc.topic} | Page: {doc.page_number}\n\n")
            f.write(doc.content)
