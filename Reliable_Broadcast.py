import networkx as nx
import numpy as np
import random
import subprocess
from networkx.algorithms import approximation

import multipartite_wheel
import kdiamond
import kpasted
import generalized_wheel


# Check the Minimum Vertex Cut (VC)
def check_vertex_cut_external(data,k):
    if len(data) == 0:
        return False
    if k < 2:
        return True
    if frozenset() in data:     # an edge with the source
        return True
    if len(data) < k:
        return False

    # input for the external MHS
    with open('mhs_input.dat', 'w') as f:
        for elem in data:
            f.write(' '.join(str(e) for e in elem)+'\n')
    result = subprocess.check_output(["./MHS/agdmhs mhs_input.dat -a pmmcs"], shell=True)
    result = result.decode("utf-8")
    n_mc = int((result.split('\n')[-2].split()[-1].strip()))
    if n_mc >= k:
        return True
    else:
        return False


def msgComplexity_dolev_maurer(n,k,filename):

    G = nx.random_regular_graph(k, n)
    while True:
        if nx.node_connectivity(G) == k:
            break
        else:
            G = nx.random_regular_graph(k, n)

    source = random.sample(G.nodes(),1)[0]

    PATHS_paths = {}
    TOFORWARD_paths = {}
    RECEIVED_paths = {}

    for node in G.nodes():
        PATHS_paths[node] = set()
        TOFORWARD_paths[node] = set()
        RECEIVED_paths[node] = set()

    PATHSETS_pathsets = {}
    TOFORWARD_pathsets = {}
    RECEIVED_pathsets = {}

    for node in G.nodes():
        PATHSETS_pathsets[node] = set()
        TOFORWARD_pathsets[node] = set()
        RECEIVED_pathsets[node] = set()



    msg_counter_paths = [0]*n
    msg_counter_pathsets = [0]*n

    t = 1

    TOFORWARD_paths[source].add(())
    TOFORWARD_pathsets[source].add(frozenset())

    while True:

        # print(t)

        flag_noUpdate = True

        for edge in G.edges():

            send = edge[0]
            recv = edge[1]


            if recv != source and len(TOFORWARD_paths[send])>0:
                for s in TOFORWARD_paths[send]:
                    if recv not in s:
                        if send != source:
                            s_new = s + (send,)
                            RECEIVED_paths[recv].add(s_new)
                            msg_counter_paths[send]+=1
                            flag_noUpdate = False
                        else:
                            s_new = ()
                            RECEIVED_paths[recv].add(s_new)
                            msg_counter_paths[send] += 1
                            flag_noUpdate = False

            send = edge[1]
            recv = edge[0]

            if recv != source and len(TOFORWARD_paths[send])>0:
                for s in TOFORWARD_paths[send]:
                    if recv not in s:
                        if send != source:
                            s_new = s + (send,)
                            RECEIVED_paths[recv].add(s_new)
                            msg_counter_paths[send]+=1
                            flag_noUpdate = False
                        else:
                            s_new = ()
                            RECEIVED_paths[recv].add(s_new)
                            msg_counter_paths[send] += 1
                            flag_noUpdate = False


            ###########################################

            send = edge[0]
            recv = edge[1]


            if recv != source and len(TOFORWARD_pathsets[send]) > 0:
                for s in TOFORWARD_pathsets[send]:
                    if recv not in s:
                        if send != source:
                            s_new = s.union([send])
                            RECEIVED_pathsets[recv].add(s_new)
                            msg_counter_pathsets[send] += 1
                            flag_noUpdate = False
                        else:
                            s_new = frozenset()
                            RECEIVED_pathsets[recv].add(s_new)
                            msg_counter_pathsets[send] += 1
                            flag_noUpdate = False


            send = edge[1]
            recv = edge[0]

            if recv != source and len(TOFORWARD_pathsets[send]) > 0:
                for s in TOFORWARD_pathsets[send]:
                    if recv not in s:
                        if send != source:
                            s_new = s.union([send])
                            RECEIVED_pathsets[recv].add(s_new)
                            msg_counter_pathsets[send] += 1
                            flag_noUpdate = False
                        else:
                            s_new = frozenset()
                            RECEIVED_pathsets[recv].add(s_new)
                            msg_counter_pathsets[send] += 1
                            flag_noUpdate = False



        for node in G.nodes():
            TOFORWARD_paths[node].clear()
            TOFORWARD_paths[node].update(RECEIVED_paths[node])
            RECEIVED_paths[node].clear()
            PATHS_paths[node].update(RECEIVED_paths[node])

        for node in G.nodes():
            TOFORWARD_pathsets[node].clear()
            TOFORWARD_pathsets[node].update(RECEIVED_pathsets[node])
            RECEIVED_pathsets[node].clear()
            PATHSETS_pathsets[node].update(RECEIVED_pathsets[node])


        if flag_noUpdate:
            with open(filename,'a') as fd:
                fd.write('n = ' + str(n) + '\t' + 'k = ' + str(k) + '\n')
                fd.write('Msg complexity paths: ' + str(sum(msg_counter_paths)) + '\n')
                fd.write('Msg complexity pathsets: ' + str(sum(msg_counter_pathsets)) + '\n')
                fd.write('#\n')
            break

        t = t + 1

