"""
Harmonic Network Definitions

This file contains the definition of our neural network models. This
should be used an example of how to create a harmonic network using our 
helper functions in tensorflow.

"""
import tensorflow as tf
arg_scope = tf.contrib.framework.arg_scope

import harmonic_network_lite as hn_lite
from harmonic_network_helpers import *

def deep_mnist(opt, x, train_phase, device='/cpu:0'):
	"""High frequency convolutions are unstable, so get rid of them"""
	# Sure layers weight & bias
	order = 1
	# Number of Filters
	nf = opt['n_filters']
	nf2 = int(nf*opt['filter_gain'])
	nf3 = int(nf*(opt['filter_gain']**2.))
	bs = opt['batch_size']
	fs = opt['filter_size']
	nch = opt['n_channels']
	ncl = opt['n_classes']
	sm = opt['std_mult']

	# Create bias for final layer
	with tf.device(device):
		bias = tf.get_variable('b7', shape=[opt['n_classes']],
							   initializer=tf.constant_initializer(1e-2))
		x = tf.reshape(x, shape=[bs,opt['dim'],opt['dim'],1,1,nch])
	
	with arg_scope([hn_lite.conv2d, hn_lite.non_linearity, hn_lite.batch_norm], device=device):
		# Convolutional Layers with pooling
		with tf.name_scope('block1') as scope:
			cv1 = hn_lite.conv2d(x, nf, fs, padding='SAME', name='1')
			cv1 = hn_lite.non_linearity(cv1, tf.nn.relu, name='1')
			
			cv2 = hn_lite.conv2d(cv1, nf, fs, padding='SAME', name='2')
			cv2 = hn_lite.batch_norm(cv2, train_phase, name='bn1')

		with tf.name_scope('block2') as scope:
			cv2 = hn_lite.mean_pool(cv2, ksize=(1,2,2,1), strides=(1,2,2,1))
			cv3 = hn_lite.conv2d(cv2, nf2, fs, padding='SAME', name='3')
			cv3 = hn_lite.non_linearity(cv3, tf.nn.relu, name='3')
			
			cv4 = hn_lite.conv2d(cv3, nf2, fs, padding='SAME', name='4')
			cv4 = hn_lite.batch_norm(cv4, train_phase, name='bn2')

		with tf.name_scope('block3') as scope:
			cv4 = hn_lite.mean_pool(cv4, ksize=(1,2,2,1), strides=(1,2,2,1))
			cv5 = hn_lite.conv2d(cv4, nf3, fs, padding='SAME', name='5')
			cv5 = hn_lite.non_linearity(cv5, tf.nn.relu, name='5')
			
			cv6 = hn_lite.conv2d(cv5, nf3, fs, padding='SAME', name='6')
			cv6 = hn_lite.batch_norm(cv6, train_phase, name='bn3')

		# Final Layer
		with tf.name_scope('block4') as scope:
			cv7 = hn_lite.conv2d(cv6, ncl, fs, padding='SAME', phase=False,
						name='7')
			real = hn_lite.sum_magnitudes(cv7)
			cv7 = tf.reduce_mean(real, axis=[1,2,3,4])
			return tf.nn.bias_add(cv7, bias) 


