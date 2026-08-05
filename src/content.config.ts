import { defineCollection, z } from 'astro:content';
import { glob } from 'astro/loaders';

// One markdown file per project per language: `en/<slug>.md` and `it/<slug>.md`.
// The folder split keeps entry ids unique per language.
// `visible` and `featured` are the two switches the owner flips:
//   visible: false  -> the project disappears from the site entirely
//   featured: true  -> the project appears on the home page grid
const projects = defineCollection({
  loader: glob({
    pattern: '**/*.md',
    base: './src/content/projects',
    // The default generateId prefers the frontmatter `slug`, which is the same
    // for both languages of a project and makes the two entries collide.
    // Use the file path instead: "en/sentinel", "it/sentinel".
    generateId: ({ entry }) => entry.replace(/\.md$/, ''),
  }),
  schema: z.object({
    title: z.string(),
    slug: z.string(),
    lang: z.enum(['en', 'it']),
    oneLiner: z.string().max(160),
    category: z.string(),
    year: z.string().optional(),
    status: z.string(),
    statusTone: z.enum(['production', 'beta', 'prototype', 'spec']).default('beta'),
    featured: z.boolean().default(false),
    visible: z.boolean().default(true),
    order: z.number().default(99),
    metrics: z
      .array(z.object({ value: z.string(), label: z.string() }))
      .min(1)
      .max(2),
    stack: z.array(z.string()).min(1),
    repo: z.string().url().optional(),
    image: z.string().default('/images/projects/placeholder.svg'),
  }),
});

export const collections = { projects };
