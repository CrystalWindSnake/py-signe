# py-signe

#### 介绍
按照 [S.js](https://github.com/adamhaile/S) 的核心机制，在 python 中实现的响应式系统

#### 安装
```shell
pip install signe
```

#### 使用
```python
from signe import createSignal, effect, computed

get_num, set_num = createSignal(1)

@computed
def plus1():
    return get_num() + 1


@effect
def _():
    print('plus1 is :',plus1())

# 此时控制台打印 `plus1 is :2`

set_num(10)

# 此时控制台打印 `plus1 is :11`


```

- `createSignal` 创建信号。信号包含2个主要函数，分别是 `getter` 与 `setter` 函数。
- `computed` 创建计算表达。其参数为一个函数。函数中使用信号的 `getter` 函数获取值，则此计算表达与信号自动产生关联。当信号的值变化时，计算表达也会自动触发改变。
- `effect` 本质上与 `computed` 一样。可以自动捕获信号或计算表达`computed`的改变，从而自动触发。

