import {
  LayoutDashboard,
  GitCompare,
  AlertTriangle,
  FileSpreadsheet,
  Sparkles,
  BookOpen,
  Settings as SettingsIcon,
} from "lucide-react";

export const SIDEBAR_ITEMS = [
  {
    name: "Overview",
    href: "/",
    icon: LayoutDashboard,
    badge: null,
  },
  {
    name: "Reconciliation",
    href: "/reconciliation",
    icon: GitCompare,
    badge: "Run",
  },
  {
    name: "Exceptions",
    href: "/exceptions",
    icon: AlertTriangle,
    badge: "150",
  },
  {
    name: "Reports",
    href: "/reports",
    icon: FileSpreadsheet,
    badge: null,
  },
  {
    name: "AI Copilot",
    href: "/copilot",
    icon: Sparkles,
    badge: "AI",
  },
  {
    name: "Methodology",
    href: "/methodology",
    icon: BookOpen,
    badge: null,
  },
  {
    name: "Settings",
    href: "/settings",
    icon: SettingsIcon,
    badge: null,
  },
];
