# CADParser Reimplementation
## Introduction
This project was started by Frank Wang and Kevin Shao with an attempt to reimplement the [CADParser]([url](https://www.ijcai.org/proceedings/2023/200)) paper [1]. The CADParser was authored by Shengdi Zhou, Tianyi Tang, and Bin Zhou and published at the IJCAI (The International Joint Conference on Artificial Intelligence) in 2023. The main task of the paper is to generate construction command sequences from a given CAD geometry in the form of a BRep file.
### Methodology
The paper proposes an encoder-decoder model for the task of interest. The encoder is adapted from the [Uv-net paper]([url](https://arxiv.org/abs/2006.10211)) by Jayaraman _et.al._ [2] and serves to extract geometric information from the CAD model contained within BRep file. The decoder is an autoregressive Transformer [3] decoder that takes in a token representing start of a construction sequence along with a latent vector representing CAD geometry; the latent vector is the output of the encoder. Then, the decoder predicts the next construction command and continues until a complete construction sequence is generated.

Note that each construction commands have all been parametrized into a vector of 19 discrete values, where the first value indicates the type of command (eg. extrusion, line) and the remaining 18 values are some command-specific parameters. Since there are 12 commands within the paper's implementation, the command type value ranges from 0 to 11. The parameter values range from -1 to 255, where -1 means the parameter is unused (as construction types tend to use different parameters) and 0 to 255 correspond to some continuous value associated with the command that has been discretized.

In other words, the autoregressive model tries to make two categorical predictions at every iteration where it predicts the following construction command. The first is the command type (12 categories), and the second is the parameter type (257 categories).
### Main Contributions

## Chosen Result to Replicate

## Re-implementation Details
### Modifications to Original Paper
### Instructions for Running Our Code
### Computational Resources

## Our Results

## Conclusion

## References
[1] Zhou, S., Tang, T., & Zhou, B. (2023). CADParser: A Learning Approach of Sequence Modeling for B-Rep CAD. Proceedings of the Thirty-Second International Joint Conference on Artificial Intelligence (IJCAI-23).


[2] Pradeep Kumar Jayaraman, Aditya Sanghi, Joseph G Lambourne, Karl DD Willis, Thomas Davies, Hooman Shayani, and Nigel Morris. Uv-net: Learning from boundary representations. Proceedings
of the IEEE/CVF Conference on Computer Vision and Pattern Recognition.

[3] Vaswani, A., Shazeer, N., Parmar, N., Uszkoreit, J., Jones, L., Gomez, A. N., Kaiser, Ł., & Polosukhin, I. (2017). Attention is all you need. _Advances in Neural Information Processing Systems, 30_, 5998-6008.

