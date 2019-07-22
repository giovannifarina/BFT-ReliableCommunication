import networkx as nx
import math

def generate_multipartite_wheel(n,k):
    if k > n/2 or k%2 == 1:
        return None

    G = nx.Graph()

    num_levels = int(n/(k/2)) + (n % (k/2) > 0)
    level_size = int(k/2)
    for i in range(num_levels-1):
        for j in range(level_size):
            for k in range(level_size):
                G.add_edge(i*level_size+j, (i+1)*level_size+k)
    for j in range(level_size):
        for k in range(level_size):
            G.add_edge((num_levels-1) * level_size + j, k)
    # return G
    return nx.convert_node_labels_to_integers(G)

# G = generate_multipartite_wheel(20,8)
# nx.draw_networkx(G)

# nx.node_connectivity(G)