import ast
import asyncio
import collections.abc
import concurrent.futures
import decimal
import functools
import itertools
import math
import numbers
import operator
import pprint
import textwrap
import time
import traceback
from typing import Any, Union

import discord
from discord.ext import commands

from bot.utils.formatting import codeblock

OPERATORS = {
    # ast.BinOp
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.MatMult: operator.matmul,
    ast.Div: operator.truediv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.LShift: operator.lshift,
    ast.RShift: operator.rshift,
    ast.BitOr: operator.or_,
    ast.BitXor: operator.xor,
    ast.BitAnd: operator.and_,
    ast.FloorDiv: operator.floordiv,

    # ast.UnaryOp
    ast.Invert: operator.invert,
    ast.Not: operator.not_,
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,

    # ast.Compare
    ast.Eq: operator.eq,
    ast.NotEq: operator.ne,
    ast.Lt: operator.lt,
    ast.LtE: operator.le,
    ast.Gt: operator.gt,
    ast.GtE: operator.ge,
    ast.Is: operator.is_,
    ast.IsNot: operator.is_not,
    ast.In: lambda a, b: a in b,
    ast.NotIn: lambda a, b: a not in b
}


class Number(decimal.Decimal):
    """An decimal object that acts as float / int"""
    def __new__(cls, value):
        def wrap_method(method: str):
            def wrapped(self, *args, **kwargs):
                original_method = getattr(super(), method)
                functools.update_wrapper(wrapped, original_method)
                res = original_method(*args, **kwargs)
                if isinstance(res, numbers.Number):
                    res = cls(res)

                return res

            return wrapped

        to_wrap = [
            '__add__', '__sub__', '__mul__', '__truediv__', '__floordiv__', '__mod__', '__divmod__',
            '__pow__', '__radd__', '__rsub__', '__rmul__', '__rtruediv__', '__rfloordiv__', '__rmod__',
            '__rdivmod__', '__rpow__', '__neg__', '__pos__', '__abs__', '__round__', '__trunc__', '__floor__',
            '__ceil__'
        ]

        for method in to_wrap:
            setattr(cls, method, wrap_method(method))

        return decimal.Decimal.__new__(cls, value)

    def __repr__(self):
        return str(self)

    def __lshift__(self, other):
        return Number(int(self) << int(other))

    def __rshift__(self, other):
        return Number(int(self) >> int(other))

    def __rlshift__(self, other):
        return Number(int(other) << int(self))

    def __rrshift__(self, other):
        return Number(int(other) >> int(self))

    def __and__(self, other):
        return Number(int(self) & int(other))

    def __xor__(self, other):
        return Number(int(self) ^ int(other))

    def __or__(self, other):
        return Number(int(self) | int(other))

    def __rand__(self, other):
        return Number(int(other) & int(self))

    def __rxor__(self, other):
        return Number(int(other) ^ int(self))

    def __ror__(self, other):
        return Number(int(other) | int(self))

    def __index__(self):
        return int(self)


class Boolean(Number):
    def __new__(cls, value=False):
        return decimal.Decimal.__new__(cls, bool(value))

    def __repr__(self):
        return 'True' if self else 'False'

    def __str__(self):
        return repr(self)


class Undefined(Number):
    def __new__(cls, value=False):
        return decimal.Decimal.__new__(cls, 0)

    def __repr__(self):
        return self.__class__.__name__

    def __call__(self, *_, **__):
        return self


undefined = Undefined()


class EvalFunction:
    def __new__(cls, function: callable):
        self = object.__new__(cls)
        functools.update_wrapper(self, function)
        self.func = function
        return self

    def __call__(self, *args, **kwargs) -> Any:
        return self.func(*args, **kwargs)

    def __repr__(self):
        return f'<built-in function {self.func.__name__}>'


class FrozenMapping(collections.abc.Mapping):
    def __new__(cls, mapping):
        self = object.__new__(cls)
        self.mapping = mapping
        return self

    def __getitem__(self, key: str) -> Any:
        return self.mapping[key]

    def __iter__(self) -> iter:
        return iter(self.mapping)

    def __len__(self) -> int:
        return len(self.mapping)


