"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Card, CardContent } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useToast } from "@/hooks/use-toast";
import { Loader2, Upload, Save, CheckCircle } from "lucide-react";

const fichaSchema = z.object({
  // Información básica
  tipo: z.enum(["Autor", "Revista", "Antología", "Agrupación"], {
    required_error: "Selecciona un tipo de ficha",
  }),
  nombres: z.string().min(1, "Los nombres son requeridos"),
  apellidos: z.string().min(1, "Los apellidos son requeridos"),
  fechaNacimiento: z.string().optional(),
  fechaFallecimiento: z.string().optional(),

  // Lugares
  lugarNacimientoCiudad: z.string().min(1, "Ciudad de nacimiento es requerida"),
  lugarNacimientoMunicipio: z
    .string()
    .min(1, "Municipio de nacimiento es requerido"),
  lugarNacimientoEstado: z.string().min(1, "Estado de nacimiento es requerido"),
  lugarNacimientoPais: z.string().min(1, "País de nacimiento es requerido"),

  lugarFallecimientoCiudad: z.string().optional(),
  lugarFallecimientoMunicipio: z.string().optional(),
  lugarFallecimientoEstado: z.string().optional(),
  lugarFallecimientoPais: z.string().optional(),

  // Atributos adicionales
  sexo: z.enum(["Masculino", "Femenino", "Otro"]).optional(),
  seudonimo: z.string().optional(),
  actividadRelevante: z.string().optional(),
  familiaresDestacados: z.string().optional(),
  tematicaPrincipal: z.string().optional(),
  generoPrincipal: z.string().optional(),
  contextoHistorico: z.string().optional(),

  // Multimedia
  imagenAutor: z.string().optional(),
  archivoAudio: z.string().optional(),

  // Asignaciones
  editorId: z.string().min(1, "Asigna un editor"),
  revisorId: z.string().min(1, "Asigna un revisor"),
});

type FichaFormData = z.infer<typeof fichaSchema>;

const mockUsuarios = [
  { id: "1", nombre: "Ana García", rol: "Editor" },
  { id: "2", nombre: "Carlos López", rol: "Revisor" },
  { id: "3", nombre: "Pedro Martínez", rol: "Editor" },
  { id: "4", nombre: "Laura Fernández", rol: "Revisor" },
  { id: "5", nombre: "Juan Rodríguez", rol: "Editor" },
];

