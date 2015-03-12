#!/usr/bin/python
# -*- coding: utf-8 -*-
##############################################################################
#
#    Micronaet S.r.l., Migration script for PostgreSQL
#    Copyright (C) 2002-2013 Micronaet SRL (<http://www.micronaet.it>). 
#    All Rights Reserved
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import sys, os

# ----------------------------------
# Class for manage a tree structure:
# ----------------------------------

class node():
    ''' Class for manage tree structure
    '''
    
    # ------------------
    # Magic functions: -
    # ------------------    
    def __init__(self, name, parent=None, child=[], level=0):
        ''' Init script of the class
        '''
        # Initialize data elements for this class:
        self._name = name
        self._parent = parent     # parent node
        self._parents = [parent,] # list of nodes
        self._child = child       # list of child
        self._level = level
        self._leaf = False    
        self._iterate = False # if there's a new node that is yet present in _parent structure stop here
        
    # -------------------
    # Hided functions:  -
    # -------------------    
        
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
