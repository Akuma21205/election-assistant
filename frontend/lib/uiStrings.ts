// All English UI strings — single source of truth for Google Translate
export const UI_STRINGS = {
  // ── App branding ──────────────────────────────────────
  appName: "VoteGuide",
  appSubtitle: "AI Election Assistant",
  modeStandardShort: "Standard",
  modeSimplifiedShort: "Simplified",

  // ── Sync status ───────────────────────────────────────
  syncedLabel: "Saved",
  syncingLabel: "Syncing...",

  // ── Input area ────────────────────────────────────────
  inputPlaceholder: "Ask about elections, voting, candidates...",
  disclaimer: "VoteGuide provides general civic info — not legal advice.",
  pressEnter: "Enter",
  pressEnterLabel: "to send",

  // ── Empty state ───────────────────────────────────────
  emptyTitle: "Your Election Guide",
  emptyDesc:
    "Ask about voting, elections, and civic participation across India, USA & UK. Non-partisan, accurate, and personalized.",

  // ── Feature chips ─────────────────────────────────────
  votingJourneyChip: "Voting Journey",
  eligibilityChip: "Eligibility Check",
  settingsChip: "Settings",

  // ── Suggested questions ───────────────────────────────
  sq1: "How do I register to vote in India?",
  sq2: "What is the Electoral College?",
  sq3: "Am I eligible to vote?",
  sq4: "Show me election timelines",
  sq5: "How does ranked-choice voting work?",
  sq6: "What documents do I need to vote?",

  // ── Tooltips / aria-labels ────────────────────────────
  votingJourneyTooltip: "Voting Journey",
  eligibilityTooltip: "Eligibility Check",
  settingsTooltip: "Settings",
  voiceInputTooltip: "Voice input",
  sendMsgLabel: "Send message",

  // ── Settings modal ────────────────────────────────────
  settingsTitle: "Settings",
  languageLabel: "Language",
  modeLabel: "Explanation Mode",
  profileLabel: "Your Profile (for personalized guidance)",
  standardModeLabel: "Standard",
  standardModeDesc: "Detailed & comprehensive",
  simplifiedModeLabel: "Simplified",
  simplifiedModeDesc: "Explain like I'm 10",
  saveClose: "Save & Close",
  selectCountry: "Select your country",
  countryIndia: "India",
  countryUSA: "United States",
  countryUK: "United Kingdom",
  agePlaceholder: "Your age",
  firstTimeVoter: "First-time voter",

  // ── Eligibility checker ───────────────────────────────
  eligibilityTitle: "Eligibility Checker",
  eligibilityDesc:
    "Check if you meet the basic requirements to vote in your country.",
  citizenLabel: "I am a citizen of this country",
  residentLabel: "I am a current resident",
  checkBtn: "Check Eligibility",
  checkingBtn: "Checking...",
  eligibleTitle: "You're Eligible!",
  notEligibleTitle: "Not Yet Eligible",
  nextStepsLabel: "Next Steps:",
  serverConnectionError: "Could not connect to the server.",

  // ── Voting Journey modal ──────────────────────────────
  votingJourneyTitle: "Your Voting Journey",
  votingJourneyDesc:
    "Follow these steps to complete your voting journey. Click any step to learn more.",
  stepLabel: "Step",

  // ── Voting steps ──────────────────────────────────────
  step1Title: "Register",
  step1Desc: "Sign up on your country's voter portal",
  step2Title: "Get ID",
  step2Desc: "Obtain your voter ID or required documents",
  step3Title: "Verify",
  step3Desc: "Check your name on the electoral roll",
  step4Title: "Find Booth",
  step4Desc: "Locate your assigned polling station",
  step5Title: "Vote!",
  step5Desc: "Cast your vote on Election Day",
  step6Title: "Results",
  step6Desc: "Wait for official results announcement",

  // ── Errors ────────────────────────────────────────────
  voiceNotSupported: "Voice input is not supported in this browser.",
  rateLimitError: "Rate limit exceeded — please wait a moment.",
  timeoutError: "Request timed out — please try again.",
  serverError: "Failed to reach the server.",

  // ── Translation loading ───────────────────────────────
  translatingLabel: "Translating interface...",

  // ── Speech-to-Text ────────────────────────────────────────────────
  recordingLabel: "Recording... tap to stop",
  processingAudioLabel: "Processing speech...",
  micPermissionError: "Microphone permission denied.",
  sttError: "Could not process audio. Please try again.",

  // ── Text-to-Speech ────────────────────────────────────────────────
  autoSpeakOn: "Auto-speak on",
  autoSpeakOff: "Auto-speak off",
  speakMsgLabel: "Read aloud",
  stopSpeakLabel: "Stop speaking",
  ttsError: "Could not play audio.",
} as const;

export type UIStrings = Record<keyof typeof UI_STRINGS, string>;
