from flask import Flask, render_template, request, url_for
import heapq
import math
import networkx as nx
import matplotlib.pyplot as plt
import os
import matplotlib
matplotlib.use('agg')


app = Flask(__name__)

# Leer datos del archivo datos.txt
# Leer datos del archivo datos.txt
def leer_datos():
    w2i = {}
    labels = []
    info = []
    try:
        # Intentar abrir el archivo con codificación 'utf-8-sig' para manejar posibles BOM y caracteres no estándar
        with open("datos.txt", "r", encoding="utf-8-sig") as f:
            for line in f:
                node, neighbors = [elem.strip() for elem in line.split(":")]
                neighbors = neighbors.split()

                if node not in w2i:
                    w2i[node] = len(labels)
                    labels.append(node)
                    info.append(set(neighbors))
                else:
                    info[w2i[node]].update(neighbors)

                for neighbor in neighbors:
                    if neighbor not in w2i:
                        w2i[neighbor] = len(labels)
                        labels.append(neighbor)
                        info.append(set())

    except FileNotFoundError:
        print("El archivo 'datos.txt' no se encontró.")
        return None, None, None
    except UnicodeDecodeError:
        # En caso de que 'utf-8-sig' falle, intentamos con 'utf-8' y 'errors=ignore'
        print("Error de codificación, intentando con 'utf-8' y omitiendo caracteres no válidos...")
        try:
            with open("datos.txt", "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    node, neighbors = [elem.strip() for elem in line.split(":")]
                    neighbors = neighbors.split()

                    if node not in w2i:
                        w2i[node] = len(labels)
                        labels.append(node)
                        info.append(set(neighbors))
                    else:
                        info[w2i[node]].update(neighbors)

                    for neighbor in neighbors:
                        if neighbor not in w2i:
                            w2i[neighbor] = len(labels)
                            labels.append(neighbor)
                            info.append(set())
        except Exception as e:
            print(f"Ocurrió un error al leer el archivo con 'utf-8' y omitir caracteres: {e}")
            return None, None, None
    except Exception as e:
        print(f"Ocurrió un error al leer el archivo: {e}")
        return None, None, None

    return w2i, labels, info


# Implementación del algoritmo de Dijkstra
def dijkstra(graph, start):
    n = len(graph)
    dist = [float('inf')] * n
    dist[start] = 0
    prev = [-1] * n
    pq = [(0, start)]

    while pq:
        current_dist, u = heapq.heappop(pq)

        if current_dist > dist[u]:
            continue

        for v, weight in graph[u]:
            distance = current_dist + weight
            if distance < dist[v]:
                dist[v] = distance
                prev[v] = u
                heapq.heappush(pq, (distance, v))

    return dist, prev

def mostrar_camino(prev, start, target):
    path = []
    current = target
    while current != -1:
        path.append(current)
        current = prev[current]
    path.reverse()
    return path

# Función para calcular el costo dependiendo de la cantidad de paraderos recorridos
def costo(paraderos_recorridos):
    # Cada 5 paraderos equivalen a 1 sol
    costo_total = math.ceil(paraderos_recorridos / 5)  # Redondear hacia arriba
    return costo_total

# Genera imagen del camino recorrido usando networkx y matplotlib
def show_camino_recorrido(graph, labels, path, layout="spring"):
    G = nx.DiGraph()  # Grafo dirigido
    
    # Añadir nodos y aristas del camino
    for i in range(len(path) - 1):
        u = path[i]
        v = path[i + 1]
        G.add_node(u, label=labels[u])
        G.add_node(v, label=labels[v])
        G.add_edge(u, v)

    # Posiciones de los nodos
    if layout == "spring":
        pos = nx.spring_layout(G)
    elif layout == "circular":
        pos = nx.circular_layout(G)
    else:
        pos = nx.spring_layout(G)  # Layout por defecto

    plt.figure(figsize=(8, 6))
    nx.draw_networkx_nodes(G, pos, node_color='green', node_size=500)
    
    # Aquí modificamos el color de las letras a negro
    nx.draw_networkx_labels(G, pos, labels={node: labels[node] for node in G.nodes()}, font_size=10, font_color='black')
    
    nx.draw_networkx_edges(G, pos, edge_color='orange', width=2, arrows=True)

    plt.axis('off')
    
    # Asegurarse de que la carpeta 'static' exista
    if not os.path.exists('static'):
        os.makedirs('static')
    
    # Guardar la imagen en la carpeta 'static'
    filename = "static/camino_recorrido.png"
    plt.savefig(filename)
    plt.close()
    
    return filename

@app.route('/')
def inicio():
    return render_template('paginas/nexovia.html')

@app.route('/ruta')
def ruta():
    return render_template('paginas/codigo.html')

@app.route('/calcular', methods=['POST'])
def calcular():
    w2i, labels, info = leer_datos()
    
    if w2i is None:
        return render_template('paginas/codigo.html', resultado="No se pudieron cargar los datos.")

    # Crear el grafo ponderado
    G = []
    for neighbors in info:
        G.append([(w2i[node], 1) for node in neighbors])  # Peso de 1 para cada arista

    # Obtener los valores del formulario
    inicio = request.form.get('paraderoInicio').strip()
    final = request.form.get('paraderoFinal').strip()
    trafico = request.form.get('trafico').strip().lower()

    if inicio not in w2i or final not in w2i:
        resultado = "El nodo de inicio o final no está en el grafo."
        return render_template('paginas/codigo.html', resultado=resultado)

    # Ejecutar Dijkstra
    start_node = w2i[inicio]
    target_node = w2i[final]
    dist, prev = dijkstra(G, start_node)
    path = mostrar_camino(prev, start_node, target_node)

    if not path:
        resultado = f"No hay camino desde '{inicio}' a '{final}'."
    else:
        ruta = [labels[node] for node in path]
        paraderos_recorridos = len(path)
        costo_total = costo(paraderos_recorridos)
        tiempo = paraderos_recorridos * 5  # Sumar 5 minutos por cada nodo

        if trafico == "si":
            tiempo += 20  # Añadir 20 minutos si hay tráfico

        # Generar la imagen del camino recorrido
        archivo_imagen = show_camino_recorrido(G, labels, path, layout="spring")
        imagen_url = url_for('static', filename='camino_recorrido.png')

        # Crear el resultado para pasar al template
        resultado = {
            'ruta': " -> ".join(ruta),
            'costo': costo_total,
            'tiempo': tiempo,
            'imagen_url': imagen_url
        }

    return render_template('paginas/codigo.html', resultado=resultado)

@app.route('/contacto')
def contacto():
    return render_template('paginas/contacto.html')
@app.route('/nosotros')
def nosotros():
    return render_template('paginas/nosotros.html')



if __name__ == '__main__':
    app.run(debug=True)
