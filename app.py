texture_similarity_tv/AutoEncoder.py                                                                0000664 0001750 0001750 00000006737 13053754601 020204  0                                                                                                    ustar   bhorkar                         bhorkar                                                                                                                                                                                                                from __future__ import print_function
import numpy as np
import tensorflow as tf
import math as math
import glob
import cv2
import optparse
import os
import matplotlib.pyplot as plt
import skimage.transform
import config
import logging
import pickle



class AutoEncoder(object):

    def encoder(self, x):
        # Encoder Hidden layer with sigmoid activation #1
        if self.n_layer == 1:
            layer_1 = tf.nn.sigmoid(tf.add(tf.matmul(x, self.weights['encoder_h1']),
                                       self.biases['encoder_b1']))
            return layer_1
        elif self.n_layer == 2:
        # Decoder Hidden layer with sigmoid activation #2
            layer_1 = tf.nn.sigmoid(tf.add(tf.matmul(x, self.weights['encoder_h1']),
                                       self.biases['encoder_b1']))
            layer_2 = tf.nn.sigmoid(tf.add(tf.matmul(layer_1, self.weights['encoder_h2']),
                                       self.biases['encoder_b2']))
            return layer_2

    def decoder(self, x):
        # Encoder Hidden layer with sigmoid activation #1
        if self.n_layer == 1:
            layer_1 = tf.nn.sigmoid(tf.add(tf.matmul(x, self.weights['decoder_h2']),
                                           self.biases['decoder_b2']))
            return layer_1
        elif self.n_layer == 2:
            layer_1 = tf.nn.sigmoid(tf.add(tf.matmul(x, self.weights['decoder_h1']),
                                           self.biases['decoder_b1']))
            # Decoder Hidden layer with sigmoid activation #2
            layer_2 = tf.nn.sigmoid(tf.add(tf.matmul(layer_1, self.weights['decoder_h2']),
                                           self.biases['decoder_b2']))
            return layer_2

    def __init__(self, n_layers, feature_dim_used):
        learning_rate = 0.001
        self.batch_size = 16
        self.display_step = 100
        self.n_layer = n_layers;
        self.n_hidden_1 = 512  # 1st layer num features
        self.n_hidden_2 = 64  # 2nd layer num features
        n_hidden_1 = self.n_hidden_1; 
        n_hidden_2 = self.n_hidden_2;
        n_input = feature_dim_used
        gpu_options = tf.GPUOptions(per_process_gpu_memory_fraction=0.5)
        self.config = tf.ConfigProto(gpu_options=gpu_options)

        self.weights = {
            'encoder_h1': tf.Variable(tf.random_normal([n_input, n_hidden_1]), name="eh1"),
            'encoder_h2': tf.Variable(tf.random_normal([n_hidden_1, n_hidden_2]), name="eh2"),
            'decoder_h1': tf.Variable(tf.random_normal([n_hidden_2, n_hidden_1]), name="dh1"),
            'decoder_h2': tf.Variable(tf.random_normal([n_hidden_1, n_input]), name="dh2"),
        }
        self.biases = {
            'encoder_b1': tf.Variable(tf.random_normal([n_hidden_1]), name="eb1"),
            'encoder_b2': tf.Variable(tf.random_normal([n_hidden_2]), name="eb2"),
            'decoder_b1': tf.Variable(tf.random_normal([n_hidden_1]), name="db2"),
            'decoder_b2': tf.Variable(tf.random_normal([n_input]), name="db2"),
        }
        self.X = tf.placeholder("float", [None, feature_dim_used])
        self.encoder_op = self.encoder(self.X)
        self.decoder_op = self.decoder(self.encoder_op)
        self.y_pred = self.decoder_op
        self.y_true = self.X


# Define loss and optimizer, minimize the squared error
        self.cost = tf.reduce_mean(tf.pow(self.y_true - self.y_pred, 2))
        self.optimizer = tf.train.RMSPropOptimizer(
            learning_rate).minimize(self.cost)


if __name__ == '__main__':
    pass
                                 texture_similarity_tv/config.py                                                                     0000664 0001750 0001750 00000000730 13053754667 017240  0                                                                                                    ustar   bhorkar                         bhorkar                                                                                                                                                                                                                CNNInfo = dict(
  caffe_root = '../../../bin/caffe/', 
  net = 'VGG',  
  input_dict = "../../fashion_train/temp/",
  layer = 'pool1',
  feature_size = 64*64,
  keep_aspect_ratio = False
)

LSFModelInfo = dict(
   model_dict = "LSFmodel/",
   indexFile =  "saveImage",
   nLSFModelTrees = 10,   #divide the training set into nLSF trees 
   n_candidates   = 50,
   n_estimators   = 10
)

AutoEncoderInfo = dict(
   enable_autoencoder = False,
   n_layers           = 0
)
 
                                        texture_similarity_tv/DeepDescriptor.py                                                             0000664 0001750 0001750 00000012120 13053754601 020667  0                                                                                                    ustar   bhorkar                         bhorkar                                                                                                                                                                                                                import numpy as np
import matplotlib.pyplot as plt
import numpy
import time
from sklearn.decomposition import PCA as sklearnPCA
from numpy import linalg as LA
import sys
import config
import caffe
import logging
import tensorflow as tf
from AutoEncoder import AutoEncoder 

caffe_root = config.CNNInfo['caffe_root']
sys.path.insert(0, caffe_root + 'python')


