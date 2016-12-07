'''Boundary detection---suff diff to everything else to require own file'''

import os
import sys
import time

from equivariant import deep_bsd

import os
import sys
import time

import cPickle as pkl
import cv2
import equivariant
import numpy as np
import scipy as sp
import scipy.linalg as scilin
import scipy.ndimage.interpolation as sciint
import skimage.io as skio
import tensorflow as tf

import input_data

from equivariant import *
from matplotlib import pyplot as plt
from scipy import ndimage
from scipy import misc
from steer_conv import *

###HELPER FUNCTIONS------------------------------------------------------------------


def build_feed_dict(opt, io, batch, lr, pt, lr_, pt_):
	'''Build a feed_dict appropriate to training regime'''
	batch_x, batch_y, __ = batch
	fd = {lr : lr_, pt : pt_}
	bs = opt['batch_size']
	for g in xrange(len(opt['deviceIdxs'])):
		fd[io['x'][g]] = batch_x[g*bs:(g+1)*bs,:]
		fd[io['y'][g]] = batch_y[g*bs:(g+1)*bs]
	return fd

##### TRAINING LOOPS #####
def loop(mode, sess, io, opt, data, cost, lr, lr_, pt, sl=None, epoch=0,
		 optim=None, step=0, anneal=0.):
	"""Run a loop"""
	X = data[mode+'_x']
	Y = data[mode+'_y']
	is_training = (mode=='train')
	n_GPUs = len(opt['deviceIdxs'])
	generator = pklbatcher(X, Y, n_GPUs*opt['batch_size'], anneal=anneal,
						   shuffle=is_training, augment=opt['augment'],
						   img_shape=(opt['dim'], opt['dim2'], 3))
	#if is_training:
	#	generator = threadedGen(generator)
	cost_total = 0.
	for i, batch in enumerate(generator):
		fd = build_feed_dict(opt, io, batch, lr, pt, lr_, is_training)
		if sl is not None:
				fd[sl] = np.maximum(1. - float(epoch)/100.,0.)
		if mode == 'train':
			__, cost_ = sess.run([optim, cost], feed_dict=fd)
		else:
			cost_ = sess.run(cost, feed_dict=fd)
		if step % opt['display_step'] == 0:
			print('  ' + mode + ' loss: %f' % cost_)
		cost_total += cost_
	return cost_total/(i+1.), step

def construct_model_and_optimizer(opt, io, lr, pt, sl=None):
	"""Build the model and an single/multi-GPU optimizer"""
	if len(opt['deviceIdxs']) == 1:
		size = opt['dim']
		size2 = opt['dim2']
		pred, __ = opt['model'](opt, io['x'][0], pt)
		loss = get_loss(opt, pred, io['y'][0], sl=sl)
		train_op = build_optimizer(loss, lr, opt)
	return loss, train_op, pred

def save_predictions(sess, x, opt, pred, pt, data, epoch):
	"""Save predictions to output folder"""
	X = data['valid_x']
	Y = data['valid_y']
	save_path = opt['test_path'] + '/T_' + str(epoch)
	if not os.path.exists(save_path):
		os.mkdir(save_path)
	generator = pklbatcher(X, Y, opt['batch_size'], shuffle=False,
						   augment=False, img_shape=(opt['dim'], opt['dim2']))
	# Use sigmoid to map to [0,1]
	bsd_map = tf.nn.sigmoid(pred['fuse'])
	j = 0
	for batch in generator:
		batch_x, batch_y, excerpt = batch
		output = sess.run(bsd_map, feed_dict={x: batch_x, pt: False})
		for i in xrange(output.shape[0]):
			save_name = save_path + '/' + str(excerpt[i]).replace('.jpg','.png')
			im = output[i,:,:,0]
			im = (255*im).astype('uint8')
			if data['valid_x'][excerpt[i]]['transposed']:
				im = im.T
			skio.imsave(save_name, im)
			j += 1
	print('Saved predictions to: %s' % (save_path,))