def broadcast_bounded_multirand_pass(G, f, source, byz_set, CHANNEL_BOUND, filepath):

    ##### PASSIVE BYZANTINE PROCESSES #####

    PATHSETS = {}       # pathset under analysis for the delivery, i.e. pathsets associated to a single message
    TO_FORWARD = {}     # pathset to forward
    RECEIVED = {}       # pathset received, not yet analyzed
    msg_counters = {}   # counts all messages exchanged


    for node in G.nodes():
        PATHSETS[node] = set()
        TO_FORWARD[node] = []
        RECEIVED[node] = []
        msg_counters[node] = 0


    # round counter
    round = 1

    # frozenset() = empty pathset
    TO_FORWARD[source].append(frozenset())

    nodes_who_delivered = set()
    nodes_who_delivered.add(source)

    NEIGHT_DEL = {}
    for node in G.nodes():
        NEIGHT_DEL[node] = []

    # the message selected for the transmission by a node at round t
    msg_to_send_at_t = {}

    flag_allNodes_delivered = False

    while True:

        print('round:',round)

        flag_noFurtherMsgsExchanges = True

        ### SEND PHASE ###

        # MULTI-RANDOM POLICY
        for node in G.nodes():
            if node not in byz_set:
                if len(TO_FORWARD[node]) > 0:

                    # nodes who delivered do not require further pathsets
                    node_to_contact = set(nx.neighbors(G, node))
                    node_to_contact.difference_update(NEIGHT_DEL[node])
                    if len(node_to_contact) == 0:
                        continue

                    random.shuffle(TO_FORWARD[node])

                    msg_to_send_at_t[node] = []
                    num_messages_selected = 0

                    for i in range(len(TO_FORWARD[node]) - 1, -1, -1):
                        previous_length = len(node_to_contact)
                        if previous_length == 0 or num_messages_selected == CHANNEL_BOUND:
                            break
                        msg = TO_FORWARD[node][i]
                        node_to_contact.intersection_update(msg)
                        # check if it is an useful message
                        if len(node_to_contact) != previous_length:
                            msg_to_send_at_t[node].append(msg)
                            del TO_FORWARD[node][i]
                            num_messages_selected += 1

        for edge in G.edges():
            sender = edge[0]
            receiver = edge[1]

            if sender in msg_to_send_at_t and receiver not in NEIGHT_DEL[sender] and sender not in byz_set:
                for pathset in msg_to_send_at_t[sender]:
                    if receiver not in pathset:
                        if sender != source:
                            s_new = pathset.union([sender])  # it appends the id of the sender. this is for ease of simplicity, in the real protocol the labe are attached by the received to enforce safety
                        else:
                            s_new = frozenset()
                        RECEIVED[receiver].append(s_new)
                        msg_counters[sender] += 1
                        flag_noFurtherMsgsExchanges = False

            sender = edge[1]
            receiver = edge[0]

            if sender in msg_to_send_at_t and receiver not in NEIGHT_DEL[sender] and sender not in byz_set:
                for pathset in msg_to_send_at_t[sender]:
                    if receiver not in pathset:
                        if sender != source:
                            s_new = pathset.union([sender])  # it appends the id of the sender. this is for ease of simplicity, in the real protocol the labe are attached by the received to enforce safety
                        else:
                            s_new = frozenset()
                        RECEIVED[receiver].append(s_new)
                        msg_counters[sender] += 1
                        flag_noFurtherMsgsExchanges = False

        ### RECEIVE PHASE ###
        for node in G.nodes():

            if node not in byz_set:

                if node in nodes_who_delivered:
                    RECEIVED[node].clear()
                    continue

                for index in range(len(RECEIVED[node]) - 1, -1, -1):
                    if RECEIVED[node][index] in PATHSETS[node]:
                        del RECEIVED[node][index]

                random.shuffle(RECEIVED[node])

                TO_FORWARD[node].extend(RECEIVED[node])
                PATHSETS[node].update(RECEIVED[node])

                for new_set in RECEIVED[node]:
                    if len(new_set) == 0:
                        NEIGHT_DEL[node].append(source)
                    elif len(new_set) == 1:
                        NEIGHT_DEL[node].append(list(new_set)[0])

                for element in NEIGHT_DEL[node]:
                    for pathset_i in list(PATHSETS[node]):
                        if len(pathset_i) > 1 and element in pathset_i:
                            PATHSETS[node].remove(pathset_i)
                    for index in range(len(TO_FORWARD[node]) - 1, -1, -1):
                        if len(TO_FORWARD[node][index]) > 1 and element in TO_FORWARD[node][index]:
                            del TO_FORWARD[node][index]

                RECEIVED[node].clear()

        msg_to_send_at_t.clear()

        ### COMPUTATION PHASE ###
        for node in G.nodes():
            if node not in nodes_who_delivered and node not in byz_set:
                flag_min_cut = check_vertex_cut_external(PATHSETS[node], f + 1)
                if flag_min_cut:
                    nodes_who_delivered.add(node)
                    # remove all messages still to forward, and forward the empty path
                    TO_FORWARD[node].clear()
                    TO_FORWARD[node].append(frozenset())

        if len(nodes_who_delivered) == G.order() - len(byz_set) and not flag_allNodes_delivered:
            t_broadcast = round
            flag_allNodes_delivered = True

        # save the results when no further message has to be exchanged
        if flag_noFurtherMsgsExchanges and flag_allNodes_delivered:
            with open(filepath, 'a') as fd:
                fd.write('t_broadcast_multirand_passivebyz\t' + str(t_broadcast) + '\n')
                fd.write('msg_complex_multirand_passivebyz\t' + str(sum(msg_counters.values())) + '\n')
            break

        round += 1

    with open(filepath, 'a') as fd:
        fd.write('#\n')

