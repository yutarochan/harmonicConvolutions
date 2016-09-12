'''MNIST tests'''

'''Test the gConv script'''

import os
import sys
import time

import cv2
import numpy as np
import scipy.linalg as scilin
import tensorflow as tf

import input_data

from gConv2 import *
from matplotlib import pyplot as plt


# Create model
def conv_Z(x, drop_prob, n_filters, n_classes):
	# Store layers weight & bias
	weights = {
		'w1' : get_weights([3,3,1,n_filters], name='W1'),
		'w2' : get_weights([3,3,n_filters,n_filters], name='W2'),
		'w3' : get_weights([n_filters*6*6,500], name='W3'),
		'out': get_weights([500, n_classes], name='W4')
	}
	
	biases = {
		'b1': tf.Variable(tf.constant(1e-2, shape=[n_filters])),
		'b2': tf.Variable(tf.constant(1e-2, shape=[n_filters])),
		'b3': tf.Variable(tf.constant(1e-2, shape=[500])),
		'out': tf.Variable(tf.constant(1e-2, shape=[n_classes]))
	}
	
	# Reshape input picture
	x = tf.reshape(x, shape=[-1, 28, 28, 1])
	
	# Convolution Layer
	cv1 = conv2d(x, weights['w1'], biases['b1'], name='gc1')
	mp1 = tf.nn.relu(maxpool2d(cv1, k=2))
	
	# Convolution Layer
	cv2 = conv2d(mp1, weights['w2'], biases['b2'], name='gc2')
	mp2 = tf.nn.relu(maxpool2d(cv2, k=2))

	# Fully connected layer
	fc3 = tf.reshape(mp2, [-1, weights['w3'].get_shape().as_list()[0]])
	fc3 = tf.nn.bias_add(tf.matmul(fc3, weights['w3']), biases['b3'])
	fc3 = tf.nn.relu(fc3)
	# Apply Dropout
	fc3 = tf.nn.dropout(fc3, drop_prob)
	
	# Output, class prediction
	out = tf.nn.bias_add(tf.matmul(fc3, weights['out']), biases['out'])
	return out

def gConv_simple(x, drop_prob, n_filters, n_classes):
	# Store layers weight & bias
	weights = {
		'w1' : get_weights([3,3,1,n_filters], name='W1'),
		'w2' : get_weights([3,3,n_filters*4,n_filters], name='W2'),
		'w3' : get_weights([n_filters*6*6,500], name='W3'),
		'out': get_weights([500, n_classes], name='W4')
	}
	
	biases = {
		'b1': tf.Variable(tf.constant(1e-2, shape=[n_filters])),
		'b2': tf.Variable(tf.constant(1e-2, shape=[n_filters])),
		'b3': tf.Variable(tf.constant(1e-2, shape=[500])),
		'out': tf.Variable(tf.constant(1e-2, shape=[n_classes]))
	}
	
	# Reshape input picture
	x = tf.reshape(x, shape=[-1, 28, 28, 1])
	
	# Convolution Layer
	gc1 = gConv(x, weights['w1'], biases['b1'], name='gc1')
	gc1_ = tf.nn.relu(maxpool2d(gc1, k=2))
	
	# Convolution Layer
	gc2 = gConv(gc1_, weights['w2'], biases['b2'], name='gc2')
	gc2_ = coset_pooling(gc2)
	gc2_ = tf.nn.relu(maxpool2d(gc2_, k=2))

	# Fully connected layer
	fc3 = tf.reshape(gc2_, [-1, weights['w3'].get_shape().as_list()[0]])
	fc3 = tf.nn.bias_add(tf.matmul(fc3, weights['w3']), biases['b3'])
	fc3 = tf.nn.relu(fc3)
	# Apply Dropout
	fc3 = tf.nn.dropout(fc3, drop_prob)
	
	# Output, class prediction
	out = tf.nn.bias_add(tf.matmul(fc3, weights['out']), biases['out'])
	return out

