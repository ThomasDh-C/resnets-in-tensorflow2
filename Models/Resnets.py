import os
import tensorflow as tf


def regularized_padded_conv(*args, **kwargs):
    return tf.keras.layers.Conv2D(*args, **kwargs, padding='same', kernel_regularizer=_regularizer,
                                  kernel_initializer='he_normal', use_bias=False)


def bn_relu(x):
    x = tf.keras.layers.BatchNormalization()(x)
    return tf.keras.layers.ReLU()(x)


def shortcut(x, filters, stride, mode):
    if x.shape[-1] == filters:
        return x
    elif mode == 'B' or mode == 'projection':
        return regularized_padded_conv(filters, 1, strides=stride)(x)
    elif mode == 'A' or mode == 'padding':
        return tf.pad(tf.keras.layers.MaxPool2D(1, stride)(x) if stride>1 else x,
                      paddings=[(0, 0), (0, 0), (0, 0), (0, filters - x.shape[-1])])
    else:
        raise KeyError("Parameter shortcut_type not recognized!")
    

def original_block(x, filters, stride=1, **kwargs):
    c1 = regularized_padded_conv(filters, 3, strides=stride)(x)
    c2 = regularized_padded_conv(filters, 3)(bn_relu(c1))
    c2 = tf.keras.layers.BatchNormalization()(c2)
    
    x = shortcut(x, filters, stride, mode=_shortcut_type)
    return tf.keras.layers.ReLU()(tf.add(x, c2))
    
    
def preactivation_block(x, filters, stride=1, preact_block=False):
    flow = bn_relu(x)
    if preact_block:
        x = flow
        
    c1 = regularized_padded_conv(filters, 3, strides=stride)(flow)
    if _dropout:
        c1 = tf.keras.layers.Dropout(_dropout)(c1)
        
    c2 = regularized_padded_conv(filters, 3)(bn_relu(c1))
    x = shortcut(x, filters, stride, mode=_shortcut_type)
    return tf.add(x, c2)


