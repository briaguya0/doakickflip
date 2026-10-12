// adapted from https://github.com/shadcn-ui/ui/blob/b9f62a83999dc7df855738a8715f40ab156b1f10/apps/v4/registry/bases/base/blocks/dashboard-01/components/site-header.tsx
import { Separator } from '@/components/ui/separator';
import { SidebarTrigger } from '@/components/ui/sidebar';
import { useTitle } from '@/hooks/use-title';

export function PageHeader() {
  const title = useTitle();

  return (
    <header className="flex h-12 shrink-0 items-center gap-2 border-b">
      <div className="flex w-full items-center gap-1 px-4 lg:gap-2 lg:px-6">
        <SidebarTrigger className="-ml-1" />
        <Separator
          orientation="vertical"
          className="mx-2 h-4 data-vertical:self-auto"
        />
        <h1 className="text-base font-medium">{title}</h1>
      </div>
    </header>
  );
}
