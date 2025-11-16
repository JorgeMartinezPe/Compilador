class Nodo:
    def __init__(self,dato):
        self.dato = dato
        self.NodoIzquierda  = None
        self.NodoDerecha  = None
        


def insertarNodo(raiz,nodo):
    if raiz is None:
        raiz = nodo
    else:
        if raiz.dato<nodo.dato:
            if raiz.NodoDerecha is None:
                raiz.NodoDerecha =nodo
            else:
                insertarNodo(raiz.NodoDerecha,nodo)
        else:
            if raiz.NodoIzquierda is None:
                raiz.NodoIzquierda = nodo
            else:
                insertarNodo(raiz.NodoIzquierda,nodo)


def InOrden(raiz):
    if raiz is not None:
        InOrden(raiz.NodoIzquierda)
        print(raiz.dato)
        InOrden(raiz.NodoDerecha)

raiz = Nodo(21)
insertarNodo(raiz,Nodo(13))
insertarNodo(raiz,Nodo(10))
insertarNodo(raiz,Nodo(33))
insertarNodo(raiz,Nodo(18))
insertarNodo(raiz,Nodo(25))
insertarNodo(raiz,Nodo(40))

InOrden(raiz)