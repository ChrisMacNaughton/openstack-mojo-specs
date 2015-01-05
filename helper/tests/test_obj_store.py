#!/usr/bin/python
import os
import swiftclient
import threading
import hashlib
import string
import random
import utils.mojo_os_utils as mojo_os_utils
import utils.mojo_utils as mojo_utils
import sys

class ObjectPushPull(threading.Thread):
    def __init__(self, runs, thread_name, payload_size='s'):
        super(ObjectPushPull, self).__init__()
        self.runs = runs
        self.thread_name = thread_name
        self.payload_size = payload_size
        self.container = thread_name
        self.sc = self.get_swiftclient()
        self.sc.put_container(container=self.container)
        self.successes = 0
        self.failures = 0

    def get_hash(self, rstring):
        hash_object = hashlib.sha1(rstring)
        return hash_object.hexdigest()

    def get_test_string(self,):
        # Large ~ 100Mb
        sizes = {'s': 10000,
                 'm': 100000,
                 'l': 100000000,
                }
        root_str = random.choice(string.letters) + random.choice(string.letters)
        return root_str*sizes[self.payload_size]

    def run(self):
        for i in range(0, self.runs):
            test_string = self.get_test_string()
            string_hash = self.get_hash(test_string)
            test_file = 'testfile.' + self.thread_name
            self.upload_file(test_file, test_string)
            if self.verify_file(test_file, string_hash):
                self.successes += 1
            else:
                self.failures += 1

    def get_swiftclient(self):
        overcloud_novarc = mojo_utils.get_overcloud_auth()
        swift_client = mojo_os_utils.get_swift_client(overcloud_novarc)
        return swift_client
        
    def get_checkstring(self, fname):
        return fname.split('-')[1]

    def verify_file(self, fname, check_hash):
        headers, content = self.sc.get_object(self.container, fname, headers = {'If-Match': self.etag})
        return check_hash == self.get_hash(content)

    def upload_file(self, fname, contents):
        response = {}
        self.sc.put_object(self.container, fname, contents, response_dict=response)
        self.etag = response['headers']['etag']

def main(argv):
    thread1 = ObjectPushPull(10, 'thread1', payload_size='l')
    thread2 = ObjectPushPull(100, 'thread2', payload_size='s')
    thread1.start()
    thread2.start()
    thread1.join()
    thread2.join()
    print "Thread 1"
    print "    Successes:" + str(thread1.successes)
    print "    Failures:" + str(thread1.failures)
    print "Thread 2"
    print "    Successes:" + str(thread2.successes)
    print "    Failures:" + str(thread2.failures)
    if thread2.failures > 0:
        sys.exit(1)

if __name__ == "__main__":
    sys.exit(main(sys.argv))
