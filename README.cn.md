# py-signe

[ENGLISH README](./README.md)


#### 介绍
参考 [S.js](https://github.com/adamhaile/S) 与 [vue reactivity](https://github.com/vuejs/core/tree/main/packages/reactivity) 的核心机制，在 python 中实现的响应式系统

#### 安装
```shell
pip install signe
```

#### 使用
```python
from signe import signal, effect, computed

num = signal(1)

@computed
def plus1():
    return num.value + 1


@effect
def _():
    print('plus1 is :',plus1.value)

# 此时控制台打印 `plus1 is :2`

num.value=10

# 此时控制台打印 `plus1 is :11`


```

- `signal` 创建信号。通过 `.value` 读写。
- `computed` 创建计算表达。其参数为一个函数。函数中使用信号的 `signal.value` 获取值，则此计算表达与信号自动产生关联。当信号的值变化时，计算表达也会自动触发改变。
- `effect` 本质上与 `computed` 一样。可以自动捕获信号或计算表达`computed`的改变，从而自动触发。

