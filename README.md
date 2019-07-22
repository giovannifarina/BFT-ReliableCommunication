# Multi Hop Byzantine Reliable Broadcast with honest dealer made practical

Silvia Bonomi, Giovanni Farina [✉](mailto:giovanni.farina@lip6.fr), Sébastien Tixeuil

Simulation Code

Reference: https://arxiv.org/abs/1903.08988
#
The simulation code is composed by:

- Python scripts of the simulations;
- A fork of Vera-Licona Research Group [generator](https://github.com/VeraLiconaResearchGroup/Minimal-Hitting-Set-Algorithms) for the minimal hitting set problem, supporting the VC solver;
-   The [networkx](https://networkx.github.io/) implementations for [k-pasted-tree](https://github.com/giovannifarina/kpastedtree), [k-diamond](https://github.com/giovannifarina/kdiamond) , generalized wheel and multipartite wheel.
#
Required Python Module:
-   [networkx](https://networkx.github.io/)
-   [numpy](http://www.numpy.org/)
#
Setting up the simulation environment on Ubuntu:
-   Clone this repository;
-   Clone the VC solver repository and install required [dependencies](https://github.com/VeraLiconaResearchGroup/Minimal-Hitting-Set-Algorithms) executing the subsequent commands:    
    - `sudo apt-get install libboost-all-dev`
    - `cd BFT-BRB`
    - `mkdir results`    
    - `git clone https://github.com/giovannifarina/Minimum-Hitting-Set-Fork.git MHS`
    - `make -C MHS -j`
    
-   Comment/uncomment/edit final lines in `Reliable_Broadcast.py` to set a specific simulation.