def gConv_taco(x, drop_prob, n_filters, n_classes):
	# Store layers weight & bias
	weights = {
		'w1' : get_weights([3,3,1,n_filters], name='W1'),
		'w2' : get_weights([3,3,n_filters*4,n_filters], name='W2'),
		'w3' : get_weights([3,3,n_filters*4,n_filters], name='W3'),
		'w4' : get_weights([3,3,n_filters*4,n_filters], name='W4'),
		'w5' : get_weights([3,3,n_filters*4,n_filters], name='W5'),
		'w6' : get_weights([3,3,n_filters*4,n_filters], name='W6'),
		'w7' : get_weights([3,3,n_filters*4,n_filters], name='W7'),
		'out': get_weights([160, n_classes], name='W4')
	}
	
	biases = {
		'out': tf.Variable(tf.constant(1e-2, shape=[n_classes]))
	}
	
	# Reshape input picture
	xin = tf.reshape(x, shape=[-1, 28, 28, 1])
	
	# Convolution Layerss
	gc1 = tf.nn.relu(gConv(xin, weights['w1'], name='gc1'))
	gc2 = tf.nn.relu(gConv(gc1, weights['w2'], name='gc2'))
	p2_ = maxpool2d(gc2, k=2)
	gc3 = tf.nn.relu(gConv(p2_, weights['w3'], name='gc3'))
	gc4 = tf.nn.relu(gConv(gc3, weights['w4'], name='gc4'))
	gc5 = tf.nn.relu(gConv(gc4, weights['w5'], name='gc5'))
	gc6 = tf.nn.relu(gConv(gc5, weights['w6'], name='gc6'))
	gc7 = tf.nn.relu(gConv(gc6, weights['w7'], name='gc7'))
	
	gc7_ = coset_pooling(gc7)
	gc7_ = tf.reshape(gc7, [-1,160])
	
	# Output, class prediction
	out = tf.nn.bias_add(tf.matmul(gc7_, weights['out']), biases['out'])
	return out

def gConv_steer(x, drop_prob, n_filters, n_classes):
	# Store layers weight & bias
	weights = {
		'w1' : get_weights([1,1,2,n_filters], name='W1'),
		'w2' : get_weights([1,1,2*n_filters,n_filters], name='W2'),
		'w3' : get_weights([n_filters*6*6,500], name='W3'),
		'out': get_weights([500, n_classes], name='W4')
	}
	
	biases = {
		'b1': tf.Variable(tf.constant(1e-2, shape=[n_filters])),
		'b2': tf.Variable(tf.constant(1e-2, shape=[n_filters])),
		'b3': tf.Variable(tf.constant(1e-2, shape=[500])),
		'out': tf.Variable(tf.constant(1e-2, shape=[n_classes]))
	}
	
	# Reshape input picture
	x = tf.reshape(x, shape=[-1, 28, 28, 1])
	
	# Convolution Layer
	#x = conv2d(x, weights['w1'], biases['b1'], name='gc1')
	sc1 = steer_conv(x, weights['w1'], biases['b1'])
	mp1 = tf.nn.relu(maxpool2d(sc1, k=2))
	
	# Convolution Layer
	#mp1 = conv2d(mp1, weights['w2'], biases['b2'], name='gc2')
	sc2 = steer_conv(mp1, weights['w2'], biases['b2'])
	mp2 = tf.nn.relu(maxpool2d(sc2, k=2))

	# Fully connected layer
	fc3 = tf.reshape(mp2, [-1, weights['w3'].get_shape().as_list()[0]])
	fc3 = tf.nn.bias_add(tf.matmul(fc3, weights['w3']), biases['b3'])
	fc3 = tf.nn.relu(fc3)
	# Apply Dropout
	fc3 = tf.nn.dropout(fc3, drop_prob)
	
	# Output, class prediction
	out = tf.nn.bias_add(tf.matmul(fc3, weights['out']), biases['out'])
	return out

def conv2d(X, V, b=None, strides=(1,1,1,1), padding='VALID', name='conv2d'):
    """conv2d wrapper"""
    VX = tf.nn.conv2d(X, V, strides=strides, padding=padding, name=name+'_')
    if b is not None:
        VX = tf.nn.bias_add(VX, b)
    return VX

def maxpool2d(x, k=2):
    # MaxPool2D wrapper
    return tf.nn.max_pool(x, ksize=[1,k,k,1], strides=[1,k,k,1], padding='SAME')

def get_weights(filter_shape, W_init=None, name='W'):
	if W_init == None:
		stddev = np.sqrt(2.0 / np.prod(filter_shape[:2]))
		W_init = tf.random_normal(filter_shape, stddev=stddev)
	return tf.Variable(W_init, name=name)

def random_rotation(X):
	"""Randomly rotate images, independently in minibatch"""
	X = np.reshape(X, [-1,28,28,1])
	Xsh = X.shape
	for i in xrange(Xsh[0]):
		angle = np.random.rand() * 360.
		M = cv2.getRotationMatrix2D((Xsh[2]/2,Xsh[1]/2), angle, 1)
		X[i,...] = cv2.warpAffine(X[i,...], M, (Xsh[2],Xsh[1])).reshape(Xsh[1:])
	return X.reshape(-1,784)

