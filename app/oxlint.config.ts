import { defineConfig } from 'oxlint';

export default defineConfig({
  ignorePatterns: ['src/frontend/routeTree.gen.ts'],
  plugins: ['eslint', 'typescript', 'unicorn', 'oxc', 'react'],
  categories: {
    correctness: 'error',
  },
  options: {
    typeAware: true,
  },
});
