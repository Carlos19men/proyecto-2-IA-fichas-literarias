import os
import hashlib
from datetime import datetime
from typing import Any, Dict, List, Optional
from neo4j import Session

from src.database.connection import db
from src.ingestion.schemas import (
    FichaLiterariaSchema,
    AutorSchema,
    ObraSchema,
    CriticaSchema,
    AgrupacionSchema,
    RevistaSchema,
    AntologiaSchema,
    MitoLeyendaSchema,
    Multimedia,
    Persona
)
from src.config import Config

try:
    from langchain_ollama import OllamaEmbeddings
except ImportError:
    OllamaEmbeddings = None


class FichaUploader:
    """
    Clase para subir el esquema estructurado de FichaLiterariaSchema a Neo4j.
    Genera embeddings vectoriales de forma tolerante a fallos y mantiene la
    consistencia del grafo literario mediante el uso de MERGE parametrizado.
    """

    def __init__(self):
        self.db = db
        self.embeddings = None
        
        # Inicializar generador de embeddings si langchain_ollama está instalado
        if OllamaEmbeddings:
            try:
                embedding_model = os.getenv("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text")
                self.embeddings = OllamaEmbeddings(
                    model=embedding_model,
                    base_url=Config.OLLAMA_BASE_URL
                )
                print(f"[uploader] Conectado a Ollama para embeddings en {Config.OLLAMA_BASE_URL} (modelo: {embedding_model})")
            except Exception as e:
                print(f"[uploader] AVISO: No se pudo inicializar OllamaEmbeddings. Se omitira la generacion de vectores: {e}")
        else:
            print("[uploader] AVISO: Paquete 'langchain_ollama' no disponible. Los campos vectoriales se omitiran.")

    def generar_id(self, prefijo: str, texto: str) -> str:
        """Genera un identificador único determinista a partir de un texto."""
        texto_limpio = "".join(c for c in texto if c.isalnum() or c == "_").lower()
        hash_val = hashlib.md5(texto.encode("utf-8")).hexdigest()[:8]
        return f"{prefijo}_{texto_limpio[:20]}_{hash_val}".upper()

    def generar_embedding(self, texto: Optional[str]) -> Optional[List[float]]:
        """Genera un embedding de 768 dimensiones para el texto dado de forma segura."""
        if not self.embeddings or not texto or not texto.strip():
            return None
        try:
            return self.embeddings.embed_query(texto)
        except Exception as e:
            print(f"[uploader] AVISO: Error al generar embedding para '{texto[:25]}...': {e}")
            return None

    def subir_ficha(self, ficha: FichaLiterariaSchema) -> bool:
        """
        Método principal para subir una ficha completa a Neo4j.
        Maneja la sesión y transacciones correspondientes.
        """
        if not self.db.test_connection():
            print("[uploader] Cancelando subida: Neo4j no responde.")
            return False

        try:
            with self.db.driver.session() as session:
                print(f"\n[uploader] Iniciando carga del grafo para el autor: {ficha.autor.nombres} {ficha.autor.apellidos}")
                
                # 1. Cargar Autor
                autor_id = self._subir_autor(session, ficha.autor)
                print(f"   [uploader] Autor subido: {ficha.autor.nombres} {ficha.autor.apellidos} (ID: {autor_id})")

                # 2. Cargar Obras escritas por el Autor
                obras_ids = []
                for obra in ficha.autor.obras:
                    obra_id = self._subir_obra(session, autor_id, obra)
                    obras_ids.append(obra_id)
                print(f"   [uploader] {len(obras_ids)} Obras insertadas/actualizadas y enlazadas.")

                # 3. Cargar Críticas literarias
                criticas_ids = []
                for critica in ficha.autor.criticas:
                    critica_id = self._subir_critica(session, autor_id, obras_ids, critica)
                    criticas_ids.append(critica_id)
                print(f"   [uploader] {len(criticas_ids)} Criticas asociadas e indexadas semanticamente.")

                # 4. Cargar Agrupaciones literarias
                for agrupacion in ficha.agrupaciones:
                    agrupacion_id = self._subir_agrupacion(session, autor_id, agrupacion)
                    print(f"   [uploader] Agrupacion cargada: {agrupacion.nombre} (ID: {agrupacion_id})")

                # 5. Cargar Revistas
                for revista in ficha.revistas:
                    revista_id = self._subir_revista(session, autor_id, obras_ids, revista)
                    print(f"   [uploader] Revista cargada: {revista.titulo} (ID: {revista_id})")

                # 6. Cargar Antologías
                for antologia in ficha.antologias:
                    antologia_id = self._subir_antologia(session, autor_id, obras_ids, antologia)
                    print(f"   [uploader] Antologia cargada: {antologia.titulo} (ID: {antologia_id})")

                # 7. Cargar Mitos y Leyendas relacionados
                for mito in ficha.mitos_leyendas:
                    mito_id = self._subir_mito_leyenda(session, autor_id, mito)
                    print(f"   [uploader] Mito/Leyenda cargado: {mito.titulo} (ID: {mito_id})")

                print(f"[uploader] Ingesta de la ficha para '{ficha.autor.nombres} {ficha.autor.apellidos}' completada exitosamente.")
                return True

        except Exception as e:
            print(f"[uploader] Error en la transaccion de Neo4j: {e}")
            import traceback
            traceback.print_exc()
            return False

    def _subir_autor(self, session: Session, autor: AutorSchema) -> str:
        autor_id = self.generar_id("AUTOR", f"{autor.nombres}_{autor.apellidos}")
        
        # Generar texto biográfico para el vector de búsqueda semántica
        bio_texto = f"{autor.nombres} {autor.apellidos}. "
        if autor.seudonimo:
            bio_texto += f"Conocido como {autor.seudonimo}. "
        if autor.actividad_relevante:
            bio_texto += f"{autor.actividad_relevante} "
        if autor.contexto_vivio:
            bio_texto += f"Vivio en el contexto: {autor.contexto_vivio} "
        if autor.tematica_principal:
            bio_texto += f"Temas principales: {autor.tematica_principal} "
        
        embedding = self.generar_embedding(bio_texto)
        nombre_completo = autor.nombre_completo or f"{autor.nombres} {autor.apellidos}"

        cypher = """
        MERGE (a:Autor {nombres: $nombres})
        ON CREATE SET
            a.fichaId = $fichaId,
            a.apellidos = $apellidos,
            a.nombre_completo = $nombre_completo,
            a.sexo = $sexo,
            a.seudonimo = $seudonimo,
            a.fecha_nacimiento = $fecha_nacimiento,
            a.fecha_fallecimiento = $fecha_fallecimiento,
            a.lugar_nacimiento_ciudad = $lugar_nacimiento_ciudad,
            a.lugar_nacimiento_municipio = $lugar_nacimiento_municipio,
            a.lugar_nacimiento_estado = $lugar_nacimiento_estado,
            a.lugar_nacimiento_pais = $lugar_nacimiento_pais,
            a.lugar_fallecimiento_ciudad = $lugar_fallecimiento_ciudad,
            a.lugar_fallecimiento_municipio = $lugar_fallecimiento_municipio,
            a.lugar_fallecimiento_estado = $lugar_fallecimiento_estado,
            a.lugar_fallecimiento_pais = $lugar_fallecimiento_pais,
            a.actividad_relevante = $actividad_relevante,
            a.contexto_vivio = $contexto_vivio,
            a.tematica_principal = $tematica_principal,
            a.genero_principal = $genero_principal,
            a.imagen_autor = $imagen_autor,
            a.audio_voz = $audio_voz,
            a.embedding = $embedding,
            a.timestamp = datetime()
        ON MATCH SET
            a.fichaId = $fichaId,
            a.apellidos = $apellidos,
            a.nombre_completo = $nombre_completo,
            a.sexo = $sexo,
            a.seudonimo = $seudonimo,
            a.fecha_nacimiento = $fecha_nacimiento,
            a.fecha_fallecimiento = $fecha_fallecimiento,
            a.lugar_nacimiento_ciudad = $lugar_nacimiento_ciudad,
            a.lugar_nacimiento_municipio = $lugar_nacimiento_municipio,
            a.lugar_nacimiento_estado = $lugar_nacimiento_estado,
            a.lugar_nacimiento_pais = $lugar_nacimiento_pais,
            a.lugar_fallecimiento_ciudad = $lugar_fallecimiento_ciudad,
            a.lugar_fallecimiento_municipio = $lugar_fallecimiento_municipio,
            a.lugar_fallecimiento_estado = $lugar_fallecimiento_estado,
            a.lugar_fallecimiento_pais = $lugar_fallecimiento_pais,
            a.actividad_relevante = $actividad_relevante,
            a.contexto_vivio = $contexto_vivio,
            a.tematica_principal = $tematica_principal,
            a.genero_principal = $genero_principal,
            a.imagen_autor = $imagen_autor,
            a.audio_voz = $audio_voz,
            a.embedding = $embedding,
            a.timestamp = datetime()
        RETURN a.fichaId AS autorId
        """

        session.run(
            cypher,
            fichaId=autor_id,
            nombres=autor.nombres,
            apellidos=autor.apellidos,
            nombre_completo=nombre_completo,
            sexo=autor.sexo,
            seudonimo=autor.seudonimo,
            fecha_nacimiento=autor.fecha_nacimiento,
            fecha_fallecimiento=autor.fecha_fallecimiento,
            lugar_nacimiento_ciudad=autor.lugar_nacimiento.ciudad if autor.lugar_nacimiento else None,
            lugar_nacimiento_municipio=autor.lugar_nacimiento.municipio if autor.lugar_nacimiento else None,
            lugar_nacimiento_estado=autor.lugar_nacimiento.estado if autor.lugar_nacimiento else None,
            lugar_nacimiento_pais=autor.lugar_nacimiento.pais if autor.lugar_nacimiento else None,
            lugar_fallecimiento_ciudad=autor.lugar_fallecimiento.ciudad if autor.lugar_fallecimiento else None,
            lugar_fallecimiento_municipio=autor.lugar_fallecimiento.municipio if autor.lugar_fallecimiento else None,
            lugar_fallecimiento_estado=autor.lugar_fallecimiento.estado if autor.lugar_fallecimiento else None,
            lugar_fallecimiento_pais=autor.lugar_fallecimiento.pais if autor.lugar_fallecimiento else None,
            actividad_relevante=autor.actividad_relevante,
            contexto_vivio=autor.contexto_vivio,
            tematica_principal=autor.tematica_principal,
            genero_principal=autor.genero_principal,
            imagen_autor=autor.imagen_autor,
            audio_voz=autor.audio_voz,
            embedding=embedding
        )

        # Cargar familiares destacados
        for fam in autor.familiares_destacados:
            self._subir_familiar(session, autor_id, fam)

        # Cargar recursos multimedia del autor
        for mult in autor.multimedia:
            self._subir_multimedia(session, autor_id, "Autor", mult)

        return autor_id

    def _subir_familiar(self, session: Session, autor_id: str, fam: Persona):
        """Crea nodos de Persona para familiares y los relaciona con el Autor."""
        if not fam.nombres:
            return
        
        nombre_completo = f"{fam.nombres} {fam.apellidos or ''}".strip()
        cypher = """
        MATCH (a:Autor {fichaId: $autorId})
        MERGE (p:Persona {nombre_completo: $nombre_completo})
        ON CREATE SET
            p.nombres = $nombres,
            p.apellidos = $apellidos
        MERGE (a)-[r:TIENE_FAMILIAR]->(p)
        SET r.rol = $rol
        """
        session.run(
            cypher,
            autorId=autor_id,
            nombre_completo=nombre_completo,
            nombres=fam.nombres,
            apellidos=fam.apellidos,
            rol=fam.rol or "Familiar"
        )

    def _subir_obra(self, session: Session, autor_id: str, obra: ObraSchema) -> str:
        obra_id = self.generar_id("OBRA", obra.titulo)

        cypher = """
        MATCH (a:Autor {fichaId: $autorId})
        MERGE (o:Obra {titulo: $titulo})
        ON CREATE SET
            o.fichaId = $fichaId,
            o.genero = $genero,
            o.subgenero = $subgenero,
            o.fecha_publicacion = $fecha_publicacion,
            o.lugar_publicacion_ciudad = $lugar_publicacion_ciudad,
            o.lugar_publicacion_municipio = $lugar_publicacion_municipio,
            o.lugar_publicacion_estado = $lugar_publicacion_estado,
            o.lugar_publicacion_pais = $lugar_publicacion_pais,
            o.editorial = $editorial,
            o.descripcion = $descripcion,
            o.idioma_original = $idioma_original
        ON MATCH SET
            o.fichaId = $fichaId,
            o.genero = $genero,
            o.subgenero = $subgenero,
            o.fecha_publicacion = $fecha_publicacion,
            o.lugar_publicacion_ciudad = $lugar_publicacion_ciudad,
            o.lugar_publicacion_municipio = $lugar_publicacion_municipio,
            o.lugar_publicacion_estado = $lugar_publicacion_estado,
            o.lugar_publicacion_pais = $lugar_publicacion_pais,
            o.editorial = $editorial,
            o.descripcion = $descripcion,
            o.idioma_original = $idioma_original
        MERGE (a)-[:ESCRIBIO]->(o)
        RETURN o.fichaId AS obraId
        """

        session.run(
            cypher,
            autorId=autor_id,
            fichaId=obra_id,
            titulo=obra.titulo,
            genero=obra.genero,
            subgenero=obra.subgenero,
            fecha_publicacion=obra.fecha_publicacion,
            lugar_publicacion_ciudad=obra.lugar_publicacion.ciudad if obra.lugar_publicacion else None,
            lugar_publicacion_municipio=obra.lugar_publicacion.municipio if obra.lugar_publicacion else None,
            lugar_publicacion_estado=obra.lugar_publicacion.estado if obra.lugar_publicacion else None,
            lugar_publicacion_pais=obra.lugar_publicacion.pais if obra.lugar_publicacion else None,
            editorial=obra.editorial,
            descripcion=obra.descripcion,
            idioma_original=obra.idioma_original
        )

        # Cargar multimedia asociada a la obra
        for mult in obra.multimedia:
            self._subir_multimedia(session, obra_id, "Obra", mult)

        return obra_id

    def _subir_critica(self, session: Session, autor_id: str, obras_ids: List[str], critica: CriticaSchema) -> str:
        critica_id = self.generar_id("CRITICA", critica.titulo)

        # Generar embedding vectorial para la búsqueda semántica
        embedding_texto = f"{critica.titulo}. {critica.descripcion_resumen or ''} de {critica.autor}"
        embedding = self.generar_embedding(embedding_texto)

        cypher_critica = """
        MATCH (a:Autor {fichaId: $autorId})
        MERGE (c:Critica {fichaId: $fichaId})
        ON CREATE SET
            c.tipo = $tipo,
            c.autor_critica = $autor_critica,
            c.titulo = $titulo,
            c.fecha_publicacion = $fecha_publicacion,
            c.referencia_bibliografica = $referencia_bibliografica,
            c.descripcion_resumen = $descripcion_resumen,
            c.embedding = $embedding
        ON MATCH SET
            c.tipo = $tipo,
            c.autor_critica = $autor_critica,
            c.titulo = $titulo,
            c.fecha_publicacion = $fecha_publicacion,
            c.referencia_bibliografica = $referencia_bibliografica,
            c.descripcion_resumen = $descripcion_resumen,
            c.embedding = $embedding
        MERGE (c)-[:CRITICA_DE]->(a)
        RETURN c.fichaId AS criticaId
        """

        session.run(
            cypher_critica,
            autorId=autor_id,
            fichaId=critica_id,
            tipo=critica.tipo,
            autor_critica=critica.autor,
            titulo=critica.titulo,
            fecha_publicacion=critica.fecha_publicacion,
            referencia_bibliografica=critica.referencia_bibliografica,
            descripcion_resumen=critica.descripcion_resumen,
            embedding=embedding
        )

        # Intentar conectar con la Obra a la que hace crítica si se menciona el título en el texto de la crítica
        for obra_id in obras_ids:
            cypher_relacion = """
            MATCH (c:Critica {fichaId: $criticaId})
            MATCH (o:Obra {fichaId: $obraId})
            WHERE toLower(c.titulo) CONTAINS toLower(o.titulo) 
               OR toLower(c.descripcion_resumen) CONTAINS toLower(o.titulo)
               OR toLower(c.referencia_bibliografica) CONTAINS toLower(o.titulo)
            MERGE (c)-[:CRITICA_DE]->(o)
            """
            session.run(cypher_relacion, criticaId=critica_id, obraId=obra_id)

        return critica_id

    def _subir_agrupacion(self, session: Session, autor_id: str, agrupacion: AgrupacionSchema) -> str:
        agrupacion_id = self.generar_id("AGRUPACION", agrupacion.nombre)

        cypher = """
        MATCH (a:Autor {fichaId: $autorId})
        MERGE (ag:Agrupacion {nombre: $nombre})
        ON CREATE SET
            ag.fichaId = $fichaId,
            ag.lugar_encuentros_ciudad = $lugar_encuentros_ciudad,
            ag.lugar_encuentros_municipio = $lugar_encuentros_municipio,
            ag.lugar_encuentros_estado = $lugar_encuentros_estado,
            ag.lugar_encuentros_pais = $lugar_encuentros_pais,
            ag.fecha_inicio = $fecha_inicio,
            ag.fecha_culminacion = $fecha_culminacion,
            ag.caracteristica_general = $caracteristica_general,
            ag.actividades = $actividades
        ON MATCH SET
            ag.fichaId = $fichaId,
            ag.lugar_encuentros_ciudad = $lugar_encuentros_ciudad,
            ag.lugar_encuentros_municipio = $lugar_encuentros_municipio,
            ag.lugar_encuentros_estado = $lugar_encuentros_estado,
            ag.lugar_encuentros_pais = $lugar_encuentros_pais,
            ag.fecha_inicio = $fecha_inicio,
            ag.fecha_culminacion = $fecha_culminacion,
            ag.caracteristica_general = $caracteristica_general,
            ag.actividades = $actividades
        MERGE (a)-[:PERTENECE_A]->(ag)
        RETURN ag.fichaId AS agrupacionId
        """

        session.run(
            cypher,
            autorId=autor_id,
            fichaId=agrupacion_id,
            nombre=agrupacion.nombre,
            lugar_encuentros_ciudad=agrupacion.lugar_encuentros.ciudad if agrupacion.lugar_encuentros else None,
            lugar_encuentros_municipio=agrupacion.lugar_encuentros.municipio if agrupacion.lugar_encuentros else None,
            lugar_encuentros_estado=agrupacion.lugar_encuentros.estado if agrupacion.lugar_encuentros else None,
            lugar_encuentros_pais=agrupacion.lugar_encuentros.pais if agrupacion.lugar_encuentros else None,
            fecha_inicio=agrupacion.fecha_inicio,
            fecha_culminacion=agrupacion.fecha_culminacion,
            caracteristica_general=agrupacion.caracteristica_general,
            actividades=agrupacion.actividades
        )

        # Cargar integrantes
        for intg in agrupacion.integrantes:
            if not intg.nombres:
                continue
            nombre_completo = f"{intg.nombres} {intg.apellidos or ''}".strip()
            cypher_intg = """
            MATCH (ag:Agrupacion {fichaId: $agrupacionId})
            MERGE (p:Persona {nombre_completo: $nombre_completo})
            ON CREATE SET
                p.nombres = $nombres,
                p.apellidos = $apellidos
            MERGE (p)-[r:PERTENECE_A]->(ag)
            SET r.rol = $rol
            """
            session.run(
                cypher_intg,
                agrupacionId=agrupacion_id,
                nombre_completo=nombre_completo,
                nombres=intg.nombres,
                apellidos=intg.apellidos,
                rol=intg.rol or "Integrante"
            )

        # Cargar publicaciones de la agrupación
        for pub in agrupacion.publicaciones:
            cypher_pub = """
            MATCH (ag:Agrupacion {fichaId: $agrupacionId})
            MERGE (p:PublicacionAgrupacion {titulo: $titulo, anio: $anio})
            ON CREATE SET
                p.resumen = $resumen
            MERGE (ag)-[:PUBLICO]->(p)
            """
            session.run(
                cypher_pub,
                agrupacionId=agrupacion_id,
                titulo=pub.titulo,
                anio=pub.anio,
                resumen=pub.resumen
            )

        return agrupacion_id

    def _subir_revista(self, session: Session, autor_id: str, obras_ids: List[str], revista: RevistaSchema) -> str:
        revista_id = self.generar_id("REVISTA", revista.titulo)

        cypher = """
        MERGE (r:Revista {titulo: $titulo})
        ON CREATE SET
            r.fichaId = $fichaId,
            r.fecha_primer_numero = $fecha_primer_numero,
            r.fecha_ultimo_numero = $fecha_ultimo_numero,
            r.numeros_publicados = $numeros_publicados,
            r.lugar_publicacion_ciudad = $lugar_publicacion_ciudad,
            r.lugar_publicacion_municipio = $lugar_publicacion_municipio,
            r.lugar_publicacion_estado = $lugar_publicacion_estado,
            r.lugar_publicacion_pais = $lugar_publicacion_pais,
            r.editorial = $editorial,
            r.secciones = $secciones,
            r.descripcion = $descripcion,
            r.idioma_original = $idioma_original
        ON MATCH SET
            r.fichaId = $fichaId,
            r.fecha_primer_numero = $fecha_primer_numero,
            r.fecha_ultimo_numero = $fecha_ultimo_numero,
            r.numeros_publicados = $numeros_publicados,
            r.lugar_publicacion_ciudad = $lugar_publicacion_ciudad,
            r.lugar_publicacion_municipio = $lugar_publicacion_municipio,
            r.lugar_publicacion_estado = $lugar_publicacion_estado,
            r.lugar_publicacion_pais = $lugar_publicacion_pais,
            r.editorial = $editorial,
            r.secciones = $secciones,
            r.descripcion = $descripcion,
            r.idioma_original = $idioma_original
        RETURN r.fichaId AS revistaId
        """

        session.run(
            cypher,
            fichaId=revista_id,
            titulo=revista.titulo,
            fecha_primer_numero=revista.fecha_primer_numero,
            fecha_ultimo_numero=revista.fecha_ultimo_numero,
            numeros_publicados=revista.numeros_publicados,
            lugar_publicacion_ciudad=revista.lugar_publicacion.ciudad if revista.lugar_publicacion else None,
            lugar_publicacion_municipio=revista.lugar_publicacion.municipio if revista.lugar_publicacion else None,
            lugar_publicacion_estado=revista.lugar_publicacion.estado if revista.lugar_publicacion else None,
            lugar_publicacion_pais=revista.lugar_publicacion.pais if revista.lugar_publicacion else None,
            editorial=revista.editorial,
            secciones=revista.secciones,
            descripcion=revista.descripcion,
            idioma_original=revista.idioma_original
        )

        # Relacionar el Autor como colaborador o fundador de la revista
        cypher_rel_autor = """
        MATCH (a:Autor {fichaId: $autorId})
        MATCH (r:Revista {fichaId: $revistaId})
        MERGE (a)-[:COLABORO_EN]->(r)
        """
        session.run(cypher_rel_autor, autorId=autor_id, revistaId=revista_id)

        # Cargar los creadores / editores de la revista
        for creador in revista.creadores:
            if not creador.nombres:
                continue
            nombre_completo = f"{creador.nombres} {creador.apellidos or ''}".strip()
            cypher_creador = """
            MATCH (r:Revista {fichaId: $revistaId})
            MERGE (p:Persona {nombre_completo: $nombre_completo})
            ON CREATE SET
                p.nombres = $nombres,
                p.apellidos = $apellidos
            MERGE (p)-[rel:CREO]->(r)
            SET rel.rol = $rol
            """
            session.run(
                cypher_creador,
                revistaId=revista_id,
                nombre_completo=nombre_completo,
                nombres=creador.nombres,
                apellidos=creador.apellidos,
                rol=creador.rol or "Creador"
            )

        # Relacionar la Revista con las Obras publicadas en ella (búsqueda de coincidencia)
        for obra_id in obras_ids:
            cypher_rel_obra = """
            MATCH (r:Revista {fichaId: $revistaId})
            MATCH (o:Obra {fichaId: $obraId})
            WHERE toLower(r.descripcion) CONTAINS toLower(o.titulo) 
               OR toLower(r.secciones) CONTAINS toLower(o.titulo)
            MERGE (r)-[:PUBLICA]->(o)
            """
            session.run(cypher_rel_obra, revistaId=revista_id, obraId=obra_id)

        # Cargar recursos multimedia
        for mult in revista.multimedia:
            self._subir_multimedia(session, revista_id, "Revista", mult)

        return revista_id

    def _subir_antologia(self, session: Session, autor_id: str, obras_ids: List[str], antologia: AntologiaSchema) -> str:
        antologia_id = self.generar_id("ANTOLOGIA", antologia.titulo)

        cypher = """
        MERGE (an:Antologia {titulo: $titulo})
        ON CREATE SET
            an.fichaId = $fichaId,
            an.autor = $autor,
            an.genero = $genero,
            an.fecha_publicacion = $fecha_publicacion,
            an.lugar_publicacion_ciudad = $lugar_publicacion_ciudad,
            an.lugar_publicacion_municipio = $lugar_publicacion_municipio,
            an.lugar_publicacion_estado = $lugar_publicacion_estado,
            an.lugar_publicacion_pais = $lugar_publicacion_pais,
            an.editorial = $editorial,
            an.descripcion = $descripcion,
            an.idioma_original = $idioma_original
        ON MATCH SET
            an.fichaId = $fichaId,
            an.autor = $autor,
            an.genero = $genero,
            an.fecha_publicacion = $fecha_publicacion,
            an.lugar_publicacion_ciudad = $lugar_publicacion_ciudad,
            an.lugar_publicacion_municipio = $lugar_publicacion_municipio,
            an.lugar_publicacion_estado = $lugar_publicacion_estado,
            an.lugar_publicacion_pais = $lugar_publicacion_pais,
            an.editorial = $editorial,
            an.descripcion = $descripcion,
            an.idioma_original = $idioma_original
        RETURN an.fichaId AS antologiaId
        """

        session.run(
            cypher,
            fichaId=antologia_id,
            titulo=antologia.titulo,
            autor=antologia.autor,
            genero=antologia.genero,
            fecha_publicacion=antologia.fecha_publicacion,
            lugar_publicacion_ciudad=antologia.lugar_publicacion.ciudad if antologia.lugar_publicacion else None,
            lugar_publicacion_municipio=antologia.lugar_publicacion.municipio if antologia.lugar_publicacion else None,
            lugar_publicacion_estado=antologia.lugar_publicacion.estado if antologia.lugar_publicacion else None,
            lugar_publicacion_pais=antologia.lugar_publicacion.pais if antologia.lugar_publicacion else None,
            editorial=antologia.editorial,
            descripcion=antologia.descripcion,
            idioma_original=antologia.idioma_original
        )

        # Relacionar el autor con la Antología:
        # Si el autor principal es compilador de la antología o si aparece en la descripción
        cypher_rel_autor = """
        MATCH (a:Autor {fichaId: $autorId})
        MATCH (an:Antologia {fichaId: $antologiaId})
        MERGE (an)-[:CONTIENE_OBRAS_DE]->(a)
        """
        session.run(cypher_rel_autor, autorId=autor_id, antologiaId=antologia_id)

        # Conectar las Obras que contiene la Antología
        for obra_id in obras_ids:
            cypher_rel_obra = """
            MATCH (an:Antologia {fichaId: $antologiaId})
            MATCH (o:Obra {fichaId: $obraId})
            WHERE toLower(an.descripcion) CONTAINS toLower(o.titulo)
            MERGE (an)-[:CONTIENE]->(o)
            """
            session.run(cypher_rel_obra, antologiaId=antologia_id, obraId=obra_id)

        # Cargar recursos multimedia
        for mult in antologia.multimedia:
            self._subir_multimedia(session, antologia_id, "Antologia", mult)

        return antologia_id

    def _subir_mito_leyenda(self, session: Session, autor_id: str, mito: MitoLeyendaSchema) -> str:
        mito_id = self.generar_id("MITO", mito.titulo)

        cypher = """
        MATCH (a:Autor {fichaId: $autorId})
        MERGE (ml:MitoLeyenda {titulo: $titulo})
        ON CREATE SET
            ml.fichaId = $fichaId,
            ml.comunidad_creadora = $comunidad_creadora,
            ml.lugar_difusion_ciudad = $lugar_difusion_ciudad,
            ml.lugar_difusion_municipio = $lugar_difusion_municipio,
            ml.lugar_difusion_estado = $lugar_difusion_estado,
            ml.lugar_difusion_pais = $lugar_difusion_pais,
            ml.idioma_original = $idioma_original,
            ml.texto_completo = $texto_completo,
            ml.tema_principal = $tema_principal,
            ml.descripcion = $descripcion
        ON MATCH SET
            ml.fichaId = $fichaId,
            ml.comunidad_creadora = $comunidad_creadora,
            ml.lugar_difusion_ciudad = $lugar_difusion_ciudad,
            ml.lugar_difusion_municipio = $lugar_difusion_municipio,
            ml.lugar_difusion_estado = $lugar_difusion_estado,
            ml.lugar_difusion_pais = $lugar_difusion_pais,
            ml.idioma_original = $idioma_original,
            ml.texto_completo = $texto_completo,
            ml.tema_principal = $tema_principal,
            ml.descripcion = $descripcion
        MERGE (a)-[:RELACIONADO_CON]->(ml)
        RETURN ml.fichaId AS mitoId
        """

        session.run(
            cypher,
            autorId=autor_id,
            fichaId=mito_id,
            titulo=mito.titulo,
            comunidad_creadora=mito.comunidad_creadora,
            lugar_difusion_ciudad=mito.lugar_difusion.ciudad if mito.lugar_difusion else None,
            lugar_difusion_municipio=mito.lugar_difusion.municipio if mito.lugar_difusion else None,
            lugar_difusion_estado=mito.lugar_difusion.estado if mito.lugar_difusion else None,
            lugar_difusion_pais=mito.lugar_difusion.pais if mito.lugar_difusion else None,
            idioma_original=mito.idioma_original,
            texto_completo=mito.texto_completo,
            tema_principal=mito.tema_principal,
            descripcion=mito.descripcion
        )

        # Cargar recursos multimedia
        for mult in mito.multimedia:
            self._subir_multimedia(session, mito_id, "MitoLeyenda", mult)

        return mito_id

    def _subir_multimedia(self, session: Session, parent_id: str, parent_label: str, mult: Multimedia):
        """Inserta un nodo de Multimedia y lo relaciona con su entidad correspondiente."""
        if not mult.enlace:
            return
        
        mult_id = self.generar_id("MULTIMEDIA", mult.enlace)
        
        # Generar embedding vectorial para recursos multimedia
        embedding_texto = f"{mult.tipo} en enlace {mult.enlace}. Acceso {mult.restriccion or 'publico'}"
        embedding = self.generar_embedding(embedding_texto)

        cypher_mult = """
        MERGE (m:Multimedia {enlace: $enlace})
        ON CREATE SET
            m.fichaId = $fichaId,
            m.tipo = $tipo,
            m.restriccion = $restriccion,
            m.embedding = $embedding
        ON MATCH SET
            m.fichaId = $fichaId,
            m.tipo = $tipo,
            m.restriccion = $restriccion,
            m.embedding = $embedding
        RETURN m.fichaId AS multimediaId
        """
        session.run(
            cypher_mult,
            enlace=mult.enlace,
            fichaId=mult_id,
            tipo=mult.tipo,
            restriccion=mult.restriccion,
            embedding=embedding
        )

        # Crear relación (Multimedia)-[:ASOCIADA_A]->(Entidad)
        cypher_rel = f"""
        MATCH (p:{parent_label} {{fichaId: $parentId}})
        MATCH (m:Multimedia {{fichaId: $multimediaId}})
        MERGE (m)-[:ASOCIADA_A]->(p)
        """
        session.run(cypher_rel, parentId=parent_id, multimediaId=mult_id)
