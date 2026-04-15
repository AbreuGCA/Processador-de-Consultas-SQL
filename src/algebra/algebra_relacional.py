class Node:
    def __init__(self, name ,child= None):
        self.name = name
        self.child = child
        
class ScanNode(Node):
    def __init__(self, table_name):
        super().__init__("Scan")
        self.table_name = table_name
    
class  SelectionNode(Node):
    def __init__(self, condition, child):
        super().__init__("Selection", child)
        self.condition = condition
        
class ProjectionNode(Node):
    def __init__(self, columns, child):
        super().__init__("Projection", child)
        self.columns = columns
        
class JoinNode(Node):
    def __init__(self, condition, left_child, right_child):
        super().__init__("Join")
        self.condition = condition
        self.left_child = left_child
        self.right_child = right_child