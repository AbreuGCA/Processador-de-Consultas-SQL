from src.algebra.algebra_relacional import ScanNode, SelectionNode, ProjectionNode, JoinNode

class Optimizer:

    def __init__(self, parsed_query: dict):
        self.query = parsed_query

    def build_optimized_tree(self):
        root = ScanNode(self.query['from'])

        if self.query.get('where'):
            root = SelectionNode(condition=self.query['where'], child=root)

        if self.query.get('select'):
            if self.query['select'].strip() != '*':
                columns = [c.strip() for c in self.query['select'].split(',')]
                root = ProjectionNode(columns=columns, child=root)

        if self.query.get('join_table'):
            right_branch = ScanNode(self.query['join_table'])
            root = JoinNode(
                condition=self.query['join_cond'],
                left_child=root,
                right_child=right_branch
            )

        return root

    def build_unoptimized_tree(self):
        root = ScanNode(self.query['from'])

        if self.query.get('join_table'):
            right_branch = ScanNode(self.query['join_table'])
            root = JoinNode(
                condition=self.query['join_cond'],
                left_child=root,
                right_child=right_branch
            )

        if self.query.get('where'):
            root = SelectionNode(
                condition=self.query['where'],
                child=root
            )

        if self.query.get('select') and self.query['select'].strip() != '*':
            columns = [c.strip() for c in self.query['select'].split(',')]
            root = ProjectionNode(columns=columns, child=root)

        return root