class DeepDescriptor:

    def __init__(self, layer='pool1', Model='VGG', searchBool = 0, gpu = True):
    	self.layer = layer
        logging.info("instanteating the model")
        self.modeldict = config.LSFModelInfo['model_dict']


        if(config.AutoEncoderInfo['enable_autoencoder'] == 1 and searchBool):
            feature_dim_used = config.CNNInfo['feature_size']
            self.auto_encoder = AutoEncoder(
                config.AutoEncoderInfo['n_layers'], feature_dim_used)
            self.sess = tf.Session(config=self.auto_encoder.config)
            self.X = tf.placeholder("float", [None, feature_dim_used])
            # Construct model
            self.encoder_op = self.auto_encoder.encoder(self.X)
            init = tf.global_variables_initializer()
            self.saver = tf.train.Saver()
            ckpt = tf.train.get_checkpoint_state(self.modeldict)
            if ckpt and ckpt.model_checkpoint_path:
                self.saver.restore(self.sess, ckpt.model_checkpoint_path)
            else:
                logging,info("No model found")
        
        caffe.set_device(0)
        if gpu:
            caffe.set_mode_gpu()
        else:
            caffe.set_mode_cpu()
        if Model is 'VGG':
            model_def = caffe_root + 'models/vgg/VGG_ave_pool_deploy.prototxt'
            model_weights = caffe_root + 'models/vgg/vgg_normalised.caffemodel'
        elif Model is 'GoogleNet':
            model_def = caffe_root + 'models/bvlc_googlenet/deploy.prototxt'
            model_weights = caffe_root + 'models/bvlc_googlenet/bvlc_googlenet.caffemodel'

        self.net = caffe.Net(model_def,      # defines the structure of the model
                             model_weights,  # contains the trained weights
                             caffe.TEST)
        mu = np.load(caffe_root + 'python/caffe/imagenet/ilsvrc_2012_mean.npy')
        # average over pixels to obtain the mean (BGR) pixel values
        mu = mu.mean(1).mean(1)

        if Model is 'VGG':
            self.transformer = caffe.io.Transformer(
                {'data': self.net.blobs['data'].data.shape})
            self.transformer.set_transpose('data', (2, 0, 1))
            self.transformer.set_mean('data', mu)
            self.transformer.set_raw_scale('data', 255)
            self.transformer.set_channel_swap('data', (2, 1, 0))
            self.InterMediateLayer = layer
        elif Model is 'GoogleNet':

            self.transformer = caffe.io.Transformer(
                {'data': self.net.blobs['data'].data.shape})

            # move image channels to outermost dimension
            self.transformer.set_transpose('data', (2, 0, 1))
            # subtract the dataset-mean value in each channel
            self.transformer.set_mean('data', mu)
            # rescale from [0, 1] to [0, 255]
            self.transformer.set_raw_scale('data', 255)
            # swap channels from RGB to BGR
            self.transformer.set_channel_swap('data', (2, 1, 0))
            self.InterMediateLayer = 'inception_3a/output'
        else:
            loggging.info("Not supported")

    def describe(self, imagePath):
        if config.CNNInfo['keep_aspect_ratio']:
            self.preprocessImage(imagePath)
            image = caffe.io.load_image("tmp.jpg")
        else:
            image = caffe.io.load_image(imagePath)
        transformed_image = self.transformer.preprocess('data', image)
        self.net.blobs['data'].data[...] = transformed_image
        output = self.net.forward()
        feat = self.net.blobs[self.InterMediateLayer].data[0]
        shape = feat.shape
        F = np.reshape(feat, [shape[0], shape[1] * shape[2]])
        GramMatrix = np.dot(F, F.T)
        GramMatrix = GramMatrix / LA.norm(GramMatrix)
        GramMatrix = np.around(GramMatrix, decimals=4)
        return GramMatrix

    def search_describe(self, imgPath):
        GramMatrix = self.describe(imgPath);
        input_dim_used = config.CNNInfo['feature_size']
        feature = np.reshape(GramMatrix, (1, input_dim_used))
        batch = np.array(feature)
        if(config.AutoEncoderInfo['enable_autoencoder'] == 1):
            encoded_feature = self.sess.run(
                 self.encoder_op, feed_dict={self.X: batch})
            return encoded_feature
        else:
            return batch

    def preprocessImage(self, imagePath):
        img = cv2.imread(imagePath)
        h, w, _ = img.shape
        if h < w:
            img = skimage.transform.resize(
                img, (256, w * 256 / h), preserve_range=True)
        else:
            img = skimage.transform.resize(
                img, (h * 256 / w, 256), preserve_range=True)
        # Central crop to 224x224
        h, w, _ = img.shape
        img = img[h // 2 - 112:h // 2 + 112, w // 2 - 112:w // 2 + 112]
        cv2.imwrite("tmp.jpg", img)
                                                                                                                                                                                                                                                                                                                                                                                                                                                texture_similarity_tv/derby.log                                                                     0000664 0001750 0001750 00000051131 13053754601 017216  0                                                                                                    ustar   bhorkar                         bhorkar                                                                                                                                                                                                                Thu Feb 23 20:34:57 PST 2017 Thread[main,5,main] Ignored duplicate property derby.module.dataDictionary in jar:file:/home/bhorkar/Downloads/spark-1.6.2-bin-hadoop2.6/lib/spark-assembly-1.6.2-hadoop2.6.0.jar!/org/apache/derby/modules.properties
Thu Feb 23 20:34:57 PST 2017 Thread[main,5,main] Ignored duplicate property derby.module.lockManagerJ1 in jar:file:/home/bhorkar/Downloads/spark-1.6.2-bin-hadoop2.6/lib/spark-assembly-1.6.2-hadoop2.6.0.jar!/org/apache/derby/modules.properties
Thu Feb 23 20:34:57 PST 2017 Thread[main,5,main] Ignored duplicate property derby.env.classes.dvfJ2 in jar:file:/home/bhorkar/Downloads/spark-1.6.2-bin-hadoop2.6/lib/spark-assembly-1.6.2-hadoop2.6.0.jar!/org/apache/derby/modules.properties
Thu Feb 23 20:34:57 PST 2017 Thread[main,5,main] Ignored duplicate property derby.module.javaCompiler in jar:file:/home/bhorkar/Downloads/spark-1.6.2-bin-hadoop2.6/lib/spark-assembly-1.6.2-hadoop2.6.0.jar!/org/apache/derby/modules.properties
Thu Feb 23 20:34:57 PST 2017 Thread[main,5,main] Ignored duplicate property derby.module.replication.slave in jar:file:/home/bhorkar/Downloads/spark-1.6.2-bin-hadoop2.6/lib/spark-assembly-1.6.2-hadoop2.6.0.jar!/org/apache/derby/modules.properties
Thu Feb 23 20:34:57 PST 2017 Thread[main,5,main] Ignored duplicate property derby.env.jdk.rawStore.transactionJ6 in jar:file:/home/bhorkar/Downloads/spark-1.6.2-bin-hadoop2.6/lib/spark-assembly-1.6.2-hadoop2.6.0.jar!/org/apache/derby/modules.properties
Thu Feb 23 20:34:57 PST 2017 Thread[main,5,main] Ignored duplicate property derby.module.ef in jar:file:/home/bhorkar/Downloads/spark-1.6.2-bin-hadoop2.6/lib/spark-assembly-1.6.2-hadoop2.6.0.jar!/org/apache/derby/modules.properties
Thu Feb 23 20:34:57 PST 2017 Thread[main,5,main] Ignored duplicate property derby.env.jdk.rawStore.transactionJ1 in jar:file:/home/bhorkar/Downloads/spark-1.6.2-bin-hadoop2.6/lib/spark-assembly-1.6.2-hadoop2.6.0.jar!/org/apache/derby/modules.properties
Thu Feb 23 20:34:57 PST 2017 Thread[main,5,main] Ignored duplicate property derby.module.database in jar:file:/home/bhorkar/Downloads/spark-1.6.2-bin-hadoop2.6/lib/spark-assembly-1.6.2-hadoop2.6.0.jar!/org/apache/derby/modules.properties
Thu Feb 23 20:34:57 PST 2017 Thread[main,5,main] Ignored duplicate property derby.module.NoneAuthentication in jar:file:/home/bhorkar/Downloads/spark-1.6.2-bin-hadoop2.6/lib/spark-assembly-1.6.2-hadoop2.6.0.jar!/org/apache/derby/modules.properties
Thu Feb 23 20:34:57 PST 2017 Thread[main,5,main] Ignored duplicate property derby.module.netServer.autoStart in jar:file:/home/bhorkar/Downloads/spark-1.6.2-bin-hadoop2.6/lib/spark-assembly-1.6.2-hadoop2.6.0.jar!/org/apache/derby/modules.properties
Thu Feb 23 20:34:57 PST 2017 Thread[main,5,main] Ignored duplicate property derby.module.dvfJ2 in jar:file:/home/bhorkar/Downloads/spark-1.6.2-bin-hadoop2.6/lib/spark-assembly-1.6.2-hadoop2.6.0.jar!/org/apache/derby/modules.properties
Thu Feb 23 20:34:57 PST 2017 Thread[main,5,main] Ignored duplicate property derby.module.mgmt.null in jar:file:/home/bhorkar/Downloads/spark-1.6.2-bin-hadoop2.6/lib/spark-assembly-1.6.2-hadoop2.6.0.jar!/org/apache/derby/modules.properties
Thu Feb 23 20:34:57 PST 2017 Thread[main,5,main] Ignored duplicate property derby.module.nativeAuthentication in jar:file:/home/bhorkar/Downloads/spark-1.6.2-bin-hadoop2.6/lib/spark-assembly-1.6.2-hadoop2.6.0.jar!/org/apache/derby/modules.properties
Thu Feb 23 20:34:57 PST 2017 Thread[main,5,main] Ignored duplicate property derby.env.jdk.lockManagerJ6 in jar:file:/home/bhorkar/Downloads/spark-1.6.2-bin-hadoop2.6/lib/spark-assembly-1.6.2-hadoop2.6.0.jar!/org/apache/derby/modules.properties
Thu Feb 23 20:34:57 PST 2017 Thread[main,5,main] Ignored duplicate property derby.module.replication.master in jar:file:/home/bhorkar/Downloads/spark-1.6.2-bin-hadoop2.6/lib/spark-assembly-1.6.2-hadoop2.6.0.jar!/org/apache/derby/modules.properties
Thu Feb 23 20:34:57 PST 2017 Thread[main,5,main] Ignored duplicate property derby.module.dvfCDC in jar:file:/home/bhorkar/Downloads/spark-1.6.2-bin-hadoop2.6/lib/spark-assembly-1.6.2-hadoop2.6.0.jar!/org/apache/derby/modules.properties
Thu Feb 23 20:34:57 PST 2017 Thread[main,5,main] Ignored duplicate property derby.module.access.btree in jar:file:/home/bhorkar/Downloads/spark-1.6.2-bin-hadoop2.6/lib/spark-assembly-1.6.2-hadoop2.6.0.jar!/org/apache/derby/modules.properties
Thu Feb 23 20:34:57 PST 2017 Thread[main,5,main] Ignored duplicate property derby.env.jdk.lockManagerJ1 in jar:file:/home/bhorkar/Downloads/spark-1.6.2-bin-hadoop2.6/lib/spark-assembly-1.6.2-hadoop2.6.0.jar!/org/apache/derby/modules.properties
Thu Feb 23 20:34:57 PST 2017 Thread[main,5,main] Ignored duplicate property derby.module.uuidJ1 in jar:file:/home/bhorkar/Downloads/spark-1.6.2-bin-hadoop2.6/lib/spark-assembly-1.6.2-hadoop2.6.0.jar!/org/apache/derby/modules.properties
Thu Feb 23 20:34:57 PST 2017 Thread[main,5,main] Ignored duplicate property derby.module.cryptographyJ2 in jar:file:/home/bhorkar/Downloads/spark-1.6.2-bin-hadoop2.6/lib/spark-assembly-1.6.2-hadoop2.6.0.jar!/org/apache/derby/modules.properties
Thu Feb 23 20:34:57 PST 2017 Thread[main,5,main] Ignored duplicate property derby.env.jdk.rawStore.data.genericJ4 in jar:file:/home/bhorkar/Downloads/spark-1.6.2-bin-hadoop2.6/lib/spark-assembly-1.6.2-hadoop2.6.0.jar!/org/apache/derby/modules.properties
Thu Feb 23 20:34:57 PST 2017 Thread[main,5,main] Ignored duplicate property derby.env.jdk.rawStore.data.genericJ1 in jar:file:/home/bhorkar/Downloads/spark-1.6.2-bin-hadoop2.6/lib/spark-assembly-1.6.2-hadoop2.6.0.jar!/org/apache/derby/modules.properties
Thu Feb 23 20:34:57 PST 2017 Thread[main,5,main] Ignored duplicate property derby.module.access in jar:file:/home/bhorkar/Downloads/spark-1.6.2-bin-hadoop2.6/lib/spark-assembly-1.6.2-hadoop2.6.0.jar!/org/apache/derby/modules.properties
Thu Feb 23 20:34:57 PST 2017 Thread[main,5,main] Ignored duplicate property derby.module.jdbc169 in jar:file:/home/bhorkar/Downloads/spark-1.6.2-bin-hadoop2.6/lib/spark-assembly-1.6.2-hadoop2.6.0.jar!/org/apache/derby/modules.properties
Thu Feb 23 20:34:57 PST 2017 Thread[main,5,main] Ignored duplicate property derby.env.jdk.cryptographyJ2 in jar:file:/home/bhorkar/Downloads/spark-1.6.2-bin-hadoop2.6/lib/spark-assembly-1.6.2-hadoop2.6.0.jar!/org/apache/derby/modules.properties
Thu Feb 23 20:34:57 PST 2017 Thread[main,5,main] Ignored duplicate property derby.module.optimizer in jar:file:/home/bhorkar/Downloads/spark-1.6.2-bin-hadoop2.6/lib/spark-assembly-1.6.2-hadoop2.6.0.jar!/org/apache/derby/modules.properties
Thu Feb 23 20:34:57 PST 2017 Thread[main,5,main] Ignored duplicate property derby.env.jdk.mgmt.jmx in jar:file:/home/bhorkar/Downloads/spark-1.6.2-bin-hadoop2.6/lib/spark-assembly-1.6.2-hadoop2.6.0.jar!/org/apache/derby/modules.properties
Thu Feb 23 20:34:57 PST 2017 Thread[main,5,main] Ignored duplicate property derby.env.jdk.dvfJ2 in jar:file:/home/bhorkar/Downloads/spark-1.6.2-bin-hadoop2.6/lib/spark-assembly-1.6.2-hadoop2.6.0.jar!/org/apache/derby/modules.properties
Thu Feb 23 20:34:57 PST 2017 Thread[main,5,main] Ignored duplicate property derby.module.specificAuthentication in jar:file:/home/bhorkar/Downloads/spark-1.6.2-bin-hadoop2.6/lib/spark-assembly-1.6.2-hadoop2.6.0.jar!/org/apache/derby/modules.properties
Thu Feb 23 20:34:57 PST 2017 Thread[main,5,main] Ignored duplicate property derby.module.JNDIAuthentication in jar:file:/home/bhorkar/Downloads/spark-1.6.2-bin-hadoop2.6/lib/spark-assembly-1.6.2-hadoop2.6.0.jar!/org/apache/derby/modules.properties
Thu Feb 23 20:34:57 PST 2017 Thread[main,5,main] Ignored duplicate property derby.module.basicAuthentication in jar:file:/home/bhorkar/Downloads/spark-1.6.2-bin-hadoop2.6/lib/spark-assembly-1.6.2-hadoop2.6.0.jar!/org/apache/derby/modules.properties
Thu Feb 23 20:34:57 PST 2017 Thread[main,5,main] Ignored duplicate property derby.module.rawStore.data.genericJ4 in jar:file:/home/bhorkar/Downloads/spark-1.6.2-bin-hadoop2.6/lib/spark-assembly-1.6.2-hadoop2.6.0.jar!/org/apache/derby/modules.properties
Thu Feb 23 20:34:57 PST 2017 Thread[main,5,main] Ignored duplicate property derby.module.validation in jar:file:/home/bhorkar/Downloads/spark-1.6.2-bin-hadoop2.6/lib/spark-assembly-1.6.2-hadoop2.6.0.jar!/org/apache/derby/modules.properties
Thu Feb 23 20:34:57 PST 2017 Thread[main,5,main] Ignored duplicate property derby.module.rawStore.data.genericJ1 in jar:file:/home/bhorkar/Downloads/spark-1.6.2-bin-hadoop2.6/lib/spark-assembly-1.6.2-hadoop2.6.0.jar!/org/apache/derby/modules.properties
Thu Feb 23 20:34:57 PST 2017 Thread[main,5,main] Ignored duplicate property derby.module.classManagerJ6 in jar:file:/home/bhorkar/Downloads/spark-1.6.2-bin-hadoop2.6/lib/spark-assembly-1.6.2-hadoop2.6.0.jar!/org/apache/derby/modules.properties
Thu Feb 23 20:34:57 PST 2017 Thread[main,5,main] Ignored duplicate property derby.module.streams in jar:file:/home/bhorkar/Downloads/spark-1.6.2-bin-hadoop2.6/lib/spark-assembly-1.6.2-hadoop2.6.0.jar!/org/apache/derby/modules.properties
Thu Feb 23 20:34:57 PST 2017 Thread[main,5,main] Ignored duplicate property derby.module.classManagerJ2 in jar:file:/home/bhorkar/Downloads/spark-1.6.2-bin-hadoop2.6/lib/spark-assembly-1.6.2-hadoop2.6.0.jar!/org/apache/derby/modules.properties
Thu Feb 23 20:34:57 PST 2017 Thread[main,5,main] Ignored duplicate property derby.env.classes.resourceAdapterJ2 in jar:file:/home/bhorkar/Downloads/spark-1.6.2-bin-hadoop2.6/lib/spark-assembly-1.6.2-hadoop2.6.0.jar!/org/apache/derby/modules.properties
Thu Feb 23 20:34:57 PST 2017 Thread[main,5,main] Ignored duplicate property derby.env.classes.rawStore.transactionJ6 in jar:file:/home/bhorkar/Downloads/spark-1.6.2-bin-hadoop2.6/lib/spark-assembly-1.6.2-hadoop2.6.0.jar!/org/apache/derby/modules.properties
Thu Feb 23 20:34:57 PST 2017 Thread[main,5,main] Ignored duplicate property derby.module.jdbcJ8 in jar:file:/home/bhorkar/Downloads/spark-1.6.2-bin-hadoop2.6/lib/spark-assembly-1.6.2-hadoop2.6.0.jar!/org/apache/derby/modules.properties
Thu Feb 23 20:34:57 PST 2017 Thread[main,5,main] Ignored duplicate property derby.module.jdbcJ6 in jar:file:/home/bhorkar/Downloads/spark-1.6.2-bin-hadoop2.6/lib/spark-assembly-1.6.2-hadoop2.6.0.jar!/org/apache/derby/modules.properties
Thu Feb 23 20:34:57 PST 2017 Thread[main,5,main] Ignored duplicate property derby.env.jdk.classManagerJ6 in jar:file:/home/bhorkar/Downloads/spark-1.6.2-bin-hadoop2.6/lib/spark-assembly-1.6.2-hadoop2.6.0.jar!/org/apache/derby/modules.properties
Thu Feb 23 20:34:57 PST 2017 Thread[main,5,main] Ignored duplicate property derby.module.jdbcJ4 in jar:file:/home/bhorkar/Downloads/spark-1.6.2-bin-hadoop2.6/lib/spark-assembly-1.6.2-hadoop2.6.0.jar!/org/apache/derby/modules.properties
Thu Feb 23 20:34:57 PST 2017 Thread[main,5,main] Ignored duplicate property derby.module.rawStore.log in jar:file:/home/bhorkar/Downloads/spark-1.6.2-bin-hadoop2.6/lib/spark-assembly-1.6.2-hadoop2.6.0.jar!/org/apache/derby/modules.properties
Thu Feb 23 20:34:57 PST 2017 Thread[main,5,main] Ignored duplicate property derby.module.rawStore.log.readonly in jar:file:/home/bhorkar/Downloads/spark-1.6.2-bin-hadoop2.6/lib/spark-assembly-1.6.2-hadoop2.6.0.jar!/org/apache/derby/modules.properties
Thu Feb 23 20:34:57 PST 2017 Thread[main,5,main] Ignored duplicate property derby.module.access.heap in jar:file:/home/bhorkar/Downloads/spark-1.6.2-bin-hadoop2.6/lib/spark-assembly-1.6.2-hadoop2.6.0.jar!/org/apache/derby/modules.properties
Thu Feb 23 20:34:57 PST 2017 Thread[main,5,main] Ignored duplicate property derby.env.classes.jdbcJ8 in jar:file:/home/bhorkar/Downloads/spark-1.6.2-bin-hadoop2.6/lib/spark-assembly-1.6.2-hadoop2.6.0.jar!/org/apache/derby/modules.properties
Thu Feb 23 20:34:57 PST 2017 Thread[main,5,main] Ignored duplicate property derby.module.daemon in jar:file:/home/bhorkar/Downloads/spark-1.6.2-bin-hadoop2.6/lib/spark-assembly-1.6.2-hadoop2.6.0.jar!/org/apache/derby/modules.properties
Thu Feb 23 20:34:57 PST 2017 Thread[main,5,main] Ignored duplicate property derby.env.jdk.cacheManagerJ6 in jar:file:/home/bhorkar/Downloads/spark-1.6.2-bin-hadoop2.6/lib/spark-assembly-1.6.2-hadoop2.6.0.jar!/org/apache/derby/modules.properties
Thu Feb 23 20:34:57 PST 2017 Thread[main,5,main] Ignored duplicate property derby.module.tcf in jar:file:/home/bhorkar/Downloads/spark-1.6.2-bin-hadoop2.6/lib/spark-assembly-1.6.2-hadoop2.6.0.jar!/org/apache/derby/modules.properties
Thu Feb 23 20:34:57 PST 2017 Thread[main,5,main] Ignored duplicate property derby.env.classes.jdbcJ6 in jar:file:/home/bhorkar/Downloads/spark-1.6.2-bin-hadoop2.6/lib/spark-assembly-1.6.2-hadoop2.6.0.jar!/org/apache/derby/modules.properties
Thu Feb 23 20:34:57 PST 2017 Thread[main,5,main] Ignored duplicate property derby.env.classes.jdbcJ4 in jar:file:/home/bhorkar/Downloads/spark-1.6.2-bin-hadoop2.6/lib/spark-assembly-1.6.2-hadoop2.6.0.jar!/org/apache/derby/modules.properties
Thu Feb 23 20:34:57 PST 2017 Thread[main,5,main] Ignored duplicate property derby.module.access.uniquewithduplicatenullssort in jar:file:/home/bhorkar/Downloads/spark-1.6.2-bin-hadoop2.6/lib/spark-assembly-1.6.2-hadoop2.6.0.jar!/org/apache/derby/modules.properties
Thu Feb 23 20:34:57 PST 2017 Thread[main,5,main] Ignored duplicate property derby.env.jdk.cacheManagerJ1 in jar:file:/home/bhorkar/Downloads/spark-1.6.2-bin-hadoop2.6/lib/spark-assembly-1.6.2-hadoop2.6.0.jar!/org/apache/derby/modules.properties
Thu Feb 23 20:34:57 PST 2017 Thread[main,5,main] Ignored duplicate property derby.module.cacheManagerJ6 in jar:file:/home/bhorkar/Downloads/spark-1.6.2-bin-hadoop2.6/lib/spark-assembly-1.6.2-hadoop2.6.0.jar!/org/apache/derby/modules.properties
Thu Feb 23 20:34:57 PST 2017 Thread[main,5,main] Ignored duplicate property derby.module.resultSetStatisticsFactory in jar:file:/home/bhorkar/Downloads/spark-1.6.2-bin-hadoop2.6/lib/spark-assembly-1.6.2-hadoop2.6.0.jar!/org/apache/derby/modules.properties
Thu Feb 23 20:34:57 PST 2017 Thread[main,5,main] Ignored duplicate property derby.module.cacheManagerJ1 in jar:file:/home/bhorkar/Downloads/spark-1.6.2-bin-hadoop2.6/lib/spark-assembly-1.6.2-hadoop2.6.0.jar!/org/apache/derby/modules.properties
Thu Feb 23 20:34:57 PST 2017 Thread[main,5,main] Ignored duplicate property derby.env.classes.cryptographyJ2 in jar:file:/home/bhorkar/Downloads/spark-1.6.2-bin-hadoop2.6/lib/spark-assembly-1.6.2-hadoop2.6.0.jar!/org/apache/derby/modules.properties
Thu Feb 23 20:34:57 PST 2017 Thread[main,5,main] Ignored duplicate property derby.env.classes.rawStore.data.genericJ4 in jar:file:/home/bhorkar/Downloads/spark-1.6.2-bin-hadoop2.6/lib/spark-assembly-1.6.2-hadoop2.6.0.jar!/org/apache/derby/modules.properties
Thu Feb 23 20:34:57 PST 2017 Thread[main,5,main] Ignored duplicate property derby.module.database.slave in jar:file:/home/bhorkar/Downloads/spark-1.6.2-bin-hadoop2.6/lib/spark-assembly-1.6.2-hadoop2.6.0.jar!/org/apache/derby/modules.properties
Thu Feb 23 20:34:57 PST 2017 Thread[main,5,main] Ignored duplicate property derby.module.XPLAINFactory in jar:file:/home/bhorkar/Downloads/spark-1.6.2-bin-hadoop2.6/lib/spark-assembly-1.6.2-hadoop2.6.0.jar!/org/apache/derby/modules.properties
Thu Feb 23 20:34:57 PST 2017 Thread[main,5,main] Ignored duplicate property derby.module.resourceAdapterJ2 in jar:file:/home/bhorkar/Downloads/spark-1.6.2-bin-hadoop2.6/lib/spark-assembly-1.6.2-hadoop2.6.0.jar!/org/apache/derby/modules.properties
Thu Feb 23 20:34:57 PST 2017 Thread[main,5,main] Ignored duplicate property derby.module.access.sort in jar:file:/home/bhorkar/Downloads/spark-1.6.2-bin-hadoop2.6/lib/spark-assembly-1.6.2-hadoop2.6.0.jar!/org/apache/derby/modules.properties
Thu Feb 23 20:34:57 PST 2017 Thread[main,5,main] Ignored duplicate property derby.module.mgmt.jmx in jar:file:/home/bhorkar/Downloads/spark-1.6.2-bin-hadoop2.6/lib/spark-assembly-1.6.2-hadoop2.6.0.jar!/org/apache/derby/modules.properties
Thu Feb 23 20:34:57 PST 2017 Thread[main,5,main] Ignored duplicate property derby.module.rawStore.transactionJ6 in jar:file:/home/bhorkar/Downloads/spark-1.6.2-bin-hadoop2.6/lib/spark-assembly-1.6.2-hadoop2.6.0.jar!/org/apache/derby/modules.properties
Thu Feb 23 20:34:57 PST 2017 Thread[main,5,main] Ignored duplicate property derby.env.classes.JNDIAuthentication in jar:file:/home/bhorkar/Downloads/spark-1.6.2-bin-hadoop2.6/lib/spark-assembly-1.6.2-hadoop2.6.0.jar!/org/apache/derby/modules.properties
Thu Feb 23 20:34:57 PST 2017 Thread[main,5,main] Ignored duplicate property derby.module.rawStore.transactionJ1 in jar:file:/home/bhorkar/Downloads/spark-1.6.2-bin-hadoop2.6/lib/spark-assembly-1.6.2-hadoop2.6.0.jar!/org/apache/derby/modules.properties
Thu Feb 23 20:34:57 PST 2017 Thread[main,5,main] Ignored duplicate property derby.module.timer in jar:file:/home/bhorkar/Downloads/spark-1.6.2-bin-hadoop2.6/lib/spark-assembly-1.6.2-hadoop2.6.0.jar!/org/apache/derby/modules.properties
Thu Feb 23 20:34:57 PST 2017 Thread[main,5,main] Ignored duplicate property derby.module.lcf in jar:file:/home/bhorkar/Downloads/spark-1.6.2-bin-hadoop2.6/lib/spark-assembly-1.6.2-hadoop2.6.0.jar!/org/apache/derby/modules.properties
Thu Feb 23 20:34:57 PST 2017 Thread[main,5,main] Ignored duplicate property derby.module.rawStore in jar:file:/home/bhorkar/Downloads/spark-1.6.2-bin-hadoop2.6/lib/spark-assembly-1.6.2-hadoop2.6.0.jar!/org/apache/derby/modules.properties
Thu Feb 23 20:34:57 PST 2017 Thread[main,5,main] Ignored duplicate property derby.env.jdk.resourceAdapterJ2 in jar:file:/home/bhorkar/Downloads/spark-1.6.2-bin-hadoop2.6/lib/spark-assembly-1.6.2-hadoop2.6.0.jar!/org/apache/derby/modules.properties
Thu Feb 23 20:34:57 PST 2017 Thread[main,5,main] Ignored duplicate property derby.env.classes.jdbc169 in jar:file:/home/bhorkar/Downloads/spark-1.6.2-bin-hadoop2.6/lib/spark-assembly-1.6.2-hadoop2.6.0.jar!/org/apache/derby/modules.properties
Thu Feb 23 20:34:57 PST 2017 Thread[main,5,main] Ignored duplicate property derby.module.lf in jar:file:/home/bhorkar/Downloads/spark-1.6.2-bin-hadoop2.6/lib/spark-assembly-1.6.2-hadoop2.6.0.jar!/org/apache/derby/modules.properties
Thu Feb 23 20:34:57 PST 2017 Thread[main,5,main] Ignored duplicate property derby.env.jdk.jdbcJ8 in jar:file:/home/bhorkar/Downloads/spark-1.6.2-bin-hadoop2.6/lib/spark-assembly-1.6.2-hadoop2.6.0.jar!/org/apache/derby/modules.properties
Thu Feb 23 20:34:57 PST 2017 Thread[main,5,main] Ignored duplicate property derby.env.jdk.jdbcJ6 in jar:file:/home/bhorkar/Downloads/spark-1.6.2-bin-hadoop2.6/lib/spark-assembly-1.6.2-hadoop2.6.0.jar!/org/apache/derby/modules.properties
Thu Feb 23 20:34:57 PST 2017 Thread[main,5,main] Ignored duplicate property derby.env.jdk.jdbcJ4 in jar:file:/home/bhorkar/Downloads/spark-1.6.2-bin-hadoop2.6/lib/spark-assembly-1.6.2-hadoop2.6.0.jar!/org/apache/derby/modules.properties
Thu Feb 23 20:34:57 PST 2017 Thread[main,5,main] Ignored duplicate property derby.module.nodeFactory in jar:file:/home/bhorkar/Downloads/spark-1.6.2-bin-hadoop2.6/lib/spark-assembly-1.6.2-hadoop2.6.0.jar!/org/apache/derby/modules.properties
Thu Feb 23 20:34:57 PST 2017 Thread[main,5,main] Ignored duplicate property derby.module.lockManagerJ6 in jar:file:/home/bhorkar/Downloads/spark-1.6.2-bin-hadoop2.6/lib/spark-assembly-1.6.2-hadoop2.6.0.jar!/org/apache/derby/modules.properties
Thu Feb 23 20:34:57 PST 2017 Thread[main,5,main]                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          
----------------------------------------------------------------
Thu Feb 23 20:34:57 PST 2017:
Booting Derby version The Apache Software Foundation - Apache Derby - 10.10.1.1 - (1458268): instance a816c00e-015a-6e66-85c5-00002e47e430 
on database directory /home/bhorkar/fashion_cloths/deep_describe/texture_similarity/metastore_db with class loader org.apache.spark.sql.hive.client.IsolatedClientLoader$$anon$1@33cec966 
Loaded from file:/home/bhorkar/spark/lib/spark-assembly-1.6.2-hadoop2.6.0.jar
java.vendor=Oracle Corporation
java.runtime.version=1.8.0_111-b14
user.dir=/home/bhorkar/fashion_cloths/deep_describe/texture_similarity
os.name=Linux
os.arch=amd64
os.version=4.4.0-57-generic
derby.system.home=null
Database Class Loader started - derby.database.classpath=''
                                                                                                                                                                                                                                                                                                                                                                                                                                       texture_similarity_tv/exifutil.py                                                                   0000664 0001750 0001750 00000002026 13053754601 017610  0                                                                                                    ustar   bhorkar                         bhorkar                                                                                                                                                                                                                """
This script handles the skimage exif problem.
"""

from PIL import Image
import numpy as np

ORIENTATIONS = {   # used in apply_orientation
    2: (Image.FLIP_LEFT_RIGHT,),
    3: (Image.ROTATE_180,),
    4: (Image.FLIP_TOP_BOTTOM,),
    5: (Image.FLIP_LEFT_RIGHT, Image.ROTATE_90),
    6: (Image.ROTATE_270,),
    7: (Image.FLIP_LEFT_RIGHT, Image.ROTATE_270),
    8: (Image.ROTATE_90,)
}


def open_oriented_im(im_path):
    im = Image.open(im_path)
    if hasattr(im, '_getexif'):
        exif = im._getexif()
        if exif is not None and 274 in exif:
            orientation = exif[274]
            im = apply_orientation(im, orientation)
    img = np.asarray(im).astype(np.float32) / 255.
    if img.ndim == 2:
        img = img[:, :, np.newaxis]
        img = np.tile(img, (1, 1, 3))
    elif img.shape[2] == 4:
        img = img[:, :, :3]
    return img


def apply_orientation(im, orientation):
    if orientation in ORIENTATIONS:
        for method in ORIENTATIONS[orientation]:
            im = im.transpose(method)
    return im
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          texture_similarity_tv/GenerateLSFTree.py                                                            0000664 0001750 0001750 00000016740 13053754601 020706  0                                                                                                    ustar   bhorkar                         bhorkar                                                                                                                                                                                                                from __future__ import print_function
import numpy as np
import tensorflow as tf
import math as math
import glob
import cv2
from DeepDescriptor import DeepDescriptor
import optparse
import os
import matplotlib.pyplot as plt
import skimage.transform
import config
import logging
from sklearn.neighbors import LSHForest
import pickle
from AutoEncoder import AutoEncoder


class CnnActivation(object):

    def file_len(self, Filelist_glob):
        flen = 0
        for imagePath in Filelist_glob:
            flen = flen + 1
        return flen

    def __init__(self, descriptor, model_dict,
                 feature_dim_used, trainImageDict, indexFile):
        self.train_path = trainImageDict
        self.model_dict = model_dict
        self.cd = descriptor
        self.indexFile = indexFile
        self.feature_dim_used = feature_dim_used
        self.flen = self.file_len(glob.iglob(self.train_path + "/*.jpg"))
        self.Filelist = glob.iglob(self.train_path + "/*.jpg")

    def readfileFromdict(self, Filelist, batch_size=1):
        n = 0
        read_features = np.array([], dtype=np.float).reshape(
            0, self.feature_dim_used)
        imageset = []
        for imagePath in Filelist:
            # path and load the image itself
            imageID = imagePath[imagePath.rfind("/") + 1:]
            imageset.append(imageID)
            features = self.cd.describe(imagePath)
            features = np.asarray(features.ravel()).reshape(1, -1)[0][:]
            features = features[:self.feature_dim_used]
            read_features = np.vstack((read_features, features))
            if(n == batch_size - 1):
                break
            n = n + 1
        return read_features, imageset

    def EncodeTextureLSFTree(self, ntrees, autoencoderEnable):
     # Restore variables from disk.
        if autoencoderEnable == True:
            saver = tf.train.Saver()
            init = tf.global_variables_initializer()
            sess = tf.Session()
            ckpt = tf.train.get_checkpoint_state(self.model_dict)
            if ckpt and ckpt.model_checkpoint_path:
                saver.restore(sess, ckpt.model_checkpoint_path)
            else:
                logging.info("No model found")
                return
            logging.info("Tensorflow Model restored.")
        # store data in number of batches
        nSamplesPerTree = int(math.floor(self.flen / ntrees))
        for nt in xrange(ntrees):
            image_idx = open(self.indexFile + str(nt), "w")
            logging.info("Inside " + str(nt) + " tree")
            if autoencoderEnable == True:
                if self.auto_encoder.n_layer == 1:
                    X_train = np.array([], dtype=np.float).reshape(
                        0, self.auto_encoder.n_hidden_1)
                elif self.auto_encoder.n_layer == 2:
                    X_train = np.array([], dtype=np.float).reshape(
                        0, self.auto_encoder.n_hidden_2)
            else:
                X_train = np.array([], dtype=np.float).reshape(
                    0, self.feature_dim_used)
            for i in xrange(nSamplesPerTree):
                batch = []
                if i % 1000 == 1:
                    logging.info("Processed:" + str(i))
                batch, imagename = self.readfileFromdict(self.Filelist)
                image_idx.write("%s \n" % imagename)
                batch = np.array(batch)
                if autoencoderEnable == True:
                    image_idx.write("%s \n" % imagename)
                    batch = np.array(batch)
                    encode = sess.run(self.auto_encoder.encoder_op, feed_dict={
                                      self.auto_encoder.X: batch})
                    X_train = np.vstack((X_train, encode))
                else:
                    X_train = np.vstack((X_train, batch))
            logging.info(X_train.shape)
            image_idx.close()
            logging.info(str(X_train.shape))
            lshf = LSHForest(config.LSFModelInfo[
                             'n_candidates'], config.LSFModelInfo['n_estimators'])
            lshf.fit(X_train)
            pickle.dump(lshf, open(self.model_dict +
                                   "LSFModelsave.p" + str(nt), "wb"))

    def runAutoEncoder(self, auto_encoder):
        self.auto_encoder = auto_encoder
        logging.info("Running the ecoder")
        init = tf.global_variables_initializer()
        saver2 = tf.train.Saver()
        AutoEncoderFilelist = glob.iglob(self.train_path + "/*.jpg")
# Launch the graph
        with tf.Session(config=auto_encoder.config) as sess:
            sess.run(init)
            total_batch = int(self.flen / auto_encoder.batch_size)

            for epoch in range(total_batch):
                batch_xs, image = self.readfileFromdict(
                    AutoEncoderFilelist, auto_encoder.batch_size)
                # Run optimization op (backprop) and cost op (to get loss
                # value)
                _, c = sess.run([auto_encoder.optimizer, auto_encoder.cost],
                                feed_dict={auto_encoder.X: np.array(batch_xs)})
            # Display logs per epoch step
                if epoch % auto_encoder.display_step == 0:
                    print("Epoch:", '%04d' %
                          (epoch + 1), "cost=", "{:.9f}".format(c))
                    save_path = saver2.save(
                        sess, self.model_dict + "model1.ckpt", global_step=epoch)

            logging.info("Optimization Finished!")
            logging.info("Model2 saved in file: %s" % save_path)


class TextureEncode(object):
    default_args = {
        # update with model directories
    }

    def __init__(self, gpu_mode):
        indexFile = config.LSFModelInfo[
            'model_dict'] + config.LSFModelInfo['indexFile']
        ntrees = config.LSFModelInfo['nLSFModelTrees']
        feature_dim_used = config.CNNInfo['feature_size']
        model_dict = config.LSFModelInfo['model_dict']
        net = config.CNNInfo['net']
        layer = config.CNNInfo['layer']
        train_path = config.CNNInfo['input_dict']
        if not os.path.exists(model_dict):
            os.makedirs(model_dict)
        logging.info('Loading net and associated files...')
        if config.AutoEncoderInfo['enable_autoencoder']:
            # hack. tensorflow may not work caffee otherwise. initilize tensor
            # before caffe
            gpu_options = tf.GPUOptions(per_process_gpu_memory_fraction=0.8)
            sess = tf.Session(config=tf.ConfigProto(gpu_options=gpu_options))
        self.cnn_activation = CnnActivation(DeepDescriptor(layer, net, gpu = gpu_mode),
                                            model_dict, feature_dim_used, train_path, indexFile)
        if config.AutoEncoderInfo['enable_autoencoder']:
            self.autoencoder = AutoEncoder(
                config.AutoEncoderInfo['n_layers'], feature_dim_used)
            self.cnn_activation.runAutoEncoder(self.autoencoder)
        self.cnn_activation.EncodeTextureLSFTree(
            ntrees, config.AutoEncoderInfo['enable_autoencoder'])
        # load the result image and display

if __name__ == '__main__':
    logging.getLogger().setLevel(logging.INFO)
    """
    Parse command line options and start the server.
    """
    parser = optparse.OptionParser()
    parser.add_option(
        '-g', '--gpu',
        help="use gpu mode",
        action='store_true', default=True)

    opts, args = parser.parse_args()
    TextureEncode.default_args.update({'gpu_mode': opts.gpu})
    ted = TextureEncode(**TextureEncode.default_args)
    logging.info("Finished Feature extraction")
                                texture_similarity_tv/__init__.py                                                                   0000664 0001750 0001750 00000000000 13053754601 017504  0                                                                                                    ustar   bhorkar                         bhorkar                                                                                                                                                                                                                texture_similarity_tv/requirements.txt                                                              0000664 0001750 0001750 00000000227 13053754601 020672  0                                                                                                    ustar   bhorkar                         bhorkar                                                                                                                                                                                                                cv2
sklearn
numpy
tensorflow
import math as math
glob
cv2
optparse
matplotlib
skimage
logging
pickle
werkzeug
flask
tornado
numpy
pandas
pillow
pyyaml
                                                                                                                                                                                                                                                                                                                                                                         texture_similarity_tv/searcher_lsf.py                                                               0000664 0001750 0001750 00000002762 13053754601 020426  0                                                                                                    ustar   bhorkar                         bhorkar                                                                                                                                                                                                                import pickle
import linecache
import config


class Searcher:

    def __init__(self, model):
        # store our index path
        self.model = model
        self.lsf = {}
        self.nchunks = config.LSFModelInfo['nLSFModelTrees']
        for nt in xrange(0, self.nchunks):
            print("loading nt" + str(nt))
            self.lsf[nt] = (pickle.load(
                open(self.model + "/LSFModelsave.p" + str(nt), "rb")))
      # self.kdtree = pickle.load( open( model+"/LSFModelsavekd.p", "rb"
      # ) );

    def search(self, queryFeatures, limit=10):
        resultsf = {}
        for nt in xrange(0, self.nchunks):

            dist, results = self.lsf[nt].kneighbors(
                queryFeatures, n_neighbors=10)
        #    dist,results = self.kdtree.query(queryFeatures, k=10);
            results = results[0]
            for i in xrange(len(results)):
                fileName = linecache.getline(
                    self.model + config.LSFModelInfo['indexFile'] + str(nt), results[i] + 1)
                fileName = fileName.replace('[', '')
                fileName = fileName.replace(']', '')
                fileName = fileName.replace('\'', '')
                if(fileName == ''):
                    print results[i]
                    continue
                resultsf[fileName] = dist[0][i]
               # open the index file for reading
                # return our (limited) results

        resultsf = sorted([(v, k) for (k, v) in resultsf.items()])
        return resultsf[:limit]
              texture_similarity_tv/templates/                                                                    0000775 0001750 0001750 00000000000 13053754602 017404  5                                                                                                    ustar   bhorkar                         bhorkar                                                                                                                                                                                                                texture_similarity_tv/templates/index.html                                                          0000664 0001750 0001750 00000007544 13053754602 021413  0                                                                                                    ustar   bhorkar                         bhorkar                                                                                                                                                                                                                <!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="Demo">
    <meta name="author" content="Abhijeet Bhorkar">

    <title>Caffe Demos</title>

    <link href="//netdna.bootstrapcdn.com/bootstrap/3.1.1/css/bootstrap.min.css" rel="stylesheet">

    <script type="text/javascript" src="//code.jquery.com/jquery-2.1.1.js"></script>
    <script src="//netdna.bootstrapcdn.com/bootstrap/3.1.1/js/bootstrap.min.js"></script>

    <!-- Script to instantly classify an image once it is uploaded. -->
    <script type="text/javascript">
      $(document).ready(
        function(){
          $('#classifyfile').attr('disabled',true);
          $('#imagefile').change(
            function(){
              if ($(this).val()){
                $('#formupload').submit();
              }
            }
          );
        }
      );
    </script>

    <style>
    body {
      font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
      line-height:1.5em;
      color: #232323;
      -webkit-font-smoothing: antialiased;
    }

    h1, h2, h3 {
      font-family: Times, serif;
      line-height:1.5em;
      border-bottom: 1px solid #ccc;
    }
    </style>
  </head>

  <body>
    <!-- Begin page content -->
    <div class="container">
      <div class="page-header">
        <h1><a href="/"> Demos</a></h1>
      </div>

      <div>
        <h2>Texture Matching</h2>
      </div>

      {% if has_result %}
      {% if not result[0] %}
      <!-- we have error in the result. -->
      <div class="alert alert-danger">{{ result[0] }} Did you provide a valid URL or a valid image file? </div>
      {% else %}
      <div class="media">
        <a class="pull-left" href="#"><img class="media-object" width="192" height="192" src={{ imagesrc }}></a>
        <div class="media-body">
          <div class="bs-example bs-example-tabs">
            <ul id="myTab" class="nav nav-tabs">
              <li class="active"><a href="#infopred" data-toggle="tab">Similar Textured Clothings</a></li>
            </ul>
            <div id="myTabContent" class="tab-content">
              <div class="tab-pane fade in active" id="infopred">
                <ul class="list-group">
                  {% for single_pred in result[1] %}
                  <li class="list-group-item">
                  <span class="badge">{{ single_pred }}</span>
                  <h4 class="list-group-item-heading">
		    <img src="{{ url_for('static', filename = single_pred) }}" width="85" height="85">
                  </h4>
                  </li>
                  {% endfor %}
                </ul>
              </div>
            </div>
          </div>

        </div>
      </div>
      <p> CNN took {{ result[2] }} seconds. </p>
      {% endif %}
      <hr>
      {% endif %}

      <form role="form" action="classify_url" method="get">
        <div class="form-group">
          <div class="input-group">
            <input type="text" class="form-control" name="imageurl" id="imageurl" placeholder="Provide an image URL">
            <span class="input-group-btn">
              <input class="btn btn-primary" value="Classify URL" type="submit" id="classifyurl"></input>
            </span>
          </div><!-- /input-group -->
        </div>
      </form>

      <form id="formupload" class="form-inline" role="form" action="classify_upload" method="post" enctype="multipart/form-data">
        <div class="form-group">
          <label for="imagefile">Or upload an image:</label>
          <input type="file" name="imagefile" id="imagefile">
        </div>
        <!--<input type="submit" class="btn btn-primary" value="Classify File" id="classifyfile"></input>-->
      </form>
    </div>

    <hr>
    <div id="footer">
      <div class="container">
        <p>&copy; deep.ai</p>
      </div>
   </div>
 </body>
</html>
                                                                                                                                                            texture_similarity_tv/web_demo/                                                                     0000775 0001750 0001750 00000000000 13053754601 017166  5                                                                                                    ustar   bhorkar                         bhorkar                                                                                                                                                                                                                texture_similarity_tv/web_demo/requirements.txt                                                     0000664 0001750 0001750 00000000062 13053754601 022450  0                                                                                                    ustar   bhorkar                         bhorkar                                                                                                                                                                                                                werkzeug
flask
tornado
numpy
pandas
pillow
pyyaml
                                                                                                                                                                                                                                                                                                                                                                                                                                                                              texture_similarity_tv/web_demo/app.py                                                               0000664 0001750 0001750 00000016240 13053754601 020323  0                                                                                                    ustar   bhorkar                         bhorkar                                                                                                                                                                                                                import os
import time
import cPickle
import datetime
import logging
import flask
import werkzeug
import optparse
import tornado.wsgi
import tornado.httpserver
import numpy as np
import pandas as pd
from PIL import Image
import cStringIO as StringIO
import urllib
import exifutil

import caffe

REPO_DIRNAME = os.path.abspath(os.path.dirname(os.path.abspath(__file__)) + '/../..')
UPLOAD_FOLDER = '/tmp/caffe_demos_uploads'
ALLOWED_IMAGE_EXTENSIONS = set(['png', 'bmp', 'jpg', 'jpe', 'jpeg', 'gif'])

# Obtain the flask app object
app = flask.Flask(__name__)


@app.route('/')
def index():
    return flask.render_template('index.html', has_result=False)


@app.route('/classify_url', methods=['GET'])
def classify_url():
    imageurl = flask.request.args.get('imageurl', '')
    try:
        string_buffer = StringIO.StringIO(
            urllib.urlopen(imageurl).read())
        image = caffe.io.load_image(string_buffer)

    except Exception as err:
        # For any exception we encounter in reading the image, we will just
        # not continue.
        logging.info('URL Image open error: %s', err)
        return flask.render_template(
            'index.html', has_result=True,
            result=(False, 'Cannot open image from URL.')
        )

    logging.info('Image: %s', imageurl)
    result = app.clf.classify_image(image)
    return flask.render_template(
        'index.html', has_result=True, result=result, imagesrc=imageurl)


@app.route('/classify_upload', methods=['POST'])
def classify_upload():
    try:
        # We will save the file to disk for possible data collection.
        imagefile = flask.request.files['imagefile']
        filename_ = str(datetime.datetime.now()).replace(' ', '_') + \
            werkzeug.secure_filename(imagefile.filename)
        filename = os.path.join(UPLOAD_FOLDER, filename_)
        imagefile.save(filename)
        logging.info('Saving to %s.', filename)
        image = exifutil.open_oriented_im(filename)

    except Exception as err:
        logging.info('Uploaded image open error: %s', err)
        return flask.render_template(
            'index.html', has_result=True,
            result=(False, 'Cannot open uploaded image.')
        )

    result = app.clf.classify_image(image)
    return flask.render_template(
        'index.html', has_result=True, result=result,
        imagesrc=embed_image_html(image)
    )


def embed_image_html(image):
    """Creates an image embedded in HTML base64 format."""
    image_pil = Image.fromarray((255 * image).astype('uint8'))
    image_pil = image_pil.resize((256, 256))
    string_buf = StringIO.StringIO()
    image_pil.save(string_buf, format='png')
    data = string_buf.getvalue().encode('base64').replace('\n', '')
    return 'data:image/png;base64,' + data


def allowed_file(filename):
    return (
        '.' in filename and
        filename.rsplit('.', 1)[1] in ALLOWED_IMAGE_EXTENSIONS
    )


class ImagenetClassifier(object):
    default_args = {
        'model_def_file': (
            '{}/../test1/LSFModelsave.p '.format(REPO_DIRNAME)),
    }
    for key, val in default_args.iteritems():
        if not os.path.exists(val):
            raise Exception(
                "File for {} is missing. Should be at: {}".format(key, val))
    default_args['image_dim'] = 256
    default_args['raw_scale'] = 255.

    def __init__(self, model_def_file, pretrained_model_file, mean_file,
                 raw_scale, class_labels_file, bet_file, image_dim, gpu_mode):
        logging.info('Loading net and associated files...')
        if gpu_mode:
            caffe.set_mode_gpu()
        else:
            caffe.set_mode_cpu()
        self.net = caffe.Classifier(
            model_def_file, pretrained_model_file,
            image_dims=(image_dim, image_dim), raw_scale=raw_scale,
            mean=np.load(mean_file).mean(1).mean(1), channel_swap=(2, 1, 0)
        )

        with open(class_labels_file) as f:
            labels_df = pd.DataFrame([
                {
                    'synset_id': l.strip().split(' ')[0],
                    'name': ' '.join(l.strip().split(' ')[1:]).split(',')[0]
                }
                for l in f.readlines()
            ])
        self.labels = labels_df.sort('synset_id')['name'].values

        self.bet = cPickle.load(open(bet_file))
        # A bias to prefer children nodes in single-chain paths
        # I am setting the value to 0.1 as a quick, simple model.
        # We could use better psychological models here...
        self.bet['infogain'] -= np.array(self.bet['preferences']) * 0.1

    def classify_image(self, image):
        try:
            starttime = time.time()
            scores = self.net.predict([image], oversample=True).flatten()
            endtime = time.time()

            indices = (-scores).argsort()[:5]
            predictions = self.labels[indices]

            # In addition to the prediction text, we will also produce
            # the length for the progress bar visualization.
            meta = [
                (p, '%.5f' % scores[i])
                for i, p in zip(indices, predictions)
            ]
            logging.info('result: %s', str(meta))

            # Compute expected information gain
            expected_infogain = np.dot(
                self.bet['probmat'], scores[self.bet['idmapping']])
            expected_infogain *= self.bet['infogain']

            # sort the scores
            infogain_sort = expected_infogain.argsort()[::-1]
            bet_result = [(self.bet['words'][v], '%.5f' % expected_infogain[v])
                          for v in infogain_sort[:5]]
            logging.info('bet result: %s', str(bet_result))

            return (True, meta, bet_result, '%.3f' % (endtime - starttime))

        except Exception as err:
            logging.info('Classification error: %s', err)
            return (False, 'Something went wrong when classifying the '
                           'image. Maybe try another one?')


def start_tornado(app, port=5000):
    http_server = tornado.httpserver.HTTPServer(
        tornado.wsgi.WSGIContainer(app))
    http_server.listen(port)
    print("Tornado server starting on port {}".format(port))
    tornado.ioloop.IOLoop.instance().start()


def start_from_terminal(app):
    """
    Parse command line options and start the server.
    """
    parser = optparse.OptionParser()
    parser.add_option(
        '-d', '--debug',
        help="enable debug mode",
        action="store_true", default=False)
    parser.add_option(
        '-p', '--port',
        help="which port to serve content on",
        type='int', default=5000)
    parser.add_option(
        '-g', '--gpu',
        help="use gpu mode",
        action='store_true', default=False)

    opts, args = parser.parse_args()
    ImagenetClassifier.default_args.update({'gpu_mode': opts.gpu})

    # Initialize classifier + warm start by forward for allocation
   # app.clf = ImagenetClassifier(**ImagenetClassifier.default_args)
   # app.clf.net.forward()

    if opts.debug:
        app.run(debug=True, host='0.0.0.0', port=opts.port)
    else:
        start_tornado(app, opts.port)


if __name__ == '__main__':
    logging.getLogger().setLevel(logging.INFO)
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    start_from_terminal(app)
                                                                                                                                                                                                                                                                                                                                                                texture_similarity_tv/web_demo/templates/                                                           0000775 0001750 0001750 00000000000 13053754601 021164  5                                                                                                    ustar   bhorkar                         bhorkar                                                                                                                                                                                                                texture_similarity_tv/web_demo/templates/index.html                                                 0000664 0001750 0001750 00000011565 13053754601 023171  0                                                                                                    ustar   bhorkar                         bhorkar                                                                                                                                                                                                                <!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="Caffe demos">
    <meta name="author" content="BVLC (http://bvlc.eecs.berkeley.edu/)">

    <title>Caffe Demos</title>

    <link href="//netdna.bootstrapcdn.com/bootstrap/3.1.1/css/bootstrap.min.css" rel="stylesheet">

    <script type="text/javascript" src="//code.jquery.com/jquery-2.1.1.js"></script>
    <script src="//netdna.bootstrapcdn.com/bootstrap/3.1.1/js/bootstrap.min.js"></script>

    <!-- Script to instantly classify an image once it is uploaded. -->
    <script type="text/javascript">
      $(document).ready(
        function(){
          $('#classifyfile').attr('disabled',true);
          $('#imagefile').change(
            function(){
              if ($(this).val()){
                $('#formupload').submit();
              }
            }
          );
        }
      );
    </script>

    <style>
    body {
      font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
      line-height:1.5em;
      color: #232323;
      -webkit-font-smoothing: antialiased;
    }

    h1, h2, h3 {
      font-family: Times, serif;
      line-height:1.5em;
      border-bottom: 1px solid #ccc;
    }
    </style>
  </head>

  <body>
    <!-- Begin page content -->
    <div class="container">
      <div class="page-header">
        <h1><a href="/">Caffe Demos</a></h1>
        <p>
          The <a href="http://caffe.berkeleyvision.org">Caffe</a> neural network library makes implementing state-of-the-art computer vision systems easy.
        </p>
      </div>

      <div>
        <h2>Classification</h2>
        <a href="/classify_url?imageurl=http%3A%2F%2Fi.telegraph.co.uk%2Fmultimedia%2Farchive%2F02351%2Fcross-eyed-cat_2351472k.jpg">Click for a Quick Example</a>
      </div>

      {% if has_result %}
      {% if not result[0] %}
      <!-- we have error in the result. -->
      <div class="alert alert-danger">{{ result[1] }} Did you provide a valid URL or a valid image file? </div>
      {% else %}
      <div class="media">
        <a class="pull-left" href="#"><img class="media-object" width="192" height="192" src={{ imagesrc }}></a>
        <div class="media-body">
          <div class="bs-example bs-example-tabs">
            <ul id="myTab" class="nav nav-tabs">
              <li class="active"><a href="#infopred" data-toggle="tab">Maximally accurate</a></li>
              <li><a href="#flatpred" data-toggle="tab">Maximally specific</a></li>
            </ul>
            <div id="myTabContent" class="tab-content">
              <div class="tab-pane fade in active" id="infopred">
                <ul class="list-group">
                  {% for single_pred in result[2] %}
                  <li class="list-group-item">
                  <span class="badge">{{ single_pred[1] }}</span>
                  <h4 class="list-group-item-heading">
                    <a href="https://www.google.com/#q={{ single_pred[0] }}" target="_blank">{{ single_pred[0] }}</a>
                  </h4>
                  </li>
                  {% endfor %}
                </ul>
              </div>
              <div class="tab-pane fade" id="flatpred">
                <ul class="list-group">
                  {% for single_pred in result[1] %}
                  <li class="list-group-item">
                  <span class="badge">{{ single_pred[1] }}</span>
                  <h4 class="list-group-item-heading">
                    <a href="https://www.google.com/#q={{ single_pred[0] }}" target="_blank">{{ single_pred[0] }}</a>
                  </h4>
                  </li>
                  {% endfor %}
                </ul>
              </div>
            </div>
          </div>

        </div>
      </div>
      <p> CNN took {{ result[3] }} seconds. </p>
      {% endif %}
      <hr>
      {% endif %}

      <form role="form" action="classify_url" method="get">
        <div class="form-group">
          <div class="input-group">
            <input type="text" class="form-control" name="imageurl" id="imageurl" placeholder="Provide an image URL">
            <span class="input-group-btn">
              <input class="btn btn-primary" value="Classify URL" type="submit" id="classifyurl"></input>
            </span>
          </div><!-- /input-group -->
        </div>
      </form>

      <form id="formupload" class="form-inline" role="form" action="classify_upload" method="post" enctype="multipart/form-data">
        <div class="form-group">
          <label for="imagefile">Or upload an image:</label>
          <input type="file" name="imagefile" id="imagefile">
        </div>
        <!--<input type="submit" class="btn btn-primary" value="Classify File" id="classifyfile"></input>-->
      </form>
    </div>

    <hr>
    <div id="footer">
      <div class="container">
        <p>&copy; BVLC 2014</p>
      </div>
   </div>
 </body>
</html>
                                                                                                                                           texture_similarity_tv/web_demo/exifutil.py                                                          0000664 0001750 0001750 00000002026 13053754601 021371  0                                                                                                    ustar   bhorkar                         bhorkar                                                                                                                                                                                                                """
This script handles the skimage exif problem.
"""

from PIL import Image
import numpy as np

ORIENTATIONS = {   # used in apply_orientation
    2: (Image.FLIP_LEFT_RIGHT,),
    3: (Image.ROTATE_180,),
    4: (Image.FLIP_TOP_BOTTOM,),
    5: (Image.FLIP_LEFT_RIGHT, Image.ROTATE_90),
    6: (Image.ROTATE_270,),
    7: (Image.FLIP_LEFT_RIGHT, Image.ROTATE_270),
    8: (Image.ROTATE_90,)
}


def open_oriented_im(im_path):
    im = Image.open(im_path)
    if hasattr(im, '_getexif'):
        exif = im._getexif()
        if exif is not None and 274 in exif:
            orientation = exif[274]
            im = apply_orientation(im, orientation)
    img = np.asarray(im).astype(np.float32) / 255.
    if img.ndim == 2:
        img = img[:, :, np.newaxis]
        img = np.tile(img, (1, 1, 3))
    elif img.shape[2] == 4:
        img = img[:, :, :3]
    return img


def apply_orientation(im, orientation):
    if orientation in ORIENTATIONS:
        for method in ORIENTATIONS[orientation]:
            im = im.transpose(method)
    return im
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          texture_similarity_tv/web_demo/exifutil.pyc                                                         0000664 0001750 0001750 00000003020 13053754601 021527  0                                                                                                    ustar   bhorkar                         bhorkar                                                                                                                                                                                                                ó
,h\Xc           @   s¥   d  Z  d d l m Z d d l Z i e j f d 6e j f d 6e j f d 6e j e j f d 6e j	 f d 6e j e j	 f d	 6e j f d
 6Z
 d   Z d   Z d S(   s/   
This script handles the skimage exif problem.
iÿÿÿÿ(   t   ImageNi   i   i   i   i   i   i   c         C   s  t  j |   } t | d  ra | j   } | d  k	 ra d | k ra | d } t | |  } qa n  t j |  j t j	  d } | j
 d k rÆ | d  d   d  d   t j f } t j | d  } n; | j d d k r| d  d   d  d   d  d  f } n  | S(	   Nt   _getexifi  g     ào@i   i   i   i   (   i   i   i   (   R    t   opent   hasattrR   t   Nonet   apply_orientationt   npt   asarrayt   astypet   float32t   ndimt   newaxist   tilet   shape(   t   im_patht   imt   exift   orientationt   img(    (    sI   /home/bhorkar/fashion_cloths/deep_describe/googlenet/web_demo/exifutil.pyt   open_oriented_im   s    
"(c         C   s7   | t  k r3 x$ t  | D] } |  j |  }  q Wn  |  S(   N(   t   ORIENTATIONSt	   transpose(   R   R   t   method(    (    sI   /home/bhorkar/fashion_cloths/deep_describe/googlenet/web_demo/exifutil.pyR   #   s    (   t   __doc__t   PILR    t   numpyR   t   FLIP_LEFT_RIGHTt
   ROTATE_180t   FLIP_TOP_BOTTOMt	   ROTATE_90t
   ROTATE_270R   R   R   (    (    (    sI   /home/bhorkar/fashion_cloths/deep_describe/googlenet/web_demo/exifutil.pyt   <module>   s   	                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                texture_similarity_tv/web_demo/readme.md                                                            0000664 0001750 0001750 00000003524 13053754601 020751  0                                                                                                    ustar   bhorkar                         bhorkar                                                                                                                                                                                                                ---
title: Web demo
description: Image classification demo running as a Flask web server.
category: example
include_in_docs: true
priority: 10
---

# Web Demo

## Requirements

The demo server requires Python with some dependencies.
To make sure you have the dependencies, please run `pip install -r examples/web_demo/requirements.txt`, and also make sure that you've compiled the Python Caffe interface and that it is on your `PYTHONPATH` (see [installation instructions](/installation.html)).

Make sure that you have obtained the Reference CaffeNet Model and the ImageNet Auxiliary Data:

    ./scripts/download_model_binary.py models/bvlc_reference_caffenet
    ./data/ilsvrc12/get_ilsvrc_aux.sh

NOTE: if you run into trouble, try re-downloading the auxiliary files.

## Run

Running `python examples/web_demo/app.py` will bring up the demo server, accessible at `http://0.0.0.0:5000`.
You can enable debug mode of the web server, or switch to a different port:

    % python examples/web_demo/app.py -h
    Usage: app.py [options]

    Options:
      -h, --help            show this help message and exit
      -d, --debug           enable debug mode
      -p PORT, --port=PORT  which port to serve content on

## How are the "maximally accurate" results generated?

In a nutshell: ImageNet predictions are made at the leaf nodes, but the organization of the project allows leaf nodes to be united via more general parent nodes, with 'entity' at the very top.
To give "maximally accurate" results, we "back off" from maximally specific predictions to maintain a high accuracy.
The `bet_file` that is loaded in the demo provides the graph structure and names of all relevant ImageNet nodes as well as measures of information gain between them.
Please see the "Hedging your bets" paper from [CVPR 2012](http://www.image-net.org/projects/hedging/) for further information.
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            