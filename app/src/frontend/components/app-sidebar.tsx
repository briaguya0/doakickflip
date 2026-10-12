import {
  NumberCircleOneIcon,
  NumberCircleTwoIcon,
} from '@phosphor-icons/react';
import { Link, useMatchRoute } from '@tanstack/react-router';
import { AppSidebarHeader } from '@/components/app-sidebar-header';
import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
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
      <AppSidebarHeader />
      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupContent>
            <SidebarMenu>
              {items.map((item) => (
                <SidebarMenuItem key={item.title}>
                  <SidebarMenuButton
                    render={<Link to={item.to} />}
                    className="data-active:shadow-[inset_3px_0_0_var(--sidebar-primary)]"
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
