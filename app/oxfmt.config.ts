import { defineConfig } from 'oxfmt';

export default defineConfig({
  ignorePatterns: ['src/frontend/routeTree.gen.ts'],
  singleQuote: true,
  printWidth: 80,
  sortPackageJson: false,
  sortTailwindcss: true,
});
