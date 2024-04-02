# EliteFurretAI
**The goal of this project (EliteFurretAI) is to build a superhuman bot to play VGC**. It is not to further research, nor is it to build a theoretically sound approach -- the goal is to be the best that no one ever was.

![AI Pokeball](docs/images/aipokeball.png)

### Summary
- In the purest sense, **a VGC battle is an imperfect information zero-sum two player game with a very large simultaneous action space, complex game mechanics, a high degree of stochasticity and an effectively continuous state space**.
    - VGC is an incredibly difficult AI problem. The fact that there is a large pool of top players (and they’re hard to sort) demonstrates the difficulty of this problem even for humans.
- After reading a wide array of literature, **we suggest we should tackle VGC directly** (instead of through Singles) because of the 40x action space, 3000x branching factor and the additional importance given to game interactions. These factors necessitate that an agent more deeply understands game mechanics and be more computationally efficient.
- Given these properties of VGC and top existing bots, **we will attempt to use a model-based search algorithm with depth-limited + heavily pruned search and a Nash Equilibrium-based value function that does not assume unobservable information**. We plan to initialize our agent with human data and train using self-play.
    - There is still quite a lot we need to understand about specifically how VGC behaves in order to make more informed algorithmic choices, and so this approach is very likely to change as we learn more.
- Industry’s dominance in making State of the Art agents demonstrates that **with enough talent, capacity and infrastructure, virtually all problems with VGC’s nature can be solved**. However, assessing the current state of resources available to us, the current bottlenecks for developing a successful agent is (in order):
    - **Talent** – Very few agents have seen dedicated and organized support over a span more than 6-9 months; having a dedicated and organized team is crucial.
    - **Engine** – Faster pokemon engine with ability to simulate (where we can control RNG)
    - **Capacity** – CPU for generating training data, GPU for inference
    - **Human Training Data** – while not essential, this will accelerate training convergence by orders of magnitude, reduce capacity needs and accelerate our own internal learning speed tremendously. It will also help our bot transition to playing humans more easily.

## Our Current Proposed Approach
From our analysis of avalailable literature, we’ve seen:
- Model-free alone is unlikely to produce superhuman performance without the capacity that we don’t have available
- Search is necessary for decision-time planning, and game abstractions are necessary to make search tractable
- The behavior of VGC from a game-theoretic perspective is still unknown, and theory might not help the practical purposes of making a superhuman bot.

Because of this last point, any approach we suggest pre-hoc is very likely to change as we learn more about what works in practice and how VGC behaves. That being said, we feel the best approach will likely be:

Basic Foundation:
- **Policy** – based on Nash Equilibrium using Deep Learning to create the best policy/value networks that generalize to the game well. This allows for most flexibility for decision-time planning.
- **Search** – during decision-time planning, we can explore the following options:
    - Using the above networks directly if sufficiently accurate
    - Using Depth-Limited search
    - Using MCTS
- **Game Abstractions** – these will help speed up both training our networks and our speed. We will explore the following abstractions:
    - Decision Abstractions
        - Using a network to pick top N likely actions from opponents and only rely on search using these
        - Using a network to eliminate exploring states that have low predicted value for our agents
    - State Abstractions
        - Use a network that embeds each state, and use Locality-Sensitive Hashing to quickly eliminate branches to explore if they are very similar to other previously explored
        - Binning HP (exact HP values mostly don’t matter)
        - Binning PP (exact PP values mostly don’t matter)
        - Use a network to predict the opponent’s infostate/the worldstate
    - Chance Abstractions
        - Only explore good luck or bad luck (Athena assumes one RNG roll per turn per player)
        - Ignore unlikely outcomes

