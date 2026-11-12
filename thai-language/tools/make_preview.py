#!/usr/bin/env python3
"""Draw the Steam Workshop preview with the repository's shared layout (tools/workshop_preview.py)."""
import os
import subprocess
import sys

MOD = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.exit(subprocess.call([sys.executable, os.path.join(os.path.dirname(MOD), 'tools', 'workshop_preview.py'),
                          MOD, 'ภาษาไทย', 'Thai Language Pack', 'แปลทั้งเกม  ·  ทุกยุค  ·  ทุก DLC']))
