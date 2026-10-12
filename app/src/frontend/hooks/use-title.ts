import { useMatches } from '@tanstack/react-router';

export function useTitle() {
  const matches = useMatches();
  const matchWithTitle = [...matches]
    .reverse()
    .find((match) => match.staticData.title);
  return matchWithTitle?.staticData.title;
}
