/**
 * Translations for PyroLens — FR and EN.
 */

export const TRANSLATIONS = {
  brand: {
    title: { fr: "PyroLens", en: "PyroLens" },
    subtitle: { fr: "Feux actifs · données NASA FIRMS", en: "Active fires · NASA FIRMS data" },
  },
  search: {
    placeholder: { fr: "Rechercher un lieu…", en: "Search a location…" },
    label: { fr: "Rechercher un lieu", en: "Search a location" },
    go: { fr: "Aller", en: "Go" },
  },
  searchBtn: { fr: "Rechercher un lieu", en: "Search a location" },
  announcements: { fr: "Annonces", en: "Announcements" },
  contact: { fr: "Contact", en: "Contact" },
  menu: { fr: "Ouvrir le menu principal", en: "Open main menu" },

  toast: {
    searching: { fr: "Recherche…", en: "Searching…" },
    located: { fr: "Lieu localisé", en: "Location found" },
    notFound: { fr: "Lieu introuvable : essayez un nom de ville ou de pays", en: "Location not found: try a city or country name" },
    announce: { fr: "Données hotspots : VIIRS 375 m – NASA FIRMS (dernières 24 h)", en: "Hotspot data: VIIRS 375 m – NASA FIRMS (last 24 h)" },
  },

  nav: {
    map: { fr: "Carte", en: "Map" },
    overview: { fr: "Aperçu", en: "Overview" },
    calendar: { fr: "Calendrier", en: "Calendar" },
    jobs: { fr: "Jobs", en: "Jobs" },
    quality: { fr: "Qualité", en: "Quality" },
    risk: { fr: "Risque", en: "Risk" },
  },

  overview: {
    title: { fr: "Aperçu des observations", en: "Observation overview" },
    subtitle: { fr: "Résumé synthétique du pipeline de traitement. Données mockées si les artefacts publics ne sont pas disponibles.", en: "Synthetic summary of the processing pipeline. Mock data if public artifacts are unavailable." },
    loading: { fr: "Chargement des artefacts du pipeline…", en: "Loading pipeline artifacts…" },
    satellite: { fr: "Satellite", en: "Satellite" },
    startDate: { fr: "Date début", en: "Start date" },
    endDate: { fr: "Date fin", en: "End date" },
    overviewMap: { fr: "Carte d'aperçu (voir mode Carte pour la vue interactive)", en: "Overview map (see Map mode for interactive view)" },
    zoneCovered: { fr: "Zone couverte :", en: "Covered area:" },
    gridRisk: { fr: "Grille risque", en: "Risk grid" },
    cards: {
      period: { fr: "Période", en: "Period" },
      satellites: { fr: "Satellites", en: "Satellites" },
      pilotSites: { fr: "Sites pilotes", en: "Pilot sites" },
      obsStates: { fr: "États observabilité", en: "Observability states" },
      pipeline: { fr: "Pipeline", en: "Pipeline" },
      unitPeriod: { fr: "données MODIS/VIIRS", en: "MODIS/VIIRS data" },
      unitSatellites: { fr: "MODIS Terra, Aqua, VIIRS", en: "MODIS Terra, Aqua, VIIRS" },
      unitSites: { fr: "Cameroun, etc.", en: "Cameroon, etc." },
      unitObs: { fr: "vert / jaune / orange / rouge", en: "green / yellow / orange / red" },
      unitPipeline: { fr: "version", en: "version" },
    },
    satellitesOpt: {
      viirs: { fr: "VIIRS SNPP", en: "VIIRS SNPP" },
      terra: { fr: "MODIS Terra", en: "MODIS Terra" },
      aqua: { fr: "MODIS Aqua", en: "MODIS Aqua" },
    },
  },

  calendar: {
    title: { fr: "Calendrier des feux", en: "Fire calendar" },
    subtitle: { fr: "Données réelles du pipeline PyroLens (2013–2020) : cellules en divergence inter-capteurs par jour.", en: "Real data from the PyroLens pipeline (2013–2020): inter-sensor divergence cells per day." },
    apiError: { fr: "API indisponible :", en: "API unavailable:" },
    loading: { fr: "Chargement du calendrier…", en: "Loading calendar…" },
    legend: { fr: "Légende", en: "Legend" },
    legendNote: { fr: "nombre = cellules en divergence capteurs ce jour-là · niveaux = terciles des jours non nuls", en: "count = inter-sensor divergence cells this day · levels = terciles of non-zero days" },
    daysCovered: { fr: "jours couverts", en: "days covered" },
    months: {
      fr: ["Janvier","Février","Mars","Avril","Mai","Juin","Juillet","Août","Septembre","Octobre","Novembre","Décembre"],
      en: ["January","February","March","April","May","June","July","August","September","October","November","December"],
    },
    dow: { fr: ["Lun","Mar","Mer","Jeu","Ven","Sam","Dim"], en: ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"] },
  },

  jobs: {
    title: { fr: "Jobs", en: "Jobs" },
    subtitle: { fr: "Tâches réelles de l'API PyroLens : harmonisation, analyse de zone FIRMS, historique archive, entraînement du modèle de risque.", en: "Real tasks from the PyroLens API: harmonization, FIRMS zone analysis, archive history, risk model training." },
    loading: { fr: "Chargement…", en: "Loading…" },
    apiError: { fr: "API indisponible :", en: "API unavailable:" },
    none: { fr: "Aucun job pour le moment — lance une analyse de zone ou une prédiction depuis la carte.", en: "No jobs yet — start a zone analysis or prediction from the map." },
    back: { fr: "← Retour aux jobs", en: "← Back to jobs" },
    headers: {
      jobId: { fr: "Job ID", en: "Job ID" },
      type: { fr: "Type", en: "Type" },
      status: { fr: "Statut", en: "Status" },
      progress: { fr: "Progression", en: "Progress" },
      created: { fr: "Créé le", en: "Created" },
    },
    kind: {
      harmonization: { fr: "Harmonisation", en: "Harmonization" },
      firms_analyze: { fr: "Analyse zone FIRMS", en: "FIRMS zone analysis" },
      firms_history: { fr: "Historique archive", en: "Archive history" },
      predict: { fr: "Prédiction risque", en: "Risk prediction" },
    },
    status: {
      pending: { fr: "En attente", en: "Pending" },
      running: { fr: "En cours", en: "Running" },
      succeeded: { fr: "Terminé", en: "Completed" },
      failed: { fr: "Échoué", en: "Failed" },
    },
    timeline: {
      created: { fr: "Créé", en: "Created" },
      started: { fr: "Démarré", en: "Started" },
      progress: { fr: "Progression", en: "Progress" },
      finished: { fr: "Terminé", en: "Finished" },
    },
    table: {
      type: { fr: "Type", en: "Type" },
      params: { fr: "Paramètres", en: "Parameters" },
      error: { fr: "Erreur", en: "Error" },
      result: { fr: "Résultat", en: "Result" },
    },
  },

  dq: {
    title: { fr: "Rapport de qualité des données", en: "Data quality report" },
    loading: { fr: "Chargement…", en: "Loading…" },
  },

  risk: {
    title: { fr: "Couche risque de feu", en: "Fire risk layer" },
    subtitle: { fr: "Prédiction probabiliste · grille {g}° · emprise Cameroun", en: "Probabilistic prediction · {g}° grid · Cameroon coverage" },
    hint: { fr: "Activez la vue Carte pour afficher la couche risque sur la carte interactive.", en: "Switch to Map view to display the risk layer on the interactive map." },
    hint2: { fr: "Ouvrez le panneau de configuration avec la sphère flottante.", en: "Open the configuration panel using the floating sphere." },
  },

  riskPanel: {
    title: { fr: "Analyse de risque de feu", en: "Fire risk analysis" },
    config: { fr: "Configuration", en: "Configuration" },
    toggleLayer: { fr: "Afficher la couche risque", en: "Show risk layer" },
    grid: { fr: "Grille (°)", en: "Grid (°)" },
    window: { fr: "Fenêtre (jours)", en: "Window (days)" },
    windowDays: { fr: "jours", en: "days" },
    date: { fr: "Date de référence", en: "Reference date" },
    threshold: { fr: "Seuil d'affichage", en: "Display threshold" },
    run: { fr: "Exécuter prédiction", en: "Run prediction" },
    load: { fr: "Charger artefact", en: "Load artifact" },
    honesty: { fr: "Bandeau honnêteté", en: "Honesty banner" },
    honestyText: { fr: "Estimation du risque d'activité de feu <b>détectée</b>", en: "Estimation of <b>detected</b> fire activity risk" },
    honestyTail: { fr: "pas une alerte incendie", en: "not a fire alert" },
    honestyData: { fr: "données {origin} · généré le {generatedAt}", en: "data from {origin} · generated {generatedAt}" },
    waiting: { fr: "Module de prédiction en attente de données", en: "Prediction module awaiting data" },
    metrics: { fr: "Métriques du modèle", en: "Model metrics" },
    metricPR: { fr: "PR-AUC", en: "PR-AUC" },
    metricF1: { fr: "F1", en: "F1" },
    metricBaseline: { fr: "Baseline", en: "Baseline" },
    log: { fr: "Journal d'exécution", en: "Execution log" },
    status: {
      ok: { fr: "Données chargées", en: "Data loaded" },
      loading: { fr: "Chargement…", en: "Loading…" },
      error: { fr: "Indisponible", en: "Unavailable" },
      none: { fr: "En attente", en: "Waiting" },
    },
  },

  ai: {
    title: { fr: "Assistant IA", en: "AI Assistant" },
    newChat: { fr: "Nouvelle conversation", en: "New conversation" },
    placeholder: { fr: "Posez votre question…", en: "Ask a question…" },
    send: { fr: "Envoyer", en: "Send" },
    thinking: { fr: "Réflexion en cours…", en: "Thinking…" },
    note: { fr: "Réponses générées par IA, à vérifier. Ce n'est pas une alerte incendie.", en: "AI-generated responses, verify them. This is not a fire alert." },
    suggestions: {
      summarize: { fr: "Résumer la zone affichée sur la carte.", en: "Summarize the area shown on the map." },
      colors: { fr: "Que signifient les niveaux de risque et les couleurs ?", en: "What do the risk levels and colors mean?" },
      modisViirs: { fr: "Quelle est la différence entre MODIS et VIIRS ?", en: "What is the difference between MODIS and VIIRS?" },
    },
    notConnected: { fr: "Assistant non connecté : le backend /api/v1/chat est requis.", en: "Assistant not connected: backend /api/v1/chat is required." },
    welcome: {
      fr: "Bonjour, je peux vous aider à lire la carte, comprendre les niveaux de risque et les données FIRMS. Que souhaitez-vous savoir ?",
      en: "Hello, I can help you read the map, understand risk levels and FIRMS data. What would you like to know?",
    },
    welcomeNew: {
      fr: "Nouvelle conversation. Que souhaitez-vous savoir ?",
      en: "New conversation. What would you like to know?",
    },
  },

  sphere: { fr: "Assistant IA", en: "AI Assistant" },

  lang: {
    fr: { fr: "Français", en: "French" },
    en: { fr: "Anglais", en: "English" },
  },
};
