import { SkateboardIcon } from '@/components/skateboard-icon';
import { SidebarHeader } from '@/components/ui/sidebar';
import { cn } from '@/lib/utils';

export function AppSidebarHeader() {
  return (
    <SidebarHeader>
      <div
        className={cn(
          'flex h-12 items-center gap-2.5',
          'transition-[width] group-data-[collapsible=icon]:w-8',
        )}
      >
        <SkateboardIcon
          className={cn(
            'size-8 shrink-0',
            'text-sidebar-primary',
            'drop-shadow-[0_0_8px_color-mix(in_oklab,var(--sidebar-primary)_35%,transparent)]',
          )}
        />
        <span
          className={cn(
            'min-w-0 overflow-hidden whitespace-nowrap',
            'translate-y-0.5 [text-box:trim-both_cap_alphabetic]',
            'text-base leading-none font-extrabold uppercase [word-spacing:0.2em]',
          )}
        >
          Do a
          <small className="text-sidebar-primary block text-xs tracking-[0.22em]">
            Kickflip
          </small>
        </span>
      </div>
      <div className="border-sidebar-primary/55 border-t-2" />
    </SidebarHeader>
  );
}
