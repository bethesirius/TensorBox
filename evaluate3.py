import tensorflow as tf
import os
import json
import subprocess
import sysv_ipc

from scipy.misc import imread, imresize
from scipy import misc

from train import build_forward
from utils.annolist import AnnotationLib as al
from utils.train_utils import add_rectangles, rescale_boxes
from pymouse import PyMouse

import cv2
import argparse
import time
import numpy as np

def get_image_dir(args):
    weights_iteration = int(args.weights.split('-')[-1])
    expname = '_' + args.expname if args.expname else ''
    image_dir = '%s/images_%s_%d%s' % (os.path.dirname(args.weights), os.path.basename(args.test_boxes)[:-5], weights_iteration, expname)
    return image_dir

def get_results(args, H):
    tf.reset_default_graph()
    x_in = tf.placeholder(tf.float32, name='x_in', shape=[H['image_height'], H['image_width'], 3])
    if H['use_rezoom']:
        pred_boxes, pred_logits, pred_confidences, pred_confs_deltas, pred_boxes_deltas = build_forward(H, tf.expand_dims(x_in, 0), 'test', reuse=None)
        grid_area = H['grid_height'] * H['grid_width']
        pred_confidences = tf.reshape(tf.nn.softmax(tf.reshape(pred_confs_deltas, [grid_area * H['rnn_len'], 2])), [grid_area, H['rnn_len'], 2])
        if H['reregress']:
            pred_boxes = pred_boxes + pred_boxes_deltas
    else:
        pred_boxes, pred_logits, pred_confidences = build_forward(H, tf.expand_dims(x_in, 0), 'test', reuse=None)
    saver = tf.train.Saver()
    with tf.Session() as sess:
        sess.run(tf.initialize_all_variables())
        saver.restore(sess, args.weights)

        pred_annolist = al.AnnoList()

        true_annolist = al.parse(args.test_boxes)
        data_dir = os.path.dirname(args.test_boxes)
        image_dir = get_image_dir(args)
        subprocess.call('mkdir -p %s' % image_dir, shell=True)

	#ivc = cv2.VideoCapture('/home/caucse/images/ets.mp4')
	#c=1

	#if vc.isOpened():
    	#    rval , frame = vc.read()
	#else:
	#    rval = False

	memory = sysv_ipc.SharedMemory(123463)
	memory2 = sysv_ipc.SharedMemory(123464)
	size = 768, 1024, 3

	pedal = PyMouse()
	pedal.press(1)
	road_center = 320
	while True:
	    #rval, frame = vc.read()
	    #c = c + 1
	    #if c % 6 is 0:
		#    c = c + 1
	    #time.sleep(0.5)
	    cv2.waitKey(1)
	    frameCount = bytearray(memory.read())
	    curve = bytearray(memory2.read())
	    #print(curve[0])
	    #print(curve[1])
	    #print(curve[2])
	    #print(curve[3])
	    m = np.array(frameCount, dtype=np.uint8)
	    orig_img = m.reshape(size)
	    #print orig_img[0]
	    #cv2.imshow('1', m)

	    #true_anno = true_annolist[i]
	    #orig_img = imread('%s/%s' % (data_dir, true_anno.imageName))[:,:,:3]
	    #orig_img = imread('/home/caucse/images/1.jpg')
	    #orig_img = m
	    img = imresize(orig_img, (H["image_height"], H["image_width"]), interp='cubic')
	    feed = {x_in: img}
	    (np_pred_boxes, np_pred_confidences) = sess.run([pred_boxes, pred_confidences], feed_dict=feed)
	    pred_anno = al.Annotation()
	    #pred_anno.imageName = true_anno.imageName
	    new_img, rects = add_rectangles(H, [img], np_pred_confidences, np_pred_boxes,
					    use_stitching=True, rnn_len=H['rnn_len'], min_conf=args.min_conf, tau=args.tau, show_suppressed=args.show_suppressed)
	    flag = 0
	    for rect in rects:
		print(rect.x1, rect.x2, rect.y2)
		if (rect.x1 < road_center and rect.x2 > road_center and rect.y2 > 200) and (rect.x2 - rect.x1 > 30):
			flag = 1

	    if flag is 1:
		pedal.press(2)
		print("break!")
	    else:
		pedal.release(2)
		pedal.press(1)
		print("acceleration!")
		
	    pred_anno.rects = rects
	    pred_anno.imagePath = os.path.abspath(data_dir)
	    pred_anno = rescale_boxes((H["image_height"], H["image_width"]), pred_anno, orig_img.shape[0], orig_img.shape[1])
	    pred_annolist.append(pred_anno)
	    #imname = '%s/%s' % (image_dir, os.path.basename(true_anno.imageName))
	    #imname = '/home/caucse/images/_%s.jpg' % (c)
	    cv2.imshow('.jpg', new_img)
	    #misc.imsave(imname, new_img)
	    #if c % 25 == 0:
		#print(c)



 	
        for i in range(len(true_annolist)):
            true_anno = true_annolist[i]
            #orig_img = imread('%s/%s' % (data_dir, true_anno.imageName))[:,:,:3]
	    orig_img = imread('/home/caucse/images/1.jpg')
            img = imresize(orig_img, (H["image_height"], H["image_width"]), interp='cubic')
            feed = {x_in: img}
            (np_pred_boxes, np_pred_confidences) = sess.run([pred_boxes, pred_confidences], feed_dict=feed)
            pred_anno = al.Annotation()
            pred_anno.imageName = true_anno.imageName
            new_img, rects = add_rectangles(H, [img], np_pred_confidences, np_pred_boxes,
                                            use_stitching=True, rnn_len=H['rnn_len'], min_conf=args.min_conf, tau=args.tau, show_suppressed=args.show_suppressed)
            
	    for rect in rects:
		print(rect.x1, rect.y1, rect.x2, rect.y2)
            	
            pred_anno.rects = rects
            pred_anno.imagePath = os.path.abspath(data_dir)
            pred_anno = rescale_boxes((H["image_height"], H["image_width"]), pred_anno, orig_img.shape[0], orig_img.shape[1])
            pred_annolist.append(pred_anno)
            #imname = '%s/%s' % (image_dir, os.path.basename(true_anno.imageName))
	    imname = '/home/caucse/images/_1.jpg'
            misc.imsave(imname, new_img)
            if i % 25 == 0:
                print(i)
    return pred_annolist, true_annolist

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--weights', default='output/overfeat_rezoom_2017_02_09_13.28/save.ckpt-100000')
    parser.add_argument('--expname', default='')
    parser.add_argument('--test_boxes', default='default')
    parser.add_argument('--gpu', default=0)
    parser.add_argument('--logdir', default='output')
    parser.add_argument('--iou_threshold', default=0.5, type=float)
    parser.add_argument('--tau', default=0.25, type=float)
    parser.add_argument('--min_conf', default=0.2, type=float)
    parser.add_argument('--show_suppressed', default=True, type=bool)
    args = parser.parse_args()
    os.environ['CUDA_VISIBLE_DEVICES'] = str(args.gpu)
    hypes_file = '%s/hypes.json' % os.path.dirname(args.weights)
    with open(hypes_file, 'r') as f:
        H = json.load(f)
    expname = args.expname + '_' if args.expname else ''
    pred_boxes = '%s.%s%s' % (args.weights, expname, os.path.basename(args.test_boxes))
    true_boxes = '%s.gt_%s%s' % (args.weights, expname, os.path.basename(args.test_boxes))


    pred_annolist, true_annolist = get_results(args, H)
    pred_annolist.save(pred_boxes)
    true_annolist.save(true_boxes)

    try:
        rpc_cmd = './utils/annolist/doRPC.py --minOverlap %f %s %s' % (args.iou_threshold, true_boxes, pred_boxes)
        print('$ %s' % rpc_cmd)
        rpc_output = subprocess.check_output(rpc_cmd, shell=True)
        print(rpc_output)
        txt_file = [line for line in rpc_output.split('\n') if line.strip()][-1]
        output_png = '%s/results.png' % get_image_dir(args)
        plot_cmd = './utils/annolist/plotSimple.py %s --output %s' % (txt_file, output_png)
        print('$ %s' % plot_cmd)
        plot_output = subprocess.check_output(plot_cmd, shell=True)
        print('output results at: %s' % plot_output)
    except Exception as e:
        print(e)

if __name__ == '__main__':
    main()
