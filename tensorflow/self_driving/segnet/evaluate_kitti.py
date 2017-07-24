"""Evaluate SegNet.

nohup python -u -m self_driving.segnet.evaluate_kitti > self_driving/segnet/output.txt 2>&1 &

"""

import os
import tensorflow as tf
from utils import kitti_segnet
from scipy import misc
import matplotlib.cm as cm
from matplotlib.colors import Normalize

LOG_DIR = 'save'
EPOCH = 237
BATCH_SIZE = 1
IMAGE_HEIGHT = 375
IMAGE_WIDTH = 1242
NUM_CLASSES = 3

test_dir = "/usr/local/google/home/limeng/Downloads/kitti/data_road/training/train.txt"


def color_image(image, num_classes):
    cmap = cm.get_cmap('Set1')
    norm = Normalize(vmin=0., vmax=num_classes)
    return cmap(norm(image))


def main(_):
    test_image_filenames, test_label_filenames = kitti_segnet.get_filename_list(test_dir)
    index = 0

    with tf.Graph().as_default():
        with tf.device('/cpu:0'):
            config = tf.ConfigProto()
            config.gpu_options.allocator_type = 'BFC'
            sess = tf.InteractiveSession(config=config)

            images, labels = kitti_segnet.CamVidInputs(test_image_filenames,
                                                       test_label_filenames,
                                                       BATCH_SIZE,
                                                       shuffle=False)

            saver = tf.train.import_meta_graph(os.path.join(LOG_DIR, "segnet.ckpt.meta"))
            saver.restore(sess, tf.train.latest_checkpoint(LOG_DIR))

            graph = tf.get_default_graph()
            train_data = graph.get_tensor_by_name("train_data:0")
            train_label = graph.get_tensor_by_name("train_labels:0")
            logits = tf.get_collection("logits")[0]

            # Start the queue runners.
            coord = tf.train.Coordinator()
            threads = tf.train.start_queue_runners(sess=sess, coord=coord)

            for i in range(EPOCH):
                image_batch, label_batch = sess.run([images, labels])
                feed_dict = {
                    train_data: image_batch,
                    train_label: label_batch
                }
                prediction = sess.run([logits], feed_dict)
                pred = tf.argmax(prediction[0], dimension=3).eval()
                for batch in range(BATCH_SIZE):
                    up_color = color_image(pred[batch], NUM_CLASSES)
                    misc.imsave('output/segnet_kitti/decision_%d.png' % index, up_color)
                    misc.imsave('output/segnet_kitti/train_%d.png' % index, image_batch[batch])
                    index += 1

            coord.request_stop()
            coord.join(threads)


if __name__ == '__main__':
    tf.app.run(main=main)