def deep_bsd(opt, x, train_phase, device='/cpu:0'):
	"""High frequency convolutions are unstable, so get rid of them"""
	# Sure layers weight & bias
	order = 1
	nf = int(opt['n_filters'])
	nf2 = int((opt['filter_gain'])*nf)
	nf3 = int((opt['filter_gain']**2)*nf)
	nf4 = int((opt['filter_gain']**3)*nf)
	bs = opt['batch_size']
	fs = opt['filter_size']
	nch = opt['n_channels']
	ncl = opt['n_classes']
	tp = train_phase
	d = device
	
	sm = opt['std_mult']
	with tf.device(d):
		bias = tf.get_variable('fuse', shape=[1],
							   initializer=tf.constant_initializer(1e-2))
		
		side_weights = {
			'sw1' : tf.get_variable('sw1', shape=[1,1,(order+1)*nf,1],
									initializer=tf.constant_initializer(1e-2)),
			'sw2' : tf.get_variable('sw2', shape=[1,1,(order+1)*nf2,1],
									initializer=tf.constant_initializer(1e-2)),
			'sw3' : tf.get_variable('sw3', shape=[1,1,(order+1)*nf3,1],
									initializer=tf.constant_initializer(1e-2)),
			'sw4' : tf.get_variable('sw4', shape=[1,1,(order+1)*nf4,1],
									initializer=tf.constant_initializer(1e-2)),
			'sw5' : tf.get_variable('sw5', shape=[1,1,(order+1)*nf4,1],
									initializer=tf.constant_initializer(1e-2)),
			'h1' : tf.get_variable('h1', shape=[1,1,5,1],
								   initializer=tf.constant_initializer(1e-2))
		}
		fm = {}
		cv = {}
		
	# Convolutional Layers
	with tf.name_scope('stage1') as scope:
		cv1 = h_conv(x, [fs,fs,nch,nf], name='1_1', device=d)
		cv1 = h_nonlin(cv1, tf.nn.relu, name='1_1', device=d)
	
		cv2 = h_conv(cv1, [fs,fs,nf,nf], name='1_2', device=d)
		cv2 = h_batch_norm(cv2, tf.nn.relu, tp, name='bn1', device=d)
		fm[1] = conv2d(stack_magnitudes(cv2), side_weights['sw1']) 
		cv[1] = cv2
	
	with tf.name_scope('stage2') as scope:
		cv3 = mean_pooling(cv2, ksize=(1,2,2,1), strides=(1,2,2,1))
		cv3 = h_conv(cv3, [fs,fs,nf,nf2], name='2_1', device=d)
		cv3 = h_nonlin(cv3, tf.nn.relu, name='2_1', device=d)
	
		cv4 = h_conv(cv3, [fs,fs,nf2,nf2], name='2_2', device=d)
		cv4 = h_batch_norm(cv4, tf.nn.relu, train_phase, name='bn2', device=d)
		fm[2] = conv2d(stack_magnitudes(cv4), side_weights['sw2']) 
		cv[2] = cv4
		
	with tf.name_scope('stage3') as scope:
		cv5 = mean_pooling(cv4, ksize=(1,2,2,1), strides=(1,2,2,1))
		cv5 = h_conv(cv5, [fs,fs,nf2,nf3], name='3_1', device=d)
		cv5 = h_nonlin(cv5, tf.nn.relu, name='3_1', device=d)
	
		cv6 = h_conv(cv5, [fs,fs,nf3,nf3], name='3_2', device=d)
		cv6 = h_batch_norm(cv6, tf.nn.relu, train_phase, name='bn3', device=d)
		fm[3] = conv2d(stack_magnitudes(cv6), side_weights['sw3']) 
		cv[3] = cv6
		
	with tf.name_scope('stage4') as scope:
		cv7 = mean_pooling(cv6, ksize=(1,2,2,1), strides=(1,2,2,1))
		cv7 = h_conv(cv7, [fs,fs,nf3,nf4], name='4_1', device=d)
		cv7 = h_nonlin(cv7, tf.nn.relu, name='4_1', device=d)
	
		cv8 = h_conv(cv7, [fs,fs,nf4,nf4], name='4_2', device=d)
		cv8 = h_batch_norm(cv8, tf.nn.relu, train_phase, name='bn4', device=d)
		fm[4] = conv2d(stack_magnitudes(cv8), side_weights['sw4']) 
		cv[4] = cv8
		
	with tf.name_scope('stage5') as scope:
		cv9 = mean_pooling(cv8, ksize=(1,2,2,1), strides=(1,2,2,1))
		cv9 = h_conv(cv9, [fs,fs,nf4,nf4], name='5_1', device=d)
		cv9 = h_nonlin(cv9, tf.nn.relu, name='5_1', device=d)
	
		cv10 = h_conv(cv9, [fs,fs,nf4,nf4], name='5_2', device=d)
		cv10 = h_batch_norm(cv10, tf.nn.relu, train_phase, name='bn5', device=d)
		fm[5] = conv2d(stack_magnitudes(cv10), side_weights['sw5']) 
		cv[5] = cv10
		
		out = 0
	
	fms = {}
	side_preds = []
	xsh = tf.shape(x)
	with tf.name_scope('fusion') as scope:
		for key in fm.keys():
			if opt['machine'] == 'grumpy':
				fms[key] = tf.image.resize_images(fm[key], tf.stack([xsh[1], xsh[2]]))
			else:
				fms[key] = tf.image.resize_images(fm[key], xsh[1], xsh[2])
			side_preds.append(fms[key])
		side_preds = tf.concat(axis=3, values=side_preds)

		fms['fuse'] = conv2d(side_preds, side_weights['h1'], b=bias, padding='SAME')
		return fms, out, weights, psis, cv