**Training Approach**: We will generate data via self-play, guided with human data
- **Self-Play**: given the complex game dynamics and partial observability, we need extraordinary amounts of data, which can only be reasonably generated by self-play. We will likely use MCCFR to generate data for optimal policies (in an abstracted game).
- **Initializing with Human Data**: While not necessary, this will help encode game mechanics, improve performance against humans (by better exploring likely human-caused states)  and drastically speed up training, making this approach feasible. Concretely, we will generate some training samples based on human-like decisions learned from human data.

**Increasing Problem Complexity:** Given the high degree of complexity of the properties VGC has, we believe we should start with more constrained problems, verify our approaches and gradually introduce complexities to overcome computational constraints.

## Stages of Development
To build towards the above, we can separate development into 6 stages:

**Stage I**: Advocate for external support
- Obtain GPUs and CPUs to accelerate data generation and inference; evaluate costs and survey grants. Having multiple threads will allow for better decision-time planning as well.
- Build a fast pokemon engine (supports RNG manipulation and simulation). This will be necessary for search during decision-time planning and will unblock self-play.
- Build game engine utilities (inverse damage calculator, log interpreter, etc) to help our bot ingest the maximal amount of information to improve performance
- Apply for human-based Training Data (ideally omniscient, but doesn’t necessarily need to be); as you can see above/below, the ability to predict the worldstate cascades into better predictions across every component of the agent

**Stage II**: Build supervised networks
- **Information Network**: Infostate + history → E[Worldstate]
    - This is most important as if this can get accuracy of up to 95%+, we can transition from imperfect to perfect information games and save computation.
    - There is a dependency on game engine utilities
    - Needs to optimize for probability of information
    - Should also be evaluated by how effective it is based on the # of potential histories one can have, and how many it can eliminate
- **“Value” Network**: Infostate + E[Worldstate] → P(win)
    - The higher the accuracy here, the less we need to search, meaning we will face less computational constraints
    - This is not a truly valuable network because it isn’t sound (based on average policy across players), but we can try it for shits and giggles and see if it works like it did in FutreSightAI
    - Note: this has a dependency on the Information Network accuracy
- **Human Policy Network**: PBS + E[Worldstate] → P(action) over all opponent legal actions
    - The higher the accuracy here, the less we need to search, meaning we will face less computational constraints
    - Note: this has a dependency on the Information Network accuracy

**Stage III**: Test a FutureSightAI-like approach on VGC, just because I’m curious
- Take top M likely worldstates, with probabilities of each
    - Take top N<sub>-i</sub> opponent actions by likelihood (store likelihood)
    - Simulate future states w/ chance using abstractions (let’s say C possible states from joint actions) using all top N<sub>-i</sub> actions
    - Identify Top N<sub>i</sub> best response actions to opponent’s, and calculate probability they would be chosen
- For each action, sum up the expected value across each worldstate, joint action and chance (M*N*C), incorporating probability they would be chosen (since opponent thinks we might play like this)
- Take an action proportional to the expected value
- Consider going one level deeper with more abstraction

**Step IV**: Train ESCHER on a smaller game, with self-play
- Build game engine w/ abstractions (large amount of work)
- Experiment with opponent policy during MCCFR (e.g. using a human policy network, random play, on-policy, or some combination)
- Consider extending ESCHER by training an average Value network directly
- Evaluate performance

**Step V**: Implement AI on Decision-Time Planning with ESCHER networks
- Try using ESCHER networks directly
- Try using Depth Limited Solving with Linear CFR+ w/ above game abstractions

**Step VI**: Expand to full game
- Using both above approaches
- Attempt more intense abstractions

More details on this approach, thinking and understanding that led us to this development plan can be found [here](https://docs.google.com/document/d/14menCHw8z06KJWZ5F_K-MjgWVo_b7PESR7RlG-em4ic/edit).

### Why the name EliteFurretAI?
Eventually, this bot will make Furret central the VGC meta. Because Nintendo will not give Furret the buffs it desperately needs, only a superhuman AI will be able to derive the right team to build around this monster and unlease its latent potential.

![OG Furret](docs/images/furret.png)
