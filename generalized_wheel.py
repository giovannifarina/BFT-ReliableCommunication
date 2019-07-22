import networkx as nx

def generate_generalized_wheel(n,k):
    G = nx.Graph()
    clique = []
    if k == 3:
        clique.append(0)
        G.add_node(0)
    else:
        for i in range(k-2):
            clique.append(i)
            for j in range(i,k-2):
                if i < j:
                    G.add_edge(i,j)
    for i in range(k-2,n-1):
        G.add_edge(i,i+1)
        for e in clique:
            G.add_edge(e,i)

    G.add_edge(k-2,n-1)
    for e in clique:
        G.add_edge(e, n-1)

    return G

# import matplotlib.pyplot as plt
# nx.draw(generate_generalized_wheel(20,5))
# plt.show()

