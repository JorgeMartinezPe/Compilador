from ClassParser import ParserAsignacion, ASTNode, TablaSimbolos
from lexico import tokenizar
from collections import defaultdict
from semantico import analizar_semantica
from generadorCodigo import GeneradorIntermedio

# Código de prueba
codigo_limpio = """
int main() {
    int suma = 0;
    int i = 0;
    
    while (i < 10) {
        if (i == 5) {
            break;
        }
        
        if (i % 2 == 0) {
            i = i + 1;
            continue;
        }
        
        suma = suma + i;
        i = i + 1;
    }
    
    return suma;
}
"""

# ======== TOKENIZACIÓN ========
tokens_ordenados, contador, errores_token = tokenizar(codigo_limpio)

# ======== IMPRESIÓN DE TOKENS ========
print("=" * 60)
print("ANÁLISIS LÉXICO")
print("=" * 60)
print("Orden de tokens:")
for token in tokens_ordenados:
    num_linea, columna, tipo, valor, linea = token
    print(f"Línea {num_linea}, Col {columna}, Tipo: {tipo}, Valor: {valor}")

# ======== ERRORES DE TOKENIZACIÓN ========
if errores_token:
    print("\n Errores de tokenización:")
    for e in errores_token:
        print("-", e)
else:
    # Convertimos tokens a formato (tipo, valor) para el parser
    tokens_parser = [(t[2], t[3]) for t in tokens_ordenados]
    tokens_parser.append(("EOF", "EOF"))

    # ======== PARSER ========
    print("\n" + "=" * 60)
    print("ANÁLISIS SINTÁCTICO")
    print("=" * 60)
    
    #  CORREGIDO: Pasar tokens_con_ubicacion al parser
    parser = ParserAsignacion(tokens_ordenados, tokens_parser)  # tokens_ordenados tiene toda la info
    
    try:
        arbol = parser.program()
        print(" Análisis sintáctico exitoso")
        
        # ======== FUNCIÓN PARA IMPRIMIR EL ÁRBOL ========
        def imprimir_arbol_detallado(node, indent=0):
            espacio = "  " * indent
            info_tipo = f" [tipo: {node.tipo}]" if hasattr(node, 'tipo') and node.tipo else ""
            info_valor = f" [valor: {node.valor}]" if hasattr(node, 'valor') and node.valor else ""
            
            print(f"{espacio}{node.nombre}{info_valor}{info_tipo}")
            
            for hijo in node.hijos:
                imprimir_arbol_detallado(hijo, indent + 1)
        
        print("\n=== ESTRUCTURA DEL ÁRBOL GENERADO ===")
        imprimir_arbol_detallado(arbol)
        print("=== FIN ESTRUCTURA DEL ÁRBOL ===\n")
        
        # ======== ANÁLISIS SEMÁNTICO ========
        print("=" * 60)
        print("ANÁLISIS SEMÁNTICO")
        print("=" * 60)
        
        # Pasar la tabla de símbolos del parser al árbol
        arbol.tabla_global = parser.tabla_global
        

        tabla_simbolos, errores_semanticos = analizar_semantica(arbol, tokens_info=tokens_ordenados)
        
        # ✅ NUEVA SECCIÓN: GENERACIÓN DE CÓDIGO INTERMEDIO
        if not errores_semanticos:
            print("\n" + "=" * 60)
            print("GENERACIÓN DE CÓDIGO INTERMEDIO")
            print("=" * 60)
            
            # Crear generador y generar código
            generador = GeneradorIntermedio()
            codigo_tac = generador.generar_codigo(arbol)
            
            # Imprimir código intermedio generado
            generador.imprimir_codigo()
            
            # Guardar código intermedio para uso posterior
            arbol.codigo_intermedio = codigo_tac
            print(f"\n Código intermedio generado: {len(codigo_tac)} instrucciones")
        
        # ======== RESUMEN FINAL ========
        print("\n" + "=" * 60)
        print("RESUMEN DEL COMPILADOR")
        print("=" * 60)
        
        # Estadísticas de tokens
        print(f"\nESTADÍSTICAS DE TOKENS:")
        for tipo, cantidad in contador.items():
            print(f"   {tipo}: {cantidad}")
        
        # Resultado del análisis semántico
        if errores_semanticos:
            print(f"\nANÁLISIS SEMÁNTICO: {len(errores_semanticos)} error(es) encontrado(s)")
            print("\nErrores semánticos:")
            for e in errores_semanticos:
                print(f"{e}\n")  #  Los errores ya vienen formateados
        else:
            print(f"\n ANÁLISIS SEMÁNTICO: Correcto")
            
            # ✅ NUEVO: Información del código intermedio
            if hasattr(arbol, 'codigo_intermedio'):
                print(f"\n GENERACIÓN DE CÓDIGO: Exitosa")
                print(f"   Instrucciones TAC generadas: {len(arbol.codigo_intermedio)}")
                print(f"   Temporales usados: {generador.contador_temporales}")
                print(f"   Etiquetas creadas: {generador.contador_etiquetas}")
        
        # Información de la tabla de símbolos
        print(f"\n INFORMACIÓN DE TABLA DE SÍMBOLOS:")
        if hasattr(arbol, 'tabla_global') and arbol.tabla_global:
            total_variables = len(arbol.tabla_global.simbolos)
            total_funciones = len(arbol.tabla_global.funciones)
            print(f"   Variables declaradas: {total_variables}")
            print(f"   Funciones declaradas: {total_funciones}")
            
            # Variables no usadas
            no_usadas = arbol.tabla_global.obtener_variables_no_usadas()
            if no_usadas:
                print(f"    Variables no usadas: {', '.join(no_usadas)}")
            else:
                print(f"    Todas las variables están siendo usadas")
        else:
            print("    No hay información de tabla de símbolos disponible")
        
        # Estado final
        estado_final = 'NO VÁLIDO' if errores_semanticos else 'VÁLIDO'
        if not errores_semanticos and hasattr(arbol, 'codigo_intermedio'):
            estado_final += ' + CÓDIGO INTERMEDIO GENERADO'
        
        print(f"\nESTADO FINAL: {estado_final}")
        
    except SyntaxError as e:
        #  Los errores sintácticos ya vienen con formato mejorado
        print(f"\n{e}")
        
        # Mostrar tabla de símbolos incluso si hay error sintáctico
        if hasattr(parser, 'tabla_global') and parser.tabla_global:
            print("\n Tabla de símbolos hasta el error:")
            parser.tabla_global.imprimir_tabla()