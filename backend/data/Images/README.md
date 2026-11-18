# AIKTC Chatbot Image Directory

This directory contains the normalized image files used by the AIKTC Receptionist Chatbot. 
Images are referenced by the Knowledge Base JSON files located under `backend/data/kb/` and served by the frontend.

## Directory Structure

All files and subfolders are structured hierarchically using lowercase names and underscores. Titles (Dr., Prof., Ar., etc.) have been removed from file and folder names.

```
frontend/public/images/
├── engineering/
│   ├── aiml/
│   │   └── salim_shaikh.avif             # Dr. Salim Shaikh (HOD)
│   ├── bscit/
│   │   └── tabrez_khan.avif              # Prof. Tabrez Khan (Coordinator)
│   ├── civil/
│   │   └── fauwaz_parkar.avif            # Dr. Fauwaz Parkar (HOD)
│   ├── co/
│   │   └── tabrez_khan.avif              # Prof. Tabrez Khan (HOD)
│   ├── ds/
│   │   └── zeeshan_zainuddin_khan.avif   # Prof. Zeeshan Zainuddin Khan (Faculty)
│   ├── ece/
│   │   └── afzal_nehal_ahmed_shaikh.avif # Dr. Shaikh Afzal N. A. (HOD)
│   ├── ecs/
│   │   └── bandanawaz_kotiyal.avif       # Prof. Bandanawaz Kotiyal (HOD)
│   └── mechanical/
│       └── zakir_ansari.avif             # Prof. Ansari Zakir Sajid (Faculty)
├── architecture/
│   └── barch/
│       └── raj_mhatre.jpg                # Prof. Raj Mhatre (Dean)
└── pharmacy/
    ├── bpharm/
    │   └── shariq_syed.jpg               # Dr. Shariq Syed (Dean)
    ├── dpharm/
    │   └── abusufyan_shaikh.png          # Dr. Abusufyan Shaikh (HOD)
    └── mpharm/
        └── anwar_baig.jpg                # Dr. Mirza Anwar Baig (Faculty/HOD)
```

## Guidelines for Adding Images
1. Use **lowercase** letters, **underscores** instead of spaces, and remove honorific titles (Dr., Prof., Ar.) from filenames.
2. Standardize on web-friendly formats: `.avif`, `.jpg`, `.png`, or `.webp`.
3. Update both the per-department JSON files in `backend/data/kb/` and the legacy flat JSON files (`engineering.json`, `pharmacy.json`, `architecture.json`) when adding or modifying images.
