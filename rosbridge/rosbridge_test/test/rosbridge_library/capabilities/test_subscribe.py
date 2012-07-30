#!/usr/bin/env python
PKG = 'rosbridge_library'
import roslib
roslib.load_manifest(PKG)
roslib.load_manifest("std_msgs")
import rospy

import unittest
import time

from json import loads, dumps
from std_msgs.msg import String

from rosbridge_library.capabilities import subscribe
from rosbridge_library.protocol import Protocol
from rosbridge_library.protocol import InvalidArgumentException, MissingArgumentException


class TestSubscribe(unittest.TestCase):

    def setUp(self):
        rospy.init_node("test_subscribe")

    def dummy_cb(self, msg):
        pass

    def test_update_params(self):
        """ Adds a bunch of random clients to the subscription and sees whether
        the correct parameters are chosen as the min """
        client_id = "client_test_update_params"
        topic = "/test_update_params"
        msg_type = "std_msgs/String"

        subscription = subscribe.Subscription(client_id, topic, None)

        min_throttle_rate = 5
        min_queue_length = 2
        min_frag_size = 20

        for throttle_rate in range(min_throttle_rate, min_throttle_rate + 10):
            for queue_length in range(min_queue_length, min_queue_length + 10):
                for frag_size in range(min_frag_size, min_frag_size + 10):
                    sid = throttle_rate * 100 + queue_length * 10 + frag_size
                    subscription.subscribe(sid, msg_type, throttle_rate,
                                           queue_length, frag_size)

        subscription.update_params()

        try:
            self.assertEqual(subscription.throttle_rate, min_throttle_rate)
            self.assertEqual(subscription.queue_length, min_queue_length)
            self.assertEqual(subscription.fragment_size, min_frag_size)
            self.assertEqual(subscription.compression, "none")

            subscription.clients.values()[0]["compression"] = "png"

            subscription.update_params()

            self.assertEqual(subscription.throttle_rate, min_throttle_rate)
            self.assertEqual(subscription.queue_length, min_queue_length)
            self.assertEqual(subscription.fragment_size, min_frag_size)
            self.assertEqual(subscription.compression, "png")
        except:
            subscription.unregister()
            raise

        subscription.unregister()

    def test_missing_arguments(self):
        proto = Protocol("test_missing_arguments")
        sub = subscribe.Subscribe(proto)
        msg = {"op": "subscribe"}
        self.assertRaises(MissingArgumentException, sub._subscribe, None, msg)

    def test_invalid_arguments(self):
        proto = Protocol("test_invalid_arguments")
        sub = subscribe.Subscribe(proto)

        msg = {"op": "subscribe", "topic": 3}
        self.assertRaises(InvalidArgumentException, sub._subscribe, None, msg)

        msg = {"op": "subscribe", "topic": "/jon", "type": 3}
        self.assertRaises(InvalidArgumentException, sub._subscribe, None, msg)

        msg = {"op": "subscribe", "topic": "/jon", "throttle_rate": "fast"}
        self.assertRaises(InvalidArgumentException, sub._subscribe, None, msg)

        msg = {"op": "subscribe", "topic": "/jon", "fragment_size": "five cubits"}
        self.assertRaises(InvalidArgumentException, sub._subscribe, None, msg)

        msg = {"op": "subscribe", "topic": "/jon", "queue_length": "long"}
        self.assertRaises(InvalidArgumentException, sub._subscribe, None, msg)

        msg = {"op": "subscribe", "topic": "/jon", "compression": 9000}
        self.assertRaises(InvalidArgumentException, sub._subscribe, None, msg)

    def test_subscribe_works(self):
        proto = Protocol("test_subscribe_works")
        sub = subscribe.Subscribe(proto)
        topic = "/test_subscribe_works"
        msg = String()
        msg.data = "test test_subscribe_works works"
        msg_type = "std_msgs/String"

        received = {"msg": None}

        def send(outgoing):
            received["msg"] = outgoing

        proto.send = send

        sub.subscribe(loads(dumps({"op": "subscribe", "topic": topic, "type": msg_type})))

        p = rospy.Publisher(topic, String)
        time.sleep(0.25)
        p.publish(msg)

        time.sleep(0.25)
        self.assertEqual(received["msg"]["msg"]["data"], msg.data)

if __name__ == '__main__':
    import rostest
    rostest.rosrun(PKG, 'test_subscribe', TestSubscribe)