def broadcast_bounded_multishor_pass_act(G,f,source,byz_set, CHANNEL_BOUND, filepath):

    ##### PASSIVE BYZANTINE PROCESSES #####

    PATHSETS = {}       # pathset under analysis for the delivery, i.e. pathsets associated to a single message
    TO_FORWARD = {}     # pathset to forward
    RECEIVED = {}       # pathset received, not yet analyzed
    msg_counters = {}

    for node in G.nodes():
        PATHSETS[node] = set()
        TO_FORWARD[node] = []
        RECEIVED[node] = []
        msg_counters[node] = 0

    # round counter
    round = 1

    # frozenset() = empty pathset
    TO_FORWARD[source].append(frozenset())

    nodes_who_delivered = set()
    nodes_who_delivered.add(source)

    NEIGHT_DEL = {}
    for node in G.nodes():
        NEIGHT_DEL[node] = []

    # the message selected for the transmission by a node at round t
    msg_to_send_at_t = {}

    flag_allNodes_delivered = False

    while True:

        print('round:',round)

        flag_noFurtherMsgsExchanges = True

        ### SEND PHASE ###

        # MULTI-SHORTEST POLICY
        for node in G.nodes():
            if node not in byz_set:
                if len(TO_FORWARD[node]) > 0:

                    # nodes who delivered do not require further pathsets
                    node_to_contact = set(nx.neighbors(G, node))
                    node_to_contact.difference_update(NEIGHT_DEL[node])
                    if len(node_to_contact) == 0:
                        continue

                    # sort by the lenght of the pathset
                    TO_FORWARD[node].sort(key=lambda x: len(x), reverse=True)

                    msg_to_send_at_t[node] = []
                    num_messages_selected = 0

                    for i in range(len(TO_FORWARD[node]) - 1, -1, -1):
                        previous_length = len(node_to_contact)
                        if previous_length == 0 or num_messages_selected == CHANNEL_BOUND:
                            break
                        msg = TO_FORWARD[node][i]
                        node_to_contact.intersection_update(msg)
                        # check if it is an useful message
                        if len(node_to_contact) != previous_length:
                            msg_to_send_at_t[node].append(msg)
                            del TO_FORWARD[node][i]
                            num_messages_selected += 1

        for edge in G.edges():
            sender = edge[0]
            receiver = edge[1]

            if sender in msg_to_send_at_t and receiver not in NEIGHT_DEL[sender] and sender not in byz_set:
                for pathset in msg_to_send_at_t[sender]:
                    if receiver not in pathset:
                        if sender != source:
                            s_new = pathset.union([sender])  # it appends the id of the sender. this is for ease of simplicity, in the real protocol the labe are attached by the received to enforce safety
                        else:
                            s_new = frozenset()
                        RECEIVED[receiver].append(s_new)
                        msg_counters[sender] += 1
                        flag_noFurtherMsgsExchanges = False

            sender = edge[1]
            receiver = edge[0]

            if sender in msg_to_send_at_t and receiver not in NEIGHT_DEL[sender] and sender not in byz_set:
                for pathset in msg_to_send_at_t[sender]:
                    if receiver not in pathset:
                        if sender != source:
                            s_new = pathset.union([sender])  # it appends the id of the sender. this is for ease of simplicity, in the real protocol the labe are attached by the received to enforce safety
                        else:
                            s_new = frozenset()
                        RECEIVED[receiver].append(s_new)
                        msg_counters[sender] += 1
                        flag_noFurtherMsgsExchanges = False

        ### RECEIVE PHASE ###
        for node in G.nodes():
            if node not in byz_set:
                if node in nodes_who_delivered:
                    RECEIVED[node].clear()
                    continue

                for index in range(len(RECEIVED[node]) - 1, -1, -1):
                    if RECEIVED[node][index] in PATHSETS[node]:
                        del RECEIVED[node][index]

                random.shuffle(RECEIVED[node])

                TO_FORWARD[node].extend(RECEIVED[node])
                PATHSETS[node].update(RECEIVED[node])

                for new_set in RECEIVED[node]:
                    if len(new_set) == 0:
                        NEIGHT_DEL[node].append(source)
                    elif len(new_set) == 1:
                        NEIGHT_DEL[node].append(list(new_set)[0])

                for element in NEIGHT_DEL[node]:
                    for pathset_i in list(PATHSETS[node]):
                        if len(pathset_i) > 1 and element in pathset_i:
                            PATHSETS[node].remove(pathset_i)
                    for index in range(len(TO_FORWARD[node]) - 1, -1, -1):
                        if len(TO_FORWARD[node][index]) > 1 and element in TO_FORWARD[node][index]:
                            del TO_FORWARD[node][index]

                RECEIVED[node].clear()

        msg_to_send_at_t.clear()

        ### COMPUTATION PHASE ###
        for node in G.nodes():
            if node not in nodes_who_delivered and node not in byz_set:
                flag_min_cut = check_vertex_cut_external(PATHSETS[node], f + 1)
                if flag_min_cut:
                    nodes_who_delivered.add(node)
                    # remove all messages still to forward, and forward the empty path
                    TO_FORWARD[node].clear()
                    TO_FORWARD[node].append(frozenset())

        if len(nodes_who_delivered) == G.order() - len(byz_set) and not flag_allNodes_delivered:
            t_broadcast = round
            flag_allNodes_delivered = True

        # save the results when no further message has to be exchanged
        if flag_noFurtherMsgsExchanges and flag_allNodes_delivered:
            with open(filepath, 'a') as fd:
                fd.write('t_broadcast_multishortest_passivebyz\t' + str(t_broadcast) + '\n')
                fd.write('msg_complex_multishortest_passivebyz\t' + str(sum(msg_counters.values())) + '\n')
            break

        round += 1

    ### OMNISCIENT BYZANTINE FAULTS ###


    PATHSETS = {}  # pathset under analysis for the delivery, i.e. pathsets associated to a single message
    TO_FORWARD = {}  # pathset to forward
    RECEIVED = {}  # pathset received, not yet analyzed
    msg_counters = {}


    for node in G.nodes():
        PATHSETS[node] = set()
        TO_FORWARD[node] = []
        RECEIVED[node] = []
        msg_counters[node] = 0

    BYZ_MSG = {}
    for node in G.nodes():
        BYZ_MSG[node] = set()

    # time
    round = 1

    # frozenset() = empty pathset
    TO_FORWARD[source].append(frozenset())

    nodes_who_delivered = set()
    nodes_who_delivered.add(source)

    NEIGHT_DEL = {}
    for node in G.nodes():
        NEIGHT_DEL[node] = []

    # the message selected for the transmission by a node at time t
    msg_to_send_at_t = {}

    flag_allNodes_delivered = False

    while True:

        print('round:',round)

        flag_noFurtherMsgsExchanges = True

        ### SEND PHASE ###

        # MULTI-SHORTEST POLICY
        for node in G.nodes():
            if node not in byz_set:
                if len(TO_FORWARD[node]) > 0:

                    # nodes who delivered do not require further pathsets
                    node_to_contact = set(nx.neighbors(G, node))
                    node_to_contact.difference_update(NEIGHT_DEL[node])
                    if len(node_to_contact) == 0:
                        continue

                    # sort by the lenght of the pathset
                    TO_FORWARD[node].sort(key=lambda x: len(x), reverse=True)

                    msg_to_send_at_t[node] = []
                    num_messages_selected = 0

                    for i in range(len(TO_FORWARD[node]) - 1, -1, -1):
                        previous_length = len(node_to_contact)
                        if previous_length == 0 or num_messages_selected == CHANNEL_BOUND:
                            break
                        msg = TO_FORWARD[node][i]
                        node_to_contact.intersection_update(msg)
                        # check if it is an useful message
                        if len(node_to_contact) != previous_length:
                            msg_to_send_at_t[node].append(msg)
                            del TO_FORWARD[node][i]
                            num_messages_selected += 1


        for edge in G.edges():

            sender = edge[0]
            receiver = edge[1]

            if sender in msg_to_send_at_t and receiver not in NEIGHT_DEL[sender] and sender not in byz_set:
                for pathset in msg_to_send_at_t[sender]:
                    if receiver not in pathset:
                        if sender != source:
                            s_new = pathset.union([sender])  # it appends the id of the sender. this is for ease of simplicity, in the real protocol the labe are attached by the received to enforce safety
                        else:
                            s_new = frozenset()
                        RECEIVED[receiver].append(s_new)
                        msg_counters[sender] += 1
                        flag_noFurtherMsgsExchanges = False


            if sender in byz_set and receiver not in byz_set and receiver not in nodes_who_delivered:
                byz = sender
                node = receiver
                byz_counter = 0
                byz_fake_node = G.order() + 1

                receiver_neighbors = set(nx.neighbors(G, receiver))
                receiver_neighbors.difference_update(byz_set)
                receiver_neighbors = list(receiver_neighbors)

                stop_flag = False
                while True:
                    for target_neigh in receiver_neighbors:
                        s_new = frozenset([target_neigh, byz])
                        if s_new not in BYZ_MSG[node]:
                            BYZ_MSG[node].add(s_new)
                            RECEIVED[node].append(s_new)
                            byz_counter += 1
                            if byz_counter == CHANNEL_BOUND:
                                stop_flag = True
                                break
                    if stop_flag:
                        break
                    while True:
                        for target_neigh in receiver_neighbors:
                            while byz_fake_node in G:
                                byz_fake_node += 1
                            s_new = frozenset([byz_fake_node, target_neigh, byz])
                            byz_fake_node += 1
                            if s_new not in BYZ_MSG[node]:
                                BYZ_MSG[node].add(s_new)
                                RECEIVED[node].append(s_new)
                                byz_counter += 1
                                if byz_counter == CHANNEL_BOUND:
                                    stop_flag = True
                                    break
                        if stop_flag:
                            break
                    if stop_flag:
                        break

            sender = edge[1]
            receiver = edge[0]

            if sender in msg_to_send_at_t and receiver not in NEIGHT_DEL[sender] and sender not in byz_set:
                for pathset in msg_to_send_at_t[sender]:
                    if receiver not in pathset:
                        if sender != source:
                            s_new = pathset.union([
                                                      sender])  # it appends the id of the sender. this is for ease of simplicity, in the real protocol the labe are attached by the received to enforce safety
                        else:
                            s_new = frozenset()
                        RECEIVED[receiver].append(s_new)
                        msg_counters[sender] += 1
                        flag_noFurtherMsgsExchanges = False

            if sender in byz_set and receiver not in byz_set and receiver not in nodes_who_delivered:
                byz = sender
                node = receiver
                byz_counter = 0
                byz_fake_node = G.order() + 1

                receiver_neighbors = set(nx.neighbors(G, receiver))
                receiver_neighbors.difference_update(byz_set)
                receiver_neighbors = list(receiver_neighbors)

                stop_flag = False
                while True:
                    for target_neigh in receiver_neighbors:
                        s_new = frozenset([target_neigh, byz])
                        if s_new not in BYZ_MSG[node]:
                            BYZ_MSG[node].add(s_new)
                            RECEIVED[node].append(s_new)
                            byz_counter += 1
                            if byz_counter == CHANNEL_BOUND:
                                stop_flag = True
                                break
                    if stop_flag:
                        break
                    while True:
                        for target_neigh in receiver_neighbors:
                            while byz_fake_node in G:
                                byz_fake_node += 1
                            s_new = frozenset([byz_fake_node, target_neigh, byz])
                            byz_fake_node += 1
                            if s_new not in BYZ_MSG[node]:
                                BYZ_MSG[node].add(s_new)
                                RECEIVED[node].append(s_new)
                                byz_counter += 1
                                if byz_counter == CHANNEL_BOUND:
                                    stop_flag = True
                                    break
                        if stop_flag:
                            break
                    if stop_flag:
                        break

        for node in G.nodes():
            if node not in byz_set:
                if node in nodes_who_delivered:
                    RECEIVED[node].clear()
                    continue

                for index in range(len(RECEIVED[node]) - 1, -1, -1):
                    if RECEIVED[node][index] in PATHSETS[node]:
                        del RECEIVED[node][index]

                random.shuffle(RECEIVED[node])

                TO_FORWARD[node].extend(RECEIVED[node])
                PATHSETS[node].update(RECEIVED[node])

                for new_set in RECEIVED[node]:
                    if len(new_set) == 0:
                        NEIGHT_DEL[node].append(source)
                    elif len(new_set) == 1:
                        NEIGHT_DEL[node].append(list(new_set)[0])

                for element in NEIGHT_DEL[node]:
                    for pathset_i in list(PATHSETS[node]):
                        if len(pathset_i) > 1 and element in pathset_i:
                            PATHSETS[node].remove(pathset_i)
                    for index in range(len(TO_FORWARD[node]) - 1, -1, -1):
                        if len(TO_FORWARD[node][index]) > 1 and element in TO_FORWARD[node][index]:
                            del TO_FORWARD[node][index]

                RECEIVED[node].clear()

        msg_to_send_at_t.clear()

        # ANALYZING PHASE, try to deliver
        for node in G.nodes():
            if node not in nodes_who_delivered and node not in byz_set:
                flag_min_cut = check_vertex_cut_external(PATHSETS[node], f + 1)
                if flag_min_cut:
                    nodes_who_delivered.add(node)
                    # remove all messages still to forward, and forward the empty path
                    TO_FORWARD[node].clear()
                    TO_FORWARD[node].append(frozenset())

        if len(nodes_who_delivered) == G.order() - len(byz_set) and not flag_allNodes_delivered:
            t_broadcast = round
            flag_allNodes_delivered = True


        # save the results when no further message has to be exchanged
        if flag_noFurtherMsgsExchanges and flag_allNodes_delivered:
            with open(filepath, 'a') as fd:
                fd.write('t_broadcast_multishortest_activeomnibyz\t' + str(t_broadcast) + '\n')
                fd.write('msg_complex_multishortest_activeomnibyz\t' + str(sum(msg_counters.values())) + '\n')
            break

        round += 1

    ### NON OMNISCIENT BYZANTINE FAULTS ###

    PATHSETS = {}  # pathset under analysis for the delivery, i.e. pathsets associated to a single message
    TO_FORWARD = {}  # pathset to forward
    RECEIVED = {}  # pathset received, not yet analyzed
    msg_counters = {}


    for node in G.nodes():
        PATHSETS[node] = set()
        TO_FORWARD[node] = []
        RECEIVED[node] = []
        msg_counters[node] = 0

    BYZ_ACTIVATION = {}
    BYZ_MSG = {}

    for node in G.nodes():
        BYZ_MSG[node] = set()

    for node in byz_set:
        BYZ_ACTIVATION[node] = 0

    # time
    round = 1

    # frozenset() = empty pathset
    TO_FORWARD[source].append(frozenset())

    nodes_who_delivered = set()
    nodes_who_delivered.add(source)

    NEIGHT_DEL = {}
    for node in G.nodes():
        NEIGHT_DEL[node] = []

    # the message selected for the transmission by a node at time t
    msg_to_send_at_t = {}

    flag_allNodes_delivered = False

    while True:

        print('round:',round)

        flag_noFurtherMsgsExchanges = True

        # MULTI-SHORTEST POLICY
        for node in G.nodes():
            if node not in byz_set:
                if len(TO_FORWARD[node]) > 0:

                    # nodes who delivered do not require further pathsets
                    node_to_contact = set(nx.neighbors(G, node))
                    node_to_contact.difference_update(NEIGHT_DEL[node])
                    if len(node_to_contact) == 0:
                        continue

                    # sort by the lenght of the pathset
                    TO_FORWARD[node].sort(key=lambda x: len(x), reverse=True)

                    msg_to_send_at_t[node] = []
                    num_messages_selected = 0

                    for i in range(len(TO_FORWARD[node]) - 1, -1, -1):
                        previous_length = len(node_to_contact)
                        if previous_length == 0 or num_messages_selected == CHANNEL_BOUND:
                            break
                        msg = TO_FORWARD[node][i]
                        node_to_contact.intersection_update(msg)
                        # check if it is an useful message
                        if len(node_to_contact) != previous_length:
                            msg_to_send_at_t[node].append(msg)
                            del TO_FORWARD[node][i]
                            num_messages_selected += 1

        for edge in G.edges():

            sender = edge[0]
            receiver = edge[1]

            if sender in msg_to_send_at_t and receiver not in NEIGHT_DEL[sender] and sender not in byz_set:
                for pathset in msg_to_send_at_t[sender]:
                    if receiver not in pathset:
                        if sender != source:
                            s_new = pathset.union([sender])  # it appends the id of the sender. this is for ease of simplicity, in the real protocol the labe are attached by the received to enforce safety
                        else:
                            s_new = frozenset()
                        RECEIVED[receiver].append(s_new)
                        msg_counters[sender] += 1
                        flag_noFurtherMsgsExchanges = False

            if (receiver in byz_set and sender in msg_to_send_at_t and BYZ_ACTIVATION[receiver] == 0) or (sender in byz_set and receiver in byz_set and BYZ_ACTIVATION[sender]==2 and BYZ_ACTIVATION[receiver]==0):
                BYZ_ACTIVATION[receiver] = 1

            if sender in byz_set and BYZ_ACTIVATION[sender] == 2 and receiver not in byz_set:
                byz = sender
                node = receiver
                byz_counter = 0
                byz_fake_node = G.order() + 1

                receiver_neighbors = set(nx.neighbors(G, receiver))
                receiver_neighbors.difference_update(byz_set)
                receiver_neighbors = list(receiver_neighbors)

                stop_flag = False
                while True:
                    for target_neigh in receiver_neighbors:
                        s_new = frozenset([target_neigh, byz])
                        if s_new not in BYZ_MSG[node]:
                            BYZ_MSG[node].add(s_new)
                            RECEIVED[node].append(s_new)
                            byz_counter += 1
                            if byz_counter == CHANNEL_BOUND:
                                stop_flag = True
                                break
                    if stop_flag:
                        break
                    while True:
                        for target_neigh in receiver_neighbors:
                            while byz_fake_node in G:
                                byz_fake_node += 1
                            s_new = frozenset([byz_fake_node, target_neigh, byz])
                            byz_fake_node += 1
                            if s_new not in BYZ_MSG[node]:
                                BYZ_MSG[node].add(s_new)
                                RECEIVED[node].append(s_new)
                                byz_counter += 1
                                if byz_counter == CHANNEL_BOUND:
                                    stop_flag = True
                                    break
                        if stop_flag:
                            break
                    if stop_flag:
                        break

            sender = edge[1]
            receiver = edge[0]

            if sender in msg_to_send_at_t and receiver not in NEIGHT_DEL[sender] and sender not in byz_set:
                for pathset in msg_to_send_at_t[sender]:
                    if receiver not in pathset:
                        if sender != source:
                            s_new = pathset.union([
                                                      sender])  # it appends the id of the sender. this is for ease of simplicity, in the real protocol the labe are attached by the received to enforce safety
                        else:
                            s_new = frozenset()
                        RECEIVED[receiver].append(s_new)
                        msg_counters[sender] += 1
                        flag_noFurtherMsgsExchanges = False

            if (receiver in byz_set and sender in msg_to_send_at_t and BYZ_ACTIVATION[receiver] == 0) or (sender in byz_set and receiver in byz_set and BYZ_ACTIVATION[sender]==2 and BYZ_ACTIVATION[receiver]==0):
                BYZ_ACTIVATION[receiver] = 1

            if sender in byz_set and BYZ_ACTIVATION[sender] == 2 and receiver not in byz_set:
                byz = sender
                node = receiver
                byz_counter = 0
                byz_fake_node = G.order() + 1

                receiver_neighbors = set(nx.neighbors(G, receiver))
                receiver_neighbors.difference_update(byz_set)
                receiver_neighbors = list(receiver_neighbors)

                stop_flag = False
                while True:
                    for target_neigh in receiver_neighbors:
                        s_new = frozenset([target_neigh, byz])
                        if s_new not in BYZ_MSG[node]:
                            BYZ_MSG[node].add(s_new)
                            RECEIVED[node].append(s_new)
                            byz_counter += 1
                            if byz_counter == CHANNEL_BOUND:
                                stop_flag = True
                                break
                    if stop_flag:
                        break
                    while True:
                        for target_neigh in receiver_neighbors:
                            while byz_fake_node in G:
                                byz_fake_node += 1
                            s_new = frozenset([byz_fake_node, target_neigh, byz])
                            byz_fake_node += 1
                            if s_new not in BYZ_MSG[node]:
                                BYZ_MSG[node].add(s_new)
                                RECEIVED[node].append(s_new)
                                byz_counter += 1
                                if byz_counter == CHANNEL_BOUND:
                                    stop_flag = True
                                    break
                        if stop_flag:
                            break
                    if stop_flag:
                        break

        for node in G.nodes():
            if node not in byz_set:
                if node in nodes_who_delivered:
                    RECEIVED[node].clear()
                    continue

                for index in range(len(RECEIVED[node]) - 1, -1, -1):
                    if RECEIVED[node][index] in PATHSETS[node]:
                        del RECEIVED[node][index]

                random.shuffle(RECEIVED[node])

                TO_FORWARD[node].extend(RECEIVED[node])
                PATHSETS[node].update(RECEIVED[node])

                for new_set in RECEIVED[node]:
                    if len(new_set) == 0:
                        NEIGHT_DEL[node].append(source)
                    elif len(new_set) == 1:
                        NEIGHT_DEL[node].append(list(new_set)[0])

                for element in NEIGHT_DEL[node]:
                    for pathset_i in list(PATHSETS[node]):
                        if len(pathset_i) > 1 and element in pathset_i:
                            PATHSETS[node].remove(pathset_i)
                    for index in range(len(TO_FORWARD[node]) - 1, -1, -1):
                        if len(TO_FORWARD[node][index]) > 1 and element in TO_FORWARD[node][index]:
                            del TO_FORWARD[node][index]

                RECEIVED[node].clear()

        msg_to_send_at_t.clear()

        # ANALYZING PHASE, try to deliver
        for node in G.nodes():
            if node not in nodes_who_delivered and node not in byz_set:
                flag_min_cut = check_vertex_cut_external(PATHSETS[node], f + 1)
                if flag_min_cut:
                    nodes_who_delivered.add(node)
                    # remove all messages still to forward, and forward the empty path
                    TO_FORWARD[node].clear()
                    TO_FORWARD[node].append(frozenset())

        if len(nodes_who_delivered) == G.order() - len(byz_set) and not flag_allNodes_delivered:
            t_broadcast = round
            flag_allNodes_delivered = True


        # save the results when no further message has to be exchanged
        if flag_noFurtherMsgsExchanges and flag_allNodes_delivered:
            with open(filepath, 'a') as fd:
                fd.write('t_broadcast_multishortest_activeNONomnibyz\t' + str(t_broadcast) + '\n')
                fd.write('msg_complex_multishortest_activeNONomnibyz\t' + str(sum(msg_counters.values())) + '\n')
            break

        round += 1

        for node in byz_set:
            if BYZ_ACTIVATION[node] == 1:
                BYZ_ACTIVATION[node] == 2

    with open(filepath, 'a') as fd:
        fd.write('#\n')


