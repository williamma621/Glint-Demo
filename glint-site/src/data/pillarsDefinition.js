export const PILLARS = [
  { key: 'moralityValues', label: 'Morality Values', group: 'Hard Basics' },
  { key: 'finance', label: 'Finance', group: 'Hard Basics' },
  { key: 'family', label: 'Family', group: 'Hard Basics' },
  { key: 'career', label: 'Career', group: 'Hard Basics' },
  { key: 'religion', label: 'Religion', group: 'Hard Basics' },
  { key: 'lifestyle', label: 'Lifestyle', group: 'Hard Basics' },
  { key: 'socialBattery', label: 'Social Battery', group: 'Hard Basics' },
  { key: 'attachment', label: 'Attachment', group: 'Soft Dynamics' },
  { key: 'loveLanguages', label: 'Love Languages', group: 'Soft Dynamics' },
  { key: 'conflictStyle', label: 'Conflict Style', group: 'Soft Dynamics' },
  { key: 'intellect', label: 'Intellect', group: 'Soft Dynamics' },
  { key: 'eq', label: 'EQ', group: 'Soft Dynamics' },
  { key: 'humor', label: 'Humor', group: 'Soft Dynamics' },
  { key: 'riskTolerance', label: 'Risk Tolerance', group: 'Soft Dynamics' },
]

export const TYPE_PILLARS = new Set(PILLARS.map((pillar) => pillar.key))

export const STYLE_TAG_DEFINITIONS = {
  scale: {
    label: 'Preference Strength (0-10)',
    meaning: {
      0: 'Strongly avoid / opposite preference.',
      10: 'Core preference / strongly seek.',
      mid: '1-3 = mild, 4-6 = balanced or situational, 7-9 = strong preference.',
    },
  },
  rules: [
    'Use short, human tags (2-5 words).',
    'Prefer observable, concrete language.',
    'Keep tags mutually exclusive when possible.',
  ],
}

export const INITIAL_PROFILE = PILLARS.reduce((acc, pillar) => {
  acc[pillar.key] = { type: 'Unknown', confidence: 0 }
  return acc
}, {})
