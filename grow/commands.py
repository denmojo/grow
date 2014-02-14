#!/usr/bin/env python

import logging
import base64
import gflags as flags
import os
from google.apputils import appcommands
from grow import deployments
from grow.client import client
from grow.common import sdk_utils
from grow.server import manager
from grow.pods import commands as pod_commands
from grow.pods import pods
from grow.pods import storage

FLAGS = flags.FLAGS
flags.DEFINE_string('project', None, 'Project ID (owner/name).')
flags.DEFINE_string('changeset', None, 'Changeset name.')
flags.DEFINE_string('host', None, 'Grow server hostname (e.g. example.com).')



class UpCmd(appcommands.Cmd):
  """Uploads a pod to a remote pod server."""

  SKIP_PATTERNS = (
      '.DS_Store',
  )

  def Run(self, argv):
    owner, nickname = FLAGS.project.split('/')
    host = FLAGS.host
    pod = pods.Pod(argv[1], storage=storage.FileStorage)

    # Uploading to GrowEdit on dev appserver.
    if True or (host is not None and 'localhost' in host):
      service = client.Client(host=FLAGS.host)
      for pod_path in pod.list_dir('/'):
        if os.path.basename(pod_path) in UpCmd.SKIP_PATTERNS:
          continue
        path = os.path.join(pod.root, pod_path)
        content = open(path).read()
        if isinstance(content, unicode):
          content = content.encode('utf-8')
        content = base64.b64encode(content)
        service.rpc('pods.update_file', {
           'project': {
             'owner': {'nickname': owner},
             'nickname': nickname,
           },
           'file': {
             'pod_path': pod_path,
             'content_b64': content,
           }
        })
        print 'Uploaded: {}'.format(pod_path)
#      req = service.pods().finalizeStagedFiles(body={
#        'pod': {'changeset': changeset}
#      })
#      req.execute()
      print 'Upload finalized.'
    else:
      raise NotImplementedError()
#      google_cloud_storage.upload_to_gcs(pod, changeset, host=host)


class RunCmd(appcommands.Cmd):
  """Runs a local pod server for a single pod."""

  def Run(self, argv):
    if len(argv) != 2:
      raise Exception('Must specify pod directory.')
    root = os.path.abspath(os.path.join(os.getcwd(), argv[-1]))
    sdk_utils.check_version(quiet=True)
    logging.info('Serving pod with root: {}'.format(root))
    manager.start(root)


class DeployCmd(appcommands.Cmd):
  """Deploys a pod to a remote destination."""

  flags.DEFINE_enum('destination', None, ['gcs', 'local', 's3'],
                    'Destination to deploy to.')

  flags.DEFINE_string('bucket', None,
                      'Google Cloud Storage or Amazon S3 bucket.')

  flags.DEFINE_string('out_dir', None, 'Directory to write to.')

  def Run(self, argv):
    root = os.path.abspath(os.path.join(os.getcwd(), argv[-1]))
    pod = pods.Pod(root, storage=storage.FileStorage)

    if FLAGS.destination is None:
      raise appcommands.AppCommandsError('Must specify: --destination.')

    if FLAGS.destination == 'gcs':
      if FLAGS.bucket is None:
        raise appcommands.AppCommandsError('Must specify: --bucket.')
      deployment = deployments.GoogleCloudStorageDeployment(bucket=FLAGS.bucket)
    elif FLAGS.destination == 's3':
      if FLAGS.bucket is None:
        raise appcommands.AppCommandsError('Must specify: --bucket.')
      deployment = deployments.AmazonS3Deployment(bucket=FLAGS.bucket)
    elif FLAGS.destination == 'local':
      out_dir = os.path.abspath(os.path.join(os.getcwd(), FLAGS.out_dir))
      deployment = deployments.FileSystemDeployment(out_dir=out_dir)

    deployment.deploy(pod)


class DumpCmd(appcommands.Cmd):
  """Generates static files and dumps them to a local destination."""

  def Run(self, argv):
    root = os.path.abspath(os.path.join(os.getcwd(), argv[-2]))
    out_dir = os.path.abspath(os.path.join(os.getcwd(), argv[-1]))
    pod = pods.Pod(root, storage=storage.FileStorage)
    pod.dump(out_dir=out_dir)


class InitCmd(appcommands.Cmd):
  """Initializes a blank pod (or one with a theme) for local development."""

  def Run(self, argv):
    if len(argv) != 3:
      raise Exception('Usage: grow init <repo> <pod root>')
    root = os.path.abspath(os.path.join(os.getcwd(), argv[-1]))
    repo_url = argv[-2]
    pod = pods.Pod(root, storage=storage.FileStorage)
    pod_commands.init(pod, repo_url)


class TestCmd(appcommands.Cmd):
  """Validates a pod and runs its tests."""

  def Run(self):
    raise NotImplementedError()