def run():
	mnist = input_data.read_data_sets("/tmp/data/", one_hot=True)
	
	# Parameters
	lr = 1e-3
	batch_size = 500
	dataset_size = 50000
	valid_size = 5000
	n_epochs = 500
	display_step = dataset_size / batch_size
	save_step = 100
	model = 'steer'
	test_rot = False
	
	# Network Parameters
	n_input = 784 # MNIST data input (img shape: 28*28)
	n_classes = 10 # MNIST total classes (0-9 digits)
	dropout = 0.75 # Dropout, probability to keep units
	n_filters = 10
	
	# tf Graph input
	x = tf.placeholder(tf.float32, [None, n_input])
	y = tf.placeholder(tf.float32, [None, n_classes])
	learning_rate = tf.placeholder(tf.float32)
	keep_prob = tf.placeholder(tf.float32) 
	
	# Construct model
	if model == 'simple_Z':
		pred = conv_Z(x, keep_prob, n_filters, n_classes)
	elif model == 'simple':
		pred = gConv_simple(x, keep_prob, n_filters, n_classes)
	elif model == 'taco':
		pred = gConv_taco(x, keep_prob, n_filters, n_classes)
	elif model == 'steer':
		pred = gConv_steer(x, keep_prob, n_filters, n_classes)
	else:
		print('Model unrecognized')
		sys.exit(1)
	
	# Define loss and optimizer
	cost = tf.reduce_mean(tf.nn.softmax_cross_entropy_with_logits(pred, y))
	#optimizer = tf.train.MomentumOptimizer(learning_rate=lr, momentum=0.9).minimize(cost)
	optimizer = tf.train.AdamOptimizer(learning_rate=learning_rate).minimize(cost)
	
	# Evaluate model
	correct_pred = tf.equal(tf.argmax(pred, 1), tf.argmax(y, 1))
	accuracy = tf.reduce_mean(tf.cast(correct_pred, tf.float32))
			
	# Initializing the variables
	init = tf.initialize_all_variables()
	
	# Launch the graph
	with tf.Session() as sess:
		sess.run(init)
		step = 1
		start = time.time()
		# Keep training until reach max iterations
		while step < n_epochs * (dataset_size / batch_size):
			batch_x, batch_y = mnist.train.next_batch(batch_size)
			lr_current = lr/np.sqrt(1.+step*(float(batch_size) / dataset_size))
			
			# Optimize
			feed_dict = {x: batch_x, y: batch_y, keep_prob: dropout,
						 learning_rate : lr_current}
			sess.run(optimizer, feed_dict=feed_dict)
			
			if step % display_step == 0:
				# Calculate batch loss and accuracy
				feed_dict = {x: batch_x, y: batch_y, keep_prob: 1.}
				loss, acc = sess.run([cost, accuracy], feed_dict=feed_dict)
				
				# Validation accuracy
				vacc = 0.
				for i in xrange(valid_size/batch_size):
					X = mnist.validation.images[batch_size*i:batch_size*(i+1)]
					Y = mnist.validation.labels[batch_size*i:batch_size*(i+1)]
					if test_rot:
						X = random_rotation(X)
					feed_dict={x : X, y : Y, keep_prob: 1.}
					vacc += sess.run(accuracy, feed_dict=feed_dict)
					
				print "[" + str(step*batch_size/dataset_size) + \
					"], Minibatch Loss: " + \
					"{:.6f}".format(loss) + ", Train Acc: " + \
					"{:.5f}".format(acc) + ", Time: " + \
					"{:.5f}".format(time.time()-start) + ", Val acc: " + \
					"{:.5f}".format(vacc*batch_size/valid_size)
			step += 1
		
		print "Testing"
		
		# Test accuracy
		tacc = 0.
		for i in xrange(200):
			X = mnist.test.images[50*i:50*(i+1)]
			if test_rot:
				X = random_rotation(X)
			feed_dict={x: X,
					   y: mnist.test.labels[50*i:50*(i+1)], keep_prob: 1.}
			tacc += sess.run(accuracy, feed_dict=feed_dict)
		print('Test accuracy: %f' % (tacc/200.,))


def forward():
	mnist = input_data.read_data_sets("/tmp/data/", one_hot=True)
	
	# Network Parameters
	n_input = 784 # MNIST data input (img shape: 28*28)
	n_filters = 10
	
	# tf Graph input
	x = tf.placeholder(tf.float32, [None,28,28,1])
	y = steer_conv(x, 0)

	# Initializing the variables
	init = tf.initialize_all_variables()
	
	X = mnist.train.next_batch(100)[0][np.random.randint(100),:]
	X = np.reshape(X, [1,28,28,1])
	# Launch the graph
	with tf.Session() as sess:
		sess.run(init)
		Y = sess.run(y, feed_dict={x : X})
	
	fig = plt.figure(1)
	plt.imshow(np.squeeze(Y), cmap='gray', interpolation='nearest')
	plt.show()


if __name__ == '__main__':
	run()
	#forward()