#### EDIT TO CHANGE SIMULATION PARAMETERS ####

def simulate_bounded_multirand_randomreg_pass():
    filepath = 'results/bounded_multirand_randomreg_bound_pass.dat'
    for n in [100]:                              # EDIT the list values to set the network size
        # for k in range(3, int(n/2)+1):           # EDIT range parameters to set the network connectivity
        for k in range(3, 11):                  # for certain values it may explode

            G = nx.random_regular_graph(k, n)
            while True:
                if approximation.node_connectivity(G) == k:
                    break
                else:
                    G = nx.random_regular_graph(k, n)

            f = int((k - 1) / 2)
            CHANNEL_BOUND = f + 1

            for iteration_counter1 in range(3):
                byz_set = set(random.sample(G.nodes(), f))
                for iteration_counter2 in range(3):
                    with open(filepath, 'a') as fd:
                        fd.write(str(n) + '\t' + str(k) + '\t' + str(f) + '\n')
                    while True:
                        source = random.sample(G.nodes(), 1)[0]
                        if source not in byz_set:
                            break
                    broadcast_bounded_multirand_pass(G,f,source,byz_set, CHANNEL_BOUND, filepath)

def simulate_bounded_multirand_multiwheel_pass():
    filepath = 'results/bounded_multirand_multiwheel_bound_pass.dat'
    for n in [100]:  # EDIT the list values to set the network size
        # for k in range(4, int(n / 2) - 1, 2):  # EDIT range parameters to set the network connectivity
        for k in range(4, 13, 2):  # EDIT range parameters to set the network connectivity

            G = multipartite_wheel.generate_multipartite_wheel(n, k)

            f = int((k - 1) / 2)
            CHANNEL_BOUND = f + 1

            # selecting a Byzantine placement
            for iteration_counter1 in range(3):

                byz_set = set(random.sample(G.nodes(), f))

                # selecting a sources

                for iteration_counter2 in range(1):

                    with open(filepath, 'a') as fd:
                        fd.write(str(G.order()) + '\t' + str(k) + '\t' + str(f) + '\n')

                    while True:
                        source = random.sample(G.nodes(), 1)[0]
                        if source not in byz_set:
                            break

                    broadcast_bounded_multirand_pass(G,f,source,byz_set, CHANNEL_BOUND, filepath)

