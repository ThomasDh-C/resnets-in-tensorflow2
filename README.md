# cifar-vs-tensorflow2
Nice and tidy implementation of classical neural network for classification in tensorflow 2.0

Requirements:
- tensorflow 2.0

Set experiments in experiments.yaml \
Run using: python run_experiments.py

```
Implemented models (cifar versions only):
  From "Very Deep Convolutional Neural Network Based Image Classification Using Small Training Sample Size":
    - VGG11
    - VGG16
    - VGG19

  From "Deep Residual Learning for Image Recognition":
    - Resnet20
    - Resnet32
    - Resnet44
    - Resnet56
    - Resnet110
    - Resnet1001

  From "Identity Mappings in Deep Residual Networks" (with preactivated layers):
    - Resnet20
    - Resnet32
    - Resnet44
    - Resnet56
    - Resnet110
    - Resnet164
    - Resnet1001
```

Default training schedule:
- SGD with momentum 0.9
- warm-up LR = 0.01 for iterations [0, 400)
- LR = 0.1 for iterations [400, 32000)
- LR = 0.01 for iterations [32000, 48000)
- LR = 0.001 for iterations [48000, 64000)
- Weight decay = 0.0001

Example of experiment:
```
module: 'Models.Resnets'
model: 'cifar_resnet110'
model_parameters:
    shortcut_mode: 'B' #(A or B as in Deep Residual Learning for Image Recognition)
    block_type: 'original' #(original for Resnet v1, preactivated for Resnet v2)
train_parameters:
    logdir: 'logs'
    run_name: 'resnet110_v1'
    num_steps: 64000 #(iterations after which the training ends)
    log_interval: 400 #(how often statistics are printed and saved to tensorboard)
    val_interval: 4000 #(how often validation on the test set is done)
skip_error_test: True #(whether to skip a quick run before beginning the actual training)
```
