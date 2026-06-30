import { FileText, Users, BarChart3, PlusCircle } from "lucide-react";
import { cn } from "@/lib/utils";

interface SidebarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
}

export function Sidebar({ activeTab, setActiveTab }: SidebarProps) {
  const navItems = [
    { id: "fichas", label: "Fichas", icon: FileText },
    { id: "usuarios", label: "Usuarios", icon: Users },
    { id: "estadisticas", label: "Estadísticas", icon: BarChart3 },
    { id: "nueva", label: "Nueva Ficha", icon: PlusCircle },
  ];

  return (
    <aside className="w-64 flex-shrink-0 border-r border-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 h-[calc(100vh-4rem)] sticky top-16 hidden md:block">
      <div className="p-4 space-y-1">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;

          return (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              className={cn(
                "w-full flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-200 text-sm font-medium cursor-pointer",
                isActive
                  ? "bg-primary text-primary-foreground shadow-md shadow-primary/20"
                  : "text-muted-foreground hover:bg-secondary hover:text-foreground"
              )}
            >
              <Icon className={cn("h-5 w-5 transition-transform duration-200", isActive && "scale-110")} />
              {item.label}
            </button>
          );
        })}
      </div>

      {/* Mini info card at bottom of sidebar */}
      <div className="absolute bottom-4 left-4 right-4">
        <div className="rounded-lg bg-secondary/50 p-4 border border-border/50 backdrop-blur-sm">
          <p className="text-xs font-semibold text-foreground font-playfair">LetraScopio v1.0</p>
          <p className="text-[10px] text-muted-foreground mt-1">
            Sistema de curación de fichas literarias
          </p>
        </div>
      </div>
    </aside>
  );
}