def simulate_bounded_multirand_kdiamond_pass():
    filepath = 'results/bounded_multirand_kdiamond_bound_pass.dat'
    for n in [100]:                              # EDIT the list values to set the network size
        # for k in range(3, int(n / 2) + 1):  # EDIT range parameters to set the network connectivity
        for k in range(3, 11):                  # for certain values it may explode

            G, nodes_to_analyze = kdiamond.generate_k_diamond(n, k)
            f = int((k - 1) / 2)
            CHANNEL_BOUND = f + 1

            for source in nodes_to_analyze:

                source = source[0]

                for iteration_counter1 in range(3):
                    byz_set = set(G.nodes())
                    byz_set.remove(source)
                    byz_set = set(random.sample(byz_set, f))

                    with open(filepath, 'a') as fd:
                        fd.write(str(n) + '\t' + str(k) + '\t' + str(f) + '\n')

                    broadcast_bounded_multirand_pass(G,f,source,byz_set, CHANNEL_BOUND, filepath)

def simulate_bounded_multirand_kpastedtree_pass():
    filepath = 'results/bounded_multirand_kpastedtree_bound_pass.dat'
    for n in [100]:  # EDIT the list values to set the network size
        # for k in range(3, int(n / 2) + 1):  # EDIT range parameters to set the network connectivity
        for k in range(3, 11):                  # for certain values it may explode

            G, nodes_to_analyze = kpasted.generate_k_pasted(n, k)
            f = int((k - 1) / 2)
            CHANNEL_BOUND = f + 1

            for source in nodes_to_analyze:

                source = source[0]

                for iteration_counter1 in range(3):
                    byz_set = set(G.nodes())
                    byz_set.remove(source)
                    byz_set = set(random.sample(byz_set, f))

                    with open(filepath, 'a') as fd:
                        fd.write(str(n) + '\t' + str(k) + '\t' + str(f) + '\n')

                    broadcast_bounded_multirand_pass(G,f,source,byz_set, CHANNEL_BOUND, filepath)

