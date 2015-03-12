#!/usr/bin/python
# -*- encoding: utf-8 -*-

class node():
    ''' Tree node linked to openerp object
    '''
    parent = False        # Parent of the node
    child = []            # Child of the node
    
    name = False          # Name of the node (for print)
    root = False          # The node is the root
    recursion = False     # True if this node create a recursion (so stop navigate)
    openerp = False       # Self object in openerp
    openerp_obj = False   # OpenERP object pool linked to the node
    parent_field = False  # Field name for relation element
    level = 0             # Level of node (parent is 0)

    def _check_recursion(self, elements = None):
        ''' Check recursion in a tree family
        '''
        if elements is None:
            elements = []
        
        if self.name in elements:
            return True # recursion
        elif self.parent:
            elements.append(self.name)
            return self.parent._check_recursion(elements)
        else:
            return False # No recursion and no parent (leave node)
            
    def _get_child(self):
        ''' 
        '''
        if self.recursion:
            return # stop analyzing
        # Loop on all fields searching many2one
        columns = self.openerp_obj._columns
        for field in columns:
            if columns[field]._type == "many2one": 
                self.child.append(
                    node(
                        openerp_obj = self.openerp.pool.get(columns[field]._obj),
                        openerp = self.openerp,
                        parent = self, 
                        parent_field = field))
            elif self.openerp_obj._columns[field]._type == "many2many": 
                pass # TODO segnalare i m2m
                
        return
    
    def __init__(self, openerp_obj, openerp, parent = False, parent_field = False):
        ''' Create the object
        '''
        if parent:
            self.parent = parent
            self.parent_field = parent_field
            self.level = parent.level + 1

        self.openerp = openerp        
        self.name = openerp_obj._name
        self.root = not parent
        self.recursion = self._check_recursion()
        self.openerp_obj = openerp_obj
        self._print_node(extra_info = True )
        self._get_child()
        return
        
    def _print_node(self, extra_info = False):
        ''' Print single node:
        '''        
        if not self.parent:
            print "\nRoot: [%s]" %(self.name, )
        else:
            if extra_info:
                print "|-%s-> %s) Node: %s [figlio: %s], parent: %s, recursion %s" % (
                    "-" * self.level,
                    self.level,
                    self.name,
                    self.parent.name if self.parent else "/",
                    self.parent_field,
                    "***RECURSION***" if self.recursion else "False",
                    )
            else:
                print "|-%s-> Node: %s [figlio: %s]" % (
                    "-" * self.level,
                    self.name, 
                    self.parent.name if self.parent else "/")
        return
        
    def show(self, ):
        ''' Print tree structure (recursive)
        ''' 
        self._print_node()
        # Child:
        for child in self.child:
            child.show()
        return

