# -*- coding: utf-8 -*

import re


class Query:
    def __init__(self, index=None, term=None, rlist=None, negated=None):
        if rlist is not None and negated is not None:
            self.result_list = rlist
            self.anti = negated
        if index is not None and term is not None:
            self.result_list = index.get_related_docs(term)
            self.anti = False

    @staticmethod
    def __intersect_lists(a, b):
        res = []
        i, j = 0, 0
        while i < len(a) and j < len(b):
            if a[i] == b[j]:
                res.append(a[i])
                i += 1
                j += 1
            elif a[i] > b[j]:
                j += 1
            elif a[i] < b[j]:
                i += 1
        return res

    @staticmethod
    def __subtract_lists(a, b):
        if b is None:
            return []
        res = []
        i, j = 0, 0
        while i < len(a) and j < len(b):
            if a[i] == b[j]:
                i += 1
                j += 1
            elif a[i] > b[j]:
                j += 1
            elif a[i] < b[j]:
                res.append(a[i])
                i += 1
        if i < len(a):
            res.extend(a[i:])
        return res

    @staticmethod
    def __unite_lists(a, b):
        if len(a) == 0:
            return b
        elif len(b) == 0:
            return a
        res = []
        i, j = 0, 0
        while i < len(a) and j < len(b):
            if a[i] <= b[j]:
                if len(res) == 0 or a[i] != res[-1]:
                    res.append(a[i])
                i += 1
            else:
                if len(res) == 0 or b[j] != res[-1]:
                    res.append(b[j])
                j += 1
        if i < len(a):
            res.extend([x for x in a[i:] if x > res[-1]])
        if j < len(b):
            res.extend([x for x in b[i:] if x > res[-1]])
        return res

    def get_query_urls(self, _):
        if not self.anti:
            return self.result_list
        else:
            raise ValueError('This query is too wild to process (imbalanced negated)')

    def __and__(self, other):
        anti_result = False
        if not self.anti:
            if not other.anti:
                res_list = Query.__intersect_lists(self.result_list, other.result_list)
            else:
                res_list = Query.__subtract_lists(self.result_list, other.result_list)
        else:
            if not other.anti:
                res_list = Query.__subtract_lists(other.result_list, self.result_list)
            else:
                res_list = Query.__unite_lists(self.result_list, other.result_list)
                anti_result = True
        return Query(rlist=res_list, negated=anti_result)

    def __or__(self, other):
        anti_result = False
        if not self.anti:
            if not other.anti:
                res_list = Query.__unite_lists(self.result_list, other.result_list)
            else:
                raise ValueError('This query is too wild to process (union with negated)')
        else:
            if not other.anti:
                raise ValueError('This query is too wild to process (union with negated)')
            else:
                res_list = Query.__intersect_lists(self.result_list, other.result_list)
                anti_result = True
        return Query(rlist=res_list, negated=anti_result)

    def negate(self):
        self.anti = not self.anti
        return self


class QueryProcessor:
    def __init__(self, index):
        self.index = index
        self.query_tokens = []

    def process(self, query):
        query = self.get_stream(query)
        compute_stack = []

        for token in query:
            if token == '&' or token == '|':
                result_1 = compute_stack.pop()
                result_2 = compute_stack.pop()
                if token == '&':
                    compute_stack.append(result_1 & result_2)
                else:
                    compute_stack.append(result_1 | result_2)
            elif token == '!':
                result_1 = compute_stack.pop()
                compute_stack.append(result_1.negate())
            else:
                compute_stack.append(Query(index=self.index, term=token))

        return compute_stack[0]

    @staticmethod
    def is_operator(x):
        if x == '|':
            return True
        elif x == '&':
            return True
        elif x == '!':
            return True
        elif x == '(' or x == ')':
            return True
        else:
            return False

    @staticmethod
    def get_priority(op):
        if op == '|':
            return 1
        elif op == '&':
            return 2
        elif op == '!':
            return 3
        else:
            return 0

    @staticmethod
    def encode_utf8(text):
        try:
            return text.encode('utf-8')
        except UnicodeEncodeError:
            return text

    def get_stream(self, query):
        query = re.sub(r'\s+', '', query)
        query = re.findall(r"[^&|!()]+|\S", query)
        query = map(lambda x: self.encode_utf8(x), query)
        query = map(lambda x: x.lower(), query)

        self.query_tokens = list(query)
        output = self.convert_to_polish_notation()
        return output

    def convert_to_polish_notation(self):
        output_string = []
        stack = []
        while len(self.query_tokens) > 0:
            next_token = self.query_tokens.pop(0)
            if not self.is_operator(next_token):
                output_string += [next_token]
            elif next_token == '(':
                stack += [next_token]
            elif next_token == ')':
                while stack[-1] != '(':
                    output_string += [stack.pop(-1)]
                stack.pop(-1)
            else:
                current_priority = self.get_priority(next_token)
                while len(stack) > 0:
                    stack_priority = self.get_priority(stack[-1])
                    if next_token == '!':
                        if current_priority >= stack_priority:
                            break
                    else:
                        if current_priority > stack_priority:
                            break
                    output_string += [stack.pop(-1)]
                stack += [next_token]

        while len(stack) > 0:
            output_string += [stack.pop(-1)]

        return output_string
