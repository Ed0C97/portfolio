export const languages = { en: 'EN', it: 'IT' } as const;
export type Lang = keyof typeof languages;
export const defaultLang: Lang = 'en';

export const ui = {
  en: {
    'nav.projects': 'Projects',
    'nav.about': 'About',
    'nav.contact': 'Contact',
    'hero.hi': "Hi, I'm",
    'hero.viewProjects': 'View projects',
    'hero.github': 'GitHub',
    'home.featuredKicker': 'Selected work',
    'home.featuredTitle': 'Featured projects',
    'home.viewAll': 'All projects',
    'home.aboutKicker': 'About',
    'home.aboutTitle': 'Who I am',
    'home.expKicker': 'Experience',
    'home.expTitle': 'Where I have worked',
    'home.skillsKicker': 'Skills',
    'home.skillsTitle': 'What I work with',
    'home.eduKicker': 'Education',
    'home.eduTitle': 'Education and certifications',
    'home.contactKicker': 'Contact',
    'home.contactTitle': 'Get in touch',
    'home.contactBody':
      'The fastest way to reach me is email. I answer in Italian or English.',
    'home.contactCta': 'Write me',
    'projects.kicker': 'Archive',
    'projects.title': 'All projects',
    'projects.subtitle':
      'Every project links to its folder in the portfolio repository, with code samples and a longer writeup.',
    'project.back': 'All projects',
    'project.stack': 'Stack',
    'project.repo': 'View on GitHub',
    'project.next': 'Next project',
    'footer.location': 'Rome, Italy',
    'thesis.label': 'B.Sc. thesis',
  },
  it: {
    'nav.projects': 'Progetti',
    'nav.about': 'Chi sono',
    'nav.contact': 'Contatti',
    'hero.hi': 'Ciao, sono',
    'hero.viewProjects': 'Vedi i progetti',
    'hero.github': 'GitHub',
    'home.featuredKicker': 'Lavori scelti',
    'home.featuredTitle': 'Progetti in evidenza',
    'home.viewAll': 'Tutti i progetti',
    'home.aboutKicker': 'Chi sono',
    'home.aboutTitle': 'In breve',
    'home.expKicker': 'Esperienza',
    'home.expTitle': 'Dove ho lavorato',
    'home.skillsKicker': 'Competenze',
    'home.skillsTitle': 'Con cosa lavoro',
    'home.eduKicker': 'Formazione',
    'home.eduTitle': 'Studi e certificazioni',
    'home.contactKicker': 'Contatti',
    'home.contactTitle': 'Scrivimi',
    'home.contactBody':
      'Il modo piu rapido per raggiungermi e la mail. Rispondo in italiano o in inglese.',
    'home.contactCta': 'Scrivimi',
    'projects.kicker': 'Archivio',
    'projects.title': 'Tutti i progetti',
    'projects.subtitle':
      'Ogni progetto rimanda alla sua cartella nel repository del portfolio, con esempi di codice e una descrizione estesa.',
    'project.back': 'Tutti i progetti',
    'project.stack': 'Stack',
    'project.repo': 'Vedi su GitHub',
    'project.next': 'Prossimo progetto',
    'footer.location': 'Roma, Italia',
    'thesis.label': 'Tesi triennale',
  },
} as const;

export function getLangFromUrl(url: URL): Lang {
  const [, first] = url.pathname.split('/');
  if (first === 'it') return 'it';
  return 'en';
}

export function useTranslations(lang: Lang) {
  return function t(key: keyof (typeof ui)['en']): string {
    return ui[lang][key] ?? ui[defaultLang][key];
  };
}

/** Path helpers for the language toggle: `/x` <-> `/it/x`. */
export function toEnglishPath(pathname: string): string {
  const p = pathname.replace(/^\/it(\/|$)/, '/');
  return p === '' ? '/' : p;
}

export function toItalianPath(pathname: string): string {
  if (pathname === '/' || pathname === '') return '/it/';
  if (pathname.startsWith('/it/') || pathname === '/it') return pathname;
  return '/it' + pathname;
}

/** Localized href builder: localePath('en', '/projects/') -> '/projects/'. */
export function localePath(lang: Lang, path: string): string {
  return lang === 'it' ? toItalianPath(path) : path;
}
