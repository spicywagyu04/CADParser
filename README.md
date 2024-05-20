# CADParser Reimplementation
## Introduction
This project was started by Frank Yang and Kevin Shao with an attempt to reimplement the [CADParser]([url](https://www.ijcai.org/proceedings/2023/200)) paper [1]. The CADParser was authored by Shengdi Zhou, Tianyi Tang, and Bin Zhou and published at the IJCAI (The International Joint Conference on Artificial Intelligence) in 2023. The main task of the paper is to generate construction command sequences that can readily used for user-editing and the creation of 3D CAD from a given CAD geometry in the form of a BRep file.
### Methodology
The paper proposes an encoder-decoder model for the task of interest. The encoder is adapted from the [Uv-net paper]([url](https://arxiv.org/abs/2006.10211)) by Jayaraman _et.al._ [2] and serves to extract geometric information from the CAD model contained within BRep file. The decoder is an autoregressive Transformer [3] decoder that takes in a token representing start of a construction sequence along with a latent vector representing CAD geometry; the latent vector is the output of the encoder. Then, the decoder predicts the next construction command and continues until a complete construction sequence is generated.


<img width="559" alt="CADParser commands with type and parameters" src="https://github.com/spicywagyu04/CADParser/assets/96509953/ba2fdc4a-d3c1-4eb6-89e1-b42c44a8306a">


Note that each construction commands have all been parametrized into a vector of 17 discrete values, where the first value indicates the type of command (eg. extrusion, line) and the remaining 16 values are some command-specific parameters. Since there are 12 commands within the paper's implementation, the command type value ranges from 0 to 11. The parameter values range from -1 to 255, where -1 means the parameter is unused (as construction types tend to use different parameters) and 0 to 255 correspond to some continuous value associated with the command that has been discretized.

In other words, the autoregressive model tries to make two categorical predictions at every iteration where it predicts the following construction command. The first is the command type (12 categories), and the second is the parameter type (257 categories).

<img width="1150" alt="CADParser model architecture" src="https://github.com/spicywagyu04/CADParser/assets/96509953/9e436d1f-a12f-4ac9-b687-4ec9c9e386e3">

### Main Contributions
Compared to the DeepCAD paper [4], the CADParser paper expanded the set of processable CAD construction commands from 4 to 10. In addition, it provides a public dataset of size 40k+ containing CAD models with their construction command sequences. This dataset has samples with more complex commands that the CADParser model is able to process.

## Chosen Result to Replicate
<img width="579" alt="CADParser results" src="https://github.com/spicywagyu04/CADParser/assets/96509953/200536ec-c454-4436-8b15-a06035e6e955">

In our reimplementation project, we wish to replicate the CADParser's IOU and Recall metric scores, which are 0.81 and 0.64 respectively. 

IOU: a measure of geometric similarity between CAD models reconstructed from generated CAD construction command sequences and the ground truth CAD model.

Recall: the proportion of generated command sequences that can be successfully reconstructed into CAD models.

## Re-implementation Details
### Modifications to Original Paper
Since CADParser does not have public code, we needed to make the following modifications due to our limited domain knowledge and the paper's ambiguity in certain sections:

* We used Fusion360 dataset instead of the CADParser dataset to train our model. This was because the CADParser dataset contains complex commands in JSON format that are difficult to preprocess into vectors. Preprocessing requires specific domain knowledge in CAD, and we did not have sufficient time to implement it. We were able to find a preprocessing script for commands line, arc, circle, and extrusion, which are the only commands that the Fusion360 dataset contains.
  * The Fusion360 dataset contains around 8200 samples, compared to CADParser's 40,000+.
* We implemented our own version of Fusion Module. The general architecture is similar to the paper's specification. The paper was not clear about how the Fusion Module handles variable command sequence length. Hence, we used a dynamic linear layer. Also, the paper did not specify Fusion Module's output dimension, which in our implementation is set to 64.
* The rest of the architecture as described in the paper. Given the face-adjacency graph, which is a form of the graph representation of the 3D CAD, and the npz vector format, represents the json construction sequence after processing by the script, The face-adjacency graph is passed through the UV-Net to output the node-wise embedding and graph-wise embedding. The node-wise embedding are input as the keys and values to the masked-attention block, while the graph-wise embedding is combined with the generated tokens to be the input the masked-cross attention. In our decoder, both the embedder and the autoregressive transformer decoder are implemented according to the paper. Then, similar to the paper, two projection heads is used to projects the output into the command type and the command parameters.

Here is an overview of our implementation.
Given the dataset to be around 8000 pairs of construction sequence in JSON and the face-adjacency graph in DGL objects. We first used the sequence parsing code provided to convert the constructio sequence into the vector format representatino in NPZ file.
For the encoder (UV-Net), we have two parts: the curve encoder and the surface encoder. For both encoders, we used 3 Convolutional layer that has (6x64), (64x128), (128x256), and followed with average pooling and a fully-connected layer that downsamples the 256 to 64. Then a GCN is followed. We followed the node convolution and edge convolution operation in the UV-Net paper. (There are two separate equations describing each operation). There are two outputs from the encoder: a node-wise embedding describing each node and a graph-wise embedding processed by a pooling. 

For the decoder, we first have a CAD embedder that projects each CAD to a vector of 64 dimension, which has the positional embedding, comand embedding, parameter embedding, and group embedding. A fusion module is employed, which contains a linear layer, to combine the embedded CAD (64 dimension) and the graph-wise embedding (128 dimension)from the encoder. The output size from the fusion is again 64 dimension.
The output of the fusion module is inputted to the autoregressive transformer block. The block consists of 8 atttention heads with four decoder layers. The node-wise embedding from the encoder is input as the memory (which is the Q and V) of the second attention block. The output of the transformer decoder is separated by two headers, each with a softmax to calculate the corresponding command type and command parameters. 

To calculate the loss, the cross entropy loss is used. We used the same learning rate, scheduler, and other training setting as described in the paper Section 3.4.

### Instructions for Running Our Code
We recommend to run our code in CADParser.ipynb on Google Colab. The only dependency that requires installation is the DGL package for CUDA. DGL is a library for handling graph representations which we use for representing our CAD models' geometric features. The remaining dependencies are all within the default Colab environment and do not require installation.

The code should be able to run successfully by running every cell from the top.

### Computational Resources
We use a Google Colab L4 GPU to run our notebook, which runs about 1 hour for 100 epochs. A T4 GPU would also work.

## Results and Analysis
Here is a plot of our training loss:
<img width="902" alt="training-loss" src="https://github.com/spicywagyu04/CADParser/assets/96509953/05da3d9d-164e-4b9d-9e23-11a1b26fa12e">

Unfortunately, we have yet to generate actual CAD models from our command sequences, as doing so requires using a CAD-specific software.

### Challenges
The main challenge encountered during the re-implementation is that the author have left out some details in their paper. This makes our implementation with ambiguous and depending on the interpretation of the words. Also, the author does not provide the processing code that they have used. After realized that it requires the CAD domain knowledge to write the processing code to parse their dataset, especially the construction sequence part of the dataset, we need to find another equivalent dataset that has similar setting as the one in the paper but with less complexity in terms of the number of commands and the number of parameters. 

## Conclusion and Future Work
Through implementing this project, we have several key takeaways. First, we hand the hands-on experience with transformer and graph models. We gained a practical knowledge in implementing these models in a real world setting. We also realized that data processing is a critical and time-consuming step in the ML projects. Third, through this combination of the GCN with transformer decoder, we also learned that we cannot combine the strength of different models to leverage their complementary strengths. Lastly, ML in real world setting can be very huge. Therefore, careful planning is needed.

There is much that we would like to implement in the future. In fact, we plan to get this project to work over summer. What we need to do is fix the training loss to ensure that our model is actually learning. Then, we could research about softwares to convert construction command sequences into CAD models. Last but not least, we should research ways to parse JSON data of more complex CAD commands so that we could integrate CADParser's own dataset in our project.

## References
[1] Zhou, S., Tang, T., & Zhou, B. (2023). CADParser: A Learning Approach of Sequence Modeling for B-Rep CAD. Proceedings of the Thirty-Second International Joint Conference on Artificial Intelligence (IJCAI-23).


[2] Pradeep Kumar Jayaraman, Aditya Sanghi, Joseph G Lambourne, Karl DD Willis, Thomas Davies, Hooman Shayani, and Nigel Morris. Uv-net: Learning from boundary representations. Proceedings
of the IEEE/CVF Conference on Computer Vision and Pattern Recognition.

[3] Vaswani, A., Shazeer, N., Parmar, N., Uszkoreit, J., Jones, L., Gomez, A. N., Kaiser, Ł., & Polosukhin, I. (2017). Attention is all you need. _Advances in Neural Information Processing Systems, 30_, 5998-6008.

[4] Wu, R., Xiao, C., & Zheng, C. (2021). DeepCAD: A Deep Generative Network for Computer-Aided Design Models. arXiv preprint arXiv:2105.09492. Retrieved from https://arxiv.org/abs/2105.09492

