import React from 'react';

/**
 * JourneyView Component
 * Visual Roadmap of the complete ICAI Chartered Accountancy journey:
 * Foundation -> Intermediate -> Articleship -> Final -> ACA.
 */
export default function JourneyView({ onNavigate }) {
  const stages = [
    {
      step: '01',
      title: 'CA Foundation',
      hindi: 'नींव',
      status: 'completed',
      duration: '4 Months Study Period',
      papers: [
        'Paper 1: Accounting (100 Marks)',
        'Paper 2: Business Laws (100 Marks)',
        'Paper 3: Quantitative Aptitude (100 Marks)',
        'Paper 4: Business Economics (100 Marks)',
      ],
      desc: 'Entry level qualifying exam for 10+2 students.',
    },
    {
      step: '02',
      title: 'CA Intermediate',
      hindi: 'मध्यवर्ती',
      status: 'active', // Sister's current stage!
      duration: '8 Months Study Period',
      papers: [
        'Group 1: Advanced Accounting, Corporate Laws, Taxation',
        'Group 2: Cost & Management Accounting, Auditing & Ethics, Financial Mgmt & Strategic Mgmt',
      ],
      desc: 'Current stage. Passing both groups qualifies you for 2-year practical articleship training.',
      isCurrent: true,
    },
    {
      step: '03',
      title: 'Practical Training (Articleship)',
      hindi: 'व्यावहारिक प्रशिक्षण',
      status: 'upcoming',
      duration: '2 Years Full-Time Mandatory',
      papers: [
        'ICITSS (Orientation + IT Training) before commencement',
        'AICITSS (Advanced IT + GMCS) during the 2nd year',
      ],
      desc: 'Hands-on practical auditing, taxation, and advisory training under a practicing Chartered Accountant.',
    },
    {
      step: '04',
      title: 'CA Final & Self-Paced Modules',
      hindi: 'अंतिम चरण',
      status: 'upcoming',
      duration: 'Final Examination',
      papers: [
        'Group 1: Financial Reporting (FR), Advanced Financial Management (AFM), Advanced Auditing',
        'Group 2: Direct Tax & International Tax, Indirect Tax Laws (IDT), Integrated Business Solutions',
        'Self-Paced Online Modules (SPOM Set A, B, C, D)',
      ],
      desc: 'The pinnacle examination qualifying you for the prestigious ICAI fellowship and CA designation.',
    },
    {
      step: '05',
      title: 'Fellow Chartered Accountant (ACA / FCA)',
      hindi: 'चार्टर्ड एकाउंटेंट',
      status: 'destination',
      duration: 'Lifelong Distinction',
      papers: ['ICAI Membership Induction', 'Certificate of Practice (COP) or Industry Leadership'],
      desc: 'Globally recognized professional credential empowering you in global finance, practice, and governance.',
    },
  ];

  return (
    <div className="view-container journey-view">
      <div className="view-header">
        <div>
          <h2>The CA Professional Journey</h2>
          <p className="view-subtitle">
            Every step forward builds your mastery as a future Chartered Accountant.
          </p>
        </div>
      </div>

      <div className="journey-timeline">
        {stages.map((stage, idx) => (
          <div
            key={idx}
            className={`journey-card ${stage.isCurrent ? 'current-stage' : ''} ${stage.status}`}
          >
            <div className="journey-card-header">
              <div className="step-circle">{stage.step}</div>
              <div className="journey-title-group">
                <div className="journey-title-row">
                  <h3>{stage.title}</h3>
                  <span className="journey-hindi">{stage.hindi}</span>
                  {stage.isCurrent && (
                    <span className="current-badge">📍 Current Preparation Stage</span>
                  )}
                </div>
                <span className="journey-duration">{stage.duration}</span>
              </div>
            </div>

            <p className="journey-desc">{stage.desc}</p>

            <div className="journey-papers-box">
              <span className="papers-heading">Key Papers & Milestones:</span>
              <ul className="papers-list">
                {stage.papers.map((p, i) => (
                  <li key={i}>{p}</li>
                ))}
              </ul>
            </div>

            {stage.isCurrent && (
              <div className="journey-cta-row">
                <button
                  className="primary-button"
                  onClick={() => onNavigate && onNavigate('study')}
                >
                  Continue Studying Intermediate ➜
                </button>
                <button
                  className="secondary-button"
                  onClick={() => onNavigate && onNavigate('companion')}
                >
                  Ask Sathi for Advice
                </button>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
