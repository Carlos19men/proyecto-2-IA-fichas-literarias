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
import { MoreHorizontal, Eye, Edit, Trash2 } from "lucide-react";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

interface Ficha {
  id: string;
  nombre: string;
  tipo: string;
  estado: string;
  editor: string;
  revisor: string;
  fechaCreacion: string;
  fechaActualizacion: string;
}

interface FichasTableProps {
  data: Ficha[];
}

export function FichasTable({ data }: FichasTableProps) {
  const getEstadoColor = (estado: string) => {
    switch (estado) {
      case "Validada":
        return "bg-green-100 text-green-800 dark:bg-green-900/40 dark:text-green-200";
      case "Por Revisar":
        return "bg-yellow-100 text-yellow-800 dark:bg-yellow-900/40 dark:text-yellow-200";
      case "Por Completar":
        return "bg-blue-100 text-blue-800 dark:bg-blue-900/40 dark:text-blue-200";
      case "Rechazada":
        return "bg-red-100 text-red-800 dark:bg-red-900/40 dark:text-red-200";
      default:
        return "bg-gray-100 text-gray-800 dark:bg-gray-900/40 dark:text-gray-200";
    }
  };

  const getTipoColor = (tipo: string) => {
    switch (tipo) {
      case "Autor":
        return "bg-purple-100 text-purple-800 dark:bg-purple-900/40 dark:text-purple-200";
      case "Revista":
        return "bg-indigo-100 text-indigo-800 dark:bg-indigo-900/40 dark:text-indigo-200";
      case "Antología":
        return "bg-pink-100 text-pink-800 dark:bg-pink-900/40 dark:text-pink-200";
      case "Agrupación":
        return "bg-cyan-100 text-cyan-800 dark:bg-cyan-900/40 dark:text-cyan-200";
      default:
        return "bg-gray-100 text-gray-800 dark:bg-gray-900/40 dark:text-gray-200";
    }
  };

  return (
    <div className="rounded-md border border-border">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Nombre</TableHead>
            <TableHead>Tipo</TableHead>
            <TableHead>Estado</TableHead>
            <TableHead>Editor</TableHead>
            <TableHead>Revisor</TableHead>
            <TableHead>Fecha Creación</TableHead>
            <TableHead className="text-right">Acciones</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {data.map((ficha) => (
            <TableRow key={ficha.id}>
              <TableCell className="font-medium text-foreground">{ficha.nombre}</TableCell>
              <TableCell>
                <Badge className={getTipoColor(ficha.tipo)}>{ficha.tipo}</Badge>
              </TableCell>
              <TableCell>
                <Badge className={getEstadoColor(ficha.estado)}>
                  {ficha.estado}
                </Badge>
              </TableCell>
              <TableCell className="text-muted-foreground">{ficha.editor}</TableCell>
              <TableCell className="text-muted-foreground">{ficha.revisor}</TableCell>
              <TableCell className="text-muted-foreground">{ficha.fechaCreacion}</TableCell>
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
                      <Eye className="mr-2 h-4 w-4" />
                      Ver detalles
                    </DropdownMenuItem>
                    <DropdownMenuItem>
                      <Edit className="mr-2 h-4 w-4" />
                      Editar ficha
                    </DropdownMenuItem>
                    <DropdownMenuSeparator />
                    <DropdownMenuItem className="text-red-600 dark:text-red-400">
                      <Trash2 className="mr-2 h-4 w-4" />
                      Eliminar ficha
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
