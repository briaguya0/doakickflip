import { defineConfig } from 'oxlint';

export default defineConfig({
  plugins: ['eslint', 'typescript', 'unicorn', 'oxc', 'react'],
  categories: {
    correctness: 'error',
  },
  options: {
    typeAware: true,
  },
});
