import {
  type StaticDataRouteOption,
  useMatches,
  useRouter,
} from '@tanstack/react-router';

function useMatchesFor(to?: string) {
  const currentMatches = useMatches();
  const router = useRouter();
  return to === undefined ? currentMatches : router.matchRoutes(to);
}

function useStaticData<K extends keyof StaticDataRouteOption>(
  key: K,
  to?: string,
) {
  const matches = useMatchesFor(to);
  const matchWithValue = [...matches]
    .reverse()
    .find((match) => match.staticData[key] !== null);
  return matchWithValue?.staticData[key] ?? null;
}

export function useTitle(to?: string) {
  return useStaticData('title', to);
}

export function useIcon(to?: string) {
  return useStaticData('icon', to);
}
