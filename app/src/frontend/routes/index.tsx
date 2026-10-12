import { NumberCircleOneIcon } from '@phosphor-icons/react';
import { createFileRoute } from '@tanstack/react-router';
import { Button } from '@/components/ui/button';

export const Route = createFileRoute('/')({
  component: Page1,
  staticData: { title: 'Page 1', icon: <NumberCircleOneIcon /> },
});

function Page1() {
  return <Button>Do a Kickflip</Button>;
}
