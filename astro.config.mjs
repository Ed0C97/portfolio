// @ts-check
import { defineConfig } from 'astro/config';

// Local-only for now. When publishing to GitHub Pages, set `site` (and `base`
// if deploying to Ed0C97.github.io/<repo>) and follow README.md.
export default defineConfig({
  i18n: {
    defaultLocale: 'en',
    locales: ['en', 'it'],
    routing: {
      prefixDefaultLocale: false,
    },
  },
});
