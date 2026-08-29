"use client";

import * as React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { ShieldCheck, ChevronLeft, ChevronRight } from "lucide-react";
import { cn } from "@/lib/utils";
import { SIDEBAR_ITEMS } from "@/lib/constants";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

interface SidebarProps {
  collapsed: boolean;
  onToggleCollapse: () => void;
}

export function Sidebar({ collapsed, onToggleCollapse }: SidebarProps) {
  const pathname = usePathname();

  return (
    <aside
      className={cn(
        "relative flex flex-col border-r bg-card text-card-foreground transition-all duration-300 ease-in-out z-30 select-none",
        collapsed ? "w-16" : "w-64"
      )}
    >
      {/* Brand Header */}
      <div className="flex h-14 items-center justify-between px-3 border-b">
        <Link href="/" className="flex items-center gap-2.5 overflow-hidden font-semibold">
          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-primary text-primary-foreground shadow-sm">
            <ShieldCheck className="h-5 w-5" />
          </div>
          {!collapsed && (
            <div className="flex flex-col">
              <span className="text-sm font-bold tracking-tight text-foreground">LedgerGuard</span>
              <span className="text-[10px] text-muted-foreground font-mono">AI FINANCE CONTROLLER</span>
            </div>
          )}
        </Link>
        <Button
          variant="ghost"
          size="icon"
          onClick={onToggleCollapse}
          className="h-7 w-7 text-muted-foreground hover:text-foreground"
          aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
        >
          {collapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
        </Button>
      </div>

      {/* Navigation Links */}
      <nav className="flex-1 space-y-1 p-2 overflow-y-auto">
        {SIDEBAR_ITEMS.map((item) => {
          const isActive = pathname === item.href || (item.href !== "/" && pathname.startsWith(item.href));
          const Icon = item.icon;

          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 rounded-md px-3 py-2 text-xs font-medium transition-colors relative group",
                isActive
                  ? "bg-primary/10 text-primary font-semibold dark:bg-primary/20"
                  : "text-muted-foreground hover:bg-accent hover:text-foreground"
              )}
            >
              <Icon className={cn("h-4 w-4 shrink-0", isActive ? "text-primary" : "text-muted-foreground group-hover:text-foreground")} />
              {!collapsed && <span className="truncate flex-1">{item.name}</span>}
              {!collapsed && item.badge && (
                <Badge
                  variant={item.badge === "AI" ? "ai" : item.badge === "Run" ? "default" : "secondary"}
                  className="px-1.5 py-0 text-[10px] h-4"
                >
                  {item.badge}
                </Badge>
              )}

              {/* Tooltip for collapsed view */}
              {collapsed && (
                <div className="absolute left-full ml-2 hidden rounded-md bg-popover px-2 py-1 text-xs text-popover-foreground shadow-md group-hover:block z-50 whitespace-nowrap border">
                  {item.name}
                </div>
              )}
            </Link>
          );
        })}
      </nav>

      {/* Demo Status Footer */}
      {!collapsed && (
        <div className="p-3 border-t bg-muted/30">
          <div className="flex items-center justify-between text-[11px] text-muted-foreground">
            <span>Track 4: Finance AI</span>
            <span className="font-mono text-emerald-600 dark:text-emerald-400 font-semibold">● v1.0.0</span>
          </div>
        </div>
      )}
    </aside>
  );
}