def rerun_model(opt, data):
	"""Generalized training function
	
	opt: dict of options
	data: dict of numpy data
	"""
	n_GPUs = len(opt['deviceIdxs'])
	print('Using Multi-GPU Model with %d devices.' % n_GPUs)
	# Make placeholders
	io = {}
	io['x'] = []
	io['y'] = []
	for g in opt['deviceIdxs']:
		with tf.device('/gpu:%d' % g):
			io_x, io_y = get_io_placeholders(opt)
			io['x'].append(io_x)
			io['y'].append(io_y)
	lr = tf.placeholder(tf.float32, name='learning_rate')
	pt = tf.placeholder(tf.bool, name='phase_train')
	if opt['anneal_sl']:
		sl = tf.placeholder(tf.float32, [], name='side_loss_multiplier')
	else:
		sl = None
	
	# Construct model and optimizer
	loss, train_op, pred = construct_model_and_optimizer(opt, io, lr, pt, sl=sl)
	
	# Initializing the variables
	init = tf.initialize_all_variables()
	#init_var = []
	#for var in tf.all_variables():
	#	if 'ExponentialMovingAverage' in var.name:
	#		init_var.append(var)
	#init = tf.initialize_variables(init_var)
	
	# Summary writers
	tcost_ss = create_scalar_summary('training_cost')
	vcost_ss = create_scalar_summary('validation_cost')
	lr_ss = create_scalar_summary('learning_rate')
	
	# Configure tensorflow session
	config = config_init()
	if n_GPUs == 1:
		config.inter_op_parallelism_threads = 1 #prevent inter-session threads?
	sess = tf.Session(config=config)
	summary = tf.train.SummaryWriter(opt['log_path'], sess.graph)
	print('Summaries constructed...')
	
	sess.run(init)
	saver = tf.train.Saver()
	if opt['load_pretrained']:
		saver.restore(sess, './checkpoints/deep_bsd/trialS/model.ckpt')
	start = time.time()

##### MAIN SCRIPT #####
def get_settings(opt):
	# Parameters
	tf.reset_default_graph()
	
	# Default configuration
	opt['trial_num'] = 'R'
	opt['combine_train_val'] = False	
	
	data = load_pkl(opt['data_dir'], 'bsd_pkl_float', prepend='')
	opt['model'] = getattr(equivariant, 'deep_bsd')
	opt['is_bsd'] = True
	opt['lr'] = 1e-2
	opt['batch_size'] = 2
	opt['std_mult'] = 1
	opt['momentum'] = 0.95
	opt['psi_preconditioner'] = 3.4
	opt['delay'] = 8
	opt['display_step'] = 8
	opt['save_step'] = 10
	opt['is_classification'] = True
	opt['n_epochs'] = 250
	opt['dim'] = 321
	opt['dim2'] = 481
	opt['n_channels'] = 3
	opt['n_classes'] = 10
	opt['n_filters'] = 8 #32
	opt['filter_gain'] = 2
	opt['augment'] = True
	opt['lr_div'] = 10.
	opt['log_path'] = './logs/deep_bsd'
	opt['checkpoint_path'] = './checkpoints/deep_bsd'
	opt['test_path'] = './bsd/trial' + opt['trial_num']
	opt['anneal_sl'] = True
	opt['load_pretrained'] = False
	opt['sparsity'] = 1
	if not os.path.exists(opt['test_path']):
		os.mkdir(opt['test_path'])
	opt['save_test_step'] = 5
	
	# Check that save paths exist
	opt['log_path'] = opt['log_path'] + '/trial' + str(opt['trial_num'])
	opt['checkpoint_path'] = opt['checkpoint_path'] + '/trial' + \
							str(opt['trial_num']) 
	if not os.path.exists(opt['log_path']):
		print('Creating log path')
		os.mkdir(opt['log_path'])
	if not os.path.exists(opt['checkpoint_path']):
		print('Creating checkpoint path')
		os.mkdir(opt['checkpoint_path'])
	opt['checkpoint_path'] = opt['checkpoint_path'] + '/model.ckpt'
	
	# Print out options
	for key, val in opt.iteritems():
		print(key + ': ' + str(val))
	return opt, data

def run(opt):
	opt, data = get_settings(opt)
	return rerun_model(opt, data)


if __name__ == '__main__':
	deviceIdxs = [int(x.strip()) for x in sys.argv[1].split(',')]
	opt = {}
	opt['deviceIdxs'] = deviceIdxs
	opt['data_dir'] = sys.argv[2]
	opt['machine'] = sys.argv[3]

	run(opt)
	print("ALL FINISHED! :)")
