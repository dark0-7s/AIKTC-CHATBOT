/**
 * Quick chips data — multilingual.
 * Each chip has labels in en/hi/hinglish and a fixed message (always English,
 * since the backend processes English queries regardless of UI language).
 */
export const CHIPS = [
  {
    label: { en: "Predict my chances", hi: "मेरी संभावना जानें", hinglish: "Mera chance check karo" },
    message: "I want to check my admission chances",
    badge: "prediction"
  },
  {
    label: { en: "Latest cutoffs", hi: "नवीनतम कटऑफ", hinglish: "Latest cutoff dikhao" },
    message: "Show me the latest MHT-CET cutoff table for CSE",
    badge: "table"
  },
  {
    label: { en: "Faculty directory", hi: "संकाय सूची", hinglish: "Faculty list dikhao" },
    message: "Show me the faculty of the CSE department",
    badge: "faculty"
  },
  {
    label: { en: "Fee structure", hi: "शुल्क विवरण", hinglish: "Fee kitni hai?" },
    message: "What is the annual fee for engineering at AIKTC?",
    badge: "text"
  },
  {
    label: { en: "Placements 2024", hi: "प्लेसमेंट 2024", hinglish: "Placements 2024" },
    message: "Tell me about placements at AIKTC for 2024",
    badge: "text"
  },
  {
    label: { en: "Hostel info", hi: "हॉस्टल जानकारी", hinglish: "Hostel ke baare mein batao" },
    message: "Tell me about hostel facilities and fees",
    badge: "text"
  },
  {
    label: { en: "Director info", hi: "निदेशक जानकारी", hinglish: "Director kaun hai?" },
    message: "Who is the director of AIKTC?",
    badge: "media_card"
  },
  {
    label: { en: "Admission process", hi: "प्रवेश प्रक्रिया", hinglish: "Admission kaise hota hai?" },
    message: "How do I apply for admission to AIKTC?",
    badge: "steps"
  },
  {
    label: { en: "Contact admissions", hi: "प्रवेश कार्यालय संपर्क", hinglish: "Admissions se baat karo" },
    message: "I want to contact the AIKTC admissions office",
    badge: "contact"
  },
  {
    label: { en: "Labs — CSE", hi: "लैब — CSE", hinglish: "Labs — CSE" },
    message: "Show me the labs for Computer Science Engineering",
    badge: "list"
  }
];
