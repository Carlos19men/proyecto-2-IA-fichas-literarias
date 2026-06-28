"use client";

import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { MoreHorizontal, UserPlus, Mail, Shield } from "lucide-react";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

interface User {
  id: string;
  nombre: string;
  email: string;
  rol: string;
  fichasAsignadas: number;
  fechaRegistro: string;
  estado: string;
}

interface UsersTableProps {
  data: User[];
}

export function UsersTable({ data }: UsersTableProps) {
  const getRolColor = (rol: string) => {
    switch (rol) {
      case "Administrador":
        return "bg-red-100 text-red-800 dark:bg-red-900/40 dark:text-red-200";
      case "Editor":
        return "bg-blue-100 text-blue-800 dark:bg-blue-900/40 dark:text-blue-200";
      case "Revisor":
        return "bg-green-100 text-green-800 dark:bg-green-900/40 dark:text-green-200";
      case "Investigador":
        return "bg-purple-100 text-purple-800 dark:bg-purple-900/40 dark:text-purple-200";
      default:
        return "bg-gray-100 text-gray-800 dark:bg-gray-900/40 dark:text-gray-200";
    }
  };

  const getEstadoColor = (estado: string) => {
    return estado === "Activo"
      ? "bg-green-100 text-green-800 dark:bg-green-900/40 dark:text-green-200"
      : "bg-gray-100 text-gray-800 dark:bg-gray-900/40 dark:text-gray-200";
  };

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <div>
          <h3 className="text-lg font-semibold text-foreground">Colaboradores del Proyecto</h3>
          <p className="text-sm text-muted-foreground">
            Gestiona los usuarios y sus permisos en el sistema
          </p>
        </div>
        <Button>
          <UserPlus className="mr-2 h-4 w-4" />
          Nuevo Usuario
        </Button>
      </div>

      <div className="rounded-md border border-border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Nombre</TableHead>
              <TableHead>Email</TableHead>
              <TableHead>Rol</TableHead>
              <TableHead>Fichas Asignadas</TableHead>
              <TableHead>Fecha Registro</TableHead>
              <TableHead>Estado</TableHead>
              <TableHead className="text-right">Acciones</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {data.map((user) => (
              <TableRow key={user.id}>
                <TableCell className="font-medium">
                  <div className="flex items-center gap-2">
                    <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary/10">
                      <span className="text-xs font-bold text-primary">
                        {user.nombre.charAt(0)}
                      </span>
                    </div>
                    <span className="text-foreground">{user.nombre}</span>
                  </div>
                </TableCell>
                <TableCell>
                  <div className="flex items-center gap-2 text-muted-foreground">
                    <Mail className="h-3 w-3" />
                    {user.email}
                  </div>
                </TableCell>
                <TableCell>
                  <Badge className={getRolColor(user.rol)}>
                    <Shield className="mr-1 h-3 w-3" />
                    {user.rol}
                  </Badge>
                </TableCell>
                <TableCell>
                  <span className="font-medium text-foreground">{user.fichasAsignadas}</span>
                </TableCell>
                <TableCell className="text-muted-foreground">{user.fechaRegistro}</TableCell>
                <TableCell>
                  <Badge className={getEstadoColor(user.estado)}>
                    {user.estado}
                  </Badge>
                </TableCell>
                <TableCell className="text-right">
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button variant="ghost" className="h-8 w-8 p-0">
                        <span className="sr-only">Abrir menú</span>
                        <MoreHorizontal className="h-4 w-4" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      <DropdownMenuLabel>Acciones</DropdownMenuLabel>
                      <DropdownMenuItem>
                        <Mail className="mr-2 h-4 w-4" />
                        Enviar correo
                      </DropdownMenuItem>
                      <DropdownMenuItem>
                        <Shield className="mr-2 h-4 w-4" />
                        Cambiar rol
                      </DropdownMenuItem>
                      <DropdownMenuSeparator />
                      <DropdownMenuItem className="text-green-600 dark:text-green-400">
                        Activar usuario
                      </DropdownMenuItem>
                      <DropdownMenuItem className="text-red-600 dark:text-red-400">
                        Desactivar usuario
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-muted p-4 rounded-lg">
          <h4 className="font-medium mb-2 text-foreground">Roles del Sistema</h4>
          <ul className="space-y-1 text-sm">
            <li className="flex items-center gap-2 text-muted-foreground">
              <Shield className="h-3 w-3 text-red-500" />
              <span>Administrador: Acceso total</span>
            </li>
            <li className="flex items-center gap-2 text-muted-foreground">
              <Shield className="h-3 w-3 text-blue-500" />
              <span>Editor: Crear/editar fichas</span>
            </li>
            <li className="flex items-center gap-2 text-muted-foreground">
              <Shield className="h-3 w-3 text-green-500" />
              <span>Revisor: Validar fichas</span>
            </li>
            <li className="flex items-center gap-2 text-muted-foreground">
              <Shield className="h-3 w-3 text-purple-500" />
              <span>Investigador: Solo lectura</span>
            </li>
          </ul>
        </div>

        <div className="bg-muted p-4 rounded-lg">
          <h4 className="font-medium mb-2 text-foreground">Estadísticas de Usuarios</h4>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-muted-foreground">Total usuarios:</span>
              <span className="font-medium text-foreground">12</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Usuarios activos:</span>
              <span className="font-medium text-foreground">10</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Editores activos:</span>
              <span className="font-medium text-foreground">4</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Revisores activos:</span>
              <span className="font-medium text-foreground">3</span>
            </div>
          </div>
        </div>

        <div className="bg-muted p-4 rounded-lg">
          <h4 className="font-medium mb-2 text-foreground">Permisos por Rol</h4>
          <p className="text-sm text-muted-foreground">
            Los administradores pueden asignar roles desde este panel. Solo los
            usuarios con rol &ldquo;Administrador&rdquo; pueden acceder a esta sección.
          </p>
        </div>
      </div>
    </div>
  );
}
