"""This module has nodes for importing a classifier with Timeflux."""

from timeflux.core.node import Node
from muselsl import stream, list_muses
import sys

class StartMuse(Node):

	def __init__(self):
		muses = list_muses()
		stream(muses[0]['address'])

	def update(self):
		pass
