"use client";

import { Card, CardContent } from "@/components/ui/card";
import {
  FileText,
  CheckCircle,
  Clock,
  XCircle,
  Users,
  TrendingUp,
} from "lucide-react";

export function StatsCards() {
  const stats = [
    {
      title: "Total Fichas",
      value: "47",
      description: "+5 esta semana",
      icon: FileText,
      color: "text-blue-600 dark:text-blue-400",
      bgColor: "bg-blue-50 dark:bg-blue-950/30",
    },
    {
      title: "Validadas",
      value: "24",
      description: "Listas para Neo4j",
      icon: CheckCircle,
      color: "text-green-600 dark:text-green-400",
      bgColor: "bg-green-50 dark:bg-green-950/30",
    },
    {
      title: "Por Revisar",
      value: "8",
      description: "En proceso de curación",
      icon: Clock,
      color: "text-yellow-600 dark:text-yellow-400",
      bgColor: "bg-yellow-50 dark:bg-yellow-950/30",
    },
    {
      title: "Rechazadas",
      value: "3",
      description: "Requieren corrección",
      icon: XCircle,
      color: "text-red-600 dark:text-red-400",
      bgColor: "bg-red-50 dark:bg-red-950/30",
    },
    {
      title: "Colaboradores",
      value: "12",
      description: "Editores y Revisores",
      icon: Users,
      color: "text-purple-600 dark:text-purple-400",
      bgColor: "bg-purple-50 dark:bg-purple-950/30",
    },
    {
      title: "Tasa de Validación",
      value: "85%",
      description: "Eficiencia del proceso",
      icon: TrendingUp,
      color: "text-emerald-600 dark:text-emerald-400",
      bgColor: "bg-emerald-50 dark:bg-emerald-950/30",
    },
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
      {stats.map((stat, index) => {
        const Icon = stat.icon;
        return (
          <Card key={index} className="border-border dark:border-white/10 shadow-sm bg-card/50 backdrop-blur-sm overflow-hidden transition-all duration-200 hover:-translate-y-0.5 hover:shadow-md">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-muted-foreground">
                    {stat.title}
                  </p>
                  <h3 className="text-2xl font-bold mt-1 text-foreground">{stat.value}</h3>
                  <p className="text-xs text-muted-foreground mt-1">
                    {stat.description}
                  </p>
                </div>
                <div className={`p-3 rounded-lg ${stat.bgColor}`}>
                  <Icon className={`h-6 w-6 ${stat.color}`} />
                </div>
              </div>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}
