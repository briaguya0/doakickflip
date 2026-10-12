import { AppSidebar } from '@/components/app-sidebar';
import { Button } from '@/components/ui/button';
import { SidebarProvider, SidebarTrigger } from '@/components/ui/sidebar';

export function App() {
  return (
    <SidebarProvider>
      <AppSidebar />
      <main className="flex flex-col items-start gap-4 p-8">
        <SidebarTrigger />
        <h2 className="text-3xl font-bold">Hello from React!</h2>
        <Button>Do a Kickflip</Button>
      </main>
    </SidebarProvider>
  );
}