class EvalLib(collections.abc.Mapping):
    def __new__(cls):
        self = object.__new__(cls)

        self.functions = FrozenMapping({
            i: EvalFunction(j) for i, j in {
                # Built-ins
                'absolute': abs,
                'all': all,
                'any': any,
                'binary': bin,
                'boolean': Boolean,
                'character': chr,
                'dictionary': dict,
                'enumerate': enumerate,
                'filter': filter,
                'hexadecimal': hex,
                'length': len,
                'list': list,
                'map': map,
                'max': max,
                'min': min,
                'number': Number,
                'octal': oct,
                'range': range,
                'round': round,
                'string': str,
                'zip': zip,

                # Math module
                'arccos': math.acos,
                'arccosh': math.acosh,
                'arcsin': math.asin,
                'arcsinh': math.asinh,
                'arctan': math.atan,
                'arctanh': math.atanh,
                'ceiling': math.ceil,
                'cos': math.cos,
                'cosh': math.cosh,
                'degrees': math.degrees,
                'distance': math.dist,
                'exp': math.exp,
                'floor': math.floor,
                'hypotenuse': math.hypot,
                'log': math.log,
                'log2': math.log2,
                'log10': math.log10,
                'radians': math.radians,
                'sin': math.sin,
                'sinh': math.sinh,
                'sqrt': math.sqrt,
                'tan': math.tan,
                'tanh': math.tanh
            }.items()
        })
        self.constants = FrozenMapping({
            'euler': Number(str(math.e)),
            'pi': Number(str(math.pi)),
            'tau': Number(str(math.tau)),
            'infinity': Number('inf'),
            'nan': Number('nan'),
            'undefined': undefined
        })
        self.aliases = FrozenMapping({
            'abs': 'absolute',
            'bin': 'binary',
            'bool': 'boolean',
            'char': 'character',
            'chr': 'character',
            'dict': 'dictionary',
            'hex': 'hexadecimal',
            'len': 'length',
            'num': 'number',
            'oct': 'octal',
            'str': 'string',
            'acos': 'arccos',
            'arcos': 'arccos',
            'acosh': 'arccosh',
            'arcosh': 'arccosh',
            'asin': 'arcsin',
            'asinh': 'arcsin',
            'atan': 'arctan',
            'atanh': 'arctanh',
            'ceil': 'ceiling',
            'cosine': 'cos',
            'deg': 'degrees',
            'dist': 'distance',
            'hypot': 'hypotenuse',
            'prod': 'product',
            'rad': 'radians',
            'sine': 'sin',
            'tangent': 'tan',
            'e': 'euler',
            'inf': 'infinity',
            'undef': 'undefined'
        })

        return self

    def __getitem__(self, key: str) -> Union[Number, EvalFunction]:
        if key in self.aliases:
            key = self.aliases[key]

        if key in self.functions:
            return self.functions[key]

        if key in self.constants:
            return self.constants[key]

        raise KeyError(key)

    def __iter__(self) -> iter:
        return itertools.chain(self.functions, self.constants, self.aliases)

    def __len__(self) -> int:
        return len(self.functions) + len(self.constants) + len(self.aliases)


evallib = EvalLib()


