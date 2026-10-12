// adapted from https://github.com/shadcn-ui/ui/blob/b9f62a83999dc7df855738a8715f40ab156b1f10/apps/v4/registry/bases/base/blocks/dashboard-01/components/site-header.tsx
import { AppSidebarTrigger } from '@/components/app-sidebar-trigger';
import { Separator } from '@/components/ui/separator';
import { useTitle } from '@/hooks/use-static-data';

export function PageHeader() {
  const title = useTitle();

  return (
    <header className="h-header -mt-px flex shrink-0 items-center gap-2 border-b">
      <div className="flex w-full items-center gap-1 px-3">
        <AppSidebarTrigger />
        <Separator
          orientation="vertical"
          className="mr-4 ml-2 h-4 data-vertical:self-auto"
        />
        <h1 className="text-xl font-semibold [text-box:trim-both_cap_alphabetic]">
          {title}
        </h1>
      </div>
    </header>
  );
}
