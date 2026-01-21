import re
def tokenizar(codigo):
    CABECERA = r"(?P<CABECERA>\#include\s*<(\w+\.h|\w+)>)"
    PALABRA_RESERVADAS = r"(?P<PALABRA_RESERVADA>\b(endl|cout|nullptr|switch|case|default|using namespace std)\b)"
    VARIABLES = r"(?P<VARIABLE>[a-zA-Z][a-zA-Z_0-9]*)"
    NUMERO = r"(?P<NUMERO>\d+(\.\d+)?)"
    SUMA = r"(?P<SUMA>\+)"
    MODULO = r"(?P<MODULO>%)"
    RESTA = r"(?P<RESTA>\-)"
    DIVISION = r"(?P<DIVISION>/)"
    MULTIPLICACION = r"(?P<MULTIPLICACION>\*)"
    ASIGNACION = r"(?P<ASIGNACION>\=)"
    OPERADOR_DESPLAZAMIENTO = r"(?P<OPERADOR_DESPLAZAMIENTO><<|>>)"
    PARENTESIS_APERTURA = r"(?P<PARENTESIS_APERTURA>\()"
    PARENTESIS_CIERRE = r"(?P<PARENTESIS_CIERRE>\))"
    LLAVE_APERTURA = r"(?P<LLAVE_APERTURA>\{)"
    LLAVE_CIERRE = r"(?P<LLAVE_CIERRE>\})"
    PUNTO_COMA = r"(?P<PUNTO_COMA>;)"
    STRING = r'(?P<STRING>"[^"]*")'
    AND_LOGICO = r"(?P<AND_LOGICO>&&)"
    OR_LOGICO  = r"(?P<OR_LOGICO>\|\|)"
    MENOR_IGUAL = r"(?P<MENOR_IGUAL><=)"
    MAYOR_IGUAL = r"(?P<MAYOR_IGUAL>>=)"
    IGUAL_IGUAL = r"(?P<IGUAL_IGUAL>==)"
    DIFERENTE = r"(?P<DIFERENTE>!=)"
    MENOR_QUE = r"(?P<MENOR_QUE><)"
    MAYOR_QUE = r"(?P<MAYOR_QUE>>)"
    COMA = r"(?P<COMA>,)"
    IF = r"(?P<IF>\bif\b)"
    ELSE = r"(?P<ELSE>\belse\b)"
    WHILE = r"(?P<WHILE>\bwhile\b)"
    FOR = r"(?P<FOR>\bfor\b)"
    RETURN = r"(?P<RETURN>\breturn\b)"
    BREAK = r"(?P<BREAK>\bbreak\b)"
    CONTINUE = r"(?P<CONTINUE>\bcontinue\b)"
    TRUE = r"(?P<TRUE>\btrue\b)"
    FALSE = r"(?P<FALSE>\bfalse\b)"
    
    CHAR_LITERAL = r"(?P<CHAR_LITERAL>'(\\.|[^\\'])')"
    
    TIPO_DATO = r"(?P<TIPO_DATO>\b(int|float|char|void|string|bool)\b)"
    CONST_PI = r"(?P<CONST_PI>\bpi\b)"

    TOKENS = r"|".join([
        CABECERA,PALABRA_RESERVADAS,IF,WHILE,FOR,ELSE,RETURN,BREAK,CONTINUE,TRUE,FALSE,MODULO,COMA,
        TIPO_DATO,
        CONST_PI,STRING,CHAR_LITERAL,
        NUMERO,VARIABLES,
        AND_LOGICO,OR_LOGICO,MENOR_IGUAL,MAYOR_IGUAL,
        IGUAL_IGUAL,DIFERENTE,OPERADOR_DESPLAZAMIENTO,SUMA,RESTA,
        MULTIPLICACION,DIVISION,ASIGNACION,MENOR_QUE,MAYOR_QUE,PUNTO_COMA,
        PARENTESIS_APERTURA,PARENTESIS_CIERRE,LLAVE_APERTURA,LLAVE_CIERRE
    ])

    patron = re.compile(TOKENS)
    contador_tokens = {}
    tokens = []
    errores = []
    pos_consumido = 0
    lineas = codigo.splitlines()

    # Recorremos línea por línea para obtener posición y contenido
    for num_linea, linea in enumerate(lineas, start=1):
        last_end = 0
        for match in patron.finditer(linea):
            tipo = match.lastgroup
            valor = match.group()
            if tipo != "ESPACIO":  # ignoramos espacios
                columna = match.start() + 1  # columna 1-based
                tokens.append((num_linea, columna, tipo, valor, linea))
                contador_tokens[tipo] = contador_tokens.get(tipo, 0) + 1
            last_end = match.end()

        # Verificar basura no reconocida en la línea
        if last_end < len(linea):
            basura = linea[last_end:]
            if basura.strip():
                errores.append(f"Caracteres no reconocidos en línea {num_linea}, col {last_end+1}: '{basura}'")

    return tokens,contador_tokens, errores