class SafeEvaluator(ast.NodeVisitor):
    def __init__(self, expression: str):
        self.expression = expression
        self.nodes = ast.parse(expression).body
        self.env = {}

    def visit(self, node: ast.AST) -> Any:
        res = super().visit(node)
        if isinstance(res, (Number, Boolean)):
            return res
        if isinstance(res, bool):
            return Boolean(res)
        if isinstance(res, numbers.Number):
            return Number(res)
        return res

    def evaluate(self):
        for node in self.nodes:
            segment = ast.get_source_segment(self.expression, node)
            try:
                yield segment, self.visit(node)
            except Exception as exc:
                yield segment, exc

    def generic_visit(self, node: ast.AST) -> Any:
        raise NotImplementedError(f'Node "{node.__class__.__name__}" is not implemented')

    def visit_Expr(self, node: ast.Expr) -> Any:
        return self.visit(node.value)

    def visit_Constant(self, node: ast.Constant) -> Any:
        if isinstance(node.value, bool):
            return Boolean(node.value)
        if isinstance(node.value, numbers.Number):
            return Number(ast.get_source_segment(self.expression, node))
        return node.value

    def visit_BinOp(self, node: ast.BinOp) -> Any:
        return OPERATORS[type(node.op)](self.visit(node.left), self.visit(node.right))

    def visit_BoolOp(self, node: ast.BoolOp) -> Any:
        res = None
        if type(node.op) == ast.And:
            for value in node.values:
                res = self.visit(value)
                if not res:
                    break
            return res

        if type(node.op) == ast.Or:
            for value in node.values:
                res = self.visit(value)
                if res:
                    break
            return res

    def visit_UnaryOp(self, node: ast.UnaryOp) -> Any:
        return OPERATORS[type(node.op)](self.visit(node.operand))

    def visit_Compare(self, node: ast.Compare) -> Boolean:
        left = self.visit(node.left)
        for op, comp in zip(node.ops, node.comparators):
            right = self.visit(comp)
            if not OPERATORS[type(op)](left, right):
                return Boolean(False)
            left = right

        return Boolean(True)

    def visit_Name(self, node: ast.Name) -> Any:
        context = type(node.ctx)
        if context == ast.Load:
            if node.id.lower() in evallib:
                return evallib[node.id.lower()]
            return self.env.get(node.id, undefined)
        if context == ast.Store:
            if node.id in evallib:
                return
            return node.id
        return undefined

    def visit_Assign(self, node: ast.Assign) -> None:
        value = self.visit(node.value)
        for target in map(self.visit, node.targets):
            if target in evallib:
                continue
            self.env[target] = value

    def visit_Call(self, node: ast.Call) -> Any:
        return self.visit(node.func)(*map(self.visit, node.args), **dict(map(self.visit, node.keywords)))

    def visit_IfExp(self, node: ast.IfExp) -> Any:
        return self.visit(node.body) if self.visit(node.test) else self.visit(node.orelse)

    def visit_List(self, node: ast.List) -> list[Any]:
        return list(map(self.visit, node.elts))

    def visit_Tuple(self, node: ast.Tuple) -> tuple[Any]:
        return tuple(map(self.visit, node.elts))


class Math(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command()
    async def functions(self, ctx: commands.Context):
        evallib = EvalLib()
        embed = discord.Embed(color=0x5050fa)
        embed.add_field(
            name='Available functions', inline=False, value=', '.join(f'`{i}`' for i in evallib.functions)
        )

        embed.add_field(
            name='Available constants', inline=False, value=', '.join(f'`{i}`' for i in evallib.constants)
        )

        await ctx.send(embed=embed)

    @commands.command(aliases=['calc', 'c'])
    async def calculate(self, ctx: commands.Context, *, expression: str):
        eval_time = time.perf_counter()
        try:
            evaluator = SafeEvaluator(expression)

        except SyntaxError as exc:
            await ctx.send(
                embed=discord.Embed(
                    color=0xfa5050,
                    title='Syntax error!',
                    description=codeblock(f'{exc.text.strip()}\n{"^":>{exc.offset}}\n{exc.msg}')
                )
            )
            return

        values = []
        errors = []
        with concurrent.futures.ThreadPoolExecutor() as pool:
            def _():
                decimal.setcontext(
                    decimal.Context(prec=32, rounding=decimal.ROUND_HALF_EVEN, capitals=0, traps=[])
                )
                for segment, value in evaluator.evaluate():
                    values.append((segment, value))
                    if isinstance(value, Exception):
                        errors.append((segment, value))

            try:
                await asyncio.wait_for(self.bot.loop.run_in_executor(pool, _), timeout=10)
            except asyncio.TimeoutError as exc:
                errors.append(('<unknown>', exc))

        embed = discord.Embed(description=f':clock2: Evaluated in {(time.perf_counter()-eval_time)*1000:g}ms')

        embed.add_field(
            name='Results',
            inline=False,
            value=codeblock(
                '\n'.join(
                    f'{textwrap.shorten(i, width=30, placeholder="…")} => {pprint.pformat(j)}'
                    if j is not None else i for i, j in values
                )
            )
        )

        if errors:
            embed.color = 0xfa5050
            embed.title = f'Evaluated {len(evaluator.nodes)} expressions with {len(errors)} errors'
            embed.add_field(
                name='Errors',
                inline=False,
                value=codeblock(
                    '\n\n'.join(
                        f'On {textwrap.shorten(i, width=40, placeholder="…")}:\n' +
                        textwrap.indent('\n'.join(traceback.format_exception_only(type(j), j)), '  ')
                        for i, j in errors
                    )
                )
            )

        else:
            embed.color = 0x50fa50
            embed.title = f'Evaluated {len(evaluator.nodes)} expressions'

        if evaluator.env:
            embed.add_field(
                name='Environment',
                value=codeblock('\n'.join(f'{i} => {j}' for i, j in evaluator.env.items()))
            )

        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Math(bot))
