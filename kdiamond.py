import networkx as nx

def generate_k_diamond(n,k):
    if n < 2*k:
        raise Exception('n has to be at least twice the value of k')

    free_node_label = 2*k

    Tree = nx.DiGraph()
    Expanding_nodes = [0]
    Future_expanding_nodes = []
    last_expanded_node = 0
    Unshared_leaves = [] # the future expanding nodes will be all the unshared leaves
    Shared_leaves = []
    Phase = 0
    counter_phase3 = 0
    last_expanded_index = 0

    # base tree
    for i in range(1,k+1):
        Tree.add_edge(0,i)
        Tree.node[i]['type'] = 'shared'
        Shared_leaves.append(i)
    Tree.node[0]['type'] = 'root'

    def Phase1_goToNextLevel():
        nonlocal free_node_label
        nonlocal Unshared_leaves
        nonlocal Future_expanding_nodes
        nonlocal Phase

        Future_expanding_nodes = Unshared_leaves
        Unshared_leaves = []
        Expanding_nodes.clear()
        next_expanding_node = Future_expanding_nodes.pop()
        Tree.node[next_expanding_node]['type'] = 'internal'
        shared_nodes_to_move = [y for x, y in Tree.out_edges(last_expanded_node) if
                                Tree.node[y]['type'] == 'shared']

        Tree.remove_nodes_from(shared_nodes_to_move[:k - 2])
        for node in shared_nodes_to_move[:k - 2]:
            Tree.add_edge(next_expanding_node, node)
            Tree.node[node]['type'] = 'shared'
        Tree.add_edge(next_expanding_node, free_node_label)
        Tree.node[free_node_label]['type'] = 'shared'
        Expanding_nodes.append(next_expanding_node)
        Phase = 2

    def Phase2_newSharedAndInternals():
        nonlocal free_node_label
        nonlocal last_expanded_node
        nonlocal Phase
        nonlocal counter_phase3
        nonlocal last_expanded_index

        added_shared_node_flag = False
        for node in Expanding_nodes:
            if Tree.degree(node) < k + k - 2:
                Tree.add_edge(node, free_node_label)
                Tree.node[free_node_label]['type'] = 'shared'
                last_expanded_node = node
                added_shared_node_flag = True
                break
        if not added_shared_node_flag:  # new internal and expanding
            if len(Future_expanding_nodes) > 0:
                next_expanding_node = Future_expanding_nodes.pop()
                Tree.node[next_expanding_node]['type'] = 'internal'
                shared_nodes_to_move = [y for x, y in Tree.out_edges(last_expanded_node) if
                                        Tree.node[y]['type'] == 'shared']
                Tree.remove_nodes_from(shared_nodes_to_move[:k - 2])
                for node in shared_nodes_to_move[:k - 2]:
                    Tree.add_edge(next_expanding_node, node)
                    Tree.node[node]['type'] = 'shared'
                Tree.add_edge(next_expanding_node, free_node_label)
                Tree.node[free_node_label]['type'] = 'shared'
                Expanding_nodes.append(next_expanding_node)
                last_expanded_node = next_expanding_node
            else:  # all unshared are internals now
                Phase = 3
                counter_phase3 = 0
                last_expanded_index = 0
                Phase3_newUnshared()

    def Phase3_newUnshared():
        nonlocal Phase
        nonlocal counter_phase3
        nonlocal last_expanded_index

        if last_expanded_index < len(Expanding_nodes):
            node_to_expand = Expanding_nodes[last_expanded_index]
            shared_nodes_to_move = [y for x, y in Tree.out_edges(node_to_expand) if Tree.node[y]['type'] == 'shared']
            Tree.remove_nodes_from(shared_nodes_to_move[:k - 1])
            Tree.add_edge(node_to_expand, free_node_label)
            Tree.node[free_node_label]['type'] = 'unshared'
            Unshared_leaves.append(free_node_label)
            last_expanded_index += 1
        else:
            counter_phase3 += 1
            if counter_phase3 == k - 1:
                Phase = 5
                Phase5_newShared()
            else:
                Phase = 4
                Phase4_newShared()

    def Phase4_newShared():
        nonlocal Phase
        nonlocal last_expanded_index

        added_shared_node_flag = False
        for node in Expanding_nodes:
            if Tree.degree(node) < k + k - 2:
                Tree.add_edge(node, free_node_label)
                Tree.node[free_node_label]['type'] = 'shared'
                added_shared_node_flag = True
                break
        if not added_shared_node_flag:
            Phase = 3
            last_expanded_index = 0
            Phase3_newUnshared()


    def Phase5_newShared():
        nonlocal last_expanded_node
        nonlocal Phase

        # print('hellooooooo')

        last_expanded_node = Expanding_nodes[-1]
        if Tree.degree(last_expanded_node) < k + k - 2:
            Tree.add_edge(last_expanded_node, free_node_label)
            Tree.node[free_node_label]['type'] = 'shared'
            if Tree.degree(last_expanded_node) == k + k - 2:
                Phase = 1


    for iteration in range(2 * k, n):

        free_node_label += 1
        # print(Phase)

        if Phase == 0:  # first tree expansion
            if Tree.degree(Expanding_nodes[0]) < k + k - 2:
                Tree.add_edge(Expanding_nodes[0], free_node_label)
                Tree.node[free_node_label]['type'] = 'shared'
                Shared_leaves.append(free_node_label)
            elif len(Shared_leaves) >= k - 1:
                for i in range(k - 1):
                    node_to_remove = Shared_leaves.pop()
                    Tree.remove_node(node_to_remove)
                Tree.add_edge(Expanding_nodes[0], free_node_label)
                Tree.node[free_node_label]['type'] = 'unshared'
                Unshared_leaves.append(free_node_label)
            else:
                Phase = 1   # increase hight
                del Shared_leaves
                Phase1_goToNextLevel()

        elif Phase == 1:
            Phase1_goToNextLevel()

        elif Phase == 2:
            Phase2_newSharedAndInternals()

        elif Phase == 3:
            Phase3_newUnshared()

        elif Phase == 4:
            Phase4_newShared()

        elif Phase == 5:
            Phase5_newShared()

    node_label = free_node_label +1
    G = nx.Graph()
    node_mapping = {}

    Nodes_To_Analize = []
    node = 0
    types_inserted = set()
    while Tree.out_degree(node) > 0:
        types_inserted.add(Tree.node[node]['type'])
        Nodes_To_Analize.append([node, Tree.node[node]['type']])
        node = next(Tree.neighbors(node))


    for node in Tree.nodes():
        mapping = []
        if Tree.node[node]['type'] != 'shared':

            if Tree.node[node]['type'] == 'unshared' and 'unshared' not in types_inserted:
                types_inserted.add(Tree.node[node]['type'])
                Nodes_To_Analize.append([node, Tree.node[node]['type']])

            mapping.append(node)
            G.add_node(node)
            G.node[node]['type'] = Tree.node[node]['type']
            for i in range(k-1):
                mapping.append(node_label)
                G.add_node(node_label)
                G.node[node_label]['type'] = Tree.node[node]['type']
                node_label += 1
            node_mapping[node] = mapping
        else:

            if 'shared' not in types_inserted:
                types_inserted.add(Tree.node[node]['type'])
                Nodes_To_Analize.append([node, Tree.node[node]['type']])

            for i in range(k):
                mapping.append(node)
            node_mapping[node] = mapping
            G.add_node(node)
            G.node[node]['type'] = Tree.node[node]['type']

    for node in Tree.nodes():
        if Tree.node[node]['type'] == 'unshared':
            for i in range(k):
                for j in range(k):
                    if i<j:
                        G.add_edge(node_mapping[node][i], node_mapping[node][j])
        elif Tree.node[node]['type'] != 'shared': # root or internal
            for edge in Tree.out_edges(node):
                for i in range(k):
                    G.add_edge(node_mapping[edge[0]][i], node_mapping[edge[1]][i])

    relabelling = {}
    counter = 0
    for node in G.nodes():
        relabelling[node] = counter
        counter += 1
    G = nx.relabel_nodes(G, relabelling)
    for i in range(len(Nodes_To_Analize)):
        Nodes_To_Analize[i][0] = relabelling[Nodes_To_Analize[i][0]]

    return G, Nodes_To_Analize
    # return nx.convert_node_labels_to_integers(G)