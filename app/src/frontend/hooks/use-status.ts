import { useQuery } from '@tanstack/react-query';

export type Status = 'ok' | 'pending' | 'problem';
export type StatusInfo = { status: Status; label: string };

function fetchFakeTwitchStatus(): Promise<StatusInfo> {
  return Promise.resolve({ status: 'problem', label: 'Not connected' });
}

function fetchFakeSettingsStatus(): Promise<StatusInfo | null> {
  return Promise.resolve({ status: 'problem', label: 'Needs attention' });
}

export function useTwitchStatus() {
  const { data: twitchStatus } = useQuery({
    queryKey: ['twitch-status'],
    queryFn: fetchFakeTwitchStatus,
  });
  return twitchStatus ?? null;
}

export function useSettingsStatus() {
  const { data: settingsStatus } = useQuery({
    queryKey: ['settings-status'],
    queryFn: fetchFakeSettingsStatus,
  });
  return settingsStatus ?? null;
}