export function FichaForm() {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { toast } = useToast();

  const {
    register,
    handleSubmit,
    control,
    formState: { errors },
  } = useForm<FichaFormData>({
    resolver: zodResolver(fichaSchema),
    defaultValues: {
      tipo: "Autor",
      lugarNacimientoPais: "Venezuela",
    },
  });

  const onSubmit = async (data: FichaFormData) => {
    setIsSubmitting(true);

    // Simular envío a API
    await new Promise((resolve) => setTimeout(resolve, 1500));

    toast({
      title: "✅ Ficha creada exitosamente",
      description:
        "La ficha ha sido guardada en MongoDB y asignada a los colaboradores.",
    });

    setIsSubmitting(false);
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
      <Tabs defaultValue="basica">
        <TabsList className="grid grid-cols-4">
          <TabsTrigger value="basica">Información Básica</TabsTrigger>
          <TabsTrigger value="biografia">Biografía</TabsTrigger>
          <TabsTrigger value="multimedia">Multimedia</TabsTrigger>
          <TabsTrigger value="asignacion">Asignación</TabsTrigger>
        </TabsList>

        <TabsContent value="basica" className="space-y-4">
          <Card>
            <CardContent className="pt-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="tipo">Tipo de Ficha *</Label>
                  <Select>
                    <SelectTrigger>
                      <SelectValue placeholder="Selecciona tipo" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="Autor">Autor</SelectItem>
                      <SelectItem value="Revista">Revista</SelectItem>
                      <SelectItem value="Antología">Antología</SelectItem>
                      <SelectItem value="Agrupación">Agrupación</SelectItem>
                    </SelectContent>
                  </Select>
                  {errors.tipo && (
                    <p className="text-sm text-red-500">
                      {errors.tipo.message}
                    </p>
                  )}
                </div>

                <div className="space-y-2">
                  <Label htmlFor="seudonimo">Seudónimo (opcional)</Label>
                  <Input
                    {...register("seudonimo")}
                    placeholder="Nombre de pluma o alias"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
                <div className="space-y-2">
                  <Label htmlFor="nombres">Nombres *</Label>
                  <Input
                    {...register("nombres")}
                    placeholder="Nombres de pila"
                  />
                  {errors.nombres && (
                    <p className="text-sm text-red-500">
                      {errors.nombres.message}
                    </p>
                  )}
                </div>

                <div className="space-y-2">
                  <Label htmlFor="apellidos">Apellidos *</Label>
                  <Input
                    {...register("apellidos")}
                    placeholder="Apellidos completos"
                  />
                  {errors.apellidos && (
                    <p className="text-sm text-red-500">
                      {errors.apellidos.message}
                    </p>
                  )}
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
                <div className="space-y-2">
                  <Label htmlFor="fechaNacimiento">Fecha de Nacimiento</Label>
                  <Input {...register("fechaNacimiento")} type="date" />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="fechaFallecimiento">
                    Fecha de Fallecimiento
                  </Label>
                  <Input {...register("fechaFallecimiento")} type="date" />
                </div>
              </div>

              <div className="space-y-2 mt-4">
                <Label htmlFor="sexo">Sexo</Label>
                <Select>
                  <SelectTrigger>
                    <SelectValue placeholder="Selecciona sexo" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="Masculino">Masculino</SelectItem>
                    <SelectItem value="Femenino">Femenino</SelectItem>
                    <SelectItem value="Otro">Otro</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="biografia" className="space-y-4">
          <Card>
            <CardContent className="pt-6">
              <div className="space-y-4">
                <div>
                  <h4 className="font-medium mb-2">Lugar de Nacimiento *</h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label htmlFor="lugarNacimientoCiudad">Ciudad</Label>
                      <Input
                        {...register("lugarNacimientoCiudad")}
                        placeholder="Caracas"
                      />
                      {errors.lugarNacimientoCiudad && (
                        <p className="text-sm text-red-500">
                          {errors.lugarNacimientoCiudad.message}
                        </p>
                      )}
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="lugarNacimientoMunicipio">
                        Municipio
                      </Label>
                      <Input
                        {...register("lugarNacimientoMunicipio")}
                        placeholder="Libertador"
                      />
                      {errors.lugarNacimientoMunicipio && (
                        <p className="text-sm text-red-500">
                          {errors.lugarNacimientoMunicipio.message}
                        </p>
                      )}
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="lugarNacimientoEstado">Estado</Label>
                      <Input
                        {...register("lugarNacimientoEstado")}
                        placeholder="Distrito Capital"
                      />
                      {errors.lugarNacimientoEstado && (
                        <p className="text-sm text-red-500">
                          {errors.lugarNacimientoEstado.message}
                        </p>
                      )}
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="lugarNacimientoPais">País</Label>
                      <Input
                        {...register("lugarNacimientoPais")}
                        placeholder="Venezuela"
                      />
                      {errors.lugarNacimientoPais && (
                        <p className="text-sm text-red-500">
                          {errors.lugarNacimientoPais.message}
                        </p>
                      )}
                    </div>
                  </div>
                </div>

                <div>
                  <h4 className="font-medium mb-2">
                    Lugar de Fallecimiento (opcional)
                  </h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label htmlFor="lugarFallecimientoCiudad">Ciudad</Label>
                      <Input {...register("lugarFallecimientoCiudad")} />
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="lugarFallecimientoMunicipio">
                        Municipio
                      </Label>
                      <Input {...register("lugarFallecimientoMunicipio")} />
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="lugarFallecimientoEstado">Estado</Label>
                      <Input {...register("lugarFallecimientoEstado")} />
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="lugarFallecimientoPais">País</Label>
                      <Input {...register("lugarFallecimientoPais")} />
                    </div>
                  </div>
                </div>
              </div>

              <div className="space-y-4 mt-6">
                <div className="space-y-2">
                  <Label htmlFor="actividadRelevante">
                    Actividad Relevante
                  </Label>
                  <Textarea
                    {...register("actividadRelevante")}
                    placeholder="Estudios, cargos, profesión - Incluye lugar y periodo"
                    rows={2}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="familiaresDestacados">
                    Familiares Destacados
                  </Label>
                  <Textarea
                    {...register("familiaresDestacados")}
                    placeholder="Padres, hermanos o hijos relevantes"
                    rows={2}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="tematicaPrincipal">
                    Temática Principal de su Obra
                  </Label>
                  <Textarea
                    {...register("tematicaPrincipal")}
                    placeholder="Temas recurrentes o dominantes en su producción literaria"
                    rows={2}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="generoPrincipal">
                    Género Principal Cultivado
                  </Label>
                  <Input
                    {...register("generoPrincipal")}
                    placeholder="Ej: poesía, narrativa, ensayo"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="contextoHistorico">
                    Contexto Histórico en que Vivió
                  </Label>
                  <Textarea
                    {...register("contextoHistorico")}
                    placeholder="Entorno social, geográfico o histórico que influyó en el autor"
                    rows={3}
                  />
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="multimedia" className="space-y-4">
          <Card>
            <CardContent className="pt-6">
              <div className="space-y-6">
                <div className="space-y-2">
                  <Label htmlFor="imagenAutor">Imagen del Autor</Label>
                  <div className="flex items-center gap-4">
                    <Input
                      {...register("imagenAutor")}
                      placeholder="Enlace a imagen .jpg"
                    />
                    <Button type="button" variant="outline" size="sm">
                      <Upload className="h-4 w-4 mr-2" />
                      Subir
                    </Button>
                  </div>
                  <p className="text-sm text-muted-foreground">
                    Formato .jpg recomendado
                  </p>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="archivoAudio">
                    Audio con la Voz del Autor
                  </Label>
                  <div className="flex items-center gap-4">
                    <Input
                      {...register("archivoAudio")}
                      placeholder="Enlace a archivo .mp3"
                    />
                    <Button type="button" variant="outline" size="sm">
                      <Upload className="h-4 w-4 mr-2" />
                      Subir
                    </Button>
                  </div>
                  <p className="text-sm text-muted-foreground">
                    Formato .mp3 recomendado
                  </p>
                </div>

                <div className="space-y-2">
                  <Label>Multimedia Adicional</Label>
                  <Textarea
                    placeholder="Otros recursos asociados, incluyendo enlace, tipo y restricciones de acceso"
                    rows={3}
                  />
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="asignacion" className="space-y-4">
          <Card>
            <CardContent className="pt-6">
              <div className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-2">
                    <Label htmlFor="editorId">Asignar Editor *</Label>
                    <Select>
                      <SelectTrigger>
                        <SelectValue placeholder="Selecciona editor" />
                      </SelectTrigger>
                      <SelectContent>
                        {mockUsuarios
                          .filter((u) => u.rol === "Editor")
                          .map((user) => (
                            <SelectItem key={user.id} value={user.id}>
                              {user.nombre} ({user.rol})
                            </SelectItem>
                          ))}
                      </SelectContent>
                    </Select>
                    {errors.editorId && (
                      <p className="text-sm text-red-500">
                        {errors.editorId.message}
                      </p>
                    )}
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="revisorId">Asignar Revisor *</Label>
                    <Select>
                      <SelectTrigger>
                        <SelectValue placeholder="Selecciona revisor" />
                      </SelectTrigger>
                      <SelectContent>
                        {mockUsuarios
                          .filter((u) => u.rol === "Revisor")
                          .map((user) => (
                            <SelectItem key={user.id} value={user.id}>
                              {user.nombre} ({user.rol})
                            </SelectItem>
                          ))}
                      </SelectContent>
                    </Select>
                    {errors.revisorId && (
                      <p className="text-sm text-red-500">
                        {errors.revisorId.message}
                      </p>
                    )}
                  </div>
                </div>

                <div className="bg-muted p-4 rounded-lg">
                  <h4 className="font-medium mb-2">
                    Instrucciones para el Editor
                  </h4>
                  <p className="text-sm text-muted-foreground">
                    El editor asignado deberá completar los 16 atributos
                    obligatorios de esta ficha antes de que pueda pasar a
                    revisión. El sistema notificará automáticamente al editor
                    sobre esta asignación.
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      <div className="flex justify-end gap-3 pt-4 border-t">
        <Button type="button" variant="outline">
          Cancelar
        </Button>
        <Button type="submit" disabled={isSubmitting}>
          {isSubmitting ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Guardando...
            </>
          ) : (
            <>
              <Save className="mr-2 h-4 w-4" />
              Guardar Ficha
            </>
          )}
        </Button>
        <Button type="button" variant="secondary">
          <CheckCircle className="mr-2 h-4 w-4" />
          Guardar y Asignar
        </Button>
      </div>
    </form>
  );
}
