"use client";

import { useState } from "react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { DashboardHeader } from "@/components/admin/dashboard-header";
import { FichasTable } from "@/components/admin/fichas-table";
import { FichaForm } from "@/components/admin/ficha-form";
import { UsersTable } from "@/components/admin/users-table";
import { StatsCards } from "@/components/admin/stats-cards";
import { Sidebar } from "@/components/admin/sidebar";
import { AdminProviders } from "@/components/admin/providers";

const mockFichas = [
  {
    id: "1",
    nombre: "Rómulo Gallegos",
    tipo: "Autor",
    estado: "Validada",
    editor: "María Pérez",
    revisor: "Carlos López",
    fechaCreacion: "2024-02-15",
    fechaActualizacion: "2024-02-20",
  },
  {
    id: "2",
    nombre: "Teresa de la Parra",
    tipo: "Autor",
    estado: "Por Revisar",
    editor: "Ana García",
    revisor: "Pedro Martínez",
    fechaCreacion: "2024-02-18",
    fechaActualizacion: "2024-02-18",
  },
  {
    id: "3",
    nombre: "Revista Horizontes",
    tipo: "Revista",
    estado: "Por Completar",
    editor: "Juan Rodríguez",
    revisor: "Laura Fernández",
    fechaCreacion: "2024-02-10",
    fechaActualizacion: "2024-02-10",
  },
  {
    id: "4",
    nombre: "Antología del Cuento Venezolano",
    tipo: "Antología",
    estado: "Rechazada",
    editor: "Sofía Ramírez",
    revisor: "Diego Gómez",
    fechaCreacion: "2024-02-05",
    fechaActualizacion: "2024-02-08",
  },
  {
    id: "5",
    nombre: "Arturo Uslar Pietri",
    tipo: "Autor",
    estado: "Validada",
    editor: "Miguel Torres",
    revisor: "Isabel Vargas",
    fechaCreacion: "2024-02-22",
    fechaActualizacion: "2024-02-25",
  },
];

const mockUsers = [
  {
    id: "1",
    nombre: "Ana García",
    email: "ana.garcia@letrascopio.com",
    rol: "Editor",
    fichasAsignadas: 5,
    fechaRegistro: "2024-01-15",
    estado: "Activo",
  },
  {
    id: "2",
    nombre: "Carlos López",
    email: "carlos.lopez@letrascopio.com",
    rol: "Revisor",
    fichasAsignadas: 8,
    fechaRegistro: "2024-01-20",
    estado: "Activo",
  },
  {
    id: "3",
    nombre: "Pedro Martínez",
    email: "pedro.martinez@letrascopio.com",
    rol: "Investigador",
    fichasAsignadas: 3,
    fechaRegistro: "2024-02-01",
    estado: "Activo",
  },
  {
    id: "4",
    nombre: "Laura Fernández",
    email: "laura.fernandez@letrascopio.com",
    rol: "Editor",
    fichasAsignadas: 7,
    fechaRegistro: "2024-01-10",
    estado: "Inactivo",
  },
  {
    id: "5",
    nombre: "Juan Rodríguez",
    email: "juan.rodriguez@letrascopio.com",
    rol: "Administrador",
    fichasAsignadas: 12,
    fechaRegistro: "2024-01-05",
    estado: "Activo",
  },
];

