import {
  NumberCircleOneIcon,
  NumberCircleTwoIcon,
  StarFourIcon,
} from '@phosphor-icons/react';
import { Link, useMatchRoute } from '@tanstack/react-router';
import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from '@/components/ui/sidebar';

const items = [
  { title: 'Page 1', to: '/', icon: NumberCircleOneIcon },
  { title: 'Page 2', to: '/page-2', icon: NumberCircleTwoIcon },
] as const;

export function AppSidebar() {
  const matchRoute = useMatchRoute();

  return (
    <Sidebar collapsible="icon" variant="inset">
      <SidebarHeader>
        <div className="flex h-12 items-center gap-2 overflow-hidden transition-[width] group-data-[collapsible=icon]:w-8">
          <div className="bg-sidebar-primary text-sidebar-primary-foreground flex aspect-square size-8 shrink-0 items-center justify-center rounded-lg">
            <StarFourIcon />
          </div>
          <span className="text-sm font-medium whitespace-nowrap">
            Do a Kickflip
          </span>
        </div>
      </SidebarHeader>
      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupContent>
            <SidebarMenu>
              {items.map((item) => (
                <SidebarMenuItem key={item.title}>
                  <SidebarMenuButton
                    render={<Link to={item.to} />}
                    isActive={!!matchRoute({ to: item.to })}
                    tooltip={item.title}
                  >
                    <item.icon />
                    <span>{item.title}</span>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>
    </Sidebar>
  );
}
