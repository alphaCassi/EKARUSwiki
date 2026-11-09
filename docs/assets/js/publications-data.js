/* EKARUS publications, shown on pages/publications.html (with filters and sorting).

   To add a publication, copy one { ... } block and fill it in:
     title    exact title
     authors  list of "Surname, Initials" in the paper's order
     year     publication year (number)
     venue    journal or conference, volume, page / paper number
     type     "paper" (refereed), "proceedings", "poster" or "talk"
     doi      DOI without https://doi.org/ ("" if none yet)
     url      link to use when there's no DOI ("" otherwise)
     related  true if the work is not about EKARUS itself but uses or describes it
   Sources used: SPIE Astronomical Telescopes + Instrumentation 2026 programme, HAL, Zenodo,
   authors' publication pages. Check NASA ADS for new items: https://ui.adsabs.harvard.edu */
window.EKARUS_PUBLICATIONS = [
  {
    title: "EKARUS at the Asiago Observatory: towards the first light of a new XAO R&D platform",
    authors: ["Héritier, C. T.", "Greggio, D.", "Alagao, M. A.", "Asghar, M.", "Ballone, A.", "Balestra, A.",
      "Barr, D.", "Baruffolo, A.", "Battaini, F.", "Bonaglia, M.", "Bournane, M. Y.", "Busoni, L.", "Carolo, E.",
      "Cerpelloni, P.", "Cetre, S.", "Chambouleyron, V.", "Costa, E.", "Cortese, L.", "D'Ambrogio, M.",
      "Di Antonio, I.", "Di Filippo, S.", "Di Francesco, B.", "Di Rico, G.", "Di Rosa, S.", "Diretto, D.",
      "Esposito, S.", "Farinato, J.", "Fétick, R.", "Ferraiuolo, P.", "Forte, T.", "Frigo, A.", "Fusco, T.",
      "Lampitelli, S.", "Lapucci, T.", "Lessio, L.", "Lorenzetto, A.", "Machado, T.", "Magniez, A.",
      "Marafatto, L.", "Menessini, M.", "Merli, L.", "Morris, T.", "Mosele, M.", "Muslimov, E.", "Neichel, B.",
      "Oyarzún, F.", "Rebrysh, O.", "Rodeghiero, G.", "Sacquegna, S.", "Sauvage, J.-F.", "Selvestrel, D.",
      "Striffling, A.", "Tomasella, L.", "Traverso, L.", "Umbriaco, G.", "Van Gaalen, R.", "Vassallo, D."],
    year: 2026,
    venue: "Proc. SPIE, Adaptive Optics Systems X, Astronomical Telescopes + Instrumentation, Copenhagen",
    type: "proceedings",
    doi: "10.1117/12.3102925",
    url: "",
    related: false
  },
  {
    title: "EKARUS at Asiago Observatory: optomechanical design and AIT procedures of the visible stage",
    authors: ["D'Ambrogio, M.", "Greggio, D.", "Héritier, C. T.", "Alagao, M. A.", "Bournane, M. Y.", "Carolo, E.",
      "Ballone, A.", "Di Rosa, S.", "Di Antonio, I.", "Muslimov, E.", "Magniez, A.", "Menessini, M.",
      "Ferraiuolo, P."],
    year: 2026,
    venue: "Proc. SPIE, Astronomical Telescopes + Instrumentation, Copenhagen",
    type: "proceedings",
    doi: "10.1117/12.3102910",
    url: "",
    related: false
  },
  {
    title: "EKARUS at Asiago Observatory: simulations and performance analysis of a modular XAO system",
    authors: ["Menessini, M.", "Busoni, L.", "Héritier, C. T.", "Chambouleyron, V."],
    authorsIncomplete: true,
    year: 2026,
    venue: "Proc. SPIE, Adaptive Optics Systems X, paper 14150-305, Copenhagen",
    type: "proceedings",
    doi: "",
    url: "https://spie.org/astronomical-telescopes-instrumentation/presentation/EKARUS-at-Asiago-Observatory--simulations-and-performance-analysis-of/14150-305",
    related: false
  },
  {
    title: "EKARUS at Asiago Observatory: design and implementation of the instrument control software",
    authors: ["Costa, E."],
    authorsIncomplete: true,
    year: 2026,
    venue: "Proc. SPIE, Software and Cyberinfrastructure for Astronomy IX, paper 14155-187, Copenhagen",
    type: "proceedings",
    doi: "",
    url: "https://spie.org/astronomical-telescopes-instrumentation/presentation/EKARUS-at-Asiago-Observatory---Design-and-Implementation-of/14155-187",
    related: false
  },
  {
    title: "EKARUS: The future of PAPYRUS at the Cima Ekar Telescope",
    authors: ["Héritier, C. T.", "Greggio, D.", "Rebrysh, O.", "Alagao, M. A.", "Ballone, A.", "Chambouleyron, V.",
      "Menessini, M.", "Busoni, L.", "Carolo, E.", "D'Ambrogio, M.", "Di Antonio, I.", "Barr, D.", "Cetre, S.",
      "Bonaglia, M.", "Bournane, M. Y.", "Muslimov, E.", "Di Rico, G.", "Esposito, S.", "Farinato, J.",
      "Lessio, L.", "Machado, T.", "Fétick, R.", "Fusco, T.", "Magniez, A.", "Morris, T.", "Neichel, B.",
      "Di Francesco, B.", "Sacquegna, S.", "Cerpelloni, P.", "Costa, E.", "Merli, L.", "Di Filippo, S.",
      "Umbriaco, G.", "Rodeghiero, G.", "Van Gaalen, R.", "Sauvage, J.-F.", "Striffling, A.", "Tomasella, L."],
    year: 2025,
    venue: "Adaptive Optics for Extremely Large Telescopes 8 (AO4ELT8), Viña del Mar",
    type: "poster",
    doi: "10.5281/zenodo.21107775",
    url: "",
    related: false
  },
  {
    title: "EKARUS: A New Adaptive Optics R&D Platform at the Asiago Observatory",
    authors: ["Greggio, D."],
    year: 2026,
    venue: "Seminar, INAF – Osservatorio Astronomico di Padova, 19 February 2026",
    type: "talk",
    doi: "",
    url: "https://indico.dfa.unipd.it/event/1719/",
    related: false
  },
  {
    title: "Cassiopee: Defining the next-generation deformable mirror and high-speed SWIR camera for adaptive optics applications",
    authors: ["Neichel, B.", "Fusco, T.", "Oyarzún, F.", "Chambouleyron, V.", "Sauvage, J.-F."],
    authorsIncomplete: true,
    year: 2026,
    venue: "SPIE Astronomical Telescopes + Instrumentation, Copenhagen (on-sky validation planned on EKARUS)",
    type: "proceedings",
    doi: "10.48550/arXiv.2608.24526",
    url: "",
    related: true
  },
  {
    title: "The observing with adaptive optics school: training the next generation of AO scientists and engineers",
    authors: ["Neichel, B.", "Busoni, L.", "Chambouleyron, V.", "Alagao, M. A.", "Rebrysh, O."],
    authorsIncomplete: true,
    year: 2026,
    venue: "Proc. SPIE, Astronomical Telescopes + Instrumentation, Copenhagen",
    type: "proceedings",
    doi: "10.1117/12.3101465",
    url: "",
    related: true
  }
];
