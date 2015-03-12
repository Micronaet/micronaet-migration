#!/usr/bin/python
# -*- coding: utf-8 -*-
###############################################################################
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
###############################################################################


# -----------------------------------------------------------------------------
#                                 CLASS NODE
# -----------------------------------------------------------------------------

class openerp_node():
    ''' Node for OpenERP analysis (for importation)
    '''    

    # -------------------------------------------------------------------------
    #                               Private data
    # -------------------------------------------------------------------------
    _openerp = False         # OpenERP connection istance
    _columns = {}            # list of columnn of the object, format:
                             #  {'field_name': (type of field, object related), }

    # -------------------------------------------------------------------------
    #                               Public data
    # -------------------------------------------------------------------------
    name = False            # OpenERP object name    
    score = 0               # Total of nodes that link this node
    record = 0              # Total records in the table 
    childs = False          # Node child (only one level for node) format:
                            #   (node element, relation field, type of relation)

    # -------------------------------------------------------------------------
    #                               Magic method
    # -------------------------------------------------------------------------
    def __init__(self, name, openerp):
        ''' Generator of the object
        
            self: instance element
            node_list: list of node that is populated during creation
            openerp: openerp object for connection XML-RPC to OpenERP
        '''
        self.name = name
        self.table = name.replace(".", "_")
        self._openerp = openerp

        # Calculate fields:
        self._get_columns()
        self.record = self._total_record()
        return 

    # -------------------------------------------------------------------------
    #                               Private method
    # -------------------------------------------------------------------------
    def _get_columns(self, ):
        ''' Get column dict (column: type) >> search in ir_model_fields table
            >> ttype = (reference, serialized, datetime, many2many, text, 
                       selection, float, one2many, binary, char, many2one,
                       html, date, boolean, integer, )
                       
            self: object reference
        ''' 
        self._columns = {}
        field_ids = self._openerp._socket.execute(
            self._openerp._dbname, self._openerp._orm_uid, self._openerp._orm_password, 
            'ir.model.fields', 'search', [('model', '=', self.name)], )

        for field in self._openerp._socket.execute(
                self._openerp._dbname, self._openerp._orm_uid, self._openerp._orm_password, 'ir.model.fields', 
                'read', field_ids, ):
            if field['ttype'] in ('many2one', 'many2many', 'one2many', ):
                self._columns[field['name']] = (field['ttype'], field['relation'])
            else: # normal field:    
                self._columns[field['name']] = (field['ttype'], )
        return 
        
    def _total_record(self, ):
        ''' Get total record for current object-table node

            self: object reference
        '''
        try:
            self._openerp.pg_execute("SELECT count(*) FROM %s;" % (self.table, ), force_not_verbose = True)
            record = self._openerp._pg_cursor.fetchone()
            return record[0]
        except:
            return "#ERR"    

    # -------------------------------------------------------------------------
    #                               Public method
    # -------------------------------------------------------------------------
    def add_score(self, ):
        ''' Add one to score value for get the number of linked node
        
            self: instance element
        ''' 
        self.score += 1
        return
    
    def add_childs(self, all_nodes):
        ''' Add child to this node with extra info
        
            self: instance element
            all_node: dict of all node {'object': node istance}
        '''
        
        self.childs = []
        for field, value in self._columns.iteritems():
            if len(value) == 2:   # m2m m2o o2m
                #                   node element         field, type
                self.childs.append((all_nodes[value[1]], field, value[0]))
                all_nodes[value[1]].add_score()

    def info(self, score_range = False):
        ''' Show info of the node
        
            self: instance element    
            score_range: if present is a list with (>= min score, <= max score) value 
        '''
        if not score_range or (self.score >= score_range[0] and self.score <= score_range[1]):
            print "=" * 87
            print "| ROOT: %s [score: %s] record: %s" % (self.name, self.score, self.record)
            print "-" * 87
            for child in self.childs:       # Print only first level
                if child[2] == "many2one":
                    print "|==> %-30s >> on %-25s type %-15s" % (child[0].name, child[1], child[2], )
                elif child[2] == "many2many":
                    print "|--> %-30s >> on %-25s type %-15s" % (child[0].name, child[1], child[2], )
                else: # "one2many"
                    print "|  > (%-29s >> on %-25s type %-14s)" % (child[0].name, child[1], child[2], )
            print "=" * 87
        return
        

