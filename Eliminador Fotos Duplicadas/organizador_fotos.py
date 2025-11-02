#!/usr/bin/env python3
"""
ORGANIZADOR AUTOMÁTICO DE FOTOS v2.0
Procesa miles de fotos automáticamente sin límites
Por Claude - Gratis y sin restricciones
"""

import os
import shutil
import hashlib
from datetime import datetime
from pathlib import Path
import json
from collections import defaultdict

# Intentar importar librerías opcionales
try:
    from PIL import Image
    from PIL.ExifTags import TAGS
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("⚠️ PIL no instalada. Ejecuta: pip install Pillow")

try:
    import imagehash
    IMAGEHASH_AVAILABLE = True
except ImportError:
    IMAGEHASH_AVAILABLE = False
    print("⚠️ imagehash no instalado. Ejecuta: pip install imagehash")

class OrganizadorFotos:
    def __init__(self, carpeta_origen, carpeta_destino):
        self.carpeta_origen = Path(carpeta_origen)
        self.carpeta_destino = Path(carpeta_destino)
        self.estadisticas = {
            'total_procesadas': 0,
            'movidas_definitivas': 0,
            'duplicados_exactos': 0,
            'cuasi_duplicados': 0,
            'sin_fecha': 0,
            'calidad_dudosa': 0,
            'errores': 0
        }
        self.hashes_md5 = {}
        self.hashes_perceptuales = {}
        self.reporte = []
        
    def crear_estructura_carpetas(self):
        """Crea la estructura de carpetas necesaria"""
        carpetas = [
            self.carpeta_destino / "00_PENDIENTE_REVISION" / "DUPLICADOS_POR_CONFIRMAR",
            self.carpeta_destino / "00_PENDIENTE_REVISION" / "FOTOS_SIN_FECHA",
            self.carpeta_destino / "00_PENDIENTE_REVISION" / "CALIDAD_DUDOSA",
            self.carpeta_destino / "00_METADATOS_PROBLEMA"
        ]
        
        # Crear carpetas para cada mes del año
        meses = ['01_Enero', '02_Febrero', '03_Marzo', '04_Abril', '05_Mayo', '06_Junio',
                '07_Julio', '08_Agosto', '09_Septiembre', '10_Octubre', '11_Noviembre', '12_Diciembre']
        
        for año in range(2020, 2026):  # Ajusta según tus necesidades
            for mes in meses:
                carpetas.append(self.carpeta_destino / str(año) / mes)
        
        for carpeta in carpetas:
            carpeta.mkdir(parents=True, exist_ok=True)
            
        print("✅ Estructura de carpetas creada")
        
    def calcular_hash_md5(self, archivo):
        """Calcula el hash MD5 de un archivo"""
        hash_md5 = hashlib.md5()
        try:
            with open(archivo, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except:
            return None
            
    def obtener_fecha_foto(self, archivo):
        """Extrae la fecha de los metadatos EXIF o del archivo"""
        fecha = None
        
        if PIL_AVAILABLE:
            try:
                imagen = Image.open(archivo)
                exifdata = imagen.getexif()
                
                # Buscar fecha en EXIF
                for tag_id, value in exifdata.items():
                    tag = TAGS.get(tag_id, tag_id)
                    if tag in ['DateTime', 'DateTimeOriginal', 'DateTimeDigitized']:
                        try:
                            fecha = datetime.strptime(value, '%Y:%m:%d %H:%M:%S')
                            break
                        except:
                            continue
            except:
                pass
        
        # Si no hay fecha EXIF, usar fecha de modificación del archivo
        if not fecha:
            try:
                timestamp = os.path.getmtime(archivo)
                fecha = datetime.fromtimestamp(timestamp)
            except:
                return None
                
        return fecha
        
    def evaluar_calidad(self, archivo):
        """Evalúa la calidad técnica de la imagen"""
        if not PIL_AVAILABLE:
            return "OK"
            
        try:
            imagen = Image.open(archivo)
            ancho, alto = imagen.size
            
            # Criterios de calidad
            if ancho < 800 or alto < 600:
                return "BAJA_RESOLUCION"
            
            # Verificar tamaño del archivo (muy pequeño = baja calidad)
            tamaño_kb = os.path.getsize(archivo) / 1024
            if tamaño_kb < 50:
                return "MUY_COMPRIMIDA"
                
            return "OK"
        except:
            return "ERROR"
            
    def detectar_cuasi_duplicados(self, archivo):
        """Detecta imágenes similares usando hash perceptual"""
        if not PIL_AVAILABLE or not IMAGEHASH_AVAILABLE:
            return False
            
        try:
            imagen = Image.open(archivo)
            hash_perceptual = str(imagehash.average_hash(imagen))
            
            # Buscar hashes similares
            for archivo_existente, hash_existente in self.hashes_perceptuales.items():
                if archivo_existente != archivo:
                    diferencia = sum(c1 != c2 for c1, c2 in zip(hash_perceptual, hash_existente))
                    if diferencia <= 5:  # Umbral de similitud
                        return archivo_existente
                        
            self.hashes_perceptuales[archivo] = hash_perceptual
            return False
        except:
            return False
            
    def procesar_imagen(self, archivo):
        """Procesa una imagen individual"""
        archivo_path = Path(archivo)
        nombre_archivo = archivo_path.name
        
        print(f"📸 Procesando: {nombre_archivo}")
        self.estadisticas['total_procesadas'] += 1
        
        # 1. Calcular hash MD5 para detectar duplicados exactos
        hash_md5 = self.calcular_hash_md5(archivo)
        
        if hash_md5 and hash_md5 in self.hashes_md5:
            # Duplicado exacto encontrado
            self.estadisticas['duplicados_exactos'] += 1
            accion = f"❌ ELIMINAR (duplicado exacto de {self.hashes_md5[hash_md5]})"
            self.reporte.append({
                'archivo': nombre_archivo,
                'accion': 'ELIMINAR',
                'razon': f'Duplicado exacto de {self.hashes_md5[hash_md5]}'
            })
            print(f"   {accion}")
            return
            
        if hash_md5:
            self.hashes_md5[hash_md5] = nombre_archivo
            
        # 2. Detectar cuasi-duplicados
        cuasi_duplicado = self.detectar_cuasi_duplicados(archivo)
        if cuasi_duplicado:
            destino = self.carpeta_destino / "00_PENDIENTE_REVISION" / "DUPLICADOS_POR_CONFIRMAR" / nombre_archivo
            self.estadisticas['cuasi_duplicados'] += 1
            accion = f"⚠️  REVISAR: Posible duplicado de {cuasi_duplicado}"
            self.reporte.append({
                'archivo': nombre_archivo,
                'accion': 'REVISAR',
                'destino': str(destino),
                'razon': f'Cuasi-duplicado de {cuasi_duplicado}'
            })
            print(f"   {accion}")
            shutil.copy2(archivo, destino)
            return
            
        # 3. Obtener fecha de la foto
        fecha = self.obtener_fecha_foto(archivo)
        
        if not fecha:
            # Sin fecha - mover a revisión
            destino = self.carpeta_destino / "00_PENDIENTE_REVISION" / "FOTOS_SIN_FECHA" / nombre_archivo
            self.estadisticas['sin_fecha'] += 1
            accion = "📅 SIN FECHA: Moviendo a revisión"
            self.reporte.append({
                'archivo': nombre_archivo,
                'accion': 'REVISAR',
                'destino': str(destino),
                'razon': 'Sin metadatos de fecha'
            })
        else:
            # 4. Evaluar calidad
            calidad = self.evaluar_calidad(archivo)
            
            if calidad != "OK":
                destino = self.carpeta_destino / "00_PENDIENTE_REVISION" / "CALIDAD_DUDOSA" / nombre_archivo
                self.estadisticas['calidad_dudosa'] += 1
                accion = f"⚠️  CALIDAD: {calidad}"
                self.reporte.append({
                    'archivo': nombre_archivo,
                    'accion': 'REVISAR',
                    'destino': str(destino),
                    'razon': calidad
                })
            else:
                # Imagen OK - mover a carpeta definitiva
                meses = ['01_Enero', '02_Febrero', '03_Marzo', '04_Abril', '05_Mayo', '06_Junio',
                        '07_Julio', '08_Agosto', '09_Septiembre', '10_Octubre', '11_Noviembre', '12_Diciembre']
                
                año = fecha.year
                mes = meses[fecha.month - 1]
                destino = self.carpeta_destino / str(año) / mes / nombre_archivo
                self.estadisticas['movidas_definitivas'] += 1
                accion = f"✅ MOVER A: {año}/{mes}/"
                self.reporte.append({
                    'archivo': nombre_archivo,
                    'accion': 'CONSERVAR',
                    'destino': str(destino),
                    'fecha': fecha.strftime('%Y-%m-%d')
                })
                
        print(f"   {accion}")
        
        # Copiar archivo al destino
        try:
            destino.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(archivo, destino)
        except Exception as e:
            self.estadisticas['errores'] += 1
            print(f"   ❌ Error: {e}")
            
    def procesar_carpeta(self):
        """Procesa todas las imágenes de la carpeta origen"""
        extensiones_imagen = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.raw', '.heic']
        
        archivos = []
        for ext in extensiones_imagen:
            archivos.extend(self.carpeta_origen.glob(f'**/*{ext}'))
            archivos.extend(self.carpeta_origen.glob(f'**/*{ext.upper()}'))
            
        total = len(archivos)
        print(f"\n🎯 Encontradas {total} imágenes para procesar\n")
        
        for i, archivo in enumerate(archivos, 1):
            print(f"\n[{i}/{total}]", end=" ")
            self.procesar_imagen(archivo)
            
    def generar_reporte(self):
        """Genera el reporte final"""
        print("\n" + "="*60)
        print("📊 REPORTE FINAL DE ORGANIZACIÓN")
        print("="*60)
        
        print(f"""
📈 ESTADÍSTICAS:
   • Total procesadas: {self.estadisticas['total_procesadas']}
   • ✅ Movidas a definitivas: {self.estadisticas['movidas_definitivas']}
   • ❌ Duplicados exactos eliminados: {self.estadisticas['duplicados_exactos']}
   • ⚠️  Cuasi-duplicados (revisión): {self.estadisticas['cuasi_duplicados']}
   • 📅 Sin fecha (revisión): {self.estadisticas['sin_fecha']}
   • 📸 Calidad dudosa (revisión): {self.estadisticas['calidad_dudosa']}
   • ❗ Errores: {self.estadisticas['errores']}
        """)
        
        # Guardar reporte detallado en JSON
        reporte_path = self.carpeta_destino / "reporte_organizacion.json"
        with open(reporte_path, 'w', encoding='utf-8') as f:
            json.dump({
                'estadisticas': self.estadisticas,
                'detalles': self.reporte,
                'fecha_proceso': datetime.now().isoformat()
            }, f, indent=2, ensure_ascii=False)
            
        print(f"💾 Reporte detallado guardado en: {reporte_path}")

        
        
        # Crear archivo de resumen legible
        resumen_path = self.carpeta_destino / "RESUMEN_ORGANIZACION.txt"
        with open(resumen_path, 'w', encoding='utf-8') as f:
            f.write("RESUMEN DE ORGANIZACIÓN DE FOTOS\n")
            f.write("="*50 + "\n\n")
            f.write(f"Fecha de proceso: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write("ESTADÍSTICAS:\n")
            for key, value in self.estadisticas.items():
                f.write(f"  {key}: {value}\n")
            f.write("\n\nDETALLES POR ARCHIVO:\n")
            f.write("-"*50 + "\n")
            
            for item in self.reporte:
                f.write(f"\n📸 {item['archivo']}\n")
                f.write(f"   Acción: {item['accion']}\n")
                if 'destino' in item:
                    f.write(f"   Destino: {item['destino']}\n")
                if 'razon' in item:
                    f.write(f"   Razón: {item['razon']}\n")
                    
        print(f"📄 Resumen legible guardado en: {resumen_path}")
        
def main():
    print("""
╔══════════════════════════════════════════════════════╗
║     🖼️  ORGANIZADOR AUTOMÁTICO DE FOTOS v2.0  🖼️      ║
║         Procesa miles de fotos sin límites           ║
╚══════════════════════════════════════════════════════╝
    """)
    
    # Configurar rutas
    print("📁 CONFIGURACIÓN DE CARPETAS")
    print("-"*40)
    
    carpeta_origen = input("Ingresa la ruta de la carpeta con las fotos desordenadas: ").strip()
    if not carpeta_origen:
        carpeta_origen = "."  # Carpeta actual por defecto
        
    carpeta_destino = input("Ingresa la ruta donde quieres organizar las fotos: ").strip()
    if not carpeta_destino:
        carpeta_destino = "FOTOS_ORGANIZADAS"
        
    # Validar carpetas
    if not os.path.exists(carpeta_origen):
        print("❌ La carpeta origen no existe")
        return
        
    # Crear organizador
    organizador = OrganizadorFotos(carpeta_origen, carpeta_destino)
    
    print(f"\n✅ Carpeta origen: {carpeta_origen}")
    print(f"✅ Carpeta destino: {carpeta_destino}")
    
    # Preguntar si instalar dependencias
    if not PIL_AVAILABLE or not IMAGEHASH_AVAILABLE:
        print("\n⚠️  ATENCIÓN: Algunas funciones avanzadas requieren librerías adicionales")
        print("   Recomendado ejecutar: pip install Pillow imagehash")
        continuar = input("\n¿Continuar sin todas las funciones? (s/n): ").lower()
        if continuar != 's':
            print("\nInstala las librerías con: pip install Pillow imagehash")
            return
            
    # Ejecutar proceso
    print("\n🚀 INICIANDO PROCESO DE ORGANIZACIÓN...")
    print("-"*40)
    
    organizador.crear_estructura_carpetas()
    organizador.procesar_carpeta()
    organizador.generar_reporte()
    
    print("\n✨ ¡PROCESO COMPLETADO!")
    print(f"📁 Revisa tus fotos organizadas en: {carpeta_destino}")
    print("\n⚠️  IMPORTANTE: Revisa la carpeta '00_PENDIENTE_REVISION' para:")
    print("   • Confirmar/eliminar posibles duplicados")
    print("   • Asignar fechas a fotos sin metadatos")
    print("   • Revisar fotos de calidad dudosa")

if __name__ == "__main__":
    main()