def bootleneck_block(x, filters, stride=1, preact_block=False):
    flow = bn_relu(x)
    if preact_block:
        x = flow
         
    c1 = regularized_padded_conv(filters//_bootleneck_width, 1)(flow)
    c2 = regularized_padded_conv(filters//_bootleneck_width, 3, strides=stride)(bn_relu(c1))
    c3 = regularized_padded_conv(filters, 1)(bn_relu(c2))
    
    x = shortcut(x, filters, stride, mode=_shortcut_type)
    return tf.add(x, c3)


def group_of_blocks(x, block_type, num_blocks, filters, stride):   
    x = block_type(x, filters, stride, preact_block=True)
    for i in range(num_blocks-1):
        x = block_type(x, filters)
    return x


def Resnet(input_shape, n_classes, l2_reg=0.5e-4, group_sizes=(2, 2, 2), features=(16, 32, 64), strides=(1, 2, 2),
           shortcut_type='B', block_type='preactivated', first_conv={"filters": 16, "kernel_size": 3, "strides": 1},
           dropout=0, cardinality=1, bootleneck_width=4):
    
    global _regularizer, _shortcut_type, _preact_projection, _dropout, _cardinality, _bootleneck_width
    _bootleneck_width = bootleneck_width # used in ResNeXts and bootleneck blocks
    _regularizer = tf.keras.regularizers.l2(l2_reg)
    _shortcut_type = shortcut_type # used in blocks
    _cardinality = cardinality # used in ResNeXts
    _dropout = dropout # used in Wide ResNets
    
    block_types = {'preactivated': preactivation_block,
                   'bootleneck': bootleneck_block,
                   'original': original_block}
    
    selected_block = block_types[block_type]
    inputs = tf.keras.layers.Input(shape=input_shape)
    flow = regularized_padded_conv(**first_conv)(inputs)
    
    if block_type == 'original':
        flow = bn_relu(flow)
    
    for group_size, feature, stride in zip(group_sizes, features, strides):
        flow = group_of_blocks(flow,
                               block_type=selected_block,
                               num_blocks=group_size,
                               filters=feature,
                               stride=stride)
    
    if block_type != 'original':
        flow = bn_relu(flow)
    
    flow = tf.keras.layers.GlobalAveragePooling2D()(flow)
    outputs = tf.keras.layers.Dense(n_classes, kernel_regularizer=_regularizer)(flow)
    model = tf.keras.Model(inputs=inputs, outputs=outputs)
    return model


def load_weights_func(model, model_name):
    try: model.load_weights(os.path.join('saved_models', model_name + '.tf'))
    except tf.errors.NotFoundError: print("No weights found for this model!")
    return model


def cifar_resnet20(block_type='preactivated', shortcut_type='B', load_weights=False):
    model = Resnet(input_shape=(32, 32, 3), n_classes=10, l2_reg=0.5e-4, group_sizes=(3, 3, 3), features=(16, 32, 64),
                   strides=(1, 2, 2), first_conv={"filters": 16, "kernel_size": 3, "strides": 1}, shortcut_type=shortcut_type, 
                   block_type=block_type)
    if load_weights: model = load_weights_func(model, 'cifar_resnet20_' + block_type)
    return model


def cifar_resnet32(block_type='preactivated', shortcut_type='B', load_weights=False):
    model = Resnet(input_shape=(32, 32, 3), n_classes=10, l2_reg=0.5e-4, group_sizes=(5, 5, 5), features=(16, 32, 64),
                   strides=(1, 2, 2), first_conv={"filters": 16, "kernel_size": 3, "strides": 1}, shortcut_type=shortcut_type, 
                   block_type=block_type)
    if load_weights: model = load_weights_func(model, 'cifar_resnet32_' + block_type)
    return model


def cifar_resnet44(block_type='preactivated', shortcut_type='B', load_weights=False):
    model = Resnet(input_shape=(32, 32, 3), n_classes=10, l2_reg=0.5e-4, group_sizes=(7, 7, 7), features=(16, 32, 64),
                   strides=(1, 2, 2), first_conv={"filters": 16, "kernel_size": 3, "strides": 1}, shortcut_type=shortcut_type, 
                   block_type=block_type)
    if load_weights: model = load_weights_func(model, 'cifar_resnet44_' + block_type)
    return model


def cifar_resnet56(block_type='preactivated', shortcut_type='B', load_weights=False):
    model = Resnet(input_shape=(32, 32, 3), n_classes=10, l2_reg=0.5e-4, group_sizes=(9, 9, 9), features=(16, 32, 64),
                   strides=(1, 2, 2), first_conv={"filters": 16, "kernel_size": 3, "strides": 1}, shortcut_type=shortcut_type, 
                   block_type=block_type)
    if load_weights: model = load_weights_func(model, 'cifar_resnet56_' + block_type)
    return model


def cifar_resnet110(block_type='preactivated', shortcut_type='B', load_weights=False):
    model = Resnet(input_shape=(32, 32, 3), n_classes=10, l2_reg=0.5e-4, group_sizes=(18, 18, 18), features=(16, 32, 64),
                   strides=(1, 2, 2), first_conv={"filters": 16, "kernel_size": 3, "strides": 1}, shortcut_type=shortcut_type, 
                   block_type=block_type)
    if load_weights: model = load_weights_func(model, 'cifar_resnet110_' + block_type)
    return model


def cifar_resnet164(shortcut_type='B', load_weights=False):
    model = Resnet(input_shape=(32, 32, 3), n_classes=10, l2_reg=0.5e-4, group_sizes=(18, 18, 18), features=(64, 128, 256),
                   strides=(1, 2, 2), first_conv={"filters": 16, "kernel_size": 3, "strides": 1}, shortcut_type=shortcut_type, 
                   block_type='bootleneck')
    if load_weights: model = load_weights_func(model, 'cifar_resnet164')
    return model


def cifar_resnet1001(shortcut_type='B', load_weights=False):
    model = Resnet(input_shape=(32, 32, 3), n_classes=10, l2_reg=0.5e-4, group_sizes=(111, 111, 111), features=(64, 128, 256),
                   strides=(1, 2, 2), first_conv={"filters": 16, "kernel_size": 3, "strides": 1}, shortcut_type=shortcut_type, 
                   block_type='bootleneck')
    if load_weights: model = load_weights_func(model, 'cifar_resnet1001')
    return model


def cifar_wide_resnet(N, K, block_type='preactivated', shortcut_type='B', dropout=0):
    assert (N-4) % 6 == 0, "N-4 has to be divisible by 6"
    lpb = (N-4) // 6 # layers per block - since N is total number of convolutional layers in Wide ResNet
    model = Resnet(input_shape=(32, 32, 3), n_classes=10, l2_reg=2.5e-4, group_sizes=(lpb, lpb, lpb), features=(16*K, 32*K, 64*K),
                   strides=(1, 2, 2), first_conv={"filters": 16, "kernel_size": 3, "strides": 1}, shortcut_type=shortcut_type,
                   block_type=block_type, dropout=dropout)
    return model


def cifar_WRN_16_4(shortcut_type='B', load_weights=False, dropout=0):
    model = cifar_wide_resnet(16, 4, 'preactivated', shortcut_type, dropout=dropout)
    if load_weights: model = load_weights_func(model, 'cifar_WRN_16_4')
    return model


def cifar_WRN_40_4(shortcut_type='B', load_weights=False, dropout=0):
    model = cifar_wide_resnet(40, 4, 'preactivated', shortcut_type, dropout=dropout)
    if load_weights: model = load_weights_func(model, 'cifar_WRN_40_4')
    return model


def cifar_WRN_16_8(shortcut_type='B', load_weights=False, dropout=0):
    model = cifar_wide_resnet(16, 8, 'preactivated', shortcut_type, dropout=dropout)
    if load_weights: model = load_weights_func(model, 'cifar_WRN_16_8')
    return model


def cifar_WRN_28_10(shortcut_type='B', load_weights=False, dropout=0):
    model = cifar_wide_resnet(28, 10, 'preactivated', shortcut_type, dropout=dropout)
    if load_weights: model = load_weights_func(model, 'cifar_WRN_28_10')
    return model


def cifar_resnext(N, cardinality, width, shortcut_type='B',):
    assert (N-3) % 9 == 0, "N-4 has to be divisible by 6"
    lpb = (N-3) // 9 # layers per block - since N is total number of convolutional layers in Wide ResNet
    model = Resnet(input_shape=(32, 32, 3), n_classes=10, l2_reg=0.5e-4, group_sizes=(lpb, lpb, lpb), features=(16*width, 32*width, 64*width),
                   strides=(1, 2, 2), first_conv={"filters": 16, "kernel_size": 3, "strides": 1}, shortcut_type=shortcut_type,
                   block_type='resnext', cardinality=cardinality, width=width)
    return model