def simulate_bounded_multishor_randomreg_pass_act():
    filepath = 'results/bounded_multishort_randomreg_bound_pass_act.dat'
    for n in [50]:  # EDIT the list values to set the network size
        for k in range(3, int(n / 2) + 1):  # EDIT range parameters to set the network connectivity

            G = nx.random_regular_graph(k, n)
            while True:
                if approximation.node_connectivity(G) == k:
                    break
                else:
                    G = nx.random_regular_graph(k, n)

            CHANNEL_BOUND = int((k - 1) / 2) + 1

            for iteration_counter1 in range(3):

                for f in range(CHANNEL_BOUND):

                    byz_set = set(random.sample(G.nodes(), f))
                    for iteration_counter2 in range(1):
                        with open(filepath, 'a') as fd:
                            fd.write(str(n) + '\t' + str(k) + '\t' + str(f) + '\n')
                        while True:
                            source = random.sample(G.nodes(), 1)[0]
                            if source not in byz_set:
                                break

                        broadcast_bounded_multishor_pass_act(G, CHANNEL_BOUND -1, source, byz_set, CHANNEL_BOUND, filepath)

def simulate_bounded_multishor_multiwheel_pass_act():
    filepath = 'results/bounded_multishort_multiwheel_bound_pass_act.dat'
    for n in [50]:  # EDIT the list values to set the network size
        for k in range(4, int(n / 2) - 1, 2):  # EDIT range parameters to set the network connectivity

            G = multipartite_wheel.generate_multipartite_wheel(n, k)

            CHANNEL_BOUND = int((k - 1) / 2) + 1

            # selecting a Byzantine placement
            for iteration_counter1 in range(3):

                for f in range(CHANNEL_BOUND):

                    byz_set = set(random.sample(G.nodes(), f))

                    # selecting a sources

                    for iteration_counter2 in range(1):

                        with open(filepath, 'a') as fd:
                            fd.write(str(G.order()) + '\t' + str(k) + '\t' + str(f) + '\n')

                        while True:
                            source = random.sample(G.nodes(), 1)[0]
                            if source not in byz_set:
                                break

                        broadcast_bounded_multishor_pass_act(G, CHANNEL_BOUND-1, source, byz_set, CHANNEL_BOUND, filepath)

