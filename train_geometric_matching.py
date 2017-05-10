import cPickle as pickle
import numpy as np
import theano_funcs
import utils
import vgg16

from lasagne.layers import set_all_param_values, get_all_param_values
from os.path import join
from tqdm import tqdm


def train_geometric_matching():
    print('building model')
    layers = vgg16.build_model()

    # file to store the learned weights
    weightsfile = join('weights', 'weights.pickle')

    # initialize the feature extraction layers
    pretrainfile = join('weights', 'vgg16.pkl')
    print('initializing feature extraction layers from %s' % (pretrainfile))
    with open(pretrainfile, 'rb') as f:
        data = pickle.load(f)
    set_all_param_values(layers['pool4a'], data['param values'][0:20])
    set_all_param_values(layers['pool4b'], data['param values'][0:20])

    #with open(weightsfile, 'rb') as f:
    #    param_values = pickle.load(f)
    #set_all_param_values(layers['trans'], param_values)

    mean = data['mean value']

    max_epochs = 5000
    batch_size = 16
    sample_every = 25  # visualizes network output every n epochs
    sample_dir = join('data', 'samples')
    voc_fpath = '/media/hdd/hendrik/datasets/pascal-2011'
    train_fpaths, valid_fpaths = utils.train_val_split(voc_fpath)

    print('compiling theano functions for training')
    train_func = theano_funcs.create_train_func(layers)
    print('compiling theano functions for validation')
    valid_func = theano_funcs.create_valid_func(layers)

    try:
        for epoch in range(1, max_epochs + 1):
            print('epoch %d' % (epoch))
            train_losses = []
            num_train_idx = (len(train_fpaths) + batch_size - 1) / batch_size
            train_iter = utils.get_batch_idx(len(train_fpaths), batch_size)
            for i, idx in tqdm(train_iter, total=num_train_idx, leave=False):
                X_crop_train, X_warp_train, M_train = utils.prepare_batch(
                    train_fpaths[idx], mean)
                M, train_loss = train_func(X_crop_train, X_warp_train, M_train)
                train_losses.append(train_loss)
                if epoch % sample_every == 0:
                    utils.plot_samples(X_crop_train, X_warp_train, M, mean,
                                       prefix=join(sample_dir, 'train_%d' % i))
            print(' train loss = %.6f' % (np.mean(train_losses)))

            valid_losses = []
            num_valid_idx = (len(valid_fpaths) + batch_size - 1) / batch_size
            valid_iter = utils.get_batch_idx(len(valid_fpaths), batch_size)
            for i, idx in tqdm(valid_iter, total=num_valid_idx, leave=False):
                X_crop_valid, X_warp_valid, M_valid = utils.prepare_batch(
                    valid_fpaths[idx], mean)
                M, valid_loss = valid_func(X_crop_valid, X_warp_valid, M_valid)
                valid_losses.append(valid_loss)
                if epoch % sample_every == 0:
                    utils.plot_samples(X_crop_valid, X_warp_valid, M, mean,
                                       prefix=join(sample_dir, 'valid_%d' % i))
            print(' valid loss = %.6f' % (np.mean(valid_losses)))
    except KeyboardInterrupt:
        print('caught ctrl-c, stopped training')

    print('saving weights to %s' % (weightsfile))
    weights = get_all_param_values(layers['trans'])
    with open(weightsfile, 'wb') as f:
        pickle.dump(weights, f, protocol=pickle.HIGHEST_PROTOCOL)


if __name__ == '__main__':
    train_geometric_matching()