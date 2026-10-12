import { createFileRoute } from '@tanstack/react-router';
import { Button } from '@/components/ui/button';

export const Route = createFileRoute('/')({
  component: Page1,
});

function Page1() {
  return (
    <>
      <h2 className="text-3xl font-bold">Page 1</h2>
      <Button>Do a Kickflip</Button>
    </>
  );
}
