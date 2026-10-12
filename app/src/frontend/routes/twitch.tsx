import { createFileRoute } from '@tanstack/react-router';
import { TwitchGlitchIcon } from '@/components/twitch-glitch-icon';

export const Route = createFileRoute('/twitch')({
  component: Twitch,
  staticData: { title: 'Twitch', icon: <TwitchGlitchIcon /> },
});

function Twitch() {
  return null;
}