# -----------------------------------------------------------------------------
#                                  CLASS NODES
# -----------------------------------------------------------------------------

class nodes():
    ''' All Node for OpenERP analysis (for importation)
    '''    

    # -------------------------------------------------------------------------
    #                               Private attributes
    # -------------------------------------------------------------------------
    _openerp = False        # OpenERP connector element (for get data)
    _objects = False        # List of models in OpenERP
    _node_list = {}         # Node list for link the child

    # -------------------------------------------------------------------------
    #                               Public attributes
    # -------------------------------------------------------------------------
        
    # -------------------------------------------------------------------------
    #                               Magic method
    # -------------------------------------------------------------------------
    def __init__(self, openerp):
        ''' Generator of the object
        
            self: instance element
            node_list: list of node that is populated during creation
            openerp: openerp object for connection XML-RPC to OpenERP
        '''
        self._openerp = openerp
        self._get_objects()
        self._create_node_list()
        return

    # -------------------------------------------------------------------------
    #                               Private method
    # -------------------------------------------------------------------------
    def _get_objects(self, ):
        ''' Get openerp objects list
                       
            self: object reference
        '''

        self._objects = []
        model_ids = self._openerp._socket.execute(
            self._openerp._dbname, self._openerp._orm_uid, self._openerp._orm_password, 
            'ir.model', 'search', [], )
        for model in self._openerp._socket.execute(
                self._openerp._dbname, self._openerp._orm_uid, self._openerp._orm_password, 'ir.model',
                'read', model_ids, ):
            if not model['osv_memory']: # not the wizard obj
                self._objects.append(model['model'])
        sorted(self._objects)
        return 

    def _create_node_list(self, ):
        '''Create root element list (all openerp object) 
        
           self: instance element           
        '''
        # Create node list (list of object in openerp)
        for model in self._objects: 
            self._node_list[model] = openerp_node(model, self._openerp)
            
        # Add child elements (list of m2o object linked with field name
        for node in self._node_list:
            self._node_list[node].add_childs(self._node_list)
        return
    
    # -------------------------------------------------------------------------
    #                               Public method
    # -------------------------------------------------------------------------
    def draw_tree(self, name, tree_path = None, only_field = False, relation = ''):
        ''' Recursive function that draw a tree from start node
        
            self: instance element
            name: node name for start drawing
            tree_path: list of node name passed (for recursive test and level)
            only_field: name of the field to write (many2many or many2one)
            relation: type of relation with parent
        '''
        node = self._node_list[name]
        if tree_path is None:
            tree_path = []
        level = 1 + len(tree_path)

        # Write node:
        if name not in tree_path:
            print "%s>>%02d>> %s [%s] (record: %s)" % (" " * 2 * level, level, name, relation, node.record)
            tree_path.append(name)
            
        else:    
            print "%s>>%02d>> %s [%s] (record: %s) *** RECURSION" % (" " * 2 * level, level, name, relation, node.record)
            return

        for child in node.childs:
            if (only_field and only_field == child[2]) or (not only_field and child[2] in ('many2one', 'many2many')): # only this 2 relations!
                child_tree = tree_path[:] # reset path list
                self.draw_tree(self._node_list[child[0].name].name, child_tree, relation = child[2])
        return
        
    def info(self, score_range = False):
        ''' Show info of the node for all node in the list (one level only)
        
            self: instance element    
            score_range: if present is a list with (min score, max score) value 
        '''
        for node in self._node_list:
            self._node_list[node].info(score_range = score_range)
        return

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