def simulate_bounded_multishor_kdiamond_pass_act():
    filepath = 'results/bounded_multishort_kdiamond_bound_pass_act.dat'

    for n in [50]:  # EDIT the list values to set the network size
        for k in range(3, int(n / 2) + 1):  # EDIT range parameters to set the network connectivity

            G, nodes_to_analyze = kdiamond.generate_k_diamond(n, k)

            CHANNEL_BOUND = int((k - 1) / 2) + 1

            for source in nodes_to_analyze:

                for f in range(CHANNEL_BOUND):

                    source = source[0]

                    for iteration_counter1 in range(1):
                        byz_set = set(G.nodes())
                        byz_set.remove(source)
                        byz_set = set(random.sample(byz_set, f))

                        with open(filepath, 'a') as fd:
                            fd.write(str(n) + '\t' + str(k) + '\t' + str(f) + '\n')

                        broadcast_bounded_multishor_pass_act(G, CHANNEL_BOUND -1, source, byz_set, CHANNEL_BOUND, filepath)

def simulate_bounded_multishor_kpastedtree_pass_act():
    filepath = 'results/bounded_multishort_kpastedtree_bound_pass_act.dat'
    for n in [50]:                              # EDIT the list values to set the network size
        for k in range(3, int(n / 2) + 1):  # EDIT range parameters to set the network connectivity

            G, nodes_to_analyze = kpasted.generate_k_pasted(n, k)

            CHANNEL_BOUND = int((k - 1) / 2) + 1

            for source in nodes_to_analyze:

                source = source[0]

                for f in range(CHANNEL_BOUND):

                    for iteration_counter1 in range(1):
                        byz_set = set(G.nodes())
                        byz_set.remove(source)
                        byz_set = set(random.sample(byz_set, f))

                        with open(filepath, 'a') as fd:
                            fd.write(str(n) + '\t' + str(k) + '\t' + str(f) + '\n')

                        broadcast_bounded_multishor_pass_act(G, CHANNEL_BOUND-1, source, byz_set, CHANNEL_BOUND, filepath)

