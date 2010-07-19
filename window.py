#Copyright (c) 2010 Walter Bender

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place - Suite 330,
# Boston, MA 02111-1307, USA.

import pygtk
pygtk.require('2.0')
import gtk
import gobject
from math import sqrt

from gettext import gettext as _

try:
    from sugar.graphics import style
    GRID_CELL_SIZE = style.GRID_CELL_SIZE
except:
    GRID_CELL_SIZE = 0

from grid import Grid
from sprites import Sprites
from constants import C, MASKS, CARD_DIM

LEVEL_BOUNDS = [[[1, 2], [0, 1], [2, 3], [1, 2]],
                [[1, 2], [0, 1], [1, 4], [0, 3]], 
                [[0, 3], [-1, 2], [1, 5], [-1, 4]]]

class Game():
    """ The game play -- called from within Sugar or GNOME """

    def __init__(self, canvas, path, parent=None):
        """ Initialize the playing surface """

        self.path = path
        self.activity = parent

        # starting from command line
        # we have to do all the work that was done in CardSortActivity.py
        if parent is None:
            self.sugar = False
            self.canvas = canvas

        # starting from Sugar
        else:
            self.sugar = True
            self.canvas = canvas
            parent.show_all()

            self.canvas.set_flags(gtk.CAN_FOCUS)
            self.canvas.add_events(gtk.gdk.BUTTON_PRESS_MASK)
            self.canvas.add_events(gtk.gdk.BUTTON_RELEASE_MASK)
            self.canvas.connect("expose-event", self._expose_cb)
            self.canvas.connect("button-press-event", self._button_press_cb)
            self.canvas.connect("button-release-event", self._button_release_cb)
            self.width = gtk.gdk.screen_width()
            self.height = gtk.gdk.screen_height() - GRID_CELL_SIZE
            self.card_dim = CARD_DIM
            self.scale = 0.6 * self.height / (self.card_dim * 3)

        # Initialize the sprite repository
        self.sprites = Sprites(self.canvas)

        # Initialize the grid
        self.grid = Grid(self)
        self.bounds = LEVEL_BOUNDS[0]
        self.level = 0

        # Start solving the puzzle
        self.press = None
        self.release = None
        self.start_drag = [0, 0]

    def _button_press_cb(self, win, event):
        win.grab_focus()
        x, y = map(int, event.get_coords())
        self.start_drag = [x, y]
        spr = self.sprites.find_sprite((x, y))
        if spr is None:
            self.press = None
            self.release = None
            return True
        # take note of card under button press
        self.press = spr
        return True

    def _button_release_cb(self, win, event):
        win.grab_focus()
        x, y = map(int, event.get_coords())
        spr = self.sprites.find_sprite((x, y))
        if spr is None:
            self.press = None
            self.release = None
            return True
        # take note of card under button release
        self.release = spr
        # if the same card (click) then rotate
        if self.press == self.release:
            # check to see if it was an aborted move
            if distance(self.start_drag, [x, y]) < 20:
                pass
        else:
            self.grid.swap(self.press, self.release)
        self.press = None
        self.release = None
        if self.test() == True:
            if self.level < 2:
                gobject.timeout_add(3000, self.activity.level_cb, None)
        return True

    def _expose_cb(self, win, event):
        self.sprites.refresh(event)
        return True

    def _destroy_cb(self, win, event):
        gtk.main_quit()

    def mask(self, level):
        """ mask out cards not on play level """
        self.grid.hide_list(MASKS[level])
        self.bounds = LEVEL_BOUNDS[level]
        self.level = level

    def test(self):
        """ Test the grid to see if the level is solved """
        for i in range(24):
            if i not in MASKS[self.level]:
                if not self.test_card(i):
                    return False
        return True

    def test_card(self, i):
        """ Test a card with its neighbors; tests are bounded by the level """
        row = int(i/6)
        col = i%6
        if row > self.bounds[0][0] and row <= self.bounds[0][1]:
            if C[self.grid.grid[i]][0] != C[self.grid.grid[i - 6]][1]:
                return False
            if C[self.grid.grid[i]][3] != C[self.grid.grid[i - 6]][2]:
                return False
        if row > self.bounds[1][0] and row <= self.bounds[1][1]:
            if C[self.grid.grid[i]][1] != C[self.grid.grid[i + 6]][0]:
                return False
            if C[self.grid.grid[i]][2] != C[self.grid.grid[i + 6]][3]:
                return False
        if col > self.bounds[2][0] and col <= self.bounds[2][1]:
            if C[self.grid.grid[i]][3] != C[self.grid.grid[i - 1]][0]:
                return False
            if C[self.grid.grid[i]][2] != C[self.grid.grid[i - 1]][1]:
                return False
        if col > self.bounds[3][0] and col <= self.bounds[3][1]:
            if C[self.grid.grid[i]][0] != C[self.grid.grid[i + 1]][3]:
                return False
            if C[self.grid.grid[i]][1] != C[self.grid.grid[i + 1]][2]:
                return False
        return True


def distance(start, stop):
    """ Measure the length of drag between button press and button release. """
    dx = start[0] - stop[0]
    dy = start[1] - stop[1]
    return sqrt(dx * dx + dy * dy)