export default function AdminPanel() {
  const [activeTab, setActiveTab] = useState("fichas");

  return (
    <AdminProviders>
      <div className="h-screen overflow-hidden bg-background flex flex-col">
        <DashboardHeader />

        <div className="flex flex-1 overflow-hidden">
          <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} />

          <main className="flex-1 overflow-y-scroll p-4 md:p-8">
            <div className="max-w-7xl mx-auto space-y-8 animate-fade-slide-up">
              <StatsCards />

              <div className="mt-8">
                {activeTab === "fichas" && (
                  <Card className="border-border dark:border-white/10 shadow-sm">
                    <CardHeader>
                      <CardTitle className="font-playfair">Gestión de Fichas Literarias</CardTitle>
                      <CardDescription>
                        Administra las fichas literarias y su estado en el proceso de
                        curación
                      </CardDescription>
                    </CardHeader>
                    <CardContent>
                      <FichasTable data={mockFichas} />
                    </CardContent>
                  </Card>
                )}

                {activeTab === "usuarios" && (
                  <Card className="border-border dark:border-white/10 shadow-sm">
                    <CardHeader>
                      <CardTitle className="font-playfair">Gestión de Usuarios y Roles</CardTitle>
                      <CardDescription>
                        Administra los colaboradores del proyecto y sus permisos
                      </CardDescription>
                    </CardHeader>
                    <CardContent>
                      <UsersTable data={mockUsers} />
                    </CardContent>
                  </Card>
                )}

                {activeTab === "estadisticas" && (
                  <Card className="border-border dark:border-white/10 shadow-sm bg-transparent border-none shadow-none">
                    <CardHeader className="px-0 pt-0">
                      <CardTitle className="font-playfair">Estadísticas del Sistema</CardTitle>
                      <CardDescription>
                        Monitoreo y análisis del flujo de trabajo
                      </CardDescription>
                    </CardHeader>
                    <CardContent className="px-0">
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <Card className="border-border dark:border-white/10 shadow-sm">
                          <CardHeader>
                            <CardTitle className="text-lg">
                              Distribución por Estado
                            </CardTitle>
                          </CardHeader>
                          <CardContent>
                            <div className="space-y-4">
                              <div className="flex justify-between items-center p-3 rounded-md hover:bg-secondary/50 transition-colors">
                                <span className="text-sm font-medium text-foreground">Por Completar</span>
                                <span className="font-semibold bg-secondary text-foreground px-2.5 py-0.5 rounded-full text-sm">12</span>
                              </div>
                              <div className="flex justify-between items-center p-3 rounded-md hover:bg-secondary/50 transition-colors">
                                <span className="text-sm font-medium text-foreground">Por Revisar</span>
                                <span className="font-semibold bg-secondary text-foreground px-2.5 py-0.5 rounded-full text-sm">8</span>
                              </div>
                              <div className="flex justify-between items-center p-3 rounded-md hover:bg-secondary/50 transition-colors">
                                <span className="text-sm font-medium text-foreground">Validada</span>
                                <span className="font-semibold bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400 px-2.5 py-0.5 rounded-full text-sm">24</span>
                              </div>
                              <div className="flex justify-between items-center p-3 rounded-md hover:bg-secondary/50 transition-colors">
                                <span className="text-sm font-medium text-foreground">Rechazada</span>
                                <span className="font-semibold bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400 px-2.5 py-0.5 rounded-full text-sm">3</span>
                              </div>
                            </div>
                          </CardContent>
                        </Card>

                        <Card className="border-border dark:border-white/10 shadow-sm">
                          <CardHeader>
                            <CardTitle className="text-lg">Actividad Reciente</CardTitle>
                          </CardHeader>
                          <CardContent>
                            <div className="space-y-4 relative before:absolute before:inset-0 before:ml-5 before:-translate-x-px md:before:mx-auto md:before:translate-x-0 before:h-full before:w-0.5 before:bg-border dark:before:bg-white/20">
                              <div className="relative flex items-center justify-between md:justify-normal md:odd:flex-row-reverse group is-active">
                                <div className="flex items-center justify-center w-10 h-10 rounded-full border border-border dark:border-white/50 bg-secondary dark:bg-card group-[.is-active]:bg-primary group-[.is-active]:text-primary-foreground text-muted-foreground dark:text-foreground shadow shrink-0 md:order-1 md:group-odd:-translate-x-1/2 md:group-even:translate-x-1/2 z-10 transition-colors">
                                  <span className="text-xs font-bold">1</span>
                                </div>
                                <div className="w-[calc(100%-4rem)] md:w-[calc(50%-2.5rem)] bg-card border border-border dark:border-white/10 p-4 rounded shadow-sm hover:shadow-md transition-shadow">
                                  <div className="flex items-center justify-between space-x-2 mb-1">
                                    <div className="font-bold text-sm text-foreground">Ficha &ldquo;Andrés Bello&rdquo; completada</div>
                                    <time className="text-xs font-medium text-primary">Hace 2h</time>
                                  </div>
                                  <div className="text-xs text-muted-foreground">Por Ana García</div>
                                </div>
                              </div>
                              <div className="relative flex items-center justify-between md:justify-normal md:odd:flex-row-reverse group">
                                <div className="flex items-center justify-center w-10 h-10 rounded-full border border-border dark:border-white/50 bg-secondary dark:bg-card text-muted-foreground dark:text-foreground shadow shrink-0 md:order-1 md:group-odd:-translate-x-1/2 md:group-even:translate-x-1/2 z-10 transition-colors">
                                  <span className="text-xs font-bold">2</span>
                                </div>
                                <div className="w-[calc(100%-4rem)] md:w-[calc(50%-2.5rem)] bg-card border border-border dark:border-white/10 p-4 rounded shadow-sm hover:shadow-md transition-shadow">
                                  <div className="flex items-center justify-between space-x-2 mb-1">
                                    <div className="font-bold text-sm text-foreground">Usuario nuevo registrado</div>
                                    <time className="text-xs font-medium text-muted-foreground">Hace 5h</time>
                                  </div>
                                  <div className="text-xs text-muted-foreground">Rol: Editor</div>
                                </div>
                              </div>
                              <div className="relative flex items-center justify-between md:justify-normal md:odd:flex-row-reverse group">
                                <div className="flex items-center justify-center w-10 h-10 rounded-full border border-border dark:border-white/50 bg-secondary dark:bg-card text-muted-foreground dark:text-foreground shadow shrink-0 md:order-1 md:group-odd:-translate-x-1/2 md:group-even:translate-x-1/2 z-10 transition-colors">
                                  <span className="text-xs font-bold">3</span>
                                </div>
                                <div className="w-[calc(100%-4rem)] md:w-[calc(50%-2.5rem)] bg-card border border-border dark:border-white/10 p-4 rounded shadow-sm hover:shadow-md transition-shadow">
                                  <div className="flex items-center justify-between space-x-2 mb-1">
                                    <div className="font-bold text-sm text-foreground">3 fichas validadas</div>
                                    <time className="text-xs font-medium text-muted-foreground">Hace 1 día</time>
                                  </div>
                                  <div className="text-xs text-muted-foreground">Por Carlos López</div>
                                </div>
                              </div>
                            </div>
                          </CardContent>
                        </Card>
                      </div>
                    </CardContent>
                  </Card>
                )}

                {activeTab === "nueva" && (
                  <Card className="border-border dark:border-white/10 shadow-sm">
                    <CardHeader>
                      <CardTitle className="font-playfair">Crear Nueva Ficha Literaria</CardTitle>
                      <CardDescription>
                        Agrega una nueva ficha al sistema y asigna editores y revisores
                      </CardDescription>
                    </CardHeader>
                    <CardContent>
                      <FichaForm />
                    </CardContent>
                  </Card>
                )}
              </div>
            </div>
          </main>
        </div>
      </div>
    </AdminProviders>
  );
}