def simulate_bounded_multishor_multiwheel_pass_act_worstplace():
    filepath = 'results/bounded_multishort_multiwheel_bound_pass_act_worstplace.dat'
    for n in [50]:                              # EDIT the list values to set the network size
        for k in range(4, int(n / 2) - 1, 2):  # EDIT range parameters to set the network connectivity

            G = multipartite_wheel.generate_multipartite_wheel(n, k)

            f = int((k - 1) / 2)
            CHANNEL_BOUND = f + 1

            byz_set = set()
            source = random.sample(G.nodes(), 1)[0]

            neightSource = set(nx.neighbors(G, source))
            for i in range(int(f / 2)):
                byz1 = neightSource.pop()
                for neight in neightSource:
                    if set(nx.neighbors(G, byz1)) != set(nx.neighbors(G, neight)):
                        byz2 = neight
                        break
                neightSource.remove(byz2)
                byz_set.add(byz1)
                byz_set.add(byz2)
            if f % 2 == 1:
                byz1 = neightSource.pop()
                byz_set.add(byz1)


            with open(filepath, 'a') as fd:
                fd.write(str(G.order()) + '\t' + str(k) + '\t' + str(f) + '\n')

            while True:
                source = random.sample(G.nodes(), 1)[0]
                if source not in byz_set:
                    break

            broadcast_bounded_multishor_pass_act(G, f, source, byz_set, CHANNEL_BOUND, filepath)

def simulate_bounded_multishor_gebwheel_pass_act_worstplace():
    filepath = 'results/bounded_multishort_genwheel_bound_pass_act_worstplace.dat'
    for n in [50]:                              # EDIT the list values to set the network size
        for k in range(3, int(n / 2) + 1):  # EDIT range parameters to set the network connectivity

            G = generalized_wheel.generate_generalized_wheel(n, k)

            f = int((k - 1) / 2)
            CHANNEL_BOUND = f + 1

            for attempt in range(10):

                byz_set = set(range(f))

                while True:
                    source = random.sample(G.nodes(), 1)[0]
                    if source not in byz_set and source > k/2:
                        break

                with open(filepath, 'a') as fd:
                    fd.write(str(n) + '\t' + str(k) + '\t' + str(f) + '\n')

                broadcast_bounded_multishor_pass_act(G, f, source, byz_set, CHANNEL_BOUND, filepath)

msgComplexity_dolev_maurer(n=20,k=3,filename='results/compare20_3.dat')

simulate_bounded_multirand_randomreg_pass()
simulate_bounded_multirand_multiwheel_pass()
simulate_bounded_multirand_kdiamond_pass()
simulate_bounded_multirand_kpastedtree_pass()

simulate_bounded_multishor_randomreg_pass_act()
simulate_bounded_multishor_multiwheel_pass_act()
simulate_bounded_multishor_kdiamond_pass_act()
simulate_bounded_multishor_kpastedtree_pass_act()

simulate_bounded_multishor_multiwheel_pass_act_worstplace()
simulate_bounded_multishor_gebwheel_pass_act_worstplace()
