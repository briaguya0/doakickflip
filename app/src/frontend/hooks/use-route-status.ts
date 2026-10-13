import { useSettingsStatus, useTwitchStatus } from '@/hooks/use-status';

export function useRouteStatus(to: string) {
  const twitchStatus = useTwitchStatus();
  const settingsStatus = useSettingsStatus();

  switch (to) {
    case '/twitch':
      return twitchStatus;
    case '/settings':
      return settingsStatus;
    default:
      return null;
  }
}
