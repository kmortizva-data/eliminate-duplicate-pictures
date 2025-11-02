#!/usr/bin/env python3
"""
ANALIZADOR DE RESULTADOS - Estadísticas de fotos organizadas
Ejecutar DESPUÉS de organizar las fotos
"""

import os
from pathlib import Path
from collections import defaultdict

def analizar_carpeta_organizada(carpeta_path):
    """Analiza la distribución de fotos en la carpeta organizada"""
    carpeta = Path(carpeta_path)
    
    if not carpeta.exists():
        print(f"❌ La carpeta {carpeta_path} no existe")
        return
    
    print(f"\n{'='*60}")
    print(f"📊 ANÁLISIS DE: {carpeta_path}")
    print(f"{'='*60}")
    
    # Contar fotos por año y mes
    distribucion = defaultdict(lambda: defaultdict(int))
    total_fotos = 0
    
    # Buscar carpetas de años (nombres numéricos)
    for año_carpeta in sorted(carpeta.glob("[0-9]*")):
        if año_carpeta.is_dir():
            año = año_carpeta.name
            for mes_carpeta in sorted(año_carpeta.glob("*")):
                if mes_carpeta.is_dir():
                    # Contar archivos de imagen
                    extensiones = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff']
                    cantidad = 0
                    for ext in extensiones:
                        cantidad += len(list(mes_carpeta.glob(f"*{ext}")))
                        cantidad += len(list(mes_carpeta.glob(f"*{ext.upper()}")))
                    
                    if cantidad > 0:
                        distribucion[año][mes_carpeta.name] = cantidad
                        total_fotos += cantidad
    
    if total_fotos == 0:
        print("⚠️ No se encontraron fotos organizadas por año/mes")
    else:
        print(f"\n📷 TOTAL DE FOTOS ORGANIZADAS: {total_fotos:,}")
        print(f"\n{'='*40}")
        print("📅 DISTRIBUCIÓN POR AÑO")
        print(f"{'='*40}")
        
        # Estadísticas por año
        años_con_fotos = []
        for año in sorted(distribucion.keys()):
            total_año = sum(distribucion[año].values())
            porcentaje = (total_año / total_fotos) * 100
            años_con_fotos.append((año, total_año, porcentaje))
            
            print(f"\n🗓️ AÑO {año}")
            print(f"   Total: {total_año:,} fotos ({porcentaje:.1f}%)")
            
            # Gráfico de barras simple
            barra_size = int(porcentaje / 2)  # Escala para que quepa en pantalla
            barra = "█" * barra_size
            print(f"   {barra}")
            
            # Top 3 meses
            meses_ordenados = sorted(distribucion[año].items(), 
                                    key=lambda x: x[1], reverse=True)[:3]
            
            if meses_ordenados:
                print(f"   📈 Top 3 meses con más fotos:")
                for i, (mes, cantidad) in enumerate(meses_ordenados, 1):
                    porcentaje_mes = (cantidad / total_año) * 100
                    medalla = "🥇" if i == 1 else "🥈" if i == 2 else "🥉"
                    print(f"      {medalla} {mes}: {cantidad:,} fotos ({porcentaje_mes:.1f}%)")
        
        # Resumen general
        print(f"\n{'='*40}")
        print("📊 RESUMEN GENERAL")
        print(f"{'='*40}")
        
        # Top 3 años
        años_ordenados = sorted(años_con_fotos, key=lambda x: x[1], reverse=True)[:3]
        print("\n🏆 TOP 3 AÑOS CON MÁS FOTOS:")
        for i, (año, cantidad, porcentaje) in enumerate(años_ordenados, 1):
            medalla = "🥇" if i == 1 else "🥈" if i == 2 else "🥉"
            print(f"   {medalla} {año}: {cantidad:,} fotos ({porcentaje:.1f}%)")
        
        # Estadísticas adicionales
        print(f"\n📈 ESTADÍSTICAS:")
        print(f"   • Años con fotos: {len(distribucion)}")
        print(f"   • Promedio por año: {total_fotos // len(distribucion):,} fotos")
        
        # Carpetas vacías
        carpetas_vacias = 0
        for año_carpeta in carpeta.glob("[0-9]*"):
            if año_carpeta.is_dir():
                for mes_carpeta in año_carpeta.glob("*"):
                    if mes_carpeta.is_dir() and not any(mes_carpeta.iterdir()):
                        carpetas_vacias += 1
        
        if carpetas_vacias > 0:
            print(f"\n📁 Carpetas vacías: {carpetas_vacias}")
            print("   (Normal - solo se llenan si hay fotos de esa fecha)")
    
    # Analizar carpeta de revisión
    revision_path = carpeta / "00_PENDIENTE_REVISION"
    if revision_path.exists():
        print(f"\n{'='*40}")
        print("⚠️  FOTOS PENDIENTES DE REVISIÓN")
        print(f"{'='*40}")
        
        total_revisar = 0
        for subcarpeta in revision_path.glob("*"):
            if subcarpeta.is_dir():
                cantidad = len(list(subcarpeta.glob("*.*")))
                if cantidad > 0:
                    print(f"   📁 {subcarpeta.name}: {cantidad:,} fotos")
                    total_revisar += cantidad
        
        if total_revisar > 0:
            print(f"\n   Total a revisar: {total_revisar:,} fotos")
            print("\n   💡 RECOMENDACIONES:")
            print("   1. Revisa DUPLICADOS_POR_CONFIRMAR primero")
            print("   2. Asigna fechas a FOTOS_SIN_FECHA")
            print("   3. Decide sobre CALIDAD_DUDOSA al final")
        else:
            print("   ✅ No hay fotos pendientes de revisión")
    
    print(f"\n{'='*60}")
    print("✨ ANÁLISIS COMPLETADO")
    print(f"{'='*60}\n")

def main():
    print("""
    ╔══════════════════════════════════════════════╗
    ║   📊 ANALIZADOR DE FOTOS ORGANIZADAS 📊      ║
    ║      Estadísticas detalladas por año         ║
    ╚══════════════════════════════════════════════╝
    """)
    
    carpeta = input("\n📁 Ruta de la carpeta con fotos organizadas\n   (Enter = FOTOS_ORGANIZADAS): ").strip()
    
    if not carpeta:
        carpeta = "FOTOS_ORGANIZADAS"
    
    analizar_carpeta_organizada(carpeta)
    
    input("\n🎯 Presiona Enter para salir...")

if __name__ == "__main__":
    main()
